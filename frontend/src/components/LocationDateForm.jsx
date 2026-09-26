import React from 'react';
import { MapPin, Calendar, Search, Loader2, Sparkles } from 'lucide-react';

const POPULAR_LOCATIONS = ['Shimla', 'Bengaluru', 'New Delhi', 'London', 'San Francisco', 'Tokyo'];

export default function LocationDateForm({
  location,
  setLocation,
  date,
  setDate,
  onAnalyze,
  onSearchOnly,
  isAnalyzing,
  isSearchingWeather,
}) {
  return (
    <div className="w-full glass-panel rounded-2xl p-5 border border-slate-800 shadow-xl space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
        {/* Location input */}
        <div className="md:col-span-5 space-y-1.5">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <MapPin className="w-3.5 h-3.5 text-cyan-400" /> Target Location
          </label>
          <div className="relative">
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Enter city (e.g. Shimla, Bengaluru, London...)"
              className="w-full bg-slate-900/80 border border-slate-700/80 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 rounded-xl px-4 py-2.5 text-slate-100 placeholder-slate-500 text-sm outline-none transition-all"
            />
          </div>
          {/* Quick location pills */}
          <div className="flex flex-wrap gap-1.5 pt-1">
            {POPULAR_LOCATIONS.map((loc) => (
              <button
                key={loc}
                type="button"
                onClick={() => setLocation(loc)}
                className={`text-[11px] px-2 py-0.5 rounded-md border transition-colors ${
                  location.toLowerCase() === loc.toLowerCase()
                    ? 'bg-cyan-500/20 border-cyan-500/60 text-cyan-300'
                    : 'bg-slate-850 hover:bg-slate-800 border-slate-700/60 text-slate-400 hover:text-slate-200'
                }`}
              >
                {loc}
              </button>
            ))}
          </div>
        </div>

        {/* Date input */}
        <div className="md:col-span-3 space-y-1.5">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-cyan-400" /> Target Date
          </label>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="w-full bg-slate-900/80 border border-slate-700/80 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 rounded-xl px-4 py-2.5 text-slate-100 text-sm outline-none transition-all"
          />
        </div>

        {/* Action Buttons */}
        <div className="md:col-span-4 grid grid-cols-2 gap-2">
          {/* Direct Weather Lookup Button */}
          <button
            type="button"
            onClick={onSearchOnly}
            disabled={isSearchingWeather || isAnalyzing || !location.trim()}
            className="h-11 flex items-center justify-center space-x-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 active:scale-[0.99] text-slate-200 font-medium text-xs border border-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            title="Fetch real meteorological forecast without full agent mesh"
          >
            {isSearchingWeather ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin text-cyan-400" />
                <span>Fetching...</span>
              </>
            ) : (
              <>
                <Search className="w-3.5 h-3.5 text-cyan-400" />
                <span>Live Weather</span>
              </>
            )}
          </button>

          {/* Full Multi-Agent Analyze Button */}
          <button
            type="button"
            onClick={onAnalyze}
            disabled={isAnalyzing || isSearchingWeather || !location.trim()}
            className="h-11 flex items-center justify-center space-x-1.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 active:scale-[0.99] text-white font-semibold text-xs shadow-lg shadow-cyan-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin text-white" />
                <span>Agents Active...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5 text-cyan-100" />
                <span>Analyze Plan</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
