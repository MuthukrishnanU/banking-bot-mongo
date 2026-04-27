print("Importing config...", flush=True)
from app.core.config import settings
print("Importing db...", flush=True)
from app.core.db import get_collection
print("Importing ingestion...", flush=True)
from app.services.ingestion import ingest_file
print("Importing query...", flush=True)
from app.services.query import transcribe_audio, get_rag_response
print("All imports successful!", flush=True)
