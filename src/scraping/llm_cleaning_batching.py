import pandas as pd
import re
from openai import OpenAI
import json
import time

# === CONFIG ===
client = OpenAI(api_key="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")
INPUT_CSV = "data/raw/frag_posts.csv"
OUTPUT_CSV = "data/cleaned/frag_posts_llm_cleaned.json"
MAX_RETRIES = 3
SLEEP_BETWEEN_CALLS = 1  # seconds

BRANDS = [
    "Creed", "Dior", "Chanel", "Tom Ford", "Maison Francis Kurkdjian", "MFK",
    "Byredo", "Amouage", "Xerjoff", "Le Labo", "Guerlain", "YSL",
    "Armani", "Parfums de Marly", "PDM", "Acqua di Parma", "Afnan", "Al Haramain Perfumes",
    "Al-Rehab", "Ariana Grande", "Armaf", "Avon", "Azzaro", "BDK Parfums",
    "BORNTOSTANDOUT®", "Bath & Body Works", "Bond No 9", "Britney Spears", "Burberry",
    "Bvlgari", "By Kilian", "Cacharel", "Calvin Klein", "Carolina Herrera", "Chopard",
    "Christian Dior", "Clive Christian", "Coach", "Davidoff", "Diptyque", "Dolce & Gabbana",
    "Dunhill", "Elie Saab", "Elizabeth Arden", "Estée Lauder", "Fendi", "Ferrari",
    "Giorgio Armani", "Givenchy", "Gucci", "Hermès", "Hugo Boss", "Jean Paul Gaultier",
    "Jimmy Choo", "Jo Malone London", "Jo Malone", "Juicy Couture", "Kenzo", "Kilian",
    "Lacoste", "Lancôme", "Loewe", "Louis Vuitton", "Mancera", "Mugler", "Montale",
    "Nina Ricci", "Nishane", "Oud Al Qasr", "Penhaligon's", "Perry Ellis", "Prada",
    "Ralph Lauren", "Rochas", "Salvatore Ferragamo", "Serge Lutens", "Valentino",
    "Viktor & Rolf", "Zara", "Lattafa", "Frederic Malle", "MM", "Initio", "Aaron Terence Hughes", "ATH"
]

BRAND_MAP = {
    "MFK": "Maison Francis Kurkdjian",
    "Maison Francis Kurkdjian": "Maison Francis Kurkdjian",
    "PDM": "Parfums de Marly",
    "Parfums de Marly": "Parfums de Marly",
    "YSL": "Yves Saint Laurent",
    "Yves Saint Laurent": "Yves Saint Laurent",
    "ATH": "Aaron Terence Hughes",
    "Aaron Terence Hughes" : "Aaron Terence Hughes"
}

for b in BRANDS:
    if b not in BRAND_MAP:
        BRAND_MAP[b] = b

def normalize_brand(text):
    for key, norm in BRAND_MAP.items():
        if key.lower() in text.lower():
            text_clean = re.sub(re.escape(key), "", text, flags=re.IGNORECASE).strip()
            return norm, text_clean
    return None, text

def remove_emojis(text):
    """Remove all emojis from a string."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002700-\U000027BF"
        "\U0001F900-\U0001F9FF"
        "\U00002600-\U000026FF"
        "\U00002B00-\U00002BFF"
        "\U0000200D"
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub(r"", text)

def filter_lines(body):
    """
    Filter out irrelevant lines:
    - blank
    - contextual text (lines with no brand or number)
    - imgur links
    Keep dashed/strikethrough lines (representing sold bottles)
    """
    lines = []
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        line = remove_emojis(line)  # remove emojis
        if "imgur.com" in line.lower():
            continue
        # Skip lines that don't contain numbers (likely price/size) or brands
        if not any(brand.lower() in line.lower() for brand in BRANDS) and not re.search(r"\d", line):
            continue
        lines.append(line)
    return lines

'''
def parse_fragments_with_llm(fragments, author, flair):
    """
    Send a list of fragments in a single GPT call for structured JSON extraction.
    """
    # Join multiple lines into a single prompt
    joined_text = "\n".join(fragments)
    prompt = f"""
