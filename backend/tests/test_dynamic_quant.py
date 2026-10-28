import sys
import os
import warnings

# Ensure UTF-8 stdout on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Suppress pandas deprecation warnings during test
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.data.market_service import market_service
from backend.agents.quant_agent import quant_agent

def main():
    print("Testing dynamic market data for tracked tickers...")
    stocks = market_service.list_tracked_stocks()
    print(f"Total tracked stocks: {len(stocks)}")
    assert len(stocks) >= 7, f"Expected at least 7 stocks, got {len(stocks)}"
    
    for s in stocks:
        ticker = s['ticker']
        price = s['current_price']
        curr = s['currency']
        change = s['change_percent']
        vol = s['volume_anomaly_ratio']
        print(f"  {ticker:<10} | {curr} {price:>9.2f} | Change: {change:>6.2f}% | Vol Anomaly: {vol:>4.2f}x")
    
    print("\nTesting QuantAgent on RELIANCE:")
    mdata = market_service.get_market_data("RELIANCE")
    assert "metrics" in mdata
    assert "rsi_14" in mdata["metrics"]
    assert "sma_50" in mdata["metrics"]
    assert "sma_200" in mdata["metrics"]
    assert "macd" in mdata["metrics"]
    
    quant_res = quant_agent.analyze("RELIANCE", mdata)
    print(f"  Stance: {quant_res['stance']} (Score: {quant_res['score']}/100, Latency: {quant_res['latency_ms']}ms)")
    print(f"  RSI-14: {quant_res['metrics']['rsi_14']}, 50-SMA: {quant_res['metrics']['sma_50']}, 200-SMA: {quant_res['metrics']['sma_200']}")
    for sig in quant_res['signals']:
        print(f"    - {sig}")

    print("\nTesting QuantAgent on NVDA:")
    nvda_data = market_service.get_market_data("NVDA")
    nvda_res = quant_agent.analyze("NVDA", nvda_data)
    print(f"  Stance: {nvda_res['stance']} (Score: {nvda_res['score']}/100, Latency: {nvda_res['latency_ms']}ms)")
    print(f"  RSI-14: {nvda_res['metrics']['rsi_14']}, 50-SMA: {nvda_res['metrics']['sma_50']}, 200-SMA: {nvda_res['metrics']['sma_200']}")
    for sig in nvda_res['signals']:
        print(f"    - {sig}")

    print("\nSub-phase 1.1 verification PASSED successfully!")

if __name__ == "__main__":
    main()
