/**
 * Veena Voice Input Component
 *
 * Voice-to-text input for field data entry.
 * Uses Web Speech API with fallback messaging.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Mic, MicOff, Loader2, Volume2 } from 'lucide-react';

interface VeenaVoiceInputProps {
  onTranscript: (text: string) => void;
  onInterimTranscript?: (text: string) => void;
  placeholder?: string;
  className?: string;
  language?: string;
  continuous?: boolean;
  disabled?: boolean;
}

// Check for Web Speech API support
const SpeechRecognition =
  typeof window !== 'undefined'
    ? (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    : null;

export function VeenaVoiceInput({
  onTranscript,
  onInterimTranscript,
  placeholder = 'Click mic to speak...',
  className,
  language = 'en-US',
  continuous = false,
  disabled = false,
}: VeenaVoiceInputProps) {
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [interimText, setInterimText] = useState('');
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    setIsSupported(!!SpeechRecognition);
  }, []);

  const startListening = useCallback(() => {
    if (!SpeechRecognition || disabled) return;

    setError(null);
    setInterimText('');

    const recognition = new SpeechRecognition();
    recognition.continuous = continuous;
    recognition.interimResults = true;
    recognition.lang = language;

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event: any) => {
      let interim = '';
      let final = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += transcript;
        } else {
          interim += transcript;
        }
      }

      if (interim) {
        setInterimText(interim);
        onInterimTranscript?.(interim);
      }

      if (final) {
        setInterimText('');
        onTranscript(final.trim());
      }
    };

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      setError(event.error === 'not-allowed' 
        ? 'Microphone access denied' 
        : 'Speech recognition error');
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
      if (continuous && recognitionRef.current === recognition) {
        // Restart if continuous mode
        try {
          recognition.start();
        } catch {
          // Ignore restart errors
        }
      }
    };

    recognitionRef.current = recognition;
    
    try {
      recognition.start();
    } catch (err) {
      setError('Failed to start speech recognition');
    }
  }, [continuous, disabled, language, onInterimTranscript, onTranscript]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    setIsListening(false);
    setInterimText('');
  }, []);

  const toggleListening = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  if (!isSupported) {
    return (
      <div className={cn('flex items-center gap-2 text-muted-foreground text-sm', className)}>
        <MicOff className="h-4 w-4" />
        <span>Voice input not supported in this browser</span>
      </div>
    );
  }

  return (
    <div className={cn('flex items-center gap-3', className)}>
      <Button
        type="button"
        variant={isListening ? 'destructive' : 'outline'}
        size="icon"
        onClick={toggleListening}
        disabled={disabled}
        className={cn(
          'relative',
          isListening && 'animate-pulse'
        )}
      >
        {isListening ? (
          <Volume2 className="h-4 w-4" />
        ) : (
          <Mic className="h-4 w-4" />
        )}
        {isListening && (
          <span className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full animate-ping" />
        )}
      </Button>

      <div className="flex-1 min-w-0">
        {error ? (
          <p className="text-sm text-destructive">{error}</p>
        ) : isListening ? (
          <div className="flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            <p className="text-sm text-muted-foreground truncate">
              {interimText || 'Listening...'}
            </p>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">{placeholder}</p>
        )}
      </div>
    </div>
  );
}

export default VeenaVoiceInput;
