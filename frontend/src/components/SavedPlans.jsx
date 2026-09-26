import React from 'react';
import { Bookmark, MapPin, Calendar, Trash2, ArrowUpRight, CheckCircle2 } from 'lucide-react';

export default function SavedPlans({ plans, onDeletePlan, onLoadPlan }) {
  if (!plans || plans.length === 0) {
    return (
      <div className="w-full glass-panel rounded-2xl p-8 border border-slate-800 text-center space-y-3">
        <Bookmark className="w-8 h-8 text-slate-600 mx-auto" />
        <h4 className="text-sm font-semibold text-slate-300">No Saved Plans Yet</h4>
        <p className="text-xs text-slate-500 max-w-sm mx-auto">
          Analyze weather for an outdoor expedition and click "Save Plan" to pin it to your dashboard.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full glass-panel rounded-2xl p-6 border border-slate-800 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2 text-cyan-400">
          <Bookmark className="w-4 h-4" />
          <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-200">
            Saved Weather Expeditions & Plans ({plans.length})
          </h3>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {plans.map((plan) => (
          <div
            key={plan.id}
            className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-slate-700/80 transition-all flex flex-col justify-between space-y-3 group"
          >
            <div>
              <div className="flex items-start justify-between gap-2 mb-1.5">
                <span className="font-semibold text-sm text-white group-hover:text-cyan-300 transition-colors line-clamp-1">
                  {plan.title}
                </span>
                <span className="text-[11px] font-bold px-2 py-0.5 rounded-md bg-cyan-950/60 border border-cyan-800/40 text-cyan-300 shrink-0">
                  {plan.outdoor_score}/100
                </span>
              </div>

              <div className="flex items-center space-x-3 text-xs text-slate-400 mb-2">
                <span className="flex items-center gap-1">
                  <MapPin className="w-3 h-3 text-cyan-400" /> {plan.location}
                </span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Calendar className="w-3 h-3 text-slate-500" /> {plan.target_date}
                </span>
              </div>

              <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed">
                {plan.summary}
              </p>

              {/* Tags */}
              {plan.tags && (
                <div className="flex flex-wrap gap-1 mt-2.5">
                  {plan.tags.map((tag, i) => (
                    <span
                      key={i}
                      className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/50"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between pt-3 border-t border-slate-800/80">
              <button
                type="button"
                onClick={() => onLoadPlan(plan)}
                className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-medium transition-colors"
              >
                <span>View Details</span>
                <ArrowUpRight className="w-3 h-3" />
              </button>
              <button
                type="button"
                onClick={() => onDeletePlan(plan.id)}
                className="text-xs text-slate-500 hover:text-rose-400 p-1 rounded transition-colors"
                title="Delete Plan"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
