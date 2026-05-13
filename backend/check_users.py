import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = "mongodb+srv://dbUser:dbPwd123@cluster0.l5s8qju.mongodb.net/?appName=Cluster0&tlsAllowInvalidCertificates=true"
DB_NAME = "bankingPolicyDB"
COLLECTION_USERS = "bankingUserIds"

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
collection = db[COLLECTION_USERS]

users = list(collection.find())
print(f"Found {len(users)} users in {COLLECTION_USERS}")
for user in users:
    print(f"User ID: {user.get('userId')}, Password: {user.get('userPwd')}")
