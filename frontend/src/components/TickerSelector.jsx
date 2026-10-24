import React, { useState } from 'react';
import { TrendingUp, TrendingDown, Search } from 'lucide-react';

export default function TickerSelector({
  stocks = [],
  selectedTicker,
  onSelectTicker,
  isLoading,
}) {
  const [search, setSearch] = useState('');

  const filtered = stocks.filter(
    (s) =>
      s.ticker.toLowerCase().includes(search.toLowerCase()) ||
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.sector.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="bg-[#0f172a]/80 border border-slate-800 rounded-2xl p-4 shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
        <div>
          <h3 className="text-sm font-bold text-white tracking-wide uppercase flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span>
            Tracked Assets Watchlist
          </h3>
          <p className="text-xs text-slate-400">
            Select a stock to run multi-agent consensus & RAG reasoning
          </p>
        </div>

        {/* Quick Search */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            placeholder="Search symbol, sector..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full sm:w-52 pl-8 pr-3 py-1.5 text-xs bg-slate-900/80 border border-slate-750 border-slate-800 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
          />
        </div>
      </div>

      {/* Ticker Cards / Pills Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
        {filtered.map((stock) => {
          const isSelected = selectedTicker === stock.ticker;
          const isPositive = stock.change >= 0;

          return (
            <button
              key={stock.ticker}
              type="button"
              disabled={isLoading}
              onClick={() => onSelectTicker(stock.ticker)}
              className={`p-3 rounded-xl border text-left transition-all relative overflow-hidden group ${
                isSelected
                  ? 'bg-gradient-to-br from-indigo-950/60 to-slate-900 border-indigo-500/80 ring-2 ring-indigo-500/30 shadow-lg shadow-indigo-950/40'
                  : 'bg-slate-900/50 border-slate-800/80 hover:border-slate-700 hover:bg-slate-800/40'
              }`}
            >
              {isSelected && (
                <div className="absolute top-0 right-0 w-8 h-8 bg-indigo-500/20 blur-md rounded-full pointer-events-none" />
              )}

              <div className="flex items-center justify-between mb-1">
                <span className="font-mono font-bold text-sm text-white group-hover:text-indigo-400 transition-colors">
                  {stock.ticker}
                </span>
                <span className="text-[10px] uppercase font-semibold text-slate-500 px-1 py-0.2 bg-slate-800/60 rounded">
                  {stock.exchange}
                </span>
              </div>

              <div className="text-[11px] text-slate-400 truncate mb-2" title={stock.name}>
                {stock.name}
              </div>

              <div className="flex items-baseline justify-between pt-1 border-t border-slate-800/60">
                <span className="font-mono text-xs font-semibold text-slate-200">
                  {stock.symbol}
                  {stock.price.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </span>
                <span
                  className={`text-[11px] font-semibold flex items-center font-mono ${
                    isPositive ? 'text-emerald-400' : 'text-rose-400'
                  }`}
                >
                  {isPositive ? (
                    <TrendingUp className="w-3 h-3 mr-0.5 inline" />
                  ) : (
                    <TrendingDown className="w-3 h-3 mr-0.5 inline" />
                  )}
                  {isPositive ? '+' : ''}
                  {stock.change}%
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
