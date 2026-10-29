import sys
import os
import warnings

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.backtest.simulator import backtest_simulator

def main():
    print("Testing Backtest Quantitative Performance & Risk Metrics...")

    # Test 1: NVDA (US Equity vs S&P 500)
    print("\n1. Testing NVDA (US Benchmark S&P 500 comparison):")
    res_nvda = backtest_simulator.simulate("NVDA", historical_date="2025-05-15", holding_days=90)
    m = res_nvda.get("performance_metrics", {})
    print(f"  Holding Window: {res_nvda['historical_date']} to {res_nvda['exit_date']}")
    print(f"  Realized Return: {res_nvda['actual_return_pct']:+.2f}%")
    print(f"  CAGR:            {m['cagr_pct']:+.2f}%")
    print(f"  Max Drawdown:    {m['max_drawdown_pct']:.2f}%")
    print(f"  Sharpe Ratio:    {m['sharpe_ratio']:.2f}")
    print(f"  Sortino Ratio:   {m['sortino_ratio']:.2f}")
    print(f"  Ann. Volatility: {m['annualized_volatility_pct']:.2f}%")
    print(f"  Benchmark:       {m['benchmark_name']} ({m['benchmark_return_pct']:+.2f}%)")
    print(f"  Alpha:           {m['alpha_pct']:+.2f}%")
    print(f"  Trajectory Win%: {m['win_rate_trajectory_pct']:.1f}%")

    assert m["benchmark_name"] == "S&P 500", "US asset must compare against S&P 500"
    assert m["max_drawdown_pct"] <= 0.0, "Max drawdown must be non-positive"
    assert abs(m["alpha_pct"] - (res_nvda["actual_return_pct"] - m["benchmark_return_pct"])) < 0.05
    assert 0.0 <= m["win_rate_trajectory_pct"] <= 100.0

    # Test 2: RELIANCE (Indian Equity vs Nifty 50)
    print("\n2. Testing RELIANCE (Indian Benchmark NIFTY 50 comparison):")
    res_rel = backtest_simulator.simulate("RELIANCE", historical_date="2025-08-01", holding_days=60)
    m_rel = res_rel.get("performance_metrics", {})
    print(f"  Holding Window: {res_rel['historical_date']} to {res_rel['exit_date']}")
    print(f"  Realized Return: {res_rel['actual_return_pct']:+.2f}%")
    print(f"  Max Drawdown:    {m_rel['max_drawdown_pct']:.2f}%")
    print(f"  Sharpe Ratio:    {m_rel['sharpe_ratio']:.2f}")
    print(f"  Sortino Ratio:   {m_rel['sortino_ratio']:.2f}")
    print(f"  Benchmark:       {m_rel['benchmark_name']} ({m_rel['benchmark_return_pct']:+.2f}%)")
    print(f"  Alpha:           {m_rel['alpha_pct']:+.2f}%")

    assert m_rel["benchmark_name"] == "NIFTY 50", "Indian asset must compare against Nifty 50"
    assert m_rel["max_drawdown_pct"] <= 0.0
    assert abs(m_rel["alpha_pct"] - (res_rel["actual_return_pct"] - m_rel["benchmark_return_pct"])) < 0.05

    # Test 3: TCS (Indian Tech vs Nifty 50)
    print("\n3. Testing TCS:")
    res_tcs = backtest_simulator.simulate("TCS", historical_date="2025-06-15", holding_days=90)
    m_tcs = res_tcs.get("performance_metrics", {})
    print(f"  TCS Return: {res_tcs['actual_return_pct']:+.2f}% | Alpha vs Nifty: {m_tcs['alpha_pct']:+.2f}% | Sharpe: {m_tcs['sharpe_ratio']}")
    assert m_tcs["benchmark_name"] == "NIFTY 50"

    print("\nSub-phase 3.2 Performance & Risk Metrics verification PASSED successfully!")

if __name__ == "__main__":
    main()
