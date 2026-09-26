/**
 * Browser Geolocation API Utilities for MausamAI
 * Handles live GPS coordinate detection, error classification, and permission checks.
 */

export class GeolocationError extends Error {
  constructor(code, message, originalError = null) {
    super(message);
    this.name = 'GeolocationError';
    this.code = code; // 'PERMISSION_DENIED' | 'POSITION_UNAVAILABLE' | 'TIMEOUT' | 'UNSUPPORTED'
    this.originalError = originalError;
  }
}

export function isGeolocationSupported() {
  return typeof window !== 'undefined' && 'navigator' in window && 'geolocation' in navigator;
}

export async function checkGeolocationPermission() {
  if (typeof window === 'undefined' || !('navigator' in window) || !('permissions' in navigator)) {
    return 'prompt';
  }
  try {
    const status = await navigator.permissions.query({ name: 'geolocation' });
    return status.state; // 'granted' | 'prompt' | 'denied'
  } catch (e) {
    return 'prompt';
  }
}

export function getCurrentCoordinates(options = {}) {
  return new Promise((resolve, reject) => {
    if (!isGeolocationSupported()) {
      return reject(
        new GeolocationError(
          'UNSUPPORTED',
          'Geolocation is not supported by your browser. Please enter your location manually.'
        )
      );
    }

    const defaultOptions = {
      enableHighAccuracy: true,
      timeout: 10000, // 10 second timeout
      maximumAge: 60000, // Cache for 1 minute
      ...options,
    };

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: Number(position.coords.latitude.toFixed(5)),
          longitude: Number(position.coords.longitude.toFixed(5)),
          accuracy: position.coords.accuracy,
          timestamp: position.timestamp,
        });
      },
      (error) => {
        let code = 'POSITION_UNAVAILABLE';
        let message = 'Unable to detect your current position. You can search any city manually.';

        switch (error.code) {
          case error.PERMISSION_DENIED:
            code = 'PERMISSION_DENIED';
            message = 'Location access was denied. You can search any city or region manually.';
            break;
          case error.POSITION_UNAVAILABLE:
            code = 'POSITION_UNAVAILABLE';
            message = 'GPS position is currently unavailable. Using manual search fallback.';
            break;
          case error.TIMEOUT:
            code = 'TIMEOUT';
            message = 'Location detection timed out. Using manual search fallback.';
            break;
          default:
            code = 'UNKNOWN';
            message = error.message || 'An error occurred while detecting location.';
        }

        reject(new GeolocationError(code, message, error));
      },
      defaultOptions
    );
  });
}
