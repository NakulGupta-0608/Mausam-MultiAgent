import React, { useState } from 'react';
import { Terminal, ChevronDown, ChevronRight, CheckCircle2, AlertCircle, Clock, Cpu, Brain, Zap } from 'lucide-react';

export default function AgentExecutionTrace({ trace = [], totalExecutionMs = 0, stoppingCondition = null }) {
  const [isOpen, setIsOpen] = useState(true);
  const [expandedSteps, setExpandedSteps] = useState({});

  if (!trace || trace.length === 0) return null;

  const toggleStep = (id) => {
    setExpandedSteps((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="w-full glass-panel rounded-2xl border border-slate-800 shadow-xl overflow-hidden">
      {/* Header with toggle */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full p-5 flex items-center justify-between bg-slate-900/60 hover:bg-slate-900/90 transition-colors text-left"
      >
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-cyan-950/60 border border-cyan-800/40 text-cyan-400">
            <Terminal className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="font-semibold text-sm text-white">Multi-Agent Audit Trace & Execution Timeline</h3>
              <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">
                {trace.length} Steps Logged
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Transparent logging of action, input, output, and explicit reasoning across every agent
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {stoppingCondition && (
            <span className="hidden sm:inline-block text-[11px] font-mono text-slate-400 bg-slate-800 px-2.5 py-1 rounded-md border border-slate-700">
              Budget: {stoppingCondition.steps_executed}/{stoppingCondition.max_steps} steps
            </span>
          )}
          <span className="text-xs font-mono text-cyan-400 bg-cyan-950/40 border border-cyan-800/50 px-2.5 py-1 rounded-md">
            Total: {totalExecutionMs}ms
          </span>
          {isOpen ? (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronRight className="w-4 h-4 text-slate-400" />
          )}
        </div>
      </button>

      {/* Trace Timeline */}
      {isOpen && (
        <div className="p-5 border-t border-slate-800 space-y-4">
          {/* Stopping Condition Notice */}
          {stoppingCondition && stoppingCondition.stopped_early && (
            <div className="p-3.5 rounded-xl bg-amber-950/40 border border-amber-500/40 text-xs text-amber-200 flex items-center space-x-2.5 mb-2">
              <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>
                <strong>Stopping Condition Triggered:</strong> {stoppingCondition.reason} (Reviews: {stoppingCondition.reviews_count}/{stoppingCondition.max_reviews})
              </span>
            </div>
          )}

          <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
            {trace.map((step, idx) => {
              const isExpanded = expandedSteps[step.id];

              return (
                <div key={step.id || idx} className="relative group">
                  {/* Timeline node */}
                  <span className="absolute -left-6 top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-slate-900 border-2 border-cyan-500 shadow-sm shadow-cyan-500/50">
                    <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
                  </span>

                  <div className="rounded-xl bg-slate-900/70 border border-slate-800/90 p-4 space-y-3 hover:border-slate-700 transition-all">
                    {/* Header Row */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs font-bold text-cyan-300 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/40">
                          {step.agent_name}
                        </span>
                        <span className="text-xs text-slate-400 font-medium">
                          {step.stage}
                        </span>
                        {step.action && (
                          <span className="text-[10px] font-mono uppercase bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">
                            {step.action}
                          </span>
                        )}
                      </div>

                      <div className="flex items-center space-x-2 text-[11px] font-mono text-slate-400">
                        <span className={`flex items-center gap-1 ${step.status === 'completed' ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {step.status === 'completed' ? <CheckCircle2 className="w-3.5 h-3.5" /> : <AlertCircle className="w-3.5 h-3.5" />}
                          {step.status}
                        </span>
                        <span>•</span>
                        <span className="text-cyan-400">{step.duration_ms} ms</span>
                      </div>
                    </div>

                    {/* Summary */}
                    <p className="text-xs text-slate-200 leading-relaxed font-medium">
                      {step.summary}
                    </p>

                    {/* Explicit Reasoning Block */}
                    {step.reasoning && (
                      <div className="p-3 rounded-lg bg-slate-950/70 border border-cyan-950 text-xs text-slate-300 space-y-1">
                        <div className="flex items-center space-x-1.5 text-cyan-400 font-semibold text-[11px]">
                          <Brain className="w-3.5 h-3.5" />
                          <span>Audit Reasoning & Heuristic Deduction:</span>
                        </div>
                        <p className="text-[11px] text-slate-400 leading-relaxed pl-5">
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
                          <span>{isExpanded ? 'Hide Payload Details' : 'View Input & Output Data'}</span>
                        </button>

                        {isExpanded && (
                          <div className="mt-2.5 p-3 rounded-lg bg-slate-950/90 border border-slate-800 font-mono text-[11px] space-y-2 overflow-x-auto text-slate-300">
                            {step.inputs && Object.keys(step.inputs).length > 0 && (
                              <div>
                                <span className="text-cyan-400 font-semibold block mb-1">Inputs:</span>
                                <pre className="text-slate-400">{JSON.stringify(step.inputs, null, 2)}</pre>
                              </div>
                            )}
                            {step.outputs && Object.keys(step.outputs).length > 0 && (
                              <div>
                                <span className="text-emerald-400 font-semibold block mb-1">Outputs:</span>
                                <pre className="text-slate-400">{JSON.stringify(step.outputs, null, 2)}</pre>
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
