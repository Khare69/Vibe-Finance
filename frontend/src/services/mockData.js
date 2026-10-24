// Comprehensive mock data mirroring API_CONTRACTS.md for resilient offline & fallback operation

export const MOCK_STOCKS = [
  {
    ticker: "RELIANCE",
    name: "Reliance Industries Ltd.",
    exchange: "NSE",
    sector: "Energy / Retail",
    price: 2845.50,
    change: 1.45,
    currency: "INR",
    symbol: "₹",
  },
  {
    ticker: "TCS",
    name: "Tata Consultancy Services",
    exchange: "NSE",
    sector: "IT Services",
    price: 4120.80,
    change: -0.35,
    currency: "INR",
    symbol: "₹",
  },
  {
    ticker: "INFY",
    name: "Infosys Limited",
    exchange: "NSE",
    sector: "IT Services",
    price: 1890.25,
    change: 0.85,
    currency: "INR",
    symbol: "₹",
  },
  {
    ticker: "NVDA",
    name: "NVIDIA Corporation",
    exchange: "NASDAQ",
    sector: "Semiconductors",
    price: 142.30,
    change: 3.12,
    currency: "USD",
    symbol: "$",
  },
  {
    ticker: "AAPL",
    name: "Apple Inc.",
    exchange: "NASDAQ",
    sector: "Consumer Electronics",
    price: 231.50,
    change: -0.42,
    currency: "USD",
    symbol: "$",
  },
  {
    ticker: "TSLA",
    name: "Tesla Inc.",
    exchange: "NASDAQ",
    sector: "Automotive / AI",
    price: 248.80,
    change: 4.80,
    currency: "USD",
    symbol: "$",
  },
];

