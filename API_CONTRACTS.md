# Vibe Finance - Multi-Agent System API & Architecture Contract

## 1. Core Endpoints

### `GET /api/health`
Status check and system mode.
Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "degraded_mode": false,
  "active_feed": "LIVE_YAHOO",
  "rag_corpus_documents": 12
}
```

### `GET /api/stocks`
List of pre-configured tracked tickers with quick summary (e.g. INFY, TCS, RELIANCE, NVDA, AAPL, TSLA).

### `POST /api/analyze`
Main multi-agent analysis request.
Request:
```json
{
  "ticker": "RELIANCE",
  "user_profile": {
    "risk_level": "conservative", // "conservative" | "moderate" | "aggressive"
    "investment_horizon": "medium", // "short" | "medium" | "long"
    "panic_sell_tendency": 0.8, // 0.0 - 1.0
    "preferred_sectors": ["Energy", "Tech"],
    "portfolio_cash": 250000
  },
  "explain_mode": "beginner", // "beginner" | "expert"
  "simulated_stale_data": false,
  "simulated_rag_timeout": false
}
```
Response:
```json
{
  "ticker": "RELIANCE",
  "company_name": "Reliance Industries Ltd.",
  "timestamp": "2026-10-24T22:30:00Z",
  "price_data": {
    "current_price": 2845.50,
    "change_percent": 1.45,
    "volume_anomaly_ratio": 1.62,
    "feed_status": "LIVE", // or "STALE_FALLBACK_EOD"
    "confidence_penalty": 0.0
  },
  "agents": {
    "quant": {
      "name": "Quantitative Analyst",
      "stance": "BULLISH", // "BULLISH" | "BEARISH" | "NEUTRAL"
      "score": 82, // 0 - 100
      "latency_ms": 115,
      "signals": [
        "RSI at 58.4 indicates bullish momentum without overbought conditions",
        "Volume 1.62x 20-day moving average on breakout above 50-EMA",
        "MACD histogram widening positive"
      ],
      "metrics": {
        "rsi_14": 58.4,
        "sma_50": 2780.2,
        "sma_200": 2650.0,
        "momentum_score": 84
      }
    },
    "rag": {
      "name": "Fundamental Researcher",
      "stance": "BEARISH", // Can disagree with Quant!
      "score": 41,
      "latency_ms": 342,
      "timed_out": false,
      "key_findings": [
        "Management highlighted 18% increase in capex debt servicing costs in Q3 transcript",
        "Retail division margin compression of 140 bps cited due to discounting pressure",
        "Substantial working capital drain observed in recent regulatory filing"
      ],
      "citations": [
        {
          "id": "cite-1",
          "document_title": "Q3 FY26 Earnings Call Transcript",
          "source_type": "SEBI_TRANSCRIPT",
          "section": "Management Q&A - Page 8",
          "excerpt": "While top-line growth stayed resilient, debt servicing on our accelerated 5G and green energy capex expanded 18% YoY, creating transient headwinds on net cash flows.",
          "relevance_score": 0.94
        },
        {
          "id": "cite-2",
          "document_title": "Annual Report & Financial Statements (Form 10-K / SEBI Filing)",
          "source_type": "SEBI_FILING",
          "section": "Management Discussion & Analysis - Segment Performance",
          "excerpt": "Core retail EBITDA margin faced a contraction of approximately 140 basis points owing to aggressive competitive promotional pricing across tier-2 cities.",
          "relevance_score": 0.89
        }
      ]
    },
    "behavioral_risk": {
      "name": "Behavioral Risk Manager",
      "stance": "CAUTION",
      "score": 52,
      "latency_ms": 85,
      "user_risk_profile": "conservative",
      "behavioral_adjustments": [
        "User has high panic-sell score (0.80). Down-weighting breakout momentum.",
        "Downside volatility risk of 14% exceeds user's stated max tolerable weekly drawdown (-8%).",
        "Suggesting staggered SIP / staged accumulation rather than lump-sum entry."
      ]
    }
  },
  "debate": {
    "has_disagreement": true,
    "quant_vs_rag_conflict": "Quant sees technical breakout above 50-EMA with strong volume, while Fundamental RAG flags rising capex debt and retail margin contraction.",
    "confidence_calibration_score": 63,
    "resolution_summary": "The technical breakout is tempered by fundamental debt headwinds. For this conservative user, technical bullishness is restrained, producing a Cautious Hold / Accumulate on Dips stance.",
    "dialogue_steps": [
      {
        "speaker": "Quant Agent",
        "text": "Reliance has formed a textbook cup-and-handle pattern with 1.62x volume expansion. Technical probabilities favor an immediate test of 2950."
      },
      {
        "speaker": "Fundamental RAG Agent",
        "text": "Caution: The Q3 transcript explicitly records CFO commentary regarding an 18% jump in debt service charges and 140 bps retail margin compression. This rally lacks fundamental free cash flow support."
      },
      {
        "speaker": "Behavioral Risk Manager",
        "text": "Given the user's high panic-selling score (0.80), a volatile false breakout could trigger emotional liquidation. I am vetoing the aggressive Buy and capping maximum allocation to 4%."
      }
    ]
  },
  "synthesis": {
    "final_action": "CAUTIOUS_ACCUMULATE", // "STRONG_BUY" | "BUY" | "CAUTIOUS_ACCUMULATE" | "HOLD" | "TRIM" | "SELL"
    "headline": "Wait for Dip near ₹2,790: Strong Technicals Restrained by Debt Load & User Risk Limit",
    "weight_breakdown": {
      "technicals": 35,
      "fundamentals": 40,
      "risk_profile": 25
    },
    "explain_modes": {
      "expert": "Consensus reflects a multi-factor divergence: quantitative 50-EMA breakout divergence offset by fundamental leverage expansion (18% debt-servicing increase) and conservative risk penalization.",
      "beginner": "Think of this like a car speeding up smoothly on the highway (great technicals), but the fuel gauge shows the engine is burning double the gas with debt. Because you don't like scary rollercoasters, we suggest waiting for a cheaper price before buying."
    }
  },
  "sentiment_shift": {
    "ticker": "RELIANCE",
    "current_quarter": "Q3 FY26",
    "previous_quarter": "Q2 FY26",
    "overall_sentiment_score_current": -0.15,
    "overall_sentiment_score_previous": 0.42,
    "keyword_frequencies": [
      {"word": "headwinds", "current_count": 9, "previous_count": 2},
      {"word": "capex", "current_count": 14, "previous_count": 6},
      {"word": "margin pressure", "current_count": 7, "previous_count": 1},
      {"word": "robust demand", "current_count": 4, "previous_count": 11}
    ]
  },
  "telemetry": {
    "total_execution_ms": 542,
    "vector_retrieval_ms": 128,
    "documents_scanned": 8,
    "confidence_score": 63,
    "degraded_data": false,
    "degraded_reason": null
  }
}
```

### `POST /api/simulate-trade`
Evaluates behavioral nudge before trade execution.
Request:
```json
{
  "ticker": "TSLA",
  "action": "BUY",
  "quantity": 10,
  "price": 240.0,
  "user_profile": { "risk_level": "conservative" }
}
```
Response:
```json
{
  "warning_triggered": true,
  "nudge_message": "Hold on! Your profile is Conservative, but TSLA has an annualized volatility of 52% and the Fundamental Agent notes zero earnings support. Adding this will increase your portfolio Tech concentration to 64%.",
  "portfolio_delta": {
    "current_tech_pct": 52.0,
    "projected_tech_pct": 64.5,
    "current_beta": 0.95,
    "projected_beta": 1.28
  },
  "suggested_alternative": "Consider an index ETF or low-beta blue chip like TCS."
}
```

### `GET /api/portfolio`
Returns current simulated user portfolio with risk heatmap data, sector breakdown, and beta.

### `POST /api/backtest`
Backtest simulator on historical date.
Request:
```json
{
  "ticker": "NVDA",
  "historical_date": "2025-10-15",
  "holding_days": 90
}
```
Response:
```json
{
  "historical_date": "2025-10-15",
  "entry_price": 132.50,
  "exit_price": 178.20,
  "actual_return_pct": 34.49,
  "agent_recommendation_then": "STRONG_BUY",
  "quant_score_then": 92,
  "rag_score_then": 88,
  "was_profitable": true,
  "reasoning_snapshot": "Both Quant momentum and Q3 Data Center AI revenue guidance confirmed massive demand runway."
}
```
