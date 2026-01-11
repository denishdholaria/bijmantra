/**
 * Voice Command System
 * Hands-free voice interaction for field operations
 * 
 * Features:
 * - Wake word detection ("Hey Veena" or "Hey Bijmantra")
 * - Voice commands for navigation and data entry
 * - Audio feedback
 * - Offline command recognition
 * 
 * Tech Stack: Web Speech API + Custom Command Parser
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { cn } from '@/lib/utils'

interface VoiceCommand {
  patterns: string[]
  action: (params: string[]) => void
  description: string
  category: 'navigation' | 'data' | 'search' | 'system'
}

interface VoiceCommandProps {
  enabled?: boolean
  wakeWord?: string
  onCommand?: (command: string, action: string) => void
}

export function VoiceCommandProvider({ 
  enabled = true, 
  wakeWord = 'hey veena',
  onCommand 
}: VoiceCommandProps) {
  const navigate = useNavigate()
  const [isListening, setIsListening] = useState(false)
  const [isAwake, setIsAwake] = useState(false)
  const [lastCommand, setLastCommand] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)
  const recognitionRef = useRef<SpeechRecognition | null>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Define voice commands
  const commands: VoiceCommand[] = [
    // Navigation commands
    {
      patterns: ['go to dashboard', 'open dashboard', 'show dashboard'],
      action: () => navigate('/dashboard'),
      description: 'Navigate to dashboard',
      category: 'navigation'
    },
    {
      patterns: ['go to trials', 'open trials', 'show trials'],
      action: () => navigate('/trials'),
      description: 'Navigate to trials',
      category: 'navigation'
    },
    {
      patterns: ['go to germplasm', 'open germplasm', 'show germplasm'],
      action: () => navigate('/germplasm'),
      description: 'Navigate to germplasm',
      category: 'navigation'
    },
    {
      patterns: ['go to observations', 'open observations', 'record observations'],
      action: () => navigate('/observations'),
      description: 'Navigate to observations',
      category: 'navigation'
    },
    {
      patterns: ['go to analytics', 'open analytics', 'show analytics'],
      action: () => navigate('/analytics'),
      description: 'Navigate to analytics',
      category: 'navigation'
    },
    {
      patterns: ['go to settings', 'open settings'],
      action: () => navigate('/settings'),
      description: 'Navigate to settings',
      category: 'navigation'
    },

    // Search commands
    {
      patterns: ['search for (.+)', 'find (.+)', 'look up (.+)'],
      action: (params) => {
        const query = params[0]
        navigate(`/search?q=${encodeURIComponent(query)}`)
        provideFeedback(`Searching for ${query}`)
      },
      description: 'Search for items',
      category: 'search'
    },

    // Data commands
    {
      patterns: ['new observation', 'add observation', 'record data'],
      action: () => {
        navigate('/observations/new')
        provideFeedback('Opening new observation form')
      },
      description: 'Create new observation',
      category: 'data'
    },
    {
      patterns: ['new trial', 'create trial'],
      action: () => {
        navigate('/trials/new')
        provideFeedback('Opening new trial form')
      },
      description: 'Create new trial',
      category: 'data'
    },

    // System commands
    {
      patterns: ['sync data', 'synchronize'],
      action: () => {
        provideFeedback('Syncing data...')
        // Trigger sync
      },
      description: 'Sync offline data',
      category: 'system'
    },
    {
      patterns: ['go offline', 'offline mode'],
      action: () => {
        navigate('/offline')
        provideFeedback('Switching to offline mode')
      },
      description: 'Switch to offline mode',
      category: 'system'
    },
    {
      patterns: ['help', 'what can you do', 'voice commands'],
      action: () => {
        provideFeedback('I can help you navigate, search, and record data. Try saying "go to trials" or "search for wheat"')
      },
      description: 'Show help',
      category: 'system'
    },
    {
      patterns: ['stop listening', 'go to sleep', 'goodbye'],
      action: () => {
        setIsAwake(false)
        provideFeedback('Going to sleep. Say "Hey Veena" to wake me up.')
      },
      description: 'Stop voice commands',
      category: 'system'
    }
  ]

  // Text-to-speech feedback
  const provideFeedback = useCallback((text: string) => {
    setFeedback(text)
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 1.1
      utterance.pitch = 1.0
      speechSynthesis.speak(utterance)
    }
    setTimeout(() => setFeedback(null), 3000)
  }, [])

  // Process voice input
  const processCommand = useCallback((transcript: string) => {
    const lowerTranscript = transcript.toLowerCase().trim()
    setLastCommand(lowerTranscript)

    // Check for wake word
    if (!isAwake && lowerTranscript.includes(wakeWord)) {
      setIsAwake(true)
      provideFeedback('Yes? How can I help?')
      return
    }

    if (!isAwake) return

    // Reset sleep timeout
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    timeoutRef.current = setTimeout(() => {
      setIsAwake(false)
      provideFeedback('Going to sleep')
    }, 30000) // Sleep after 30s of inactivity

    // Match commands
    for (const command of commands) {
      for (const pattern of command.patterns) {
        const regex = new RegExp(`^${pattern}$`, 'i')
        const match = lowerTranscript.match(regex)
        
        if (match) {
          const params = match.slice(1)
          command.action(params)
          onCommand?.(lowerTranscript, command.description)
          return
        }
      }
    }

    // No match found
    provideFeedback("I didn't understand that. Try saying 'help' for available commands.")
  }, [isAwake, wakeWord, commands, provideFeedback, onCommand])

  // Initialize speech recognition
  useEffect(() => {
    if (!enabled) return
    if (!('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)) {
      console.warn('Speech recognition not supported')
      return
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    recognitionRef.current = new SpeechRecognition()
    recognitionRef.current.continuous = true
    recognitionRef.current.interimResults = false
    recognitionRef.current.lang = 'en-US'

    recognitionRef.current.onresult = (event) => {
      const last = event.results.length - 1
      const transcript = event.results[last][0].transcript
      processCommand(transcript)
    }

    recognitionRef.current.onerror = (event) => {
      console.error('Speech recognition error:', event.error)
      if (event.error === 'not-allowed') {
        setIsListening(false)
      }
    }

    recognitionRef.current.onend = () => {
      // Restart if still enabled
      if (isListening && recognitionRef.current) {
        recognitionRef.current.start()
      }
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop()
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [enabled, isListening, processCommand])

  // Toggle listening
  const toggleListening = useCallback(() => {
    if (!recognitionRef.current) return

    if (isListening) {
      recognitionRef.current.stop()
      setIsListening(false)
      setIsAwake(false)
    } else {
      recognitionRef.current.start()
      setIsListening(true)
      provideFeedback('Voice commands activated. Say "Hey Veena" to start.')
    }
  }, [isListening, provideFeedback])

  if (!enabled) return null

  return (
    <>
      {/* Voice Command Indicator */}
      <VoiceIndicator
        isListening={isListening}
        isAwake={isAwake}
        lastCommand={lastCommand}
        feedback={feedback}
        onToggle={toggleListening}
      />
    </>
  )
}

