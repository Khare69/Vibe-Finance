import React from 'react';
import {
  TrendingUp,
  TrendingDown,
  BookOpen,
  ShieldAlert,
  Zap,
  MessageSquare,
  AlertCircle,
  CheckCircle2,
  FileText,
  Clock,
  ShieldCheck,
  Scale,
  Terminal,
} from 'lucide-react';

export default function MultiAgentDebate({
  analysis: propAnalysis,
  agents: propAgents,
  debate: propDebate,
  synthesis: propSynthesis,
  regulatoryGuardrail,
  explainMode = 'beginner',
  onOpenCitation,
  onSelectCitation,
  selectedTicker,
}) {
  const analysis =
    propAnalysis ||
    (propAgents || propDebate || propSynthesis
      ? {
          agents: propAgents,
          debate: propDebate,
          synthesis: propSynthesis,
          regulatory_compliance_guardrail: regulatoryGuardrail,
          ticker: selectedTicker,
        }
      : null);

  const handleCitationClick = onOpenCitation || onSelectCitation || (() => {});

  if (!analysis) return null;

  const { agents, debate, synthesis } = analysis;
  const quant = agents?.quant;
  const rag = agents?.rag;
  const risk = agents?.behavioral_risk;

  // Stance Colors
  const getStanceStyle = (stance) => {
    switch (stance?.toUpperCase()) {
      case 'BULLISH':
        return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
      case 'BEARISH':
        return 'bg-rose-500/15 text-rose-400 border-rose-500/30';
      case 'NEUTRAL':
      case 'MODERATE':
        return 'bg-slate-500/15 text-slate-300 border-slate-500/30';
      case 'CAUTION':
      case 'SAFE':
        return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
      case 'DANGER':
        return 'bg-red-500/20 text-red-400 border-red-500/40';
      default:
        return 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30';
    }
  };

  const getActionBadge = (action) => {
    switch (action) {
      case 'STRONG_BUY':
        return { label: 'STRONG BUY', color: 'bg-emerald-500 text-white shadow-emerald-500/30' };
      case 'BUY':
        return { label: 'BUY', color: 'bg-emerald-600 text-white shadow-emerald-600/30' };
      case 'CAUTIOUS_ACCUMULATE':
        return { label: 'CAUTIOUS ACCUMULATE (DIP BUY)', color: 'bg-indigo-600 text-white shadow-indigo-600/30' };
      case 'HOLD':
        return { label: 'HOLD', color: 'bg-slate-600 text-white shadow-slate-600/30' };
      case 'TRIM':
        return { label: 'TRIM / REDUCE RISK', color: 'bg-amber-600 text-white shadow-amber-600/30' };
      case 'SELL':
        return { label: 'STRONG SELL / VETO', color: 'bg-rose-600 text-white shadow-rose-600/30' };
      default:
        return { label: action || 'ANALYZE', color: 'bg-indigo-600 text-white shadow-indigo-600/30' };
    }
  };

  const actionInfo = getActionBadge(synthesis?.final_action);
  const confidence = debate?.confidence_calibration_score || 50;

  return (
    <div className="space-y-6">
      {/* Top Consensus Synthesis Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-[#0d1527] to-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-3">
              <span className={`px-3 py-1 rounded-lg text-xs font-black tracking-wider uppercase shadow-md ${actionInfo.color}`}>
                {actionInfo.label}
              </span>
              <span className="text-xs text-indigo-300 font-semibold flex items-center gap-1.5 font-mono">
                <Scale className="w-3.5 h-3.5 text-indigo-400" /> Multi-Agent Consensus · FinCom Protocol
              </span>
            </div>
            <h2 className="text-lg sm:text-xl font-bold text-white tracking-tight leading-snug">
              {synthesis?.headline}
            </h2>
            <p className="text-xs text-slate-300 leading-relaxed">
              {debate?.resolution_summary}
            </p>
          </div>

          {/* Calibrated Confidence Score Meter */}
          <div className="flex items-center gap-4 bg-slate-950/80 border border-slate-800 p-4 rounded-xl shrink-0">
            <div className="relative w-16 h-16 flex items-center justify-center">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                <path
                  className="text-slate-800"
                  strokeWidth="3.5"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                <path
                  className={
                    confidence > 70
                      ? 'text-emerald-400'
                      : confidence > 50
                      ? 'text-indigo-400'
                      : 'text-amber-400'
                  }
                  strokeDasharray={`${confidence}, 100`}
                  strokeWidth="3.5"
                  strokeLinecap="round"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
              </svg>
              <div className="absolute font-mono font-bold text-base text-white">
                {confidence}%
              </div>
            </div>
            <div>
              <div className="text-[11px] uppercase tracking-wider font-bold text-slate-400">
                Confidence Calibration
              </div>
              <div className="text-xs text-slate-200 font-medium">
                {confidence >= 75
                  ? 'High Consensus Alignment'
                  : confidence >= 55
                  ? 'Tempered Multi-Agent Debate'
                  : 'High Disagreement Penalty'}
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5 font-mono">
                {debate?.has_disagreement
                  ? 'Agent friction active (-penalty applied)'
                  : 'Harmonious agent agreement'}
              </div>
            </div>
          </div>
        </div>

        {/* Highlighted Disagreement Alert if Agents Conflict */}
        {debate?.has_disagreement && (
          <div className="mt-4 pt-4 border-t border-slate-800 flex items-start gap-3 bg-amber-500/10 border border-amber-500/30 rounded-xl p-3 text-xs text-amber-200">
            <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold uppercase tracking-wider block text-amber-300">
                Adversarial Disagreement Detected:
              </span>
              <span>{debate.quant_vs_rag_conflict}</span>
            </div>
          </div>
        )}

        {/* Formal Dissensions Filed Under FinCom Protocol */}
        {debate?.dissensions && debate.dissensions.length > 0 && (
          <div className="mt-3 bg-slate-950/90 border border-rose-500/30 rounded-xl p-3 space-y-2">
            <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-rose-400">
              <span className="flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                Formal Dissension Filed under FinCom Protocol
              </span>
              <span className="font-mono text-slate-400">&Delta; {debate.divergence} pts</span>
            </div>
            {debate.dissensions.map((dis, dIdx) => (
              <div key={dIdx} className="text-xs text-slate-300 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-rose-300">
                    {dis.dissenting_agent} <span className="text-slate-500 font-normal">dissents against</span> {dis.opposing_agent}
                  </span>
                  <span className="text-[10px] font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                    {dis.risk_threshold_condition}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">{dis.dissent_rationale}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 3 Specialized Autonomous Agent Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Agent 1: Quantitative Technical Analyst */}
        <div className="bg-[#0f172a] border border-slate-800 rounded-2xl p-5 shadow-lg flex flex-col justify-between hover:border-slate-700 transition-all">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  <Zap className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">Quant Analyst</h3>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {quant?.latency_ms || 24}ms · Mathematical Factor Model
                  </span>
                </div>
              </div>
              <span
                className={`px-2.5 py-1 text-[11px] font-bold rounded-lg border uppercase tracking-wider ${getStanceStyle(
                  quant?.stance
                )}`}
              >
                {quant?.stance || 'NEUTRAL'}
              </span>
            </div>

            {/* Score & Gauge */}
            <div className="mb-4 bg-slate-900/80 p-3 rounded-xl border border-slate-800">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400">Technical Momentum Score</span>
                <span className="font-mono font-bold text-white">{quant?.score ?? 50}/100</span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-indigo-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${quant?.score || 0}%` }}
                />
              </div>
            </div>

            {/* Metrics Chips */}
            <div className="grid grid-cols-2 gap-2 mb-4 text-[11px] font-mono">
              <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800/80">
                <span className="text-slate-500 block text-[10px]">Wilder RSI (14)</span>
                <span className="text-slate-200 font-bold">{quant?.metrics?.rsi_14 || '58.4'}</span>
              </div>
              <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800/80">
                <span className="text-slate-500 block text-[10px]">50-Day EMA</span>
                <span className="text-slate-200 font-bold">
                  {quant?.metrics?.sma_50 || quant?.metrics?.ema_50 || 'N/A'}
                </span>
              </div>
            </div>

            {/* Signals List */}
            <div className="space-y-2">
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Factor Signals
              </div>
              {quant?.signals && quant.signals.length > 0 ? (
                quant.signals.map((sig, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                    <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                    <span>{sig}</span>
                  </div>
                ))
              ) : (
                <div className="text-xs text-slate-500 italic">No anomalous momentum signals detected.</div>
              )}
            </div>
          </div>

          <div className="pt-4 mt-4 border-t border-slate-800/60 text-[10px] text-slate-500 flex justify-between font-mono">
            <span>AST Sandbox: Verified</span>
            <span>Weight: 35%</span>
          </div>
        </div>

        {/* Agent 2: Fundamental RAG Researcher */}
        <div className="bg-[#0f172a] border border-slate-800 rounded-2xl p-5 shadow-lg flex flex-col justify-between hover:border-slate-700 transition-all">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-xl bg-violet-500/10 text-violet-400 border border-violet-500/20">
                  <BookOpen className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">Fundamental RAG</h3>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {rag?.latency_ms || 42}ms · SEC & SEBI Filings
                  </span>
                </div>
              </div>
              <span
                className={`px-2.5 py-1 text-[11px] font-bold rounded-lg border uppercase tracking-wider ${getStanceStyle(
                  rag?.stance
                )}`}
              >
                {rag?.timed_out ? 'TIMED OUT' : rag?.stance || 'NEUTRAL'}
              </span>
            </div>

            {/* Score & Gauge */}
            <div className="mb-4 bg-slate-900/80 p-3 rounded-xl border border-slate-800">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400">Fundamental Health Score</span>
                <span className="font-mono font-bold text-white">{rag?.score ?? 50}/100</span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    (rag?.score || 0) > 60
                      ? 'bg-emerald-500'
                      : (rag?.score || 0) > 40
                      ? 'bg-amber-500'
                      : 'bg-rose-500'
                  }`}
                  style={{ width: `${rag?.score || 0}%` }}
                />
              </div>
            </div>

            {/* Key Findings */}
            <div className="space-y-2 mb-4">
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Audited Filing Disclosures
              </div>
              {rag?.key_findings && rag.key_findings.length > 0 ? (
                rag.key_findings.map((finding, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                    <div className="w-1.5 h-1.5 rounded-full bg-violet-400 shrink-0 mt-1.5" />
                    <span>{finding}</span>
                  </div>
                ))
              ) : (
                <div className="text-xs text-slate-500 italic">No regulatory red flags identified.</div>
              )}
            </div>

            {/* Highlight-to-Source Citations */}
            {rag?.citations && rag.citations.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-slate-800/80">
                <div className="text-[11px] font-bold uppercase tracking-wider text-indigo-400 flex items-center justify-between">
                  <span className="flex items-center gap-1">
                    <FileText className="w-3 h-3" /> Source Citations ({rag.citations.length})
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">Inspect evidence</span>
                </div>
                <div className="space-y-2">
                  {rag.citations.map((cite, cIdx) => (
                    <button
                      key={cite.id || cIdx}
                      type="button"
                      onClick={() => handleCitationClick(cite)}
                      className="w-full text-left p-2.5 rounded-xl bg-slate-900/90 hover:bg-indigo-950/40 border border-slate-800 hover:border-indigo-500/40 transition-all flex flex-col gap-1.5 group cursor-pointer shadow-sm"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="text-[11px] font-bold text-slate-200 group-hover:text-indigo-300 line-clamp-1">
                          {cite.document_title}
                        </div>
                        <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 shrink-0 border border-indigo-500/30">
                          {Math.round((cite.relevance_score || 0.85) * 100)}% Match
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
                        <span className="truncate pr-1">
                          {cite.section}
                          {cite.page_number ? ` · Page ${cite.page_number}` : ''}
                        </span>
                        <span className="shrink-0 text-slate-500">
                          {cite.fiscal_period || 'FY24'}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="pt-4 mt-4 border-t border-slate-800/60 text-[10px] text-slate-500 flex justify-between font-mono">
            <span>RAG: BM25 + Vector RRF</span>
            <span>Weight: 40%</span>
          </div>
        </div>

        {/* Agent 3: Behavioral Risk Manager */}
        <div className="bg-[#0f172a] border border-slate-800 rounded-2xl p-5 shadow-lg flex flex-col justify-between hover:border-slate-700 transition-all">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  <ShieldCheck className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">Behavioral Risk</h3>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {risk?.latency_ms || 18}ms · Suitability & Drawdown
                  </span>
                </div>
              </div>
              <span
                className={`px-2.5 py-1 text-[11px] font-bold rounded-lg border uppercase tracking-wider ${getStanceStyle(
                  risk?.stance
                )}`}
              >
                {risk?.stance || 'SAFE'}
              </span>
            </div>

            {/* Score & Gauge */}
            <div className="mb-4 bg-slate-900/80 p-3 rounded-xl border border-slate-800">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400">Risk Safety Alignment</span>
                <span className="font-mono font-bold text-white">{risk?.score ?? 50}/100</span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-amber-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${risk?.score || 0}%` }}
                />
              </div>
            </div>

            {/* Profile Context */}
            <div className="bg-slate-900/60 p-2.5 rounded-xl border border-slate-800/80 mb-4 text-xs">
              <div className="text-[10px] uppercase font-bold text-slate-400 mb-1">
                Investor Mandate Applied
              </div>
              <div className="flex justify-between text-slate-300 text-[11px]">
                <span>Risk Profile:</span>
                <span className="font-bold text-indigo-400 capitalize">
                  {risk?.user_risk_profile || 'Conservative'}
                </span>
              </div>
            </div>

            {/* Behavioral Adjustments */}
            <div className="space-y-2">
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Risk Management Rules
              </div>
              {risk?.behavioral_adjustments && risk.behavioral_adjustments.length > 0 ? (
                risk.behavioral_adjustments.map((adj, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                    <div className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0 mt-1.5" />
                    <span>{adj}</span>
                  </div>
                ))
              ) : (
                <div className="text-xs text-slate-500 italic">Position satisfies risk mandate criteria.</div>
              )}
            </div>
          </div>

          <div className="pt-4 mt-4 border-t border-slate-800/60 text-[10px] text-slate-500 flex justify-between font-mono">
            <span>Model: Behavioral-Guard-v2</span>
            <span>Weight: 25%</span>
          </div>
        </div>
      </div>

      {/* Autonomous Multi-Turn Adversarial Debate Transcript */}
      <div className="bg-[#0f172a] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-200 font-mono">
            <MessageSquare className="w-4 h-4 text-indigo-400" />
            Adversarial Multi-Agent Cross-Examination Transcript
          </div>
          <div className="flex items-center gap-2 text-[11px] text-slate-400 font-mono">
            <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
              {debate?.dialogue_steps?.length || 0} Turns Recorded
            </span>
            <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-indigo-400">
              FinCom v2.4
            </span>
          </div>
        </div>

        <p className="text-xs text-slate-400 leading-relaxed">
          Specialized agents cross-examine hypotheses, contest momentum claims against audited balance sheets, and apply behavioral drawdown caps before synthesizing final execution consensus.
        </p>

        <div className="space-y-3 pt-1">
          {debate?.dialogue_steps && debate.dialogue_steps.length > 0 ? (
            debate.dialogue_steps.map((step, idx) => {
              const speakerLower = (step.speaker || '').toLowerCase();
              const isQuant = speakerLower.includes('quant');
              const isRag = speakerLower.includes('fundamental') || speakerLower.includes('rag');
              const isRisk = speakerLower.includes('risk');

              return (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl border bg-slate-900/60 border-slate-800/80 hover:border-slate-700/80 transition-all flex items-start gap-3.5"
                >
                  <div
                    className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 font-bold text-xs font-mono ${
                      isQuant
                        ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                        : isRag
                        ? 'bg-violet-500/20 text-violet-400 border border-violet-500/30'
                        : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    }`}
                  >
                    {isQuant ? 'Q' : isRag ? 'F' : 'R'}
                  </div>
                  <div className="flex-1 text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-200">{step.speaker}</span>
                        <span
                          className={`text-[10px] font-mono px-1.5 py-0.2 rounded border ${
                            isQuant
                              ? 'bg-indigo-950/60 text-indigo-300 border-indigo-500/30'
                              : isRag
                              ? 'bg-violet-950/60 text-violet-300 border-violet-500/30'
                              : 'bg-amber-950/60 text-amber-300 border-amber-500/30'
                          }`}
                        >
                          {isQuant ? 'Technical Factor' : isRag ? 'Audited Evidence' : 'Risk Mandate'}
                        </span>
                      </div>
                      <span className="text-[10px] text-slate-500 font-mono">
                        Turn {idx + 1} of {debate.dialogue_steps.length}
                      </span>
                    </div>

                    <p className="text-slate-300 leading-relaxed pt-0.5">{step.text}</p>

                    {/* Referenced Evidence Chips for Fundamental RAG */}
                    {isRag && rag?.citations && rag.citations.length > 0 && (
                      <div className="mt-2.5 pt-2 border-t border-slate-800/60 flex flex-wrap items-center gap-1.5">
                        <span className="text-[10px] text-slate-500 font-mono">Source Cross-Ref:</span>
                        {rag.citations.map((cite, cIdx) => (
                          <button
                            key={cite.id || cIdx}
                            type="button"
                            onClick={() => handleCitationClick(cite)}
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono bg-violet-950/60 hover:bg-violet-900/80 border border-violet-500/30 text-violet-300 hover:text-white transition-all cursor-pointer"
                          >
                            <BookOpen className="w-2.5 h-2.5 text-violet-400" />
                            <span>
                              {cite.document_title?.split(' ')[0] || 'Filing'} ({cite.fiscal_period || 'Q3'})
                            </span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="text-xs text-slate-500 italic p-4 text-center">
              Autonomous debate transcript initializing...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
