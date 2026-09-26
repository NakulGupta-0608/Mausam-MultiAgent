import React from 'react';
import {
  Sun,
  CloudRain,
  Wind,
  Droplets,
  Eye,
  ShieldCheck,
  Calendar,
  Compass,
  Thermometer,
  Cloud,
  CheckCircle2,
} from 'lucide-react';

export default function WeatherOverview({ weather, isLiveLocation = false }) {
  if (!weather) return null;

  const loc = weather.location;

  return (
    <div className="w-full glass-panel rounded-2xl p-6 border border-slate-800 shadow-xl space-y-6">
      {/* Header section with location & big temp */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-2xl font-bold text-white tracking-tight">
              {loc?.name || 'Target Location'}
            </h2>
            {loc?.country && (
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300">
                {loc.region ? `${loc.region}, ` : ''}{loc.country}
              </span>
            )}
            {isLiveLocation && (
              <span className="inline-flex items-center gap-1 text-[11px] font-medium px-2.5 py-0.5 rounded-full bg-cyan-950/60 text-cyan-300 border border-cyan-800/50">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping mr-0.5" />
                Live GPS Location
              </span>
            )}
            <span className="inline-flex items-center gap-1 text-[11px] font-medium px-2.5 py-0.5 rounded-full bg-emerald-950/60 text-emerald-400 border border-emerald-800/50">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              Verified Live Telemetry
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-400 mt-2">
            <span>Observed Date: <strong>{weather.observed_date}</strong></span>
            <span>•</span>
            <span>Coordinates: <strong>{loc?.latitude}°, {loc?.longitude}°</strong></span>
            <span>•</span>
            <span>Timezone: <strong>{loc?.timezone || 'UTC'}</strong></span>
            <span>•</span>
            <span className="text-cyan-400 font-mono">Provider: {weather.source}</span>
          </div>
        </div>

        <div className="flex items-baseline space-x-3 bg-slate-900/60 px-4 py-2.5 rounded-xl border border-slate-800 shrink-0">
          <div className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-cyan-300 to-blue-400 bg-clip-text text-transparent">
            {weather.temp_c}°C
          </div>
          <div className="text-sm text-slate-400">
            <span className="font-medium text-slate-200 block">{weather.condition_text}</span>
            <span>Feels like {weather.feels_like_c}°C</span>
          </div>
        </div>
      </div>

      {/* Atmospheric Telemetry Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800/80 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Humidity</span>
            <Droplets className="w-3.5 h-3.5 text-blue-400" />
          </div>
          <div className="text-lg font-bold text-white">{weather.humidity}%</div>
          <div className="text-[10px] text-slate-500">Relative moisture</div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800/80 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Wind Speed</span>
            <Wind className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div className="text-lg font-bold text-white">{weather.wind_kph} <span className="text-xs font-normal text-slate-400">km/h</span></div>
          <div className="text-[10px] text-slate-500">From {weather.wind_direction}</div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800/80 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Rain Risk</span>
            <CloudRain className="w-3.5 h-3.5 text-indigo-400" />
          </div>
          <div className="text-lg font-bold text-white">{weather.precipitation_prob}%</div>
          <div className="text-[10px] text-slate-500">{weather.precipitation_mm}mm volume</div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800/80 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>UV Index</span>
            <Sun className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-lg font-bold text-white">{weather.uv_index}</div>
          <div className="text-[10px] text-slate-500">
            {weather.uv_index > 7 ? 'Very High' : weather.uv_index > 5 ? 'Moderate' : 'Low'}
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800/80 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Air Quality</span>
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="text-lg font-bold text-white">{weather.air_quality_index} <span className="text-xs font-normal text-slate-400">AQI</span></div>
          <div className="text-[10px] text-slate-500">Baseline indicator</div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800/80 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Visibility</span>
            <Eye className="w-3.5 h-3.5 text-purple-400" />
          </div>
          <div className="text-lg font-bold text-white">{weather.visibility_km} <span className="text-xs font-normal text-slate-400">km</span></div>
          <div className="text-[10px] text-slate-500">Visual horizon</div>
        </div>
      </div>

      {/* 5-Day Forecast Row */}
      {weather.forecast_days && weather.forecast_days.length > 0 && (
        <div className="pt-2">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-cyan-400" /> 5-Day Real Forecast Outlook
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {weather.forecast_days.map((day, idx) => (
              <div
                key={day.date}
                className="p-3 rounded-xl bg-slate-900/50 border border-slate-800 hover:border-slate-700/80 transition-all text-center flex flex-col items-center justify-between"
              >
                <div className="text-xs font-medium text-slate-300">
                  {idx === 0 ? 'Today' : day.date.slice(5)}
                </div>
                <div className="my-2">
                  {day.rain_probability > 40 ? (
                    <CloudRain className="w-6 h-6 text-indigo-400 mx-auto" />
                  ) : day.condition.toLowerCase().includes('clear') || day.condition.toLowerCase().includes('sun') ? (
                    <Sun className="w-6 h-6 text-amber-400 mx-auto" />
                  ) : (
                    <Cloud className="w-6 h-6 text-slate-300 mx-auto" />
                  )}
                </div>
                <div className="text-xs font-bold text-white">
                  {day.max_temp_c}° / <span className="text-slate-400 font-normal">{day.min_temp_c}°</span>
                </div>
                <div className="text-[11px] text-slate-400 mt-1 truncate max-w-full">
                  {day.condition}
                </div>
                <div className="text-[10px] text-cyan-400 mt-1 font-medium">
                  {day.rain_probability}% rain
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
