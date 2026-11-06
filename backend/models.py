from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class UserDB(BaseModel):
    id: str
    username: str
    hashed_password: str
    email: Optional[str] = None
    role: str = "investor"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class UserRegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_\-\.]+$")
    password: str = Field(min_length=6, max_length=128)
    email: Optional[str] = Field(default=None, max_length=100)


class UserLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class UserAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class UserProfileDB(BaseModel):
    id: str = "default_user"
    risk_level: str = Field(default="conservative")
    investment_horizon: str = Field(default="medium")
    panic_sell_tendency: float = Field(default=0.8, ge=0.0, le=1.0)
    preferred_sectors: List[str] = Field(default_factory=lambda: ["Energy", "Tech"])
    portfolio_cash: float = Field(default=250000.0, ge=0.0)
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PortfolioHoldingDB(BaseModel):
    user_id: str = "default_user"
    ticker: str
    company_name: str
    shares: float = Field(gt=0)
    avg_cost: float = Field(gt=0)
    currency: str = "INR"
    sector: str = "Tech"
    beta: float = 1.0
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class WatchlistDB(BaseModel):
    user_id: str = "default_user"
    ticker: str
    target_price: Optional[float] = None
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DecisionMemoDB(BaseModel):
    id: str
    user_id: str = "default_user"
    ticker: str
    company_name: str
    memo_markdown: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
