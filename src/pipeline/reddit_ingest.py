import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import certifi
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

from src.pipeline.reddit_cleaning import clean_reddit_post_with_o4_mini
from src.scraping.reddit_scraper import scrape_reddit

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL") or os.getenv("mongo_URL")
DB_NAME = os.getenv("MONGO_DB_NAME", "fragrancetracker")
POSTS_COLLECTION_NAME = os.getenv("REDDIT_POSTS_COLLECTION", "reddit_posts")
LISTINGS_COLLECTION_NAME = os.getenv("REDDIT_LISTINGS_COLLECTION", "reddit_listings")


def _mongo_client():
    if not MONGO_URL:
        raise ValueError("MONGO_URL must be set")

    options = {
        "serverSelectionTimeoutMS": 5000,
        "connectTimeoutMS": 5000,
        "socketTimeoutMS": 5000,
    }
    if MONGO_URL.startswith("mongodb+srv://") or os.getenv("MONGO_TLS") == "true":
        options["tlsCAFile"] = certifi.where()

    client = MongoClient(MONGO_URL, **options)
    client.admin.command("ping")
    return client


def scrape_and_store_recent_posts(limit=10, clean=True):
    print(f"Starting Reddit scrape with limit={limit}")
    df = scrape_reddit(limit=limit)
    print(f"Scraped {len(df)} posts from Reddit")
    if df.empty:
        return {"scraped": 0, "upserted": 0, "modified": 0}

    scraped_at = datetime.now(timezone.utc)
    records = df.where(df.notnull(), None).to_dict(orient="records")

    post_operations = []
    listing_operations = []
    for index, record in enumerate(records, start=1):
        url = record.get("url")
        if not url:
            print(f"Skipping post {index}/{len(records)} because it has no URL")
            continue

        title = record.get("title") or "(untitled)"
        print(f"Processing post {index}/{len(records)}: {title[:120]}")

        if clean:
            print(f"Cleaning post {index}/{len(records)} with o4-mini")
            cleaned_listings = clean_reddit_post_with_o4_mini(record)
            print(f"Extracted {len(cleaned_listings)} listings from post {index}/{len(records)}")
        else:
            cleaned_listings = []

        record["scraped_at"] = scraped_at
        record["source"] = "reddit"
        record["subreddit"] = "fragranceswap"
        record["cleaned_with"] = os.getenv("OPENAI_CLEANING_MODEL", "o4-mini") if clean else None
        record["cleaned_listing_count"] = len(cleaned_listings)

        post_operations.append(
            UpdateOne(
                {"url": url},
                {
                    "$set": record,
                    "$setOnInsert": {"created_in_db_at": scraped_at},
                },
                upsert=True,
            )
        )

        for index, listing in enumerate(cleaned_listings):
            listing["post_url"] = url
            listing["post_title"] = record.get("title")
            listing["post_date"] = record.get("date")
            listing["scraped_at"] = scraped_at
            listing["cleaned_with"] = record["cleaned_with"]
            listing_key = f"{url}#{index}"
            listing_operations.append(
                UpdateOne(
                    {"listing_key": listing_key},
                    {
                        "$set": listing,
                        "$setOnInsert": {
                            "listing_key": listing_key,
                            "created_in_db_at": scraped_at,
                        },
                    },
                    upsert=True,
                )
            )

    if not post_operations:
        return {"scraped": len(records), "posts_upserted": 0, "posts_modified": 0, "listings_upserted": 0, "listings_modified": 0}

    print(f"Writing {len(post_operations)} posts to MongoDB collection {POSTS_COLLECTION_NAME}")
    client = _mongo_client()
    try:
        db = client[DB_NAME]
        post_result = db[POSTS_COLLECTION_NAME].bulk_write(post_operations, ordered=False)
        listing_result = None
        if listing_operations:
            print(f"Writing {len(listing_operations)} listings to MongoDB collection {LISTINGS_COLLECTION_NAME}")
            listing_result = db[LISTINGS_COLLECTION_NAME].bulk_write(listing_operations, ordered=False)
        summary = {
            "scraped": len(records),
            "posts_upserted": post_result.upserted_count,
            "posts_modified": post_result.modified_count,
            "listings_extracted": len(listing_operations),
            "listings_upserted": listing_result.upserted_count if listing_result else 0,
            "listings_modified": listing_result.modified_count if listing_result else 0,
        }
        print(f"Ingestion complete: {summary}")
        return summary
    finally:
        client.close()


if __name__ == "__main__":
    limit = int(os.getenv("REDDIT_SCRAPE_LIMIT", "10"))
    print(scrape_and_store_recent_posts(limit=limit))
