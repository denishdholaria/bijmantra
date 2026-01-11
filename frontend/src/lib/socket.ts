/**
 * Socket.io Real-time Collaboration
 * Live updates, presence, and collaborative features
 */

import { io, Socket } from 'socket.io-client'
import { create } from 'zustand'

// Socket configuration
const SOCKET_CONFIG = {
  url: import.meta.env.VITE_SOCKET_URL || 'http://localhost:8000',
  path: '/ws/socket.io',
  reconnectionAttempts: 5,
  reconnectionDelay: 1000,
}

// Event types
export const SocketEvents = {
  // Connection
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
  CONNECT_ERROR: 'connect_error',

  // Presence
  USER_JOINED: 'user:joined',
  USER_LEFT: 'user:left',
  USERS_ONLINE: 'users:online',
  CURSOR_MOVE: 'cursor:move',

  // Data sync
  DATA_CREATED: 'data:created',
  DATA_UPDATED: 'data:updated',
  DATA_DELETED: 'data:deleted',
  SYNC_REQUEST: 'sync:request',
  SYNC_RESPONSE: 'sync:response',

  // Collaboration
  ROOM_JOIN: 'room:join',
  ROOM_LEAVE: 'room:leave',
  ROOM_MESSAGE: 'room:message',
  TYPING_START: 'typing:start',
  TYPING_STOP: 'typing:stop',

  // Notifications
  NOTIFICATION: 'notification',
  ALERT: 'alert',
} as const

// Types
export interface OnlineUser {
  id: string
  name: string
  avatar?: string
  color: string
  cursor?: { x: number; y: number; page: string }
  lastSeen: number
}

export interface DataChangeEvent {
  type: 'germplasm' | 'trial' | 'observation' | 'trait'
  action: 'created' | 'updated' | 'deleted'
  id: string
  data?: Record<string, unknown>
  userId: string
  timestamp: number
}

export interface RoomMessage {
  id: string
  roomId: string
  userId: string
  userName: string
  content: string
  timestamp: number
}

// Presence colors for users
const PRESENCE_COLORS = [
  '#ef4444', '#f97316', '#eab308', '#22c55e', '#14b8a6',
  '#3b82f6', '#8b5cf6', '#ec4899', '#f43f5e', '#06b6d4',
]

function getRandomColor(): string {
  return PRESENCE_COLORS[Math.floor(Math.random() * PRESENCE_COLORS.length)]
}

// Socket service class
class SocketService {
  private socket: Socket | null = null
  private reconnectAttempts = 0
  private listeners: Map<string, Set<(data: unknown) => void>> = new Map()
  private userColor: string = getRandomColor()

  /**
   * Connect to the socket server
   */
  connect(userId: string, userName: string): void {
    if (this.socket?.connected) return

    this.socket = io(SOCKET_CONFIG.url, {
      path: SOCKET_CONFIG.path,
      transports: ['websocket', 'polling'],
      auth: {
        userId,
        userName,
        color: this.userColor,
      },
      reconnectionAttempts: SOCKET_CONFIG.reconnectionAttempts,
      reconnectionDelay: SOCKET_CONFIG.reconnectionDelay,
    })

    this.setupEventHandlers()
  }

  private setupEventHandlers(): void {
    if (!this.socket) return

    this.socket.on(SocketEvents.CONNECT, () => {
      console.log('[Socket] Connected')
      this.reconnectAttempts = 0
      this.emit('internal:connected', null)
    })

    this.socket.on(SocketEvents.DISCONNECT, (reason) => {
      console.log('[Socket] Disconnected:', reason)
      this.emit('internal:disconnected', { reason })
    })

    this.socket.on(SocketEvents.CONNECT_ERROR, (error) => {
      console.error('[Socket] Connection error:', error)
      this.reconnectAttempts++
      this.emit('internal:error', { error: error.message })
    })

    // Forward all events to listeners
    Object.values(SocketEvents).forEach((event) => {
      this.socket?.on(event, (data: unknown) => {
        this.emit(event, data)
      })
    })
  }

  /**
   * Disconnect from the socket server
   */
  disconnect(): void {
    this.socket?.disconnect()
    this.socket = null
  }

  /**
   * Subscribe to an event
   */
  on(event: string, callback: (data: unknown) => void): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event)!.add(callback)

    return () => {
      this.listeners.get(event)?.delete(callback)
    }
  }

  /**
   * Emit an event to listeners
   */
  private emit(event: string, data: unknown): void {
    this.listeners.get(event)?.forEach((callback) => {
      try {
        callback(data)
      } catch (e) {
        console.error(`[Socket] Error in ${event} listener:`, e)
      }
    })
  }

  /**
   * Send an event to the server
   */
  send(event: string, data?: unknown): void {
    if (!this.socket?.connected) {
      console.warn('[Socket] Not connected, cannot send:', event)
      return
    }
    this.socket.emit(event, data)
  }

  /**
   * Join a room for collaborative editing
   */
  joinRoom(roomId: string): void {
    this.send(SocketEvents.ROOM_JOIN, { roomId })
  }

  /**
   * Leave a room
   */
  leaveRoom(roomId: string): void {
    this.send(SocketEvents.ROOM_LEAVE, { roomId })
  }

  /**
   * Send cursor position for presence
   */
  sendCursor(x: number, y: number, page: string): void {
    this.send(SocketEvents.CURSOR_MOVE, { x, y, page })
  }

  /**
   * Broadcast data change
   */
  broadcastDataChange(change: Omit<DataChangeEvent, 'userId' | 'timestamp'>): void {
    this.send(SocketEvents.DATA_UPDATED, change)
  }

  /**
   * Send room message
   */
  sendMessage(roomId: string, content: string): void {
    this.send(SocketEvents.ROOM_MESSAGE, { roomId, content })
  }

  /**
   * Check if connected
   */
  get connected(): boolean {
    return this.socket?.connected ?? false
  }

  /**
   * Get socket ID
   */
  get id(): string | undefined {
    return this.socket?.id
  }
}

