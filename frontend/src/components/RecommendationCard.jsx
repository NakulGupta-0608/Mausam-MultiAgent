import React, { useState } from 'react';
import {
  CheckCircle,
  AlertTriangle,
  Bookmark,
  Check,
  Package,
  Clock,
  Shield,
  ThumbsUp,
  Sparkles,
  ArrowRight,
} from 'lucide-react';

const VERDICT_STYLES = {
  Optimal: {
    bg: 'bg-emerald-950/40',
    border: 'border-emerald-500/40',
    badge: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    scoreColor: 'text-emerald-400',
    barColor: 'from-emerald-500 to-teal-400',
  },
  Caution: {
    bg: 'bg-amber-950/40',
    border: 'border-amber-500/40',
    badge: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
    scoreColor: 'text-amber-400',
    barColor: 'from-amber-500 to-yellow-400',
  },
  Unfavorable: {
    bg: 'bg-orange-950/40',
    border: 'border-orange-500/40',
    badge: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
    scoreColor: 'text-orange-400',
    barColor: 'from-orange-500 to-red-400',
  },
  Severe: {
    bg: 'bg-rose-950/40',
    border: 'border-rose-500/40',
    badge: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
    scoreColor: 'text-rose-400',
    barColor: 'from-rose-500 to-red-600',
  },
};

export default function RecommendationCard({
  recommendation,
  query,
  location,
  targetDate,
  onSavePlan,
  isSaved,
}) {
  if (!recommendation) return null;

  const style = VERDICT_STYLES[recommendation.verdict_badge] || VERDICT_STYLES.Caution;
  const [checkedGear, setCheckedGear] = useState({});

  const toggleGear = (item) => {
    setCheckedGear((prev) => ({ ...prev, [item]: !prev[item] }));
  };

  const handleSave = () => {
    if (isSaved) return;
    onSavePlan({
      title: `${recommendation.activities[0]?.activity || 'Weather Plan'} @ ${location}`,
      location: location,
      target_date: targetDate,
      query: query,
      verdict: recommendation.verdict_badge,
      outdoor_score: recommendation.outdoor_score,
      summary: recommendation.comfort_summary,
      packing_checklist: recommendation.packing_checklist,
      tags: [recommendation.verdict_badge, recommendation.activities[0]?.activity || 'Outdoor'],
    });
  };

  return (
    <div className={`w-full rounded-2xl p-6 border shadow-2xl transition-all ${style.bg} ${style.border}`}>
      {/* Top Banner: Score & Verdict */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center space-x-2.5 mb-2">
            <span className={`text-xs uppercase font-bold tracking-wider px-3 py-1 rounded-full border ${style.badge}`}>
              {recommendation.verdict_badge}
            </span>
            <span className="text-xs text-slate-400 flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-cyan-400" /> Synthesized Agent Decision
            </span>
          </div>
          <h3 className="text-xl font-bold text-white tracking-tight">
            {recommendation.headline}
          </h3>
          <p className="text-sm text-slate-300 mt-1 max-w-2xl leading-relaxed">
            {recommendation.comfort_summary}
          </p>
        </div>

        {/* Outdoor Suitability Score Card */}
        <div className="flex items-center sm:flex-col items-end sm:items-center justify-between p-4 rounded-xl bg-slate-900/80 border border-slate-800 min-w-[140px]">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Suitability Score
          </span>
          <div className={`text-4xl font-black ${style.scoreColor} my-1`}>
            {recommendation.outdoor_score}<span className="text-base text-slate-500 font-normal">/100</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div
              className={`h-full bg-gradient-to-r ${style.barColor} rounded-full`}
              style={{ width: `${recommendation.outdoor_score}%` }}
            />
          </div>
        </div>
      </div>

      {/* Main Content Grid: Activity & Packing */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 pt-6">
        {/* Activity Recommendation */}
        <div className="lg:col-span-7 space-y-4">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-cyan-400" /> Activity Feasibility
          </h4>

          {recommendation.activities.map((act, idx) => (
            <div
              key={idx}
              className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3"
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-100 text-base">{act.activity}</span>
                <span
                  className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                    act.verdict === 'Recommended'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      : act.verdict === 'Conditional'
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                  }`}
                >
                  {act.verdict} ({act.confidence_score}% confidence)
                </span>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">
                {act.reasoning}
              </p>

              <div className="flex items-center space-x-2 text-xs text-cyan-300 bg-cyan-950/30 p-2.5 rounded-lg border border-cyan-800/40">
                <Clock className="w-4 h-4 text-cyan-400 shrink-0" />
                <span><strong>Recommended Window:</strong> {act.ideal_time_window}</span>
              </div>

              {act.alternatives && act.alternatives.length > 0 && (
                <div className="pt-1 text-xs text-slate-400">
                  <span className="text-slate-500 font-medium">Backup Alternatives: </span>
                  {act.alternatives.join(' • ')}
                </div>
              )}
            </div>
          ))}

          {/* Risk Alerts */}
          {recommendation.risk_alerts && recommendation.risk_alerts.length > 0 && (
            <div className="space-y-2 pt-2">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5 text-amber-400" /> Risk Assessment & Hazards
              </h4>
              <div className="space-y-2">
                {recommendation.risk_alerts.map((alert, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-start space-x-3 text-xs"
                  >
                    <AlertTriangle
                      className={`w-4 h-4 mt-0.5 shrink-0 ${
                        alert.severity === 'high' || alert.severity === 'critical'
                          ? 'text-rose-400'
                          : alert.severity === 'moderate'
                          ? 'text-amber-400'
                          : 'text-emerald-400'
                      }`}
                    />
                    <div className="space-y-0.5">
                      <div className="font-semibold text-slate-200">{alert.title}</div>
                      <div className="text-slate-400">{alert.description}</div>
                      <div className="text-cyan-300/90 text-[11px] pt-1">
                        <strong>Mitigation:</strong> {alert.mitigation}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Gear Checklist & Actions */}
        <div className="lg:col-span-5 space-y-4 flex flex-col justify-between">
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Package className="w-3.5 h-3.5 text-cyan-400" /> Dynamic Packing Checklist
            </h4>
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
              {recommendation.packing_checklist.map((item, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => toggleGear(item)}
                  className={`w-full flex items-center justify-between p-2.5 rounded-lg border text-xs text-left transition-all ${
                    checkedGear[item]
                      ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-200 line-through'
                      : 'bg-slate-850 hover:bg-slate-800/80 border-slate-700/60 text-slate-300'
                  }`}
                >
                  <span>{item}</span>
                  <div
                    className={`w-4 h-4 rounded border flex items-center justify-center transition-colors ${
                      checkedGear[item]
                        ? 'bg-emerald-500 border-emerald-500 text-slate-950'
                        : 'border-slate-600'
                    }`}
                  >
                    {checkedGear[item] && <Check className="w-3 h-3 stroke-[3]" />}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Action to Save Plan */}
          <div className="pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={handleSave}
              disabled={isSaved}
              className={`w-full flex items-center justify-center space-x-2 py-3 px-4 rounded-xl font-medium text-xs border transition-all ${
                isSaved
                  ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300 cursor-default'
                  : 'bg-slate-800 hover:bg-slate-700/80 border-slate-700 text-white shadow-md'
              }`}
            >
              {isSaved ? (
                <>
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                  <span>Plan Saved to Dashboard</span>
                </>
              ) : (
                <>
                  <Bookmark className="w-4 h-4 text-cyan-400" />
                  <span>Save Plan to Workspace</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