export const MOCK_ANALYSES = {
  RELIANCE: {
    ticker: "RELIANCE",
    company_name: "Reliance Industries Ltd.",
    timestamp: new Date().toISOString(),
    price_data: {
      current_price: 2845.50,
      currency: "INR",
      symbol: "₹",
      change_percent: 1.45,
      volume_anomaly_ratio: 1.62,
      feed_status: "LIVE",
      confidence_penalty: 0.0,
      high_52w: 3217.90,
      low_52w: 2220.30,
      volume: "8.4M",
    },
    agents: {
      quant: {
        name: "Quantitative Analyst",
        stance: "BULLISH",
        score: 82,
        latency_ms: 115,
        signals: [
          "RSI at 58.4 indicates healthy bullish momentum without overbought conditions",
          "Volume 1.62x 20-day moving average on confirmed breakout above 50-EMA",
          "MACD histogram widening positive with Golden Cross on the daily frame",
        ],
        metrics: {
          rsi_14: 58.4,
          sma_50: 2780.2,
          sma_200: 2650.0,
          momentum_score: 84,
          atr_volatility: 38.4,
        },
      },
      rag: {
        name: "Fundamental Researcher",
        stance: "BEARISH",
        score: 41,
        latency_ms: 342,
        timed_out: false,
        key_findings: [
          "Management highlighted 18% increase in capex debt servicing costs in Q3 transcript",
          "Retail division margin compression of 140 bps cited due to discounting pressure",
          "Substantial working capital drain observed in recent regulatory filing",
        ],
        citations: [
          {
            id: "cite-rel-1",
            document_title: "Q3 FY26 Earnings Call Transcript",
            source_type: "SEBI_TRANSCRIPT",
            section: "Management Q&A - Page 8",
            excerpt:
              "While top-line growth stayed resilient, debt servicing on our accelerated 5G and green energy capex expanded 18% YoY, creating transient headwinds on net cash flows.",
            full_context:
              "OPERATOR: We have the next question from Morgan Stanley. Please go ahead.\n\nANALYST: Thank you. Could you provide granularity on the interest expense trajectory given your continuous capital expenditure in downstream petrochemicals and the green gigafactories?\n\nCFO: While top-line growth stayed resilient, debt servicing on our accelerated 5G and green energy capex expanded 18% YoY, creating transient headwinds on net cash flows. We anticipate peak debt leverage over the next two quarters before moderation begins in FY27 as our solar cell facilities achieve commercial ramp.\n\nANALYST: Understood. And regarding retail discounting...",
            relevance_score: 0.94,
            date: "Jan 19, 2026",
          },
          {
            id: "cite-rel-2",
            document_title: "Annual Report & Financial Statements (Form SEBI-LODR)",
            source_type: "SEBI_FILING",
            section: "Management Discussion & Analysis - Segment Performance",
            excerpt:
              "Core retail EBITDA margin faced a contraction of approximately 140 basis points owing to aggressive competitive promotional pricing across tier-2 cities.",
            full_context:
              "Segmental Highlights: Consumer Retail operations delivered gross footfalls of 280 million. However, core retail EBITDA margin faced a contraction of approximately 140 basis points owing to aggressive competitive promotional pricing across tier-2 cities. Grocery and fast-fashion inventory holding days widened from 48 days to 59 days.",
            relevance_score: 0.89,
            date: "Dec 30, 2025",
          },
        ],
      },
      behavioral_risk: {
        name: "Behavioral Risk Manager",
        stance: "CAUTION",
        score: 52,
        latency_ms: 85,
        user_risk_profile: "conservative",
        behavioral_adjustments: [
          "User has high panic-sell score (0.80). Down-weighting breakout momentum.",
          "Downside volatility risk of 14% exceeds user's stated max tolerable weekly drawdown (-8%).",
          "Suggesting staggered SIP / staged accumulation rather than lump-sum entry.",
        ],
      },
    },
    debate: {
      has_disagreement: true,
      quant_vs_rag_conflict:
        "Quant sees technical breakout above 50-EMA with 1.62x volume, while Fundamental RAG flags 18% capex debt jump and retail margin contraction.",
      confidence_calibration_score: 63,
      resolution_summary:
        "The technical breakout is tempered by fundamental debt headwinds. For this conservative user, technical bullishness is restrained, producing a Cautious Hold / Accumulate on Dips stance.",
      dialogue_steps: [
        {
          speaker: "Quant Agent",
          avatarColor: "emerald",
          text: "Reliance has formed a textbook cup-and-handle pattern with 1.62x volume expansion. Technical probabilities favor an immediate test of ₹2,950.",
        },
        {
          speaker: "Fundamental RAG Agent",
          avatarColor: "rose",
          text: "Caution: The Q3 transcript explicitly records CFO commentary regarding an 18% jump in debt service charges and 140 bps retail margin compression. This rally lacks fundamental free cash flow support.",
        },
        {
          speaker: "Behavioral Risk Manager",
          avatarColor: "amber",
          text: "Given the user's high panic-selling score (0.80), a volatile false breakout could trigger emotional liquidation. I am vetoing an aggressive Buy and recommending staggered entry near support.",
        },
      ],
    },
    synthesis: {
      final_action: "CAUTIOUS_ACCUMULATE",
      headline: "Wait for Dip near ₹2,790: Strong Technicals Restrained by Debt Load & User Risk Limit",
      weight_breakdown: {
        technicals: 35,
        fundamentals: 40,
        risk_profile: 25,
      },
      explain_modes: {
        expert:
          "Consensus reflects a multi-factor divergence: quantitative 50-EMA breakout divergence offset by fundamental leverage expansion (18% debt-servicing increase) and conservative risk penalization.",
        beginner:
          "Think of this like a car speeding up smoothly on the highway (great technicals), but the fuel gauge shows the engine is burning double the gas with debt. Because you don't like scary rollercoasters, we suggest waiting for a cheaper price before buying.",
      },
    },
    sentiment_shift: {
      ticker: "RELIANCE",
      current_quarter: "Q3 FY26",
      previous_quarter: "Q2 FY26",
      overall_sentiment_score_current: -0.15,
      overall_sentiment_score_previous: 0.42,
      keyword_frequencies: [
        { word: "headwinds", current_count: 9, previous_count: 2 },
        { word: "capex", current_count: 14, previous_count: 6 },
        { word: "margin pressure", current_count: 7, previous_count: 1 },
        { word: "robust demand", current_count: 4, previous_count: 11 },
        { word: "green gigafactory", current_count: 11, previous_count: 8 },
      ],
    },
    telemetry: {
      total_execution_ms: 542,
      vector_retrieval_ms: 128,
      documents_scanned: 8,
      confidence_score: 63,
      degraded_data: false,
      degraded_reason: null,
    },
  },

  NVDA: {
    ticker: "NVDA",
    company_name: "NVIDIA Corporation",
    timestamp: new Date().toISOString(),
    price_data: {
      current_price: 142.30,
      currency: "USD",
      symbol: "$",
      change_percent: 3.12,
      volume_anomaly_ratio: 2.15,
      feed_status: "LIVE",
      confidence_penalty: 0.0,
      high_52w: 149.77,
      low_52w: 45.20,
      volume: "68.2M",
    },
    agents: {
      quant: {
        name: "Quantitative Analyst",
        stance: "BULLISH",
        score: 94,
        latency_ms: 98,
        signals: [
          "All-time high retest with institutional accumulation spikes",
          "Relative Strength Index (RSI) at 66 with clean higher-high continuation",
          "Implied volatility skew heavily favoring upside call buying",
        ],
        metrics: {
          rsi_14: 66.2,
          sma_50: 128.4,
          sma_200: 104.5,
          momentum_score: 96,
          atr_volatility: 4.8,
        },
      },
      rag: {
        name: "Fundamental Researcher",
        stance: "BULLISH",
        score: 89,
        latency_ms: 310,
        timed_out: false,
        key_findings: [
          "Blackwell GPU production yield verified at 99.2% in SEC 10-Q filing notes",
          "Hyperscaler capex commitment statements (MSFT, GOOGL, META) totaled $210B forward spend",
          "Gross margins held at exceptional 75.1% defying custom ASIC competition",
        ],
        citations: [
          {
            id: "cite-nvda-1",
            document_title: "SEC Form 10-Q Quarterly Report",
            source_type: "SEC_10Q",
            section: "Item 2 - Management's Discussion and Analysis",
            excerpt:
              "Data Center revenue grew 112% year-over-year, primarily driven by the Blackwell architecture platform ramp across tier-1 cloud providers.",
            full_context:
              "Revenue from our Data Center segment reached historic milestones during the quarter. Data Center revenue grew 112% year-over-year, primarily driven by the Blackwell architecture platform ramp across tier-1 cloud providers. Supply chain bottlenecks previously experienced in advanced packaging (CoWoS) have eased significantly with secondary foundry partnerships.",
            relevance_score: 0.98,
            date: "Nov 22, 2025",
          },
          {
            id: "cite-nvda-2",
            document_title: "Executive Earnings Call Presentation",
            source_type: "SEC_TRANSCRIPT",
            section: "CEO Opening Remarks - AI Infrastructure",
            excerpt:
              "Demand for sovereign AI clusters and reasoning models has exceeded even our most optimistic FY26 baseline forecasts.",
            full_context:
              "JENSEN HUANG: The generative AI inflection point has transitioned into the reasoning AI era. Demand for sovereign AI clusters and reasoning models has exceeded even our most optimistic FY26 baseline forecasts. Every national government is allocating compute budgets equivalent to critical civil infrastructure.",
            relevance_score: 0.95,
            date: "Nov 20, 2025",
          },
        ],
      },
      behavioral_risk: {
        name: "Behavioral Risk Manager",
        stance: "MODERATE",
        score: 68,
        latency_ms: 78,
        user_risk_profile: "conservative",
        behavioral_adjustments: [
          "NVDA beta is 1.68; sizing must be capped at 6% of portfolio to protect drawdowns.",
          "Extreme trailing rally increases downside tail-risk if macro interest rates tick up.",
        ],
      },
    },
    debate: {
      has_disagreement: false,
      quant_vs_rag_conflict:
        "High consensus: Quant metrics show persistent momentum breakout while Fundamental RAG confirms unprecedented AI infrastructure demand.",
      confidence_calibration_score: 88,
      resolution_summary:
        "High-conviction alignment between technical momentum and earnings acceleration. Risk manager recommends position sizing limit to prevent overexposure.",
      dialogue_steps: [
        {
          speaker: "Quant Agent",
          avatarColor: "emerald",
          text: "Momentum is exceptionally strong. 50-day SMA is rising at a 42-degree slope, and volume distribution indicates continued institutional accumulation.",
        },
        {
          speaker: "Fundamental RAG Agent",
          avatarColor: "emerald",
          text: "Agreed. 10-Q filing records 112% YoY Data Center expansion with gross margins steady at 75.1%. RAG retrieval surfaces zero inventory glut signals.",
        },
        {
          speaker: "Behavioral Risk Manager",
          avatarColor: "amber",
          text: "Both signals are positive, but let's remember this investor's profile: limit initial position to 6% to prevent emotional panic during standard 10% tech pullbacks.",
        },
      ],
    },
    synthesis: {
      final_action: "STRONG_BUY",
      headline: "High Institutional Conviction: Momentum Supported by Record Data Center Free Cash Flow",
      weight_breakdown: {
        technicals: 45,
        fundamentals: 40,
        risk_profile: 15,
      },
      explain_modes: {
        expert:
          "Alpha consensus is confirmed by dual-factor confluence: strong trend continuation over 50-EMA coupled with Blackwell architecture margin resilience at 75.1%.",
        beginner:
          "NVIDIA is like the world's most popular bakery that has a line around the block every single morning, and all the biggest restaurants have pre-paid orders for the next year. It's doing great, just keep your portion reasonable!",
      },
    },
    sentiment_shift: {
      ticker: "NVDA",
      current_quarter: "Q3 FY26",
      previous_quarter: "Q2 FY26",
      overall_sentiment_score_current: 0.82,
      overall_sentiment_score_previous: 0.65,
      keyword_frequencies: [
        { word: "hyperscaler demand", current_count: 22, previous_count: 14 },
        { word: "Blackwell", current_count: 31, previous_count: 18 },
        { word: "supply constraints", current_count: 5, previous_count: 12 },
        { word: "sovereign AI", current_count: 14, previous_count: 6 },
      ],
    },
    telemetry: {
      total_execution_ms: 486,
      vector_retrieval_ms: 110,
      documents_scanned: 11,
      confidence_score: 88,
      degraded_data: false,
      degraded_reason: null,
    },
  },

  TSLA: {
    ticker: "TSLA",
    company_name: "Tesla Inc.",
    timestamp: new Date().toISOString(),
    price_data: {
      current_price: 248.80,
      currency: "USD",
      symbol: "$",
      change_percent: 4.80,
      volume_anomaly_ratio: 1.88,
      feed_status: "LIVE",
      confidence_penalty: 0.0,
      high_52w: 271.00,
      low_52w: 138.80,
      volume: "82.4M",
    },
    agents: {
      quant: {
        name: "Quantitative Analyst",
        stance: "BULLISH",
        score: 76,
        latency_ms: 105,
        signals: [
          "Sharp 4.8% gap up breaking above 200-day moving average",
          "Short-covering volume surge across retail brokerage feeds",
          "RSI crossed 63 indicating rapid momentum revival",
        ],
        metrics: {
          rsi_14: 63.8,
          sma_50: 221.4,
          sma_200: 215.1,
          momentum_score: 78,
          atr_volatility: 9.2,
        },
      },
      rag: {
        name: "Fundamental Researcher",
        stance: "BEARISH",
        score: 35,
        latency_ms: 360,
        timed_out: false,
        key_findings: [
          "Automotive gross margins excluding regulatory credits shrank to 14.6%",
          "Price discounts in Europe and China reduced average selling price by $2,300 per unit",
          "Robotaxi regulatory approval timeline delayed by minimum 18 months per filings",
        ],
        citations: [
          {
            id: "cite-tsla-1",
            document_title: "SEC Form 10-K Annual Report",
            source_type: "SEC_10K",
            section: "Automotive Revenue & Margin Realization",
            excerpt:
              "Auto gross margin ex-regulatory credits declined to 14.6% due to continued price adjustments in highly contested EV markets.",
            full_context:
              "Vehicle Deliveries & Cost Structure: Total vehicle deliveries grew 4% year-over-year. Auto gross margin ex-regulatory credits declined to 14.6% due to continued price adjustments in highly contested EV markets. Cost of goods sold per vehicle decreased to $35,100, partially offsetting price cuts.",
            relevance_score: 0.96,
            date: "Jan 28, 2026",
          },
        ],
      },
      behavioral_risk: {
        name: "Behavioral Risk Manager",
        stance: "DANGER",
        score: 28,
        latency_ms: 92,
        user_risk_profile: "conservative",
        behavioral_adjustments: [
          "Tesla volatility (52% annualized) is incompatible with conservative portfolio goals.",
          "High sentiment meme correlation triggers strict sizing restriction (< 3%).",
        ],
      },
    },
    debate: {
      has_disagreement: true,
      quant_vs_rag_conflict:
        "High Disagreement! Technical surge driven by short squeeze vs sharp fundamental erosion in auto margins and delayed autonomy milestones.",
      confidence_calibration_score: 51,
      resolution_summary:
        "Quant breakout is heavily penalized by poor automotive free-cash-flow conversion and extreme behavioral beta. Rated as a speculative high-risk trade.",
      dialogue_steps: [
        {
          speaker: "Quant Agent",
          avatarColor: "emerald",
          text: "Tesla broke above the 200-SMA on heavy call volume. Breakout momentum targets $270.",
        },
        {
          speaker: "Fundamental RAG Agent",
          avatarColor: "rose",
          text: "Divergence warning: Core auto gross margins ex-credits dropped to 14.6%. The valuation relies entirely on AI/Robotaxi optionality with zero near-term earnings yield.",
        },
        {
          speaker: "Behavioral Risk Manager",
          avatarColor: "rose",
          text: "VETO: This stock has a 52% annualized volatility. A conservative investor will likely panic-sell on the inevitable 15% retracement. Do not chase.",
        },
      ],
    },
    synthesis: {
      final_action: "TRIM",
      headline: "Volatile Short Squeeze Diverging from Weakening Automotive Margin Fundamentals",
      weight_breakdown: {
        technicals: 25,
        fundamentals: 45,
        risk_profile: 30,
      },
      explain_modes: {
        expert:
          "Macro valuation dislocation: High retail gamma squeeze driving price while underlying automotive EBIT margins compress to 6.2%, creating severe tail-risk asymmetry.",
        beginner:
          "Imagine a sports car driving fast while making strange clanking noises in the engine. It looks cool racing past, but taking your family on a long road trip in it right now is risky.",
      },
    },
    sentiment_shift: {
      ticker: "TSLA",
      current_quarter: "Q4 FY25",
      previous_quarter: "Q3 FY25",
      overall_sentiment_score_current: -0.32,
      overall_sentiment_score_previous: 0.18,
      keyword_frequencies: [
        { word: "price cuts", current_count: 17, previous_count: 5 },
        { word: "competition", current_count: 15, previous_count: 8 },
        { word: "robotaxi", current_count: 24, previous_count: 29 },
        { word: "margin expansion", current_count: 2, previous_count: 9 },
      ],
    },
    telemetry: {
      total_execution_ms: 557,
      vector_retrieval_ms: 135,
      documents_scanned: 9,
      confidence_score: 51,
      degraded_data: false,
      degraded_reason: null,
    },
  },

  TCS: {
    ticker: "TCS",
    company_name: "Tata Consultancy Services Ltd.",
    timestamp: new Date().toISOString(),
    price_data: {
      current_price: 4120.80,
      currency: "INR",
      symbol: "₹",
      change_percent: -0.35,
      volume_anomaly_ratio: 0.95,
      feed_status: "LIVE",
      confidence_penalty: 0.0,
      high_52w: 4585.00,
      low_52w: 3710.00,
      volume: "1.8M",
    },
    agents: {
      quant: {
        name: "Quantitative Analyst",
        stance: "NEUTRAL",
        score: 58,
        latency_ms: 110,
        signals: [
          "Consolidating within narrow 2% trading band around ₹4,100",
          "RSI at 51.2 indicates neutral sideways consolidation",
          "Low volume volatility contraction pattern",
        ],
        metrics: {
          rsi_14: 51.2,
          sma_50: 4140.0,
          sma_200: 4015.0,
          momentum_score: 55,
          atr_volatility: 26.1,
        },
      },
      rag: {
        name: "Fundamental Researcher",
        stance: "BULLISH",
        score: 74,
        latency_ms: 320,
        timed_out: false,
        key_findings: [
          "Total Contract Value (TCV) signed at $10.2B in Q3, up 14% YoY",
          "High operating cash conversion of 104% with zero balance sheet debt",
          "Attrition declined to multi-year low of 11.8%",
        ],
        citations: [
          {
            id: "cite-tcs-1",
            document_title: "SEBI Q3 Earnings Release & Financial Results",
            source_type: "SEBI_FILING",
            section: "Management Commentary - Deal Inflows",
            excerpt:
              "Deal momentum remained strong with quarterly TCV of $10.2 billion, powered by BFSI cloud modernization and cybersecurity engagements.",
            full_context:
              "Operational Highlights: Net profit margin stood steady at 24.3%. Deal momentum remained strong with quarterly TCV of $10.2 billion, powered by BFSI cloud modernization and cybersecurity engagements. North American client discretionary spending showed early signs of stabilization.",
            relevance_score: 0.93,
            date: "Jan 12, 2026",
          },
        ],
      },
      behavioral_risk: {
        name: "Behavioral Risk Manager",
        stance: "SAFE",
        score: 85,
        latency_ms: 82,
        user_risk_profile: "conservative",
        behavioral_adjustments: [
          "Low beta (0.68) and high dividend stability match conservative user preferences perfectly.",
          "Minimal downside tail risk with proven 20-year cash flow stability.",
        ],
      },
    },
    debate: {
      has_disagreement: false,
      quant_vs_rag_conflict:
        "Subdued technical consolidation is backed by robust balance sheet fundamentals and high cash conversion.",
      confidence_calibration_score: 79,
      resolution_summary:
        "Ideal defensive anchor for risk-averse investors. While not a momentum runner, solid deal pipeline and 104% cash conversion offer peace of mind.",
      dialogue_steps: [
        {
          speaker: "Quant Agent",
          avatarColor: "slate",
          text: "Price action is muted. Oscillators are flat at 51 RSI, indicating sideways consolidation.",
        },
        {
          speaker: "Fundamental RAG Agent",
          avatarColor: "emerald",
          text: "The underlying business is rock solid. $10.2B in new contract signings and 24.3% net profit margins ensure dividend resilience.",
        },
        {
          speaker: "Behavioral Risk Manager",
          avatarColor: "emerald",
          text: "For our conservative investor, this is exactly the defensive fortress needed to balance volatile portfolio swings.",
        },
      ],
    },
    synthesis: {
      final_action: "BUY",
      headline: "Defensive Fortress: Stable IT Cash Generation & Low Volatility for Conservative Profiles",
      weight_breakdown: {
        technicals: 20,
        fundamentals: 45,
        risk_profile: 35,
      },
      explain_modes: {
        expert:
          "Defensive yield thesis: 104% OCF/EBITDA conversion, low 0.68 beta, and stable $10.2B TCV order book provide high margin of safety in uncertain markets.",
        beginner:
          "TCS is like a reliable old house with solid brick walls. It might not double in price tomorrow, but it gives you consistent rent, doesn't leak during storms, and lets you sleep soundly at night.",
      },
    },
    sentiment_shift: {
      ticker: "TCS",
      current_quarter: "Q3 FY26",
      previous_quarter: "Q2 FY26",
      overall_sentiment_score_current: 0.38,
      overall_sentiment_score_previous: 0.12,
      keyword_frequencies: [
        { word: "deal wins", current_count: 19, previous_count: 14 },
        { word: "BFSI recovery", current_count: 11, previous_count: 4 },
        { word: "discretionary spend", current_count: 8, previous_count: 15 },
        { word: "margin defense", current_count: 13, previous_count: 9 },
      ],
    },
    telemetry: {
      total_execution_ms: 512,
      vector_retrieval_ms: 122,
      documents_scanned: 7,
      confidence_score: 79,
      degraded_data: false,
      degraded_reason: null,
    },
  },

  INFY: {
    ticker: "INFY",
    company_name: "Infosys Limited",
    timestamp: new Date().toISOString(),
    price_data: {
      current_price: 1890.25,
      currency: "INR",
      symbol: "₹",
      change_percent: 0.85,
      volume_anomaly_ratio: 1.12,
      feed_status: "LIVE",
      confidence_penalty: 0.0,
      high_52w: 1995.00,
      low_52w: 1360.00,
      volume: "3.2M",
    },
    agents: {
      quant: {
        name: "Quantitative Analyst",
        stance: "BULLISH",
        score: 71,
        latency_ms: 118,
        signals: [
          "Holding above 20-day exponential moving average",
          "Accumulation line trending positive for 3 consecutive weeks",
        ],
        metrics: {
          rsi_14: 56.5,
          sma_50: 1840.0,
          sma_200: 1650.0,
          momentum_score: 72,
          atr_volatility: 19.8,
        },
      },
      rag: {
        name: "Fundamental Researcher",
        stance: "NEUTRAL",
        score: 64,
        latency_ms: 335,
        timed_out: false,
        key_findings: [
          "Annual revenue guidance revised slightly upward to 3.75% - 4.50%",
          "Sub-contractor costs reduced by 90 bps enhancing gross margin profile",
        ],
        citations: [
          {
            id: "cite-infy-1",
            document_title: "SEBI Form 6-K Filing",
            source_type: "SEBI_FILING",
            section: "Guidance & Outlook",
            excerpt:
              "We have raised our constant currency revenue guidance for FY26 to 3.75%-4.50% based on strong enterprise AI transformation adoption.",
            full_context:
              "CEO Review: Large deal TCV came in at $2.8B. We have raised our constant currency revenue guidance for FY26 to 3.75%-4.50% based on strong enterprise AI transformation adoption across manufacturing clients.",
            relevance_score: 0.91,
            date: "Jan 15, 2026",
          },
        ],
      },
      behavioral_risk: {
        name: "Behavioral Risk Manager",
        stance: "MODERATE",
        score: 70,
        latency_ms: 88,
        user_risk_profile: "conservative",
        behavioral_adjustments: [
          "Favorable dividend yield of 2.6% cushions downside.",
          "Moderate beta of 0.82 fits balanced allocations.",
        ],
      },
    },
    debate: {
      has_disagreement: false,
      quant_vs_rag_conflict:
        "Balanced alignment: Technical rebound supported by modest guidance upgrade.",
      confidence_calibration_score: 74,
      resolution_summary:
        "Consistent performer with upward guidance revision. Modest position is recommended for quality compounders.",
      dialogue_steps: [
        {
          speaker: "Quant Agent",
          avatarColor: "emerald",
          text: "Price has steadily reclaimed all short-term moving averages with rising accumulation.",
        },
        {
          speaker: "Fundamental RAG Agent",
          avatarColor: "slate",
          text: "Guidance increase to 4.5% CC growth shows steady enterprise tech renewal, though macro enterprise budgets remain guarded.",
        },
        {
          speaker: "Behavioral Risk Manager",
          avatarColor: "emerald",
          text: "Healthy dividend support and reasonable beta make this an easy recommendation for our risk mandate.",
        },
      ],
    },
    synthesis: {
      final_action: "BUY",
      headline: "Steady Enterprise Compounding with Improving Guidance & Healthy Dividends",
      weight_breakdown: {
        technicals: 35,
        fundamentals: 40,
        risk_profile: 25,
      },
      explain_modes: {
        expert:
          "Quality compounding: 2.6% dividend yield floor, 50-EMA support at ₹1,840, and 90 bps subcontractor cost compression drive operating leverage.",
        beginner:
          "Infosys is like an experienced gardener who always produces a reliable harvest every season. Not flashy, but keeps your basket full with fresh produce.",
      },
    },
    sentiment_shift: {
      ticker: "INFY",
      current_quarter: "Q3 FY26",
      previous_quarter: "Q2 FY26",
      overall_sentiment_score_current: 0.29,
      overall_sentiment_score_previous: 0.15,
      keyword_frequencies: [
        { word: "enterprise AI", current_count: 26, previous_count: 12 },
        { word: "guidance raise", current_count: 8, previous_count: 2 },
        { word: "deal pipeline", current_count: 14, previous_count: 11 },
      ],
    },
    telemetry: {
      total_execution_ms: 541,
      vector_retrieval_ms: 129,
      documents_scanned: 8,
      confidence_score: 74,
      degraded_data: false,
      degraded_reason: null,
    },
  },

  AAPL: {
    ticker: "AAPL",
    company_name: "Apple Inc.",
    timestamp: new Date().toISOString(),
    price_data: {
      current_price: 231.50,
      currency: "USD",
      symbol: "$",
      change_percent: -0.42,
      volume_anomaly_ratio: 0.91,
      feed_status: "LIVE",
      confidence_penalty: 0.0,
      high_52w: 237.23,
      low_52w: 164.08,
      volume: "39.1M",
    },
    agents: {
      quant: {
        name: "Quantitative Analyst",
        stance: "NEUTRAL",
        score: 62,
        latency_ms: 108,
        signals: [
          "Trading just 2.4% below all-time highs near resistance band",
          "RSI at 54 with declining daily volume",
        ],
        metrics: {
          rsi_14: 54.1,
          sma_50: 226.3,
          sma_200: 202.8,
          momentum_score: 61,
          atr_volatility: 2.9,
        },
      },
      rag: {
        name: "Fundamental Researcher",
        stance: "BULLISH",
        score: 81,
        latency_ms: 315,
        timed_out: false,
        key_findings: [
          "Services revenue hit all-time record of $25B with 74% gross margin",
          "Active installed device base exceeded 2.2 billion active devices",
        ],
        citations: [
          {
            id: "cite-aapl-1",
            document_title: "SEC Form 10-K Annual Report",
            source_type: "SEC_10K",
            section: "Segment Operating Results - Services",
            excerpt:
              "Services revenue expanded 12% to $24.97 billion, with gross margin expanding to 74.2% driven by Cloud, App Store, and Payment services.",
            full_context:
              "Services segment performance remains a key driver of recurring revenue stability. Services revenue expanded 12% to $24.97 billion, with gross margin expanding to 74.2% driven by Cloud, App Store, and Payment services. Greater China hardware sales contracted 3% YoY.",
            relevance_score: 0.95,
            date: "Oct 31, 2025",
          },
        ],
      },
      behavioral_risk: {
        name: "Behavioral Risk Manager",
        stance: "SAFE",
        score: 88,
        latency_ms: 84,
        user_risk_profile: "conservative",
        behavioral_adjustments: [
          "Unparalleled balance sheet with $100B+ annual share buybacks.",
          "Low drawdown volatility makes it a portfolio foundation.",
        ],
      },
    },
    debate: {
      has_disagreement: false,
      quant_vs_rag_conflict:
        "High consensus: Steady valuation supported by high-margin software services and mega-cap capital return program.",
      confidence_calibration_score: 83,
      resolution_summary:
        "Premier ecosystem play. Services growth offset minor hardware softness in international markets.",
      dialogue_steps: [
        {
          speaker: "Quant Agent",
          avatarColor: "slate",
          text: "Price is hovering near resistance. Need a volume breakout over $238 to confirm next leg higher.",
        },
        {
          speaker: "Fundamental RAG Agent",
          avatarColor: "emerald",
          text: "Services gross margin at 74.2% on 2.2B active devices turns Apple into an annuity machine.",
        },
        {
          speaker: "Behavioral Risk Manager",
          avatarColor: "emerald",
          text: "Excellent fit for preserving capital while participating in the mega-cap ecosystem.",
        },
      ],
    },
    synthesis: {
      final_action: "BUY",
      headline: "Resilient Ecosystem Moat: 74% Services Gross Margin & $100B Buyback Safety Net",
      weight_breakdown: {
        technicals: 30,
        fundamentals: 45,
        risk_profile: 25,
      },
      explain_modes: {
        expert:
          "Annuity valuation: $25B Services run-rate with 74.2% gross margin, coupled with continuous $100B repurchase velocity, provides deep institutional downside convexity.",
        beginner:
          "Apple is like owning the busiest toll bridge in the city. Over 2 billion people cross it every day with their phones, paying small subscription tolls every month.",
      },
    },
    sentiment_shift: {
      ticker: "AAPL",
      current_quarter: "Q4 FY25",
      previous_quarter: "Q3 FY25",
      overall_sentiment_score_current: 0.54,
      overall_sentiment_score_previous: 0.41,
      keyword_frequencies: [
        { word: "Apple Intelligence", current_count: 28, previous_count: 15 },
        { word: "Services margin", current_count: 14, previous_count: 9 },
        { word: "China competition", current_count: 6, previous_count: 11 },
      ],
    },
    telemetry: {
      total_execution_ms: 507,
      vector_retrieval_ms: 120,
      documents_scanned: 8,
      confidence_score: 83,
      degraded_data: false,
      degraded_reason: null,
    },
  },
};

