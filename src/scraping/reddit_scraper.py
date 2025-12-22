import praw
import pandas as pd
import time

def scrape_reddit(limit=1000):
    reddit = praw.Reddit(
        client_id="EpiBq-Xw-pL3P5Pz1pj9yQ",
        client_secret="LL4dU5l7Bmc9djHGUZ5ZuMb00IOWLw",
        user_agent="frag_shopper"
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