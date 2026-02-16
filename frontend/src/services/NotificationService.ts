export type PushSubscriptionPayload = {
  endpoint: string
  keys: {
    p256dh: string
    auth: string
  }
}

class NotificationService {
  async requestPermission(): Promise<NotificationPermission> {
    if (!('Notification' in window)) return 'denied'
    return Notification.requestPermission()
  }

  async subscribeToPush(): Promise<void> {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) return

    const permission = await this.requestPermission()
    if (permission !== 'granted') return

    const registration = await navigator.serviceWorker.ready
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: this.urlBase64ToUint8Array(
        import.meta.env.VITE_VAPID_PUBLIC_KEY || 'BElw7I9k-placeholder-vapid-public-key',
      ),
    })

    const json = subscription.toJSON() as PushSubscriptionPayload
    await fetch('/api/v2/pwa/notifications/subscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(json),
    })
  }

  private urlBase64ToUint8Array(base64String: string): Uint8Array {
    const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
    const rawData = window.atob(base64)
    return Uint8Array.from([...rawData].map((char) => char.charCodeAt(0)))
  }
}

export const notificationService = new NotificationService()
