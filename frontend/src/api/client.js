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
