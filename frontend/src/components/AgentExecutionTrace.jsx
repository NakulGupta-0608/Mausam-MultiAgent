import React, { useState } from 'react';
import { Terminal, ChevronDown, ChevronRight, CheckCircle2, Clock, Cpu } from 'lucide-react';

export default function AgentExecutionTrace({ trace = [], totalExecutionMs = 0 }) {
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
              <h3 className="font-semibold text-sm text-white">Multi-Agent Execution Trace</h3>
              <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">
                {trace.length} Steps
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Live observability and step-by-step pipeline telemetry
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
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
          <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
            {trace.map((step, idx) => {
              const isExpanded = expandedSteps[step.id];

              return (
                <div key={step.id || idx} className="relative group">
                  {/* Timeline node */}
                  <span className="absolute -left-6 top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-slate-900 border-2 border-cyan-500 shadow-sm shadow-cyan-500/50">
                    <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
                  </span>

                  <div className="rounded-xl bg-slate-900/70 border border-slate-800/90 p-4 space-y-2 hover:border-slate-700 transition-all">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-xs font-bold text-cyan-300 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/40">
                          {step.agent_name}
                        </span>
                        <span className="text-xs text-slate-400 font-medium">
                          {step.stage}
                        </span>
                      </div>

                      <div className="flex items-center space-x-2 text-[11px] font-mono text-slate-400">
                        <span className="flex items-center gap-1 text-emerald-400">
                          <CheckCircle2 className="w-3.5 h-3.5" /> {step.status}
                        </span>
                        <span>•</span>
                        <span className="text-cyan-400">{step.duration_ms} ms</span>
                      </div>
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed">
                      {step.summary}
                    </p>

                    {/* Expand inputs / outputs */}
                    {(step.inputs || step.outputs) && (
                      <div className="pt-2">
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
