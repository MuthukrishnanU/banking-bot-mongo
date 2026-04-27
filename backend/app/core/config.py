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
