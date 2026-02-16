import * as React from 'react';
import { Check, ChevronsUpDown, Search, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';

export interface SearchableSelectOption {
  value: string;
  label: string;
  description?: string;
  disabled?: boolean;
  group?: string;
}

interface SearchableSelectProps {
  options: SearchableSelectOption[];
  value?: string | string[];
  onChange?: (value: string | string[]) => void;
  placeholder?: string;
  searchPlaceholder?: string;
  emptyMessage?: string;
  multiple?: boolean;
  disabled?: boolean;
  className?: string;
  maxHeight?: number;
}

export function SearchableSelect({
  options,
  value,
  onChange,
  placeholder = 'Select...',
  searchPlaceholder = 'Search...',
  emptyMessage = 'No results found.',
  multiple = false,
  disabled = false,
  className,
  maxHeight = 300,
}: SearchableSelectProps) {
  const [open, setOpen] = React.useState(false);
  const [search, setSearch] = React.useState('');

  const selectedValues = React.useMemo(() => {
    if (!value) return [];
    return Array.isArray(value) ? value : [value];
  }, [value]);

  const filteredOptions = React.useMemo(() => {
    if (!search) return options;
    const lower = search.toLowerCase();
    return options.filter(
      (opt) =>
        opt.label.toLowerCase().includes(lower) ||
        opt.description?.toLowerCase().includes(lower)
    );
  }, [options, search]);

  const groupedOptions = React.useMemo(() => {
    const groups: Record<string, SearchableSelectOption[]> = {};
    filteredOptions.forEach((opt) => {
      const group = opt.group || '';
      if (!groups[group]) groups[group] = [];
      groups[group].push(opt);
    });
    return groups;
  }, [filteredOptions]);

  const handleSelect = (optValue: string) => {
    if (multiple) {
      const newValues = selectedValues.includes(optValue)
        ? selectedValues.filter((v) => v !== optValue)
        : [...selectedValues, optValue];
      onChange?.(newValues);
    } else {
      onChange?.(optValue);
      setOpen(false);
    }
  };

  const handleRemove = (optValue: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (multiple) {
      onChange?.(selectedValues.filter((v) => v !== optValue));
    } else {
      onChange?.('');
    }
  };

  const getLabel = (val: string) => {
    return options.find((opt) => opt.value === val)?.label || val;
  };

  const displayValue = () => {
    if (selectedValues.length === 0) {
      return <span className="text-muted-foreground">{placeholder}</span>;
    }

    if (multiple) {
      return (
        <div className="flex flex-wrap gap-1">
          {selectedValues.slice(0, 3).map((val) => (
            <Badge key={val} variant="secondary" className="text-xs">
              {getLabel(val)}
              <button
                type="button"
                className="ml-1 hover:text-destructive"
                onClick={(e) => handleRemove(val, e)}
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
          {selectedValues.length > 3 && (
            <Badge variant="outline" className="text-xs">
              +{selectedValues.length - 3} more
            </Badge>
          )}
        </div>
      );
    }

    return getLabel(selectedValues[0]);
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          disabled={disabled}
          className={cn(
            'w-full justify-between font-normal',
            !selectedValues.length && 'text-muted-foreground',
            className
          )}
        >
          <div className="flex-1 text-left truncate">{displayValue()}</div>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-full p-0" align="start">
        <div className="flex items-center border-b px-3">
          <Search className="mr-2 h-4 w-4 shrink-0 opacity-50" />
          <Input
            placeholder={searchPlaceholder}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="border-0 focus-visible:ring-0 focus-visible:ring-offset-0"
          />
          {search && (
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              onClick={() => setSearch('')}
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
        <ScrollArea style={{ maxHeight }}>
          {filteredOptions.length === 0 ? (
            <div className="py-6 text-center text-sm text-muted-foreground">
              {emptyMessage}
            </div>
          ) : (
            <div className="p-1">
              {Object.entries(groupedOptions).map(([group, opts]) => (
                <div key={group}>
                  {group && (
                    <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
                      {group}
                    </div>
                  )}
                  {opts.map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      disabled={opt.disabled}
                      onClick={() => handleSelect(opt.value)}
                      className={cn(
                        'relative flex w-full cursor-pointer select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none',
                        'hover:bg-accent hover:text-accent-foreground',
                        'focus:bg-accent focus:text-accent-foreground',
                        opt.disabled && 'opacity-50 cursor-not-allowed',
                        selectedValues.includes(opt.value) && 'bg-accent/50'
                      )}
                    >
                      <span
                        className={cn(
                          'absolute left-2 flex h-3.5 w-3.5 items-center justify-center',
                          !selectedValues.includes(opt.value) && 'opacity-0'
                        )}
                      >
                        <Check className="h-4 w-4" />
                      </span>
                      <div className="flex flex-col items-start">
                        <span>{opt.label}</span>
                        {opt.description && (
                          <span className="text-xs text-muted-foreground">
                            {opt.description}
                          </span>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </PopoverContent>
    </Popover>
  );
}

export default SearchableSelect;
