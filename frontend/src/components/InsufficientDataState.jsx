import React from 'react';
import { DatabaseZap, AlertCircle, RefreshCw, Compass, Calendar, ArrowRight } from 'lucide-react';

export default function InsufficientDataState({ data, onRetry, onAdjustDate }) {
  if (!data) return null;

  const review = data.review || {};
  const message = data.message || review.critique_notes || 'Empirical telemetry for this location or date range is incomplete.';
  const correctionRequest = review.correction_request || 'DataAgent must acquire complete empirical telemetry including temperature, wind velocity, and multi-day forecast array.';

  return (
    <div className="w-full rounded-2xl p-6 sm:p-8 bg-amber-950/30 border border-amber-500/40 shadow-2xl relative overflow-hidden animate-fadeIn space-y-6">
      {/* Background accent */}
      <div className="absolute top-0 right-0 -mt-8 -mr-8 w-48 h-48 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-amber-900/50 pb-5">
        <div className="flex items-center space-x-3.5">
          <div className="p-3 rounded-xl bg-amber-900/40 border border-amber-700/50 text-amber-400 shrink-0">
            <DatabaseZap className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[11px] font-mono uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-amber-900/60 border border-amber-600/50 text-amber-300 font-semibold">
                Critic Gate Halted: NEEDS_MORE_DATA
              </span>
              <span className="text-xs text-slate-400">Zero Synthetic Hallucination Enforced</span>
            </div>
            <h3 className="text-lg sm:text-xl font-bold text-white mt-1">
              Insufficient Empirical Meteorological Telemetry
            </h3>
          </div>
        </div>

        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold text-xs transition-all shadow-lg shadow-amber-950/40 shrink-0 self-start sm:self-auto"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Re-execute Pipeline</span>
          </button>
        )}
      </div>

      {/* Critic Findings Audit */}
      <div className="space-y-3">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <AlertCircle className="w-3.5 h-3.5 text-amber-400" /> Adversarial Critic Audit Finding
        </h4>
        <div className="p-4 rounded-xl bg-slate-900/80 border border-amber-800/40 space-y-2 text-xs">
          <p className="text-amber-200 font-medium leading-relaxed">
            {message}
          </p>
          {correctionRequest && (
            <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-400">
              <span className="text-cyan-400 font-mono font-semibold">Required Data Remediation: </span>
              {correctionRequest}
            </div>
          )}
        </div>
      </div>

      {/* Actionable Guidance for the User */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1.5 text-xs">
          <div className="flex items-center space-x-2 text-slate-200 font-semibold">
            <Calendar className="w-3.5 h-3.5 text-cyan-400" />
            <span>Check Forecast Window</span>
          </div>
          <p className="text-slate-400 text-[11px] leading-relaxed">
            Empirical numerical weather models are verified up to 16 days forward. Dates beyond this window lack deterministic telemetry.
          </p>
          {onAdjustDate && (
            <button
              type="button"
              onClick={onAdjustDate}
              className="text-[11px] text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1 mt-1 pt-1"
            >
              <span>Reset to Today</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          )}
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1.5 text-xs">
          <div className="flex items-center space-x-2 text-slate-200 font-semibold">
            <Compass className="w-3.5 h-3.5 text-cyan-400" />
            <span>Clarify Geographic Area</span>
          </div>
          <p className="text-slate-400 text-[11px] leading-relaxed">
            Specify landmark, state, or region (e.g., &quot;Manali, Himachal Pradesh&quot;) if a generic query matches multiple sparse microclimates.
          </p>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1.5 text-xs">
          <div className="flex items-center space-x-2 text-slate-200 font-semibold">
            <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
            <span>Multi-Agent Constraint</span>
          </div>
          <p className="text-slate-400 text-[11px] leading-relaxed">
            MausamAI strictly forbids fabricating weather numbers when real data is unavailable. No synthetic substitutes are permitted.
          </p>
        </div>
      </div>
    </div>
  );
}