// Singleton instance
export const socketService = new SocketService()

// Zustand store for socket state
interface SocketStore {
  isConnected: boolean
  onlineUsers: OnlineUser[]
  currentRoom: string | null
  messages: RoomMessage[]
  setConnected: (connected: boolean) => void
  setOnlineUsers: (users: OnlineUser[]) => void
  addUser: (user: OnlineUser) => void
  removeUser: (userId: string) => void
  updateUserCursor: (userId: string, cursor: { x: number; y: number; page: string }) => void
  setCurrentRoom: (roomId: string | null) => void
  addMessage: (message: RoomMessage) => void
  clearMessages: () => void
}

export const useSocketStore = create<SocketStore>((set) => ({
  isConnected: false,
  onlineUsers: [],
  currentRoom: null,
  messages: [],

  setConnected: (connected) => set({ isConnected: connected }),

  setOnlineUsers: (users) => set({ onlineUsers: users }),

  addUser: (user) =>
    set((state) => ({
      onlineUsers: [...state.onlineUsers.filter((u) => u.id !== user.id), user],
    })),

  removeUser: (userId) =>
    set((state) => ({
      onlineUsers: state.onlineUsers.filter((u) => u.id !== userId),
    })),

  updateUserCursor: (userId, cursor) =>
    set((state) => ({
      onlineUsers: state.onlineUsers.map((u) =>
        u.id === userId ? { ...u, cursor } : u
      ),
    })),

  setCurrentRoom: (roomId) => set({ currentRoom: roomId }),

  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message].slice(-100), // Keep last 100 messages
    })),

  clearMessages: () => set({ messages: [] }),
}))

// React hooks
import { useEffect } from 'react'
import { useAuthStore } from '@/store/auth'

export function useSocket() {
  const { user } = useAuthStore()
  const { isConnected, setConnected, setOnlineUsers, addUser, removeUser, updateUserCursor } =
    useSocketStore()

  useEffect(() => {
    if (!user) return

    // Connect with user info
    socketService.connect(String(user.id), user.full_name)

    // Set up event listeners
    const unsubConnect = socketService.on('internal:connected', () => {
      setConnected(true)
    })

    const unsubDisconnect = socketService.on('internal:disconnected', () => {
      setConnected(false)
    })

    const unsubUsersOnline = socketService.on(SocketEvents.USERS_ONLINE, (data) => {
      setOnlineUsers(data as OnlineUser[])
    })

    const unsubUserJoined = socketService.on(SocketEvents.USER_JOINED, (data) => {
      addUser(data as OnlineUser)
    })

    const unsubUserLeft = socketService.on(SocketEvents.USER_LEFT, (data) => {
      removeUser((data as { userId: string }).userId)
    })

    const unsubCursorMove = socketService.on(SocketEvents.CURSOR_MOVE, (data) => {
      const { userId, ...cursor } = data as { userId: string; x: number; y: number; page: string }
      updateUserCursor(userId, cursor)
    })

    return () => {
      unsubConnect()
      unsubDisconnect()
      unsubUsersOnline()
      unsubUserJoined()
      unsubUserLeft()
      unsubCursorMove()
      socketService.disconnect()
    }
  }, [user, setConnected, setOnlineUsers, addUser, removeUser, updateUserCursor])

  return {
    isConnected,
    send: socketService.send.bind(socketService),
    joinRoom: socketService.joinRoom.bind(socketService),
    leaveRoom: socketService.leaveRoom.bind(socketService),
    sendCursor: socketService.sendCursor.bind(socketService),
    broadcastDataChange: socketService.broadcastDataChange.bind(socketService),
  }
}

export function usePresence() {
  const { onlineUsers } = useSocketStore()
  return { onlineUsers }
}

export function useRoom(roomId: string) {
  const { messages, addMessage, clearMessages, setCurrentRoom } = useSocketStore()

  useEffect(() => {
    socketService.joinRoom(roomId)
    setCurrentRoom(roomId)

    const unsubMessage = socketService.on(SocketEvents.ROOM_MESSAGE, (data) => {
      addMessage(data as RoomMessage)
    })

    return () => {
      unsubMessage()
      socketService.leaveRoom(roomId)
      setCurrentRoom(null)
      clearMessages()
    }
  }, [roomId, addMessage, clearMessages, setCurrentRoom])

  return {
    messages,
    sendMessage: (content: string) => socketService.sendMessage(roomId, content),
  }
}
