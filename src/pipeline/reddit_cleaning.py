import json
import os
import re
import time

from dotenv import load_dotenv
from openai import AuthenticationError, OpenAI, OpenAIError

load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_CLEANING_MODEL", "o4-mini")
MAX_RETRIES = int(os.getenv("OPENAI_CLEANING_MAX_RETRIES", "3"))
SLEEP_BETWEEN_CALLS = float(os.getenv("OPENAI_CLEANING_RETRY_SLEEP", "1"))


def _client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY must be set")
    return OpenAI(api_key=api_key)


def _extract_json(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\[.*\]|\{.*\})", text, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(1))


def clean_reddit_post_with_o4_mini(post):
    title = post.get("title") or ""
    body = post.get("body") or ""
    author = post.get("author")
    flair = post.get("flair")

    if "[WTS]" not in title.upper():
        return []

    prompt = f"""
Extract fragrance sale listings from this Reddit r/fragranceswap post.

Title:
{title}

Body:
{body}

Return only a JSON array. Each object must have:
- author: {json.dumps(author)}
- flair: {json.dumps(flair)}
- brand: string or null
- frag_name: string or null
- size_ml: number or null
- price_usd: number or null
- fill_percent: number from 0 to 100 or null
- status: "SOLD", "AVAILABLE", "LISTED", or null
- raw_text: the source line or phrase used for the extraction

Rules:
- Split multiple fragrances into separate objects.
- Ignore timestamps, shipping notes, payment notes, photos, and unrelated conversation.
- Mark strikethrough items such as ~~text~~ as SOLD.
- Treat CONUS, G&S, F&F, shipped, add-on, bottle, partial, and tester as context, not fragrance names.
- Return [] if there are no fragrance sale listings.
"""

    client = _client()
    for attempt in range(MAX_RETRIES):
        try:
            response = client.responses.create(
                model=OPENAI_MODEL,
                input=prompt,
            )
            data = _extract_json(response.output_text)
            if not isinstance(data, list):
                raise ValueError("OpenAI response was not a JSON array")
            return data
        except AuthenticationError as exc:
            raise RuntimeError(
                "OpenAI authentication failed. Check that OPENAI_API_KEY in .env "
                "is current, saved, and has access to the requested model."
            ) from exc
        except OpenAIError as exc:
            if attempt == MAX_RETRIES - 1:
                raise RuntimeError(f"OpenAI cleaning failed with {OPENAI_MODEL}: {exc}") from exc
            time.sleep(SLEEP_BETWEEN_CALLS)
        except Exception:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(SLEEP_BETWEEN_CALLS)

    return []
