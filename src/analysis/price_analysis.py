import pandas as pd
import numpy as np
import json
import re
import os

# Configuration
REDDIT_DATA_PATH = 'data/cleaned/frag_posts_llm_cleaned.json'
JOMASHOP_DATA_PATH = 'data/cleaned/jomashop_cleaned.csv'
OUTPUT_PATH = 'data/analysis/reddit_vs_jomashop_analysis.csv'

def calculate_reputation_weight(flair_text):
    """
    Parses flair text (e.g., "Legacy:0/Buys:1/Sales:22") and calculates weight.
    Curve:
        If Sales <= 15: Weight = Sales^2
        If Sales > 15: Natural log curve tailored to be continuous.
        
    Note: To make it continuous at 15:
    15^2 = 225
    Log curve form: a * ln(x) + b
    We need curve(15) = 225. 
    Let's pick a slope at 15 to be somewhat smooth or just pick a arbitrary log curve that starts here.
    Derivative of x^2 at 15 is 2*15 = 30.
    Derivative of a*ln(x) is a/x. at 15: a/15.
    If we want smooth connection: a/15 = 30 => a = 450.
    Then 450 * ln(15) + b = 225
    b = 225 - 450 * ln(15) ~= 225 - 450 * 2.708 ~= 225 - 1218 = -993.
    So: 450 * ln(x) - 993
    """
    if not isinstance(flair_text, str):
        return 1.0 # Default weight for no flair? Or 0? Let's say 1 (equivalent to 1 sale? No, 1 sale is weight 1). Let's use 0 sales -> weight 0?
                   # Actually, new sellers might have 0 sales. Weight 0 means they don't contribute? Maybe small weight.
                   # Let's parse first.
    
    # regex to find "Sales:X"
    match = re.search(r'Sales:(\d+)', flair_text)
    if match:
        sales = int(match.group(1))
    else:
        sales = 0
        
    if sales <= 15:
        return float(sales**2)
    else:
        return 450.0 * np.log(sales) - 993.0

def normalize_price(row):
    """
    Normalizes price to 100% fill.
    Price_Norm = Price / (Fill_Percent / 100)
    """
    price = row.get('price')
    if pd.isna(price):
        return np.nan
        
    fill = row.get('fill_percent')
    
    # If fill is missing, assume 100% or mostly full?
    # Context: If missing, it's often a new bottle or not specified.
    # Let's assume 95% if not new, but if it says "BNIB" in corpus it might be 100.
    # For now, let's assume 100% if missing to be conservative on price (lower normalized price).
    # Wait, if it's 50% full and we assume 100%, we calculate Price / 1.0 = Price.
    # If we knew it was 50%, Price / 0.5 = 2 * Price.
    # So assuming 100% when it's actually partial UNDERESTIMATES the value (good for finding deals? No, bad for value estimation).
    # However, for this analysis, if fill is missing, we likely can't do better.
    if pd.isna(fill):
        fill = 100.0
        
    # Safety clip
    if fill <= 0: return np.nan
    if fill > 100: fill = 100 # Should not happen but data can be dirty
    
    return price / (fill / 100.0)

def main():
    # 1. Load Data
    print("Loading data...")
    if not os.path.exists(REDDIT_DATA_PATH):
        raise FileNotFoundError(f"{REDDIT_DATA_PATH} not found.")
    
    with open(REDDIT_DATA_PATH, 'r') as f:
        reddit_data = json.load(f)
    
    df_reddit = pd.DataFrame(reddit_data)
    
    print(f"Loaded {len(df_reddit)} Reddit posts.")
    
    # 2. Process Reddit Data
    # Extract sales and calc weight
    df_reddit['weight'] = df_reddit['flair'].apply(calculate_reputation_weight)
    
    # Normalize price
    df_reddit['normalized_price'] = df_reddit.apply(normalize_price, axis=1)
    
    # Filter out invalid prices/weights
    # We allow weight 0? If weight is 0, it contributes nothing to weighted average.
    # Maybe min weight should be small epsilon?
    # If sales=0, weight=0. 
    # Let's set min sales to 1 effectively for weight? 
    # Or just let them be 0 (excluded from average).
    # If someone has 0 sales, do we trust their price? Maybe not for "market value" analysis.
    df_reddit = df_reddit.dropna(subset=['normalized_price'])
    # Only keep listings where we have some weight?
    # If we drop weight 0, we drop new sellers.
    # Users might want to see new sellers deals, but for *Average Price Calculation* we want reputation.
    # So yes, drop weight 0 for AVG calculation.
    df_analysis = df_reddit[df_reddit['weight'] > 0].copy()
    
    # Normalize frag_name to uppercase for matching
    df_analysis['frag_name'] = df_analysis['frag_name'].astype(str).str.upper().str.strip()
    
    print(f"Posts with valid price and >0 reputation: {len(df_analysis)}")
    
    # 3. Group by Fragrance
    # We need to group by 'frag_name'? 
    # Wait, 'frag_name' in reddit json might be messy.
    # The user said "all the fragrances from reddit that have an associated price in the jomashop_cleaned.csv"
    # This implies we need a link.
    # In jomashop_cleaned.csv, there is 'reddit_name'.
    # We should merge on this 'reddit_name'.
    # BUT, df_reddit has 'frag_name' which might just be what the LLM extracted.
    # Is 'frag_name' in df_reddit standardized to match 'reddit_name' in jomashop csv?
    # Let's check the jomashop csv columns again.
    # Col 2: reddit_name.
    # Let's assume df_reddit['frag_name'] text matches jomashop_cleaned['reddit_name'].
    # Or strict match?
    
    # Let's aggregate df_reddit by 'frag_name' first
    
    # Weighted Average function
    def weighted_avg(x):
        try:
            return np.average(x['normalized_price'], weights=x['weight'])
        except ZeroDivisionError:
            return np.nan

    # Weighted Std Dev function
    def weighted_std(x):
        try:
            average = np.average(x['normalized_price'], weights=x['weight'])
            variance = np.average((x['normalized_price'] - average)**2, weights=x['weight'])
            return np.sqrt(variance)
        except ZeroDivisionError:
            return np.nan
            
    grouped = df_analysis.groupby('frag_name')[['normalized_price', 'weight']].apply(
        lambda x: pd.Series({
            'weighted_avg_price': weighted_avg(x),
            'weighted_std_dev': weighted_std(x),
            'listing_count': len(x),
            'total_sales_volume_proxy': x['weight'].sum()
        })
    ).reset_index()
    
    # 4. Merge with Jomashop
    print("Loading Jomashop data...")
    df_jomashop = pd.read_csv(JOMASHOP_DATA_PATH)
    
    # Merge keys: df_jomashop['reddit_name'] vs grouped['frag_name']
    merged = pd.merge(
        df_jomashop, 
        grouped, 
        left_on='reddit_name', 
        right_on='frag_name', 
        how='left'
    )
    
    # 5. Calculate Comparison Metrics
    merged['weighted_price_diff'] = merged['weighted_avg_price'] - merged['jomashop_price']
    
    # 6. Save
    # Ensure dir exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    cols_to_save = [
        'brand', 'reddit_name', 'jomashop_name', 'jomashop_price', 'jomashop_url',
        'match_score',
        'weighted_avg_price', 'weighted_std_dev', 'listing_count', 
        'weighted_price_diff'
    ]
    
    merged[cols_to_save].to_csv(OUTPUT_PATH, index=False)
    print(f"Saved analysis to {OUTPUT_PATH}")
    print("\nSample Output:")
    print(merged[cols_to_save].head())

if __name__ == "__main__":
    main()
