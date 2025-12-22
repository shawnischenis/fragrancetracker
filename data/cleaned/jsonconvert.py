import pandas as pd
import json

# Load your JSON file
with open("data/cleaned/frag_posts_llm_cleaned.json", "r") as f:
    data = json.load(f)

# Convert to DataFrame
df = pd.DataFrame(data)

# Save to CSV
df.to_csv("data/cleaned/reddit_big_cleaned.csv", index=False)