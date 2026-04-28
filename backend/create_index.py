import os
from dotenv import load_dotenv
load_dotenv()
from app.core.db import get_collection
from app.core.config import settings
try:
    from pymongo.operations import SearchIndexModel
except ImportError:
    print("pymongo version doesn't support SearchIndexModel")
    import sys; sys.exit(1)

collection = get_collection("vector_store")

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
    name=settings.VECTOR_INDEX_NAME,
    type="vectorSearch"
)

try:
    result = collection.create_search_index(model=search_index_model)
    print("Created index:", result)
except Exception as e:
    print("Error creating search index:", e)
