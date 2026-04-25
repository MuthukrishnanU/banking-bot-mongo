from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "banking_bot")
    COLLECTION_FILES: str = os.getenv("COLLECTION_FILES", "policy_files")
    COLLECTION_METRICS: str = os.getenv("COLLECTION_METRICS", "metrics")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    VECTOR_INDEX_NAME: str = os.getenv("VECTOR_INDEX_NAME", "vector_index")

settings = Settings()
