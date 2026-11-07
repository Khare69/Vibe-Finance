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
  ArrowDownRight,
  RefreshCw,
  Repeat,
  Percent
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  Legend
} from 'recharts';
import { runBacktest } from '../services/api';

export default function BacktestSimulator({ ticker, activeTicker }) {
  const effectiveTicker = ticker || activeTicker || 'NVDA';
  const [simulationMode, setSimulationMode] = useState('single_window'); // 'single_window' | 'rolling_walk_forward'
  const [selectedDate, setSelectedDate] = useState('2024-10-15');
  const [holdingDays, setHoldingDays] = useState(90);
  const [numWindows, setNumWindows] = useState(4);
  const [windowDays, setWindowDays] = useState(45);
  const [slippageBps, setSlippageBps] = useState(10);
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [chartMode, setChartMode] = useState('return'); // 'return' | 'price'

  // Dynamic currency symbol determination
  const isUS = ['NVDA', 'AAPL', 'TSLA', 'MSFT', 'AMZN', 'GOOGL'].includes(
    effectiveTicker?.toUpperCase()
  );
  const currencySymbol = isUS ? '$' : '₹';

  const handleRunBacktest = async (e, overrideMode) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    const activeMode = overrideMode || simulationMode;

    try {
      const data = await runBacktest({
        ticker: effectiveTicker,
        historicalDate: selectedDate,
        holdingDays: Number(holdingDays),
        simulationMode: activeMode,
        numWindows: Number(numWindows),
        windowDays: Number(windowDays),
        slippageBps: Number(slippageBps),
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
  }, [effectiveTicker]);

  const isRolling = result?.simulation_mode === 'rolling_walk_forward';
  const isProfitable = isRolling
    ? (result?.cumulative_metrics?.strategy_return_pct ?? 0) >= 0
    : (result?.actual_return_pct ?? 0) >= 0;

  const metrics = isRolling ? result?.cumulative_metrics : result?.performance_metrics;
  const pit = result?.point_in_time_metrics;
  const trajectory = result?.trajectory || [];
  const equityCurve = result?.equity_curve || [];
  const windows = result?.windows || [];

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
      case 'ABSTAIN':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/40';
      default:
        return 'bg-slate-700/40 text-slate-300 border-slate-600/40';
    }
  };

  return (
    <div className="bg-[#0f172a] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-5">
      {/* Header with Mode Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <History className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white tracking-wide uppercase">
                Institutional Walk-Forward Backtesting v2
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-semibold">
                Zero Look-Ahead Bias
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Audit agent multi-factor consensus on point-in-time snapshot dates against actual market outcomes
            </p>
          </div>
        </div>

        {/* Mode Selector Toggle */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-900 border border-slate-800 rounded-xl self-start sm:self-auto">
          <button
            type="button"
            onClick={() => {
              setSimulationMode('single_window');
              handleRunBacktest(null, 'single_window');
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
              simulationMode === 'single_window'
                ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Clock className="w-3.5 h-3.5" />
            <span>Single Snapshot</span>
          </button>
          <button
            type="button"
            onClick={() => {
              setSimulationMode('rolling_walk_forward');
              handleRunBacktest(null, 'rolling_walk_forward');
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
              simulationMode === 'rolling_walk_forward'
                ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Repeat className="w-3.5 h-3.5" />
            <span>Rolling Walk-Forward v2</span>
          </button>
        </div>
      </div>

      {/* Simulator Query Controls */}
      <form onSubmit={handleRunBacktest} className="grid grid-cols-1 sm:grid-cols-4 gap-3">
        {simulationMode === 'single_window' ? (
          <>
            <div>
              <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">
                Historical Snapshot Date
              </label>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 text-xs rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500 font-mono"
              />
            </div>

            <div>
              <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">
                Forward Duration
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
          </>
        ) : (
          <>
            <div>
              <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">
                Rolling Windows Count
              </label>
              <select
                value={numWindows}
                onChange={(e) => setNumWindows(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-800 text-xs rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500 font-mono"
              >
                <option value={2}>2 Sequential Windows</option>
                <option value={3}>3 Sequential Windows</option>
                <option value={4}>4 Sequential Windows</option>
                <option value={6}>6 Sequential Windows</option>
              </select>
            </div>

            <div>
              <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">
                Window Span
              </label>
              <select
                value={windowDays}
                onChange={(e) => setWindowDays(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-800 text-xs rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500 font-mono"
              >
                <option value={30}>30-Day Horizons</option>
                <option value={45}>45-Day Horizons</option>
                <option value={60}>60-Day Horizons</option>
                <option value={90}>90-Day Horizons</option>
              </select>
            </div>
          </>
        )}

        <div>
          <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">
            Slippage & Fee Drag
          </label>
          <select
            value={slippageBps}
            onChange={(e) => setSlippageBps(Number(e.target.value))}
            className="w-full bg-slate-900 border border-slate-800 text-xs rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500 font-mono"
          >
            <option value={5}>5 bps (0.05% institutional)</option>
            <option value={10}>10 bps (0.10% standard)</option>
            <option value={20}>20 bps (0.20% retail + spread)</option>
          </select>
        </div>

        <div className="flex items-end">
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white rounded-lg text-xs font-bold transition-all shadow-md shadow-indigo-600/30 flex items-center justify-center gap-1.5"
          >
            {isLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3 h-3 fill-current" />}
            <span>{isLoading ? 'Replaying State...' : isRolling ? 'Run Rolling Backtest v2' : 'Replay Point-in-Time'}</span>
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
                {isRolling
                  ? `Rolling Multi-Window Synthesis (${result.cumulative_metrics?.total_windows} Windows)`
                  : `Multi-Agent Consensus on ${result.historical_date}`}
              </span>
              <div className="flex items-center gap-2 mt-1">
                {isRolling ? (
                  <span className="px-2.5 py-0.5 rounded text-xs font-bold border font-mono bg-indigo-500/20 text-indigo-300 border-indigo-500/40">
                    HIT RATE: {result.cumulative_metrics?.recommendation_hit_rate_pct}% ({result.cumulative_metrics?.hit_count}/{result.cumulative_metrics?.total_windows} Hits)
                  </span>
                ) : (
                  <>
                    <span
                      className={`px-2.5 py-0.5 rounded text-xs font-bold border font-mono ${getRecommendationBadge(
                        result.agent_recommendation_then
                      )}`}
                    >
                      {result.agent_recommendation_then}
                    </span>
                    <span className="text-xs text-slate-300">
                      Quant: <b className="text-white font-mono">{result.quant_score_then}</b>/100 · RAG:{' '}
                      <b className="text-white font-mono">{result.rag_score_then}</b>/100
                    </span>
                  </>
                )}
              </div>
            </div>

            {/* Realized Forward Return */}
            <div className="text-left sm:text-right">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">
                {isRolling ? 'Cumulative Strategy Net Return' : `Actual Forward Return (${result.holding_days}d)`}
              </span>
              <div
                className={`text-xl font-mono font-black flex items-center sm:justify-end gap-1 ${
                  isProfitable ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {isProfitable ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
                {isProfitable ? '+' : ''}
                {isRolling ? result.cumulative_metrics?.strategy_return_pct : result.actual_return_pct}%
              </div>
            </div>
          </div>

          {/* Institutional Performance & Risk Metrics Grid */}
          {metrics && (
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1.5 flex items-center gap-1.5">
                <Award className="w-3 h-3 text-emerald-400" />
                Institutional Risk & Performance Metrics ({isRolling ? 'Rolling Multi-Window Aggregate' : 'Single Forward Window'}):
              </span>
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-2 text-xs font-mono">
                {/* Alpha vs Benchmark */}
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-slate-500 text-[10px] block">
                    Alpha vs {metrics.benchmark_name?.split(' ')[0]}
                  </span>
                  <span
                    className={`font-bold text-sm flex items-center gap-0.5 ${
                      (metrics.cumulative_alpha_pct ?? metrics.alpha_pct) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                    }`}
                  >
                    {(metrics.cumulative_alpha_pct ?? metrics.alpha_pct) >= 0 ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                    {(metrics.cumulative_alpha_pct ?? metrics.alpha_pct) >= 0 ? '+' : ''}
                    {metrics.cumulative_alpha_pct ?? metrics.alpha_pct}%
                  </span>
                  <span className="text-[10px] text-slate-500 block">
                    Bench: {metrics.benchmark_return_pct >= 0 ? '+' : ''}{metrics.benchmark_return_pct}%
                  </span>
                </div>

                {/* Sharpe Ratio */}
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-slate-500 text-[10px] block">Sharpe Ratio</span>
                  <span
                    className={`font-bold text-sm ${
                      metrics.sharpe_ratio >= 1.0 ? 'text-emerald-400' : metrics.sharpe_ratio >= 0 ? 'text-indigo-300' : 'text-rose-400'
                    }`}
                  >
                    {metrics.sharpe_ratio?.toFixed(2)}
                  </span>
                  <span className="text-[10px] text-slate-500 block">
                    Sortino: {metrics.sortino_ratio?.toFixed(2)}
                  </span>
                </div>

                {/* Calmar Ratio */}
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-slate-500 text-[10px] block">Calmar Ratio</span>
                  <span className="font-bold text-sm text-indigo-300">
                    {metrics.calmar_ratio ? metrics.calmar_ratio.toFixed(2) : 'N/A'}
                  </span>
                  <span className="text-[10px] text-slate-500 block">
                    CAGR / |MDD|
                  </span>
                </div>

                {/* Profit Factor */}
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-slate-500 text-[10px] block">Profit Factor</span>
                  <span className={`font-bold text-sm ${metrics.profit_factor >= 1.5 ? 'text-emerald-400' : 'text-slate-200'}`}>
                    {metrics.profit_factor ? metrics.profit_factor.toFixed(2) : '1.00'}x
                  </span>
                  <span className="text-[10px] text-slate-500 block">
                    Gains / Losses
                  </span>
                </div>

                {/* Max Drawdown */}
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-slate-500 text-[10px] block">Max Drawdown</span>
                  <span
                    className={`font-bold text-sm ${
                      metrics.max_drawdown_pct < -15 ? 'text-rose-400' : 'text-amber-300'
                    }`}
                  >
                    {metrics.max_drawdown_pct}%
                  </span>
                  <span className="text-[10px] text-slate-500 block">
                    Peak-to-trough
                  </span>
                </div>

                {/* Slippage & Info Ratio */}
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-slate-500 text-[10px] block">Info Ratio</span>
                  <span className="font-bold text-sm text-slate-200">
                    {metrics.information_ratio ? metrics.information_ratio.toFixed(2) : '0.00'}
                  </span>
                  <span className="text-[10px] text-slate-500 block">
                    Drag: -{metrics.total_slippage_drag_pct ?? (metrics.slippage_bps ? (metrics.slippage_bps/100).toFixed(2) : '0.10')}%
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Rolling Walk-Forward Sequence Table (when in rolling mode) */}
          {isRolling && windows.length > 0 && (
            <div className="space-y-2">
              <span className="text-[10px] uppercase font-bold text-slate-400 block flex items-center gap-1.5">
                <Repeat className="w-3 h-3 text-indigo-400" />
                Rolling Sequential Windows Breakdown:
              </span>
              <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-slate-900/80 text-[10px] uppercase text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="p-2.5">Window</th>
                      <th className="p-2.5">Period (Entry &rarr; Exit)</th>
                      <th className="p-2.5">Point-in-Time Verdict</th>
                      <th className="p-2.5">Divergence (&Delta;)</th>
                      <th className="p-2.5">Asset Gross</th>
                      <th className="p-2.5">Strategy Net</th>
                      <th className="p-2.5">Benchmark</th>
                      <th className="p-2.5">Directional Hit</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {windows.map((w, idx) => (
                      <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                        <td className="p-2.5 font-bold text-white">#{w.window_index}</td>
                        <td className="p-2.5 text-slate-400">
                          {w.entry_date} &rarr; {w.exit_date} ({w.holding_days}d)
                        </td>
                        <td className="p-2.5">
                          <span className={`px-2 py-0.5 rounded text-[11px] font-bold border ${getRecommendationBadge(w.recommendation)}`}>
                            {w.recommendation}
                          </span>
                        </td>
                        <td className="p-2.5 font-bold text-amber-300">&Delta; {w.divergence}</td>
                        <td className={`p-2.5 font-bold ${w.asset_return_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {w.asset_return_pct >= 0 ? '+' : ''}{w.asset_return_pct}%
                        </td>
                        <td className={`p-2.5 font-bold ${w.strategy_return_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {w.strategy_return_pct >= 0 ? '+' : ''}{w.strategy_return_pct}%
                        </td>
                        <td className="p-2.5 text-slate-400">
                          {w.benchmark_return_pct >= 0 ? '+' : ''}{w.benchmark_return_pct}%
                        </td>
                        <td className="p-2.5">
                          {w.is_hit ? (
                            <span className="flex items-center gap-1 text-emerald-400 font-bold text-[11px]">
                              <CheckCircle2 className="w-3.5 h-3.5" /> Hit
                            </span>
                          ) : (
                            <span className="flex items-center gap-1 text-rose-400 font-bold text-[11px]">
                              <XCircle className="w-3.5 h-3.5" /> Miss
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Equity Curves (Rolling multi-window compounding vs Buy & Hold) */}
          {isRolling && equityCurve.length > 0 && (
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
              <span className="text-[10px] uppercase font-bold text-slate-400 flex items-center gap-1.5">
                <BarChart2 className="w-3 h-3 text-indigo-400" />
                Cumulative Strategy Compounding vs Buy-and-Hold & Benchmark (Base 100)
              </span>
              <div className="h-44 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={equityCurve} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 10 }} stroke="#334155" />
                    <YAxis tick={{ fill: '#64748b', fontSize: 10 }} domain={['auto', 'auto']} stroke="#334155" />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload;
                          return (
                            <div className="bg-slate-900 border border-slate-700 p-2 rounded shadow-lg text-xs font-mono space-y-0.5">
                              <span className="text-slate-400 block">{data.date} (Window #{data.window})</span>
                              <div className="text-indigo-400 font-bold">Strategy: {data.strategy_equity}</div>
                              <div className="text-emerald-400">Asset: {data.asset_equity}</div>
                              <div className="text-slate-400">Benchmark: {data.benchmark_equity}</div>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
                    <Line type="monotone" dataKey="strategy_equity" name="Vibe Strategy" stroke="#6366f1" strokeWidth={2.5} dot={{ r: 3 }} />
                    <Line type="monotone" dataKey="asset_equity" name="Buy & Hold" stroke="#10b981" strokeWidth={1.5} dot={{ r: 2 }} />
                    <Line type="monotone" dataKey="benchmark_equity" name="Benchmark Index" stroke="#64748b" strokeWidth={1.5} strokeDasharray="3 3" dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Single Window Daily Return Area Chart */}
          {!isRolling && trajectory.length > 0 && (
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase font-bold text-slate-400 flex items-center gap-1.5">
                  <BarChart2 className="w-3 h-3 text-indigo-400" />
                  Point-in-Time Trajectory ({trajectory.length} Trading Days)
                </span>
                <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 rounded p-0.5 text-[10px] font-mono">
                  <button
                    type="button"
                    onClick={() => setChartMode('return')}
                    className={`px-2 py-0.5 rounded ${
                      chartMode === 'return' ? 'bg-indigo-600 text-white font-bold' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Return %
                  </button>
                  <button
                    type="button"
                    onClick={() => setChartMode('price')}
                    className={`px-2 py-0.5 rounded ${
                      chartMode === 'price' ? 'bg-indigo-600 text-white font-bold' : 'text-slate-400 hover:text-white'
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
                        <stop offset="5%" stopColor={isProfitable ? '#10b981' : '#f43f5e'} stopOpacity={0.4} />
                        <stop offset="95%" stopColor={isProfitable ? '#10b981' : '#f43f5e'} stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 10 }} tickFormatter={(val) => val ? val.slice(5) : ''} stroke="#334155" />
                    <YAxis tick={{ fill: '#64748b', fontSize: 10 }} domain={['auto', 'auto']} stroke="#334155" tickFormatter={(val) => chartMode === 'return' ? `${val}%` : `${currencySymbol}${val}`} />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload;
                          return (
                            <div className="bg-slate-900 border border-slate-700 p-2 rounded shadow-lg text-xs font-mono">
                              <span className="text-slate-400 block">{data.date}</span>
                              <div className="text-white font-bold">Price: {currencySymbol}{data.price?.toFixed(2)}</div>
                              <div className={data.return_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                                Return: {data.return_pct >= 0 ? '+' : ''}{data.return_pct}%
                              </div>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    {chartMode === 'return' && <ReferenceLine y={0} stroke="#475569" strokeDasharray="3 3" />}
                    <Area type="monotone" dataKey={chartMode === 'return' ? 'return_pct' : 'price'} stroke={isProfitable ? '#10b981' : '#f43f5e'} strokeWidth={2} fillOpacity={1} fill="url(#backtestGradient)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Reasoning / Summary Snapshot */}
          <div className="text-xs text-slate-300 space-y-1">
            <span className="text-[10px] uppercase font-bold text-slate-400 block">
              {isRolling ? 'Institutional Walk-Forward Summary Verdict:' : 'Multi-Agent Historical Reasoning Snapshot:'}
            </span>
            <p className="p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono leading-relaxed text-slate-200">
              "{isRolling ? result.summary_verdict : result.reasoning_snapshot}"
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
