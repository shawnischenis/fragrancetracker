import pandas as pd
from pymongo import MongoClient
import os

from dotenv import load_dotenv
load_dotenv()

CSV_PATH = 'data/cleaned/price_comparison.csv'
MONGO_URI = os.getenv('MONGO_URL') or os.getenv('mongo_URL')
if not MONGO_URI:
    raise ValueError("MONGO_URL not found in environment variables")
DB_NAME = 'fragrancetracker'
COLLECTION_NAME = 'fragrances'

def migrate():
    # 1. Read CSV
    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found.")
        return
    
    df = pd.read_csv(CSV_PATH)
    
    # 2. Transform for Mongo
    # Convert regex mismatches or NaNs where appropriate
    # Mongo handles NaNs but sometimes None is better.
    records = df.where(pd.notnull(df), None).to_dict(orient='records')
    
    # 3. Connect to Mongo
    options = {}
    if MONGO_URI.startswith("mongodb+srv://") or os.getenv("MONGO_TLS") == "true":
        import certifi

        options["tlsCAFile"] = certifi.where()
    client = MongoClient(MONGO_URI, **options)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    
    # 4. Insert (Upsert based on reddit_name to avoid dupes)
    count = 0
    for record in records:
        # Use reddit_name as unique identifier for now
        filter_query = {'reddit_name': record['reddit_name']}
        update_query = {'$set': record}
        
        result = collection.update_one(filter_query, update_query, upsert=True)
        if result.upserted_id or result.modified_count > 0:
            count += 1
            
    print(f"Successfully migrated/updated {count} records to MongoDB '{DB_NAME}.{COLLECTION_NAME}'.")

if __name__ == "__main__":
    migrate()
