// Central API Service connecting to FastAPI backend with resilient client-side fallback

import {
  MOCK_STOCKS,
  MOCK_ANALYSES,
  MOCK_USER_PORTFOLIO,
  MOCK_BACKTESTS,
} from './mockData';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function checkSystemHealth() {
  try {
    const res = await fetch(`${BASE_URL}/api/health`, { method: 'GET' });
    if (!res.ok) throw new Error('Health check non-200');
    const data = await res.json();
    return { ...data, is_backend_offline: false };
  } catch (err) {
    return {
      status: 'offline_mock',
      version: '1.0.0',
      degraded_mode: true,
      active_feed: 'OFFLINE_DEMO_SNAPSHOT',
      rag_corpus_documents: 0,
      is_backend_offline: true,
    };
  }
}

export async function getStocks() {
  try {
    const res = await fetch(`${BASE_URL}/api/stocks`);
    if (!res.ok) throw new Error('Failed to fetch stocks from backend');
    return await res.json();
  } catch (err) {
    // Graceful fallback to mock stocks
    return MOCK_STOCKS;
  }
}

export async function runMultiAgentAnalysis({
  ticker = 'RELIANCE',
  userProfile = {
    risk_level: 'conservative',
    investment_horizon: 'medium',
    panic_sell_tendency: 0.8,
    preferred_sectors: ['Energy', 'Tech'],
    portfolio_cash: 250000,
  },
  explainMode = 'beginner',
  simulatedStaleData = false,
  simulatedRagTimeout = false,
}) {
  try {
    const res = await fetch(`${BASE_URL}/api/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ticker,
        user_profile: userProfile,
        explain_mode: explainMode,
        simulated_stale_data: simulatedStaleData,
        simulated_rag_timeout: simulatedRagTimeout,
      }),
    });

    if (!res.ok) throw new Error('Backend analyze failed');
    const data = await res.json();
    return { ...data, is_offline_mock: false };
  } catch (err) {
    // Robust mock handling with transparent demo snapshot tagging
    const base = MOCK_ANALYSES[ticker] || MOCK_ANALYSES['RELIANCE'];
    const cloned = JSON.parse(JSON.stringify(base));
    cloned.is_offline_mock = true;
    cloned.price_data.feed_status = 'OFFLINE_DEMO_SNAPSHOT';
    cloned.telemetry.degraded_data = true;
    cloned.telemetry.degraded_reason =
      'Backend unreachable: Showing offline demo snapshot. Run backend for live agent analysis.';

    // Handle Stale Live Data Simulation
    if (simulatedStaleData) {
      cloned.price_data.feed_status = 'STALE_FALLBACK_EOD';
      cloned.price_data.confidence_penalty = 25.0;
      cloned.telemetry.degraded_data = true;
      cloned.telemetry.degraded_reason =
        'Live streaming socket disconnected: Utilizing EOD cache snapshot (-25 confidence penalty applied)';
      cloned.debate.confidence_calibration_score = Math.max(
        25,
        cloned.debate.confidence_calibration_score - 25
      );
      cloned.telemetry.confidence_score =
        cloned.debate.confidence_calibration_score;
    }

    // Handle RAG Timeout Simulation
    if (simulatedRagTimeout) {
      cloned.agents.rag.timed_out = true;
      cloned.agents.rag.score = 0;
      cloned.agents.rag.key_findings = [
        'WARNING: Vector RAG corpus retrieval timed out after 3,000ms threshold.',
        'Synthesizer falling back gracefully to Pure Quantitative + Behavioral rules engine.',
      ];
      cloned.agents.rag.citations = [];
      cloned.telemetry.vector_retrieval_ms = 3000;
      cloned.telemetry.degraded_reason =
        'RAG Vector Timeout: Fallback active with technical momentum signals only.';
      cloned.debate.quant_vs_rag_conflict =
        'RAG Agent unavailable (Timeout). Analysis synthesized with Quant indicators and User Risk profile constraints only.';
      cloned.debate.confidence_calibration_score = Math.round(
        cloned.debate.confidence_calibration_score * 0.75
      );
      cloned.telemetry.confidence_score =
        cloned.debate.confidence_calibration_score;
    }

    return cloned;
  }
}

export async function simulateTrade({
  ticker,
  action = 'BUY',
  quantity = 10,
  price,
  userProfile = { risk_level: 'conservative' },
}) {
  try {
    const res = await fetch(`${BASE_URL}/api/simulate-trade`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ticker,
        action,
        quantity,
        price,
        user_profile: userProfile,
      }),
    });
    if (!res.ok) throw new Error('Trade simulation error');
    return await res.json();
  } catch (err) {
    // Client-side fallback behavioral nudge logic
    const isConservative =
      userProfile.risk_level?.toLowerCase() === 'conservative';
    const isVolatile = ticker === 'TSLA' || ticker === 'NVDA';

    if (isConservative && isVolatile && action === 'BUY') {
      return {
        warning_triggered: true,
        nudge_message: `Hold on! Your profile is Conservative, but ${ticker} has high annualized volatility (~48-52%) and momentum swings. Adding this allocation increases your portfolio Beta to 1.24 and Tech concentration significantly.`,
        portfolio_delta: {
          current_tech_pct: 46.5,
          projected_tech_pct: 58.2,
          current_beta: 0.88,
          projected_beta: 1.24,
          cash_remaining: 320000,
        },
        suggested_alternative:
          'Consider an index ETF or a low-beta blue chip like TCS or INFY to protect your downside threshold.',
      };
    }

    return {
      warning_triggered: false,
      nudge_message: `Trade for ${quantity} shares of ${ticker} aligns within your ${userProfile.risk_level} risk tolerance boundaries.`,
      portfolio_delta: {
        current_tech_pct: 46.5,
        projected_tech_pct: 48.0,
        current_beta: 0.88,
        projected_beta: 0.91,
        cash_remaining: 380000,
      },
      suggested_alternative: null,
    };
  }
}

export async function getPortfolio() {
  try {
    const res = await fetch(`${BASE_URL}/api/portfolio`);
    if (!res.ok) throw new Error('Portfolio fetch error');
    return await res.json();
  } catch (err) {
    return MOCK_USER_PORTFOLIO;
  }
}

export async function runBacktest({ ticker, historicalDate, holdingDays = 90 }) {
  try {
    const res = await fetch(`${BASE_URL}/api/backtest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ticker,
        historical_date: historicalDate,
        holding_days: holdingDays,
      }),
    });
    if (!res.ok) throw new Error('Backtest error');
    return await res.json();
  } catch (err) {
    const isINR = !['NVDA', 'TSLA', 'AAPL', 'MSFT'].includes(ticker?.toUpperCase());
    const baseEntry = ticker?.toUpperCase() === 'RELIANCE' ? 1220.0 : (ticker?.toUpperCase() === 'TCS' ? 3850.0 : 135.0);
    const baseExit = ticker?.toUpperCase() === 'RELIANCE' ? 1340.0 : (ticker?.toUpperCase() === 'TCS' ? 4210.0 : 182.0);
    const retPct = Number((((baseExit - baseEntry) / baseEntry) * 100).toFixed(2));

    const found = MOCK_BACKTESTS[ticker] || {
      historical_date: historicalDate || '2024-10-15',
      exit_date: '2025-01-13',
      holding_days: holdingDays,
      holding_days_actual: 62,
      entry_price: baseEntry,
      exit_price: baseExit,
      actual_return_pct: retPct,
      agent_recommendation_then: 'BUY',
      quant_score_then: 76,
      rag_score_then: 72,
      was_profitable: true,
      performance_metrics: {
        cagr_pct: Number((retPct * 3.8).toFixed(2)),
        max_drawdown_pct: -4.3,
        sharpe_ratio: 1.82,
        sortino_ratio: 2.34,
        annualized_volatility_pct: 19.4,
        benchmark_name: isINR ? 'Nifty 50 (^NSEI)' : 'S&P 500 (^GSPC)',
        benchmark_return_pct: 3.25,
        alpha_pct: Number((retPct - 3.25).toFixed(2)),
        win_rate_trajectory_pct: 74.2,
      },
      point_in_time_metrics: {
        rsi_14: 58.4,
        sma_50: Number((baseEntry * 0.98).toFixed(2)),
        sma_200: Number((baseEntry * 0.94).toFixed(2)),
        macd_hist: 1.82,
        volume_anomaly_ratio: 1.34,
      },
      trajectory: [
        { date: '2024-10-15', price: baseEntry, return_pct: 0.0 },
        { date: '2024-11-01', price: Number((baseEntry * 1.02).toFixed(2)), return_pct: 2.0 },
        { date: '2024-11-15', price: Number((baseEntry * 1.01).toFixed(2)), return_pct: 1.0 },
        { date: '2024-12-01', price: Number((baseEntry * 1.05).toFixed(2)), return_pct: 5.0 },
        { date: '2024-12-15', price: Number((baseEntry * 1.07).toFixed(2)), return_pct: 7.0 },
        { date: '2025-01-13', price: baseExit, return_pct: retPct },
      ],
      reasoning_snapshot:
        'Point-in-time multi-factor analysis confirmed bullish momentum breakout with strong fundamental margin resilience.',
    };
    return found;
  }
}