Extract structured fragrance info from the following lines:
\"\"\"{joined_text}\"\"\"

Return a JSON array. Each element should have:
- author: string
- flair: string
- brand: string
- frag_name: string
- size: number in mL
- price: number in USD
- fill_percent: number 0-100 or null if unknown
- status: SOLD, AVAILABLE, LISTED, or null

Do NOT include any explanation, comments, or text. Only return valid JSON.
For brand, use the normalized brand if possible. If not certain, use null.
Include author and flair from the Reddit post for each element.
"""
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model="gpt-5-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.choices[0].message.content
            data = json.loads(content)
            # Add author and flair if missing
            for entry in data:
                entry["author"] = author
                entry["flair"] = flair
            return data
        except Exception as e:
            print(f"Retry {attempt+1}/{MAX_RETRIES} failed: {e}")
            time.sleep(SLEEP_BETWEEN_CALLS)
    return []

'''


def clean_post_with_llm(lines, author, flair):
    """
    Batch-process a list of lines using GPT to extract structured fragrance info.
    - Handles multiple fragrances per line.
    - Normalizes brands using BRAND_MAP.
    - Marks strikethrough lines as SOLD.
    - Returns a list of dicts with author, flair, brand, frag_name, size, price, fill_percent, status.
    """
    # Join lines into a single text block
    joined_text = "\n".join(lines)
    
    # Detect local strikethrough
    local_status = []
    for line in lines:
        local_status.append(bool(re.search(r"~~.*~~", line)))

    # Prepare normalized brand list for GPT
    normalized_brands = ", ".join(BRAND_MAP.values())

    prompt = f"""
Extract structured fragrance info from the following Reddit lines:
\"\"\"{joined_text}\"\"\"

Rules:
- Return a JSON array, one object per fragrance (split multiple fragrances in a line into separate objects).
- Each object must include:
  - author: "{author}"
  - flair: "{flair}"
  - brand: string (normalize using these brands if possible: {normalized_brands}, else null)
  - frag_name: string
  - size: number in mL (or null if unknown)
  - price: number in USD (or null if unknown)
  - fill_percent: number 0-100 (or null if unknown)
  - status: SOLD if strikethrough detected, otherwise AVAILABLE, LISTED, or null
- Ignore emojis, imgur links, or any contextual text.
- Do not include any explanation or extra text. Only return valid JSON.
"""

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model="gpt-5-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.choices[0].message.content

            # Ensure valid JSON
            data = json.loads(content)

            # Override status if local strikethrough detected
            for idx, entry in enumerate(data):
                if idx < len(local_status) and local_status[idx]:
                    entry["status"] = "SOLD"

            return data

        except Exception as e:
            print(f"Retry {attempt+1}/{MAX_RETRIES} failed: {e}")
            time.sleep(SLEEP_BETWEEN_CALLS)

    return []

def process_csv(input_csv, output_csv):
    df = pd.read_csv(input_csv)
    results = []

    for idx, row in df.iterrows():
        print(f"Processing post {idx + 1}/{len(df)}: {row['title']}")
        title = row["title"]
        if "[WTS]" not in title.upper() or "(bottle)" not in title.lower() and "(bottles)" not in title.lower():
            continue
        body = row["body"]
        author = row.get("author", None)
        flair = row.get("flair", None)
        lines = filter_lines(body)
        # Batch fragments in chunks to reduce API calls
        batch_size = 10
        for i in range(0, len(lines), batch_size):
            batch = lines[i:i+batch_size]
            parsed = clean_post_with_llm(batch, author, flair)
            results.extend(parsed)

    # Save JSON output
    with open(output_csv, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"✅ Saved {len(results)} entries to {output_csv}")

if __name__ == "__main__":
    process_csv(INPUT_CSV, OUTPUT_CSV)
