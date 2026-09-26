/**
 * Web Push and Service Worker Utilities for MausamAI
 */

export function isPushNotificationSupported() {
  return (
    typeof window !== 'undefined' &&
    'serviceWorker' in navigator &&
    'PushManager' in window &&
    'Notification' in window
  );
}

export function getNotificationPermissionState() {
  if (typeof window === 'undefined' || !('Notification' in window)) {
    return 'unsupported';
  }
  return Notification.permission; // 'default', 'granted', 'denied'
}

export function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export async function registerServiceWorker() {
  if (!isPushNotificationSupported()) {
    console.warn('[MausamAI] Push notifications or Service Worker not supported in this browser environment.');
    return null;
  }
  try {
    const registration = await navigator.serviceWorker.register('/sw.js', { scope: '/' });
    await navigator.serviceWorker.ready;
    return registration;
  } catch (error) {
    console.error('[MausamAI] Service Worker registration failed:', error);
    return null;
  }
}

export async function getCurrentPushSubscription() {
  if (!isPushNotificationSupported()) return null;
  try {
    const registration = await navigator.serviceWorker.ready;
    return await registration.pushManager.getSubscription();
  } catch (error) {
    console.error('[MausamAI] Failed to get existing push subscription:', error);
    return null;
  }
}

export async function subscribeToPush(vapidPublicKey) {
  if (!isPushNotificationSupported()) {
    throw new Error('Push notifications are not supported in your browser.');
  }

  const permission = await Notification.requestPermission();
  if (permission !== 'granted') {
    throw new Error(`Notification permission ${permission}. Please grant browser permission to receive alerts.`);
  }

  const registration = await navigator.serviceWorker.ready;
  let subscription = await registration.pushManager.getSubscription();

  if (!subscription) {
    const applicationServerKey = urlBase64ToUint8Array(vapidPublicKey);
    subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey,
    });
  }

  const jsonSub = subscription.toJSON();
  return {
    endpoint: jsonSub.endpoint,
    keys: {
      p256dh: jsonSub.keys.p256dh,
      auth: jsonSub.keys.auth,
    },
    user_agent: navigator.userAgent,
  };
}

export async function unsubscribeFromPush() {
  if (!isPushNotificationSupported()) return null;
  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
    if (subscription) {
      const endpoint = subscription.endpoint;
      await subscription.unsubscribe();
      return endpoint;
    }
    return null;
  } catch (error) {
    console.error('[MausamAI] Failed to unsubscribe from push manager:', error);
    return null;
  }
}
