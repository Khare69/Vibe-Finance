from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class UserProfileDB(BaseModel):
    id: str = "default_user"
    risk_level: str = Field(default="conservative")
    investment_horizon: str = Field(default="medium")
    panic_sell_tendency: float = Field(default=0.8, ge=0.0, le=1.0)
    preferred_sectors: List[str] = Field(default_factory=lambda: ["Energy", "Tech"])
    portfolio_cash: float = Field(default=250000.0, ge=0.0)
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class PortfolioHoldingDB(BaseModel):
    ticker: str
    company_name: str
    shares: float = Field(gt=0)
    avg_cost: float = Field(gt=0)
    currency: str = "INR"
    sector: str = "Tech"
    beta: float = 1.0
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class WatchlistDB(BaseModel):
    ticker: str
    target_price: Optional[float] = None
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class DecisionMemoDB(BaseModel):
    id: str
    ticker: str
    company_name: str
    memo_markdown: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
