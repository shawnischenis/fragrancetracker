import pandas as pd
import spacy
import re
from openai import OpenAI
import json
import time

# === CONFIG ===
client = OpenAI(api_key = "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")
INPUT_CSV = "data/raw/reddit_posts.csv"
OUTPUT_CSV = "data/cleaned/llm_normalized.csv"
MAX_RETRIES = 3
SLEEP_BETWEEN_CALLS = 1  # seconds

# === SpaCy NLP ===
nlp = spacy.load("en_core_web_sm")

BRANDS = [
    "Creed", "Dior", "Chanel", "Tom Ford", "Maison Francis Kurkdjian",  "MFK", 
    "Byredo", "Amouage", "Xerjoff", "Le Labo", "Guerlain", "YSL",
    "Armani", "Parfums de Marly",  "PDM", 
    "Acqua di Parma", "Afnan", "Al Haramain Perfumes", "Al-Rehab", "Ariana Grande", "Armaf", "Avon", "Azzaro",
    "BDK Parfums", "BORNTOSTANDOUT®", "Bath & Body Works", "Bond No 9", "Britney Spears", "Burberry", "Bvlgari",
    "By Kilian", "Cacharel", "Calvin Klein", "Carolina Herrera", "Chopard", "Christian Dior", "Clive Christian",
    "Coach", "Davidoff", "Diptyque", "Dolce & Gabbana", "Dunhill", "Elie Saab", "Elizabeth Arden", "Estée Lauder",
    "Fendi", "Ferrari", "Giorgio Armani", "Givenchy", "Gucci", "Hermès", "Hugo Boss", "Jean Paul Gaultier",
    "Jimmy Choo", "Jo Malone London", "Jo Malone", "Juicy Couture", "Kenzo", "Kilian", "Lacoste", "Lancôme", "Loewe", "Louis Vuitton",
    "Mancera", "Mugler", "Montale", "Nina Ricci", "Nishane", "Oud Al Qasr", "Parfums de Marly", "Penhaligon's",
    "Perry Ellis", "Prada", "Ralph Lauren", "Rochas", "Salvatore Ferragamo", "Serge Lutens", "Tom Ford", "Valentino",
    "Viktor & Rolf", "Yves Saint Laurent", "Zara", "Lattafa", "Frederic Malle", "Kilian", "MM", "Initio"
]

BRAND_MAP = {
    "MFK": "Maison Francis Kurkdjian",
    "Maison Francis Kurkdjian": "Maison Francis Kurkdjian",
    "PDM": "Parfums de Marly",
    "Parfums de Marly": "Parfums de Marly",
    "YSL": "Yves Saint Laurent",
    "Yves Saint Laurent": "Yves Saint Laurent"
}


for b in BRANDS:
    if b not in BRAND_MAP:
        BRAND_MAP[b] = b

def normalize_brand(line):
    for key, norm in BRAND_MAP.items():
        if key.lower() in line.lower():
            line = re.sub(re.escape(key), "", line, flags=re.IGNORECASE).strip()
            return norm, line
    return None, line

def clean_post_with_llm(line):
    """
    Uses OpenAI LLM to extract structured info for a single bottle line.
    Returns a dict with keys: brand, frag_name, size, price, fill_percent, status
    """
    # Normalize brand first
    brand, line_no_brand = normalize_brand(line)

    prompt = f"""
Extract structured fragrance info from this text:
"{line_no_brand}"

Return a JSON with keys:
- frag_name: string
- size: number in mL
- price: number in USD
- fill_percent: number 0-100
- status: SOLD, AVAILABLE, LISTED, or None

Do not include brand, we already normalized it. Respond ONLY with valid JSON.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role":"user","content": prompt}]
        )
        import json
        content = response.choices[0].message.content
        data = json.loads(content)
        data["brand"] = brand
        return data
    except Exception as e:
        print(f"LLM parse error for line: {line} -> {e}")
        return None

def process_post(title, body):
    """
    Process a single Reddit post.
    Only WTS + bottle posts are considered.
    Returns a list of dicts.
    """
    if "[WTS]" not in title.upper() or "(bottle)" not in title.lower():
        return []

    rows = []
    for line in body.splitlines():
        # Split lines further by 'and' or ',' to handle multiple bottles
        fragments = [f.strip() for f in re.split(r" and |,", line) if f.strip()]
        for frag in fragments:
            parsed = clean_post_with_llm(frag)
            if parsed:
                rows.append(parsed)
    return rows

def process_csv(input_csv, output_csv):
    df = pd.read_csv(input_csv)
    if "title" not in df.columns or "body" not in df.columns:
        raise ValueError("Input CSV must have 'title' and 'body' columns")

    all_rows = []
    for _, row in df.iterrows():
        all_rows.extend(process_post(row["title"], row["body"]))

    out_df = pd.DataFrame(all_rows, columns=["brand","frag_name","size","price","fill_percent","status"])
    out_df.to_csv(output_csv, index=False)
    print(f"✅ Cleaned CSV saved to {output_csv} with {len(out_df)} rows")


if __name__ == "__main__":
    process_csv("data/raw/reddit_posts.csv", "data/cleaned/reddit_cleaned_llm.csv")
