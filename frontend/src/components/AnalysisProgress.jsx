import React from 'react';
import { Loader2, CheckCircle2, Clock, Cpu, ShieldCheck } from 'lucide-react';

const STAGES = [
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

export default function AnalysisProgress({ isAnalyzing, currentStageIndex = 0 }) {
  if (!isAnalyzing) return null;

  return (
    <div className="w-full glass-panel rounded-2xl p-5 border border-cyan-500/30 bg-slate-900/90 shadow-2xl relative overflow-hidden animate-fadeIn">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2 text-cyan-400">
          <Cpu className="w-5 h-5 animate-spin" />
          <h3 className="font-semibold text-sm tracking-wide text-white">
            5-Agent Planning, Execution & Critique Mesh Active
          </h3>
        </div>
        <span className="text-xs font-mono text-cyan-400/80 bg-cyan-950/60 px-2.5 py-0.5 rounded-full border border-cyan-800/40">
          Orchestrating
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-800 rounded-full h-1.5 mb-6 overflow-hidden">
        <div
          className="bg-gradient-to-r from-cyan-500 via-blue-500 to-emerald-500 h-1.5 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${Math.max(15, ((currentStageIndex + 1) / STAGES.length) * 100)}%` }}
        />
      </div>

      {/* 5 Agent Stage Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {STAGES.map((stage, idx) => {
          const isDone = idx < currentStageIndex;
          const isCurrent = idx === currentStageIndex;
          const isPending = idx > currentStageIndex;

          return (
            <div
              key={stage.id}
              className={`p-3 rounded-xl border transition-all flex flex-col justify-between ${
                isCurrent
                  ? 'bg-cyan-950/40 border-cyan-500/50 shadow-lg shadow-cyan-950/40 ring-1 ring-cyan-500/30'
                  : isDone
                  ? 'bg-slate-900/60 border-emerald-500/30 text-slate-300'
                  : 'bg-slate-950/40 border-slate-800/60 text-slate-500'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400">
                    {stage.agent}
                  </span>
                  {isCurrent && <Loader2 className="w-3.5 h-3.5 text-cyan-400 animate-spin" />}
                  {isDone && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
                  {isPending && <Clock className="w-3.5 h-3.5 text-slate-600" />}
                </div>
                <h4 className={`text-xs font-semibold ${isCurrent ? 'text-white' : isDone ? 'text-slate-200' : 'text-slate-400'}`}>
                  {stage.label}
                </h4>
              </div>
              <p className="text-[10px] text-slate-400 mt-2 line-clamp-2">
                {stage.desc}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
