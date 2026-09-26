import React from 'react';
import { Sparkles, ArrowRight, Compass } from 'lucide-react';

const SUGGESTIONS = [
  { label: 'Alpine Trek & Day Hike', query: 'Can I go on an alpine day trek? Need packing and weather advice.' },
  { label: 'Outdoor Garden Wedding', query: 'Planning an open-air evening reception. Will rain or wind disrupt it?' },
  { label: '50km Morning Cycle', query: 'Feasibility for an early morning road cycling training loop.' },
  { label: 'Photography & Sunset', query: 'Optimal photography window for golden hour and clear visibility.' },
];

export default function ChatQueryInput({ query, setQuery, onAnalyze, isAnalyzing }) {
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onAnalyze();
    }
  };

  return (
    <div className="w-full glass-panel rounded-2xl p-5 border border-slate-800 shadow-xl relative overflow-hidden">
      {/* Decorative glow */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="flex items-center space-x-2 mb-3 text-cyan-400">
        <Sparkles className="w-4 h-4" />
        <span className="text-xs font-semibold uppercase tracking-wider">
          Natural Language Activity & Decision Query
        </span>
      </div>

      <div className="relative">
        <textarea
          rows={2}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything (e.g. 'Can I go hiking tomorrow morning? What should I carry?', 'Is it safe for cycling?')"
          className="w-full bg-slate-900/80 border border-slate-700/80 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 rounded-xl px-4 py-3 text-slate-100 placeholder-slate-500 text-sm md:text-base outline-none resize-none transition-all"
        />
      </div>

      {/* Suggested queries */}
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className="text-xs text-slate-500 flex items-center gap-1">
          <Compass className="w-3 h-3" /> Quick Prompts:
        </span>
        {SUGGESTIONS.map((s, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => setQuery(s.query)}
            className="text-xs px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-800 hover:text-cyan-300 text-slate-400 border border-slate-700/50 transition-colors"
          >
            {s.label}
          </button>
        ))}
      </div>
    </div>
  );
}
