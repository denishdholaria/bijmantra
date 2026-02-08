/**
 * Real-time Event System
 * Foundation for live updates - can be upgraded to Socket.io/Ably later
 * Currently uses EventSource (SSE) with fallback to polling
 */

type EventCallback = (data: unknown) => void

interface RealtimeEvent {
  type: string
  payload: unknown
  timestamp: number
  userId?: string
}

class RealtimeClient {
  private listeners: Map<string, Set<EventCallback>> = new Map()
  private eventSource: EventSource | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private isConnected = false
  private connectionListeners: Set<(connected: boolean) => void> = new Set()

  constructor() {
    // Auto-connect when in browser
    if (typeof window !== 'undefined') {
      this.connect()
    }
  }

  /**
   * Connect to the real-time event stream
   */
  connect(url?: string) {
    const eventUrl = url || '/api/events/stream'
    
    try {
      this.eventSource = new EventSource(eventUrl)
      
      this.eventSource.onopen = () => {
        this.isConnected = true
        this.reconnectAttempts = 0
        this.notifyConnectionChange(true)
        console.log('[Realtime] Connected to event stream')
      }

      this.eventSource.onmessage = (event) => {
        try {
          const data: RealtimeEvent = JSON.parse(event.data)
          this.emit(data.type, data.payload)
        } catch (e) {
          console.error('[Realtime] Failed to parse event:', e)
        }
      }

      this.eventSource.onerror = () => {
        this.isConnected = false
        this.notifyConnectionChange(false)
        this.eventSource?.close()
        this.scheduleReconnect()
      }
    } catch (e) {
      console.warn('[Realtime] SSE not available, using polling fallback')
      this.startPolling()
    }
  }

  /**
   * Fallback polling mechanism
   */
  private pollingInterval: ReturnType<typeof setInterval> | null = null
  
  private startPolling() {
    if (this.pollingInterval) return
    
    this.pollingInterval = setInterval(async () => {
      try {
        const response = await fetch('/api/events/poll')
        if (response.ok) {
          const events: RealtimeEvent[] = await response.json()
          events.forEach(event => this.emit(event.type, event.payload))
        }
      } catch {
        // Silently fail polling
      }
    }, 5000) // Poll every 5 seconds
  }

  private stopPolling() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval)
      this.pollingInterval = null
    }
  }

  /**
   * Schedule reconnection with exponential backoff
   */
  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.warn('[Realtime] Max reconnect attempts reached, falling back to polling')
      this.startPolling()
      return
    }

    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts)
    this.reconnectAttempts++
    
    console.log(`[Realtime] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`)
    setTimeout(() => this.connect(), delay)
  }

  /**
   * Subscribe to an event type
   */
  on(eventType: string, callback: EventCallback): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set())
    }
    this.listeners.get(eventType)!.add(callback)

    // Return unsubscribe function
    return () => {
      this.listeners.get(eventType)?.delete(callback)
    }
  }

  /**
   * Emit an event to all listeners
   */
  private emit(eventType: string, data: unknown) {
    // Emit to specific listeners
    this.listeners.get(eventType)?.forEach(callback => {
      try {
        callback(data)
      } catch (e) {
        console.error(`[Realtime] Error in ${eventType} listener:`, e)
      }
    })

    // Emit to wildcard listeners
    this.listeners.get('*')?.forEach(callback => {
      try {
        callback({ type: eventType, data })
      } catch (e) {
        console.error('[Realtime] Error in wildcard listener:', e)
      }
    })
  }

  /**
   * Subscribe to connection state changes
   */
  onConnectionChange(callback: (connected: boolean) => void): () => void {
    this.connectionListeners.add(callback)
    // Immediately notify of current state
    callback(this.isConnected)
    return () => this.connectionListeners.delete(callback)
  }

  private notifyConnectionChange(connected: boolean) {
    this.connectionListeners.forEach(cb => cb(connected))
  }

  /**
   * Check if connected
   */
  get connected() {
    return this.isConnected
  }

  /**
   * Disconnect from the event stream
   */
  disconnect() {
    this.eventSource?.close()
    this.eventSource = null
    this.stopPolling()
    this.isConnected = false
    this.notifyConnectionChange(false)
  }
}

// Singleton instance
export const realtime = new RealtimeClient()

// Event types for type safety
export const RealtimeEvents = {
  // Data sync events
  GERMPLASM_UPDATED: 'germplasm:updated',
  GERMPLASM_CREATED: 'germplasm:created',
  TRIAL_UPDATED: 'trial:updated',
  OBSERVATION_CREATED: 'observation:created',
  
  // Collaboration events
  USER_JOINED: 'user:joined',
  USER_LEFT: 'user:left',
  CURSOR_MOVED: 'cursor:moved',
  
  // Notification events
  NOTIFICATION: 'notification',
  ALERT: 'alert',
  
  // System events
  SYNC_COMPLETE: 'sync:complete',
  SYNC_CONFLICT: 'sync:conflict',
  SYSTEM_MESSAGE: 'system:message',
} as const

// React hook for real-time events
import { useEffect, useState } from 'react'

export function useRealtimeEvent<T = unknown>(eventType: string, callback?: (data: T) => void) {
  const [lastEvent, setLastEvent] = useState<T | null>(null)

  useEffect(() => {
    const unsubscribe = realtime.on(eventType, (data) => {
      setLastEvent(data as T)
      callback?.(data as T)
    })
    return unsubscribe
  }, [eventType, callback])

  return lastEvent
}

export function useRealtimeConnection() {
  const [isConnected, setIsConnected] = useState(realtime.connected)

  useEffect(() => {
    return realtime.onConnectionChange(setIsConnected)
  }, [])

  return isConnected
}
