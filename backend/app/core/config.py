from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb+srv://dbUser:dbPwd123@cluster0.l5s8qju.mongodb.net/?appName=Cluster0&tlsAllowInvalidCertificates=true")
    DB_NAME: str = os.getenv("DB_NAME", "bankingPolicyDB")
    COLLECTION_FILES: str = os.getenv("COLLECTION_FILES", "bankingPolicyDocs")
    COLLECTION_METRICS: str = os.getenv("COLLECTION_METRICS", "bankingPolicyMetricsValues")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "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")
    VECTOR_INDEX_NAME: str = os.getenv("VECTOR_INDEX_NAME", "bankingPolicyVectorDB")

settings = Settings()
