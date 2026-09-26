import React from 'react';
import {
  MapPin,
  Calendar,
  Search,
  Loader2,
  Sparkles,
  Compass,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  X,
} from 'lucide-react';

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
  isDetectingLocation,
  onRefreshLocation,
  liveCoords,
  onClearLiveCoords,
  locationWarning,
  onDismissWarning,
}) {
  return (
    <div className="w-full glass-panel rounded-2xl p-5 border border-slate-800 shadow-xl space-y-4">
      {/* Fallback / Permission warning notice */}
      {locationWarning && (
        <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-center justify-between text-xs text-amber-300 animate-fadeIn">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>{locationWarning}</span>
          </div>
          {onDismissWarning && (
            <button
              onClick={onDismissWarning}
              className="text-amber-400 hover:text-amber-200 p-1"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
        {/* Location input */}
        <div className="md:col-span-5 space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-cyan-400" /> Target Location
            </label>

            {/* Refresh / Auto-Detect Location Button */}
            <button
              type="button"
              onClick={onRefreshLocation}
              disabled={isDetectingLocation || isSearchingWeather || isAnalyzing}
              className={`text-[11px] font-medium flex items-center gap-1 px-2.5 py-0.5 rounded-lg border transition-all ${
                liveCoords
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/20'
                  : 'bg-cyan-500/10 border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/20'
              } disabled:opacity-50`}
              title="Detect or refresh current GPS coordinates via browser Geolocation API"
            >
              {isDetectingLocation ? (
                <>
                  <RefreshCw className="w-3 h-3 animate-spin text-cyan-400" />
                  <span>Locating GPS...</span>
                </>
              ) : liveCoords ? (
                <>
                  <RefreshCw className="w-3 h-3 text-emerald-400" />
                  <span>Refresh Location</span>
                </>
              ) : (
                <>
                  <Compass className="w-3 h-3 text-cyan-400" />
                  <span>Detect Live Location</span>
                </>
              )}
            </button>
          </div>

          <div className="relative">
            <input
              type="text"
              value={location}
              onChange={(e) => {
                setLocation(e.target.value);
                if (liveCoords && onClearLiveCoords) {
                  onClearLiveCoords();
                }
              }}
              placeholder="Detecting live GPS or enter city manually..."
              className="w-full bg-slate-900/80 border border-slate-700/80 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 rounded-xl px-4 py-2.5 text-slate-100 placeholder-slate-500 text-sm outline-none transition-all pr-10"
            />
            {liveCoords && (
              <span
                className="absolute right-3 top-1/2 -translate-y-1/2 flex h-2.5 w-2.5"
                title="Live GPS coordinates active"
              >
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
              </span>
            )}
          </div>

          {/* Active Live GPS Coordinate Badge or Popular Pills */}
          {liveCoords ? (
            <div className="flex items-center justify-between text-[11px] pt-1 px-1">
              <span className="text-emerald-400 flex items-center gap-1 font-mono">
                <CheckCircle className="w-3 h-3" />
                Live GPS: {liveCoords.latitude.toFixed(4)}°, {liveCoords.longitude.toFixed(4)}°
              </span>
              <button
                type="button"
                onClick={onClearLiveCoords}
                className="text-slate-400 hover:text-slate-200 underline text-[10px]"
              >
                Switch to manual city
              </button>
            </div>
          ) : (
            <div className="flex flex-wrap gap-1.5 pt-1">
              {POPULAR_LOCATIONS.map((loc) => (
                <button
                  key={loc}
                  type="button"
                  onClick={() => {
                    setLocation(loc);
                    if (liveCoords && onClearLiveCoords) onClearLiveCoords();
                  }}
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
          )}
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
