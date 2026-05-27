from motor.motor_asyncio import AsyncIOMotorClient
import os
from pymongo.errors import PyMongoError

from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL") or os.getenv("mongo_URL") or "mongodb://localhost:27017"
DB_NAME = "fragrancetracker"

class Database:
    client: AsyncIOMotorClient = None
    
    async def connect(self):
        import certifi

        options = {
            "serverSelectionTimeoutMS": 5000,
            "connectTimeoutMS": 5000,
            "socketTimeoutMS": 5000,
        }
        if MONGO_URL.startswith("mongodb+srv://") or os.getenv("MONGO_TLS") == "true":
            options["tlsCAFile"] = certifi.where()

        self.client = AsyncIOMotorClient(MONGO_URL, **options)
        try:
            await self.client.admin.command("ping")
        except PyMongoError as exc:
            message = str(exc)
            if "SSL handshake failed" in message or "TLSV1_ALERT_INTERNAL_ERROR" in message:
                raise RuntimeError(
                    "MongoDB TLS handshake failed. If this is MongoDB Atlas, check that "
                    "the cluster is active and your current IP is allowed in Atlas "
                    "Network Access."
                ) from exc
            raise
        print("Connected to MongoDB")
        
    def close(self):
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")
            
    def get_db(self):
        return self.client[DB_NAME]

db = Database()

async def get_database():
    return db.get_db()
