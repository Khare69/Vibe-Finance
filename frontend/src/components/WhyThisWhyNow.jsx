import React from 'react';
import { HelpCircle, Brain, SlidersHorizontal, BookOpen, Layers } from 'lucide-react';

export default function WhyThisWhyNow({
  synthesis,
  explainMode = 'beginner',
  onToggleExplainMode,
}) {
  if (!synthesis) return null;

  const weights = synthesis.weight_breakdown || {
    technicals: 35,
    fundamentals: 40,
    risk_profile: 25,
  };

  const isBeginner = explainMode === 'beginner';

  return (
    <div className="bg-[#0f172a] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-5">
      {/* Header with ELI5 Toggle */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide uppercase">
              "Why This, Why Now?" Decomposition
            </h3>
            <p className="text-xs text-slate-400">
              Transparent multi-agent attribution weights & explainable reasoning breakdown
            </p>
          </div>
        </div>

        {/* Explain Mode Toggle (ELI5 vs Institutional Expert) */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-900 border border-slate-800 rounded-xl self-start sm:self-auto">
          <button
            type="button"
            onClick={() => onToggleExplainMode('beginner')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
              isBeginner
                ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Brain className="w-3.5 h-3.5" />
            <span>ELI5 (Beginner)</span>
          </button>
          <button
            type="button"
            onClick={() => onToggleExplainMode('expert')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
              !isBeginner
                ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Institutional Expert</span>
          </button>
        </div>
      </div>

      {/* Attribution Weights Progress Bars */}
      <div className="space-y-3 pt-1">
        <div className="text-xs font-semibold text-slate-300 flex items-center justify-between">
          <span>Signal Weight Decomposition:</span>
          <span className="text-[11px] text-slate-500 font-mono">100% Attribution Total</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {/* Technicals Weight */}
          <div className="bg-slate-900/70 p-3 rounded-xl border border-slate-800">
            <div className="flex justify-between items-center text-xs mb-1.5">
              <span className="text-slate-400">Technicals (Quant)</span>
              <span className="font-mono font-bold text-indigo-400">{weights.technicals}%</span>
            </div>
            <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
              <div
                className="bg-indigo-500 h-full rounded-full transition-all duration-500"
                style={{ width: `${weights.technicals}%` }}
              />
            </div>
            <span className="text-[10px] text-slate-500 mt-1 block">
              Moving averages, volume surge, RSI
            </span>
          </div>

          {/* Fundamentals Weight */}
          <div className="bg-slate-900/70 p-3 rounded-xl border border-slate-800">
            <div className="flex justify-between items-center text-xs mb-1.5">
              <span className="text-slate-400">Fundamentals (RAG)</span>
              <span className="font-mono font-bold text-violet-400">{weights.fundamentals}%</span>
            </div>
            <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
              <div
                className="bg-violet-500 h-full rounded-full transition-all duration-500"
                style={{ width: `${weights.fundamentals}%` }}
              />
            </div>
            <span className="text-[10px] text-slate-500 mt-1 block">
              SEC/SEBI filings, margins, debt capex
            </span>
          </div>

          {/* Risk Profile Weight */}
          <div className="bg-slate-900/70 p-3 rounded-xl border border-slate-800">
            <div className="flex justify-between items-center text-xs mb-1.5">
              <span className="text-slate-400">Risk Profile (Behavioral)</span>
              <span className="font-mono font-bold text-amber-400">{weights.risk_profile}%</span>
            </div>
            <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
              <div
                className="bg-amber-500 h-full rounded-full transition-all duration-500"
                style={{ width: `${weights.risk_profile}%` }}
              />
            </div>
            <span className="text-[10px] text-slate-500 mt-1 block">
              Drawdown limits, panic score caps
            </span>
          </div>
        </div>
      </div>

      {/* Dynamic Explanation Panel (ELI5 vs Expert) */}
      <div
        className={`p-4 rounded-xl border transition-all ${
          isBeginner
            ? 'bg-gradient-to-r from-indigo-950/40 via-purple-950/20 to-slate-900 border-indigo-500/30'
            : 'bg-slate-900/90 border-slate-700/80'
        }`}
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span
              className={`text-xs uppercase font-bold tracking-wider px-2 py-0.5 rounded ${
                isBeginner
                  ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                  : 'bg-slate-800 text-slate-300 border border-slate-700'
              }`}
            >
              {isBeginner ? 'Plain English Analogy' : 'Institutional Macro Attribution'}
            </span>
          </div>
          <span className="text-[11px] text-slate-500">
            {isBeginner ? 'Simplified for clear intuition' : 'Quantitative portfolio terms'}
          </span>
        </div>

        <p className="text-sm text-slate-200 leading-relaxed font-sans">
          {isBeginner
            ? synthesis.explain_modes?.beginner ||
              'Imagine this company like an engine moving fast, but fuel costs are high. Because of your cautious style, waiting for a dip is safer.'
            : synthesis.explain_modes?.expert ||
              'Factor alpha is constrained by rising debt-service coverage ratios despite positive technical momentum divergence.'}
        </p>
      </div>
    </div>
  );
}
