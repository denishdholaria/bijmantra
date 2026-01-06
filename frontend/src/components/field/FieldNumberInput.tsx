/**
 * Field Number Input
 * 
 * Large touch-friendly number input with +/- buttons for field data collection.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Minus, Plus } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useFieldMode } from '@/hooks/useFieldMode';

interface FieldNumberInputProps {
  value: number | null;
  onChange: (value: number | null) => void;
  label?: string;
  unit?: string;
  min?: number;
  max?: number;
  step?: number;
  precision?: number;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  className?: string;
  autoFocus?: boolean;
}

export function FieldNumberInput({
  value,
  onChange,
  label,
  unit,
  min,
  max,
  step = 1,
  precision = 1,
  placeholder = '0',
  disabled = false,
  required = false,
  className,
  autoFocus = false,
}: FieldNumberInputProps) {
  const { isFieldMode, triggerHaptic } = useFieldMode();
  const inputRef = useRef<HTMLInputElement>(null);
  const [localValue, setLocalValue] = useState(value?.toString() ?? '');
  const longPressTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const repeatTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  // Sync local value with prop
  useEffect(() => {
    setLocalValue(value?.toString() ?? '');
  }, [value]);

  // Auto focus
  useEffect(() => {
    if (autoFocus && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [autoFocus]);

  const clampValue = useCallback((val: number): number => {
    if (min !== undefined && val < min) return min;
    if (max !== undefined && val > max) return max;
    return val;
  }, [min, max]);

  const handleIncrement = useCallback(() => {
    const current = value ?? 0;
    const newValue = clampValue(Number((current + step).toFixed(precision)));
    onChange(newValue);
    triggerHaptic(30);
  }, [value, step, precision, clampValue, onChange, triggerHaptic]);

  const handleDecrement = useCallback(() => {
    const current = value ?? 0;
    const newValue = clampValue(Number((current - step).toFixed(precision)));
    onChange(newValue);
    triggerHaptic(30);
  }, [value, step, precision, clampValue, onChange, triggerHaptic]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const inputValue = e.target.value;
    setLocalValue(inputValue);

    if (inputValue === '' || inputValue === '-') {
      onChange(null);
      return;
    }

    const parsed = parseFloat(inputValue);
    if (!isNaN(parsed)) {
      onChange(clampValue(parsed));
    }
  }, [onChange, clampValue]);

  const handleBlur = useCallback(() => {
    if (localValue === '' || localValue === '-') {
      setLocalValue(value?.toString() ?? '');
    }
  }, [localValue, value]);

  // Long press for continuous increment/decrement
  const startLongPress = useCallback((action: 'increment' | 'decrement') => {
    const handler = action === 'increment' ? handleIncrement : handleDecrement;
    
    longPressTimer.current = setTimeout(() => {
      repeatTimer.current = setInterval(handler, 100);
    }, 500);
  }, [handleIncrement, handleDecrement]);

  const stopLongPress = useCallback(() => {
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
    if (repeatTimer.current) {
      clearInterval(repeatTimer.current);
      repeatTimer.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopLongPress();
    };
  }, [stopLongPress]);

  const buttonSize = isFieldMode ? 'h-14 w-14' : 'h-10 w-10';
  const inputSize = isFieldMode ? 'h-14 text-2xl' : 'h-10 text-lg';
  const iconSize = isFieldMode ? 'h-6 w-6' : 'h-5 w-5';

  return (
    <div className={cn('space-y-2', className)}>
      {label && (
        <Label className={cn('block', isFieldMode && 'text-lg font-semibold')}>
          {label}
          {required && <span className="text-destructive ml-1">*</span>}
        </Label>
      )}
      
      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant="outline"
          size="icon"
          className={cn(buttonSize, 'shrink-0 rounded-lg')}
          onClick={handleDecrement}
          onMouseDown={() => startLongPress('decrement')}
          onMouseUp={stopLongPress}
          onMouseLeave={stopLongPress}
          onTouchStart={() => startLongPress('decrement')}
          onTouchEnd={stopLongPress}
          disabled={disabled || (min !== undefined && (value ?? 0) <= min)}
        >
          <Minus className={iconSize} />
        </Button>

        <div className="relative flex-1">
          <Input
            ref={inputRef}
            type="text"
            inputMode="decimal"
            value={localValue}
            onChange={handleInputChange}
            onBlur={handleBlur}
            placeholder={placeholder}
            disabled={disabled}
            className={cn(
              inputSize,
              'text-center font-mono font-semibold',
              unit && 'pr-12'
            )}
          />
          {unit && (
            <span className={cn(
              'absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground',
              isFieldMode ? 'text-lg' : 'text-sm'
            )}>
              {unit}
            </span>
          )}
        </div>

        <Button
          type="button"
          variant="outline"
          size="icon"
          className={cn(buttonSize, 'shrink-0 rounded-lg')}
          onClick={handleIncrement}
          onMouseDown={() => startLongPress('increment')}
          onMouseUp={stopLongPress}
          onMouseLeave={stopLongPress}
          onTouchStart={() => startLongPress('increment')}
          onTouchEnd={stopLongPress}
          disabled={disabled || (max !== undefined && (value ?? 0) >= max)}
        >
          <Plus className={iconSize} />
        </Button>
      </div>

      {(min !== undefined || max !== undefined) && (
        <p className={cn(
          'text-muted-foreground',
          isFieldMode ? 'text-sm' : 'text-xs'
        )}>
          Range: {min ?? '−∞'} to {max ?? '∞'}
        </p>
      )}
    </div>
  );
}

export default FieldNumberInput;
