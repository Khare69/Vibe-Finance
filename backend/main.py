import time
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
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
    from .agents.llm_client import llm_client
    from .personalization.profiler import user_profiler
    from .personalization.portfolio import portfolio_service
    from .backtest.simulator import backtest_simulator
    from .observability.audit_logger import audit_logger
    from .database import (
        get_user_profile_async as db_get_user_profile_async,
        upsert_user_profile_async as db_upsert_user_profile_async,
        get_all_holdings_async as db_get_all_holdings_async,
        upsert_holding_async as db_upsert_holding_async,
        delete_holding_async as db_delete_holding_async,
        get_watchlist_async as db_get_watchlist_async,
        add_to_watchlist_async as db_add_to_watchlist_async,
        remove_from_watchlist_async as db_remove_from_watchlist_async,
        save_memo_async as db_save_memo_async,
        get_memos_async as db_get_memos_async
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
    from agents.llm_client import llm_client
    from personalization.profiler import user_profiler
    from personalization.portfolio import portfolio_service
    from backtest.simulator import backtest_simulator
    from observability.audit_logger import audit_logger
    from database import (
        get_user_profile_async as db_get_user_profile_async,
        upsert_user_profile_async as db_upsert_user_profile_async,
        get_all_holdings_async as db_get_all_holdings_async,
        upsert_holding_async as db_upsert_holding_async,
        delete_holding_async as db_delete_holding_async,
        get_watchlist_async as db_get_watchlist_async,
        add_to_watchlist_async as db_add_to_watchlist_async,
        remove_from_watchlist_async as db_remove_from_watchlist_async,
        save_memo_async as db_save_memo_async,
        get_memos_async as db_get_memos_async
    )
    from models import UserProfileDB, PortfolioHoldingDB, WatchlistDB, DecisionMemoDB


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application lifecycle and gracefully closes async client pools."""
    yield
    await llm_client.close()


app = FastAPI(
    title="Vibe Finance Multi-Agent API",
    description="Multi-Agent system for quantitative, fundamental RAG, and behavioral investment synthesis",
    version="1.0.0",
    lifespan=lifespan
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
    historical_date: str = Field(default="2024-10-15")
    holding_days: Optional[int] = Field(default=90, ge=7, le=365)

class UploadDocumentRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=20)
    document_title: str = Field(default="Corporate Filing")
    section: str = Field(default="Management Discussion")
    content: str = Field(min_length=10)
    source_type: Optional[str] = "USER_UPLOAD"


# --- Endpoints ---

@app.get("/api/health")
async def get_health():
    # Probe market data service status asynchronously without blocking event loop
    sample_stock = await asyncio.to_thread(market_service.get_market_data, "NVDA")
    is_live = sample_stock.get("feed_status") == "LIVE_YAHOO"
    return {
        "status": "healthy",
        "version": "1.0.0",
        "degraded_mode": not is_live,
        "active_feed": "LIVE_YAHOO" if is_live else "STALE_FALLBACK_EOD",
        "rag_corpus_documents": len(RAG_DOCUMENTS)
    }

@app.get("/api/stocks")
async def list_stocks():
    return await asyncio.to_thread(market_service.list_tracked_stocks)

@app.get("/api/stocks/{ticker}/history")
async def get_stock_history(ticker: str, timeframe: Optional[str] = "1M"):
    return await asyncio.to_thread(market_service.get_history, ticker=ticker, timeframe=timeframe or "1M")

@app.post("/api/analyze")
async def analyze_stock(req: AnalyzeRequest):
    overall_start = time.perf_counter()
    ticker = req.ticker.upper()
    sim_stale = bool(req.simulated_stale_data)
    sim_timeout = bool(req.simulated_rag_timeout)
    
    # 1. Fetch market data non-blockingly via worker thread
    stock_info = await asyncio.to_thread(market_service.get_stock_info, ticker)
    company_name = stock_info["name"] if stock_info else f"{ticker} Corp"
    market_data = await asyncio.to_thread(market_service.get_market_data, ticker, sim_stale)
    
    # 2. Resolve User Profile
    profile_dict = req.user_profile.model_dump() if req.user_profile else {}
    resolved_profile = await asyncio.to_thread(user_profiler.get_profile, profile_dict)

    # 3. Parallel Agent Orchestration with asyncio.gather (Zero Event-Loop Blocking)
    quant_task = quant_agent.analyze_async(ticker, market_data)
    rag_task = rag_agent.analyze_async(ticker, simulated_rag_timeout=sim_timeout)
    behavioral_task = behavioral_agent.analyze_async(ticker, resolved_profile, market_data)

    results = await asyncio.gather(quant_task, rag_task, behavioral_task, return_exceptions=True)

    quant_res = results[0] if not isinstance(results[0], Exception) else {
        "name": "Quantitative Analyst", "stance": "NEUTRAL", "score": 50, "latency_ms": 1,
        "signals": ["Quantitative analysis recovered from error"], "metrics": {}
    }
    rag_res = results[1] if not isinstance(results[1], Exception) else {
        "name": "Fundamental Researcher", "stance": "NEUTRAL", "score": 50, "latency_ms": 1,
        "timed_out": True, "key_findings": ["RAG agent exception handled gracefully"], "citations": []
    }
    behavioral_res = results[2] if not isinstance(results[2], Exception) else {
        "name": "Behavioral Risk Manager", "stance": "CAUTION", "score": 50, "latency_ms": 1,
        "user_risk_profile": "moderate", "behavioral_adjustments": []
    }

    # 4. Async Debate & Consensus Arbitrage
    debate_res = await debate_engine.conduct_debate_async(
        ticker=ticker,
        quant_result=quant_res,
        rag_result=rag_res,
        behavioral_result=behavioral_res,
        stale_data=sim_stale
    )

    # 5. Async Synthesis
    synthesis_res = await synthesis_agent.synthesize_async(
        ticker=ticker,
        quant_result=quant_res,
        rag_result=rag_res,
        behavioral_result=behavioral_res,
        debate_result=debate_res,
        market_data=market_data
    )

    # 6. Sentiment Timeline non-blocking
    sentiment_shift = await asyncio.to_thread(rag_retriever.get_sentiment_timeline, ticker)

    # 7. Telemetry & Degradation Flags
    total_elapsed_ms = max(int((time.perf_counter() - overall_start) * 1000), 1)

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

    telemetry_data = await asyncio.to_thread(
        audit_logger.log_analysis,
        ticker=ticker,
        total_ms=total_elapsed_ms,
        quant_ms=quant_res["latency_ms"],
        rag_ms=rag_res["latency_ms"],
        risk_ms=behavioral_res["latency_ms"],
        vector_ms=rag_res.get("latency_ms", 1) if not sim_timeout else 0,
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
    return await asyncio.to_thread(portfolio_service.simulate_trade, req.model_dump())

@app.get("/api/portfolio")
async def get_portfolio():
    return await asyncio.to_thread(portfolio_service.get_portfolio)

@app.post("/api/backtest")
async def run_backtest(req: BacktestRequest):
    return await asyncio.to_thread(
        backtest_simulator.simulate,
        ticker=req.ticker,
        historical_date=req.historical_date,
        holding_days=req.holding_days or 90
    )

@app.get("/api/telemetry/recent")
async def get_telemetry_logs():
    return await asyncio.to_thread(audit_logger.get_recent_logs)

# --- SQLite Persistent Non-Blocking CRUD Endpoints ---

@app.get("/api/user-profile")
async def get_stored_user_profile():
    profile = await db_get_user_profile_async()
    return profile.model_dump()

@app.put("/api/user-profile")
async def update_stored_user_profile(profile: UserProfileDB):
    saved = await db_upsert_user_profile_async(profile)
    return saved.model_dump()

@app.get("/api/portfolio/holdings")
async def get_stored_holdings():
    holdings = await db_get_all_holdings_async()
    return [h.model_dump() for h in holdings]

@app.post("/api/portfolio/holdings")
async def upsert_stored_holding(holding: PortfolioHoldingDB):
    saved = await db_upsert_holding_async(holding)
    return saved.model_dump()

@app.delete("/api/portfolio/holdings/{ticker}")
async def delete_stored_holding(ticker: str):
    success = await db_delete_holding_async(ticker)
    if not success:
        raise HTTPException(status_code=404, detail=f"Holding {ticker} not found")
    return {"status": "deleted", "ticker": ticker.upper()}

@app.get("/api/watchlist")
async def get_user_watchlist():
    items = await db_get_watchlist_async()
    return [w.model_dump() for w in items]

@app.post("/api/watchlist")
async def add_item_to_watchlist(item: WatchlistDB):
    saved = await db_add_to_watchlist_async(item)
    return saved.model_dump()

@app.delete("/api/watchlist/{ticker}")
async def remove_item_from_watchlist(ticker: str):
    success = await db_remove_from_watchlist_async(ticker)
    if not success:
        raise HTTPException(status_code=404, detail=f"Watchlist item {ticker} not found")
    return {"status": "deleted", "ticker": ticker.upper()}

@app.post("/api/memos")
async def save_decision_memo(memo: DecisionMemoDB):
    saved = await db_save_memo_async(memo)
    return saved.model_dump()

@app.get("/api/memos")
async def list_decision_memos():
    memos = await db_get_memos_async()
    return [m.model_dump() for m in memos]

@app.post("/api/rag/upload")
async def upload_rag_document(req: UploadDocumentRequest):
    chunks = await asyncio.to_thread(
        rag_retriever.ingest_document,
        ticker=req.ticker,
        document_title=req.document_title,
        section=req.section,
        content=req.content,
        source_type=req.source_type or "USER_UPLOAD"
    )
    return {
        "status": "indexed",
        "ticker": req.ticker.upper(),
        "chunks_created": len(chunks),
        "total_corpus_documents": len(rag_retriever.documents)
    }

@app.post("/api/rag/upload-file")
async def upload_rag_file(
    file: UploadFile = File(...),
    ticker: str = Form(...),
    document_title: Optional[str] = Form("Uploaded Corporate Document")
):
    """Handles PDF and text file uploads, extracting text via PyMuPDF and indexing into VectorStore."""
    filename = file.filename or "uploaded_file"
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in ["pdf", "txt", "md"]:
        raise HTTPException(status_code=400, detail="Only .pdf, .txt, and .md files are supported for vector ingestion")

    content_bytes = await file.read()
    if len(content_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds maximum 10MB limit")

    if ext == "pdf":
        chunks = await asyncio.to_thread(
            rag_retriever.ingest_pdf,
            pdf_bytes=content_bytes,
            ticker=ticker,
            document_title=document_title or filename
        )
    else:
        text = content_bytes.decode("utf-8", errors="ignore")
        chunks = await asyncio.to_thread(
            rag_retriever.ingest_document,
            ticker=ticker,
            document_title=document_title or filename,
            section="Uploaded File",
            content=text,
            source_type="FILE_UPLOAD"
        )

    return {
        "status": "indexed",
        "ticker": ticker.upper(),
        "filename": filename,
        "chunks_created": len(chunks),
        "total_corpus_documents": len(rag_retriever.documents)
    }
