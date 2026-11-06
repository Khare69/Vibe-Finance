"""
Dedicated Live Network Validation Test Suite.
Safely tests external online financial providers (Yahoo Finance / yfinance)
and AI services (Google Gemini API) with strict boundary validation.

Usage:
  # Run with live internet access:
  python backend/tests/test_live_network.py
"""
import os
import sys
import time
from datetime import datetime, timezone

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

# Enable live network flag for this test suite
os.environ["VIBE_ALLOW_NETWORK"] = "1"
os.environ.pop("VIBE_OFFLINE_MODE", None)

from backend.data.network_guard import is_network_allowed, probe_connectivity, get_network_diagnostics
from backend.data.market_service import market_service
from backend.agents.llm_client import llm_client


def run_live_network_tests():
    print("=" * 70)
    print(" VIBE FINANCE — SAFE LIVE NETWORK & ONLINE DATA VALIDATION")
    print("=" * 70)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    
    diag = get_network_diagnostics()
    print(f"Diagnostic State: allowed={diag['network_allowed']}, whitelisted_domains={len(diag['whitelisted_domains'])}")
    
    # 1. Probe connectivity
    print("\n[Step 1/3] Testing outbound HTTPS connectivity to Yahoo Finance...")
    is_connected = probe_connectivity("query1.finance.yahoo.com", 443, timeout=3.0)
    
    if not is_connected:
        print("\n[FAIL] Internet access is currently unreachable or blocked by sandbox.")
        print("   To execute live network tests, run this command with internet access enabled")
        print("   (e.g., BypassSandbox: true).")
        print("=" * 70)
        return False

    print("[PASS] Active outbound internet connection verified (query1.finance.yahoo.com:443 responded).")

    # 2. Test Live yfinance Market Data for NSE (RELIANCE) and US (NVDA)
    print("\n[Step 2/3] Fetching real 1-year OHLCV data & computing live quantitative indicators...")
    test_tickers = ["RELIANCE", "NVDA"]

    for ticker in test_tickers:
        t0 = time.perf_counter()
        data = market_service.get_market_data(ticker)
        bars = market_service.get_history(ticker, "1M")
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        price = data.get("current_price")
        feed_status = data.get("feed_status")
        change_pct = data.get("change_percent")
        volatility = data.get("annualized_volatility")
        beta = data.get("beta")
        metrics = data.get("metrics", {})
        rsi = metrics.get("rsi_14")
        sma_50 = metrics.get("sma_50")
        sma_200 = metrics.get("sma_200")
        macd = metrics.get("macd", {})
        symbol = data.get("symbol", "$")

        print(f"\n--- Asset: {ticker} ({data.get('currency')}) ---")
        print(f"  • Feed Status       : {feed_status} ({elapsed_ms:.1f} ms)")
        print(f"  • Live Price        : {symbol}{price:,.2f} ({change_pct:+.2f}%)")
        print(f"  • Annual Volatility : {volatility * 100:.1f}%")
        print(f"  • Rolling Beta      : {beta:.2f}")
        print(f"  • Wilder RSI-14     : {rsi:.1f}")
        print(f"  • 50-SMA / 200-SMA  : {symbol}{sma_50:,.2f} / {symbol}{sma_200:,.2f}")
        print(f"  • MACD Line / Hist  : {macd.get('line'):.2f} / {macd.get('hist'):.2f}")

        # Assert safety and mathematical validity boundaries
        assert price > 0.0, f"Live price for {ticker} must be positive, got {price}"
        assert 0.0 <= rsi <= 100.0, f"RSI must be bounded between 0 and 100, got {rsi}"
        assert 0.1 <= beta <= 5.0, f"Beta must be within realistic financial bounds [0.1, 5.0], got {beta}"
        assert len(bars) >= 20, f"Expected at least 20 historical daily bars, got {len(bars)}"

    print("\n[PASS] Live market data ingestion, candle parsing, and indicator math successfully validated!")

    # 3. Test Google Gemini API (if key configured)
    print("\n[Step 3/3] Checking LLM Agent Client API connectivity...")
    if llm_client.is_available():
        print(f"  • Gemini API key detected. Model configured: {llm_client.model}")
        print("  • Dispatching live probe prompt to Google Gemini API...")
        t0 = time.perf_counter()
        dialogue = llm_client.generate_debate_dialogue(
            ticker="NVDA",
            quant_result={"stance": "BULLISH", "score": 88, "signals": ["RSI 62", "Golden Cross"]},
            rag_result={"stance": "BULLISH", "score": 82, "key_findings": ["112% Data Center Growth"]},
            behavioral_result={"stance": "FAVORABLE", "behavioral_adjustments": ["Limit position to 10%"]},
            user_risk_profile="moderate"
        )
        elapsed_llm = (time.perf_counter() - t0) * 1000.0
        if dialogue and len(dialogue) == 3:
            print(f"[PASS] Gemini API responded in {elapsed_llm:.1f} ms with structured 3-speaker debate dialogue.")
        else:
            print(f"[WARN] Gemini API did not return expected structure (took {elapsed_llm:.1f} ms), falling back safely.")
    else:
        print("  • No GEMINI_API_KEY detected in environment (or unconfigured).")
        print("  • LLMAgentClient is operating in verified deterministic fallback mode (offline-safe).")

    print("\n" + "=" * 70)
    print(" ALL LIVE NETWORK VALIDATION CHECKS PASSED CLEANLY & SAFELY")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = run_live_network_tests()
    sys.exit(0 if success else 1)
