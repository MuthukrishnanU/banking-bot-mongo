import time
import os
import tiktoken
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_classic.chains import RetrievalQA
from app.core.db import get_collection, get_db
from app.core.config import settings
# from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric, ContextualRelevancyMetric, ContextualPrecisionMetric
# from deepeval.test_case import LLMTestCase
# from deepeval.tracing import trace

client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Supported LLM models
SUPPORTED_MODELS = [
    "gpt-3.5-turbo",
    "gpt-4o-mini",
    "gemini-2.5-flash",
    "mistral-small-latest",
    "meta-llama/Meta-Llama-3-8B-Instruct",
]

def get_llm(model_name: str = "gpt-3.5-turbo", temperature: float = 0.7):
    """Instantiate the correct LangChain chat model based on user selection."""

    # --- OpenAI models ---
    if model_name in ("gpt-3.5-turbo", "gpt-4o-mini"):
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=settings.OPENAI_API_KEY,
        )

    # --- Google Gemini ---
    if model_name.startswith("gemini"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=settings.GOOGLE_API_KEY,
        )

    # --- Mistral (via Mistral API) ---
    if model_name.startswith("mistral"):
        from langchain_mistralai import ChatMistralAI
        return ChatMistralAI(
            model=model_name,
            temperature=temperature,
            mistral_api_key=settings.MISTRALAI_API_KEY,
        )

    # --- Llama / other HuggingFace models ---
    if "llama" in model_name.lower() or "meta-llama" in model_name.lower():
        #from langchain_huggingface import HuggingFaceEndpoint
        from langchain_community.chat_models.huggingface import ChatHuggingFace
        from langchain_community.llms import HuggingFaceEndpoint
        llm_hf = HuggingFaceEndpoint(
            repo_id=model_name,
            task="conversational",
            temperature=temperature,
            huggingfacehub_api_token=settings.HUGGINGFACEHUB_API_TOKEN,
        )
        return ChatHuggingFace(llm=llm_hf)

    # Fallback to OpenAI gpt-3.5-turbo
    return ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=temperature,
        openai_api_key=settings.OPENAI_API_KEY,
    )


def estimate_tokens(text: str) -> int:
    """Estimate token count using tiktoken cl100k_base encoding.
    This encoding is a reasonable approximation for all modern LLMs."""
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        # Rough fallback: ~4 chars per token
        return len(text) // 4


def count_tokens_for_rag(query_text: str, context_docs: list, response_text: str) -> int:
    """Estimate total tokens (prompt + completion) for a RAG call."""
    # Build an approximation of the full prompt: query + retrieved context
    context_text = "\n".join(context_docs)
    prompt_text = f"{query_text}\n{context_text}"
    prompt_tokens = estimate_tokens(prompt_text)
    completion_tokens = estimate_tokens(response_text)
    return prompt_tokens + completion_tokens


def transcribe_audio(audio_file_path: str):
    with open(audio_file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )
    return transcript.text

from langchain_community.callbacks import get_openai_callback

def get_rag_response(query_text: str, user_id: str = None, model_name: str = "gpt-3.5-turbo", temperature: float = 0.7):
    start_time = time.time()
    embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
    
    # 1. Semantic Cache Check (To reduce token usage)
    cache_collection = get_collection("semantic_cache")
    cache_store = MongoDBAtlasVectorSearch(
        collection=cache_collection,
        embedding=embeddings,
        index_name="cache_index",
        text_key="query"
    )
    
    cache_results = cache_store.similarity_search_with_score(query_text, k=1)
    if cache_results and cache_results[0][1] > 0.95: # High similarity threshold
        doc = cache_results[0][0]
        response = doc.page_content # In MongoDBAtlasVectorSearch, page_content is the text
        # If response was stored in metadata instead:
        if not response or response == query_text:
            response = doc.metadata.get("response")
            
        latency = time.time() - start_time
        # Try to get _id from metadata or query again
        cache_id = str(doc.metadata.get("_id"))
        if not cache_id or cache_id == "None":
            cached_doc = cache_collection.find_one({"query": query_text})
            cache_id = str(cached_doc["_id"]) if cached_doc else None

        log_metrics(query_text, response, [], latency, metrics=None, tokens=0, cached=True, user_id=user_id, model_name=model_name)
        return {"response": response, "sources": [], "latency": latency, "cached": True, "query_id": cache_id}

    # 2. RAG retrieval
    vector_store = MongoDBAtlasVectorSearch(
        collection=get_collection("vector_store"),
        embedding=embeddings,
        index_name=settings.VECTOR_INDEX_NAME
    )

    # Instantiate the selected LLM
    llm = get_llm(model_name, temperature)
    is_openai = model_name in ("gpt-3.5-turbo", "gpt-4o-mini")
    tokens = 0

    if is_openai:
        # Use OpenAI callback for token tracking
        with get_openai_callback() as cb:
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=vector_store.as_retriever(),
                return_source_documents=True
            )
            rag_result = qa_chain.invoke({"query": query_text})
            response = rag_result["result"]
            source_documents = [doc.page_content for doc in rag_result["source_documents"]]
            tokens = cb.total_tokens
    else:
        # Non-OpenAI models: use tiktoken estimation for token tracking
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(),
            return_source_documents=True
        )
        rag_result = qa_chain.invoke({"query": query_text})
        response = rag_result["result"]
        source_documents = [doc.page_content for doc in rag_result["source_documents"]]
        # Estimate tokens from query + retrieved context + response
        tokens = count_tokens_for_rag(query_text, source_documents, response)

    latency = time.time() - start_time
    
    # DeepEval metrics (only if sources found)
    metrics = None
    if source_documents:
        metrics = evaluate_rag(query_text, response, source_documents)
    
    # Update Semantic Cache
    cache_entry = {
        "query": query_text,
        "response": response,
        "tokens": tokens,
        "model": model_name,
        "latency": latency,
        "temperature": temperature,
        "timestamp": time.time(),
        "userId": user_id or "NA",
        "embedding": embeddings.embed_query(query_text)
    }
    result = cache_collection.insert_one(cache_entry)
    cache_id = str(result.inserted_id)
    
    # Log to MongoDB
    log_metrics(query_text, response, source_documents, latency, metrics, tokens=tokens, user_id=user_id, model_name=model_name)
    
    return {
        "response": response,
        "sources": source_documents,
        "latency": latency,
        "metrics": metrics,
        "tokens": tokens,
        "model": model_name,
        "temperature": temperature,
        "query_id": cache_id
    }

def evaluate_rag(query, response, contexts):
    return {
        "faithfulness": 0.0,
        "answer_relevancy": 0.0,
        "contextual_relevancy": 0.0,
        "contextual_precision": 0.0
    }

def log_metrics(query, response, sources, latency, metrics=None, tokens=0, cached=False, user_id=None, model_name="gpt-3.5-turbo"):
    collection = get_collection(settings.COLLECTION_METRICS)
    log_entry = {
        "query": query,
        "response": response,
        "sources_count": len(sources),
        "latency": latency,
        "token_usage": tokens,
        "metrics": metrics,
        "cached": cached,
        "userId": user_id or "NA",
        "model": model_name,
        "timestamp": time.time()
    }
    collection.insert_one(log_entry)
