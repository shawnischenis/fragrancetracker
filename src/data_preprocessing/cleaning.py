import pandas as pd

reddit_df = pd.read_csv("/Users/shawnchen/Documents/fragrancetracker/data/cleaned/reddit_big_cleaned.csv")

reddit_df = reddit_df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
reddit_df = reddit_df.drop_duplicates()

for col in ["size", "price", "fill_percent"]:
    reddit_df[col] = pd.to_numeric(reddit_df[col], errors="coerce")


reddit_df["status"] = reddit_df["status"].str.upper().replace({
    "LISTED": "LISTED",
    "AVAILABLE": "AVAILABLE",
    "SOLD": "SOLD",
    "": None
})

reddit_df = reddit_df.dropna(subset = ["fragrance_name", "size", "price"])


# 6️⃣ Standardize fragrance names
reddit_df["frag_name"] = (
    reddit_df["frag_name"]
    .str.replace(r"\(.*?\)", "", regex=True)  # remove parentheses info
    .str.replace(r"[^a-zA-Z0-9\s]", "", regex=True)  # remove symbols
    .str.strip()
)


