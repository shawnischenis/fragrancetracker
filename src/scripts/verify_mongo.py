from pymongo import MongoClient
import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = "fragrancetracker"

client = MongoClient(MONGO_URL)
db = client[DB_NAME]
count = db.fragrances.count_documents({})
print(f"Fragrances count: {count}")
sample = db.fragrances.find_one()
print(f"Sample: {sample}")
