import pandas as pd
import re
from difflib import SequenceMatcher

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def clean_reddit_data(file_path):
    print(f"Loading Reddit data from {file_path}...")
    df = pd.read_csv(file_path)
    
    # Convert numeric columns
    for col in ["price", "size", "fill_percent"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        
    # Filter for high fill percent or missing (assumed full)
    # Keeping items with > 90% fill or NaN fill (often implied new/full in listings if not specified, though risky, we'll assume for now or filter strictly)
    # For this pass, let's be stricter: >= 90 or NaN
    df = df[ (df['fill_percent'] >= 90) | (df['fill_percent'].isna()) ]
    
    # Standardize text
    df['brand'] = df['brand'].astype(str).str.strip().str.upper()
    df['frag_name'] = df['frag_name'].astype(str).str.strip()
    
    # Remove common noise from frag_name
    df['clean_name'] = df['frag_name'].str.replace(r"\(.*?\)", "", regex=True).str.strip().str.upper()
    
    return df

def clean_jomashop_data(file_path):
    print(f"Loading Jomashop data from {file_path}...")
    df = pd.read_csv(file_path)
    
    # Clean price
    df['discount_price'] = df['discount_price'].astype(str).str.replace('$', '').str.replace(',', '')
    df['price'] = pd.to_numeric(df['discount_price'], errors='coerce')
    
    # Standardize text
    df['brand'] = df['brand'].astype(str).str.strip().str.upper()
    df['product'] = df['product'].astype(str).str.strip().str.upper()
    
    # Extract size if possible (simple regex for "3.4 oz" or "100 ml")
    # Jomashop "size" column often empty, need to parse "product"
    def extract_size(text):
        match = re.search(r'(\d+(\.\d+)?)\s*(OZ|ML)', text)
        if match:
            return match.group(0)
        return None

    df['extracted_size'] = df['product'].apply(extract_size)
    
    return df

def match_and_compare(reddit_df, jomashop_df):
    print("Matching products...")
    
    # Calculate Reddit stats
    reddit_stats = reddit_df.groupby(['brand', 'clean_name']).agg(
        reddit_avg_price=('price', 'mean'),
        reddit_count=('price', 'count'),
        reddit_std=('price', 'std')
    ).reset_index()
    
    results = []
    
    # Iterate through Reddit groups and find Jomashop match
    # This is O(N*M) naive matching, acceptable for small datasets
    # Optimization: Filter Jomashop by brand first
    
    for _, r_row in reddit_stats.iterrows():
        r_brand = r_row['brand']
        r_name = r_row['clean_name']
        
        # Filter Jomashop by brand (exact match)
        j_candidates = jomashop_df[jomashop_df['brand'] == r_brand]
        
        best_match = None
        best_score = 0
        
        for _, j_row in j_candidates.iterrows():
            # Compare names
            score = similar(r_name, j_row['product'])
            if score > best_score:
                best_score = score
                best_match = j_row
        
        # Threshold for match
        if best_score > 0.4: # Low threshold for now, can tune
            results.append({
                'brand': r_brand,
                'reddit_name': r_name,
                'jomashop_name': best_match['product'],
                'match_score': best_score,
                'reddit_avg': r_row['reddit_avg_price'],
                'reddit_count': r_row['reddit_count'],
                'jomashop_price': best_match['price'],
                'jomashop_url': best_match['url'],
                'price_diff': best_match['price'] - r_row['reddit_avg_price']
            })
            
    return pd.DataFrame(results)

if __name__ == "__main__":
    reddit_path = "/Users/shawnchen/Documents/fragrancetracker/data/cleaned/reddit_big_cleaned.csv"
    jomashop_path = "/Users/shawnchen/Documents/fragrancetracker/data/raw/jomashop_perfumes.csv"
    
    r_df = clean_reddit_data(reddit_path)
    j_df = clean_jomashop_data(jomashop_path)
    
    comparison_df = match_and_compare(r_df, j_df)
    
    output_path = "/Users/shawnchen/Documents/fragrancetracker/data/cleaned/price_comparison.csv"
    comparison_df.to_csv(output_path, index=False)
    print(f"Comparison saved to {output_path}")
    print(comparison_df.head())
