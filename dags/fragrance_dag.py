from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os

# Add project root to path so we can import src
PROJECT_ROOT = os.getenv("FRAGRANCE_TRACKER_ROOT", "/Users/shawnchen/Documents/fragrancetracker")
sys.path.append(PROJECT_ROOT)

from src.pipeline.reddit_ingest import scrape_and_store_recent_posts
from src.pipeline.alert_evaluator import evaluate_alerts, send_pending_alert_notifications

default_args = {
    'owner': 'fragrancetracker',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

SCRAPE_LIMIT = int(os.getenv("REDDIT_SCRAPE_LIMIT", "10"))
SCRAPE_SCHEDULE = os.getenv("REDDIT_SCRAPE_SCHEDULE", "0 */3 * * *")

dag = DAG(
    'fragrance_reddit_recent_posts',
    default_args=default_args,
    description='Scrape recent r/fragranceswap posts into MongoDB',
    schedule_interval=SCRAPE_SCHEDULE,
    catchup=False
)

def run_scraper(**kwargs):
    print(f"Scraping {SCRAPE_LIMIT} recent posts from r/fragranceswap...")
    result = scrape_and_store_recent_posts(limit=SCRAPE_LIMIT)
    print(f"Scrape complete: {result}")

def run_alerts(**kwargs):
    result = evaluate_alerts()
    print(f"Alert evaluation complete: {result}")

def run_notifications(**kwargs):
    result = send_pending_alert_notifications()
    print(f"Notification sending complete: {result}")

t1 = PythonOperator(
    task_id='scrape_and_store_recent_reddit_posts',
    python_callable=run_scraper,
    dag=dag,
)

t2 = PythonOperator(
    task_id='evaluate_alerts',
    python_callable=run_alerts,
    dag=dag,
)

t3 = PythonOperator(
    task_id='send_alert_notifications',
    python_callable=run_notifications,
    dag=dag,
)

t1 >> t2 >> t3
