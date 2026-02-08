import { useState, useEffect, useCallback, useRef } from 'react'
import { logger } from '@/lib/logger'

interface UseVeenaVoiceProps {
  onTranscript?: (transcript: string) => void
  lang?: string
}

export function useVeenaVoice({ onTranscript, lang = 'en-US' }: UseVeenaVoiceProps = {}) {
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSupported, setIsSupported] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  
  const recognitionRef = useRef<any>(null)
  const synthRef = useRef<SpeechSynthesis | null>(null)

  // Initialize Speech Recognition
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const Recognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
      if (Recognition) {
        setIsSupported(true)
        const recognition = new Recognition()
        recognition.continuous = false // Stop after one sentence/command
        recognition.interimResults = true
        recognition.lang = lang

        recognition.onstart = () => {
          setIsListening(true)
          setError(null)
        }

        recognition.onend = () => {
          setIsListening(false)
        }

        recognition.onerror = (event: any) => {
          logger.error('Speech recognition error', new Error(event.error))
          setError(event.error)
          setIsListening(false)
        }

        recognition.onresult = (event: any) => {
          let interimTranscript = ''
          let finalTranscript = ''

          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              finalTranscript += event.results[i][0].transcript
            } else {
              interimTranscript += event.results[i][0].transcript
            }
          }

          if (finalTranscript) {
            setTranscript(finalTranscript)
            if (onTranscript) {
              onTranscript(finalTranscript)
            }
          } else {
            setTranscript(interimTranscript)
          }
        }

        recognitionRef.current = recognition
      }

      if ('speechSynthesis' in window) {
        synthRef.current = window.speechSynthesis
      }
    }
  }, [lang, onTranscript])

  const startListening = useCallback(() => {
    if (recognitionRef.current && !isListening) {
      try {
        setTranscript('')
        recognitionRef.current.start()
      } catch (e) {
        logger.error('Start listening failed', e as Error)
      }
    }
  }, [isListening])

  const stopListening = useCallback(() => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop()
    }
  }, [isListening])

  const speak = useCallback((text: string) => {
    if (synthRef.current) {
      // Cancel previous speech
      synthRef.current.cancel()

      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = lang
      
      // Try to find a good voice
      const voices = synthRef.current.getVoices()
      const preferredVoice = voices.find(v => v.name.includes('Google') || v.name.includes('Samantha') || v.name.includes('Natural'))
      if (preferredVoice) {
        utterance.voice = preferredVoice
      }

      utterance.onstart = () => setIsSpeaking(true)
      utterance.onend = () => setIsSpeaking(false)
      utterance.onerror = () => setIsSpeaking(false)

      synthRef.current.speak(utterance)
    }
  }, [lang])

  const stopSpeaking = useCallback(() => {
    if (synthRef.current) {
      synthRef.current.cancel()
      setIsSpeaking(false)
    }
  }, [])

  return {
    isListening,
    transcript,
    error,
    isSupported,
    startListening,
    stopListening,
    isSpeaking,
    speak,
    stopSpeaking
  }
}
