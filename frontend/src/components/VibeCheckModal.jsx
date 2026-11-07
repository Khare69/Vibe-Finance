import React, { useState } from 'react';
import { X, ShieldCheck, Zap, Sliders, AlertCircle, Compass, Scale } from 'lucide-react';

export default function VibeCheckModal({ isOpen, onClose, userProfile, onSaveProfile }) {
  if (!isOpen) return null;

  // Local interactive state
  const [marketDropReaction, setMarketDropReaction] = useState('panic_freeze');
  const [horizon, setHorizon] = useState(userProfile?.investment_horizon || 'medium');
  const [volatilityAppetite, setVolatilityAppetite] = useState('moderate');
  const [riskSlider, setRiskSlider] = useState(
    userProfile?.risk_level === 'aggressive'
      ? 80
      : userProfile?.risk_level === 'moderate'
      ? 50
      : 25
  );

  // Dynamic profile calculation based on scenarios & slider
  const calculateProfile = () => {
    let score = riskSlider;

    if (marketDropReaction === 'panic_sell') score -= 25;
    if (marketDropReaction === 'buy_dip') score += 20;

    if (volatilityAppetite === 'avoid') score -= 15;
    if (volatilityAppetite === 'all_in') score += 25;

    if (horizon === 'short') score -= 10;
    if (horizon === 'long') score += 15;

    score = Math.max(5, Math.min(95, score));

    let riskLevel = 'moderate';
    let panicTendency = 0.5;

    if (score < 40) {
      riskLevel = 'conservative';
      panicTendency = 0.82;
    } else if (score > 70) {
      riskLevel = 'aggressive';
      panicTendency = 0.25;
    } else {
      riskLevel = 'moderate';
      panicTendency = 0.52;
    }

    return { score, riskLevel, panicTendency };
  };

  const calculated = calculateProfile();

  const handleApply = () => {
    onSaveProfile({
      risk_level: calculated.riskLevel,
      investment_horizon: horizon,
      panic_sell_tendency: calculated.panicTendency,
      preferred_sectors: ['Tech', 'Energy'],
      portfolio_cash: userProfile?.portfolio_cash || 250000,
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl bg-[#0f172a] border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <Scale className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg sm:text-xl font-bold text-white tracking-tight">
                Investor Risk Profile Calibration
              </h2>
              <p className="text-xs text-slate-400">
                Calibrate behavioral risk tolerance and drawdown constraints to guide agent consensus
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-6 overflow-y-auto">
          {/* Scenario 1 */}
          <div className="space-y-3">
            <label className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center text-xs font-bold font-mono">1</span>
              Market Drawdown Scenario: The portfolio drops 10% in one week. What is your reaction?
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              {[
                { id: 'panic_sell', label: 'Liquidate to preserve cash', desc: 'Strict risk-off capital preservation' },
                { id: 'panic_freeze', label: 'Hold through volatility', desc: 'Wait for fundamental mean reversion' },
                { id: 'buy_dip', label: 'Opportunistically buy the dip', desc: 'Capitalize on value dislocations' },
              ].map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => setMarketDropReaction(opt.id)}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    marketDropReaction === opt.id
                      ? 'border-indigo-500 bg-indigo-500/15 text-white shadow-sm'
                      : 'border-slate-800 bg-slate-900/40 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                  }`}
                >
                  <div className="text-xs font-semibold text-slate-100">{opt.label}</div>
                  <div className="text-[11px] text-slate-400 mt-1">{opt.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Scenario 2 */}
          <div className="space-y-3">
            <label className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center text-xs font-bold font-mono">2</span>
              Investment Horizon: What is your primary capital allocation timeframe?
            </label>
            <div className="grid grid-cols-3 gap-2.5">
              {[
                { id: 'short', label: 'Short-Term', sub: '< 6 months' },
                { id: 'medium', label: 'Medium-Term', sub: '1 - 3 years' },
                { id: 'long', label: 'Long-Term', sub: '3 - 10+ years' },
              ].map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => setHorizon(opt.id)}
                  className={`p-3 rounded-xl border text-center transition-all ${
                    horizon === opt.id
                      ? 'border-indigo-500 bg-indigo-500/15 text-white'
                      : 'border-slate-800 bg-slate-900/40 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                  }`}
                >
                  <div className="text-xs font-semibold text-slate-100">{opt.label}</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">{opt.sub}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Scenario 3 */}
          <div className="space-y-3">
            <label className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center text-xs font-bold font-mono">3</span>
              High-Beta Volatility Appetite: Sizing in volatile growth equities
            </label>
            <div className="grid grid-cols-3 gap-2.5">
              {[
                { id: 'avoid', label: 'Strict Avoidance', desc: 'Focus exclusively on defensive cash flows' },
                { id: 'moderate', label: 'Capped (5-10%)', desc: 'Disciplined tactical satellite allocation' },
                { id: 'all_in', label: 'Core Allocation', desc: 'Embrace maximum beta & alpha potential' },
              ].map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => setVolatilityAppetite(opt.id)}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    volatilityAppetite === opt.id
                      ? 'border-indigo-500 bg-indigo-500/15 text-white'
                      : 'border-slate-800 bg-slate-900/40 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                  }`}
                >
                  <div className="text-xs font-semibold text-slate-100">{opt.label}</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">{opt.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Interactive Risk Slider */}
          <div className="space-y-2 pt-2 border-t border-slate-800/80">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                <Sliders className="w-3.5 h-3.5 text-indigo-400" /> Fine-Tune Risk Tolerance Meter:
              </span>
              <span className="font-mono font-bold text-indigo-400 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-500/30">
                {riskSlider} / 100
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              value={riskSlider}
              onChange={(e) => setRiskSlider(Number(e.target.value))}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
            />
            <div className="flex justify-between text-[11px] text-slate-500 font-mono">
              <span>Capital Preservation (0)</span>
              <span>Balanced Growth (50)</span>
              <span>Max Alpha (100)</span>
            </div>
          </div>

          {/* Instant Calibrated Profile Preview */}
          <div className="p-4 rounded-xl border border-indigo-500/30 bg-slate-950/80 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-indigo-400" />
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-300 font-mono">
                  Calibrated Risk Mandate
                </span>
              </div>
              <span
                className={`px-3 py-1 text-xs font-bold uppercase rounded-full border ${
                  calculated.riskLevel === 'conservative'
                    ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
                    : calculated.riskLevel === 'aggressive'
                    ? 'bg-rose-500/20 text-rose-400 border-rose-500/40'
                    : 'bg-indigo-500/20 text-indigo-400 border-indigo-500/40'
                }`}
              >
                {calculated.riskLevel}
              </span>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              {calculated.riskLevel === 'conservative' &&
                'The Behavioral Risk Agent will prioritize capital preservation, penalize volatile speculative rallies, and require strict margin-of-safety fundamentals.'}
              {calculated.riskLevel === 'moderate' &&
                'The Behavioral Risk Agent will balance momentum breakout opportunities with disciplined downside stop-loss guidance and defensive sector anchors.'}
              {calculated.riskLevel === 'aggressive' &&
                'The Behavioral Risk Agent will permit higher beta exposure, allowing Quant momentum and high-conviction catalysts to drive the consensus action.'}
            </p>

            <div className="grid grid-cols-2 gap-3 pt-2 border-t border-slate-800/80 text-[11px] text-slate-400 font-mono">
              <div>
                Panic Sell Sensitivity:{' '}
                <span className="text-white font-bold">{calculated.panicTendency}</span>
              </div>
              <div>
                Max Tolerable Drawdown:{' '}
                <span className="text-white font-bold">
                  {calculated.riskLevel === 'conservative'
                    ? '-8%'
                    : calculated.riskLevel === 'moderate'
                    ? '-15%'
                    : '-25%'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/60 flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium text-slate-300 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleApply}
            className="px-5 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg shadow-md shadow-indigo-600/30 transition-all hover:scale-[1.02]"
          >
            Apply & Recalibrate Engine
          </button>
        </div>
      </div>
    </div>
  );
}
