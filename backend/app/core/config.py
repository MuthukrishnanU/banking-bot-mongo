from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    MONGODB_URI: str = os.getenv("MONGODB_URI")
    DB_NAME: str = os.getenv("DB_NAME")
    COLLECTION_FILES: str = os.getenv("COLLECTION_FILES")
    COLLECTION_METRICS: str = os.getenv("COLLECTION_METRICS")
    COLLECTION_USERS: str = os.getenv("COLLECTION_USERS")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    VECTOR_INDEX_NAME: str = os.getenv("VECTOR_INDEX_NAME")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    MISTRALAI_API_KEY: str = os.getenv("MISTRALAI_API_KEY")
    HUGGINGFACEHUB_API_TOKEN: str = os.getenv("HUGGINGFACEHUB_API_TOKEN")

settings = Settings()
