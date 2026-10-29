import os
import sys
import asyncio
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.agents.quant_agent import quant_agent
from backend.agents.rag_agent import rag_agent
from backend.agents.behavioral_agent import behavioral_agent
from backend.agents.debate_engine import debate_engine
from backend.agents.synthesis_agent import synthesis_agent
from backend.agents.llm_client import llm_client
from backend.data.market_service import market_service
from backend.database import (
    get_user_profile_async,
    get_all_holdings_async,
    get_watchlist_async,
    get_memos_async
)


async def main():
    print("=== Testing Async Event Loop & Parallel Multi-Agent Orchestration ===")

    # 1. Test LLM Async Client lifecycle
    print("\n--- 1. Testing LLM Client Async Pool ---")
    client = await llm_client.get_async_client()
    assert client is not None, "Async client should be initialized"
    print("Async HTTPX client successfully initialized.")

    # 2. Test Parallel Agent Execution via asyncio.gather
    print("\n--- 2. Testing Parallel Agent Execution with asyncio.gather ---")
    ticker = "NVDA"
    market_data = await asyncio.to_thread(market_service.get_market_data, ticker)
    user_profile = {"risk_level": "conservative", "panic_sell_tendency": 0.8}

    t0 = time.perf_counter()
    quant_task = quant_agent.analyze_async(ticker, market_data)
    rag_task = rag_agent.analyze_async(ticker, simulated_rag_timeout=False)
    risk_task = behavioral_agent.analyze_async(ticker, user_profile, market_data)

    quant_res, rag_res, risk_res = await asyncio.gather(quant_task, rag_task, risk_task)
    total_gather_ms = (time.perf_counter() - t0) * 1000

    print(f"Parallel gather completed in {total_gather_ms:.2f}ms")
    print(f"  Quant Agent: Score={quant_res['score']}, Stance={quant_res['stance']}")
    print(f"  RAG Agent: Score={rag_res['score']}, Stance={rag_res['stance']}, Citations={len(rag_res['citations'])}")
    print(f"  Behavioral Agent: Score={risk_res['score']}, Stance={risk_res['stance']}")

    assert quant_res["score"] > 0, "Quant score must be positive"
    assert rag_res["score"] > 0, "RAG score must be positive"
    assert risk_res["score"] > 0, "Risk score must be positive"

    # 3. Test Async Debate Engine
    print("\n--- 3. Testing Async Debate Engine ---")
    debate_res = await debate_engine.conduct_debate_async(
        ticker=ticker,
        quant_result=quant_res,
        rag_result=rag_res,
        behavioral_result=risk_res,
        stale_data=False
    )
    print(f"  Confidence Score: {debate_res['confidence_calibration_score']}/100")
    print(f"  Debate Turns: {len(debate_res['dialogue_steps'])} speakers")
    assert len(debate_res["dialogue_steps"]) == 3, "Debate must have 3 agent perspectives"

    # 4. Test Async Synthesis Agent
    print("\n--- 4. Testing Async Synthesis Agent ---")
    synthesis_res = await synthesis_agent.synthesize_async(
        ticker=ticker,
        quant_result=quant_res,
        rag_result=rag_res,
        behavioral_result=risk_res,
        debate_result=debate_res,
        market_data=market_data
    )
    print(f"  Final Action: {synthesis_res['final_action']}")
    print(f"  Headline: {synthesis_res['headline']}")
    print(f"  Weights: {synthesis_res['weight_breakdown']}")
    assert synthesis_res["final_action"] in [
        "STRONG_BUY", "BUY", "CAUTIOUS_ACCUMULATE", "HOLD", "TRIM", "SELL"
    ], f"Invalid action {synthesis_res['final_action']}"

    # 5. Test Non-blocking Database Async Queries
    print("\n--- 5. Testing Non-Blocking Async Database Wrappers ---")
    profile = await get_user_profile_async("default_user")
    holdings = await get_all_holdings_async()
    watchlist = await get_watchlist_async()
    memos = await get_memos_async()

    print(f"  User Profile: id={profile.id}, risk={profile.risk_level}, cash={profile.portfolio_cash}")
    print(f"  Holdings count: {len(holdings)}")
    print(f"  Watchlist count: {len(watchlist)}")
    print(f"  Decision memos count: {len(memos)}")

    assert profile.id == "default_user", "Profile should exist"
    assert len(holdings) > 0, "Initial seed holdings should exist"

    # 6. Test graceful connection pool closure
    print("\n--- 6. Testing Clean Shutdown ---")
    await llm_client.close()
    print("LLM async client pool closed successfully.")

    print("\n[SUCCESS] Sub-phase 4.1 Async Event Loop & Network Optimization verified!")


if __name__ == "__main__":
    asyncio.run(main())
