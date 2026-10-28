import time
from typing import Dict, Any, List

class BehavioralAgent:
    """
    Behavioral Risk Manager Agent.
    Evaluates individual investor psychology, panic selling propensity,
    risk capacity, and downweights speculative momentum to protect capital.
    """

    TOLERABLE_DRAWDOWN = {
        "conservative": 0.08,
        "moderate": 0.15,
        "aggressive": 0.28
    }

    def analyze(self, ticker: str, user_profile: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.perf_counter()
        risk_level = user_profile.get("risk_level", "moderate").lower()
        panic_tendency = float(user_profile.get("panic_sell_tendency", 0.5))
        horizon = user_profile.get("investment_horizon", "medium").lower()

        # Stock volatility characteristics
        metrics = market_data.get("metrics", {})
        price = market_data.get("current_price", 100.0)
        vol_ratio = market_data.get("volume_anomaly_ratio", 1.0)
        
        # Volatility estimation based on ticker
        stock_volatilities = {
            "RELIANCE": 0.22,
            "TCS": 0.18,
            "INFY": 0.24,
            "NVDA": 0.46,
            "AAPL": 0.21,
            "TSLA": 0.52
        }
        annual_vol = stock_volatilities.get(ticker.upper(), 0.25)
        weekly_drawdown_risk = annual_vol * 0.65  # Estimated tail weekly move

        max_tolerable = self.TOLERABLE_DRAWDOWN.get(risk_level, 0.15)
        adjustments: List[str] = []

        # Behavioral adjustment checks
        if panic_tendency >= 0.7:
            adjustments.append(f"User has high panic-sell score ({panic_tendency:.2f}). Down-weighting breakout momentum.")
        elif panic_tendency <= 0.3:
            adjustments.append(f"User exhibits high emotional discipline (panic-sell score {panic_tendency:.2f}). Allowing normal risk budget.")

        if weekly_drawdown_risk > max_tolerable:
            adjustments.append(
                f"Downside volatility risk of {int(weekly_drawdown_risk * 100)}% exceeds user's stated max tolerable weekly drawdown (-{int(max_tolerable * 100)}%)."
            )
        else:
            adjustments.append(
                f"Downside volatility risk of {int(weekly_drawdown_risk * 100)}% remains within user's tolerable risk threshold ({int(max_tolerable * 100)}%)."
            )

        if horizon == "short" and annual_vol > 0.30:
            adjustments.append("Short horizon combined with high volatility increases sequence-of-returns risk.")
        else:
            adjustments.append("Suggesting staggered SIP / staged accumulation rather than lump-sum entry.")

        # Behavioral score calculation
        base_score = 65
        if risk_level == "conservative":
            base_score -= 15
        elif risk_level == "aggressive":
            base_score += 15

        if panic_tendency > 0.6:
            base_score -= int((panic_tendency - 0.5) * 30)

        if weekly_drawdown_risk > max_tolerable:
            base_score -= 10

        behavioral_score = max(20, min(85, base_score))

        if behavioral_score < 55 or panic_tendency > 0.65:
            stance = "CAUTION"
        elif behavioral_score >= 70:
            stance = "FAVORABLE"
        else:
            stance = "MODERATE"

        elapsed_ms = max(int((time.perf_counter() - start_time) * 1000), 1)

        return {
            "name": "Behavioral Risk Manager",
            "stance": stance,
            "score": behavioral_score,
            "latency_ms": elapsed_ms,
            "user_risk_profile": risk_level,
            "behavioral_adjustments": adjustments
        }

behavioral_agent = BehavioralAgent()
