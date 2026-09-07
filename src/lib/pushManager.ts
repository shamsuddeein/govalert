import { api } from "./api";

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export async function requestAndSubscribeWebPush(): Promise<boolean> {
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
    console.warn("Web Push API is not supported in this browser.");
    return false;
  }

  try {
    const permission = await Notification.requestPermission();
    if (permission !== "granted") {
      console.warn("Push notification permission denied by user.");
      return false;
    }

    const registration = await navigator.serviceWorker.ready;

    // Fetch VAPID public key from backend API
    const res = await api.fetchVapidKey();
    const vapidPublicKey = res?.public_key || "BEl62iUYgUivxIkv69yViEuiBIa1-A1J9s3kK3yP1N2_vH3v_rK2A0Z0J_7R9a1x_B2u4E5F6G7H8I9J0K1L2M3";

    let subscription = await registration.pushManager.getSubscription();
    if (!subscription) {
      const convertedKey = urlBase64ToUint8Array(vapidPublicKey);
      subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: convertedKey,
      });
    }

    // Persist subscription in Django backend DB
    const subJson = subscription.toJSON();
    await api.subscribePush({
      endpoint: subJson.endpoint,
      keys: subJson.keys,
    });

    console.info("Web Push subscription active.");
    return true;
  } catch (error) {
    console.error("Failed to subscribe to Web Push notifications:", error);
    return false;
  }
}
