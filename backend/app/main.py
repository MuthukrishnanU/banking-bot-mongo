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

@app.post("/query")
async def query_bot(
    text: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None)
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
    
    response_data = get_rag_response(query_text)
    return {
        "query": query_text,
        **response_data
    }

@app.get("/usage")
async def get_usage():
    try:
        cache_collection = get_collection("semantic_cache")
        # Fetch all records, exclude embedding for performance
        usage_data = list(cache_collection.find({}, {"embedding": 0}))
        
        # Convert ObjectId to string for JSON serialization
        for item in usage_data:
            item["_id"] = str(item["_id"])
            
        return usage_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
