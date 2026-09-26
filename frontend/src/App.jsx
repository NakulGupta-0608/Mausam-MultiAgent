import React, { useState, useEffect } from 'react';
import { apiClient, WeatherApiError } from './api/client';
import Header from './components/Header';
import ChatQueryInput from './components/ChatQueryInput';
import LocationDateForm from './components/LocationDateForm';
import AnalysisProgress from './components/AnalysisProgress';
import WeatherOverview from './components/WeatherOverview';
import WeatherDegradedState from './components/WeatherDegradedState';
import RecommendationCard from './components/RecommendationCard';
import SavedPlans from './components/SavedPlans';
import NotificationCenter from './components/NotificationCenter';
import AgentExecutionTrace from './components/AgentExecutionTrace';
import { AlertCircle, Sparkles } from 'lucide-react';

export default function App() {
  const [backendOnline, setBackendOnline] = useState(false);
  const [query, setQuery] = useState('Can I plan an alpine day trek with clear visibility and moderate winds?');
  const [location, setLocation] = useState('Shimla');
  const [date, setDate] = useState(() => new Date().toISOString().split('T')[0]);

  // Loading flags
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSearchingWeather, setIsSearchingWeather] = useState(false);
  const [analysisStage, setAnalysisStage] = useState(0);

  // Data states
  const [directWeather, setDirectWeather] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [weatherError, setWeatherError] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  // Storage
  const [savedPlans, setSavedPlans] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [isSavedCurrent, setIsSavedCurrent] = useState(false);

  // Initial load
  useEffect(() => {
    checkHealth();
    fetchPlans();
    fetchNotifications();
    // Load initial real weather for default location
    handleSearchWeather('Shimla', date);
  }, []);

  const checkHealth = async () => {
    try {
      await apiClient.getHealth();
      setBackendOnline(true);
    } catch (e) {
      setBackendOnline(false);
    }
  };

  const fetchPlans = async () => {
    try {
      const data = await apiClient.getSavedPlans();
      setSavedPlans(data);
    } catch (e) {
      console.warn('Could not load plans:', e);
    }
  };

  const fetchNotifications = async () => {
    try {
      const data = await apiClient.getNotifications();
      setNotifications(data);
    } catch (e) {
      console.warn('Could not load notifications:', e);
    }
  };

  // Direct Live Weather Lookup
  const handleSearchWeather = async (targetLoc = location, targetDate = date) => {
    const loc = targetLoc.trim();
    if (!loc) {
      setErrorMsg('Please specify a target location');
      return;
    }

    setIsSearchingWeather(true);
    setErrorMsg(null);
    setWeatherError(null);

    try {
      const data = await apiClient.getWeather(loc, targetDate);
      setDirectWeather(data);
      setBackendOnline(true);
      setWeatherError(null);
    } catch (err) {
      console.error('Weather lookup failed:', err);
      setDirectWeather(null);
      setAnalysisResult(null);

      if (err instanceof WeatherApiError) {
        setWeatherError({
          errorCode: err.errorCode,
          message: err.message,
          detail: err.detail,
          locationSearched: err.locationSearched || loc,
          retriesAttempted: err.retriesAttempted,
          timestamp: err.timestamp,
        });
      } else {
        setWeatherError({
          errorCode: 'WEATHER_API_ERROR',
          message: err.message || 'Unable to connect to meteorological service.',
          locationSearched: loc,
          retriesAttempted: 0,
          timestamp: new Date().toISOString(),
        });
      }
    } finally {
      setIsSearchingWeather(false);
    }
  };

  // Full Multi-Agent Intelligence Pipeline
  const handleAnalyze = async () => {
    const loc = location.trim();
    if (!loc) {
      setErrorMsg('Please specify a target location');
      return;
    }
    if (!query.trim()) {
      setErrorMsg('Please enter an activity or question to analyze');
      return;
    }

    setErrorMsg(null);
    setWeatherError(null);
    setIsAnalyzing(true);
    setIsSavedCurrent(false);
    setAnalysisStage(0);

    const stageTimer1 = setTimeout(() => setAnalysisStage(1), 400);
    const stageTimer2 = setTimeout(() => setAnalysisStage(2), 900);

    try {
      const result = await apiClient.analyzeWeather({
        query,
        location: loc,
        target_date: date,
      });

      setAnalysisResult(result);
      setDirectWeather(result.weather);
      setBackendOnline(true);
      setWeatherError(null);
    } catch (err) {
      console.error('Analysis execution failed:', err);
      setAnalysisResult(null);
      setDirectWeather(null);

      if (err instanceof WeatherApiError) {
        setWeatherError({
          errorCode: err.errorCode,
          message: err.message,
          detail: err.detail,
          locationSearched: err.locationSearched || loc,
          retriesAttempted: err.retriesAttempted,
          timestamp: err.timestamp,
        });
      } else {
        setWeatherError({
          errorCode: 'PIPELINE_ERROR',
          message: err.message || 'Failed to complete multi-agent analysis.',
          locationSearched: loc,
          retriesAttempted: 0,
          timestamp: new Date().toISOString(),
        });
      }
    } finally {
      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);
      setIsAnalyzing(false);
    }
  };

  const handleSelectSuggestion = (suggestedCity) => {
    setLocation(suggestedCity);
    handleSearchWeather(suggestedCity, date);
  };

  const handleSavePlan = async (planData) => {
    try {
      const saved = await apiClient.savePlan(planData);
      setSavedPlans((prev) => [saved, ...prev.filter((p) => p.id !== saved.id)]);
      setIsSavedCurrent(true);
    } catch (err) {
      console.error('Save plan failed:', err);
      setErrorMsg('Failed to save plan: ' + err.message);
    }
  };

  const handleDeletePlan = async (planId) => {
    try {
      await apiClient.deletePlan(planId);
      setSavedPlans((prev) => prev.filter((p) => p.id !== planId));
    } catch (err) {
      console.error('Delete plan failed:', err);
    }
  };

  const handleLoadPlan = (plan) => {
    setLocation(plan.location);
    setDate(plan.target_date);
    setQuery(plan.query);
    handleSearchWeather(plan.location, plan.target_date);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleMarkNotifRead = async (notifId) => {
    try {
      await apiClient.markNotificationRead(notifId);
      setNotifications((prev) =>
        prev.map((n) => (n.id === notifId ? { ...n, read: true } : n))
      );
    } catch (err) {
      console.error(err);
    }
  };

  const handleMarkAllNotifRead = async () => {
    try {
      await apiClient.markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    } catch (err) {
      console.error(err);
    }
  };

  const unreadNotifCount = notifications.filter((n) => !n.read).length;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-white">
      {/* Header */}
      <Header
        backendOnline={backendOnline}
        unreadCount={unreadNotifCount}
        onToggleNotifications={() => setIsNotificationsOpen(true)}
        isAnalyzing={isAnalyzing || isSearchingWeather}
        onRefreshHealth={checkHealth}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Hero Section */}
        <div className="space-y-2">
          <div className="flex items-center space-x-2 text-cyan-400 text-xs font-semibold tracking-wider uppercase">
            <Sparkles className="w-4 h-4" />
            <span>Autonomous Weather Decision Engine</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Weather Intelligence Dashboard
          </h1>
          <p className="text-sm text-slate-400 max-w-2xl">
            Live atmospheric telemetry verified via Open-Meteo. Ask natural language questions about outdoor plans, and MausamAI’s multi-agent mesh evaluates physics, feasibility, and risks with zero simulated numbers.
          </p>
        </div>

        {/* Global Error Notice (Non-weather validation) */}
        {errorMsg && (
          <div className="p-4 rounded-xl bg-rose-950/50 border border-rose-500/40 text-rose-200 text-sm flex items-center justify-between animate-fadeIn">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{errorMsg}</span>
            </div>
            <button
              onClick={() => setErrorMsg(null)}
              className="text-xs text-rose-400 hover:text-white font-medium ml-4"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Query & Location Controls */}
        <div className="space-y-4">
          <ChatQueryInput
            query={query}
            setQuery={setQuery}
            onAnalyze={handleAnalyze}
            isAnalyzing={isAnalyzing}
          />

          <LocationDateForm
            location={location}
            setLocation={setLocation}
            date={date}
            setDate={setDate}
            onAnalyze={handleAnalyze}
            onSearchOnly={() => handleSearchWeather(location, date)}
            isAnalyzing={isAnalyzing}
            isSearchingWeather={isSearchingWeather}
          />
        </div>

        {/* Multi-Agent Analysis Progress Panel */}
        <AnalysisProgress
          isAnalyzing={isAnalyzing}
          currentStageIndex={analysisStage}
        />

        {/* Visible Unavailable / Degraded State when Weather Fails */}
        {weatherError && (
          <WeatherDegradedState
            error={weatherError}
            onRetry={() => handleSearchWeather(location, date)}
            onSelectSuggestion={handleSelectSuggestion}
          />
        )}

        {/* Weather Overview (Displayed when weather data is valid and no error) */}
        {!weatherError && directWeather && (
          <WeatherOverview weather={directWeather} />
        )}

        {/* Analysis Results Display (Recommendation & Execution Trace) */}
        {!weatherError && analysisResult && (
          <div className="space-y-8 animate-fadeIn">
            <RecommendationCard
              recommendation={analysisResult.recommendation}
              query={analysisResult.query}
              location={analysisResult.location}
              targetDate={analysisResult.target_date}
              onSavePlan={handleSavePlan}
              isSaved={isSavedCurrent}
            />

            <AgentExecutionTrace
              trace={analysisResult.trace}
              totalExecutionMs={analysisResult.total_execution_ms}
              stoppingCondition={analysisResult.stopping_condition}
            />
          </div>
        )}

        {/* Saved Plans Section */}
        <SavedPlans
          plans={savedPlans}
          onDeletePlan={handleDeletePlan}
          onLoadPlan={handleLoadPlan}
        />
      </main>

      {/* Footer */}
      <footer className="w-full border-t border-slate-900 bg-slate-950 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>MausamAI Multi-Agent System • Verified Meteorological Telemetry</span>
          <span className="text-slate-400">
            Powered by FastAPI & React + Vite + Tailwind CSS
          </span>
        </div>
      </footer>

      {/* Notification Center Slide-over */}
      <NotificationCenter
        isOpen={isNotificationsOpen}
        onClose={() => setIsNotificationsOpen(false)}
        notifications={notifications}
        onMarkRead={handleMarkNotifRead}
        onMarkAllRead={handleMarkAllNotifRead}
      />
    </div>
  );
}
