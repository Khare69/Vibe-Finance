import React from 'react';
import { ShieldCheck, Bug, WifiOff, Clock, RefreshCw } from 'lucide-react';

export default function ResiliencyControls({
  staleMode,
  ragTimeoutMode,
  onToggleStale,
  onToggleRagTimeout,
  onReset,
}) {
  return (
    <div className="bg-[#0f172a] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Bug className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide uppercase">
              Fault Injection & System Resiliency Toggles
            </h3>
            <p className="text-xs text-slate-400">
              Test how the Multi-Agent consensus and fallback mechanisms handle infrastructure failures
            </p>
          </div>
        </div>

        {(staleMode || ragTimeoutMode) && (
          <button
            onClick={onReset}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
          >
            <RefreshCw className="w-3 h-3 text-indigo-400" />
            <span>Reset All Faults</span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
        {/* Toggle 1: Stale Live Data */}
        <div
          className={`p-4 rounded-xl border transition-all ${
            staleMode
              ? 'bg-amber-950/20 border-amber-500/40 shadow-sm'
              : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <WifiOff
                className={`w-4 h-4 ${staleMode ? 'text-amber-400' : 'text-slate-500'}`}
              />
              <span className="text-xs font-bold text-slate-200">
                Simulate Stale Live Data
              </span>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={staleMode}
                onChange={(e) => onToggleStale(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-9 h-5 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-amber-500"></div>
            </label>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Simulates market feed socket drop. System automatically switches to cached EOD snapshot and penalizes confidence by -18 points.
          </p>
        </div>

        {/* Toggle 2: RAG Timeout */}
        <div
          className={`p-4 rounded-xl border transition-all ${
            ragTimeoutMode
              ? 'bg-rose-950/20 border-rose-500/40 shadow-sm'
              : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Clock
                className={`w-4 h-4 ${ragTimeoutMode ? 'text-rose-400' : 'text-slate-500'}`}
              />
              <span className="text-xs font-bold text-slate-200">
                Simulate RAG Vector Timeout
              </span>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={ragTimeoutMode}
                onChange={(e) => onToggleRagTimeout(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-9 h-5 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-rose-500"></div>
            </label>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Simulates regulatory filing corpus timeout (&gt;3000ms). Consensus degrades gracefully to Technicals + Behavioral rules only.
          </p>
        </div>
      </div>
    </div>
  );
}
