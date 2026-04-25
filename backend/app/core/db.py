from pymongo import MongoClient
from .config import settings

client = MongoClient(settings.MONGODB_URI)
db = client[settings.DB_NAME]

def get_db():
    return db

def get_collection(name: str):
    return db[name]
