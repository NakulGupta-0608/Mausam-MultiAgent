import React, { useState, useEffect } from 'react';
import {
  Bell,
  X,
  CheckCheck,
  AlertTriangle,
  AlertCircle,
  Info,
  ShieldAlert,
  Sparkles,
  Sliders,
  Send,
  ExternalLink,
  ArrowRight,
  Check,
  RefreshCw,
  Smartphone,
  Trash2,
} from 'lucide-react';
import { apiClient } from '../api/client';
import {
  isPushNotificationSupported,
  getNotificationPermissionState,
  subscribeToPush,
  unsubscribeFromPush,
} from '../utils/pushNotifications';

const SEVERITY_ICONS = {
  warning: <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />,
  danger: <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />,
  info: <Info className="w-4 h-4 text-cyan-400 shrink-0" />,
  success: <CheckCheck className="w-4 h-4 text-emerald-400 shrink-0" />,
};

const SEVERITY_BADGES = {
  warning: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  danger: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  info: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  success: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
};

const PRESET_SIMULATIONS = [
  {
    name: 'Severe Rain Influx',
    metric: 'Precipitation Probability',
    previous: 'Precip: 10% (0.0mm)',
    newVal: 'Precip: 85% (18.4mm)',
    reason: 'Rapid monsoon cloudburst front approaching within 3 hours',
    severity: 'danger',
    criticVerdict: 'APPROVE',
  },
  {
    name: 'Gale Wind Surge',
    metric: 'Wind Speed Gusts',
    previous: 'Wind: 14 km/h (Moderate)',
    newVal: 'Wind: 52 km/h (High Risk)',
    reason: 'Ridge winds exceeding safety threshold of 15 km/h for exposed trails',
    severity: 'warning',
    criticVerdict: 'APPROVE',
  },
  {
    name: 'Critic Rejection Test',
    metric: 'Temperature Drop',
    previous: 'Temp: 18°C',
    newVal: 'Temp: -4°C',
    reason: 'Unverified sensor anomaly rejected by Critic validation guardrail',
    severity: 'danger',
    criticVerdict: 'REJECT',
  },
];

