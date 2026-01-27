from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os

# Add project root to path so we can import src
sys.path.append("/Users/shawnchen/Documents/fragrancetracker")

from src.scraping.reddit_scraper import scrape_reddit
# We would need a function to process/store the scanned data
# from src.processing.ingest import ingest_new_posts

default_args = {
    'owner': 'fragrancetracker',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'fragrance_scraper_hourly',
    default_args=default_args,
    description='Scrape r/fragranceswap hourly',
    schedule_interval=timedelta(hours=1),
    catchup=False
)

def run_scraper(**kwargs):
    print("Starting scrape...")
    df = scrape_reddit(limit=50) # Limit to 50 for hourly check
    print(f"Scraped {len(df)} posts.")
    # todo: Ingest into MongoDB 'listings' collection
    # todo: Check against alerts

t1 = PythonOperator(
    task_id='scrape_reddit',
    python_callable=run_scraper,
    dag=dag,
)
