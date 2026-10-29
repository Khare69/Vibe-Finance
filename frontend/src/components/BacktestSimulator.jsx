import React, { useState, useEffect } from 'react';
import {
  History,
  Calendar,
  Play,
  CheckCircle2,
  XCircle,
  TrendingUp,
  TrendingDown,
  Clock,
  Sparkles,
  Activity,
  Shield,
  Award,
  BarChart2,
  Layers,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine
} from 'recharts';
import { runBacktest } from '../services/api';

export default function BacktestSimulator({ activeTicker = 'NVDA' }) {
  const [selectedDate, setSelectedDate] = useState('2024-10-15');
  const [holdingDays, setHoldingDays] = useState(90);
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [chartMode, setChartMode] = useState('return'); // 'return' | 'price'

  // Dynamic currency symbol determination
  const isUS = ['NVDA', 'AAPL', 'TSLA', 'MSFT', 'AMZN', 'GOOGL'].includes(
    activeTicker?.toUpperCase()
  );
  const currencySymbol = isUS ? '$' : '₹';

  const handleRunBacktest = async (e) => {
    if (e) e.preventDefault();
    setIsLoading(true);

    try {
      const data = await runBacktest({
        ticker: activeTicker,
        historicalDate: selectedDate,
        holdingDays: Number(holdingDays),
      });
      setResult(data);
    } catch (err) {
      console.error('Backtest error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Re-run whenever the active ticker changes
  useEffect(() => {
    handleRunBacktest();
  }, [activeTicker]);

  const isProfitable = (result?.actual_return_pct ?? 0) >= 0;
  const metrics = result?.performance_metrics;
  const pit = result?.point_in_time_metrics;
  const trajectory = result?.trajectory || [];

  // Recommendation Badge Styling
  const getRecommendationBadge = (rec) => {
    switch (rec) {
      case 'STRONG_BUY':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
      case 'BUY':
        return 'bg-teal-500/20 text-teal-300 border-teal-500/40';
      case 'CAUTIOUS_ACCUMULATE':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      case 'TRIM':
        return 'bg-orange-500/20 text-orange-300 border-orange-500/40';
      case 'SELL':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
      default:
        return 'bg-slate-700/40 text-slate-300 border-slate-600/40';
    }
  };

  return (
    <div className="bg-[#0f172a] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <History className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white tracking-wide uppercase">
                Deterministic Walk-Forward Backtesting Simulator
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-semibold">
                Zero Look-Ahead Bias
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Audit agent multi-factor consensus on historical snapshot dates against actual realized market outcomes
            </p>
          </div>
        </div>

        <span className="text-xs font-mono font-bold text-indigo-400 bg-indigo-950/60 px-3 py-1.5 rounded-lg border border-indigo-500/30 flex items-center gap-1.5">
          <Activity className="w-3.5 h-3.5" />
          Target: {activeTicker} ({currencySymbol})
        </span>
      </div>

      {/* Simulator Query Controls */}
      <form onSubmit={handleRunBacktest} className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">
            Historical Snapshot Date
          </label>
          <div className="relative">
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 text-xs rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>
        </div>

        <div>
          <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">
            Forward Holding Duration
          </label>
          <select
            value={holdingDays}
            onChange={(e) => setHoldingDays(Number(e.target.value))}
            className="w-full bg-slate-900 border border-slate-800 text-xs rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500 font-mono"
          >
            <option value={30}>30 Calendar Days Forward</option>
            <option value={60}>60 Calendar Days Forward</option>
            <option value={90}>90 Calendar Days Forward</option>
            <option value={180}>180 Calendar Days Forward</option>
          </select>
        </div>

        <div className="flex items-end">
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white rounded-lg text-xs font-bold transition-all shadow-md shadow-indigo-600/30 flex items-center justify-center gap-1.5"
          >
            <Play className="w-3 h-3 fill-current" />
            <span>{isLoading ? 'Replaying Historical State...' : 'Replay Point-in-Time State'}</span>
          </button>
        </div>
      </form>

      {/* Backtest Result Display */}
      {result && (
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-4">
          {/* Top Banner: Consensus Verdict & Realized Outcome */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400 block">
                Multi-Agent Consensus on {result.historical_date}
              </span>
              <div className="flex items-center gap-2 mt-1">
                <span
                  className={`px-2.5 py-0.5 rounded text-xs font-bold border font-mono ${getRecommendationBadge(
                    result.agent_recommendation_then
                  )}`}
                >
                  {result.agent_recommendation_then}
                </span>
                <span className="text-xs text-slate-300">
                  Quant Score: <b className="text-white font-mono">{result.quant_score_then}</b>/100 · RAG Score:{' '}
                  <b className="text-white font-mono">{result.rag_score_then}</b>/100
                </span>
              </div>
            </div>

            {/* Realized Forward Return */}
            <div className="text-left sm:text-right">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">
                Actual Forward Return ({result.holding_days}d / {result.holding_days_actual ?? result.holding_days} bars)
              </span>
              <div
                className={`text-xl font-mono font-black flex items-center sm:justify-end gap-1 ${
                  isProfitable ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {isProfitable ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
                {isProfitable ? '+' : ''}
                {result.actual_return_pct}%
              </div>
            </div>
          </div>

          {/* Point-in-Time Technical Indicators (What the model saw on entry date) */}
          {pit && (
            <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
              <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1.5 flex items-center gap-1.5">
                <Clock className="w-3 h-3 text-indigo-400" />
                Point-in-Time Technical Barometer ({result.historical_date}):
              </span>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs font-mono">
                <div className="bg-slate-900/90 px-2 py-1.5 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">RSI-14</span>
                  <span className={`font-bold ${pit.rsi_14 > 70 ? 'text-rose-400' : pit.rsi_14 < 30 ? 'text-emerald-400' : 'text-slate-200'}`}>
                    {pit.rsi_14?.toFixed(1)}
                  </span>
                </div>
                <div className="bg-slate-900/90 px-2 py-1.5 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">50-Day SMA</span>
                  <span className="font-bold text-slate-200">
                    {currencySymbol}{pit.sma_50?.toFixed(2)}
                  </span>
                </div>
                <div className="bg-slate-900/90 px-2 py-1.5 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">200-Day SMA</span>
                  <span className="font-bold text-slate-200">
                    {currencySymbol}{pit.sma_200?.toFixed(2)}
                  </span>
                </div>
                <div className="bg-slate-900/90 px-2 py-1.5 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">MACD Hist</span>
                  <span className={`font-bold ${pit.macd_hist >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {pit.macd_hist >= 0 ? '+' : ''}{pit.macd_hist?.toFixed(2)}
                  </span>
                </div>
                <div className="bg-slate-900/90 px-2 py-1.5 rounded border border-slate-800 col-span-2 sm:col-span-1">
                  <span className="text-[10px] text-slate-500 block">Vol Anomaly</span>
                  <span className="font-bold text-indigo-300">
                    {pit.volume_anomaly_ratio?.toFixed(2)}x
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Institutional Quantitative Performance & Risk Metrics Grid */}
          {metrics && (
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1.5 flex items-center gap-1.5">
                <Award className="w-3 h-3 text-emerald-400" />
                Institutional Risk & Performance Metrics (Forward Window):
              </span>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
                {/* Alpha vs Benchmark */}
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-slate-500 text-[10px] block">
                    Alpha vs {metrics.benchmark_name?.split(' ')[0]}
                  </span>
                  <span
                    className={`font-bold text-sm flex items-center gap-0.5 ${
                      metrics.alpha_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'
                    }`}
                  >
                    {metrics.alpha_pct >= 0 ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                    {metrics.alpha_pct >= 0 ? '+' : ''}
                    {metrics.alpha_pct}%
                  </span>
                  <span className="text-[10px] text-slate-500 block">
                    Bench: {metrics.benchmark_return_pct >= 0 ? '+' : ''}{metrics.benchmark_return_pct}%
                  </span>
                </div>

                {/* Sharpe Ratio */}
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-slate-500 text-[10px] block">Sharpe Ratio (Rf-Adj)</span>
                  <span
                    className={`font-bold text-sm ${
                      metrics.sharpe_ratio >= 1.0
                        ? 'text-emerald-400'
                        : metrics.sharpe_ratio >= 0
                        ? 'text-indigo-300'
                        : 'text-rose-400'
                    }`}
                  >
                    {metrics.sharpe_ratio?.toFixed(2)}
                  </span>
                  <span className="text-[10px] text-slate-500 block">
                    Sortino: {metrics.sortino_ratio?.toFixed(2)}
                  </span>
                </div>

                {/* Max Drawdown */}
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-slate-500 text-[10px] block">Maximum Drawdown</span>
                  <span
                    className={`font-bold text-sm ${
                      metrics.max_drawdown_pct < -15 ? 'text-rose-400' : 'text-amber-300'
                    }`}
                  >
                    {metrics.max_drawdown_pct}%
                  </span>
                  <span className="text-[10px] text-slate-500 block">
                    Ann. Vol: {metrics.annualized_volatility_pct}%
                  </span>
                </div>

                {/* CAGR & Trajectory Win Rate */}
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-slate-500 text-[10px] block">CAGR (Ann. P&L)</span>
                  <span
                    className={`font-bold text-sm ${
                      metrics.cagr_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'
                    }`}
                  >
                    {metrics.cagr_pct >= 0 ? '+' : ''}{metrics.cagr_pct}%
                  </span>
                  <span className="text-[10px] text-slate-500 block">
                    Trajectory Win: {metrics.win_rate_trajectory_pct}%
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Daily Equity / Return Trajectory Curve */}
          {trajectory.length > 0 && (
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase font-bold text-slate-400 flex items-center gap-1.5">
                  <BarChart2 className="w-3 h-3 text-indigo-400" />
                  Forward Walk-Forward Equity Trajectory ({trajectory.length} Trading Days)
                </span>
                <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 rounded p-0.5 text-[10px] font-mono">
                  <button
                    type="button"
                    onClick={() => setChartMode('return')}
                    className={`px-2 py-0.5 rounded ${
                      chartMode === 'return'
                        ? 'bg-indigo-600 text-white font-bold'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Return %
                  </button>
                  <button
                    type="button"
                    onClick={() => setChartMode('price')}
                    className={`px-2 py-0.5 rounded ${
                      chartMode === 'price'
                        ? 'bg-indigo-600 text-white font-bold'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Price ({currencySymbol})
                  </button>
                </div>
              </div>

              <div className="h-44 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={trajectory} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="backtestGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop
                          offset="5%"
                          stopColor={isProfitable ? '#10b981' : '#f43f5e'}
                          stopOpacity={0.4}
                        />
                        <stop
                          offset="95%"
                          stopColor={isProfitable ? '#10b981' : '#f43f5e'}
                          stopOpacity={0.0}
                        />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis
                      dataKey="date"
                      tick={{ fill: '#64748b', fontSize: 10 }}
                      tickFormatter={(val) => val ? val.slice(5) : ''}
                      stroke="#334155"
                    />
                    <YAxis
                      tick={{ fill: '#64748b', fontSize: 10 }}
                      domain={['auto', 'auto']}
                      stroke="#334155"
                      tickFormatter={(val) =>
                        chartMode === 'return' ? `${val}%` : `${currencySymbol}${val}`
                      }
                    />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload;
                          return (
                            <div className="bg-slate-900 border border-slate-700 p-2 rounded shadow-lg text-xs font-mono">
                              <span className="text-slate-400 block">{data.date}</span>
                              <div className="text-white font-bold">
                                Price: {currencySymbol}{data.price?.toFixed(2)}
                              </div>
                              <div
                                className={
                                  data.return_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'
                                }
                              >
                                Return: {data.return_pct >= 0 ? '+' : ''}{data.return_pct}%
                              </div>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    {chartMode === 'return' && (
                      <ReferenceLine y={0} stroke="#475569" strokeDasharray="3 3" />
                    )}
                    <Area
                      type="monotone"
                      dataKey={chartMode === 'return' ? 'return_pct' : 'price'}
                      stroke={isProfitable ? '#10b981' : '#f43f5e'}
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#backtestGradient)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Reasoning Snapshot */}
          <div className="text-xs text-slate-300 space-y-1">
            <span className="text-[10px] uppercase font-bold text-slate-400 block">
              Multi-Agent Historical Reasoning Snapshot:
            </span>
            <p className="p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono leading-relaxed text-slate-200">
              "{result.reasoning_snapshot}"
            </p>
          </div>

          {/* Validation & Price Range Footprint */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs font-mono pt-1">
            <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
              <span className="text-slate-500 text-[10px] block">Entry Price ({result.historical_date})</span>
              <span className="font-bold text-white">
                {currencySymbol}{result.entry_price?.toFixed(2)}
              </span>
            </div>
            <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
              <span className="text-slate-500 text-[10px] block">Exit Price ({result.exit_date})</span>
              <span className="font-bold text-white">
                {currencySymbol}{result.exit_price?.toFixed(2)}
              </span>
            </div>
            <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 col-span-2 sm:col-span-1">
              <span className="text-slate-500 text-[10px] block">Consensus Precision</span>
              <span
                className={`font-bold flex items-center gap-1 ${
                  (result.actual_return_pct > 0 && ['STRONG_BUY', 'BUY'].includes(result.agent_recommendation_then)) ||
                  (result.actual_return_pct < 0 && ['SELL', 'TRIM'].includes(result.agent_recommendation_then))
                    ? 'text-emerald-400'
                    : 'text-amber-400'
                }`}
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                {metrics?.alpha_pct > 0 ? 'Positive Alpha Capture' : 'Market Neutral Tracking'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
