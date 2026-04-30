"""Test script to debug LangChain's similarity_search_with_score."""
import os
from dotenv import load_dotenv
load_dotenv()

from app.core.db import get_collection
from app.core.config import settings
from langchain_openai import OpenAIEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch

def test_cache_search():
    embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
    cache_collection = get_collection("semantic_cache")
    
    print("\n--- Testing with default settings ---")
    cache_store = MongoDBAtlasVectorSearch(
        collection=cache_collection,
        embedding=embeddings,
        index_name="cache_index"
    )
    
    query = "What is the contact information email ID?"
    results = cache_store.similarity_search_with_score(query, k=1)
    print(f"Results: {results}")

    print("\n--- Testing with explicit text_key='query' ---")
    cache_store_2 = MongoDBAtlasVectorSearch(
        collection=cache_collection,
        embedding=embeddings,
        index_name="cache_index",
        text_key="query"
    )
    results_2 = cache_store_2.similarity_search_with_score(query, k=1)
    print(f"Results: {results_2}")

    if results_2:
        doc, score = results_2[0]
        print(f"Top result score: {score}")
        print(f"Top result content: {doc.page_content}")

if __name__ == "__main__":
    test_cache_search()
