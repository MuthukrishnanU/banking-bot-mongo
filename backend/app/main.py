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
    files = collection.find({}, {"docName": 1, "_id": 1})
    return [{"id": str(f["_id"]), "name": f["docName"]} for f in files]

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
