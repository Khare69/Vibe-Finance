import React from 'react';
import { AlertTriangle, TrendingUp, TrendingDown, Clock, BarChart3, Database } from 'lucide-react';

export default function PriceBanner({ analysis, isStale, isRagTimeout }) {
  if (!analysis) return null;

  const { company_name, ticker, price_data, timestamp, synthesis } = analysis;
  const isPositive = (price_data?.change_percent || 0) >= 0;
  const feedStatus = price_data?.feed_status || (isStale ? 'STALE_FALLBACK_EOD' : 'LIVE');
  const symbol = price_data?.symbol || (['NVDA', 'AAPL', 'TSLA'].includes(ticker?.toUpperCase()) ? '$' : '₹');
  const macroRegime = synthesis?.macro_regime;

  // Generate synthetic 10-point sparkline for momentum visualization
  const sparkPoints = isPositive
    ? [20, 24, 22, 28, 26, 32, 30, 36, 34, 40]
    : [40, 36, 38, 30, 32, 26, 28, 22, 24, 18];
  const maxP = Math.max(...sparkPoints);
  const minP = Math.min(...sparkPoints);
  const sparkSvgPath = sparkPoints
    .map((val, i) => {
      const x = (i / (sparkPoints.length - 1)) * 90;
      const y = 35 - ((val - minP) / (maxP - minP || 1)) * 25;
      return `${i === 0 ? 'M' : 'L'}${x},${y}`;
    })
    .join(' ');

  return (
    <div className="space-y-3">
      {/* Degraded Alert Banner if active */}
      {(feedStatus === 'STALE_FALLBACK_EOD' || isStale) && (
        <div className="bg-amber-500/10 border border-amber-500/40 rounded-xl p-3 flex items-start gap-3 text-amber-300 animate-in fade-in duration-300">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="text-xs">
            <span className="font-bold uppercase tracking-wider block">
              Market Feed Degraded: Fallback EOD Active
            </span>
            <span>
              Real-time websocket feed disconnected or delayed. Using previous close EOD metrics. An automatic -{price_data?.confidence_penalty ? Math.round(price_data.confidence_penalty) : 25} point confidence penalty has been applied to consensus scoring.
            </span>
          </div>
        </div>
      )}

      {isRagTimeout && (
        <div className="bg-rose-500/10 border border-rose-500/40 rounded-xl p-3 flex items-start gap-3 text-rose-300 animate-in fade-in duration-300">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div className="text-xs">
            <span className="font-bold uppercase tracking-wider block">
              RAG Corpus Vector Timeout
            </span>
            <span>
              Fundamental SEC/SEBI retrieval timed out. Pure Quantitative Momentum & Behavioral risk fallbacks are maintaining system operational continuity.
            </span>
          </div>
        </div>
      )}

      {/* Main Price & Volume Card */}
      <div className="bg-[#0f172a]/90 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl font-black text-white tracking-tight">
              {company_name}
            </h1>
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              {ticker}
            </span>
            <span
              className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                feedStatus === 'LIVE'
                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                  : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
              }`}
            >
              {feedStatus}
            </span>
          </div>
          <div className="flex items-center gap-4 text-xs text-slate-400">
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-slate-500" />
              As of: {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
            <span>52W H: {symbol}{price_data?.high_52w || 'N/A'}</span>
            <span>52W L: {symbol}{price_data?.low_52w || 'N/A'}</span>
            {macroRegime && (
              <span className="hidden lg:inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-indigo-300">
                Regime: {macroRegime.regime_title}
              </span>
            )}
          </div>
        </div>

        {/* Price & Sparkline & Volume Stats */}
        <div className="flex items-center gap-6">
          {/* Mini Sparkline Chart */}
          <div className="hidden sm:flex flex-col items-end">
            <span className="text-[10px] text-slate-500 uppercase tracking-wider mb-0.5">20D Trend</span>
            <svg width="90" height="35" className="overflow-visible">
              <path
                d={sparkSvgPath}
                fill="none"
                stroke={isPositive ? '#10b981' : '#f43f5e'}
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>

          {/* Price & Change */}
          <div className="text-right">
            <div className="text-2xl font-mono font-extrabold text-white">
              {symbol}
              {price_data?.current_price?.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </div>
            <div
              className={`text-xs font-mono font-bold flex items-center justify-end gap-1 ${
                isPositive ? 'text-emerald-400' : 'text-rose-400'
              }`}
            >
              {isPositive ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
              {isPositive ? '+' : ''}
              {price_data?.change_percent}%
            </div>
          </div>

          {/* Volume Anomaly */}
          <div className="pl-6 border-l border-slate-800 text-left">
            <div className="text-[10px] uppercase font-semibold text-slate-400 flex items-center gap-1">
              <BarChart3 className="w-3 h-3 text-indigo-400" /> Volume Surge
            </div>
            <div className="text-sm font-mono font-bold text-slate-200 mt-0.5">
              {price_data?.volume_anomaly_ratio}x avg
            </div>
            <div className="text-[10px] text-slate-500">
              {price_data?.volume_anomaly_ratio > 1.4 ? 'Spike detected' : 'Standard flow'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
