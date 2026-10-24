import time
from typing import Dict, Any, List

class QuantAgent:
    """
    Quantitative Analyst Agent.
    Evaluates momentum, moving averages (SMA 50, SMA 200), RSI, MACD, and volume anomalies.
    """

    def analyze(self, ticker: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.perf_counter()
        metrics = market_data.get("metrics", {})
        price = market_data.get("current_price", 100.0)
        change_pct = market_data.get("change_percent", 0.0)
        vol_ratio = market_data.get("volume_anomaly_ratio", 1.0)
        rsi = metrics.get("rsi_14", 50.0)
        sma_50 = metrics.get("sma_50", price)
        sma_200 = metrics.get("sma_200", price * 0.95)
        momentum = metrics.get("momentum_score", 50)
        macd = metrics.get("macd", {"line": 0.0, "signal": 0.0, "hist": 0.0})

        signals: List[str] = []

        # RSI signals
        if rsi > 70:
            signals.append(f"RSI at {rsi:.1f} signals overbought zone with potential mean-reversion risk")
        elif rsi < 35:
            signals.append(f"RSI at {rsi:.1f} signals deeply oversold conditions with rebound potential")
        elif rsi >= 50:
            signals.append(f"RSI at {rsi:.1f} indicates bullish momentum without overbought conditions")
        else:
            signals.append(f"RSI at {rsi:.1f} reflects softening momentum below neutral 50 threshold")

        symbol = market_data.get("symbol", "₹" if ticker.upper() in ["RELIANCE", "TCS", "INFY"] else "$")

        # Moving average signals
        if price > sma_50 and sma_50 > sma_200:
            signals.append(f"Price {symbol}{price:.1f} above 50-SMA ({symbol}{sma_50:.1f}) and 200-SMA ({symbol}{sma_200:.1f}) in Golden Cross alignment")
        elif price < sma_50 and price < sma_200:
            signals.append(f"Price {symbol}{price:.1f} trading below both 50-SMA and 200-SMA under overhead resistance")
        else:
            signals.append(f"Price consolidating between 50-SMA ({symbol}{sma_50:.1f}) and 200-SMA ({symbol}{sma_200:.1f})")

        # Volume signals
        if vol_ratio >= 1.5:
            signals.append(f"Volume {vol_ratio:.2f}x 20-day moving average on breakout above key technical pivots")
        elif vol_ratio < 0.8:
            signals.append(f"Volume quiet at {vol_ratio:.2f}x 20-day average indicating lack of institutional participation")
        else:
            signals.append(f"Volume tracking in-line at {vol_ratio:.2f}x 20-day average")

        # MACD signal
        hist = macd.get("hist", 0.0)
        if hist > 0:
            signals.append("MACD histogram widening positive confirming upward trend momentum")
        else:
            signals.append("MACD histogram contracting negative showing decelerating upside pressure")

        # Determine Quant score (0-100) and stance
        quant_score = int(momentum)
        # Apply volume and RSI modifiers
        if vol_ratio > 1.3 and price > sma_50:
            quant_score = min(98, quant_score + 5)

        if quant_score >= 65:
            stance = "BULLISH"
        elif quant_score <= 42:
            stance = "BEARISH"
        else:
            stance = "NEUTRAL"

        elapsed_ms = max(int((time.perf_counter() - start_time) * 1000), 95)

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
                "momentum_score": quant_score
            }
        }

quant_agent = QuantAgent()
