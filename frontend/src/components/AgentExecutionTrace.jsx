import React, { useState } from 'react';
import {
  Terminal,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  AlertCircle,
  Clock,
  Cpu,
  Brain,
  ShieldCheck,
  RefreshCw,
  Sliders,
  DollarSign,
} from 'lucide-react';

export default function AgentExecutionTrace({
  trace = [],
  totalExecutionMs = 0,
  stoppingCondition = null,
}) {
  const [isOpen, setIsOpen] = useState(true);
  const [expandedSteps, setExpandedSteps] = useState({});

  if (!trace || trace.length === 0) return null;

  const toggleStep = (id) => {
    setExpandedSteps((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const expandAll = () => {
    const all = {};
    trace.forEach((s) => {
      all[s.id] = true;
    });
    setExpandedSteps(all);
  };

  const collapseAll = () => {
    setExpandedSteps({});
  };

  return (
    <div className="w-full glass-panel rounded-2xl border border-slate-800 shadow-xl overflow-hidden animate-fadeIn">
      {/* Header with toggle */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full p-5 flex items-center justify-between bg-slate-900/70 hover:bg-slate-900/90 transition-colors text-left"
      >
        <div className="flex items-center space-x-3.5">
          <div className="p-2.5 rounded-xl bg-cyan-950/70 border border-cyan-800/50 text-cyan-400">
            <Terminal className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="font-semibold text-sm sm:text-base text-white">
                Multi-Agent Audit Trace & Decision Trail
              </h3>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-cyan-300 font-mono border border-slate-700">
                {trace.length} Steps
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Verified record of agent actions, statuses, review verdicts, retries, durations, and reasoning
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {stoppingCondition && (
            <span className="hidden md:inline-flex items-center gap-1.5 text-[11px] font-mono text-slate-300 bg-slate-800 px-3 py-1 rounded-lg border border-slate-700">
              <Sliders className="w-3 h-3 text-cyan-400" />
              <span>Budget: {stoppingCondition.steps_executed}/{stoppingCondition.max_steps} steps</span>
            </span>
          )}
          <span className="text-xs font-mono text-cyan-300 bg-cyan-950/60 border border-cyan-800/60 px-3 py-1 rounded-lg">
            {totalExecutionMs}ms
          </span>
          <div className="p-1 rounded-lg bg-slate-800/80 text-slate-400">
            {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </div>
        </div>
      </button>

      {/* Expandable Trace Timeline */}
      {isOpen && (
        <div className="p-5 sm:p-6 border-t border-slate-800/80 space-y-5">
          {/* Quick Toolbar */}
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs border-b border-slate-800/60 pb-3">
            <span className="text-slate-400 font-medium">
              Click individual steps to inspect payload inputs and verified outputs:
            </span>
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={expandAll}
                className="text-[11px] font-mono text-cyan-400 hover:text-cyan-300 px-2 py-1 rounded hover:bg-slate-800/60 transition-colors"
              >
                Expand All
              </button>
              <span className="text-slate-600">•</span>
              <button
                type="button"
                onClick={collapseAll}
                className="text-[11px] font-mono text-slate-400 hover:text-slate-300 px-2 py-1 rounded hover:bg-slate-800/60 transition-colors"
              >
                Collapse All
              </button>
            </div>
          </div>

          {/* Stopping Condition Audit Banner */}
          {stoppingCondition && (
            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center space-x-2 text-slate-300">
                <Sliders className="w-4 h-4 text-cyan-400 shrink-0" />
                <span>
                  <strong>Stopping Condition:</strong> {stoppingCondition.reason}
                </span>
              </div>
              <div className="flex items-center gap-3 font-mono text-[11px] text-slate-400">
                <span>Reviews: <strong>{stoppingCondition.reviews_count}/{stoppingCondition.max_reviews}</strong></span>
                <span>•</span>
                <span>Steps: <strong>{stoppingCondition.steps_executed}/{stoppingCondition.max_steps}</strong></span>
                <span>•</span>
                <span>Time Budget: <strong>{stoppingCondition.duration_ms || totalExecutionMs}ms</strong> / {stoppingCondition.time_budget_ms}ms</span>
              </div>
            </div>
          )}

          {/* Timeline Nodes */}
          <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
            {trace.map((step, idx) => {
              const isExpanded = expandedSteps[step.id];
              const reviewDecision = step.review_decision || step.outputs?.verdict;
              const retries = step.retries !== undefined ? step.retries : (step.outputs?.retries || 0);

              return (
                <div key={step.id || idx} className="relative group">
                  {/* Timeline Node Icon */}
                  <span className="absolute -left-6 top-2 flex h-4 w-4 items-center justify-center rounded-full bg-slate-950 border-2 border-cyan-500 shadow-sm shadow-cyan-500/50">
                    <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
                  </span>

                  <div className="rounded-xl bg-slate-900/80 border border-slate-800 hover:border-slate-700/80 p-4 sm:p-5 space-y-3.5 transition-all shadow-md">
                    {/* Header: Agent Name, Action, Status, Review Decision, Retries, Duration */}
                    <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-2.5">
                      <div className="flex flex-wrap items-center gap-2">
                        {/* Agent Name */}
                        <span className="font-mono text-xs font-bold text-cyan-300 bg-cyan-950/70 px-2.5 py-1 rounded-md border border-cyan-800/50">
                          {step.agent_name}
                        </span>

                        {/* Action */}
                        {step.action && (
                          <span className="text-[11px] font-mono uppercase bg-slate-800/90 text-slate-300 px-2.5 py-0.5 rounded-md border border-slate-700">
                            Action: {step.action}
                          </span>
                        )}

                        {/* Review Decision (if critic or critique step) */}
                        {reviewDecision && (
                          <span
                            className={`text-[11px] font-mono uppercase px-2.5 py-0.5 rounded-md border flex items-center gap-1 font-semibold ${
                              reviewDecision === 'APPROVE'
                                ? 'bg-emerald-950/70 text-emerald-300 border-emerald-700/60'
                                : reviewDecision === 'REJECT'
                                ? 'bg-amber-950/70 text-amber-300 border-amber-700/60'
                                : 'bg-orange-950/70 text-orange-300 border-orange-700/60'
                            }`}
                          >
                            <ShieldCheck className="w-3 h-3" />
                            Review: {reviewDecision}
                          </span>
                        )}

                        {/* Retries */}
                        <span
                          className={`text-[11px] font-mono px-2 py-0.5 rounded-md border ${
                            retries > 0
                              ? 'bg-amber-950/50 text-amber-300 border-amber-800/50'
                              : 'bg-slate-800/50 text-slate-400 border-slate-700/50'
                          }`}
                        >
                          {retries} {retries === 1 ? 'Retry' : 'Retries'}
                        </span>
                      </div>

                      {/* Status & Duration */}
                      <div className="flex items-center space-x-3 text-xs font-mono">
                        <span
                          className={`flex items-center gap-1 font-semibold ${
                            step.status === 'completed'
                              ? 'text-emerald-400'
                              : step.status === 'running'
                              ? 'text-cyan-400'
                              : 'text-rose-400'
                          }`}
                        >
                          {step.status === 'completed' && <CheckCircle2 className="w-3.5 h-3.5" />}
                          {step.status === 'failed' && <AlertCircle className="w-3.5 h-3.5" />}
                          <span className="capitalize">{step.status}</span>
                        </span>
                        <span className="text-slate-600">•</span>
                        <span className="text-cyan-300 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                          {step.duration_ms} ms
                        </span>
                      </div>
                    </div>

                    {/* Step Summary */}
                    <p className="text-xs sm:text-sm text-slate-200 leading-relaxed font-medium">
                      {step.summary}
                    </p>

                    {/* Explicit Reasoning Block */}
                    {step.reasoning && (
                      <div className="p-3.5 rounded-xl bg-slate-950/80 border border-cyan-950/60 text-xs text-slate-300 space-y-1.5">
                        <div className="flex items-center space-x-1.5 text-cyan-400 font-semibold text-[11px]">
                          <Brain className="w-3.5 h-3.5" />
                          <span>Audit Reasoning & Heuristic Justification:</span>
                        </div>
                        <p className="text-[11px] text-slate-400 leading-relaxed pl-5 font-sans">
                          {step.reasoning}
                        </p>
                      </div>
                    )}

                    {/* Expand inputs / outputs */}
                    {(step.inputs || step.outputs) && (
                      <div className="pt-1">
                        <button
                          type="button"
                          onClick={() => toggleStep(step.id)}
                          className="text-[11px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-mono transition-colors"
                        >
                          {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                          <span>{isExpanded ? 'Hide Payload Details' : 'View Input & Output Payloads'}</span>
                        </button>

                        {isExpanded && (
                          <div className="mt-2.5 p-3.5 rounded-xl bg-slate-950 border border-slate-800 font-mono text-[11px] space-y-3 overflow-x-auto text-slate-300 animate-fadeIn">
                            {step.inputs && Object.keys(step.inputs).length > 0 && (
                              <div>
                                <span className="text-cyan-400 font-semibold block mb-1">Inputs:</span>
                                <pre className="text-slate-400 p-2.5 rounded bg-slate-900/60 border border-slate-800/80 overflow-x-auto">
                                  {JSON.stringify(step.inputs, null, 2)}
                                </pre>
                              </div>
                            )}
                            {step.outputs && Object.keys(step.outputs).length > 0 && (
                              <div>
                                <span className="text-emerald-400 font-semibold block mb-1">Outputs:</span>
                                <pre className="text-slate-400 p-2.5 rounded bg-slate-900/60 border border-slate-800/80 overflow-x-auto">
                                  {JSON.stringify(step.outputs, null, 2)}
                                </pre>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
