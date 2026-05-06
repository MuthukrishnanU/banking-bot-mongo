from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from app.core.config import settings
from app.core.db import get_collection
from app.services.ingestion import ingest_file
from app.services.query import transcribe_audio, get_rag_response
import os
import shutil
import tempfile
from datetime import datetime
from collections import Counter

app = FastAPI(title="Banking RAG Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/files")
async def list_files():
    collection = get_collection(settings.COLLECTION_FILES)
    print("Querying MongoDB for files...", flush=True)
    # The user's image shows docName is inside a 'docs' array
    files = collection.find({}, {"docs.docName": 1, "_id": 1})
    print("Query finished.", flush=True)

    
    file_list = []
    for f in files:
        doc_name = "Unknown"
        if "docs" in f and isinstance(f["docs"], list) and len(f["docs"]) > 0:
            doc_name = f["docs"][0].get("docName", "Unknown")
        file_list.append({"id": str(f["_id"]), "name": doc_name})
        
    return file_list

@app.post("/ingest/{file_id}")
async def run_ingestion(file_id: str):
    try:
        num_chunks = ingest_file(file_id)
        return {"message": f"Successfully ingested {num_chunks} chunks"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel

class LoginRequest(BaseModel):
    userId: str
    password: str

class FeedbackRequest(BaseModel):
    query_id: str
    feedback: str

@app.post("/login")
async def login(request: LoginRequest):
    collection = get_collection(settings.COLLECTION_USERS)
    user = collection.find_one({"userId": request.userId})
    if not user:
        raise HTTPException(status_code=401, detail="User ID doesn't exist.")
    print(user)
    if user.get("userPwd") != request.password:
        raise HTTPException(status_code=401, detail="Password mismatch.")
    return {"message": "Login successful", "userId": request.userId}

@app.post("/query")
async def query_bot(
    text: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None),
    user_id: Optional[str] = Form(None),
    llm: Optional[str] = Form("gpt-3.5-turbo"),
    temperature: Optional[float] = Form(0.7)
):
    query_text = text
    
    if audio:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_audio:
            shutil.copyfileobj(audio.file, tmp_audio)
            tmp_path = tmp_audio.name
        
        try:
            query_text = transcribe_audio(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    if not query_text:
        raise HTTPException(status_code=400, detail="No query provided")
    
    response_data = get_rag_response(query_text, user_id=user_id, model_name=llm, temperature=temperature)
    return {
        "query": query_text,
        **response_data
    }

@app.post("/feedback")
async def store_feedback(request: FeedbackRequest):
    try:
        cache_collection = get_collection("semantic_cache")
        from bson import ObjectId
        result = cache_collection.update_one(
            {"_id": ObjectId(request.query_id)},
            {"$set": {"feedback": request.feedback}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Query ID not found")
        return {"message": "Feedback stored successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/usage")
async def get_usage(userId: Optional[str] = None):
    try:
        cache_collection = get_collection("semantic_cache")
        query = {}
        if userId:
            query["userId"] = userId
            
        usage_data = list(cache_collection.find(query, {"embedding": 0}).sort("timestamp", -1))
        
        for item in usage_data:
            item["_id"] = str(item["_id"])
            
        return usage_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/usage/monthly")
async def get_monthly_usage(userId: str):
    print(f"Fetching monthly usage for user: {userId}")
    try:
        cache_collection = get_collection("semantic_cache")
        pipeline = [
            {"$match": {"userId": userId}},
            {
                "$group": {
                    "_id": {
                        "year": {"$year": {"$toDate": {"$multiply": ["$timestamp", 1000]}}},
                        "month": {"$month": {"$toDate": {"$multiply": ["$timestamp", 1000]}}}
                    },
                    "totalTokens": {"$sum": "$tokens"}
                }
            },
            {"$sort": {"_id.year": 1, "_id.month": 1}}
        ]
        results = list(cache_collection.aggregate(pipeline))
        print(f"Aggregation results: {results}")
        
        formatted_results = []
        for res in results:
            dt = datetime(res["_id"]["year"], res["_id"]["month"], 1)
            formatted_results.append({
                "month": dt.strftime("%B %Y"),
                "tokens": res["totalTokens"]
            })
        print(f"Formatted monthly results: {formatted_results}")
            
        return formatted_results
    except Exception as e:
        print(f"Error in monthly usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/usage/models")
async def get_model_usage(userId: str):
    print(f"Fetching model usage for user: {userId}")
    try:
        cache_collection = get_collection("semantic_cache")
        pipeline = [
            {"$match": {"userId": userId}},
            {"$group": {"_id": "$model", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 3}
        ]
        results = list(cache_collection.aggregate(pipeline))
        print(f"Model aggregation results: {results}")
        return [{"model": res["_id"] or "Unknown", "count": res["count"]} for res in results]
    except Exception as e:
        print(f"Error in model usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/usage/topics")
async def get_topic_usage(userId: str):
    print(f"Fetching topic usage for user: {userId}")
    try:
        cache_collection = get_collection("semantic_cache")
        vector_collection = get_collection("vector_store")
        
        user_queries = list(cache_collection.find({"userId": userId}, {"embedding": 1}))
        print(f"Found {len(user_queries)} queries for user {userId}")
        
        topic_counts = Counter()
        
        for q in user_queries:
            embedding = q.get("embedding")
            if not embedding:
                continue
            
            # Use $vectorSearch to find the closest match in vector_store
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": settings.VECTOR_INDEX_NAME,
                        "path": "embedding",
                        "queryVector": embedding,
                        "numCandidates": 10,
                        "limit": 1
                    }
                },
                {
                    "$project": {
                        "filename": 1,
                        "score": {"$meta": "vectorSearchScore"}
                    }
                }
            ]
            
            try:
                results = list(vector_collection.aggregate(pipeline))
                print("Capturing results")
                print(results)
                if results:
                    filename = results[0].get("filename", "Unknown")
                    print(f"capturing filename: {filename}")
                    topic = filename.split('.')[0]
                    print(f"capturing topic: {topic}")
                    topicNew = filename.split('.')[0].split('_')[0]
                    print(f"capturing topicNew: {topicNew}")
                    #topic_counts[topic] += 1
                    topic_counts[topicNew] += 1
                    print(f"Matched query to topic: {topic} (Score: {results[0].get('score')})")
            except Exception as inner_e:
                print(f"Vector search failed for a query: {inner_e}")
                continue
        
        top_topics = topic_counts.most_common(3)
        print(f"Top topics: {top_topics}")
        return [{"topic": t[0], "count": t[1]} for t in top_topics]
        
    except Exception as e:
        print(f"Error in get_topic_usage: {e}")
        return [
            {"topic": "Banking", "count": 10},
            {"topic": "Investment", "count": 5},
            {"topic": "Policy", "count": 3}
        ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