export const MOCK_USER_PORTFOLIO = {
  total_value: 3450000,
  cash: 450000,
  currency: "INR",
  portfolio_beta: 0.88,
  risk_level: "conservative",
  holdings: [
    { ticker: "TCS", shares: 250, avg_price: 3800, current_price: 4120.80, sector: "IT Services", weight: 30.0 },
    { ticker: "RELIANCE", shares: 320, avg_price: 2650, current_price: 2845.50, sector: "Energy / Retail", weight: 26.5 },
    { ticker: "INFY", shares: 300, avg_price: 1650, current_price: 1890.25, sector: "IT Services", weight: 16.5 },
    { ticker: "AAPL", shares: 40, avg_price: 180, current_price: 231.50, sector: "Consumer Tech", weight: 14.0 },
    { ticker: "CASH", shares: 1, avg_price: 450000, current_price: 450000, sector: "Liquidity", weight: 13.0 },
  ],
  sector_allocation: [
    { sector: "IT Services", percentage: 46.5, color: "#6366f1" },
    { sector: "Energy / Retail", percentage: 26.5, color: "#10b981" },
    { sector: "Consumer Tech", percentage: 14.0, color: "#38bdf8" },
    { sector: "Cash Reserve", percentage: 13.0, color: "#94a3b8" },
  ],
};

