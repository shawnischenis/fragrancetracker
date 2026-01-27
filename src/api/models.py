from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Fragrance(BaseModel):
    brand: Optional[str] = None
    reddit_name: str
    jomashop_name: Optional[str] = None
    jomashop_price: Optional[float] = None
    jomashop_url: Optional[str] = None
    weighted_avg_price: Optional[float] = None
    weighted_std_dev: Optional[float] = None
    normalized_price: Optional[float] = None
    listing_count: Optional[int] = None
    weighted_price_diff: Optional[float] = None

class AlertBase(BaseModel):
    email: str
    type: str # "DEAL" or "RARE"
    target_name: str # Fragrance name or keyword
    threshold: Optional[float] = None # For DEAL: std devs below avg
    
class AlertCreate(AlertBase):
    pass

class Alert(AlertBase):
    id: str = Field(..., alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
