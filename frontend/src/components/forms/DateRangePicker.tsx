import * as React from 'react';
import { format, subDays, startOfMonth, endOfMonth, startOfYear } from 'date-fns';
import { Calendar, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export interface DateRange {
  from: Date | undefined;
  to: Date | undefined;
}

interface DateRangePickerProps {
  value?: DateRange;
  onChange?: (range: DateRange) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  presets?: boolean;
}

const defaultPresets = [
  { label: 'Today', getValue: () => ({ from: new Date(), to: new Date() }) },
  {
    label: 'Last 7 days',
    getValue: () => ({ from: subDays(new Date(), 7), to: new Date() }),
  },
  {
    label: 'Last 30 days',
    getValue: () => ({ from: subDays(new Date(), 30), to: new Date() }),
  },
  {
    label: 'Last 90 days',
    getValue: () => ({ from: subDays(new Date(), 90), to: new Date() }),
  },
  {
    label: 'This month',
    getValue: () => ({
      from: startOfMonth(new Date()),
      to: endOfMonth(new Date()),
    }),
  },
  {
    label: 'This year',
    getValue: () => ({ from: startOfYear(new Date()), to: new Date() }),
  },
];

export function DateRangePicker({
  value,
  onChange,
  placeholder = 'Select date range',
  disabled = false,
  className,
  presets = true,
}: DateRangePickerProps) {
  const [open, setOpen] = React.useState(false);
  const [fromDate, setFromDate] = React.useState(
    value?.from ? format(value.from, 'yyyy-MM-dd') : ''
  );
  const [toDate, setToDate] = React.useState(
    value?.to ? format(value.to, 'yyyy-MM-dd') : ''
  );

  React.useEffect(() => {
    setFromDate(value?.from ? format(value.from, 'yyyy-MM-dd') : '');
    setToDate(value?.to ? format(value.to, 'yyyy-MM-dd') : '');
  }, [value]);

  const handleApply = () => {
    const from = fromDate ? new Date(fromDate) : undefined;
    const to = toDate ? new Date(toDate) : undefined;
    onChange?.({ from, to });
    setOpen(false);
  };

  const handlePreset = (preset: (typeof defaultPresets)[0]) => {
    const range = preset.getValue();
    setFromDate(format(range.from, 'yyyy-MM-dd'));
    setToDate(format(range.to, 'yyyy-MM-dd'));
    onChange?.(range);
    setOpen(false);
  };

  const handleClear = () => {
    setFromDate('');
    setToDate('');
    onChange?.({ from: undefined, to: undefined });
    setOpen(false);
  };

  const displayValue = () => {
    if (!value?.from && !value?.to) {
      return placeholder;
    }
    if (value.from && value.to) {
      return `${format(value.from, 'MMM d, yyyy')} - ${format(value.to, 'MMM d, yyyy')}`;
    }
    if (value.from) {
      return `From ${format(value.from, 'MMM d, yyyy')}`;
    }
    if (value.to) {
      return `Until ${format(value.to, 'MMM d, yyyy')}`;
    }
    return placeholder;
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          disabled={disabled}
          className={cn(
            'w-full justify-between font-normal',
            !value?.from && !value?.to && 'text-muted-foreground',
            className
          )}
        >
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            <span>{displayValue()}</span>
          </div>
          <ChevronDown className="h-4 w-4 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <div className="flex">
          {presets && (
            <div className="border-r p-2 space-y-1">
              <p className="text-xs font-medium text-muted-foreground px-2 py-1">
                Quick Select
              </p>
              {defaultPresets.map((preset) => (
                <Button
                  key={preset.label}
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start text-sm"
                  onClick={() => handlePreset(preset)}
                >
                  {preset.label}
                </Button>
              ))}
            </div>
          )}
          <div className="p-4 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="from-date">From</Label>
                <Input
                  id="from-date"
                  type="date"
                  value={fromDate}
                  onChange={(e) => setFromDate(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="to-date">To</Label>
                <Input
                  id="to-date"
                  type="date"
                  value={toDate}
                  onChange={(e) => setToDate(e.target.value)}
                />
              </div>
            </div>
            <div className="flex justify-between">
              <Button variant="ghost" size="sm" onClick={handleClear}>
                Clear
              </Button>
              <Button size="sm" onClick={handleApply}>
                Apply
              </Button>
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}

export default DateRangePicker;
