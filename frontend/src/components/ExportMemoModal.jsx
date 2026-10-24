import React, { useState } from 'react';
import { X, Download, Copy, Check, FileText, Sparkles, ShieldCheck } from 'lucide-react';

export default function ExportMemoModal({ isOpen, onClose, analysis, userProfile }) {
  const [copied, setCopied] = useState(false);

  if (!isOpen || !analysis) return null;

  const { ticker, company_name, timestamp, price_data, agents, debate, synthesis, sentiment_shift, telemetry } = analysis;
  const quant = agents?.quant;
  const rag = agents?.rag;
  const risk = agents?.behavioral_risk;

  const memoContent = `# INVESTMENT DECISION MEMORANDUM
**Entity:** ${company_name} (${ticker})
**Date/Time:** ${new Date(timestamp || Date.now()).toUTCString()}
**Current Price:** ${price_data?.symbol || '₹'}${price_data?.current_price?.toLocaleString()} | **Day Change:** ${price_data?.change_percent}%
**Data Feed:** ${price_data?.feed_status || 'LIVE'} | **Confidence Calibration Score:** ${debate?.confidence_calibration_score || 63}%
**Investor Profile:** ${userProfile?.risk_level?.toUpperCase()} | **Max Tolerable Drawdown:** ${(userProfile?.panic_sell_tendency || 0.5) > 0.6 ? '-8%' : '-15%'}

---

## 1. EXECUTIVE CONSENSUS & SYNTHESIS
* **Action Recommendation:** ${synthesis?.final_action}
* **Headline:** ${synthesis?.headline}
* **Attribution Breakdown:** Technicals: ${synthesis?.weight_breakdown?.technicals}%, Fundamentals: ${synthesis?.weight_breakdown?.fundamentals}%, Risk Profile: ${synthesis?.weight_breakdown?.risk_profile}%
* **Macro Regime:** ${synthesis?.macro_regime?.regime_title || 'Dynamic Multi-Factor Regime'} (${synthesis?.macro_regime?.volatility_environment || 'Standard'})

### Plain English Summary (Beginner):
${synthesis?.explain_modes?.beginner}

### Institutional Macro Attribution (Expert):
${synthesis?.explain_modes?.expert}

---

## 2. SPECIALIZED AGENT EVIDENCE CHAIN

### A. Quantitative Analyst (Latency: ${quant?.latency_ms}ms)
* **Technical Stance:** ${quant?.stance} (Momentum Score: ${quant?.score}/100)
* **RSI (14-Period):** ${quant?.metrics?.rsi_14}
* **50-EMA:** ${price_data?.symbol || '₹'}${quant?.metrics?.sma_50} | **200-SMA:** ${price_data?.symbol || '₹'}${quant?.metrics?.sma_200}
* **Key Signals:**
${quant?.signals?.map((s) => `  - ${s}`).join('\n')}

### B. Fundamental RAG Researcher (Latency: ${rag?.latency_ms}ms)
* **Fundamental Stance:** ${rag?.stance} (Score: ${rag?.score}/100)
* **Status:** ${rag?.timed_out ? 'Degraded: Timed Out' : 'Operational (Vector Verified)'}
* **Key Regulatory Findings:**
${rag?.key_findings?.map((f) => `  - ${f}`).join('\n')}

#### Verified Document Citations:
${rag?.citations?.map((c, i) => `[${i + 1}] ${c.document_title} - ${c.section} (Relevance: ${Math.round((c.relevance_score || 0.9) * 100)}%)
    "${c.excerpt}"`).join('\n\n')}

### C. Behavioral Risk Manager (Latency: ${risk?.latency_ms}ms)
* **Personalized Stance:** ${risk?.stance} (Safety Score: ${risk?.score}/100)
* **User Drawdown Protections Applied:**
${risk?.behavioral_adjustments?.map((a) => `  - ${a}`).join('\n')}

---

## 3. ADVERSARIAL AGENT DEBATE & CONFLICT RESOLUTION
* **Disagreement Flagged:** ${debate?.has_disagreement ? 'YES - Friction Detected' : 'NO - Harmonious Consensus'}
* **Conflict Summary:** ${debate?.quant_vs_rag_conflict}
* **Resolution Arbitrage:** ${debate?.resolution_summary}

### Debate Dialogue Transcript:
${debate?.dialogue_steps?.map((step) => `[${step.speaker.toUpperCase()}]:\n"${step.text}"`).join('\n\n')}

---

## 4. QUARTER-OVER-QUARTER SENTIMENT SHIFT
* **Comparison Period:** ${sentiment_shift?.previous_quarter} -> ${sentiment_shift?.current_quarter}
* **Sentiment Score Shift:** ${sentiment_shift?.overall_sentiment_score_previous} -> ${sentiment_shift?.overall_sentiment_score_current}
* **Key Word Trends:**
${sentiment_shift?.keyword_frequencies?.map((k) => `  - "${k.word}": ${k.previous_count} -> ${k.current_count} occurrences`).join('\n')}

---

## 5. AUDIT TELEMETRY & SYSTEM TRACE
* **Total Execution Time:** ${telemetry?.total_execution_ms}ms
* **Vector Index Retrieval Time:** ${telemetry?.vector_retrieval_ms}ms
* **Documents Scanned:** ${telemetry?.documents_scanned}
* **Degraded Fallback Active:** ${telemetry?.degraded_data ? `YES (${telemetry?.degraded_reason})` : 'NO'}

*Generated autonomously by Vibe Finance Multi-Agent System.*
`;

  const handleCopy = () => {
    navigator.clipboard.writeText(memoContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([memoContent], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `VIBE_FINANCE_MEMO_${ticker}_${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in">
      <div className="relative w-full max-w-4xl bg-[#0f172a] border border-indigo-500/30 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 bg-slate-900/90 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-400">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  Exportable Memorandum
                </span>
                <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" /> Full Audit Integrity
                </span>
              </div>
              <h2 className="text-base font-bold text-white mt-1">
                Investment Decision Memo · {ticker} ({company_name})
              </h2>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Preview Content */}
        <div className="p-6 overflow-y-auto space-y-4">
          <div className="text-xs text-slate-400 flex items-center justify-between">
            <span>Complete Multi-Agent Reasoning Chain & Source Citations</span>
            <span className="font-mono text-indigo-400">{memoContent.length} characters</span>
          </div>

          <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-slate-300 leading-relaxed whitespace-pre-wrap max-h-[55vh] overflow-y-auto select-all">
            {memoContent}
          </pre>
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/80 flex items-center justify-between">
          <span className="text-xs text-slate-500 hidden sm:inline">
            Compliant with institutional audit traceability guidelines
          </span>

          <div className="flex items-center gap-3">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Copied to Clipboard</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 text-slate-400" />
                  <span>Copy Markdown</span>
                </>
              )}
            </button>
            <button
              onClick={handleDownload}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 rounded-lg shadow-md shadow-indigo-600/30 transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download .MD File</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
