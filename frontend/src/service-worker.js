/// <reference lib="webworker" />
/* eslint-disable no-restricted-globals */

import { clientsClaim } from 'workbox-core'
import { precacheAndRoute, cleanupOutdatedCaches } from 'workbox-precaching'
import { registerRoute } from 'workbox-routing'
import { StaleWhileRevalidate, CacheFirst, NetworkFirst } from 'workbox-strategies'
import { ExpirationPlugin } from 'workbox-expiration'
import { CacheableResponsePlugin } from 'workbox-cacheable-response'
import { BackgroundSyncPlugin } from 'workbox-background-sync'

self.skipWaiting()
clientsClaim()

precacheAndRoute(self.__WB_MANIFEST || [])
cleanupOutdatedCaches()

precacheAndRoute([
  { url: '/manifest.webmanifest', revision: null },
  { url: '/icons/icon-192x192.png', revision: null },
  { url: '/icons/icon-512x512.png', revision: null },
])

registerRoute(
  ({ request }) => request.mode === 'navigate',
  new NetworkFirst({
    cacheName: 'app-shell-cache',
    networkTimeoutSeconds: 4,
    plugins: [new CacheableResponsePlugin({ statuses: [0, 200] })],
  }),
)

registerRoute(
  ({ url }) => url.pathname.startsWith('/brapi/v2/traits') || url.pathname.startsWith('/brapi/v2/studies'),
  new StaleWhileRevalidate({
    cacheName: 'scientific-metadata-cache',
    plugins: [
      new CacheableResponsePlugin({ statuses: [0, 200] }),
      new ExpirationPlugin({ maxEntries: 200, maxAgeSeconds: 24 * 60 * 60 }),
    ],
  }),
)

registerRoute(
  ({ url }) => url.pathname.startsWith('/api/v2/datasets') || url.pathname.includes('/dataset'),
  new StaleWhileRevalidate({
    cacheName: 'dataset-cache',
    plugins: [
      new CacheableResponsePlugin({ statuses: [0, 200] }),
      new ExpirationPlugin({ maxEntries: 60, maxAgeSeconds: 7 * 24 * 60 * 60 }),
    ],
  }),
)

registerRoute(
  ({ request, url }) => request.destination === 'image' || url.pathname.startsWith('/uploads/'),
  new CacheFirst({
    cacheName: 'field-images-cache',
    plugins: [
      new CacheableResponsePlugin({ statuses: [0, 200] }),
      new ExpirationPlugin({ maxEntries: 300, maxAgeSeconds: 7 * 24 * 60 * 60 }),
    ],
  }),
)

const observationQueue = new BackgroundSyncPlugin('observation-queue', {
  maxRetentionTime: 24 * 60,
})

registerRoute(
  ({ request, url }) =>
    request.method === 'POST' &&
    (url.pathname.startsWith('/brapi/v2/observations') || url.pathname.startsWith('/api/v2/pwa/drafts/sync')),
  new NetworkFirst({
    cacheName: 'observation-write-through',
    plugins: [observationQueue],
  }),
  'POST',
)

self.addEventListener('push', (event) => {
  if (!event.data) return
  let payload = {}
  try {
    payload = event.data.json()
  } catch {
    payload = { title: 'Bijmantra update', body: event.data.text() }
  }

  const title = payload.title || 'Bijmantra'
  const body = payload.body || 'You have a new field update.'
  const data = payload.data || {}

  event.waitUntil(
    self.registration.showNotification(title, {
      body,
      icon: '/icons/icon-192x192.png',
      badge: '/icons/icon-72x72.png',
      data,
    }),
  )
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const target = event.notification?.data?.url || '/'
  event.waitUntil(clients.openWindow(target))
})

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting()
  }
})
