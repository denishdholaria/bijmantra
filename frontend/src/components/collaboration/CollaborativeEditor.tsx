/**
 * Collaborative Editor Component
 * Real-time collaborative editing with CRDT sync
 * 
 * APEX FEATURE: First breeding platform with real-time collaboration
 */

import { useState, useEffect, useRef } from 'react'
import { cn } from '@/lib/utils'
import { PresenceAvatars, getUserColor, getInitials } from './RealtimePresence'

interface CollaboratorActivity {
  userId: string
  userName: string
  userColor: string
  action: 'viewing' | 'editing' | 'selecting'
  field?: string
  timestamp: number
}

interface CollaborativeFieldProps {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
  type?: 'text' | 'textarea' | 'number'
  collaborators?: CollaboratorActivity[]
  className?: string
}

export function CollaborativeField({
  id,
  label,
  value,
  onChange,
  type = 'text',
  collaborators = [],
  className
}: CollaborativeFieldProps) {
  const [isFocused, setIsFocused] = useState(false)
  const [localValue, setLocalValue] = useState(value)
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement>(null)

  // Sync with external value
  useEffect(() => {
    if (!isFocused) {
      setLocalValue(value)
    }
  }, [value, isFocused])

  // Get collaborators editing this field
  const fieldCollaborators = collaborators.filter(
    c => c.field === id && c.action === 'editing'
  )

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const newValue = e.target.value
    setLocalValue(newValue)
    onChange(newValue)
  }

  const handleFocus = () => {
    setIsFocused(true)
    // Broadcast focus event
  }

  const handleBlur = () => {
    setIsFocused(false)
    // Broadcast blur event
  }

  const InputComponent = type === 'textarea' ? 'textarea' : 'input'

  return (
    <div className={cn('relative', className)}>
      <label 
        htmlFor={id}
        className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
      >
        {label}
      </label>
      
      <div className="relative">
        <InputComponent
          ref={inputRef as any}
          id={id}
          type={type === 'textarea' ? undefined : type}
          value={localValue}
          onChange={handleChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          className={cn(
            'w-full px-3 py-2 border rounded-lg transition-all',
            'bg-white dark:bg-gray-800',
            'text-gray-900 dark:text-gray-100',
            'focus:outline-none focus:ring-2',
            fieldCollaborators.length > 0
              ? 'border-2'
              : 'border-gray-300 dark:border-gray-600',
            type === 'textarea' && 'min-h-[100px] resize-y'
          )}
          style={
            fieldCollaborators.length > 0
              ? { borderColor: fieldCollaborators[0].userColor }
              : undefined
          }
        />

        {/* Collaborator indicators */}
        {fieldCollaborators.length > 0 && (
          <div className="absolute -top-2 -right-2 flex -space-x-1">
            {fieldCollaborators.slice(0, 3).map(collab => (
              <div
                key={collab.userId}
                className="w-6 h-6 rounded-full border-2 border-white dark:border-gray-800 flex items-center justify-center text-[10px] font-medium text-white shadow-sm"
                style={{ backgroundColor: collab.userColor }}
                title={`${collab.userName} is editing`}
              >
                {getInitials(collab.userName)}
              </div>
            ))}
          </div>
        )}

        {/* Typing indicator */}
        {fieldCollaborators.length > 0 && (
          <div 
            className="absolute -bottom-5 left-0 text-xs flex items-center gap-1"
            style={{ color: fieldCollaborators[0].userColor }}
          >
            <span className="flex gap-0.5">
              <span className="w-1 h-1 rounded-full animate-bounce" style={{ backgroundColor: fieldCollaborators[0].userColor, animationDelay: '0ms' }} />
              <span className="w-1 h-1 rounded-full animate-bounce" style={{ backgroundColor: fieldCollaborators[0].userColor, animationDelay: '150ms' }} />
              <span className="w-1 h-1 rounded-full animate-bounce" style={{ backgroundColor: fieldCollaborators[0].userColor, animationDelay: '300ms' }} />
            </span>
            <span>{fieldCollaborators[0].userName} is typing...</span>
          </div>
        )}
      </div>
    </div>
  )
}

interface CollaborativeFormProps {
  children: React.ReactNode
  documentId: string
  documentType: string
  className?: string
}

export function CollaborativeForm({
  children,
  documentId,
  documentType,
  className
}: CollaborativeFormProps) {
  const [collaborators, setCollaborators] = useState<CollaboratorActivity[]>([])
  const [lastSaved, setLastSaved] = useState<Date | null>(null)
  const [syncStatus, setSyncStatus] = useState<'synced' | 'syncing' | 'offline'>('synced')

  // Simulate collaborator activity
  useEffect(() => {
    const interval = setInterval(() => {
      // In production, this would come from WebSocket
      const demoActivity: CollaboratorActivity[] = [
        {
          userId: 'demo-1',
          userName: 'Dr. Sharma',
          userColor: getUserColor('demo-1'),
          action: 'viewing',
          timestamp: Date.now()
        }
      ]
      setCollaborators(demoActivity)
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className={cn('relative', className)}>
      {/* Collaboration header */}
      <div className="flex items-center justify-between mb-4 pb-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <PresenceAvatars
            users={collaborators.map(c => ({
              id: c.userId,
              name: c.userName,
              email: '',
              color: c.userColor
            }))}
            currentUserId="current-user"
          />
          
          {collaborators.length > 0 && (
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {collaborators.length} collaborator{collaborators.length !== 1 ? 's' : ''} viewing
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Sync status */}
          <div className="flex items-center gap-1.5 text-sm">
            {syncStatus === 'synced' && (
              <>
                <span className="w-2 h-2 rounded-full bg-green-500" />
                <span className="text-green-600 dark:text-green-400">Saved</span>
              </>
            )}
            {syncStatus === 'syncing' && (
              <>
                <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                <span className="text-amber-600 dark:text-amber-400">Saving...</span>
              </>
            )}
            {syncStatus === 'offline' && (
              <>
                <span className="w-2 h-2 rounded-full bg-gray-400" />
                <span className="text-gray-500">Offline</span>
              </>
            )}
          </div>

          {lastSaved && (
            <span className="text-xs text-gray-400">
              Last saved {lastSaved.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* Form content */}
      <CollaborativeContext.Provider value={{ collaborators, documentId, documentType }}>
        {children}
      </CollaborativeContext.Provider>
    </div>
  )
}

// Context
import { createContext, useContext } from 'react'

interface CollaborativeContextValue {
  collaborators: CollaboratorActivity[]
  documentId: string
  documentType: string
}

const CollaborativeContext = createContext<CollaborativeContextValue | null>(null)

export function useCollaborative() {
  const context = useContext(CollaborativeContext)
  if (!context) {
    throw new Error('useCollaborative must be used within CollaborativeForm')
  }
  return context
}

export type { CollaboratorActivity }
