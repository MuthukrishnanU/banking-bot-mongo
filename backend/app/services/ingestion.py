import os
import tempfile
import base64
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
    
    # The user's image shows docName and docStr are inside a 'docs' array
    if "docs" not in file_doc or not file_doc["docs"]:
        raise Exception("No documents found in the file record")
        
    doc = file_doc["docs"][0]
    filename = doc.get("docName", "unknown.pdf")
    doc_str = doc.get("docStr", "")
    
    try:
        file_data = base64.b64decode(doc_str)
    except Exception as e:
        raise Exception(f"Failed to decode document data: {str(e)}")

    # Add extension if missing from filename for loader selection
    if "." not in filename:
        doc_type = doc.get("docType", "pdf").lower()
        filename = f"{filename}.{doc_type}"

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
