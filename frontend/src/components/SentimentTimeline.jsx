import React from 'react';
import { BarChart3, TrendingUp, TrendingDown, ArrowRight, History } from 'lucide-react';

export default function SentimentTimeline({ sentimentData }) {
  if (!sentimentData) return null;

  const {
    current_quarter = 'Q3 FY26',
    previous_quarter = 'Q2 FY26',
    overall_sentiment_score_current = 0,
    overall_sentiment_score_previous = 0,
    keyword_frequencies = [],
  } = sentimentData;

  const sentimentDiff = overall_sentiment_score_current - overall_sentiment_score_previous;
  const isPositiveShift = sentimentDiff >= 0;

  return (
    <div className="bg-[#0f172a] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <BarChart3 className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide uppercase">
              Sentiment Shift Timeline
            </h3>
            <p className="text-xs text-slate-400">
              QoQ filing & transcript semantic analysis comparing {previous_quarter} vs {current_quarter}
            </p>
          </div>
        </div>

        {/* QoQ Sentiment Score Pill */}
        <div className="flex items-center gap-3 bg-slate-900/80 border border-slate-800 px-3 py-2 rounded-xl text-xs">
          <div>
            <span className="text-[10px] text-slate-500 uppercase block font-semibold">
              Tone Drift
            </span>
            <div className="flex items-center gap-1.5 font-mono font-bold">
              <span className={overall_sentiment_score_previous >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                {overall_sentiment_score_previous > 0 ? '+' : ''}
                {overall_sentiment_score_previous.toFixed(2)}
              </span>
              <ArrowRight className="w-3 h-3 text-slate-500" />
              <span className={overall_sentiment_score_current >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                {overall_sentiment_score_current > 0 ? '+' : ''}
                {overall_sentiment_score_current.toFixed(2)}
              </span>
            </div>
          </div>

          <div
            className={`px-2 py-1 rounded-md text-[11px] font-bold flex items-center gap-1 ${
              isPositiveShift
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
            }`}
          >
            {isPositiveShift ? (
              <TrendingUp className="w-3 h-3" />
            ) : (
              <TrendingDown className="w-3 h-3" />
            )}
            <span>
              {isPositiveShift ? '+' : ''}
              {sentimentDiff.toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      {/* Keyword Frequencies Comparison Chart */}
      <div className="space-y-3 pt-1">
        <div className="flex items-center justify-between text-xs text-slate-400 font-semibold">
          <span>Key Strategic Keywords Tracked:</span>
          <div className="flex items-center gap-4 text-[11px]">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-slate-600"></span>
              {previous_quarter}
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-indigo-500"></span>
              {current_quarter}
            </span>
          </div>
        </div>

        <div className="space-y-3">
          {keyword_frequencies.map((item, idx) => {
            const maxVal = Math.max(
              ...keyword_frequencies.map((k) => Math.max(k.current_count, k.previous_count)),
              15
            );
            const currWidth = Math.round((item.current_count / maxVal) * 100);
            const prevWidth = Math.round((item.previous_count / maxVal) * 100);
            const increased = item.current_count > item.previous_count;

            return (
              <div
                key={idx}
                className="bg-slate-900/50 p-3 rounded-xl border border-slate-800/80 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-center justify-between text-xs mb-2">
                  <span className="font-semibold text-slate-200 capitalize">
                    "{item.word}"
                  </span>
                  <div className="flex items-center gap-2 text-xs font-mono">
                    <span className="text-slate-400">{item.previous_count}x</span>
                    <ArrowRight className="w-3 h-3 text-slate-600" />
                    <span className={`font-bold ${increased ? 'text-indigo-400' : 'text-slate-300'}`}>
                      {item.current_count}x
                    </span>
                    <span
                      className={`text-[10px] px-1 rounded ${
                        increased
                          ? 'bg-indigo-500/20 text-indigo-300'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {increased ? `+${item.current_count - item.previous_count}` : `${item.current_count - item.previous_count}`}
                    </span>
                  </div>
                </div>

                {/* Comparative Double Bar */}
                <div className="space-y-1">
                  {/* Previous Quarter Bar */}
                  <div className="w-full bg-slate-800/80 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-slate-600 h-full rounded-full transition-all duration-500"
                      style={{ width: `${prevWidth}%` }}
                    />
                  </div>
                  {/* Current Quarter Bar */}
                  <div className="w-full bg-slate-800/80 h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-indigo-500 h-full rounded-full transition-all duration-500"
                      style={{ width: `${currWidth}%` }}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
