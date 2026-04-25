import time
import os
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain.chains import RetrievalQA
from app.core.db import get_collection, get_db
from app.core.config import settings
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric, ContextualRelevancyMetric, ContextualPrecisionMetric
from deepeval.test_case import LLMTestCase
from deepeval.tracing import trace

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def transcribe_audio(audio_file_path: str):
    with open(audio_file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )
    return transcript.text

from langchain_community.callbacks import get_openai_callback

def get_rag_response(query_text: str):
    start_time = time.time()
    embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
    
    # 1. Semantic Cache Check (To reduce token usage)
    cache_collection = get_collection("semantic_cache")
    cache_store = MongoDBAtlasVectorSearch(
        collection=cache_collection,
        embedding=embeddings,
        index_name="cache_index"
    )
    
    cache_results = cache_store.similarity_search_with_score(query_text, k=1)
    if cache_results and cache_results[0][1] > 0.95: # High similarity threshold
        response = cache_results[0][0].metadata.get("response")
        latency = time.time() - start_time
        log_metrics(query_text, response, [], latency, tokens=0, cached=True)
        return {"response": response, "sources": [], "latency": latency, "cached": True}

    # 2. RAG retrieval
    vector_store = MongoDBAtlasVectorSearch(
        collection=get_collection("vector_store"),
        embedding=embeddings,
        index_name=settings.VECTOR_INDEX_NAME
    )
    
    with get_openai_callback() as cb:
        qa_chain = RetrievalQA.from_chain_type(
            llm=ChatOpenAI(model="gpt-3.5-turbo", openai_api_key=settings.OPENAI_API_KEY),
            chain_type="stuff",
            retriever=vector_store.as_retriever(),
            return_source_documents=True
        )
        
        rag_result = qa_chain.invoke({"query": query_text})
        response = rag_result["result"]
        source_documents = [doc.page_content for doc in rag_result["source_documents"]]
        tokens = cb.total_tokens

    latency = time.time() - start_time
    
    # DeepEval metrics (only if sources found)
    metrics = None
    if source_documents:
        metrics = evaluate_rag(query_text, response, source_documents)
    
    # Update Semantic Cache
    cache_collection.insert_one({
        "query": query_text,
        "response": response,
        "embedding": embeddings.embed_query(query_text) # This is manual if not using MongoDBAtlasVectorSearch.add_texts
    })
    
    # Log to MongoDB
    log_metrics(query_text, response, source_documents, latency, metrics, tokens=tokens)
    
    return {
        "response": response,
        "sources": source_documents,
        "latency": latency,
        "metrics": metrics,
        "tokens": tokens
    }

def evaluate_rag(query, response, contexts):
    # For speed in demo, we might skip full eval or use small models
    # But user requested these specific metrics
    test_case = LLMTestCase(
        input=query,
        actual_output=response,
        retrieval_context=contexts
    )
    
    # Initialize metrics (requires OPENAI_API_KEY in env)
    f_metric = FaithfulnessMetric(threshold=0.7)
    ar_metric = AnswerRelevancyMetric(threshold=0.7)
    cr_metric = ContextualRelevancyMetric(threshold=0.7)
    cp_metric = ContextualPrecisionMetric(threshold=0.7)
    
    f_metric.measure(test_case)
    ar_metric.measure(test_case)
    cr_metric.measure(test_case)
    cp_metric.measure(test_case)
    
    return {
        "faithfulness": f_metric.score,
        "answer_relevancy": ar_metric.score,
        "contextual_relevancy": cr_metric.score,
        "contextual_precision": cp_metric.score
    }

def log_metrics(query, response, sources, latency, metrics=None, tokens=0, cached=False):
    collection = get_collection(settings.COLLECTION_METRICS)
    log_entry = {
        "query": query,
        "response": response,
        "sources_count": len(sources),
        "latency": latency,
        "token_usage": tokens,
        "metrics": metrics,
        "cached": cached,
        "timestamp": time.time()
    }
    collection.insert_one(log_entry)
