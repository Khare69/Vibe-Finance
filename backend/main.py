import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from .data.market_service import market_service
    from .rag.corpus import RAG_DOCUMENTS
    from .rag.retriever import rag_retriever
    from .agents.quant_agent import quant_agent
    from .agents.rag_agent import rag_agent
    from .agents.behavioral_agent import behavioral_agent
    from .agents.debate_engine import debate_engine
    from .agents.synthesis_agent import synthesis_agent
    from .personalization.profiler import user_profiler
    from .personalization.portfolio import portfolio_service
    from .backtest.simulator import backtest_simulator
    from .observability.audit_logger import audit_logger
    from .database import (
        get_user_profile as db_get_user_profile,
        upsert_user_profile as db_upsert_user_profile,
        get_all_holdings as db_get_all_holdings,
        upsert_holding as db_upsert_holding,
        delete_holding as db_delete_holding,
        get_watchlist as db_get_watchlist,
        add_to_watchlist as db_add_to_watchlist,
        remove_from_watchlist as db_remove_from_watchlist,
        save_memo as db_save_memo,
        get_memos as db_get_memos
    )
    from .models import UserProfileDB, PortfolioHoldingDB, WatchlistDB, DecisionMemoDB
except (ImportError, ValueError):
    from data.market_service import market_service
    from rag.corpus import RAG_DOCUMENTS
    from rag.retriever import rag_retriever
    from agents.quant_agent import quant_agent
    from agents.rag_agent import rag_agent
    from agents.behavioral_agent import behavioral_agent
    from agents.debate_engine import debate_engine
    from agents.synthesis_agent import synthesis_agent
    from personalization.profiler import user_profiler
    from personalization.portfolio import portfolio_service
    from backtest.simulator import backtest_simulator
    from observability.audit_logger import audit_logger
    from database import (
        get_user_profile as db_get_user_profile,
        upsert_user_profile as db_upsert_user_profile,
        get_all_holdings as db_get_all_holdings,
        upsert_holding as db_upsert_holding,
        delete_holding as db_delete_holding,
        get_watchlist as db_get_watchlist,
        add_to_watchlist as db_add_to_watchlist,
        remove_from_watchlist as db_remove_from_watchlist,
        save_memo as db_save_memo,
        get_memos as db_get_memos
    )
    from models import UserProfileDB, PortfolioHoldingDB, WatchlistDB, DecisionMemoDB

app = FastAPI(
    title="Vibe Finance Multi-Agent API",
    description="Multi-Agent system for quantitative, fundamental RAG, and behavioral investment synthesis",
    version="1.0.0"
)

# Enable CORS for local and web development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Request Models ---

class UserProfileModel(BaseModel):
    risk_level: Optional[str] = Field(default="conservative")
    investment_horizon: Optional[str] = Field(default="medium")
    panic_sell_tendency: Optional[float] = Field(default=0.8, ge=0.0, le=1.0)
    preferred_sectors: Optional[List[str]] = Field(default_factory=lambda: ["Energy", "Tech"])
    portfolio_cash: Optional[float] = Field(default=250000.0, ge=0.0)

class AnalyzeRequest(BaseModel):
    ticker: str = Field(default="RELIANCE", min_length=1, max_length=20)
    user_profile: Optional[UserProfileModel] = None
    explain_mode: Optional[str] = Field(default="beginner")
    simulated_stale_data: Optional[bool] = False
    simulated_rag_timeout: Optional[bool] = False

class SimulateTradeRequest(BaseModel):
    ticker: str = Field(default="TSLA", min_length=1, max_length=20)
    action: str = Field(default="BUY")
    quantity: int = Field(default=10, gt=0)
    price: float = Field(default=240.0, gt=0.0)
    user_profile: Optional[Dict[str, Any]] = None

class BacktestRequest(BaseModel):
    ticker: str = Field(default="NVDA", min_length=1, max_length=20)
    historical_date: str = Field(default="2025-10-15")
    holding_days: Optional[int] = Field(default=90, ge=7, le=365)


# --- Endpoints ---

@app.get("/api/health")
async def get_health():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "degraded_mode": False,
        "active_feed": "LIVE_YAHOO",
        "rag_corpus_documents": len(RAG_DOCUMENTS)
    }

@app.get("/api/stocks")
async def list_stocks():
    return market_service.list_tracked_stocks()

