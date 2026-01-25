/**
 * Vitest Test Setup
 * Configures testing environment for Bijmantra frontend
 */

import '@testing-library/jest-dom'

// Mock IndexedDB for Dexie
import 'fake-indexeddb/auto'

// Mock localStorage
const localStorageMock = {
  store: {} as Record<string, string>,
  getItem(key: string) {
    return this.store[key] || null
  },
  setItem(key: string, value: string) {
    this.store[key] = value
  },
  removeItem(key: string) {
    delete this.store[key]
  },
  clear() {
    this.store = {}
  },
}
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// Mock navigator.onLine
Object.defineProperty(navigator, 'onLine', {
  writable: true,
  value: true,
})

// Mock window.addEventListener for online/offline events
const originalAddEventListener = window.addEventListener
const onlineListeners: EventListener[] = []
const offlineListeners: EventListener[] = []

window.addEventListener = ((type: string, listener: EventListener) => {
  if (type === 'online') {
    onlineListeners.push(listener)
  } else if (type === 'offline') {
    offlineListeners.push(listener)
  }
  return originalAddEventListener.call(window, type, listener)
}) as typeof window.addEventListener

// Helper to simulate going offline/online
export function simulateOffline() {
  Object.defineProperty(navigator, 'onLine', { value: false })
  offlineListeners.forEach((listener) => listener(new Event('offline')))
}

export function simulateOnline() {
  Object.defineProperty(navigator, 'onLine', { value: true })
  onlineListeners.forEach((listener) => listener(new Event('online')))
}
