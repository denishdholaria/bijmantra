import * as React from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Switch } from '@/components/ui/switch';
import { cn } from '@/lib/utils';
import { AlertCircle, HelpCircle } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

export interface FormFieldProps {
  name: string;
  label: string;
  type?:
    | 'text'
    | 'email'
    | 'password'
    | 'number'
    | 'date'
    | 'datetime-local'
    | 'textarea'
    | 'select'
    | 'checkbox'
    | 'switch'
    | 'file';
  value?: string | number | boolean;
  onChange?: (value: string | number | boolean) => void;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  error?: string;
  helpText?: string;
  options?: { value: string; label: string }[];
  min?: number;
  max?: number;
  step?: number;
  rows?: number;
  accept?: string;
  className?: string;
}

export function FormField({
  name,
  label,
  type = 'text',
  value,
  onChange,
  placeholder,
  required = false,
  disabled = false,
  error,
  helpText,
  options = [],
  min,
  max,
  step,
  rows = 3,
  accept,
  className,
}: FormFieldProps) {
  const id = `field-${name}`;

  const handleChange = (newValue: string | number | boolean) => {
    onChange?.(newValue);
  };

  const renderInput = () => {
    switch (type) {
      case 'textarea':
        return (
          <Textarea
            id={id}
            name={name}
            value={value as string}
            onChange={(e) => handleChange(e.target.value)}
            placeholder={placeholder}
            disabled={disabled}
            rows={rows}
            className={cn(error && 'border-red-500')}
          />
        );

      case 'select':
        return (
          <Select
            value={value as string}
            onValueChange={(v: string) => handleChange(v)}
            disabled={disabled}
          >
            <SelectTrigger className={cn(error && 'border-red-500')}>
              <SelectValue placeholder={placeholder || 'Select...'} />
            </SelectTrigger>
            <SelectContent>
              {options.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );

      case 'checkbox':
        return (
          <div className="flex items-center gap-2">
            <Checkbox
              id={id}
              checked={value as boolean}
              onCheckedChange={(checked) => handleChange(checked as boolean)}
              disabled={disabled}
            />
            <Label htmlFor={id} className="font-normal cursor-pointer">
              {label}
            </Label>
          </div>
        );

      case 'switch':
        return (
          <div className="flex items-center justify-between">
            <Label htmlFor={id} className="font-normal cursor-pointer">
              {label}
            </Label>
            <Switch
              id={id}
              checked={value as boolean}
              onCheckedChange={(checked) => handleChange(checked)}
              disabled={disabled}
            />
          </div>
        );

      default:
        return (
          <Input
            id={id}
            name={name}
            type={type}
            value={value as string | number}
            onChange={(e) =>
              handleChange(
                type === 'number' ? parseFloat(e.target.value) : e.target.value
              )
            }
            placeholder={placeholder}
            disabled={disabled}
            min={min}
            max={max}
            step={step}
            accept={accept}
            className={cn(error && 'border-red-500')}
          />
        );
    }
  };

  // Checkbox and switch have their own label rendering
  if (type === 'checkbox' || type === 'switch') {
    return (
      <div className={cn('space-y-1', className)}>
        {renderInput()}
        {error && (
          <p className="text-sm text-red-500 flex items-center gap-1">
            <AlertCircle className="h-3 w-3" />
            {error}
          </p>
        )}
        {helpText && !error && (
          <p className="text-sm text-muted-foreground">{helpText}</p>
        )}
      </div>
    );
  }

  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex items-center gap-1">
        <Label htmlFor={id}>
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </Label>
        {helpText && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent>
                <p className="max-w-xs">{helpText}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>
      {renderInput()}
      {error && (
        <p className="text-sm text-red-500 flex items-center gap-1">
          <AlertCircle className="h-3 w-3" />
          {error}
        </p>
      )}
    </div>
  );
}

export default FormField;
