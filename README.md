# Multilingual Banking RAG Chatbot

This project is a RAG-based chatbot for banking policies, using MongoDB Atlas as both the document source and vector store.

## Features
- **Binary Ingestion**: Fetches documents stored as binary data in MongoDB Atlas.
- **Support for Multi-formats**: PDF, DOCX, XLSX, images, etc.
- **DeepEval Tracing**: Monitors latency, faithfulness, and relevancy.
- **Multilingual Support**: Supports text and audio input in any language via OpenAI Whisper and GPT-3.5/4.
- **Semantic Caching**: Reduces token usage by checking the vector DB for cached responses first.
- **Premium UI**: Modern Next.js interface with real-time metrics display.

## Prerequisites
- MongoDB Atlas cluster with Vector Search enabled.
- OpenAI API Key.

## Setup

1. **Environment Variables**:
   Create a `.env` file in the `backend` directory:
   ```env
   MONGODB_URI=your_mongodb_atlas_uri
   DB_NAME=banking_bot
   COLLECTION_FILES=policy_files
   OPENAI_API_KEY=your_openai_api_key
   VECTOR_INDEX_NAME=vector_index
   ```

2. **Dockerization Steps**:

### Build and Run Locally
```bash
docker-compose up --build
```

### Push to Docker Hub
1. **Login to Docker Hub**:
```bash
docker login
```

2. **Tag and Push Backend**:
```bash
docker build -t your-username/banking-bot-backend ./backend
docker push your-username/banking-bot-backend
```

3. **Tag and Push Frontend**:
```bash
docker build -t your-username/banking-bot-frontend ./frontend
docker push your-username/banking-bot-frontend
```

## MongoDB Vector Search Index
Ensure you have a Search Index defined for your `vector_store` and `semantic_cache` collections with the following JSON (example for GPT embeddings):
```json
{
  "fields": [
    {
      "numDimensions": 1536,
      "path": "embedding",
      "similarity": "cosine",
      "type": "vector"
    }
  ]
}
```
