/**
 * Field Mode Toggle
 * 
 * Quick toggle for field mode with settings popover.
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Sun, SunDim, Settings2 } from 'lucide-react';
import { useFieldMode } from '@/hooks/useFieldMode';

interface FieldModeToggleProps {
  showSettings?: boolean;
  className?: string;
}

export function FieldModeToggle({ showSettings = true, className }: FieldModeToggleProps) {
  const {
    isFieldMode,
    highContrast,
    largeText,
    hapticFeedback,
    autoDetect,
    toggleFieldMode,
    updateSettings,
    triggerHaptic,
  } = useFieldMode();

  const [open, setOpen] = useState(false);

  const handleToggle = () => {
    toggleFieldMode();
    triggerHaptic();
  };

  if (!showSettings) {
    return (
      <Button
        variant={isFieldMode ? 'default' : 'outline'}
        size="sm"
        onClick={handleToggle}
        className={className}
        title={isFieldMode ? 'Disable Field Mode' : 'Enable Field Mode'}
      >
        {isFieldMode ? <Sun className="h-4 w-4" /> : <SunDim className="h-4 w-4" />}
        <span className="hidden sm:inline ml-1">
          {isFieldMode ? 'Field Mode' : 'Normal'}
        </span>
      </Button>
    );
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant={isFieldMode ? 'default' : 'outline'}
          size="sm"
          className={className}
        >
          {isFieldMode ? <Sun className="h-4 w-4" /> : <SunDim className="h-4 w-4" />}
          <span className="hidden sm:inline ml-1">
            {isFieldMode ? 'Field Mode' : 'Normal'}
          </span>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-72" align="end">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sun className="h-5 w-5 text-yellow-500" />
              <span className="font-medium">Field Mode</span>
            </div>
            <Switch
              checked={isFieldMode}
              onCheckedChange={toggleFieldMode}
            />
          </div>

          <p className="text-sm text-muted-foreground">
            Optimized for outdoor use with larger buttons and high contrast.
          </p>

          <div className="border-t pt-4 space-y-3">
            <div className="flex items-center justify-between">
              <Label htmlFor="high-contrast" className="text-sm">
                High Contrast
              </Label>
              <Switch
                id="high-contrast"
                checked={highContrast}
                onCheckedChange={(checked) => updateSettings({ highContrast: checked })}
                disabled={!isFieldMode}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="large-text" className="text-sm">
                Large Text
              </Label>
              <Switch
                id="large-text"
                checked={largeText}
                onCheckedChange={(checked) => updateSettings({ largeText: checked })}
                disabled={!isFieldMode}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="haptic" className="text-sm">
                Haptic Feedback
              </Label>
              <Switch
                id="haptic"
                checked={hapticFeedback}
                onCheckedChange={(checked) => updateSettings({ hapticFeedback: checked })}
                disabled={!isFieldMode}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="auto-detect" className="text-sm">
                Auto-detect Sunlight
              </Label>
              <Switch
                id="auto-detect"
                checked={autoDetect}
                onCheckedChange={(checked) => updateSettings({ autoDetect: checked })}
              />
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}

/**
 * Simple field mode indicator for status bars
 */
export function FieldModeIndicator() {
  const { isFieldMode } = useFieldMode();

  if (!isFieldMode) return null;

  return (
    <div className="flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 rounded text-xs font-medium">
      <Sun className="h-3 w-3" />
      Field Mode
    </div>
  );
}
