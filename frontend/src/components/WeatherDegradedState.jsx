import React from 'react';
import {
  AlertTriangle,
  RotateCcw,
  ShieldAlert,
  Search,
  CheckCircle,
  MapPinOff,
  Clock,
  WifiOff,
} from 'lucide-react';

const ERROR_CONFIGS = {
  LOCATION_NOT_FOUND: {
    icon: <MapPinOff className="w-8 h-8 text-amber-400" />,
    badgeClass: 'bg-amber-950/60 text-amber-300 border-amber-800/60',
    title: 'Geocoding Resolution Failed',
    category: 'Location Not Found',
    guidance: 'The requested location could not be resolved against global geodetic databases. Please verify city spelling, specify the state or country, or try a major nearby metropolitan center.',
  },
  WEATHER_API_TIMEOUT: {
    icon: <Clock className="w-8 h-8 text-rose-400" />,
    badgeClass: 'bg-rose-950/60 text-rose-300 border-rose-800/60',
    title: 'Upstream Provider Timed Out',
    category: 'Network / Gateway Timeout (504)',
    guidance: 'The meteorological telemetry provider did not respond within the allocated time window after bounded retry attempts. The server has temporarily degraded this endpoint.',
  },
  WEATHER_API_ERROR: {
    icon: <WifiOff className="w-8 h-8 text-rose-400" />,
    badgeClass: 'bg-rose-950/60 text-rose-300 border-rose-800/60',
    title: 'Meteorological Service Degraded',
    category: 'Upstream Service Error (502)',
    guidance: 'The external weather model returned an upstream error. Live atmospheric readings are currently unreachable for this coordinate cluster.',
  },
  MALFORMED_RESPONSE: {
    icon: <ShieldAlert className="w-8 h-8 text-orange-400" />,
    badgeClass: 'bg-orange-950/60 text-orange-300 border-orange-800/60',
    title: 'Payload Validation Failed',
    category: 'Malformed Data Schema (422)',
    guidance: 'The raw telemetry payload returned by the weather service failed schema integrity checks. The payload was rejected to prevent corrupted data presentation.',
  },
};

export default function WeatherDegradedState({
  error,
  onRetry,
  onSelectSuggestion,
}) {
  if (!error) return null;

  const config = ERROR_CONFIGS[error.errorCode] || {
    icon: <AlertTriangle className="w-8 h-8 text-rose-400" />,
    badgeClass: 'bg-rose-950/60 text-rose-300 border-rose-800/60',
    title: 'Live Weather Unavailable',
    category: error.errorCode || 'System Error',
    guidance: error.message || 'An error occurred while communicating with the weather intelligence service.',
  };

  const SUGGESTED_LOCATIONS = ['Shimla', 'Bengaluru', 'London', 'Tokyo', 'San Francisco'];

  return (
    <div className="w-full rounded-2xl p-6 sm:p-8 bg-slate-900/90 border border-rose-500/30 shadow-2xl space-y-6 animate-fadeIn">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div className="flex items-start space-x-4">
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 shrink-0">
            {config.icon}
          </div>
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className={`text-[10px] font-mono uppercase tracking-wider font-bold px-2.5 py-0.5 rounded-full border ${config.badgeClass}`}>
                {error.errorCode || 'DEGRADED_STATE'}
              </span>
              <span className="text-xs font-semibold uppercase tracking-wider text-rose-400">
                Weather Data Unavailable
              </span>
            </div>
            <h3 className="text-xl font-bold text-white tracking-tight">
              {config.title}
            </h3>
            <p className="text-sm text-slate-300 max-w-xl">
              {error.message}
            </p>
          </div>
        </div>

        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold border border-slate-700 transition-all shrink-0"
          >
            <RotateCcw className="w-3.5 h-3.5 text-cyan-400" />
            <span>Retry Query</span>
          </button>
        )}
      </div>

      {/* Integrity Notice Banner */}
      <div className="p-4 rounded-xl bg-slate-950/60 border border-cyan-900/30 flex items-start space-x-3 text-xs leading-relaxed">
        <ShieldAlert className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <span className="font-semibold text-cyan-300">
            MausamAI Meteorological Integrity Policy
          </span>
          <p className="text-slate-400">
            MausamAI operates on strict empirical meteorological telemetry. When live upstream models cannot verify real conditions, we display an explicit degraded state rather than silently synthesizing, hallucinating, or caching fake weather numbers.
          </p>
        </div>
      </div>

      {/* Diagnostic Details Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
        <div className="p-3 rounded-lg bg-slate-950/40 border border-slate-800/80">
          <span className="text-slate-500 block mb-0.5 text-[11px]">Location Queried</span>
          <span className="font-mono font-medium text-slate-200 truncate block">
            {error.locationSearched || 'Unspecified'}
          </span>
        </div>

        <div className="p-3 rounded-lg bg-slate-950/40 border border-slate-800/80">
          <span className="text-slate-500 block mb-0.5 text-[11px]">Fault Category</span>
          <span className="font-mono font-medium text-amber-300 truncate block">
            {config.category}
          </span>
        </div>

        <div className="p-3 rounded-lg bg-slate-950/40 border border-slate-800/80">
          <span className="text-slate-500 block mb-0.5 text-[11px]">Bounded Retries Attempted</span>
          <span className="font-mono font-medium text-slate-200">
            {error.retriesAttempted} attempt(s)
          </span>
        </div>

        <div className="p-3 rounded-lg bg-slate-950/40 border border-slate-800/80">
          <span className="text-slate-500 block mb-0.5 text-[11px]">Failure Timestamp</span>
          <span className="font-mono font-medium text-slate-400 truncate block">
            {new Date(error.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })} UTC
          </span>
        </div>
      </div>

      {/* Suggested Locations */}
      {onSelectSuggestion && (
        <div className="pt-2 flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-400 flex items-center gap-1 font-medium">
            <Search className="w-3.5 h-3.5 text-cyan-400" /> Try a verified location:
          </span>
          {SUGGESTED_LOCATIONS.map((loc) => (
            <button
              key={loc}
              type="button"
              onClick={() => onSelectSuggestion(loc)}
              className="text-xs px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-cyan-950 hover:text-cyan-300 hover:border-cyan-700/60 text-slate-300 border border-slate-700/50 transition-colors"
            >
              {loc}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
