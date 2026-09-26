import React, { useState, useEffect } from 'react';
import { apiClient, WeatherApiError } from './api/client';
import Header from './components/Header';
import ChatQueryInput from './components/ChatQueryInput';
import LocationDateForm from './components/LocationDateForm';
import AnalysisProgress, { INITIAL_STAGES } from './components/AnalysisProgress';
import WeatherOverview from './components/WeatherOverview';
import WeatherDegradedState from './components/WeatherDegradedState';
import InsufficientDataState from './components/InsufficientDataState';
import RecommendationCard from './components/RecommendationCard';
import SavedPlans from './components/SavedPlans';
import NotificationCenter from './components/NotificationCenter';
import AgentExecutionTrace from './components/AgentExecutionTrace';
import { registerServiceWorker } from './utils/pushNotifications';
import { getCurrentCoordinates } from './utils/geolocation';
import { AlertCircle, Sparkles } from 'lucide-react';

export default function App() {
  const [backendOnline, setBackendOnline] = useState(false);
  const [query, setQuery] = useState('Can I plan an alpine day trek with clear visibility and moderate winds?');
  const [location, setLocation] = useState('Shimla');
  const [date, setDate] = useState(() => new Date().toISOString().split('T')[0]);

  // Live Location State
  const [liveCoords, setLiveCoords] = useState(null);
  const [isLiveLocation, setIsLiveLocation] = useState(false);
  const [isDetectingLocation, setIsDetectingLocation] = useState(false);
  const [locationWarning, setLocationWarning] = useState(null);

  // Loading flags
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSearchingWeather, setIsSearchingWeather] = useState(false);

  // Live Multi-Agent Streaming Progress state
  const [analysisStages, setAnalysisStages] = useState(() => {
    const init = {};
    INITIAL_STAGES.forEach((s) => {
      init[s.id] = { status: 'pending' };
    });
    return init;
  });
  const [liveMessage, setLiveMessage] = useState('');
  const [activeAgent, setActiveAgent] = useState('');
  const [reviewNotice, setReviewNotice] = useState(null);

  // Data states
  const [directWeather, setDirectWeather] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [insufficientDataResult, setInsufficientDataResult] = useState(null);
  const [weatherError, setWeatherError] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  // Smart Monitoring Storage & Scheduler State
  const [savedPlans, setSavedPlans] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [isSavedCurrent, setIsSavedCurrent] = useState(false);
  const [isCheckingPlan, setIsCheckingPlan] = useState({});
  const [isPollingAll, setIsPollingAll] = useState(false);
  const [monitoringStatus, setMonitoringStatus] = useState({ poll_interval_seconds: 60 });

  // Initial load: Request location permission automatically without requiring manual input
  useEffect(() => {
    registerServiceWorker();
    checkHealth();
    fetchPlans();
    fetchNotifications();
    fetchMonitoringStatus();
    handleDetectLiveLocation(true);
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

  const fetchMonitoringStatus = async () => {
    try {
      const data = await apiClient.getMonitoringStatus();
      setMonitoringStatus(data);
    } catch (e) {
      console.warn('Could not load monitoring status:', e);
    }
  };

  // Direct Live Weather Lookup (supports both coordinates and city name)
  const handleSearchWeather = async (targetLoc = location, targetDate = date, coords = liveCoords) => {
    const loc = targetLoc ? targetLoc.trim() : '';
    if (!loc && !coords) {
      setErrorMsg('Please specify a target location or enable GPS');
      return;
    }

    setIsSearchingWeather(true);
    setErrorMsg(null);
    setWeatherError(null);
    setInsufficientDataResult(null);

    try {
      const target = coords
        ? { latitude: coords.latitude, longitude: coords.longitude, location: loc }
        : loc;
      const data = await apiClient.getWeather(target, targetDate);
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
          locationSearched: loc || 'GPS Coordinates',
          retriesAttempted: 0,
          timestamp: new Date().toISOString(),
        });
      }
    } finally {
      setIsSearchingWeather(false);
    }
  };

  // Automatic Live Location Detection via browser Geolocation API & Reverse Geocoding
  const handleDetectLiveLocation = async (isInitial = false) => {
    setIsDetectingLocation(true);
    setLocationWarning(null);

    try {
      // 1. Detect browser GPS coordinates
      const coords = await getCurrentCoordinates();
      setLiveCoords(coords);
      setIsLiveLocation(true);

      // 2. Reverse geocode coordinates to human-readable city/region name
      let resolvedName = '';
      try {
        const geo = await apiClient.reverseGeocode(coords.latitude, coords.longitude);
        if (geo && geo.name) {
          resolvedName = geo.name;
          setLocation(resolvedName);
        }
      } catch (revErr) {
        console.warn('Reverse geocoding warning, proceeding with coordinates:', revErr);
        resolvedName = `Live Location (${coords.latitude.toFixed(2)}°, ${coords.longitude.toFixed(2)}°)`;
        setLocation(resolvedName);
      }

      // 3. Fetch real-time weather from Open-Meteo with coordinates
      await handleSearchWeather(resolvedName, date, coords);
    } catch (err) {
      console.warn('Live location detection error:', err);
      setLiveCoords(null);
      setIsLiveLocation(false);
      const msg = err.message || 'Location access unavailable. Defaulting to manual city search.';
      setLocationWarning(msg);

      if (isInitial) {
        // Fallback gracefully so dashboard displays immediately
        await handleSearchWeather('Shimla', date, null);
      }
    } finally {
      setIsDetectingLocation(false);
    }
  };

  // Full Multi-Agent Intelligence Pipeline via Real-Time Server-Sent Events (SSE)
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
    setInsufficientDataResult(null);
    setReviewNotice(null);
    setAnalysisResult(null);
    setIsAnalyzing(true);
    setIsSavedCurrent(false);

    // Reset stages to pending state
    const initialStages = {};
    INITIAL_STAGES.forEach((s) => {
      initialStages[s.id] = { status: 'pending' };
    });
    setAnalysisStages(initialStages);
    setLiveMessage(`Dispatching 5-agent pipeline for ${loc}...`);
    setActiveAgent('PlannerAgent');

    try {
      await apiClient.analyzeWeatherStream(
        {
          query,
          location: loc,
          target_date: date,
          latitude: liveCoords?.latitude,
          longitude: liveCoords?.longitude,
        },
        (event) => {
          if (event.type === 'start') {
            setLiveMessage(event.message || '5-agent pipeline initialized...');
          } else if (event.type === 'progress') {
            if (event.agent_name) {
              setActiveAgent(event.agent_name);
            }

            if (event.status === 'running') {
              setLiveMessage(event.message || `${event.agent_name} is running...`);
              setAnalysisStages((prev) => ({
                ...prev,
                [event.stage_id]: {
                  status: 'running',
                  action: event.action,
                  agent: event.agent_name,
                },
              }));
            } else if (event.status === 'completed') {
              setLiveMessage(event.summary || `${event.agent_name} completed.`);
              setAnalysisStages((prev) => ({
                ...prev,
                [event.stage_id]: {
                  status: 'completed',
                  action: event.action,
                  duration_ms: event.duration_ms,
                  summary: event.summary,
                  reasoning: event.reasoning,
                },
              }));

              // When DataAgent acquires verified telemetry, render WeatherOverview immediately
              if (event.weather) {
                setDirectWeather(event.weather);
                setWeatherError(null);
              }
            }
          } else if (event.type === 'review_loop') {
            setReviewNotice({
              iteration: event.iteration,
              message: event.message,
              correctionRequest: event.correction_request,
            });
            setLiveMessage(event.message);
          } else if (event.type === 'insufficient_data') {
            setInsufficientDataResult(event);
            setAnalysisStages((prev) => ({
              ...prev,
              critic: {
                status: 'failed',
                action: 'VALIDATE_RECOMMENDATION_AGAINST_SOURCE_DATA',
                summary: 'Critic halted pipeline: Insufficient empirical data',
              },
            }));
            setIsAnalyzing(false);
          } else if (event.type === 'complete') {
            setAnalysisResult(event.result);
            setDirectWeather(event.result.weather);
            setBackendOnline(true);
            setWeatherError(null);
            setIsAnalyzing(false);
            setActiveAgent('');
          } else if (event.type === 'error') {
            setIsAnalyzing(false);
            setActiveAgent('');
            setWeatherError({
              errorCode: event.error?.error_code || 'PIPELINE_ERROR',
              message: event.error?.message || 'Pipeline encountered an error.',
              detail: event.error?.detail || null,
              locationSearched: event.error?.location_searched || loc,
              retriesAttempted: event.error?.retries_attempted || 0,
              timestamp: event.error?.timestamp || new Date().toISOString(),
            });
          }
        }
      );
    } catch (err) {
      console.error('Multi-agent stream execution failed:', err);
      setIsAnalyzing(false);
      setActiveAgent('');
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
          errorCode: 'PIPELINE_ERROR',
          message: err.message || 'Failed to complete multi-agent analysis.',
          locationSearched: loc,
          retriesAttempted: 0,
          timestamp: new Date().toISOString(),
        });
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSelectSuggestion = (suggestedCity) => {
    setLocation(suggestedCity);
    handleSearchWeather(suggestedCity, date);
  };

  // Save Plan with Smart Monitoring
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
    setQuery(plan.query || `Outdoor plan for ${plan.action} in ${plan.location}`);
    handleSearchWeather(plan.location, plan.target_date);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Smart Monitoring Handlers
  const handleCheckPlan = async (planId) => {
    setIsCheckingPlan((prev) => ({ ...prev, [planId]: true }));
    try {
      const res = await apiClient.checkPlan(planId);
      if (res.plan) {
        setSavedPlans((prev) => prev.map((p) => (p.id === planId ? res.plan : p)));
      }
      if (res.notification_emitted) {
        await fetchNotifications();
      }
    } catch (err) {
      console.error('Plan check error:', err);
      setErrorMsg('Check failed: ' + err.message);
    } finally {
      setIsCheckingPlan((prev) => ({ ...prev, [planId]: false }));
    }
  };

  const handleSimulateChange = async (planId) => {
    const plan = savedPlans.find((p) => p.id === planId);
    if (!plan) return;

    setIsCheckingPlan((prev) => ({ ...prev, [planId]: true }));

    // Create a simulated significant weather change (approaching convective squall / thunderstorm)
    const simulatedWeather = {
      location: {
        name: plan.location,
        latitude: 31.1,
        longitude: 77.1,
        country: 'India',
        region: 'Himachal Pradesh',
      },
      observed_date: plan.target_date,
      temp_c: 11.5,
      feels_like_c: 7.0,
      humidity: 95,
      wind_kph: 38.0,
      wind_direction: 'NW',
      precipitation_prob: 85,
      precipitation_mm: 16.0,
      uv_index: 2.0,
      condition_text: 'Thunderstorm with Heavy Rain',
      source: 'simulated-change-test',
      forecast_days: [
        {
          date: plan.target_date,
          max_temp_c: 13.0,
          min_temp_c: 6.0,
          avg_temp_c: 9.5,
          condition: 'Thunderstorm',
          rain_probability: 85,
          uv_index: 2.0,
          wind_max_kph: 38.0,
        }
      ],
    };

    try {
      const res = await apiClient.checkPlan(planId, simulatedWeather, true);
      if (res.plan) {
        setSavedPlans((prev) => prev.map((p) => (p.id === planId ? res.plan : p)));
      }
      await fetchNotifications();
    } catch (err) {
      console.error('Simulation check failed:', err);
      setErrorMsg('Simulation failed: ' + err.message);
    } finally {
      setIsCheckingPlan((prev) => ({ ...prev, [planId]: false }));
    }
  };

  const handleTogglePlanStatus = async (planId, newStatus) => {
    try {
      const updated = await apiClient.updatePlanStatus(planId, newStatus);
      setSavedPlans((prev) => prev.map((p) => (p.id === planId ? updated : p)));
    } catch (err) {
      console.error('Update status failed:', err);
    }
  };

  const handleTriggerMonitoring = async () => {
    setIsPollingAll(true);
    try {
      await apiClient.triggerMonitoringCycle();
      await fetchPlans();
      await fetchNotifications();
    } catch (err) {
      console.error('Trigger monitoring failed:', err);
    } finally {
      setIsPollingAll(false);
    }
  };

  const handleUpdateInterval = async (intervalSec) => {
    try {
      await apiClient.updateMonitoringInterval(intervalSec);
      setMonitoringStatus((prev) => ({ ...prev, poll_interval_seconds: intervalSec }));
    } catch (err) {
      console.error('Update interval failed:', err);
    }
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
            <span>Autonomous Weather Decision Engine & Smart Monitor</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Weather Intelligence Dashboard
          </h1>
          <p className="text-sm text-slate-400 max-w-2xl leading-relaxed">
            Live atmospheric telemetry verified via Open-Meteo. Ask natural language questions about outdoor plans, and MausamAI’s 5-agent mesh evaluates physics, feasibility, comparative options, and risks with zero simulated numbers.
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
            onSearchOnly={() => handleSearchWeather(location, date, liveCoords)}
            isAnalyzing={isAnalyzing}
            isSearchingWeather={isSearchingWeather}
            isDetectingLocation={isDetectingLocation}
            onRefreshLocation={() => handleDetectLiveLocation(false)}
            liveCoords={liveCoords}
            onClearLiveCoords={() => {
              setLiveCoords(null);
              setIsLiveLocation(false);
            }}
            locationWarning={locationWarning}
            onDismissWarning={() => setLocationWarning(null)}
          />
        </div>

        {/* Real-time Multi-Agent Analysis Progress Panel */}
        <AnalysisProgress
          isAnalyzing={isAnalyzing}
          stages={analysisStages}
          liveMessage={liveMessage}
          activeAgent={activeAgent}
          reviewNotice={reviewNotice}
        />

        {/* Visible Unavailable / Degraded State when Weather Fails */}
        {weatherError && (
          <WeatherDegradedState
            error={weatherError}
            onRetry={() => handleSearchWeather(location, date, liveCoords)}
            onSelectSuggestion={handleSelectSuggestion}
          />
        )}

        {/* Insufficient Data State when Critic halts on missing empirical telemetry */}
        {!weatherError && insufficientDataResult && (
          <InsufficientDataState
            data={insufficientDataResult}
            onRetry={handleAnalyze}
            onAdjustDate={() => setDate(new Date().toISOString().split('T')[0])}
          />
        )}

        {/* Weather Overview (Displayed when weather data is valid and no error) */}
        {!weatherError && directWeather && (
          <WeatherOverview weather={directWeather} isLiveLocation={isLiveLocation} />
        )}

        {/* Analysis Results Display (Recommendation & Execution Trace) */}
        {!weatherError && !insufficientDataResult && analysisResult && (
          <div className="space-y-8 animate-fadeIn">
            <RecommendationCard
              recommendation={analysisResult.recommendation}
              query={analysisResult.query}
              location={analysisResult.location}
              targetDate={analysisResult.target_date}
              weather={directWeather}
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

        {/* Smart Monitoring & Active Saved Plans Dashboard */}
        <SavedPlans
          plans={savedPlans}
          onDeletePlan={handleDeletePlan}
          onLoadPlan={handleLoadPlan}
          onCheckPlan={handleCheckPlan}
          onSimulateChange={handleSimulateChange}
          onToggleStatus={handleTogglePlanStatus}
          onTriggerMonitoring={handleTriggerMonitoring}
          onUpdateInterval={handleUpdateInterval}
          monitoringStatus={monitoringStatus}
          isChecking={isCheckingPlan}
          isPollingAll={isPollingAll}
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
        onRefreshNotifications={fetchNotifications}
        onSelectPlan={(planId) => {
          const p = savedPlans.find((plan) => plan.id === planId);
          if (p) handleLoadPlan(p);
        }}
        savedPlans={savedPlans}
      />
    </div>
  );
}
