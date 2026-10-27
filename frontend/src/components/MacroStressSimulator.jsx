import React, { useState } from 'react';
import { ShieldAlert, TrendingDown, TrendingUp, Zap, RotateCcw, AlertTriangle, ArrowRight } from 'lucide-react';

export default function MacroStressSimulator({ portfolio, activeTicker = 'NVDA' }) {
  const [selectedScenario, setSelectedScenario] = useState('tech_crunch');

  const totalValue = portfolio?.total_value || 500000;

  const scenarios = {
    tech_crunch: {
      name: '2022 Fed Rate Hike Shock (+400 bps)',
      description: 'Rapid quantitative tightening and multiple compression across growth equities.',
      techDelta: -24.5,
      energyDelta: +14.2,
      financialsDelta: -4.8,
      overallPortfolioDelta: -14.6,
      quantStance: 'BEARISH (Breakdown below 200-SMA)',
      ragStance: 'NEUTRAL (DCF Discount Rate Escalation)',
      riskStance: 'MAX DEFENSIVE (Cap allocation to <3%)'
    },
    covid_crash: {
      name: '2020 Liquidity Crunch (Global Lockdowns)',
      description: 'Severe sudden market-wide drawdown and tail-risk volatility spike.',
      techDelta: -18.2,
      energyDelta: -32.5,
      financialsDelta: -21.0,
      overallPortfolioDelta: -22.4,
      quantStance: 'DEEPLY OVERSOLD (RSI < 25)',
      ragStance: 'BEARISH (Cash Flow Disruption Alerts)',
      riskStance: 'EMERGENCY DRAWDOWN HALT'
    },
    energy_spike: {
      name: 'Crude Oil Supply Shock ($120/bbl)',
      description: 'Geopolitical disruption driving commodity inflation and margin pressure.',
      techDelta: -8.5,
      energyDelta: +34.0,
      financialsDelta: +2.5,
      overallPortfolioDelta: +4.2,
      quantStance: 'ROTATION INFLOW (Energy momentum surge)',
      ragStance: 'MIXED (Refining gains vs input costs)',
      riskStance: 'BALANCED (Hedge tech exposure)'
    }
  };

  const active = scenarios[selectedScenario];
  const projectedPnL = Math.round((active.overallPortfolioDelta / 100) * totalValue);
  const isLoss = active.overallPortfolioDelta < 0;

  return (
    <div className="bg-[#0f172a] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide uppercase">
              Macro Shock Stress-Testing Engine
            </h3>
            <p className="text-xs text-slate-400">
              Simulate extreme historical macro shocks on your portfolio and agent weights
            </p>
          </div>
        </div>

        {/* Scenario Selector Pills */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-900 border border-slate-800 rounded-xl text-xs">
          <button
            type="button"
            onClick={() => setSelectedScenario('tech_crunch')}
            className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
              selectedScenario === 'tech_crunch'
                ? 'bg-rose-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            2022 Rates
          </button>
          <button
            type="button"
            onClick={() => setSelectedScenario('covid_crash')}
            className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
              selectedScenario === 'covid_crash'
                ? 'bg-rose-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            2020 Crash
          </button>
          <button
            type="button"
            onClick={() => setSelectedScenario('energy_spike')}
            className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
              selectedScenario === 'energy_spike'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Energy Shock
          </button>
        </div>
      </div>

      {/* Scenario Overview Card */}
      <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h4 className="text-sm font-bold text-white">{active.name}</h4>
            <p className="text-xs text-slate-400">{active.description}</p>
          </div>
          <div className="text-right shrink-0">
            <span className="text-[10px] text-slate-500 uppercase font-bold block">
              Projected Portfolio Impact
            </span>
            <div className={`text-lg font-mono font-bold flex items-center justify-end gap-1 ${
              isLoss ? 'text-rose-400' : 'text-emerald-400'
            }`}>
              {isLoss ? <TrendingDown className="w-4 h-4" /> : <TrendingUp className="w-4 h-4" />}
              <span>{isLoss ? '' : '+'}{active.overallPortfolioDelta}%</span>
              <span className="text-xs text-slate-400">
                ({isLoss ? '-' : '+'}₹{Math.abs(projectedPnL).toLocaleString()})
              </span>
            </div>
          </div>
        </div>

        {/* Sector Deltas */}
        <div className="grid grid-cols-3 gap-3 pt-2 text-xs border-t border-slate-800/80 font-mono">
          <div className="bg-slate-950/60 p-2.5 rounded-lg">
            <span className="text-slate-500 text-[10px] block">Tech Sector</span>
            <span className={`font-bold ${active.techDelta >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {active.techDelta >= 0 ? '+' : ''}{active.techDelta}%
            </span>
          </div>
          <div className="bg-slate-950/60 p-2.5 rounded-lg">
            <span className="text-slate-500 text-[10px] block">Energy Sector</span>
            <span className={`font-bold ${active.energyDelta >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {active.energyDelta >= 0 ? '+' : ''}{active.energyDelta}%
            </span>
          </div>
          <div className="bg-slate-950/60 p-2.5 rounded-lg">
            <span className="text-slate-500 text-[10px] block">Financials Sector</span>
            <span className={`font-bold ${active.financialsDelta >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {active.financialsDelta >= 0 ? '+' : ''}{active.financialsDelta}%
            </span>
          </div>
        </div>
      </div>

      {/* Autonomous Agent Defensive Re-calibration */}
      <div className="space-y-2">
        <div className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Agent Response Calibration During This Shock
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <span className="text-indigo-400 font-bold block mb-1">Quant Agent:</span>
            <span className="text-slate-300 text-[11px]">{active.quantStance}</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <span className="text-violet-400 font-bold block mb-1">Fundamental RAG:</span>
            <span className="text-slate-300 text-[11px]">{active.ragStance}</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <span className="text-amber-400 font-bold block mb-1">Risk Manager:</span>
            <span className="text-slate-300 text-[11px]">{active.riskStance}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
