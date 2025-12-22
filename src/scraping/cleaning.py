import re
import spacy
import pandas as pd

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


# -------------------
# Cleaning functions
# -------------------
def clean_frag_name(raw_name):
    """Remove URLs, descriptors, strike-throughs, parentheses, extra punctuation"""
    name = raw_name
    name = re.sub(r'https?://\S+', '', name)                   # URLs
    name = re.sub(r'\(.*?\)', '', name)                        # Parentheses content
    descriptors = ['see level', 'full presentation', 'BNIB', 'shipped', 'SOLD', '🚢', '~', '**']
    for d in descriptors:
        name = name.replace(d, '')
    name = re.sub(r'[-*]', '', name)                           # Extra punctuation
    name = re.sub(r'\s+', ' ', name)                           # Collapse spaces
    return name.strip()

def parse_size(token_text):
    token_text = token_text.replace("≈", "")
    if '/' in token_text:
        parts = [float(p) for p in re.findall(r'\d+', token_text)]
        return max(parts)
    match = re.search(r'\d+', token_text)
    if match:
        return float(match.group())
    return None

def parse_price(token_text):
    token_text = token_text.replace("~", "").replace("-", "").replace("—","")
    match = re.search(r'\$?(\d+)', token_text)
    if match:
        return float(match.group(1))
    return None

def parse_fill(line, size):
    match = re.search(r'(\d{1,3})\s?%', line)
    if match:
        return float(match.group(1))
    match = re.search(r'≈(\d+)\s?ml', line, re.IGNORECASE)
    if match and size:
        return float(match.group(1))/size * 100
    return None

def extract_brand_and_name(line, doc):
    # Try NER first
    frag_candidates = [ent.text for ent in doc.ents if ent.label_ in ["ORG", "PRODUCT", "WORK_OF_ART"]]
    frag_name = frag_candidates[0] if frag_candidates else line

    # Brand dictionary lookup
    brand = None
    for b in BRANDS:
        if b.lower() in line.lower():
            brand = b
            frag_name = frag_name.replace(b, "").strip()
            break

    frag_name = clean_frag_name(frag_name)
    return brand, frag_name

# -------------------
# Line parsing
# -------------------
def parse_line(line):
    line = line.strip()
    if not line:
        return None

    doc = nlp(line)
    brand, frag_name = extract_brand_and_name(line, doc)

    # Price
    price = None
    for token in doc:
        if "$" in token.text:
            price = parse_price(token.text)
            break

    # Size
    size = None
    for token in doc:
        if "ml" in token.text.lower():
            size = parse_size(token.text)
            break

    # Fill percent
    fill_percent = parse_fill(line, size)

    # Status
    status = None
    for s in ["SOLD", "AVAILABLE", "LISTED"]:
        if s.lower() in line.lower():
            status = s
            break

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

# -------------------
# Post parsing
# -------------------
def process_post(title, body):
    """Return list of parsed bottles from a single post"""
    if "[WTS]" not in title.upper() or "(bottle)" not in title.lower():
        return []

    rows = []
    for line in body.splitlines():
        # Split multiple bottles per line
        fragments = [f.strip() for f in re.split(r" and |,", line) if f.strip()]
        for frag in fragments:
            parsed = parse_line(frag)
            if parsed:
                rows.append(parsed)
    return rows

# -------------------
# CSV processing
# -------------------
def process_csv(input_csv, output_csv):
    df = pd.read_csv(input_csv)
    if "title" not in df.columns or "body" not in df.columns:
        raise ValueError("Input CSV must have 'title' and 'body' columns")

    all_rows = []
    for _, row in df.iterrows():
        parsed_lines = process_post(row["title"], row["body"])
        all_rows.extend(parsed_lines)

    out_df = pd.DataFrame(all_rows, columns=["brand", "frag_name", "size", "price", "fill_percent", "status"])
    # Strip whitespace
    for col in ["brand","frag_name","status"]:
        out_df[col] = out_df[col].astype(str).str.strip()
    # Drop rows without price or size
    out_df = out_df[(out_df["price"].notna()) | (out_df["size"].notna())]

    out_df.to_csv(output_csv, index=False)
    print(f"✅ Processed CSV saved to {output_csv} with {len(out_df)} rows")

if __name__ == "__main__":
    process_csv("data/raw/reddit_posts.csv", "data/cleaned/attempt5.csv")