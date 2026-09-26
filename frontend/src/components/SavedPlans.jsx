import React, { useState } from 'react';
import {
  Bookmark,
  MapPin,
  Calendar,
  Trash2,
  ArrowUpRight,
  RefreshCw,
  Sliders,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Activity,
  Play,
  Pause,
  Zap,
  TrendingDown,
  TrendingUp,
  Sparkles,
  ShieldCheck,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';

export default function SavedPlans({
  plans = [],
  onDeletePlan,
  onLoadPlan,
  onCheckPlan,
  onSimulateChange,
  onToggleStatus,
  onTriggerMonitoring,
  onUpdateInterval,
  monitoringStatus = {},
  isChecking = {},
  isPollingAll = false,
}) {
  const [expandedChanges, setExpandedChanges] = useState({});
  const [selectedInterval, setSelectedInterval] = useState(
    monitoringStatus.poll_interval_seconds || 60
  );

  const toggleChanges = (planId) => {
    setExpandedChanges((prev) => ({ ...prev, [planId]: !prev[planId] }));
  };

  const handleIntervalChange = (e) => {
    const val = parseInt(e.target.value, 10);
    setSelectedInterval(val);
    if (onUpdateInterval) {
      onUpdateInterval(val);
    }
  };

  const activePlansCount = plans.filter((p) => p.status === 'active').length;

  if (!plans || plans.length === 0) {
    return (
      <div className="w-full glass-panel rounded-2xl p-8 border border-slate-800 text-center space-y-3">
        <Bookmark className="w-8 h-8 text-slate-600 mx-auto" />
        <h4 className="text-sm font-semibold text-slate-300">No Saved Plans for Monitoring Yet</h4>
        <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
          Analyze any outdoor activity or expedition query, then click &quot;Save Plan to Workspace&quot; to activate smart background monitoring and automated change alerts.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full glass-panel rounded-2xl p-6 border border-slate-800 space-y-6">
      {/* Top Monitoring Header & Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center space-x-2.5 text-cyan-400">
            <Activity className="w-5 h-5 animate-pulse text-emerald-400" />
            <h3 className="text-base font-bold text-white tracking-tight">
              Smart Monitoring & Active Plans ({plans.length})
            </h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-700/60 text-emerald-300 font-semibold">
              {activePlansCount} Active
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
            Autonomous background scheduler continuously re-checks live telemetry against your saved snapshot. Meaningful shifts re-trigger the Risk, Recommendation, and Critic agents with deduplicated alerts.
          </p>
        </div>

        {/* Polling Interval & Scheduler Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Polling interval selector */}
          <div className="flex items-center space-x-2 bg-slate-900/80 px-3 py-1.5 rounded-xl border border-slate-800 text-xs">
            <Sliders className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-slate-400 text-[11px]">Poll Every:</span>
            <select
              value={selectedInterval}
              onChange={handleIntervalChange}
              className="bg-slate-950 text-cyan-300 text-xs font-mono font-semibold rounded px-2 py-0.5 border border-slate-700 focus:outline-none focus:border-cyan-500"
            >
              <option value={30}>30s (Rapid)</option>
              <option value={60}>60s (Standard)</option>
              <option value={120}>2 mins</option>
              <option value={300}>5 mins</option>
              <option value={600}>10 mins</option>
            </select>
          </div>

          {/* Trigger All Now Button */}
          {onTriggerMonitoring && (
            <button
              type="button"
              onClick={onTriggerMonitoring}
              disabled={isPollingAll}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700/80 text-white text-xs font-medium border border-slate-700 transition-all shadow-sm disabled:opacity-50"
              title="Run monitoring cycle across all active plans"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-cyan-400 ${isPollingAll ? 'animate-spin' : ''}`} />
              <span>{isPollingAll ? 'Polling...' : 'Poll All Active'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Plans Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {plans.map((plan) => {
          const isPlanChecking = isChecking[plan.id];
          const isExpanded = expandedChanges[plan.id];
          const hasDetectedChanges = plan.detected_changes && plan.detected_changes.length > 0;

          const initialRec = plan.initial_recommendation || {};
          const currentRec = plan.current_recommendation || {};
          const initialScore = initialRec.outdoor_score || plan.outdoor_score || 50;
          const currentScore = currentRec.outdoor_score || initialScore;
          const scoreDelta = currentScore - initialScore;
          const verdictShifted = initialRec.verdict_badge && currentRec.verdict_badge && initialRec.verdict_badge !== currentRec.verdict_badge;

          // Status style
          const isExpired = plan.status === 'expired';
          const isPaused = plan.status === 'paused';
          const isActive = plan.status === 'active';

          return (
            <div
              key={plan.id}
              className={`p-5 rounded-2xl border transition-all flex flex-col justify-between space-y-4 ${
                hasDetectedChanges
                  ? 'bg-slate-900/90 border-cyan-500/40 shadow-xl shadow-cyan-950/20'
                  : 'bg-slate-900/70 border-slate-800 hover:border-slate-700/80 shadow-lg'
              }`}
            >
              <div className="space-y-3">
                {/* Header: Title, Status Badge, Score */}
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      {/* Status badge */}
                      <span
                        className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded-full border flex items-center gap-1 font-semibold ${
                          isActive
                            ? 'bg-emerald-950/70 text-emerald-300 border-emerald-700/50'
                            : isPaused
                            ? 'bg-amber-950/70 text-amber-300 border-amber-700/50'
                            : 'bg-slate-800/80 text-slate-400 border-slate-700'
                        }`}
                      >
                        {isActive && <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping" />}
                        {isActive ? 'Monitoring Active' : isPaused ? 'Monitoring Paused' : 'Monitoring Concluded (Date Passed)'}
                      </span>

                      {/* Action tag */}
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/60">
                        {plan.action}
                      </span>
                    </div>

                    <h4 className="text-base font-bold text-white leading-snug">
                      {plan.subject || plan.title}
                    </h4>
                  </div>

                  {/* Score pill */}
                  <div className="text-right shrink-0">
                    <span className="text-lg font-black text-cyan-300 font-mono">
                      {currentScore}
                      <span className="text-xs text-slate-500 font-normal">/100</span>
                    </span>
                    <span className="text-[10px] font-bold block text-slate-400 uppercase tracking-wider">
                      {currentRec.verdict_badge || plan.verdict}
                    </span>
                  </div>
                </div>

                {/* Location, Target Date, Last Checked */}
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-400">
                  <span className="flex items-center gap-1 text-slate-300 font-medium">
                    <MapPin className="w-3.5 h-3.5 text-cyan-400" /> {plan.location}
                  </span>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5 text-slate-500" /> {plan.target_date}
                  </span>
                  <span>•</span>
                  <span className="text-[11px] font-mono text-cyan-400/90">
                    Checked: {plan.last_checked_at ? new Date(plan.last_checked_at).toLocaleTimeString() : 'Pending first check'}
                  </span>
                  <span className="text-slate-600">({plan.check_count} checks)</span>
                </div>

                {/* Score & Verdict Comparison Box (Initial vs Updated) */}
                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-xs space-y-2">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-400">Initial Snapshot:</span>
                    <span className="font-mono text-slate-300 font-medium">
                      Score: {initialScore}/100 • Verdict: <strong>{initialRec.verdict_badge || 'Caution'}</strong>
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] pt-1 border-t border-slate-800/60">
                    <span className="text-slate-400">Current Re-evaluation:</span>
                    <div className="flex items-center space-x-1.5 font-mono">
                      <span className={`font-bold ${currentScore >= 70 ? 'text-emerald-400' : currentScore >= 45 ? 'text-amber-400' : 'text-rose-400'}`}>
                        Score: {currentScore}/100
                      </span>
                      {scoreDelta !== 0 && (
                        <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded ${
                          scoreDelta > 0 ? 'bg-emerald-950 text-emerald-300' : 'bg-rose-950 text-rose-300'
                        }`}>
                          {scoreDelta > 0 ? `+${scoreDelta}` : scoreDelta} pts
                        </span>
                      )}
                      <span>•</span>
                      <span className="text-white font-bold">{currentRec.verdict_badge || 'Caution'}</span>
                    </div>
                  </div>

                  {verdictShifted && (
                    <div className="mt-1.5 p-2 rounded-lg bg-amber-950/50 border border-amber-600/40 text-[11px] text-amber-200 flex items-center space-x-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                      <span>
                        <strong>Verdict Shift Detected:</strong> {initialRec.verdict_badge} → <strong>{currentRec.verdict_badge}</strong>
                      </span>
                    </div>
                  )}
                </div>

                {/* Detected Changes Audit Trail */}
                <div className="pt-1">
                  {hasDetectedChanges ? (
                    <div className="space-y-2">
                      <button
                        type="button"
                        onClick={() => toggleChanges(plan.id)}
                        className="w-full flex items-center justify-between text-xs text-cyan-400 hover:text-cyan-300 font-medium transition-colors"
                      >
                        <span className="flex items-center gap-1.5">
                          <Zap className="w-3.5 h-3.5 text-amber-400" />
                          <span>Detected Changes ({plan.detected_changes.length})</span>
                        </span>
                        {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                      </button>

                      {isExpanded && (
                        <div className="p-3 rounded-xl bg-slate-950 border border-cyan-900/40 space-y-2 text-xs animate-fadeIn">
                          {plan.detected_changes.map((change, cIdx) => (
                            <div key={change.id || cIdx} className="border-b border-slate-800/80 pb-2 last:border-0 last:pb-0 space-y-0.5">
                              <div className="flex items-center justify-between text-[11px]">
                                <span className="font-semibold text-slate-200">{change.metric}</span>
                                <span className="font-mono text-cyan-300 font-bold">{change.old_value} → {change.new_value} ({change.delta})</span>
                              </div>
                              <p className="text-[11px] text-slate-400 leading-tight">
                                {change.significance_reason}
                              </p>
                              <span className="text-[9px] text-slate-500 font-mono block">
                                Detected: {new Date(change.timestamp).toLocaleTimeString()}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-[11px] text-slate-500 flex items-center space-x-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500/70" />
                      <span>Telemetry matches baseline snapshot (no significant shifts).</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center justify-between gap-2 pt-3 border-t border-slate-800/80">
                <div className="flex items-center space-x-2">
                  {/* Check Now Button */}
                  <button
                    type="button"
                    onClick={() => onCheckPlan(plan.id)}
                    disabled={isPlanChecking || isExpired}
                    className="text-xs px-2.5 py-1.5 rounded-lg bg-cyan-950/60 hover:bg-cyan-900/60 text-cyan-300 border border-cyan-800/50 flex items-center gap-1.5 font-medium transition-all disabled:opacity-40"
                    title="Check live weather now and re-run agents if changed"
                  >
                    <RefreshCw className={`w-3 h-3 ${isPlanChecking ? 'animate-spin' : ''}`} />
                    <span>{isPlanChecking ? 'Checking...' : 'Check Now'}</span>
                  </button>

                  {/* Simulate Shift Button (For testing & interactive demo) */}
                  {onSimulateChange && (
                    <button
                      type="button"
                      onClick={() => onSimulateChange(plan.id)}
                      disabled={isPlanChecking || isExpired}
                      className="text-xs px-2.5 py-1.5 rounded-lg bg-amber-950/50 hover:bg-amber-900/50 text-amber-300 border border-amber-800/50 flex items-center gap-1.5 font-medium transition-all disabled:opacity-40"
                      title="Simulate +45% rain and gusty winds to test re-triggering & alerts"
                    >
                      <Zap className="w-3 h-3 text-amber-400" />
                      <span>Simulate Shift</span>
                    </button>
                  )}

                  {/* Pause / Resume Button */}
                  {onToggleStatus && !isExpired && (
                    <button
                      type="button"
                      onClick={() => onToggleStatus(plan.id, isActive ? 'paused' : 'active')}
                      className="text-xs p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 border border-slate-700 transition-colors"
                      title={isActive ? 'Pause background monitoring' : 'Resume background monitoring'}
                    >
                      {isActive ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 text-emerald-400" />}
                    </button>
                  )}
                </div>

                <div className="flex items-center space-x-2">
                  {/* Load Plan into Workspace */}
                  <button
                    type="button"
                    onClick={() => onLoadPlan(plan)}
                    className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-medium transition-colors"
                    title="Load into active analysis workspace"
                  >
                    <span>Load</span>
                    <ArrowUpRight className="w-3.5 h-3.5" />
                  </button>

                  {/* Delete Button */}
                  <button
                    type="button"
                    onClick={() => onDeletePlan(plan.id)}
                    className="text-xs text-slate-500 hover:text-rose-400 p-1.5 rounded transition-colors"
                    title="Delete Plan"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
