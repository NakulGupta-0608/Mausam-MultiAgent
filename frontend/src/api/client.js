const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export class WeatherApiError extends Error {
  constructor(status, errorData, defaultMsg = 'Weather request failed') {
    let msg = defaultMsg;
    let errorCode = 'UNKNOWN_ERROR';
    let detail = null;
    let locationSearched = null;
    let retriesAttempted = 0;
    let timestamp = new Date().toISOString();

    if (errorData && typeof errorData === 'object') {
      const errObj = errorData.detail && typeof errorData.detail === 'object'
        ? errorData.detail
        : errorData;

      msg = errObj.message || (typeof errorData.detail === 'string' ? errorData.detail : defaultMsg);
      errorCode = errObj.error_code || (status === 404 ? 'LOCATION_NOT_FOUND' : 'WEATHER_API_ERROR');
      detail = errObj.detail || null;
      locationSearched = errObj.location_searched || null;
      retriesAttempted = errObj.retries_attempted || 0;
      timestamp = errObj.timestamp || timestamp;
    }

    super(msg);
    this.name = 'WeatherApiError';
    this.status = status;
    this.errorCode = errorCode;
    this.detail = detail;
    this.locationSearched = locationSearched;
    this.retriesAttempted = retriesAttempted;
    this.timestamp = timestamp;
  }
}

export const apiClient = {
  async getHealth() {
    const res = await fetch(`${BASE_URL}/health`);
    if (!res.ok) throw new Error(`Health check failed with status: ${res.status}`);
    return res.json();
  },

  async analyzeWeather({ query, location, target_date }) {
    const res = await fetch(`${BASE_URL}/analysis`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: query.trim(),
        location: location.trim(),
        target_date: target_date || undefined,
      }),
    });

    if (!res.ok) {
      const errorJson = await res.json().catch(() => null);
      throw new WeatherApiError(res.status, errorJson, `Analysis request failed (${res.status})`);
    }
    return res.json();
  },

  async analyzeWeatherStream({ query, location, target_date }, onEvent) {
    const res = await fetch(`${BASE_URL}/analysis/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: query.trim(),
        location: location.trim(),
        target_date: target_date || undefined,
      }),
    });

    if (!res.ok) {
      const errorJson = await res.json().catch(() => null);
      throw new WeatherApiError(res.status, errorJson, `Streaming analysis request failed (${res.status})`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop(); // save trailing partial chunk

      for (const part of parts) {
        const trimmed = part.trim();
        if (!trimmed) continue;
        const lines = trimmed.split('\n');
        for (const line of lines) {
          if (line.startsWith('data:')) {
            const dataStr = line.slice(5).trim();
            if (dataStr) {
              try {
                const parsed = JSON.parse(dataStr);
                onEvent(parsed);
              } catch (e) {
                console.error('SSE JSON parse error:', e, dataStr);
              }
            }
          }
        }
      }
    }

    if (buffer.trim()) {
      const lines = buffer.trim().split('\n');
      for (const line of lines) {
        if (line.startsWith('data:')) {
          const dataStr = line.slice(5).trim();
          if (dataStr) {
            try {
              const parsed = JSON.parse(dataStr);
              onEvent(parsed);
            } catch (e) {
              console.error('SSE trailing JSON parse error:', e, dataStr);
            }
          }
        }
      }
    }
  },

  async getWeather(location, date) {
    const cleanLocation = location.trim();
    const params = new URLSearchParams({ location: cleanLocation });
    if (date) params.append('date', date);

    const res = await fetch(`${BASE_URL}/weather?${params.toString()}`);
    if (!res.ok) {
      const errorJson = await res.json().catch(() => null);
      throw new WeatherApiError(res.status, errorJson, `Weather query failed (${res.status})`);
    }
    return res.json();
  },

  async getSavedPlans() {
    const res = await fetch(`${BASE_URL}/plans`);
    if (!res.ok) throw new Error(`Fetch plans failed: ${res.status}`);
    return res.json();
  },

  async savePlan(planData) {
    const res = await fetch(`${BASE_URL}/plans`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(planData),
    });
    if (!res.ok) throw new Error(`Save plan failed: ${res.status}`);
    return res.json();
  },

  async deletePlan(planId) {
    const res = await fetch(`${BASE_URL}/plans/${planId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error(`Delete plan failed: ${res.status}`);
    return res.json();
  },

  async checkPlan(planId, simulatedWeather = null, force = false) {
    const res = await fetch(`${BASE_URL}/plans/${planId}/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        simulated_weather: simulatedWeather || undefined,
        force: force,
      }),
    });
    if (!res.ok) {
      const errJson = await res.json().catch(() => null);
      throw new Error(errJson?.detail || `Plan check failed: ${res.status}`);
    }
    return res.json();
  },

  async updatePlanStatus(planId, status) {
    const res = await fetch(`${BASE_URL}/plans/${planId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    });
    if (!res.ok) throw new Error(`Update status failed: ${res.status}`);
    return res.json();
  },

  async getMonitoringStatus() {
    const res = await fetch(`${BASE_URL}/monitoring/status`);
    if (!res.ok) throw new Error(`Get monitoring status failed: ${res.status}`);
    return res.json();
  },

  async triggerMonitoringCycle() {
    const res = await fetch(`${BASE_URL}/monitoring/trigger`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(`Trigger monitoring failed: ${res.status}`);
    return res.json();
  },

  async updateMonitoringInterval(intervalSeconds) {
    const res = await fetch(`${BASE_URL}/monitoring/interval`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ interval_seconds: intervalSeconds }),
    });
    if (!res.ok) throw new Error(`Update interval failed: ${res.status}`);
    return res.json();
  },

  async getNotifications() {
    const res = await fetch(`${BASE_URL}/notifications`);
    if (!res.ok) throw new Error(`Fetch notifications failed: ${res.status}`);
    return res.json();
  },

  async markNotificationRead(notifId) {
    const res = await fetch(`${BASE_URL}/notifications/${notifId}/read`, {
      method: 'PATCH',
    });
    if (!res.ok) throw new Error(`Mark read failed: ${res.status}`);
    return res.json();
  },

  async markAllNotificationsRead() {
    const res = await fetch(`${BASE_URL}/notifications/read-all`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(`Mark all read failed: ${res.status}`);
    return res.json();
  },
};
