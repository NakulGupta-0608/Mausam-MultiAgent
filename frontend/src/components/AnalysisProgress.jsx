import React from 'react';
import { Loader2, CheckCircle2, Clock, ShieldAlert, Cpu } from 'lucide-react';

const STAGES = [
  {
    id: 'weather',
    agent: 'WeatherAnalystAgent',
    label: 'Atmospheric Telemetry & Physics Model',
    desc: 'Resolving coordinates, atmospheric pressure, temperature & humidity cycles',
  },
  {
    id: 'planner',
    agent: 'ActivityPlannerAgent',
    label: 'Activity Feasibility & Optimal Windows',
    desc: 'Evaluating user query constraints, time windows, and equipment needs',
  },
  {
    id: 'risk',
    agent: 'RiskAssessorAgent',
    label: 'Hazard Profiling & Risk Mitigation',
    desc: 'Assessing precipitation, wind shear, UV radiation & air quality',
  },
];

export default function AnalysisProgress({ isAnalyzing, currentStageIndex = 0 }) {
  if (!isAnalyzing) return null;

  return (
    <div className="w-full glass-panel rounded-2xl p-5 border border-cyan-500/30 bg-slate-900/90 shadow-2xl relative overflow-hidden animate-fadeIn">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2 text-cyan-400">
          <Cpu className="w-5 h-5 animate-spin" />
          <h3 className="font-semibold text-sm tracking-wide text-white">
            Autonomous Multi-Agent Orchestration Pipeline
          </h3>
        </div>
        <span className="text-xs font-mono text-cyan-400/80 bg-cyan-950/60 px-2.5 py-0.5 rounded-full border border-cyan-800/40">
          Processing
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-800 rounded-full h-1.5 mb-6 overflow-hidden">
        <div
          className="bg-gradient-to-r from-cyan-500 via-blue-500 to-indigo-500 h-1.5 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${Math.max(15, ((currentStageIndex + 1) / STAGES.length) * 100)}%` }}
        />
      </div>

      {/* Agent Stages */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {STAGES.map((stage, idx) => {
          const isDone = idx < currentStageIndex;
          const isCurrent = idx === currentStageIndex;
          const isPending = idx > currentStageIndex;

          return (
            <div
              key={stage.id}
              className={`p-3.5 rounded-xl border transition-all ${
                isCurrent
                  ? 'bg-cyan-950/40 border-cyan-500/50 shadow-lg shadow-cyan-950/40 ring-1 ring-cyan-500/30'
                  : isDone
                  ? 'bg-slate-900/60 border-emerald-500/30 text-slate-300'
                  : 'bg-slate-950/40 border-slate-800/60 text-slate-500'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] font-mono uppercase tracking-wider text-cyan-400">
                  {stage.agent}
                </span>
                {isCurrent && <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />}
                {isDone && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                {isPending && <Clock className="w-4 h-4 text-slate-600" />}
              </div>
              <h4 className={`text-xs font-medium ${isCurrent ? 'text-white' : isDone ? 'text-slate-200' : 'text-slate-400'}`}>
                {stage.label}
              </h4>
              <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                {stage.desc}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
