#r/fragranceswap standard schema 
#title includes [WTS][WTT] or [WTB] tag, filter for [WTS]
#title also includes (bottle) or (decant) tag, filter for (bottle) for now
#use regex to match pattern (brand) (perfume name) (new/bnib/partial) - (price)
#Use NLP to filter again on posts that dont follow this schema

import re
import spacy
import pandas as pd

nlp = spacy.load("en_core_web_sm")


BRANDS = [
    "Creed", "Dior", "Chanel", "Tom Ford", "Maison Francis Kurkdjian",
    "Byredo", "Amouage", "Xerjoff", "Le Labo", "Guerlain", "YSL", "Armani", "MFK"
]

def extract_brand_and_name(line, doc):
    """Use NLP to extract brand and frag_name from spaCy Doc"""
    # Try NER first
    frag_candidates = [ent.text for ent in doc.ents if ent.label_ in ["ORG", "PRODUCT", "WORK_OF_ART"]]
    frag_name = frag_candidates[0] if frag_candidates else line

    # Check brands dictionary
    brand = None
    for b in BRANDS:
        if b.lower() in line.lower():
            brand = b
            # Remove brand from frag_name
            frag_name = frag_name.replace(b, "").strip()
            break

    return brand, frag_name.strip()

def parse_line(line):
    line = line.strip()
    if not line:
        return None

    doc = nlp(line)

    # Brand & Frag Name
    brand, frag_name = extract_brand_and_name(line, doc)

    # Price detection: token containing '$'
    price = None
    for token in doc:
        if "$" in token.text:
            try:
                price = float(token.text.replace("$","").replace("-","").strip())
                break
            except:
                continue

    # Size detection: token containing 'ml' or 'mL'
    size = None
    for token in doc:
        if "ml" in token.text.lower():
            try:
                size = float("".join([c for c in token.text if c.isdigit() or c=="."]))
                break
            except:
                continue

    # Fill percent: token containing '%'
    fill_percent = None
    for token in doc:
        if "%" in token.text:
            try:
                fill_percent = float("".join([c for c in token.text if c.isdigit()]))
                break
            except:
                continue

    # Status detection
    status = None
    for s in ["SOLD", "AVAILABLE", "LISTED"]:
        if s.lower() in line.lower():
            status = s
            break

    # Include line only if price or size exists
    if price or size:
        return {
            "brand": brand,
            "frag_name": frag_name,
            "size": size,
            "price": price,
            "fill_percent": fill_percent,
            "status": status
        }
    return None

def process_post(title, body):
    """Return list of bottle dicts from a post"""
    if "[WTS]" not in title.upper() or "(bottle)" not in title.lower():
        return []

    rows = []
    for line in body.splitlines():
        # Handle multiple bottles separated by 'and' or ','
        fragments = [f.strip() for f in re.split(r" and |,", line) if f.strip()]
        for frag in fragments:
            parsed = parse_line(frag)
            if parsed:
                rows.append(parsed)
    return rows

def process_csv(input_csv, output_csv):
    df = pd.read_csv(input_csv)

    if "title" not in df.columns or "body" not in df.columns:
        raise ValueError("Input CSV must have 'title' and 'body' columns")

    all_rows = []
    for _, row in df.iterrows():
        parsed_lines = process_post(row["title"], row["body"])
        all_rows.extend(parsed_lines)

    out_df = pd.DataFrame(all_rows, columns=["brand", "frag_name", "size", "price", "fill_percent", "status"])
    out_df.to_csv(output_csv, index=False)
    print(f"✅ Processed CSV saved to {output_csv} with {len(out_df)} rows")


if __name__ == "__main__":
    process_csv("data/raw/reddit_posts.csv", "data/cleaned/attempt4.csv")