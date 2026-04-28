import os
from dotenv import load_dotenv
load_dotenv()
from app.core.db import get_collection

collection = get_collection("vector_store")
doc = collection.find_one()
if doc:
    print("Found doc keys:", doc.keys())
    if "text" in doc:
        print("text length:", len(doc["text"]))
    else:
        print("text key not found!")
    
    if "embedding" in doc:
        print("embedding length:", len(doc["embedding"]))
    else:
        print("embedding key not found!")
    
    if "page_content" in doc:
        print("page_content length:", len(doc["page_content"]))
else:
    print("No documents in vector_store!")
