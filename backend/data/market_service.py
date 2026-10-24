import math
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

class MarketService:
    """
    Market Data Service providing live/synthetic price feeds, technical indicator computations,
    and handling stale data fallback resilience modes.
    """

    STOCKS = {
        "RELIANCE": {
            "name": "Reliance Industries Ltd.",
            "sector": "Energy",
            "exchange": "NSE",
            "currency": "INR",
            "base_price": 2845.50,
            "change_pct": 1.45,
            "rsi": 58.4,
            "sma_50": 2780.20,
            "sma_200": 2650.00,
            "volume_anomaly": 1.62,
            "momentum_score": 84,
            "beta": 0.88,
            "annualized_volatility": 0.22,
            "macd": {"line": 14.2, "signal": 9.5, "hist": 4.7}
        },
        "TCS": {
            "name": "Tata Consultancy Services Ltd.",
            "sector": "Tech",
            "exchange": "NSE",
            "currency": "INR",
            "base_price": 3915.00,
            "change_pct": 0.35,
            "rsi": 49.2,
            "sma_50": 3940.00,
            "sma_200": 3820.00,
            "volume_anomaly": 0.95,
            "momentum_score": 52,
            "beta": 0.72,
            "annualized_volatility": 0.18,
            "macd": {"line": -2.1, "signal": 1.4, "hist": -3.5}
        },
        "INFY": {
            "name": "Infosys Ltd.",
            "sector": "Tech",
            "exchange": "NSE",
            "currency": "INR",
            "base_price": 1825.40,
            "change_pct": -0.80,
            "rsi": 44.5,
            "sma_50": 1860.00,
            "sma_200": 1710.00,
            "volume_anomaly": 1.15,
            "momentum_score": 46,
            "beta": 0.85,
            "annualized_volatility": 0.24,
            "macd": {"line": -5.3, "signal": -3.0, "hist": -2.3}
        },
        "NVDA": {
            "name": "NVIDIA Corporation",
            "sector": "Tech",
            "exchange": "NASDAQ",
            "currency": "USD",
            "base_price": 142.80,
            "change_pct": 3.85,
            "rsi": 72.1,
            "sma_50": 128.40,
            "sma_200": 105.60,
            "volume_anomaly": 2.15,
            "momentum_score": 93,
            "beta": 1.75,
            "annualized_volatility": 0.46,
            "macd": {"line": 6.8, "signal": 4.2, "hist": 2.6}
        },
        "AAPL": {
            "name": "Apple Inc.",
            "sector": "Tech",
            "exchange": "NASDAQ",
            "currency": "USD",
            "base_price": 234.50,
            "change_pct": 0.65,
            "rsi": 55.0,
            "sma_50": 228.10,
            "sma_200": 204.30,
            "volume_anomaly": 1.05,
            "momentum_score": 68,
            "beta": 1.05,
            "annualized_volatility": 0.21,
            "macd": {"line": 2.4, "signal": 1.9, "hist": 0.5}
        },
        "TSLA": {
            "name": "Tesla, Inc.",
            "sector": "Consumer Discretionary",
            "exchange": "NASDAQ",
            "currency": "USD",
            "base_price": 240.00,
            "change_pct": -2.40,
            "rsi": 38.2,
            "sma_50": 255.00,
            "sma_200": 215.00,
            "volume_anomaly": 1.78,
            "momentum_score": 35,
            "beta": 2.05,
            "annualized_volatility": 0.52,
            "macd": {"line": -8.5, "signal": -4.1, "hist": -4.4}
        }
    }

    def list_tracked_stocks(self) -> List[Dict[str, Any]]:
        stocks = []
        for ticker, meta in self.STOCKS.items():
            stocks.append({
                "ticker": ticker,
                "name": meta["name"],
                "sector": meta["sector"],
                "exchange": meta["exchange"],
                "currency": meta["currency"],
                "current_price": meta["base_price"],
                "change_percent": meta["change_pct"],
                "volume_anomaly_ratio": meta["volume_anomaly"],
                "beta": meta["beta"]
            })
        return stocks

    def get_stock_info(self, ticker: str) -> Optional[Dict[str, Any]]:
        ticker_up = ticker.upper()
        return self.STOCKS.get(ticker_up)

    def get_market_data(self, ticker: str, simulated_stale_data: bool = False) -> Dict[str, Any]:
        ticker_up = ticker.upper()
        stock = self.STOCKS.get(ticker_up)
        if not stock:
            # Fallback default values
            stock = {
                "name": f"{ticker_up} Corp",
                "sector": "General",
                "exchange": "NYSE",
                "currency": "USD",
                "base_price": 100.0,
                "change_pct": 0.0,
                "rsi": 50.0,
                "sma_50": 98.0,
                "sma_200": 95.0,
                "volume_anomaly": 1.0,
                "momentum_score": 50,
                "beta": 1.0,
                "annualized_volatility": 0.25,
                "macd": {"line": 0.0, "signal": 0.0, "hist": 0.0}
            }

        currency = stock.get("currency", "USD")
        symbol = "₹" if currency == "INR" else "$"
        base_price = stock.get("base_price", 100.0)
        high_52w = round(base_price * 1.18, 2)
        low_52w = round(base_price * 0.82, 2)

        if simulated_stale_data:
            return {
                "current_price": base_price,
                "change_percent": 0.0,
                "volume_anomaly_ratio": 1.0,
                "feed_status": "STALE_FALLBACK_EOD",
                "confidence_penalty": 25.0,
                "symbol": symbol,
                "currency": currency,
                "high_52w": high_52w,
                "low_52w": low_52w,
                "metrics": {
                    "rsi_14": stock["rsi"],
                    "sma_50": stock["sma_50"],
                    "sma_200": stock["sma_200"],
                    "momentum_score": stock["momentum_score"],
                    "macd": stock["macd"]
                }
            }
        else:
            return {
                "current_price": base_price,
                "change_percent": stock["change_pct"],
                "volume_anomaly_ratio": stock["volume_anomaly"],
                "feed_status": "LIVE",
                "confidence_penalty": 0.0,
                "symbol": symbol,
                "currency": currency,
                "high_52w": high_52w,
                "low_52w": low_52w,
                "metrics": {
                    "rsi_14": stock["rsi"],
                    "sma_50": stock["sma_50"],
                    "sma_200": stock["sma_200"],
                    "momentum_score": stock["momentum_score"],
                    "macd": stock["macd"]
                }
            }

market_service = MarketService()
