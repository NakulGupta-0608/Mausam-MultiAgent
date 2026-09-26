import React, { useState, useEffect } from 'react';
import { apiClient } from './api/client';
import Header from './components/Header';
import ChatQueryInput from './components/ChatQueryInput';
import LocationDateForm from './components/LocationDateForm';
import AnalysisProgress from './components/AnalysisProgress';
import WeatherOverview from './components/WeatherOverview';
import RecommendationCard from './components/RecommendationCard';
import SavedPlans from './components/SavedPlans';
import NotificationCenter from './components/NotificationCenter';
import AgentExecutionTrace from './components/AgentExecutionTrace';
import { AlertCircle, Compass, Zap, Shield, Sparkles } from 'lucide-react';

export default function App() {
  const [backendOnline, setBackendOnline] = useState(false);
  const [query, setQuery] = useState('Can I plan an alpine day trek with clear visibility and moderate winds?');
  const [location, setLocation] = useState('Shimla');
  const [date, setDate] = useState(() => new Date().toISOString().split('T')[0]);

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStage, setAnalysisStage] = useState(0);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  const [savedPlans, setSavedPlans] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [isSavedCurrent, setIsSavedCurrent] = useState(false);

  // Initial load
  useEffect(() => {
    checkHealth();
    fetchPlans();
    fetchNotifications();
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

  const handleAnalyze = async () => {
    if (!location.trim()) {
      setErrorMsg('Please specify a target location');
      return;
    }
    setErrorMsg(null);
    setIsAnalyzing(true);
    setIsSavedCurrent(false);
    setAnalysisStage(0);

    // Simulate multi-agent stage progress while awaiting backend response
    const stageTimer1 = setTimeout(() => setAnalysisStage(1), 400);
    const stageTimer2 = setTimeout(() => setAnalysisStage(2), 900);

    try {
      const result = await apiClient.analyzeWeather({
        query: query || 'Analyze general outdoor conditions',
        location,
        target_date: date,
      });

      setAnalysisResult(result);
      setBackendOnline(true);
    } catch (err) {
      console.error('Analysis execution failed:', err);
      setErrorMsg(err.message || 'Failed to complete multi-agent weather intelligence analysis.');
    } finally {
      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);
      setIsAnalyzing(false);
    }
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
        isAnalyzing={isAnalyzing}
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
            Ask natural language questions about outdoor plans, expeditions, or events. MausamAI’s multi-agent mesh evaluates atmospheric physics, risks, and feasibility in real time.
          </p>
        </div>

        {/* Error notification banner */}
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

        {/* Query & Location Input Controls */}
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
            isAnalyzing={isAnalyzing}
          />
        </div>

        {/* Multi-Agent Analysis Progress Panel */}
        <AnalysisProgress
          isAnalyzing={isAnalyzing}
          currentStageIndex={analysisStage}
        />

        {/* Analysis Results Display */}
        {analysisResult && (
          <div className="space-y-8 animate-fadeIn">
            {/* Weather Overview */}
            <WeatherOverview weather={analysisResult.weather} />

            {/* Recommendation & Feasibility Card */}
            <RecommendationCard
              recommendation={analysisResult.recommendation}
              query={analysisResult.query}
              location={analysisResult.location}
              targetDate={analysisResult.target_date}
              onSavePlan={handleSavePlan}
              isSaved={isSavedCurrent}
            />

            {/* Multi-Agent Trace Log */}
            <AgentExecutionTrace
              trace={analysisResult.trace}
              totalExecutionMs={analysisResult.total_execution_ms}
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
          <span>MausamAI Multi-Agent System • Dynamic Atmospheric Intelligence</span>
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
