from pymongo import MongoClient
from pymongo.errors import PyMongoError
import os

from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL") or os.getenv("mongo_URL") or "mongodb://localhost:27017"
DB_NAME = "fragrancetracker"

options = {
    "serverSelectionTimeoutMS": 5000,
    "connectTimeoutMS": 5000,
    "socketTimeoutMS": 5000,
}
if MONGO_URL.startswith("mongodb+srv://") or os.getenv("MONGO_TLS") == "true":
    import certifi

    options["tlsCAFile"] = certifi.where()

try:
    client = MongoClient(MONGO_URL, **options)
    client.admin.command("ping")
    db = client[DB_NAME]
    count = db.fragrances.count_documents({})
    print("MongoDB connection OK")
    print(f"Database: {DB_NAME}")
    print(f"Fragrances count: {count}")
    sample = db.fragrances.find_one({}, {"_id": 0})
    print(f"Sample: {sample}")
except PyMongoError as exc:
    print("MongoDB connection failed")
    print(exc)
    message = str(exc)
    if "SSL handshake failed" in message or "TLSV1_ALERT_INTERNAL_ERROR" in message:
        print(
            "Hint: Atlas commonly returns this when your current IP is not "
            "allowed under Network Access, or while the cluster is still resuming."
        )
    raise SystemExit(1)
