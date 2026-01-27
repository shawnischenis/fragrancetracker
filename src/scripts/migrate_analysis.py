import pandas as pd
from pymongo import MongoClient
import os

CSV_PATH = 'data/analysis/reddit_vs_jomashop_analysis.csv'
MONGO_URI = 'mongodb://localhost:27017/'
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
    client = MongoClient(MONGO_URI)
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