export default function NotificationCenter({
  isOpen,
  onClose,
  notifications,
  onMarkRead,
  onMarkAllRead,
  onRefreshNotifications,
  onSelectPlan,
  savedPlans = [],
}) {
  const [activeTab, setActiveTab] = useState('notifications'); // 'notifications' | 'preferences' | 'simulator'
  const [unreadOnly, setUnreadOnly] = useState(false);

  // Push notification permission state
  const [pushSupported, setPushSupported] = useState(false);
  const [permissionState, setPermissionState] = useState('default');
  const [isPushSubscribed, setIsPushSubscribed] = useState(false);
  const [isPushLoading, setIsPushLoading] = useState(false);
  const [pushStatusMessage, setPushStatusMessage] = useState('');

  // User Preferences
  const [preferences, setPreferences] = useState({
    in_app_enabled: true,
    browser_push_enabled: true,
    min_severity: 'info',
    notify_on_weather_change: true,
    notify_on_verdict_change: true,
  });
  const [isSavingPrefs, setIsSavingPrefs] = useState(false);
  const [prefSaveMsg, setPrefSaveMsg] = useState('');

  // Dev Simulator State
  const [simPlanId, setSimPlanId] = useState(savedPlans[0]?.id || '');
  const [simMetric, setSimMetric] = useState(PRESET_SIMULATIONS[0].metric);
  const [simPrevious, setSimPrevious] = useState(PRESET_SIMULATIONS[0].previous);
  const [simNew, setSimNew] = useState(PRESET_SIMULATIONS[0].newVal);
  const [simReason, setSimReason] = useState(PRESET_SIMULATIONS[0].reason);
  const [simSeverity, setSimSeverity] = useState(PRESET_SIMULATIONS[0].severity);
  const [simCriticVerdict, setSimCriticVerdict] = useState('APPROVE');
  const [simSendPush, setSimSendPush] = useState(true);
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationResult, setSimulationResult] = useState(null);

  useEffect(() => {
    if (isOpen) {
      checkPushState();
      loadPreferences();
    }
  }, [isOpen]);

  useEffect(() => {
    if (savedPlans.length > 0 && !simPlanId) {
      setSimPlanId(savedPlans[0].id);
    }
  }, [savedPlans]);

  const checkPushState = () => {
    const supported = isPushNotificationSupported();
    setPushSupported(supported);
    if (supported) {
      const state = getNotificationPermissionState();
      setPermissionState(state);
      setIsPushSubscribed(state === 'granted');
    }
  };

  const loadPreferences = async () => {
    try {
      const prefs = await apiClient.getNotificationPreferences();
      if (prefs) setPreferences(prefs);
    } catch (e) {
      console.warn('Could not load preferences:', e);
    }
  };

  const handleTogglePush = async () => {
    setIsPushLoading(true);
    setPushStatusMessage('');
    try {
      if (isPushSubscribed) {
        // Unsubscribe
        const endpoint = await unsubscribeFromPush();
        if (endpoint) {
          await apiClient.unsubscribePush(endpoint);
        }
        setIsPushSubscribed(false);
        setPermissionState(getNotificationPermissionState());
        setPushStatusMessage('Browser push notifications disabled.');
      } else {
        // Subscribe
        const { public_key } = await apiClient.getVapidPublicKey();
        const subscriptionPayload = await subscribeToPush(public_key);
        await apiClient.subscribePush(subscriptionPayload);
        setIsPushSubscribed(true);
        setPermissionState('granted');
        setPushStatusMessage('Browser push notifications active! You will receive live alerts.');
      }
    } catch (err) {
      console.error('Push subscription error:', err);
      setPushStatusMessage(err.message || 'Failed to update push subscription.');
    } finally {
      setIsPushLoading(false);
    }
  };

  const handleSavePreferences = async (updated) => {
    const nextPrefs = { ...preferences, ...updated };
    setPreferences(nextPrefs);
    setIsSavingPrefs(true);
    try {
      await apiClient.updateNotificationPreferences(nextPrefs);
      setPrefSaveMsg('Preferences saved');
      setTimeout(() => setPrefSaveMsg(''), 2500);
    } catch (e) {
      console.error('Failed to save preferences:', e);
      setPrefSaveMsg('Error saving preferences');
    } finally {
      setIsSavingPrefs(false);
    }
  };

  const handleApplyPreset = (preset) => {
    setSimMetric(preset.metric);
    setSimPrevious(preset.previous);
    setSimNew(preset.newVal);
    setSimReason(preset.reason);
    setSimSeverity(preset.severity);
    setSimCriticVerdict(preset.criticVerdict);
  };

  const handleRunSimulation = async () => {
    setIsSimulating(true);
    setSimulationResult(null);
    try {
      const res = await apiClient.simulateNotification({
        plan_id: simPlanId || undefined,
        metric: simMetric,
        previous_value: simPrevious,
        new_value: simNew,
        reason: simReason,
        severity: simSeverity,
        critic_verdict: simCriticVerdict,
        send_push: simSendPush,
      });
      setSimulationResult(res);
      if (onRefreshNotifications) {
        await onRefreshNotifications();
      }
    } catch (err) {
      setSimulationResult({
        status: 'error',
        message: err.message || 'Simulation execution failed',
      });
    } finally {
      setIsSimulating(false);
    }
  };

  const handleClearAll = async () => {
    try {
      await apiClient.clearNotifications();
      if (onRefreshNotifications) {
        await onRefreshNotifications();
      }
    } catch (err) {
      console.error('Failed to clear notifications:', err);
    }
  };

  if (!isOpen) return null;

  const filteredNotifications = notifications.filter((n) => {
    if (unreadOnly && n.read) return false;
    return true;
  });

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-fadeIn">
      {/* Click outside backdrop */}
      <div className="flex-1" onClick={onClose} />

      <div className="w-full max-w-lg bg-slate-900 border-l border-slate-800 h-full flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/80">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-cyan-500/10 border border-cyan-500/20 rounded-lg text-cyan-400">
              <Bell className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-white text-base leading-tight">Notification Center</h3>
              <p className="text-xs text-slate-400">Review-Gated & Deduplicated Weather Alerts</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Browser Push Permission Banner */}
        <div className="px-4 py-2.5 bg-slate-950/40 border-b border-slate-800 flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2">
            <Smartphone className="w-4 h-4 text-slate-400" />
            <span className="text-slate-300">Browser Push:</span>
            {permissionState === 'granted' ? (
              <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <Check className="w-3 h-3 mr-1" /> Active
              </span>
            ) : permissionState === 'denied' ? (
              <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
                Blocked
              </span>
            ) : (
              <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
                Not Enabled
              </span>
            )}
          </div>
          {pushSupported && (
            <button
              onClick={handleTogglePush}
              disabled={isPushLoading || permissionState === 'denied'}
              className="text-xs px-2.5 py-1 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 rounded-md font-medium transition-all disabled:opacity-50"
            >
              {isPushLoading
                ? 'Connecting...'
                : isPushSubscribed
                ? 'Disable Push'
                : 'Enable Push'}
            </button>
          )}
        </div>

        {pushStatusMessage && (
          <div className="px-4 py-1.5 bg-cyan-950/40 border-b border-cyan-800/40 text-[11px] text-cyan-300 flex items-center justify-between">
            <span>{pushStatusMessage}</span>
            <button onClick={() => setPushStatusMessage('')} className="text-cyan-400 hover:text-cyan-200">
              <X className="w-3 h-3" />
            </button>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-800 bg-slate-950/50 text-xs font-medium">
          <button
            onClick={() => setActiveTab('notifications')}
            className={`flex-1 py-2.5 text-center transition-all border-b-2 flex items-center justify-center gap-1.5 ${
              activeTab === 'notifications'
                ? 'border-cyan-500 text-cyan-400 bg-cyan-500/5'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Bell className="w-3.5 h-3.5" />
            Advisories
            {unreadCount > 0 && (
              <span className="px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-cyan-500 text-slate-950">
                {unreadCount}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('preferences')}
            className={`flex-1 py-2.5 text-center transition-all border-b-2 flex items-center justify-center gap-1.5 ${
              activeTab === 'preferences'
                ? 'border-cyan-500 text-cyan-400 bg-cyan-500/5'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            Preferences
          </button>

          <button
            onClick={() => setActiveTab('simulator')}
            className={`flex-1 py-2.5 text-center transition-all border-b-2 flex items-center justify-center gap-1.5 ${
              activeTab === 'simulator'
                ? 'border-amber-500 text-amber-400 bg-amber-500/5'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            Dev Simulator
          </button>
        </div>

        {/* TAB 1: NOTIFICATIONS LIST */}
        {activeTab === 'notifications' && (
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Filter toolbar */}
            <div className="px-4 py-2 bg-slate-950/30 border-b border-slate-800 flex items-center justify-between text-xs">
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setUnreadOnly(false)}
                  className={`px-2 py-0.5 rounded transition-colors ${
                    !unreadOnly ? 'bg-slate-800 text-white font-medium' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  All ({notifications.length})
                </button>
                <button
                  onClick={() => setUnreadOnly(true)}
                  className={`px-2 py-0.5 rounded transition-colors ${
                    unreadOnly ? 'bg-cyan-500/20 text-cyan-300 font-medium' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Unread ({unreadCount})
                </button>
              </div>

              <div className="flex items-center space-x-2">
                {unreadCount > 0 && (
                  <button
                    onClick={onMarkAllRead}
                    className="text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1 transition-colors"
                  >
                    <CheckCheck className="w-3.5 h-3.5" /> Mark all read
                  </button>
                )}
                {notifications.length > 0 && (
                  <button
                    onClick={handleClearAll}
                    title="Clear history"
                    className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {filteredNotifications.length === 0 ? (
                <div className="py-20 text-center text-slate-500 space-y-2">
                  <ShieldAlert className="w-12 h-12 mx-auto text-slate-600" />
                  <p className="text-sm font-medium">No active warnings or advisories</p>
                  <p className="text-xs text-slate-600">
                    Smart monitoring continually inspects saved plans for atmospheric shifts.
                  </p>
                </div>
              ) : (
                filteredNotifications.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => !item.read && onMarkRead(item.id)}
                    className={`p-3.5 rounded-xl border text-xs transition-all space-y-2 ${
                      item.read
                        ? 'bg-slate-900/40 border-slate-800/60 opacity-80'
                        : 'bg-slate-850/90 border-cyan-500/30 shadow-lg ring-1 ring-cyan-500/10'
                    }`}
                  >
                    {/* Header line with badges */}
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                        {SEVERITY_ICONS[item.severity] || SEVERITY_ICONS.info}
                        <span className="font-semibold text-slate-100 text-sm">{item.title}</span>
                      </div>

                      <div className="flex items-center space-x-1.5 shrink-0">
                        {item.is_simulated && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                            [SIMULATED]
                          </span>
                        )}
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-semibold border ${
                            SEVERITY_BADGES[item.severity] || SEVERITY_BADGES.info
                          }`}
                        >
                          {item.severity.toUpperCase()}
                        </span>
                        {!item.read && <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />}
                      </div>
                    </div>

                    {/* Notification message */}
                    <p className="text-slate-300 leading-relaxed pl-6">{item.message}</p>

                    {/* Previous vs New Values Diff Card */}
                    {(item.previous_value || item.new_value) && (
                      <div className="ml-6 p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80 space-y-1.5">
                        <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                          Atmospheric Telemetry Comparison
                        </div>
                        <div className="grid grid-cols-11 items-center gap-1 text-[11px]">
                          <div className="col-span-5 bg-slate-900/90 px-2 py-1.5 rounded border border-slate-800">
                            <span className="text-[10px] text-slate-500 block">Previous</span>
                            <span className="text-slate-300 font-mono">{item.previous_value || 'Initial snapshot'}</span>
                          </div>
                          <div className="col-span-1 text-center text-cyan-400 font-bold">
                            <ArrowRight className="w-3.5 h-3.5 mx-auto" />
                          </div>
                          <div className="col-span-5 bg-slate-900/90 px-2 py-1.5 rounded border border-cyan-500/20">
                            <span className="text-[10px] text-cyan-400/80 block">Current Telemetry</span>
                            <span className="text-cyan-200 font-mono font-medium">{item.new_value || 'Shift detected'}</span>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Reason for change */}
                    {item.reason && (
                      <div className="ml-6 px-2.5 py-1.5 rounded bg-slate-950/40 border border-slate-800/60 text-[11px] text-slate-400">
                        <span className="font-semibold text-slate-300">Reason: </span>
                        {item.reason}
                      </div>
                    )}

                    {/* Footer info: Critic review status, location, link, timestamp */}
                    <div className="flex items-center justify-between text-[11px] text-slate-500 pl-6 pt-1 flex-wrap gap-2">
                      <div className="flex items-center space-x-2">
                        {item.critic_review_approved && (
                          <span className="inline-flex items-center text-[10px] text-emerald-400 font-medium">
                            <Check className="w-3 h-3 mr-0.5" /> Critic Approved
                          </span>
                        )}
                        <span>•</span>
                        <span>{item.location || 'Regional Envelope'}</span>
                      </div>

                      <div className="flex items-center space-x-3">
                        {item.link && (
                          <a
                            href={item.link}
                            onClick={(e) => {
                              e.stopPropagation();
                              if (item.plan_id && onSelectPlan) {
                                onSelectPlan(item.plan_id);
                              }
                              onClose();
                            }}
                            className="inline-flex items-center text-cyan-400 hover:text-cyan-300 font-semibold gap-1"
                          >
                            <span>View Plan</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                        <span>{new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* TAB 2: USER PREFERENCES */}
        {activeTab === 'preferences' && (
          <div className="flex-1 overflow-y-auto p-5 space-y-6">
            <div>
              <h4 className="font-semibold text-slate-100 text-sm mb-1">Notification Preferences</h4>
              <p className="text-xs text-slate-400">
                Customize how and when you receive automated updates from smart monitoring.
              </p>
            </div>

            <div className="space-y-4">
              {/* In-app toggle */}
              <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
                <div>
                  <span className="text-xs font-semibold text-slate-200 block">In-App Notification Feed</span>
                  <span className="text-[11px] text-slate-400">Display persistent alerts inside the dashboard</span>
                </div>
                <input
                  type="checkbox"
                  checked={preferences.in_app_enabled}
                  onChange={(e) => handleSavePreferences({ in_app_enabled: e.target.checked })}
                  className="w-4 h-4 rounded text-cyan-500 bg-slate-900 border-slate-700 focus:ring-cyan-500 focus:ring-offset-slate-900 cursor-pointer"
                />
              </div>

              {/* Browser push toggle */}
              <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
                <div>
                  <span className="text-xs font-semibold text-slate-200 block">Web Push Notifications</span>
                  <span className="text-[11px] text-slate-400">Receive real-time system alerts via service worker</span>
                </div>
                <input
                  type="checkbox"
                  checked={preferences.browser_push_enabled}
                  onChange={(e) => handleSavePreferences({ browser_push_enabled: e.target.checked })}
                  className="w-4 h-4 rounded text-cyan-500 bg-slate-900 border-slate-700 focus:ring-cyan-500 focus:ring-offset-slate-900 cursor-pointer"
                />
              </div>

              {/* Min severity filter */}
              <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                <span className="text-xs font-semibold text-slate-200 block">Minimum Alert Severity</span>
                <span className="text-[11px] text-slate-400 block">
                  Only dispatch notifications when severity reaches or exceeds:
                </span>
                <div className="grid grid-cols-3 gap-2 pt-1 text-xs">
                  {['info', 'warning', 'danger'].map((sev) => (
                    <button
                      key={sev}
                      onClick={() => handleSavePreferences({ min_severity: sev })}
                      className={`py-2 px-3 rounded-lg border font-medium capitalize transition-all ${
                        preferences.min_severity === sev
                          ? 'bg-cyan-500/20 border-cyan-500/40 text-cyan-300'
                          : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                      }`}
                    >
                      {sev === 'info' ? 'All (Info+)' : sev === 'warning' ? 'Warning+' : 'Severe Only'}
                    </button>
                  ))}
                </div>
              </div>

              {/* Notification types */}
              <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
                <span className="text-xs font-semibold text-slate-200 block">Trigger Events</span>

                <label className="flex items-center space-x-2.5 text-xs text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={preferences.notify_on_weather_change}
                    onChange={(e) => handleSavePreferences({ notify_on_weather_change: e.target.checked })}
                    className="w-4 h-4 rounded text-cyan-500 bg-slate-900 border-slate-700 focus:ring-cyan-500 focus:ring-offset-slate-900"
                  />
                  <span>Significant Meteorological Shift (Rain, Wind, Temperature)</span>
                </label>

                <label className="flex items-center space-x-2.5 text-xs text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={preferences.notify_on_verdict_change}
                    onChange={(e) => handleSavePreferences({ notify_on_verdict_change: e.target.checked })}
                    className="w-4 h-4 rounded text-cyan-500 bg-slate-900 border-slate-700 focus:ring-cyan-500 focus:ring-offset-slate-900"
                  />
                  <span>Recommendation & Safety Verdict Changes</span>
                </label>
              </div>
            </div>

            {prefSaveMsg && (
              <div className="text-center text-xs text-cyan-400 font-medium">
                {prefSaveMsg}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: DEV-MODE SIMULATOR */}
        {activeTab === 'simulator' && (
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl space-y-1">
              <div className="flex items-center space-x-2 text-amber-400 font-semibold text-xs">
                <Sparkles className="w-4 h-4" />
                <span>Dev-Mode On-Demand Simulator</span>
              </div>
              <p className="text-[11px] text-amber-300/80 leading-relaxed">
                Test change detection, telemetry diff presentation, review-gated delivery, and browser push without waiting for external weather shifts. Dispatched alerts are clearly labeled <span className="font-bold">[SIMULATED]</span>.
              </p>
            </div>

            {/* Quick Presets */}
            <div className="space-y-1.5">
              <span className="text-[11px] font-semibold text-slate-400 block uppercase tracking-wider">
                Quick Simulation Presets
              </span>
              <div className="grid grid-cols-3 gap-2 text-xs">
                {PRESET_SIMULATIONS.map((preset) => (
                  <button
                    key={preset.name}
                    onClick={() => handleApplyPreset(preset)}
                    className="p-2 rounded-lg bg-slate-950/70 border border-slate-800 hover:border-amber-500/40 text-left transition-colors text-[11px]"
                  >
                    <div className="font-semibold text-slate-200">{preset.name}</div>
                    <div className="text-[10px] text-slate-400">{preset.criticVerdict === 'APPROVE' ? '✓ Approved' : '✗ Reject Test'}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Form */}
            <div className="space-y-3 text-xs">
              {savedPlans.length > 0 && (
                <div>
                  <label className="text-slate-400 block mb-1">Target Plan</label>
                  <select
                    value={simPlanId}
                    onChange={(e) => setSimPlanId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-amber-500/50"
                  >
                    {savedPlans.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.subject} ({p.location}) - {p.target_date}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="text-slate-400 block mb-1">Shift Metric</label>
                <input
                  type="text"
                  value={simMetric}
                  onChange={(e) => setSimMetric(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-amber-500/50"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-slate-400 block mb-1">Previous Telemetry</label>
                  <input
                    type="text"
                    value={simPrevious}
                    onChange={(e) => setSimPrevious(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 font-mono text-[11px]"
                  />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">New Telemetry</label>
                  <input
                    type="text"
                    value={simNew}
                    onChange={(e) => setSimNew(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-amber-200 font-mono text-[11px]"
                  />
                </div>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Change Significance Reason</label>
                <input
                  type="text"
                  value={simReason}
                  onChange={(e) => setSimReason(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-slate-400 block mb-1">Severity</label>
                  <select
                    value={simSeverity}
                    onChange={(e) => setSimSeverity(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 capitalize"
                  >
                    <option value="info">Info</option>
                    <option value="warning">Warning</option>
                    <option value="danger">Danger</option>
                  </select>
                </div>

                <div>
                  <label className="text-slate-400 block mb-1">Critic Agent Verdict</label>
                  <select
                    value={simCriticVerdict}
                    onChange={(e) => setSimCriticVerdict(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 font-semibold text-slate-200"
                  >
                    <option value="APPROVE">APPROVE (Allow Dispatch)</option>
                    <option value="REJECT">REJECT (Suppress Delivery)</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center space-x-2 pt-1">
                <input
                  type="checkbox"
                  id="simPushToggle"
                  checked={simSendPush}
                  onChange={(e) => setSimSendPush(e.target.checked)}
                  className="w-4 h-4 rounded text-amber-500 bg-slate-950 border-slate-700 focus:ring-amber-500 focus:ring-offset-slate-900"
                />
                <label htmlFor="simPushToggle" className="text-xs text-slate-300 cursor-pointer">
                  Also trigger browser push notification via Web Push API
                </label>
              </div>

              <button
                onClick={handleRunSimulation}
                disabled={isSimulating}
                className="w-full py-2.5 px-4 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold rounded-lg shadow-lg flex items-center justify-center space-x-2 transition-all disabled:opacity-50"
              >
                {isSimulating ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Simulating Change & Pipeline...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    <span>[DEV] Simulate Change & Notification</span>
                  </>
                )}
              </button>
            </div>

            {/* Simulation Response Feedback */}
            {simulationResult && (
              <div
                className={`p-3.5 rounded-xl border text-xs space-y-2 animate-fadeIn ${
                  simulationResult.status === 'success'
                    ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-200'
                    : simulationResult.status === 'suppressed'
                    ? 'bg-amber-950/40 border-amber-500/30 text-amber-200'
                    : 'bg-rose-950/40 border-rose-500/30 text-rose-200'
                }`}
              >
                <div className="font-semibold flex items-center gap-1.5">
                  {simulationResult.status === 'success' && <Check className="w-4 h-4 text-emerald-400" />}
                  {simulationResult.status === 'suppressed' && <ShieldAlert className="w-4 h-4 text-amber-400" />}
                  <span>Status: {simulationResult.status.toUpperCase()}</span>
                </div>
                <p className="text-[11px] leading-relaxed">{simulationResult.message}</p>
                {simulationResult.push_summary && (
                  <div className="text-[10px] opacity-80 pt-1 border-t border-slate-800/40">
                    Push Delivery: {simulationResult.push_summary.sent} sent,{' '}
                    {simulationResult.push_summary.expired} expired,{' '}
                    {simulationResult.push_summary.failed} failed.
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
