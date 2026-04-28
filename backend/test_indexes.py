import os
from dotenv import load_dotenv
load_dotenv()
from app.core.db import get_collection, db

collection = get_collection("vector_store")
try:
    indexes = list(collection.list_search_indexes())
    print("Search Indexes:")
    for idx in indexes:
        print(idx)
except Exception as e:
    print("Error listing search indexes:", e)

try:
    print("Regular Indexes:")
    for idx in collection.list_indexes():
        print(idx)
except Exception as e:
    print("Error listing regular indexes:", e)
