const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

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
      const err = await res.json().catch(() => ({ detail: 'Analysis failed' }));
      throw new Error(err.detail || `Analysis request failed with status: ${res.status}`);
    }
    return res.json();
  },

  async getWeather(location, date) {
    const params = new URLSearchParams({ location });
    if (date) params.append('date', date);
    const res = await fetch(`${BASE_URL}/weather/current?${params.toString()}`);
    if (!res.ok) throw new Error(`Weather fetch failed: ${res.status}`);
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
