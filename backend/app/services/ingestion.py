import os
import tempfile
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    CSVLoader,
    UnstructuredExcelLoader,
    UnstructuredImageLoader
)
from langchain_openai import OpenAIEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.db import get_collection
from app.core.config import settings
from bson import ObjectId

def get_loader(file_path: str, ext: str):
    if ext == ".pdf":
        return PyPDFLoader(file_path)
    elif ext in [".doc", ".docx"]:
        return Docx2txtLoader(file_path)
    elif ext == ".csv":
        return CSVLoader(file_path)
    elif ext in [".xls", ".xlsx"]:
        return UnstructuredExcelLoader(file_path)
    elif ext in [".png", ".jpg", ".jpeg"]:
        return UnstructuredImageLoader(file_path)
    elif ext == ".txt":
        return TextLoader(file_path)
    else:
        return TextLoader(file_path) # Fallback

def ingest_file(file_id: str):
    collection = get_collection(settings.COLLECTION_FILES)
    file_doc = collection.find_one({"_id": ObjectId(file_id)})
    
    if not file_doc:
        raise Exception("File not found in database")
    
    filename = file_doc.get("filename")
    file_data = file_doc.get("data") # Binary data
    ext = os.path.splitext(filename)[1].lower()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
        tmp_file.write(file_data)
        tmp_file_path = tmp_file.name
    
    try:
        loader = get_loader(tmp_file_path, ext)
        documents = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_documents(documents)
        
        embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
        
        vector_search = MongoDBAtlasVectorSearch.from_documents(
            documents=chunks,
            embedding=embeddings,
            collection=get_collection("vector_store"),
            index_name=settings.VECTOR_INDEX_NAME
        )
        
        return len(chunks)
    finally:
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