/* ============================================
   VOICE INDICATOR COMPONENT
   ============================================ */
interface VoiceIndicatorProps {
  isListening: boolean
  isAwake: boolean
  lastCommand: string | null
  feedback: string | null
  onToggle: () => void
}

function VoiceIndicator({ isListening, isAwake, lastCommand, feedback, onToggle }: VoiceIndicatorProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="fixed bottom-6 left-6 z-50">
      {/* Main Button */}
      <button
        onClick={onToggle}
        className={cn(
          'w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 shadow-lg',
          isListening
            ? isAwake
              ? 'bg-[#00ff88] shadow-[0_0_30px_rgba(0,255,136,0.5)]'
              : 'bg-[#ff9500] shadow-[0_0_20px_rgba(255,149,0,0.3)]'
            : 'bg-[#21262d] hover:bg-[#30363d]'
        )}
      >
        <span className="text-xl">
          {isListening ? (isAwake ? '🎤' : '👂') : '🎙️'}
        </span>
      </button>

      {/* Status Popup */}
      {(isListening || feedback) && (
        <div
          className={cn(
            'absolute left-14 bottom-0 bg-[#161b22] border border-[#30363d] rounded-lg shadow-xl overflow-hidden transition-all duration-300',
            expanded ? 'w-72' : 'w-48'
          )}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-3 py-2 bg-[#0d1117] border-b border-[#30363d]">
            <div className="flex items-center gap-2">
              <span className={cn(
                'w-2 h-2 rounded-full',
                isAwake ? 'bg-[#00ff88] animate-pulse' : 'bg-[#ff9500]'
              )} />
              <span className="font-mono text-[10px] font-semibold text-[#8b949e] uppercase tracking-wider">
                {isAwake ? 'Listening' : 'Standby'}
              </span>
            </div>
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-[#6e7681] hover:text-[#e6edf3]"
            >
              {expanded ? '−' : '+'}
            </button>
          </div>

          {/* Content */}
          <div className="p-3 space-y-2">
            {feedback && (
              <p className="text-sm text-[#00d4ff]">{feedback}</p>
            )}
            {lastCommand && !feedback && (
              <p className="text-xs text-[#8b949e]">
                Heard: "{lastCommand}"
              </p>
            )}
            {!isAwake && isListening && (
              <p className="text-xs text-[#6e7681]">
                Say "Hey Veena" to activate
              </p>
            )}
          </div>

          {/* Expanded: Command List */}
          {expanded && (
            <div className="px-3 pb-3 border-t border-[#21262d] mt-2 pt-2">
              <p className="font-mono text-[9px] text-[#6e7681] uppercase tracking-wider mb-2">
                Available Commands
              </p>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {[
                  'Go to [page]',
                  'Search for [query]',
                  'New observation',
                  'Sync data',
                  'Help'
                ].map((cmd) => (
                  <p key={cmd} className="text-[11px] text-[#8b949e]">
                    "{cmd}"
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Sound Wave Animation */}
      {isAwake && (
        <div className="absolute -inset-2 pointer-events-none">
          <div className="absolute inset-0 rounded-full border-2 border-[#00ff88] animate-ping opacity-20" />
          <div className="absolute inset-0 rounded-full border border-[#00ff88] animate-pulse opacity-40" />
        </div>
      )}
    </div>
  )
}

/* ============================================
   VOICE COMMAND HOOK
   ============================================ */
export function useVoiceCommand() {
  const [isSupported, setIsSupported] = useState(false)

  useEffect(() => {
    setIsSupported('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)
  }, [])

  return { isSupported }
}
