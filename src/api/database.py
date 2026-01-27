from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = "fragrancetracker"

class Database:
    client: AsyncIOMotorClient = None
    
    def connect(self):
        import certifi
        self.client = AsyncIOMotorClient(MONGO_URL, tlsCAFile=certifi.where())
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
