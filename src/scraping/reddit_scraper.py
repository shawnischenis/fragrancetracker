import praw
import pandas as pd
import time
import os

from dotenv import load_dotenv

load_dotenv()

def scrape_reddit(limit=1000):
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "fragrancetracker")

    if not client_id or not client_secret:
        raise ValueError("REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET must be set")

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )

    posts = []
    subreddit = reddit.subreddit("fragranceswap")

    for submission in subreddit.new(limit=limit):
        posts.append({
            "title": submission.title,
            "body": submission.selftext,
            "author": str(submission.author),
            "flair": submission.author_flair_text,
            "date": submission.created_utc,
            "url": submission.url
        })
        time.sleep(1)  # be nice to Reddit API

    df = pd.DataFrame(posts)
    return df

if __name__ == "__main__":
    df = scrape_reddit(limit=1000)
    existing_df = pd.read_csv("data/raw/reddit_posts.csv")
    joined_df = pd.concat([existing_df, df]).drop_duplicates(subset=['url'])
    joined_df.to_csv("data/raw/frag_posts.csv")
    print(f"scraped {len(joined_df)} posts")
