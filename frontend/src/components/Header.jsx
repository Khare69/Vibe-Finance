import React from 'react';
import { Activity, Shield, Sparkles, Terminal, Wifi, AlertTriangle, FileDown } from 'lucide-react';

export default function Header({
  systemHealth,
  userProfile,
  onOpenVibeCheck,
  onOpenDevDrawer,
  onOpenExportMemo,
  staleMode,
  ragTimeoutMode,
}) {
  const isDegraded = staleMode || ragTimeoutMode || systemHealth?.degraded_mode;

  const riskBadgeColors = {
    conservative: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    moderate: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
    aggressive: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
  };

  const riskLevel = userProfile?.risk_level || 'conservative';

  return (
    <header className="sticky top-0 z-40 border-b border-slate-800/80 bg-[#080c14]/90 backdrop-blur-md px-4 lg:px-8 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand / Logo */}
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 shadow-lg shadow-indigo-500/25">
            <Sparkles className="w-5 h-5 text-white" />
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-indigo-500"></span>
            </span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold tracking-tight text-white">
                Vibe<span className="text-indigo-400">Finance</span>
              </span>
              <span className="px-1.5 py-0.5 text-[10px] uppercase tracking-wider font-semibold bg-indigo-500/20 text-indigo-300 rounded border border-indigo-500/30">
                v1.0 Multi-Agent
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              Explainable AI Financial Reasoning Engine
            </p>
          </div>
        </div>

        {/* Status Indicators & Controls */}
        <div className="flex items-center gap-3">
          {/* Feed Status Indicator */}
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all ${
              isDegraded
                ? 'bg-amber-500/10 border-amber-500/40 text-amber-300'
                : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
            }`}
            title={
              isDegraded
                ? 'Feed Degraded: Operating in EOD Snapshot mode'
                : 'Live Market Data streaming active'
            }
          >
            {isDegraded ? (
              <>
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
                <span className="hidden md:inline">Feed:</span>
                <span className="font-semibold">Degraded EOD</span>
              </>
            ) : (
              <>
                <Wifi className="w-3.5 h-3.5 text-emerald-400" />
                <span className="hidden md:inline">Feed:</span>
                <span className="font-semibold">Live Feed</span>
              </>
            )}
          </div>

          {/* User Risk Profile Badge with quick re-calibrate trigger */}
          <button
            onClick={onOpenVibeCheck}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all hover:scale-105 ${
              riskBadgeColors[riskLevel] || riskBadgeColors.conservative
            }`}
            title="Click to recalibrate your risk profile via Vibe Check"
          >
            <Shield className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Profile:</span>
            <span className="font-bold capitalize">{riskLevel}</span>
          </button>

          {/* Vibe Check Modal Trigger Button */}
          <button
            onClick={onOpenVibeCheck}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-600 hover:to-violet-700 text-white text-xs font-semibold shadow-md shadow-indigo-500/20 transition-all hover:shadow-indigo-500/30 hover:scale-[1.02] active:scale-95"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Vibe Check</span>
          </button>

          {/* Export Investment Decision Memo */}
          <button
            onClick={onOpenExportMemo}
            className="flex items-center gap-1.5 p-2 md:px-3 md:py-1.5 rounded-lg bg-indigo-950/60 hover:bg-indigo-900/80 border border-indigo-500/30 text-indigo-300 hover:text-white text-xs font-medium transition-all"
            title="Export complete Multi-Agent Investment Decision Memorandum"
          >
            <FileDown className="w-3.5 h-3.5" />
            <span className="hidden md:inline">Export Memo</span>
          </button>

          {/* Developer / Session Audit Drawer Button */}
          <button
            onClick={onOpenDevDrawer}
            className="flex items-center gap-1.5 p-2 md:px-3 md:py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-slate-300 hover:text-white text-xs font-medium transition-all"
            title="Open System Telemetry & Agent Latency Audit Drawer"
          >
            <Terminal className="w-3.5 h-3.5 text-indigo-400" />
            <span className="hidden md:inline">Dev Audit</span>
          </button>
        </div>
      </div>
    </header>
  );
}
