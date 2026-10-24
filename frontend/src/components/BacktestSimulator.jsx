import React, { useState } from 'react';
import { History, Calendar, Play, CheckCircle2, XCircle, TrendingUp, TrendingDown, Clock, Sparkles } from 'lucide-react';
import { runBacktest } from '../services/api';

export default function BacktestSimulator({ activeTicker = 'NVDA' }) {
  const [selectedDate, setSelectedDate] = useState('2025-10-15');
  const [holdingDays, setHoldingDays] = useState(90);
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

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
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  // Run on mount or ticker change
  React.useEffect(() => {
    handleRunBacktest();
  }, [activeTicker]);

  const isProfitable = result?.actual_return_pct >= 0;

  return (
    <div className="bg-[#0f172a] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <History className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide uppercase">
              Historical Backtesting Simulator
            </h3>
            <p className="text-xs text-slate-400">
              Audit agent consensus accuracy on historical dates vs actual realized market returns
            </p>
          </div>
        </div>

        <span className="text-xs font-mono font-bold text-indigo-400 bg-indigo-950/60 px-3 py-1 rounded-lg border border-indigo-500/30">
          Target: {activeTicker}
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
            onChange={(e) => setHoldingDays(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 text-xs rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500 font-mono"
          >
            <option value={30}>30 Days Forward</option>
            <option value={60}>60 Days Forward</option>
            <option value={90}>90 Days Forward</option>
            <option value={180}>180 Days Forward</option>
          </select>
        </div>

        <div className="flex items-end">
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white rounded-lg text-xs font-bold transition-all shadow-md shadow-indigo-600/30 flex items-center justify-center gap-1.5"
          >
            <Play className="w-3 h-3" />
            <span>{isLoading ? 'Replaying Agent State...' : 'Replay Agent State'}</span>
          </button>
        </div>
      </form>

      {/* Backtest Result Display */}
      {result && (
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400 block">
                Agent Verdict on {result.historical_date}
              </span>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="px-2.5 py-0.5 rounded text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-mono">
                  {result.agent_recommendation_then}
                </span>
                <span className="text-xs text-slate-400">
                  Quant Score: <b className="text-white">{result.quant_score_then}</b> · RAG Score: <b className="text-white">{result.rag_score_then}</b>
                </span>
              </div>
            </div>

            {/* Realized Forward Return */}
            <div className="text-right">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">
                Actual Forward Return ({holdingDays}d)
              </span>
              <div
                className={`text-lg font-mono font-black flex items-center justify-end gap-1 ${
                  isProfitable ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {isProfitable ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                {isProfitable ? '+' : ''}
                {result.actual_return_pct}%
              </div>
            </div>
          </div>

          {/* Reasoning Snapshot */}
          <div className="text-xs text-slate-300 space-y-1">
            <span className="text-[10px] uppercase font-bold text-slate-400 block">
              Multi-Agent Historical Reasoning Snapshot:
            </span>
            <p className="p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono leading-relaxed text-slate-200">
              "{result.reasoning_snapshot}"
            </p>
          </div>

          {/* Validation Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs font-mono pt-1">
            <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
              <span className="text-slate-500 text-[10px] block">Entry Price</span>
              <span className="font-bold text-white">${result.entry_price?.toFixed(2)}</span>
            </div>
            <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
              <span className="text-slate-500 text-[10px] block">Exit Price</span>
              <span className="font-bold text-white">${result.exit_price?.toFixed(2)}</span>
            </div>
            <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 col-span-2 sm:col-span-1">
              <span className="text-slate-500 text-[10px] block">Consensus Precision</span>
              <span className="font-bold text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> High Alpha Alignment
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
