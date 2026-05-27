import os
import re
from datetime import datetime, timezone

import certifi
from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

from src.pipeline.email_sender import send_email

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL") or os.getenv("mongo_URL")
DB_NAME = os.getenv("MONGO_DB_NAME", "fragrancetracker")
ALERTS_COLLECTION = os.getenv("ALERTS_COLLECTION", "alerts")
FRAGRANCES_COLLECTION = os.getenv("FRAGRANCES_COLLECTION", "fragrances")
LISTINGS_COLLECTION = os.getenv("REDDIT_LISTINGS_COLLECTION", "reddit_listings")
EVENTS_COLLECTION = os.getenv("ALERT_EVENTS_COLLECTION", "alert_events")


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


def _normalize(text):
    return re.sub(r"[^a-z0-9]+", " ", str(text or "").lower()).strip()


def _matches_target(listing, target_name):
    target = _normalize(target_name)
    if not target:
        return False

    haystack = " ".join(
        _normalize(listing.get(field))
        for field in ("brand", "frag_name", "raw_text", "post_title")
    )
    return target in haystack


def _deal_target_price(fragrance, threshold):
    avg = fragrance.get("weighted_avg_price")
    std_dev = fragrance.get("weighted_std_dev")
    if avg is None or std_dev is None:
        return None
    return float(avg) - (float(threshold or 0) * float(std_dev))


def _find_baseline_fragrance(db, target_name):
    normalized_target = _normalize(target_name)
    for fragrance in db[FRAGRANCES_COLLECTION].find({}, {"_id": 0}):
        reddit_name = _normalize(fragrance.get("reddit_name"))
        if normalized_target == reddit_name or normalized_target in reddit_name:
            return fragrance
    return None


def evaluate_alerts():
    client = _mongo_client()
    try:
        db = client[DB_NAME]
        alerts = list(db[ALERTS_COLLECTION].find({"active": {"$ne": False}}))
        if not alerts:
            print("No active alerts to evaluate")
            return {"alerts_checked": 0, "matches": 0, "events_upserted": 0}

        listings = list(db[LISTINGS_COLLECTION].find({}))
        print(f"Evaluating {len(alerts)} active alerts against {len(listings)} listings")

        now = datetime.now(timezone.utc)
        operations = []
        matches = 0

        for alert in alerts:
            alert_id = str(alert["_id"])
            alert_type = str(alert.get("type", "")).upper()
            target_name = alert.get("target_name")

            target_price = None
            if alert_type == "DEAL":
                baseline = _find_baseline_fragrance(db, target_name)
                if not baseline:
                    print(f"Skipping DEAL alert {alert_id}: no baseline found for {target_name}")
                    continue
                target_price = _deal_target_price(baseline, alert.get("threshold"))
                if target_price is None:
                    print(f"Skipping DEAL alert {alert_id}: missing baseline stats for {target_name}")
                    continue

            for listing in listings:
                if not _matches_target(listing, target_name):
                    continue

                price = listing.get("price_usd")
                if alert_type == "DEAL":
                    if price is None or float(price) > target_price:
                        continue
                    reason = f"price ${float(price):.2f} <= target ${target_price:.2f}"
                elif alert_type == "RARE":
                    reason = "matching listing found"
                else:
                    continue

                matches += 1
                listing_key = listing.get("listing_key")
                event_key = f"{alert_id}:{listing_key}"
                operations.append(
                    UpdateOne(
                        {"event_key": event_key},
                        {
                            "$set": {
                                "event_key": event_key,
                                "alert_id": ObjectId(alert_id),
                                "alert_type": alert_type,
                                "email": alert.get("email"),
                                "target_name": target_name,
                                "listing_key": listing_key,
                                "listing": {
                                    "brand": listing.get("brand"),
                                    "frag_name": listing.get("frag_name"),
                                    "price_usd": price,
                                    "post_url": listing.get("post_url"),
                                    "raw_text": listing.get("raw_text"),
                                },
                                "reason": reason,
                                "matched_at": now,
                                "notified_at": None,
                            },
                            "$setOnInsert": {"created_at": now},
                        },
                        upsert=True,
                    )
                )

        if not operations:
            print("No alert matches found")
            return {"alerts_checked": len(alerts), "matches": 0, "events_upserted": 0}

        result = db[EVENTS_COLLECTION].bulk_write(operations, ordered=False)
        summary = {
            "alerts_checked": len(alerts),
            "matches": matches,
            "events_upserted": result.upserted_count,
            "events_modified": result.modified_count,
        }
        print(f"Alert evaluation complete: {summary}")
        return summary
    finally:
        client.close()


def send_pending_alert_notifications(limit=25):
    client = _mongo_client()
    try:
        db = client[DB_NAME]
        events = list(
            db[EVENTS_COLLECTION]
            .find({"notified_at": None})
            .sort("created_at", 1)
            .limit(limit)
        )
        if not events:
            print("No pending alert notifications")
            return {"pending": 0, "sent": 0}

        sent = 0
        for event in events:
            listing = event.get("listing", {})
            fragrance_name = " ".join(
                part for part in [listing.get("brand"), listing.get("frag_name")] if part
            ) or event.get("target_name")
            price = listing.get("price_usd")
            price_text = f"${float(price):.2f}" if price is not None else "price unknown"

            html = (
                "<h1>The Scent Index Alert</h1>"
                f"<p><strong>{fragrance_name}</strong> matched your {event.get('alert_type')} alert.</p>"
                f"<p>{event.get('reason')}</p>"
                f"<p>Price: {price_text}</p>"
                f"<p><a href=\"{listing.get('post_url')}\">Open Reddit listing</a></p>"
                f"<blockquote>{listing.get('raw_text') or ''}</blockquote>"
            )
            text = (
                f"The Scent Index Alert\n\n"
                f"{fragrance_name} matched your {event.get('alert_type')} alert.\n"
                f"{event.get('reason')}\n"
                f"Price: {price_text}\n"
                f"Listing: {listing.get('post_url')}\n"
            )

            response = send_email(
                to_email=event["email"],
                subject=f"The Scent Index alert: {fragrance_name}",
                html=html,
                text=text,
                idempotency_key=event["event_key"],
            )
            db[EVENTS_COLLECTION].update_one(
                {"_id": event["_id"]},
                {
                    "$set": {
                        "notified_at": datetime.now(timezone.utc),
                        "resend_response": response,
                    }
                },
            )
            sent += 1
            print(f"Sent alert notification {sent}/{len(events)} to {event['email']}")

        return {"pending": len(events), "sent": sent}
    finally:
        client.close()


if __name__ == "__main__":
    print(evaluate_alerts())
