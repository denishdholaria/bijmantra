/**
 * Toast Notification Hook
 * Global toast notifications with real-time event integration
 */

import { create } from 'zustand'

export type ToastType = 'success' | 'error' | 'warning' | 'info' | 'loading'

export interface Toast {
  id: string
  type: ToastType
  title: string
  description?: string
  duration?: number
  action?: {
    label: string
    onClick: () => void
  }
  dismissible?: boolean
}

interface ToastStore {
  toasts: Toast[]
  addToast: (toast: Omit<Toast, 'id'>) => string
  removeToast: (id: string) => void
  clearToasts: () => void
}

// Generate unique ID
const generateId = () => Math.random().toString(36).substring(2, 9)

export const useToastStore = create<ToastStore>((set, get) => ({
  toasts: [],
  
  addToast: (toast) => {
    const id = generateId()
    const newToast: Toast = {
      ...toast,
      id,
      duration: toast.duration ?? (toast.type === 'loading' ? Infinity : 5000),
      dismissible: toast.dismissible ?? true,
    }
    
    set((state) => ({
      toasts: [...state.toasts, newToast],
    }))
    
    // Auto-remove after duration
    if (newToast.duration !== Infinity) {
      setTimeout(() => {
        get().removeToast(id)
      }, newToast.duration)
    }
    
    return id
  },
  
  removeToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }))
  },
  
  clearToasts: () => {
    set({ toasts: [] })
  },
}))

/**
 * Hook for using toasts
 */
export function useToast() {
  const { addToast, removeToast, clearToasts } = useToastStore()
  
  return {
    toast: (options: Omit<Toast, 'id'>) => addToast(options),
    
    success: (title: string, description?: string) => 
      addToast({ type: 'success', title, description }),
    
    error: (title: string, description?: string) => 
      addToast({ type: 'error', title, description }),
    
    warning: (title: string, description?: string) => 
      addToast({ type: 'warning', title, description }),
    
    info: (title: string, description?: string) => 
      addToast({ type: 'info', title, description }),
    
    loading: (title: string, description?: string) => 
      addToast({ type: 'loading', title, description, duration: Infinity }),
    
    dismiss: removeToast,
    dismissAll: clearToasts,
    
    // Promise-based toast for async operations
    promise: async <T>(
      promise: Promise<T>,
      options: {
        loading: string
        success: string | ((data: T) => string)
        error: string | ((err: Error) => string)
      }
    ): Promise<T> => {
      const loadingId = addToast({ type: 'loading', title: options.loading })
      
      try {
        const result = await promise
        removeToast(loadingId)
        addToast({
          type: 'success',
          title: typeof options.success === 'function' 
            ? options.success(result) 
            : options.success,
        })
        return result
      } catch (err) {
        removeToast(loadingId)
        addToast({
          type: 'error',
          title: typeof options.error === 'function'
            ? options.error(err as Error)
            : options.error,
        })
        throw err
      }
    },
  }
}
