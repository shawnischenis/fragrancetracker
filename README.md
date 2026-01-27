# FragranceTracker

**The Scent Index** - A market intelligence platform for fragrance enthusiasts. This application scrapes, cleans, and analyzes prices from the secondary market (Reddit r/fragranceswap) and compares them against retail discounters (Jomashop) to identify deep discounts, market volatility, and rare bottles.

## Features

*   **Market Analysis**: Automatically scrapes hundreds of listings to calculate price with respect to bottle fill and r/fragranceswap seller reputation and volatility (Standard Deviation).
*   **Deal Logic**: Identifies "Deals" where the Reddit price is significantly lower than Jomashop retail.
*   **Smart Search**: Instant search for specific fragrances or brands with aggregation logic.
*   **Alert System**: Set alerts for deal thresholds (e.g., "Notify me if Aventus drops 0.5σ below average") or rarer perfumes.
*   **LLM Data Cleaning**: Uses OpenAI GPT-4o-mini to parse unstructured Reddit listing text into structured JSON.

## Tech Stack

*   **Frontend**: Next.js 14, React, Tailwind CSS, Framer Motion (Lucide Icons).
*   **Backend**: FastAPI (Python), Motor (Async Mongo Driver).
*   **Database**: MongoDB Atlas (Cloud).
*   **AI/ML**: OpenAI API (Data Extraction), Pandas (Statistical Analysis).
*   **DevOps**: Apache Airflow (Scheduling - *In Progress*).

## Installation & Setup

### Prerequisites
*   Node.js & npm
*   Python 3.10+
*   MongoDB Atlas Account
*   OpenAI API Key

### 1. Environment Setup
Create a `.env` file in the root directory:
```bash
OPENAI_API_KEY="sk-..."
MONGO_URL="mongodb+srv://<user>:<password>@cluster0.net/..."
```

### 2. Backend Setup
Install Python dependencies:
```bash
pip install -r requirements.txt
```
*(Note: Ensure `python-dotenv`, `pandas`, `fastapi`, `uvicorn`, `pymongo`, `motor`, `openai` are installed)*

### 3. Frontend Setup
Navigate to the frontend directory and install dependencies:
```bash
cd frontend
npm install
```

## Running the Application

### Start the Backend (API)
Returns JSON data at `http://localhost:8000`.
```bash
./src/scripts/run_api.sh
```

### Start the Frontend (Dashboard)
Launches the UI at `http://localhost:3000`.
```bash
cd frontend
npm run dev
```

## Data Pipeline
1.  **Scrape**: `src/scraping/` scripts fetch data from Reddit.
2.  **Clean**: `src/scraping/llm_cleaning.py` uses LLM to structure the data.
3.  **Analyze**: `src/data_preprocessing/clean_and_compare.py` matches Reddit data with Jomashop CSVs.
4.  **Migrate**: `src/scripts/migrate_analysis.py` pushes the final dataset to MongoDB.

---
*Status: Work in Progress (Phase 2 Complete)*
