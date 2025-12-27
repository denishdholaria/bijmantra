/**
 * Field Mode Hook
 * 
 * Manages field mode state for outdoor/sunlight usage.
 * Features: high contrast, large touch targets, simplified UI.
 */

import { useState, useEffect, useCallback } from 'react';

export interface FieldModeSettings {
  enabled: boolean;
  highContrast: boolean;
  largeText: boolean;
  hapticFeedback: boolean;
  autoDetect: boolean;
}

const DEFAULT_SETTINGS: FieldModeSettings = {
  enabled: false,
  highContrast: true,
  largeText: true,
  hapticFeedback: true,
  autoDetect: false,
};

const STORAGE_KEY = 'bijmantra-field-mode';

export function useFieldMode() {
  const [settings, setSettings] = useState<FieldModeSettings>(() => {
    if (typeof window === 'undefined') return DEFAULT_SETTINGS;
    
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        return { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
      } catch {
        return DEFAULT_SETTINGS;
      }
    }
    return DEFAULT_SETTINGS;
  });

  // Apply field mode class to document
  useEffect(() => {
    const root = document.documentElement;
    
    if (settings.enabled) {
      root.classList.add('field-mode');
      if (settings.highContrast) {
        root.classList.add('field-mode-contrast');
      }
      if (settings.largeText) {
        root.classList.add('field-mode-large');
      }
    } else {
      root.classList.remove('field-mode', 'field-mode-contrast', 'field-mode-large');
    }
  }, [settings]);

  // Persist settings
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  }, [settings]);

  // Auto-detect based on ambient light (if available)
  useEffect(() => {
    if (!settings.autoDetect) return;
    
    if ('AmbientLightSensor' in window) {
      try {
        // @ts-ignore - AmbientLightSensor is not in TypeScript types
        const sensor = new AmbientLightSensor();
        sensor.addEventListener('reading', () => {
          // High illuminance (>10000 lux) suggests outdoor sunlight
          const isOutdoor = sensor.illuminance > 10000;
          if (isOutdoor !== settings.enabled) {
            setSettings(prev => ({ ...prev, enabled: isOutdoor }));
          }
        });
        sensor.start();
        return () => sensor.stop();
      } catch {
        // Sensor not available
      }
    }
  }, [settings.autoDetect]);

  const toggleFieldMode = useCallback(() => {
    setSettings(prev => ({ ...prev, enabled: !prev.enabled }));
    
    // Haptic feedback on toggle
    if (settings.hapticFeedback && 'vibrate' in navigator) {
      navigator.vibrate(50);
    }
  }, [settings.hapticFeedback]);

  const updateSettings = useCallback((updates: Partial<FieldModeSettings>) => {
    setSettings(prev => ({ ...prev, ...updates }));
  }, []);

  const triggerHaptic = useCallback((pattern: number | number[] = 50) => {
    if (settings.enabled && settings.hapticFeedback && 'vibrate' in navigator) {
      navigator.vibrate(pattern);
    }
  }, [settings.enabled, settings.hapticFeedback]);

  return {
    ...settings,
    isFieldMode: settings.enabled,
    toggleFieldMode,
    updateSettings,
    triggerHaptic,
  };
}

/**
 * Simple hook to check if field mode is active
 */
export function useIsFieldMode(): boolean {
  const [isFieldMode, setIsFieldMode] = useState(false);

  useEffect(() => {
    const checkFieldMode = () => {
      setIsFieldMode(document.documentElement.classList.contains('field-mode'));
    };

    checkFieldMode();
    
    const observer = new MutationObserver(checkFieldMode);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class'],
    });

    return () => observer.disconnect();
  }, []);

  return isFieldMode;
}