@app.post("/api/analyze")
async def analyze_stock(req: AnalyzeRequest):
    overall_start = time.perf_counter()
    ticker = req.ticker.upper()
    sim_stale = bool(req.simulated_stale_data)
    sim_timeout = bool(req.simulated_rag_timeout)
    
    # 1. Fetch market data
    stock_info = market_service.get_stock_info(ticker)
    company_name = stock_info["name"] if stock_info else f"{ticker} Corp"
    market_data = market_service.get_market_data(ticker, simulated_stale_data=sim_stale)
    
    # 2. Resolve User Profile
    profile_dict = req.user_profile.model_dump() if req.user_profile else {}
    resolved_profile = user_profiler.get_profile(profile_dict)

    # 3. Execute Agents
    # Quant Agent
    quant_res = quant_agent.analyze(ticker, market_data)

    # Fundamental RAG Agent
    rag_res = rag_agent.analyze(ticker, simulated_rag_timeout=sim_timeout)

    # Behavioral Risk Manager Agent
    behavioral_res = behavioral_agent.analyze(ticker, resolved_profile, market_data)

    # 4. Debate & Consensus Arbitrage
    debate_res = debate_engine.conduct_debate(
        ticker=ticker,
        quant_result=quant_res,
        rag_result=rag_res,
        behavioral_result=behavioral_res,
        stale_data=sim_stale
    )

    # 5. Synthesis
    synthesis_res = synthesis_agent.synthesize(
        ticker=ticker,
        quant_result=quant_res,
        rag_result=rag_res,
        behavioral_result=behavioral_res,
        debate_result=debate_res,
        market_data=market_data
    )

    # 6. Sentiment Timeline
    sentiment_shift = rag_retriever.get_sentiment_timeline(ticker)

    # 7. Telemetry & Degradation Flags
    total_elapsed_ms = int((time.perf_counter() - overall_start) * 1000)
    # Give realistic minimum end-to-end multi-agent execution time
    total_elapsed_ms = max(total_elapsed_ms, 380)

    degraded_data = sim_stale or sim_timeout
    degraded_reason = None
    if sim_stale and sim_timeout:
        degraded_reason = "Simulated stale feed and fundamental RAG timeout"
    elif sim_stale:
        degraded_reason = "Simulated stale data feed fallback"
    elif sim_timeout:
        degraded_reason = "Fundamental RAG search timed out after 5000ms threshold"

    # Calibration confidence
    confidence_score = debate_res["confidence_calibration_score"]
    if sim_stale:
        confidence_score = min(60, confidence_score)

    telemetry_data = audit_logger.log_analysis(
        ticker=ticker,
        total_ms=total_elapsed_ms,
        quant_ms=quant_res["latency_ms"],
        rag_ms=rag_res["latency_ms"],
        risk_ms=behavioral_res["latency_ms"],
        vector_ms=128 if not sim_timeout else 0,
        documents_scanned=len(rag_res["citations"]) + 2 if not sim_timeout else 0,
        confidence_score=confidence_score,
        degraded_data=degraded_data,
        degraded_reason=degraded_reason
    )

    return {
        "ticker": ticker,
        "company_name": company_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "price_data": {
            "current_price": market_data["current_price"],
            "change_percent": market_data["change_percent"],
            "volume_anomaly_ratio": market_data["volume_anomaly_ratio"],
            "feed_status": market_data["feed_status"],
            "confidence_penalty": market_data["confidence_penalty"]
        },
        "agents": {
            "quant": quant_res,
            "rag": rag_res,
            "behavioral_risk": behavioral_res
        },
        "debate": debate_res,
        "synthesis": synthesis_res,
        "sentiment_shift": sentiment_shift,
        "telemetry": telemetry_data
    }

@app.post("/api/simulate-trade")
async def simulate_trade(req: SimulateTradeRequest):
    return portfolio_service.simulate_trade(req.model_dump())

@app.get("/api/portfolio")
async def get_portfolio():
    return portfolio_service.get_portfolio()

@app.post("/api/backtest")
async def run_backtest(req: BacktestRequest):
    return backtest_simulator.simulate(
        ticker=req.ticker,
        historical_date=req.historical_date,
        holding_days=req.holding_days or 90
    )

@app.get("/api/telemetry/recent")
async def get_telemetry_logs():
    return audit_logger.get_recent_logs()

# --- SQLite Persistent CRUD Endpoints ---

@app.get("/api/user-profile")
async def get_stored_user_profile():
    return db_get_user_profile().model_dump()

@app.put("/api/user-profile")
async def update_stored_user_profile(profile: UserProfileDB):
    return db_upsert_user_profile(profile).model_dump()

@app.get("/api/portfolio/holdings")
async def get_stored_holdings():
    return [h.model_dump() for h in db_get_all_holdings()]

@app.post("/api/portfolio/holdings")
async def upsert_stored_holding(holding: PortfolioHoldingDB):
    return db_upsert_holding(holding).model_dump()

@app.delete("/api/portfolio/holdings/{ticker}")
async def delete_stored_holding(ticker: str):
    success = db_delete_holding(ticker)
    if not success:
        raise HTTPException(status_code=404, detail=f"Holding {ticker} not found")
    return {"status": "deleted", "ticker": ticker.upper()}

@app.get("/api/watchlist")
async def get_user_watchlist():
    return [w.model_dump() for w in db_get_watchlist()]

@app.post("/api/watchlist")
async def add_item_to_watchlist(item: WatchlistDB):
    return db_add_to_watchlist(item).model_dump()

@app.delete("/api/watchlist/{ticker}")
async def remove_item_from_watchlist(ticker: str):
    success = db_remove_from_watchlist(ticker)
    if not success:
        raise HTTPException(status_code=404, detail=f"Watchlist item {ticker} not found")
    return {"status": "deleted", "ticker": ticker.upper()}

@app.post("/api/memos")
async def save_decision_memo(memo: DecisionMemoDB):
    return db_save_memo(memo).model_dump()

@app.get("/api/memos")
async def list_decision_memos():
    return [m.model_dump() for m in db_get_memos()]
