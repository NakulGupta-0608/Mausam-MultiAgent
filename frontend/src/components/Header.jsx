import React from 'react';
import { CloudLightning, Bell, Activity, Sparkles, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';

export default function Header({
  backendOnline,
  unreadCount,
  onToggleNotifications,
  isAnalyzing,
  onRefreshHealth,
}) {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800 bg-slate-950/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 shadow-lg shadow-cyan-500/20 text-white font-bold">
            <CloudLightning className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-100 to-cyan-300 bg-clip-text text-transparent">
                MausamAI
              </span>
              <span className="text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded-full bg-cyan-950/80 text-cyan-400 border border-cyan-800/60">
                Multi-Agent v0.1
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              Autonomous Meteorological Intelligence & Decision Engine
            </p>
          </div>
        </div>

        {/* Right side controls */}
        <div className="flex items-center space-x-3">
          {/* Health Status Indicator */}
          <button
            onClick={onRefreshHealth}
            title="Click to re-check backend connection"
            className="flex items-center space-x-2 px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors bg-slate-900/60 hover:bg-slate-900 border-slate-800 text-slate-300"
          >
            <span className="relative flex h-2 w-2">
              {backendOnline ? (
                <>
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </>
              ) : (
                <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
              )}
            </span>
            <span className="hidden sm:inline">
              Backend: {backendOnline ? 'Online (FastAPI)' : 'Disconnected'}
            </span>
          </button>

          {/* Active Agents Badge */}
          <div className="hidden md:flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900/50 border border-slate-800 text-xs text-slate-300">
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
            <span>5 Agents Mesh</span>
          </div>

          {/* Notifications Toggle */}
          <button
            onClick={onToggleNotifications}
            className="relative p-2 rounded-lg bg-slate-900/70 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white transition-colors"
            title="Notifications & Advisories"
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-cyan-500 text-[10px] font-bold text-white shadow-sm shadow-cyan-500/50 animate-bounce">
                {unreadCount}
              </span>
            )}
          </button>
        </div>
      </div>
    </header>
  );
}
