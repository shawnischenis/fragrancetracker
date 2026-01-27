from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from src.api.database import db, get_database
from src.api.models import Fragrance, Alert, AlertCreate
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.connect()
    yield
    db.close()

app = FastAPI(lifespan=lifespan)

# CORS (Frontend will be on localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/fragrances", response_model=List[Fragrance])
async def get_fragrances(database=Depends(get_database)):
    fragrances = []
    cursor = database["fragrances"].find().sort("weighted_price_diff", 1) # Good deals first (negative diff)
    async for document in cursor:
        document.pop("_id", None)
        
        # Sanitize NaNs which break Pydantic/JSON
        for k, v in document.items():
            if isinstance(v, float) and v != v: # Check for NaN
                document[k] = None
                
        fragrances.append(document)
    return fragrances

@app.post("/api/alerts", response_model=Alert)
async def create_alert(alert: AlertCreate, database=Depends(get_database)):
    new_alert = alert.dict()
    result = await database["alerts"].insert_one(new_alert)
    new_alert["_id"] = str(result.inserted_id)
    return new_alert