export async function getStockHistory(ticker = 'RELIANCE', timeframe = '1M') {
  try {
    const res = await fetch(`${BASE_URL}/api/stocks/${ticker}/history?timeframe=${timeframe}`);
    if (!res.ok) throw new Error('Failed to fetch stock history');
    return await res.json();
  } catch (err) {
    // Generate synthetic mock history if backend unreachable
    const baseP = 2845.50;
    const bars = [];
    const today = new Date();
    for (let i = 30; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(d.getDate() - i);
      const close = baseP * (0.95 + Math.sin(i * 0.4) * 0.05);
      bars.push({
        time: d.toISOString().split('T')[0],
        open: close * 0.995,
        high: close * 1.01,
        low: close * 0.99,
        close: close,
        volume: 1500000 + Math.floor(Math.sin(i) * 300000)
      });
    }
    return bars;
  }
}

export async function uploadRagDocument({ ticker, document_title, section, content }) {
  try {
    const res = await fetch(`${BASE_URL}/api/rag/upload`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticker, document_title, section, content })
    });
    if (!res.ok) throw new Error('Upload document failed');
    return await res.json();
  } catch (err) {
    return { status: 'mock_indexed', ticker, chunks_created: 2 };
  }
}

export async function saveDecisionMemo(memo) {
  try {
    const res = await fetch(`${BASE_URL}/api/memos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(memo)
    });
    if (!res.ok) throw new Error('Save memo failed');
    return await res.json();
  } catch (err) {
    return memo;
  }
}

export async function updateStoredUserProfile(profile) {
  try {
    const res = await fetch(`${BASE_URL}/api/user-profile`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile)
    });
    if (!res.ok) throw new Error('Update profile failed');
    return await res.json();
  } catch (err) {
    return profile;
  }
}

export async function getStoredUserProfile() {
  try {
    const res = await fetch(`${BASE_URL}/api/user-profile`);
    if (!res.ok) throw new Error('Fetch profile failed');
    return await res.json();
  } catch (err) {
    return null;
  }
}

export async function getStoredMemos() {
  try {
    const res = await fetch(`${BASE_URL}/api/memos`);
    if (!res.ok) throw new Error('Fetch memos failed');
    return await res.json();
  } catch (err) {
    return [];
  }
}
