import os
from dotenv import load_dotenv
load_dotenv()
from app.core.db import get_collection
from pymongo.operations import SearchIndexModel

collection = get_collection("semantic_cache")

search_index_model = SearchIndexModel(
    definition={
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": 1536,
                "similarity": "cosine"
            }
        ]
    },
    name="cache_index",
    type="vectorSearch"
)

try:
    result = collection.create_search_index(model=search_index_model)
    print("Created semantic cache index:", result)
except Exception as e:
    print("Error creating semantic cache index:", e)
