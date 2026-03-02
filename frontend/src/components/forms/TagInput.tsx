import * as React from 'react';
import { X, Plus } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

interface TagInputProps {
  value?: string[];
  onChange?: (tags: string[]) => void;
  placeholder?: string;
  disabled?: boolean;
  maxTags?: number;
  suggestions?: string[];
  allowCustom?: boolean;
  className?: string;
  variant?: 'default' | 'secondary' | 'outline';
}

export function TagInput({
  value = [],
  onChange,
  placeholder = 'Add tag...',
  disabled = false,
  maxTags,
  suggestions = [],
  allowCustom = true,
  className,
  variant = 'secondary',
}: TagInputProps) {
  const [input, setInput] = React.useState('');
  const [showSuggestions, setShowSuggestions] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const filteredSuggestions = React.useMemo(() => {
    if (!input) return suggestions.filter((s) => !value.includes(s));
    const lower = input.toLowerCase();
    return suggestions.filter(
      (s) => s.toLowerCase().includes(lower) && !value.includes(s)
    );
  }, [input, suggestions, value]);

  const addTag = (tag: string) => {
    const trimmed = tag.trim();
    if (!trimmed) return;
    if (value.includes(trimmed)) return;
    if (maxTags && value.length >= maxTags) return;

    onChange?.([...value, trimmed]);
    setInput('');
    setShowSuggestions(false);
  };

  const removeTag = (tag: string) => {
    onChange?.(value.filter((t) => t !== tag));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (allowCustom && input) {
        addTag(input);
      } else if (filteredSuggestions.length > 0) {
        addTag(filteredSuggestions[0]);
      }
    } else if (e.key === 'Backspace' && !input && value.length > 0) {
      removeTag(value[value.length - 1]);
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  const canAddMore = !maxTags || value.length < maxTags;

  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex flex-wrap gap-1.5">
        {value.map((tag) => (
          <Badge key={tag} variant={variant} className="gap-1 pr-1">
            {tag}
            {!disabled && (
              <button
                type="button"
                onClick={() => removeTag(tag)}
                className="ml-1 rounded-full hover:bg-background/20 p-0.5"
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </Badge>
        ))}
      </div>

      {canAddMore && !disabled && (
        <div className="relative">
          <div className="flex gap-2">
            <Input
              ref={inputRef}
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                setShowSuggestions(true);
              }}
              onFocus={() => setShowSuggestions(true)}
              onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              className="flex-1"
            />
            {allowCustom && input && (
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => addTag(input)}
              >
                <Plus className="h-4 w-4" />
              </Button>
            )}
          </div>

          {showSuggestions && filteredSuggestions.length > 0 && (
            <div className="absolute z-10 w-full mt-1 bg-popover border rounded-md shadow-md max-h-48 overflow-auto">
              {filteredSuggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  className="w-full px-3 py-2 text-left text-sm hover:bg-accent hover:text-accent-foreground"
                  onClick={() => addTag(suggestion)}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {maxTags && (
        <p className="text-xs text-muted-foreground">
          {value.length}/{maxTags} tags
        </p>
      )}
    </div>
  );
}

export default TagInput;