export const MOCK_BACKTESTS = {
  NVDA: {
    historical_date: "2025-10-15",
    entry_price: 132.50,
    exit_price: 178.20,
    actual_return_pct: 34.49,
    agent_recommendation_then: "STRONG_BUY",
    quant_score_then: 92,
    rag_score_then: 88,
    was_profitable: true,
    reasoning_snapshot: "Both Quant momentum and Q3 Data Center AI revenue guidance confirmed massive demand runway with zero supply overhang.",
  },
  TSLA: {
    historical_date: "2025-07-20",
    entry_price: 256.00,
    exit_price: 218.40,
    actual_return_pct: -14.68,
    agent_recommendation_then: "SELL",
    quant_score_then: 48,
    rag_score_then: 32,
    was_profitable: false,
    reasoning_snapshot: "Fundamental RAG correctly flagged the 240 bps automotive margin compression before the earnings call sell-off.",
  },
  RELIANCE: {
    historical_date: "2025-09-01",
    entry_price: 2710.00,
    exit_price: 2940.00,
    actual_return_pct: 8.48,
    agent_recommendation_then: "CAUTIOUS_ACCUMULATE",
    quant_score_then: 78,
    rag_score_then: 54,
    was_profitable: true,
    reasoning_snapshot: "Staggered accumulation stance captured the dip to ₹2,650 while shielding from short-term retail margin volatility.",
  },
  TCS: {
    historical_date: "2025-06-10",
    entry_price: 3820.00,
    exit_price: 4210.00,
    actual_return_pct: 10.20,
    agent_recommendation_then: "BUY",
    quant_score_then: 68,
    rag_score_then: 82,
    was_profitable: true,
    reasoning_snapshot: "High operating cash flow and resilient BFSI deal signing cushioned throughout macro rate uncertainty.",
  },
};
