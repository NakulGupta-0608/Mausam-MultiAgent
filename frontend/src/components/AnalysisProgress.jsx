import React from 'react';
import { Loader2, CheckCircle2, Clock, Cpu, RefreshCw, AlertCircle, Sparkles } from 'lucide-react';

export const INITIAL_STAGES = [
  {
    id: 'planner',
    agent: 'PlannerAgent',
    label: 'Strategic Task Planning',
    desc: 'Extracting entities, sub-goals, and atmospheric constraint thresholds',
  },
  {
    id: 'data',
    agent: 'DataAgent',
    label: 'Empirical Telemetry Retrieval',
    desc: 'Querying live Open-Meteo models without synthetic fabrication',
  },
  {
    id: 'risk',
    agent: 'RiskAnalysisAgent',
    label: 'Transparent Rule Evaluation',
    desc: 'Auditing precipitation, wind, UV, and thermal comfort boundaries',
  },
  {
    id: 'recommender',
    agent: 'RecommendationAgent',
    label: 'Comparative Decision Synthesis',
    desc: 'Evaluating 3 options, citing data evidence, and articulating limitations',
  },
  {
    id: 'critic',
    agent: 'CriticAgent',
    label: 'Adversarial Critique & Quality Audit',
    desc: 'Validating recommendation consistency against source data (max 2 cycles)',
  },
];

export default function AnalysisProgress({
  isAnalyzing,
  stages = {},
  liveMessage = '',
  activeAgent = '',
  reviewNotice = null,
}) {
  if (!isAnalyzing) return null;

  // Calculate actual completion based on backend events
  const completedStagesCount = INITIAL_STAGES.filter(
    (s) => stages[s.id]?.status === 'completed'
  ).length;

  const runningStage = INITIAL_STAGES.find(
    (s) => stages[s.id]?.status === 'running'
  );

  const basePercent = (completedStagesCount / INITIAL_STAGES.length) * 100;
  const progressPercent = Math.min(
    100,
    runningStage ? basePercent + 10 : basePercent
  );

  return (
    <div className="w-full glass-panel rounded-2xl p-5 sm:p-6 border border-cyan-500/40 bg-slate-900/95 shadow-2xl relative overflow-hidden animate-fadeIn space-y-5">
      {/* Background glow */}
      <div className="absolute top-0 left-1/4 w-96 h-32 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 relative z-10">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-xl bg-cyan-950/80 border border-cyan-700/50 text-cyan-400">
            <Cpu className="w-5 h-5 animate-spin" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="font-semibold text-sm text-white">
                5-Agent Orchestration Mesh Running
              </h3>
              <span className="text-[10px] font-mono uppercase bg-cyan-950 px-2 py-0.5 rounded border border-cyan-800/60 text-cyan-300">
                Live SSE Stream
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Real-time task dispatch across specialized planning, data, risk, and critique agents
            </p>
          </div>
        </div>

        {activeAgent && (
          <div className="flex items-center space-x-2 self-start sm:self-auto bg-slate-800/80 border border-slate-700 px-3 py-1.5 rounded-xl font-mono text-xs">
            <Loader2 className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
            <span className="text-slate-300">Active: </span>
            <span className="text-cyan-400 font-semibold">{activeAgent}</span>
          </div>
        )}
      </div>

      {/* Real-time Task Activity Ticker */}
      <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/90 text-xs flex items-center justify-between gap-3">
        <div className="flex items-center space-x-2.5 overflow-hidden">
          <span className="flex h-2 w-2 relative shrink-0">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500" />
          </span>
          <span className="text-slate-300 truncate font-mono text-[11px]">
            {liveMessage || 'Executing autonomous multi-agent pipeline...'}
          </span>
        </div>
        <span className="text-[10px] text-slate-500 font-mono shrink-0">
          {completedStagesCount}/{INITIAL_STAGES.length} Done
        </span>
      </div>

      {/* Review Loop Notice */}
      {reviewNotice && (
        <div className="p-3 rounded-xl bg-amber-950/40 border border-amber-500/40 text-xs text-amber-200 flex items-center space-x-2.5 animate-fadeIn">
          <RefreshCw className="w-4 h-4 text-amber-400 shrink-0 animate-spin" />
          <div className="space-y-0.5">
            <span className="font-semibold text-amber-300 block">
              Adversarial Revision Cycle (Attempt {reviewNotice.iteration}/2)
            </span>
            <span className="text-slate-300 text-[11px]">
              {reviewNotice.message}
            </span>
          </div>
        </div>
      )}

      {/* Progress Bar (Driven by actual completed backend events) */}
      <div className="w-full bg-slate-800/80 rounded-full h-2 overflow-hidden">
        <div
          className="bg-gradient-to-r from-cyan-500 via-blue-500 to-emerald-400 h-2 rounded-full transition-all duration-300 ease-out shadow-sm shadow-cyan-500/50"
          style={{ width: `${Math.max(8, progressPercent)}%` }}
        />
      </div>

      {/* 5 Agent Stage Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {INITIAL_STAGES.map((stage) => {
          const stageState = stages[stage.id] || { status: 'pending' };
          const isDone = stageState.status === 'completed';
          const isCurrent = stageState.status === 'running';
          const isFailed = stageState.status === 'failed';
          const isPending = stageState.status === 'pending';

          return (
            <div
              key={stage.id}
              className={`p-3.5 rounded-xl border transition-all flex flex-col justify-between ${
                isCurrent
                  ? 'bg-cyan-950/40 border-cyan-500/60 shadow-lg shadow-cyan-950/50 ring-1 ring-cyan-500/40'
                  : isDone
                  ? 'bg-slate-900/70 border-emerald-500/40 text-slate-300'
                  : isFailed
                  ? 'bg-rose-950/30 border-rose-500/40 text-rose-300'
                  : 'bg-slate-950/40 border-slate-800/60 text-slate-500'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className={`text-[10px] font-mono uppercase tracking-wider font-semibold ${
                    isCurrent ? 'text-cyan-300' : isDone ? 'text-emerald-400' : 'text-slate-400'
                  }`}>
                    {stage.agent}
                  </span>
                  {isCurrent && <Loader2 className="w-3.5 h-3.5 text-cyan-400 animate-spin" />}
                  {isDone && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
                  {isFailed && <AlertCircle className="w-3.5 h-3.5 text-rose-400" />}
                  {isPending && <Clock className="w-3.5 h-3.5 text-slate-600" />}
                </div>

                <h4 className={`text-xs font-semibold ${
                  isCurrent ? 'text-white' : isDone ? 'text-slate-100' : 'text-slate-400'
                }`}>
                  {stage.label}
                </h4>

                {stageState.action && (
                  <span className="inline-block mt-1 text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-400">
                    {stageState.action}
                  </span>
                )}
              </div>

              <div className="mt-2.5 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px]">
                <span className={isDone ? 'text-emerald-400 font-medium' : isCurrent ? 'text-cyan-400 font-medium' : 'text-slate-500'}>
                  {isDone ? 'Complete' : isCurrent ? 'Running...' : isFailed ? 'Halted' : 'Queued'}
                </span>
                {stageState.duration_ms !== undefined && (
                  <span className="font-mono text-slate-400">{stageState.duration_ms}ms</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
