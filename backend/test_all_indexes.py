import os
from dotenv import load_dotenv
load_dotenv()
from app.core.db import get_db

db = get_db()
for coll_name in db.list_collection_names():
    coll = db[coll_name]
    try:
        indexes = list(coll.list_search_indexes())
        print(f"--- {coll_name} Search Indexes ---")
        for idx in indexes:
            print(idx)
    except Exception as e:
        print(f"Error listing search indexes for {coll_name}: {e}")
