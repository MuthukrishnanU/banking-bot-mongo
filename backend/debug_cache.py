"""Diagnostic script to debug semantic cache vector search issues."""
import os
from dotenv import load_dotenv
load_dotenv()

from app.core.db import get_collection
from app.core.config import settings
from langchain_openai import OpenAIEmbeddings

cache_collection = get_collection("semantic_cache")

# 1. Check document count
doc_count = cache_collection.count_documents({})
print(f"\n[1] Documents in semantic_cache: {doc_count}")

# 2. Check if documents have the 'embedding' field
if doc_count > 0:
    sample = cache_collection.find_one()
    has_embedding = "embedding" in sample
    print(f"[2] Sample document has 'embedding' field: {has_embedding}")
    if has_embedding:
        emb = sample["embedding"]
        print(f"    Embedding type: {type(emb).__name__}, length: {len(emb) if isinstance(emb, list) else 'N/A'}")
    print(f"    Document keys: {list(sample.keys())}")
else:
    print("[2] No documents to check — cache is empty!")

# 3. Check if the Atlas Vector Search index exists
print("\n[3] Checking Atlas Search indexes on semantic_cache...")
try:
    indexes = list(cache_collection.list_search_indexes())
    if not indexes:
        print("    *** NO VECTOR SEARCH INDEXES FOUND! This is the problem. ***")
        print("    Run: python create_cache_index.py")
    else:
        for idx in indexes:
            print(f"    Index name: {idx.get('name')}")
            print(f"    Status: {idx.get('status', 'unknown')}")
            print(f"    Queryable: {idx.get('queryable', 'unknown')}")
            print(f"    Definition: {idx.get('latestDefinition', idx.get('definition', 'N/A'))}")
except Exception as e:
    print(f"    Error listing indexes: {e}")

# 4. Try a raw $vectorSearch aggregation (bypassing LangChain)
if doc_count > 0:
    print("\n[4] Testing raw $vectorSearch aggregation...")
    try:
        embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
        test_query = "test query"
        query_vector = embeddings.embed_query(test_query)
        
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "cache_index",
                    "path": "embedding",
                    "queryVector": query_vector,
                    "numCandidates": 10,
                    "limit": 3
                }
            },
            {
                "$project": {
                    "query": 1,
                    "response": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        
        results = list(cache_collection.aggregate(pipeline))
        print(f"    Raw $vectorSearch returned {len(results)} results")
        for r in results:
            print(f"    - query: {r.get('query', 'N/A')[:80]}, score: {r.get('score', 'N/A')}")
    except Exception as e:
        print(f"    *** $vectorSearch FAILED: {e} ***")
        if "index not found" in str(e).lower() or "no such" in str(e).lower():
            print("    >>> The 'cache_index' vector search index does not exist!")
            print("    >>> Run: python create_cache_index.py")
        elif "queryable" in str(e).lower() or "not ready" in str(e).lower():
            print("    >>> The index exists but is still building. Wait a few minutes.")
