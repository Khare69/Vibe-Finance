import sys
import os
import warnings

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.backtest.simulator import backtest_simulator

def main():
    print("Testing Walk-Forward Point-in-Time Backtesting Engine...")

    # Test 1: Historical simulation on NVDA across multiple dates
    dates_to_test = ["2025-04-10", "2025-09-15", "2026-01-10"]
    for d in dates_to_test:
        print(f"\n1. Testing NVDA on date {d} (90-day holding horizon):")
        res = backtest_simulator.simulate("NVDA", historical_date=d, holding_days=90)
        print(f"  Entry: {res['entry_price']} on {res['historical_date']}")
        print(f"  Exit:  {res['exit_price']} on {res['exit_date']}")
        print(f"  Realized Return: {res['actual_return_pct']:+.2f}% (Profitable: {res['was_profitable']})")
        print(f"  Agent Recommendation Then: {res['agent_recommendation_then']} (Quant: {res['quant_score_then']}, RAG: {res['rag_score_then']})")
        print(f"  PIT Indicators: RSI={res['point_in_time_metrics']['rsi_14']}, 50-SMA={res['point_in_time_metrics']['sma_50']}")
        print(f"  Trajectory steps: {len(res['trajectory'])} trading days")
        
        assert res["entry_price"] > 0
        assert res["exit_price"] > 0
        assert len(res["trajectory"]) > 0
        # Verify return formula
        expected_ret = round(((res["exit_price"] - res["entry_price"]) / res["entry_price"]) * 100, 2)
        assert abs(res["actual_return_pct"] - expected_ret) < 0.1, f"Return math mismatch: {res['actual_return_pct']} vs {expected_ret}"

    # Test 2: Test on Indian asset (RELIANCE)
    print("\n2. Testing RELIANCE on 2025-10-15 (60-day horizon):")
    rel_res = backtest_simulator.simulate("RELIANCE", historical_date="2025-10-15", holding_days=60)
    print(f"  Entry: ₹{rel_res['entry_price']} on {rel_res['historical_date']}")
    print(f"  Exit:  ₹{rel_res['exit_price']} on {rel_res['exit_date']}")
    print(f"  Realized Return: {rel_res['actual_return_pct']:+.2f}%")
    print(f"  Reasoning Snapshot: {rel_res['reasoning_snapshot']}")
    assert rel_res["entry_price"] > 0
    assert len(rel_res["trajectory"]) > 0

    # Test 3: Confirm no static lookup table - dynamic date shifts produce dynamic entry prices
    print("\n3. Testing dynamic sensitivity to dates (No static lookup table):")
    res_a = backtest_simulator.simulate("AAPL", historical_date="2025-05-01", holding_days=30)
    res_b = backtest_simulator.simulate("AAPL", historical_date="2025-08-01", holding_days=30)
    print(f"  AAPL on 2025-05-01: Entry {res_a['entry_price']}, Return {res_a['actual_return_pct']:+.2f}%")
    print(f"  AAPL on 2025-08-01: Entry {res_b['entry_price']}, Return {res_b['actual_return_pct']:+.2f}%")
    assert res_a["entry_price"] != res_b["entry_price"], "Entry prices must vary dynamically with date!"
    assert res_a["historical_date"] != res_b["historical_date"]

    print("\nSub-phase 3.1 Point-in-Time Simulation PASSED successfully!")

if __name__ == "__main__":
    main()
