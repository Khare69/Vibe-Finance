import React, { useState } from 'react';
import { Sliders, RefreshCw, CheckCircle, ArrowRight, ShieldCheck, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';

export default function PortfolioRebalancer({ portfolio, userProfile, onRebalanceComplete }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isApplying, setIsApplying] = useState(false);
  const [rebalanceApplied, setRebalanceApplied] = useState(false);

  const riskLevel = userProfile?.risk_level?.toLowerCase() || 'conservative';
  const holdings = portfolio?.holdings || [];
  const totalValue = portfolio?.total_value || 500000;

  // Target allocations based on risk profile
  const targetAllocations = {
    conservative: { Tech: 30.0, Energy: 30.0, Financials: 25.0, Cash: 15.0 },
    moderate: { Tech: 45.0, Energy: 25.0, Financials: 20.0, Cash: 10.0 },
    aggressive: { Tech: 60.0, Energy: 20.0, Financials: 15.0, Cash: 5.0 }
  }[riskLevel] || { Tech: 35.0, Energy: 30.0, Financials: 25.0, Cash: 10.0 };

  const currentSectorAllocations = portfolio?.sector_allocations || [];
  const techAlloc = currentSectorAllocations.find((s) => s.sector === 'Tech')?.allocation_pct || 46.8;
  const isOverweight = techAlloc > targetAllocations.Tech;
  const excessTechPct = Math.max(0, round(techAlloc - targetAllocations.Tech, 1));
  const excessTechValue = Math.round((excessTechPct / 100) * totalValue);

  function round(val, dec = 1) {
    return Math.round(val * Math.pow(10, dec)) / Math.pow(10, dec);
  }

  // Recommended rebalancing orders
  const proposedTrades = [
    {
      action: 'TRIM',
      ticker: 'TCS',
      shares: 8,
      approxValue: 31320,
      reason: `Reduce Tech concentration by ${round(excessTechPct * 0.45)}%`
    },
    {
      action: 'BUY / ACCUMULATE',
      ticker: 'HDFCBANK',
      shares: 15,
      approxValue: 25425,
      reason: 'Reinforce defensive Financials allocation'
    }
  ];

  const handleExecuteRebalance = () => {
    setIsApplying(true);
    setTimeout(() => {
      setIsApplying(false);
      setRebalanceApplied(true);
      if (onRebalanceComplete) onRebalanceComplete();
    }, 800);
  };

  return (
    <div className="bg-[#0f172a] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-violet-500/10 text-violet-400 border border-violet-500/20">
            <Sliders className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide uppercase">
              Automated Portfolio Rebalancing Wizard
            </h3>
            <p className="text-xs text-slate-400">
              Personalized rebalancing alignment based on your {riskLevel.toUpperCase()} mandate
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 self-start sm:self-auto py-1 px-2.5 rounded-lg bg-indigo-950/40 border border-indigo-500/30 transition-all"
        >
          <span>{isOpen ? 'Collapse Wizard' : 'Review Rebalance Strategy'}</span>
          {isOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Summary Banner */}
      <div className={`p-3.5 rounded-xl border flex items-center justify-between text-xs ${
        isOverweight
          ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
          : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
      }`}>
        <div className="flex items-center gap-2.5">
          {isOverweight ? (
            <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
          ) : (
            <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
          )}
          <span>
            {isOverweight
              ? `Tech sector is currently ${techAlloc}%, which exceeds your ${riskLevel} cap (${targetAllocations.Tech}%). Rebalancing proposal available.`
              : `Portfolio allocations are currently in alignment with your ${riskLevel} target bands.`}
          </span>
        </div>
        {isOverweight && (
          <span className="font-mono font-bold text-amber-400 shrink-0">
            Excess: +₹{excessTechValue.toLocaleString()}
          </span>
        )}
      </div>

      {/* Expandable Rebalance Table & Execution Controls */}
      {isOpen && (
        <div className="space-y-4 pt-2 animate-in fade-in duration-200">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            {Object.entries(targetAllocations).map(([sec, targetPct]) => {
              const cur = currentSectorAllocations.find((s) => s.sector === sec)?.allocation_pct || (sec === 'Cash' ? 13.0 : 0.0);
              const isDiff = cur > targetPct;
              return (
                <div key={sec} className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
                  <div className="flex justify-between text-slate-400 mb-1">
                    <span>{sec}</span>
                    <span className="font-mono text-[11px]">Target: {targetPct}%</span>
                  </div>
                  <div className="flex items-center justify-between font-mono">
                    <span className="font-bold text-white text-sm">{cur}%</span>
                    <span className={`text-[11px] font-bold ${isDiff ? 'text-amber-400' : 'text-emerald-400'}`}>
                      {cur > targetPct ? `+${round(cur - targetPct)}%` : 'OK'}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Proposed Actions */}
          <div className="space-y-2">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Recommended Optimization Trades
            </div>
            <div className="space-y-2">
              {proposedTrades.map((t, idx) => (
                <div
                  key={idx}
                  className="bg-slate-900/60 border border-slate-800 rounded-xl p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                >
                  <div className="flex items-center gap-2.5">
                    <span className={`px-2 py-0.5 rounded font-mono font-bold text-[10px] ${
                      t.action.includes('TRIM')
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    }`}>
                      {t.action}
                    </span>
                    <span className="font-bold text-white">{t.shares} shares of {t.ticker}</span>
                    <span className="text-slate-400 text-[11px]">({t.reason})</span>
                  </div>
                  <span className="font-mono text-slate-300 text-right">
                    ~₹{t.approxValue.toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Execution Button */}
          <div className="flex items-center justify-end gap-3 pt-2">
            {rebalanceApplied ? (
              <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-lg border border-emerald-500/30">
                <CheckCircle className="w-4 h-4" />
                <span>Rebalancing Plan Stored & Applied to Profile</span>
              </div>
            ) : (
              <button
                type="button"
                onClick={handleExecuteRebalance}
                disabled={isApplying}
                className="px-4 py-2 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white rounded-lg text-xs font-bold transition-all shadow-md shadow-violet-600/30 flex items-center gap-1.5"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isApplying ? 'animate-spin' : ''}`} />
                <span>{isApplying ? 'Applying Optimization...' : 'Execute Rebalance Optimization'}</span>
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
