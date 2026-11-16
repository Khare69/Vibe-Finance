import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Flame,
  Zap,
  Clock,
  RotateCcw,
  ChevronRight,
  Award,
  BarChart3,
  ArrowUpRight,
  Shield,
  Layers,
} from 'lucide-react';
import { getMarketLeaderboard } from '../services/api';

export default function MarketLeaderboard({ onSelectTicker, selectedTicker }) {
  const [leaderboardData, setLeaderboardData] = useState(null);
  const [activeTab, setActiveTab] = useState('GAINERS'); // 'GAINERS' | 'LOSERS' | 'VOLUME' | 'MOMENTUM'
  const [isLoading, setIsLoading] = useState(false);
  const [secondsRemaining, setSecondsRemaining] = useState(300);

  const fetchLeaderboard = async (force = false) => {
    setIsLoading(true);
    try {
      const data = await getMarketLeaderboard(force);
      setLeaderboardData(data);
      setSecondsRemaining(data.seconds_until_next_refresh || 300);
    } catch (err) {
      console.error('Failed to load leaderboard:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchLeaderboard(false);
  }, []);

  // 1-second countdown ticker
  useEffect(() => {
    const timer = setInterval(() => {
      setSecondsRemaining((prev) => {
        if (prev <= 1) {
          fetchLeaderboard(true);
          return 300;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const formatCountdown = (secs) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const rankings = leaderboardData?.rankings || {};
  let currentList = [];
  if (activeTab === 'GAINERS') currentList = rankings.top_gainers || [];
  else if (activeTab === 'LOSERS') currentList = rankings.top_losers || [];
  else if (activeTab === 'VOLUME') currentList = rankings.volume_shockers || [];
  else if (activeTab === 'MOMENTUM') currentList = rankings.momentum_leaders || [];

  const topGainer = rankings.top_gainers?.[0];
  const topVolume = rankings.volume_shockers?.[0];
  const topMomentum = rankings.momentum_leaders?.[0];

  return (
    <div className="bg-[#0f172a] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-6">
      {/* Top Header & 5-Minute Countdown */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <Award className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white tracking-wide uppercase flex items-center gap-2">
                Indian Equities Live Leaderboard
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
                  NSE Market Hours
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Ranks NIFTY equities by trading returns, volume breakout anomalies, and quant momentum
              </p>
            </div>
          </div>
        </div>

        {/* 5-Min Refresh Timer & Manual Action */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs font-mono">
            <Clock className="w-3.5 h-3.5 text-indigo-400 animate-spin" style={{ animationDuration: '6s' }} />
            <span className="text-slate-400">Next 5-Min Refresh:</span>
            <span className="font-bold text-amber-400">{formatCountdown(secondsRemaining)}</span>
          </div>

          <button
            type="button"
            disabled={isLoading}
            onClick={() => fetchLeaderboard(true)}
            className="p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-colors"
            title="Force Live Refresh"
          >
            <RotateCcw className={`w-4 h-4 ${isLoading ? 'animate-spin text-indigo-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Snapshot Highlight Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* Top Session Gainer */}
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span className="font-semibold flex items-center gap-1 text-emerald-400">
              <TrendingUp className="w-3.5 h-3.5" /> Top Session Return
            </span>
            <span className="font-mono text-[10px] text-slate-500">Rank #1</span>
          </div>
          <div className="flex items-baseline justify-between mt-1">
            <span className="font-mono font-bold text-white text-sm">
              {topGainer?.symbol || 'COCHINSHIP'}
            </span>
            <span className="font-mono text-xs font-bold text-emerald-400">
              +{topGainer?.change_percent ?? 5.4}%
            </span>
          </div>
          <span className="text-[11px] text-slate-400 truncate block mt-0.5">
            {topGainer?.company_name || 'Cochin Shipyard Limited'}
          </span>
        </div>

        {/* Volume Breakout Shocker */}
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span className="font-semibold flex items-center gap-1 text-amber-400">
              <Zap className="w-3.5 h-3.5" /> Volume Breakout Anomaly
            </span>
            <span className="font-mono text-[10px] text-slate-500">Anomaly &gt; 2.0x</span>
          </div>
          <div className="flex items-baseline justify-between mt-1">
            <span className="font-mono font-bold text-white text-sm">
              {topVolume?.symbol || 'RVNL'}
            </span>
            <span className="font-mono text-xs font-bold text-amber-400">
              {topVolume?.volume_anomaly_ratio ?? 3.2}x Baseline
            </span>
          </div>
          <span className="text-[11px] text-slate-400 truncate block mt-0.5">
            {topVolume?.company_name || 'Rail Vikas Nigam Limited'}
          </span>
        </div>

        {/* Momentum Leader */}
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span className="font-semibold flex items-center gap-1 text-indigo-400">
              <Flame className="w-3.5 h-3.5" /> Quantitative Momentum
            </span>
            <span className="font-mono text-[10px] text-slate-500">RSI + Trend Score</span>
          </div>
          <div className="flex items-baseline justify-between mt-1">
            <span className="font-mono font-bold text-white text-sm">
              {topMomentum?.symbol || 'HAL'}
            </span>
            <span className="font-mono text-xs font-bold text-indigo-400">
              {topMomentum?.momentum_score ?? 88} / 100
            </span>
          </div>
          <span className="text-[11px] text-slate-400 truncate block mt-0.5">
            {topMomentum?.company_name || 'Hindustan Aeronautics Limited'}
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 border-b border-slate-800">
        <button
          type="button"
          onClick={() => setActiveTab('GAINERS')}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all shrink-0 ${
            activeTab === 'GAINERS'
              ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <TrendingUp className="w-3.5 h-3.5" />
          <span>Top Gainers (% Return)</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('LOSERS')}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all shrink-0 ${
            activeTab === 'LOSERS'
              ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <TrendingDown className="w-3.5 h-3.5" />
          <span>Top Losers (Pullbacks)</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('VOLUME')}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all shrink-0 ${
            activeTab === 'VOLUME'
              ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <Zap className="w-3.5 h-3.5" />
          <span>Volume Shockers</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('MOMENTUM')}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all shrink-0 ${
            activeTab === 'MOMENTUM'
              ? 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/30'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <Flame className="w-3.5 h-3.5" />
          <span>Quant Momentum Leaders</span>
        </button>
      </div>

      {/* Leaderboard Rankings Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-900/90 text-slate-400 uppercase font-mono text-[10px] tracking-wider border-b border-slate-800">
            <tr>
              <th className="py-3 px-3 w-12 text-center">Rank</th>
              <th className="py-3 px-3">Company / Symbol</th>
              <th className="py-3 px-3">Sector & Tier</th>
              <th className="py-3 px-3 text-right">Last Price</th>
              <th className="py-3 px-3 text-right">Return (% Change)</th>
              <th className="py-3 px-3 text-right">
                {activeTab === 'VOLUME' ? 'Volume Ratio' : (activeTab === 'MOMENTUM' ? 'Momentum Score' : 'Beta')}
              </th>
              <th className="py-3 px-3 text-center">Inspect</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {currentList.map((item) => {
              const isSelected = selectedTicker === item.symbol;
              const isPositive = (item.change_percent ?? 0) >= 0;

              return (
                <tr
                  key={item.symbol}
                  className={`hover:bg-indigo-950/20 transition-colors ${
                    isSelected ? 'bg-indigo-950/40 border-l-2 border-indigo-500' : ''
                  }`}
                >
                  {/* Rank */}
                  <td className="py-3 px-3 text-center font-bold">
                    <span
                      className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs ${
                        item.rank === 1
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                          : item.rank === 2
                          ? 'bg-slate-300/20 text-slate-200 border border-slate-400/40'
                          : item.rank === 3
                          ? 'bg-amber-700/20 text-amber-500 border border-amber-700/40'
                          : 'text-slate-400'
                      }`}
                    >
                      {item.rank}
                    </span>
                  </td>

                  {/* Company */}
                  <td className="py-3 px-3 font-sans">
                    <div className="font-mono font-bold text-white text-xs">
                      {item.symbol}
                    </div>
                    <div className="text-[11px] text-slate-400 truncate max-w-[200px]">
                      {item.company_name}
                    </div>
                  </td>

                  {/* Sector */}
                  <td className="py-3 px-3 font-sans">
                    <div className="text-xs text-slate-300">{item.sector}</div>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 font-mono">
                      {item.cap_tier || 'NSE'}
                    </span>
                  </td>

                  {/* Price */}
                  <td className="py-3 px-3 text-right font-bold text-white">
                    ₹{Number(item.price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>

                  {/* Return */}
                  <td className="py-3 px-3 text-right font-bold">
                    <span
                      className={`inline-flex items-center gap-0.5 px-2 py-0.5 rounded text-xs ${
                        isPositive
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                      }`}
                    >
                      {isPositive ? '+' : ''}
                      {item.change_percent}%
                    </span>
                  </td>

                  {/* Special column based on tab */}
                  <td className="py-3 px-3 text-right text-slate-300">
                    {activeTab === 'VOLUME' ? (
                      <span className="font-bold text-amber-400">{item.volume_anomaly_ratio}x</span>
                    ) : activeTab === 'MOMENTUM' ? (
                      <span className="font-bold text-indigo-400">{item.momentum_score} / 100</span>
                    ) : (
                      <span>{item.beta}</span>
                    )}
                  </td>

                  {/* 1-Click Action */}
                  <td className="py-3 px-3 text-center">
                    <button
                      type="button"
                      onClick={() => onSelectTicker(item.symbol)}
                      className="px-2.5 py-1 text-[11px] font-sans font-semibold rounded-lg bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white border border-indigo-500/30 transition-all flex items-center gap-1 mx-auto"
                    >
                      <span>Analyze</span>
                      <ChevronRight className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between text-[11px] text-slate-500 gap-2 border-t border-slate-900 pt-3">
        <span>Sliding 5-minute cache • Automatically updates live price changes and trading returns</span>
        <span>Click "Analyze" to load any stock directly into the Multi-Agent Research Terminal</span>
      </div>
    </div>
  );
}
