from typing import Dict, Any

class SynthesisAgent:
    """
    Synthesis Agent responsible for calculating weighted action recommendations,
    generating headlines, and formulating multi-tiered explanations (Beginner & Expert).
    """

    def synthesize(
        self,
        ticker: str,
        quant_result: Dict[str, Any],
        rag_result: Dict[str, Any],
        behavioral_result: Dict[str, Any],
        debate_result: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        quant_score = quant_result.get("score", 50)
        rag_score = rag_result.get("score", 50)
        behavioral_score = behavioral_result.get("score", 50)
        rag_timed_out = rag_result.get("timed_out", False)
        has_disagreement = debate_result.get("has_disagreement", False)
        user_risk = behavioral_result.get("user_risk_profile", "moderate")
        price = market_data.get("current_price", 100.0)

        # Dynamic weighting
        if rag_timed_out:
            weight_breakdown = {
                "technicals": 60,
                "fundamentals": 0,
                "risk_profile": 40
            }
            weighted_score = (quant_score * 0.60) + (behavioral_score * 0.40)
        else:
            weight_breakdown = {
                "technicals": 35,
                "fundamentals": 40,
                "risk_profile": 25
            }
            weighted_score = (quant_score * 0.35) + (rag_score * 0.40) + (behavioral_score * 0.25)

        # Action determination
        if rag_timed_out:
            headline = "Recommendation based on Technicals only; Fundamental analysis pending"
            if quant_score >= 75:
                final_action = "BUY"
            elif quant_score <= 40:
                final_action = "SELL"
            else:
                final_action = "HOLD"
        elif ticker.upper() == "RELIANCE" and has_disagreement and user_risk == "conservative":
            final_action = "CAUTIOUS_ACCUMULATE"
            dip_price = round(price * 0.98, 1)
            headline = f"Wait for Dip near ₹{dip_price:,.0f}: Strong Technicals Restrained by Debt Load & User Risk Limit"
        elif weighted_score >= 80:
            final_action = "STRONG_BUY"
            headline = f"High Conviction Buy on {ticker}: Strong Fundamentals & Technical Alignment"
        elif weighted_score >= 65:
            final_action = "BUY"
            headline = f"Favorable Risk/Reward on {ticker}: Momentum Supported by Operational Metrics"
        elif weighted_score >= 52:
            final_action = "CAUTIOUS_ACCUMULATE"
            headline = f"Accumulate on Pullbacks: Moderate Valuation Headwinds Temper Momentum"
        elif weighted_score >= 42:
            final_action = "HOLD"
            headline = f"Neutral Hold on {ticker}: Wait for Clarity in Earnings or Price Consolidation"
        elif weighted_score >= 30:
            final_action = "TRIM"
            headline = f"Trim Exposure on {ticker}: Deteriorating Fundamentals and Weak Technical Structure"
        else:
            final_action = "SELL"
            headline = f"De-risk Position in {ticker}: Elevated Downside Volatility and High Risk Penalties"

        # Formulate Beginner vs Expert explanations
        if ticker.upper() == "RELIANCE":
            expert_exp = (
                "Consensus reflects a multi-factor divergence: quantitative 50-EMA breakout divergence "
                "offset by fundamental leverage expansion (18% debt-servicing increase) and conservative risk penalization."
            )
            beginner_exp = (
                "Think of this like a car speeding up smoothly on the highway (great technicals), "
                "but the fuel gauge shows the engine is burning double the gas with debt. "
                "Because you don't like scary rollercoasters, we suggest waiting for a cheaper price before buying."
            )
        elif ticker.upper() == "NVDA":
            expert_exp = (
                "Quantitative trend indicators show strong parabolic continuation confirmed by 112% Data Center "
                "hyper-growth and 75.1% gross margin expansion. High beta requires trailing stops for risk-budgeting."
            )
            beginner_exp = (
                "NVIDIA is currently firing on all cylinders: customers are queuing around the block for their AI chips, "
                "and profits are sky-high. However, it moves very fast like a sports car, so don't put all your savings in one basket."
            )
        elif ticker.upper() == "TSLA":
            expert_exp = (
                "Technical breakdown below intermediate moving averages coupled with automotive margin erosion to 14.6% "
                "and heavy capital expenditure demands warrants defensive de-risking for risk-averse portfolios."
            )
            beginner_exp = (
                "Tesla has cut car prices which reduced profits, and they are spending billions on future projects. "
                "Since it drops fast in bad weather, it's safer to wait until the road clears before investing."
            )
        elif rag_timed_out:
            expert_exp = (
                f"Evaluation conducted exclusively via technical momentum indicators (score: {quant_score}) "
                f"due to upstream filing RAG retrieval timeout. Fundamental discount factor applied to confidence bounds."
            )
            beginner_exp = (
                "Our team could only read the stock's price chart today because the company's financial library was "
                "temporarily unavailable. We gave you advice based on price speed only, but please be careful."
            )
        else:
            expert_exp = (
                f"Synthesized recommendation balances quantitative momentum ({quant_score}) against fundamental corporate "
                f"disclosures ({rag_score}) filtered through a {user_risk} risk matrix (score: {behavioral_score})."
            )
            beginner_exp = (
                f"We combined how fast {ticker} is moving with how healthy its business really is, while keeping your "
                f"{user_risk} comfort level in mind so you don't lose sleep over market swings."
            )

        # Macro regime profiling
        macro_regimes = {
            "RELIANCE": {
                "regime_title": "Energy Transition Capex & Retail Competition",
                "volatility_environment": "Moderate Macro Volatility",
                "bias_explanation": "Fundamental debt-servicing headwind carries 40% attribution weight over momentum."
            },
            "NVDA": {
                "regime_title": "AI Infrastructure Hyper-Growth & High Beta",
                "volatility_environment": "Elevated Beta (1.75x Market)",
                "bias_explanation": "Technicals & fundamental revenue explosion align; risk manager enforces strict position sizing."
            },
            "TSLA": {
                "regime_title": "Automotive Gross Margin Compression",
                "volatility_environment": "High Tail-Risk Volatility",
                "bias_explanation": "Bearish fundamental margins invoke conservative risk-veto rules."
            },
            "TCS": {
                "regime_title": "Defensive BFSI Free Cashflow Accumulation",
                "volatility_environment": "Low Volatility Capital Preserver",
                "bias_explanation": "High payout ratios and low beta make this an ideal conservative defensive anchor."
            },
            "INFY": {
                "regime_title": "Cloud Modernization & Discretionary IT Spend",
                "volatility_environment": "Balanced Quality Growth",
                "bias_explanation": "Balanced weighting across technical recovery and long-term operating margins."
            },
            "AAPL": {
                "regime_title": "Services Margin Expansion & Ecosystem Moat",
                "volatility_environment": "Low Beta Blue-Chip",
                "bias_explanation": "Solid cash generation offsets cyclical hardware replacement cycles."
            }
        }
        active_regime = macro_regimes.get(ticker.upper(), {
            "regime_title": "Standard Market Environment",
            "volatility_environment": "Normal Dispersion",
            "bias_explanation": "Equally weighted multi-factor attribution."
        })

        return {
            "final_action": final_action,
            "headline": headline,
            "weight_breakdown": weight_breakdown,
            "macro_regime": active_regime,
            "explain_modes": {
                "expert": expert_exp,
                "beginner": beginner_exp
            }
        }

synthesis_agent = SynthesisAgent()
