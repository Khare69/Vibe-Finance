import time
from typing import Dict, Any, List


class QuantAgent:
    """
    Quantitative Analyst Agent.
    Evaluates algorithmic momentum, moving average alignments (SMA 50, SMA 200),
    Wilder's RSI-14, 12/26/9 MACD, and 20-day volume anomalies using deterministic math.
    """

    def analyze(self, ticker: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.perf_counter()
        metrics = market_data.get("metrics", {})
        price = market_data.get("current_price", 100.0)
        vol_ratio = market_data.get("volume_anomaly_ratio", 1.0)
        rsi = metrics.get("rsi_14", 50.0)
        sma_50 = metrics.get("sma_50", price)
        sma_200 = metrics.get("sma_200", price * 0.95)
        momentum = metrics.get("momentum_score", 50)
        macd = metrics.get("macd", {"line": 0.0, "signal": 0.0, "hist": 0.0})

        signals: List[str] = []

        # RSI signals
        if rsi >= 70:
            signals.append(f"RSI at {rsi:.1f} signals overbought zone with elevated mean-reversion risk")
        elif rsi <= 35:
            signals.append(f"RSI at {rsi:.1f} signals deeply oversold conditions with rebound potential")
        elif rsi >= 50:
            signals.append(f"RSI at {rsi:.1f} indicates steady bullish momentum without overbought stretch")
        else:
            signals.append(f"RSI at {rsi:.1f} reflects softening momentum below neutral 50 centerline")

        symbol = market_data.get("symbol", "₹" if ticker.upper() in ["RELIANCE", "TCS", "INFY", "HDFCBANK"] else "$")

        # Moving average signals
        if price > sma_50 and sma_50 > sma_200:
            signals.append(f"Price {symbol}{price:.1f} above 50-SMA ({symbol}{sma_50:.1f}) and 200-SMA ({symbol}{sma_200:.1f}) in Golden Cross alignment")
        elif price < sma_50 and sma_50 < sma_200:
            signals.append(f"Price {symbol}{price:.1f} trading below both 50-SMA and 200-SMA under Death Cross overhead resistance")
        elif price > sma_50 and price < sma_200:
            signals.append(f"Price {symbol}{price:.1f} recovering above 50-SMA ({symbol}{sma_50:.1f}) but capped by long-term 200-SMA ({symbol}{sma_200:.1f})")
        else:
            signals.append(f"Price consolidating between 50-SMA ({symbol}{sma_50:.1f}) and 200-SMA ({symbol}{sma_200:.1f})")

        # Volume anomaly signals
        if vol_ratio >= 1.5:
            signals.append(f"Volume surge at {vol_ratio:.2f}x 20-day moving average confirming institutional participation")
        elif vol_ratio < 0.75:
            signals.append(f"Volume subdued at {vol_ratio:.2f}x 20-day average indicating lack of institutional conviction")
        else:
            signals.append(f"Volume tracking in-line with historical baseline at {vol_ratio:.2f}x 20-day average")

        # MACD signals
        hist = macd.get("hist", 0.0)
        macd_line = macd.get("line", 0.0)
        macd_sig = macd.get("signal", 0.0)
        if hist > 0:
            signals.append(f"MACD histogram positive (+{hist:.2f}) with MACD line ({macd_line:.2f}) above signal ({macd_sig:.2f}) confirming upside momentum")
        else:
            signals.append(f"MACD histogram negative ({hist:.2f}) reflecting decelerating momentum and trend exhaustion")

        # Derive Quant score (0-100) and stance
        quant_score = int(momentum)

        if quant_score >= 65:
            stance = "BULLISH"
        elif quant_score <= 42:
            stance = "BEARISH"
        else:
            stance = "NEUTRAL"

        # Calculate actual latency without artificial floors
        elapsed_ms = max(int((time.perf_counter() - start_time) * 1000), 1)

        return {
            "name": "Quantitative Analyst",
            "stance": stance,
            "score": quant_score,
            "latency_ms": elapsed_ms,
            "signals": signals,
            "metrics": {
                "rsi_14": round(rsi, 1),
                "sma_50": round(sma_50, 1),
                "sma_200": round(sma_200, 1),
                "macd": macd,
                "volume_anomaly_ratio": round(vol_ratio, 2),
                "momentum_score": quant_score
            }
        }

    async def analyze_async(self, ticker: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Asynchronous interface for parallel agent execution."""
        return self.analyze(ticker, market_data)


quant_agent = QuantAgent()
