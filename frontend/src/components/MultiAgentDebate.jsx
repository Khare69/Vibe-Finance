import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  BookOpen,
  ShieldAlert,
  Zap,
  MessageSquare,
  AlertCircle,
  CheckCircle2,
  HelpCircle,
  FileText,
  Clock,
  Sparkles,
  ArrowRight,
  Volume2,
  Square,
  Radio,
} from 'lucide-react';

export default function MultiAgentDebate({
  analysis,
  onOpenCitation,
}) {
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [activeSpeechIdx, setActiveSpeechIdx] = useState(null);

  // Cancel speech synthesis on unmount or when analysis/ticker changes
  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsPlayingAudio(false);
    setActiveSpeechIdx(null);

    return () => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, [analysis?.ticker]);

  if (!analysis) return null;

  const { agents, debate, synthesis } = analysis;
  const quant = agents?.quant;
  const rag = agents?.rag;
  const risk = agents?.behavioral_risk;

  const stopAudioDebate = () => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsPlayingAudio(false);
    setActiveSpeechIdx(null);
  };

  const playAudioDebate = () => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      alert('Speech synthesis is not supported on this browser.');
      return;
    }

    window.speechSynthesis.cancel();
    const steps = debate?.dialogue_steps || [];
    if (steps.length === 0) return;

    setIsPlayingAudio(true);
    let currentIdx = 0;

    const speakNextStep = () => {
      if (currentIdx >= steps.length) {
        setIsPlayingAudio(false);
        setActiveSpeechIdx(null);
        return;
      }

      setActiveSpeechIdx(currentIdx);
      const step = steps[currentIdx];
      const utterance = new SpeechSynthesisUtterance(`${step.speaker} says: ${step.text}`);

      // Modulate persona voice tone
      if (step.speaker.includes('Quant')) {
        utterance.pitch = 1.15;
        utterance.rate = 1.05;
      } else if (step.speaker.includes('Fundamental') || step.speaker.includes('RAG')) {
        utterance.pitch = 0.88;
        utterance.rate = 0.98;
      } else {
        utterance.pitch = 1.0;
        utterance.rate = 0.95;
      }

      utterance.onend = () => {
        currentIdx += 1;
        speakNextStep();
      };

      utterance.onerror = () => {
        setIsPlayingAudio(false);
        setActiveSpeechIdx(null);
      };

      window.speechSynthesis.speak(utterance);
    };

    speakNextStep();
  };

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
      <div className="bg-gradient-to-r from-indigo-950/70 via-slate-900 to-indigo-950/70 border border-indigo-500/30 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-3">
              <span className={`px-3 py-1 rounded-lg text-xs font-black tracking-wider uppercase shadow-md ${actionInfo.color}`}>
                {actionInfo.label}
              </span>
              <span className="text-xs text-indigo-300 font-semibold flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5" /> Multi-Agent Consensus
              </span>
            </div>
            <h2 className="text-lg sm:text-xl font-bold text-white tracking-tight leading-snug">
              {synthesis?.headline}
            </h2>
            <p className="text-xs text-slate-300">
              {debate?.resolution_summary}
            </p>
          </div>

          {/* Calibrated Confidence Score Meter */}
          <div className="flex items-center gap-4 bg-slate-900/90 border border-slate-800 p-4 rounded-xl shrink-0">
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
              <div className="text-[10px] text-slate-500 mt-0.5">
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
                Agent Disagreement Detected:
              </span>
              <span>{debate.quant_vs_rag_conflict}</span>
            </div>
          </div>
        )}
      </div>

      {/* 3 Specialized Agent Cards */}
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
                    {quant?.latency_ms}ms · Technicals
                  </span>
                </div>
              </div>
              <span
                className={`px-2.5 py-1 text-[11px] font-bold rounded-lg border uppercase tracking-wider ${getStanceStyle(
                  quant?.stance
                )}`}
              >
                {quant?.stance}
              </span>
            </div>

            {/* Score & Gauge */}
            <div className="mb-4 bg-slate-900/80 p-3 rounded-xl border border-slate-800">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400">Technical Momentum Score</span>
                <span className="font-mono font-bold text-white">{quant?.score}/100</span>
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
                <span className="text-slate-500 block text-[10px]">RSI (14)</span>
                <span className="text-slate-200 font-bold">{quant?.metrics?.rsi_14 || '58.4'}</span>
              </div>
              <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800/80">
                <span className="text-slate-500 block text-[10px]">50-Day EMA</span>
                <span className="text-slate-200 font-bold">₹{quant?.metrics?.sma_50 || 'N/A'}</span>
              </div>
            </div>

            {/* Signals List */}
            <div className="space-y-2">
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Primary Momentum Signals
              </div>
              {quant?.signals?.map((sig, idx) => (
                <div key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                  <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                  <span>{sig}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 mt-4 border-t border-slate-800/60 text-[10px] text-slate-500 flex justify-between">
            <span>Model: Momentum-Quant-v2</span>
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
                    {rag?.latency_ms}ms · SEC/SEBI Filings
                  </span>
                </div>
              </div>
              <span
                className={`px-2.5 py-1 text-[11px] font-bold rounded-lg border uppercase tracking-wider ${getStanceStyle(
                  rag?.stance
                )}`}
              >
                {rag?.timed_out ? 'TIMED OUT' : rag?.stance}
              </span>
            </div>

            {/* Score & Gauge */}
            <div className="mb-4 bg-slate-900/80 p-3 rounded-xl border border-slate-800">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400">Fundamental Health Score</span>
                <span className="font-mono font-bold text-white">{rag?.score}/100</span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    rag?.score > 60
                      ? 'bg-emerald-500'
                      : rag?.score > 40
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
                Key Filing Findings
              </div>
              {rag?.key_findings?.map((finding, idx) => (
                <div key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                  <div className="w-1.5 h-1.5 rounded-full bg-violet-400 shrink-0 mt-1.5" />
                  <span>{finding}</span>
                </div>
              ))}
            </div>

            {/* Highlight-to-Source Citations */}
            {rag?.citations && rag.citations.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-slate-800/80">
                <div className="text-[11px] font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-1">
                  <FileText className="w-3 h-3" /> Exact Source Citations (Click to View)
                </div>
                <div className="space-y-1.5">
                  {rag.citations.map((cite) => (
                    <button
                      key={cite.id}
                      type="button"
                      onClick={() => onOpenCitation(cite)}
                      className="w-full text-left p-2 rounded-lg bg-indigo-950/30 hover:bg-indigo-900/40 border border-indigo-500/20 hover:border-indigo-500/40 transition-all flex items-center justify-between group"
                    >
                      <div className="truncate pr-2">
                        <div className="text-[11px] font-semibold text-slate-200 group-hover:text-indigo-300 truncate">
                          {cite.document_title}
                        </div>
                        <div className="text-[10px] text-slate-400 truncate">
                          {cite.section}
                        </div>
                      </div>
                      <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 shrink-0">
                        {Math.round(cite.relevance_score * 100)}% Match
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="pt-4 mt-4 border-t border-slate-800/60 text-[10px] text-slate-500 flex justify-between">
            <span>RAG: Dense Vector Search</span>
            <span>Weight: 40%</span>
          </div>
        </div>

        {/* Agent 3: Behavioral Risk Manager */}
        <div className="bg-[#0f172a] border border-slate-800 rounded-2xl p-5 shadow-lg flex flex-col justify-between hover:border-slate-700 transition-all">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  <ShieldAlert className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">Behavioral Risk</h3>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {risk?.latency_ms}ms · Personalized
                  </span>
                </div>
              </div>
              <span
                className={`px-2.5 py-1 text-[11px] font-bold rounded-lg border uppercase tracking-wider ${getStanceStyle(
                  risk?.stance
                )}`}
              >
                {risk?.stance}
              </span>
            </div>

            {/* Score & Gauge */}
            <div className="mb-4 bg-slate-900/80 p-3 rounded-xl border border-slate-800">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400">Risk Safety Alignment</span>
                <span className="font-mono font-bold text-white">{risk?.score}/100</span>
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
                User Constraints Applied
              </div>
              <div className="flex justify-between text-slate-300 text-[11px]">
                <span>Risk Mandate:</span>
                <span className="font-bold text-indigo-400 capitalize">
                  {risk?.user_risk_profile}
                </span>
              </div>
            </div>

            {/* Behavioral Adjustments */}
            <div className="space-y-2">
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Personalized Risk Rules
              </div>
              {risk?.behavioral_adjustments?.map((adj, idx) => (
                <div key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                  <div className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0 mt-1.5" />
                  <span>{adj}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 mt-4 border-t border-slate-800/60 text-[10px] text-slate-500 flex justify-between">
            <span>Model: Behavioral-Guard-v1</span>
            <span>Weight: 25%</span>
          </div>
        </div>
      </div>

      {/* Multi-Turn Debate Dialogue Script with Audio Player */}
      <div className="bg-[#0f172a] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-300">
            <MessageSquare className="w-4 h-4 text-indigo-400" />
            Autonomous Agent Debate Transcript
          </div>

          {/* Audio Debate Controller */}
          <div className="flex items-center gap-2">
            {isPlayingAudio ? (
              <button
                type="button"
                onClick={stopAudioDebate}
                className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-rose-500/20 text-rose-300 border border-rose-500/40 text-xs font-bold transition-all hover:bg-rose-500/30"
              >
                <Square className="w-3 h-3 fill-current" />
                <span>Stop Audio</span>
                <span className="flex h-2 w-2 relative ml-1">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
                </span>
              </button>
            ) : (
              <button
                type="button"
                onClick={playAudioDebate}
                className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-bold transition-all shadow-sm shadow-indigo-600/30 active:scale-95"
              >
                <Volume2 className="w-3.5 h-3.5" />
                <span>Play Audio Debate</span>
              </button>
            )}
          </div>
        </div>

        <p className="text-xs text-slate-400">
          Watch and listen to the agents interrogate each other's conclusions in real-time before reaching synthesis
        </p>

        <div className="space-y-3 pt-2">
          {debate?.dialogue_steps?.map((step, idx) => {
            const isQuant = step.speaker.includes('Quant');
            const isRag = step.speaker.includes('Fundamental') || step.speaker.includes('RAG');
            const isRisk = step.speaker.includes('Risk');
            const isSpeakingNow = activeSpeechIdx === idx;

            return (
              <div
                key={idx}
                className={`p-3.5 rounded-xl border flex items-start gap-3.5 transition-all ${
                  isSpeakingNow
                    ? 'bg-indigo-950/40 border-indigo-500/80 shadow-lg shadow-indigo-500/10 ring-1 ring-indigo-500/50'
                    : 'bg-slate-900/60 border-slate-800/80 hover:border-slate-700'
                }`}
              >
                <div
                  className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 font-bold text-xs ${
                    isQuant
                      ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                      : isRag
                      ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                      : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                  }`}
                >
                  {isQuant ? 'Q' : isRag ? 'F' : 'R'}
                </div>
                <div className="flex-1 text-xs">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-200">{step.speaker}</span>
                      {isSpeakingNow && (
                        <span className="text-[10px] font-bold text-indigo-400 flex items-center gap-1 animate-pulse">
                          <Radio className="w-3 h-3" /> Speaking...
                        </span>
                      )}
                    </div>
                    <span className="text-[10px] text-slate-500 font-mono">
                      Step {idx + 1} of {debate.dialogue_steps.length}
                    </span>
                  </div>
                  <p className="text-slate-300 leading-relaxed">{step.text}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
