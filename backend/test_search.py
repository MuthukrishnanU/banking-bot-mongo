import os
from dotenv import load_dotenv
load_dotenv()
from app.core.db import get_collection
from app.core.config import settings
from langchain_openai import OpenAIEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch

embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
vector_store = MongoDBAtlasVectorSearch(
    collection=get_collection("vector_store"),
    embedding=embeddings,
    index_name=settings.VECTOR_INDEX_NAME
)

query = "What is the policy?"
results = vector_store.similarity_search(query, k=4)
print(f"Found {len(results)} results")
for i, res in enumerate(results):
    print(f"--- Result {i+1} ---")
    print(res.page_content[:200])
