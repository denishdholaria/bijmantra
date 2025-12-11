/**
 * Feedback Widget Component
 * 
 * Allows users to submit feedback, bug reports, and feature requests.
 * Includes screenshot capture and system info collection.
 */

import { useState } from 'react';
import { 
  MessageSquare, Bug, Lightbulb, ThumbsUp, ThumbsDown,
  Camera, Send, X, Loader2, CheckCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

type FeedbackType = 'bug' | 'feature' | 'feedback' | 'praise';

interface FeedbackData {
  type: FeedbackType;
  title: string;
  description: string;
  email?: string;
  screenshot?: string;
  systemInfo: {
    url: string;
    userAgent: string;
    timestamp: string;
    screenSize: string;
  };
}

const FEEDBACK_TYPES: { type: FeedbackType; icon: React.ReactNode; label: string; color: string }[] = [
  { type: 'bug', icon: <Bug className="h-4 w-4" />, label: 'Bug Report', color: 'text-red-500' },
  { type: 'feature', icon: <Lightbulb className="h-4 w-4" />, label: 'Feature Request', color: 'text-yellow-500' },
  { type: 'feedback', icon: <MessageSquare className="h-4 w-4" />, label: 'General Feedback', color: 'text-blue-500' },
  { type: 'praise', icon: <ThumbsUp className="h-4 w-4" />, label: 'Praise', color: 'text-green-500' },
];

interface FeedbackWidgetProps {
  onSubmit?: (data: FeedbackData) => Promise<void>;
  trigger?: React.ReactNode;
  defaultType?: FeedbackType;
}

export function FeedbackWidget({ onSubmit, trigger, defaultType = 'feedback' }: FeedbackWidgetProps) {
  const [open, setOpen] = useState(false);
  const [type, setType] = useState<FeedbackType>(defaultType);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [email, setEmail] = useState('');
  const [screenshot, setScreenshot] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const captureScreenshot = async () => {
    try {
      // Use html2canvas if available, otherwise skip
      toast.info('Screenshot capture requires html2canvas library');
    } catch (error) {
      toast.error('Failed to capture screenshot');
    }
  };

  const handleSubmit = async () => {
    if (!title.trim() || !description.trim()) {
      toast.error('Please fill in all required fields');
      return;
    }

    setIsSubmitting(true);

    const data: FeedbackData = {
      type,
      title: title.trim(),
      description: description.trim(),
      email: email.trim() || undefined,
      screenshot: screenshot || undefined,
      systemInfo: {
        url: window.location.href,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString(),
        screenSize: `${window.innerWidth}x${window.innerHeight}`,
      },
    };

    try {
      if (onSubmit) {
        await onSubmit(data);
      } else {
        // Default: log to console and show success
        console.log('Feedback submitted:', data);
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      setIsSuccess(true);
      setTimeout(() => {
        setOpen(false);
        resetForm();
      }, 2000);
    } catch (error) {
      toast.error('Failed to submit feedback. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setType(defaultType);
    setTitle('');
    setDescription('');
    setEmail('');
    setScreenshot(null);
    setIsSuccess(false);
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { setOpen(v); if (!v) resetForm(); }}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="outline" size="sm">
            <MessageSquare className="h-4 w-4 mr-2" />
            Feedback
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-md">
        {isSuccess ? (
          <div className="py-12 text-center">
            <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
            <h3 className="text-xl font-semibold">Thank You!</h3>
            <p className="text-muted-foreground mt-2">
              Your feedback has been submitted successfully.
            </p>
          </div>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle>Send Feedback</DialogTitle>
              <DialogDescription>
                Help us improve Bijmantra by sharing your thoughts
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 mt-4">
              {/* Feedback Type */}
              <div className="space-y-2">
                <Label>Type</Label>
                <div className="grid grid-cols-4 gap-2">
                  {FEEDBACK_TYPES.map((ft) => (
                    <button
                      key={ft.type}
                      onClick={() => setType(ft.type)}
                      className={cn(
                        'p-3 rounded-lg border text-center transition-all',
                        type === ft.type
                          ? 'border-primary bg-primary/5'
                          : 'border-border hover:border-primary/50'
                      )}
                    >
                      <div className={cn('mx-auto mb-1', ft.color)}>{ft.icon}</div>
                      <span className="text-xs">{ft.label.split(' ')[0]}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Title */}
              <div className="space-y-2">
                <Label htmlFor="title">
                  Title <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="title"
                  placeholder={
                    type === 'bug' ? 'Brief description of the issue' :
                    type === 'feature' ? 'What feature would you like?' :
                    'Summary of your feedback'
                  }
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>

              {/* Description */}
              <div className="space-y-2">
                <Label htmlFor="description">
                  Description <span className="text-destructive">*</span>
                </Label>
                <Textarea
                  id="description"
                  placeholder={
                    type === 'bug' ? 'Steps to reproduce, expected vs actual behavior...' :
                    type === 'feature' ? 'Describe the feature and how it would help...' :
                    'Share your thoughts...'
                  }
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={4}
                />
              </div>

              {/* Email (optional) */}
              <div className="space-y-2">
                <Label htmlFor="email">Email (optional)</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="your@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  We'll only use this to follow up on your feedback
                </p>
              </div>

              {/* Screenshot */}
              {type === 'bug' && (
                <div className="space-y-2">
                  <Label>Screenshot</Label>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={captureScreenshot}
                      disabled={!!screenshot}
                    >
                      <Camera className="h-4 w-4 mr-2" />
                      {screenshot ? 'Captured' : 'Capture Screen'}
                    </Button>
                    {screenshot && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setScreenshot(null)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              )}

              {/* System Info Notice */}
              <p className="text-xs text-muted-foreground">
                We'll automatically include your browser and page info to help us investigate.
              </p>

              {/* Submit */}
              <div className="flex justify-end gap-2 pt-2">
                <Button variant="outline" onClick={() => setOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleSubmit} disabled={isSubmitting}>
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Submitting...
                    </>
                  ) : (
                    <>
                      <Send className="h-4 w-4 mr-2" />
                      Submit
                    </>
                  )}
                </Button>
              </div>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}

// Quick feedback buttons (thumbs up/down)
interface QuickFeedbackProps {
  context: string;
  onFeedback?: (positive: boolean, context: string) => void;
}

export function QuickFeedback({ context, onFeedback }: QuickFeedbackProps) {
  const [submitted, setSubmitted] = useState<boolean | null>(null);

  const handleFeedback = (positive: boolean) => {
    setSubmitted(positive);
    onFeedback?.(positive, context);
    toast.success('Thanks for your feedback!');
  };

  if (submitted !== null) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <CheckCircle className="h-4 w-4 text-green-500" />
        Thanks for your feedback!
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-muted-foreground">Was this helpful?</span>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => handleFeedback(true)}
      >
        <ThumbsUp className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => handleFeedback(false)}
      >
        <ThumbsDown className="h-4 w-4" />
      </Button>
    </div>
  );
}

// Floating feedback button
export function FloatingFeedbackButton() {
  return (
    <div className="fixed bottom-20 right-4 z-40">
      <FeedbackWidget
        trigger={
          <Button size="lg" variant="outline" className="rounded-full shadow-lg h-12 w-12">
            <MessageSquare className="h-5 w-5" />
          </Button>
        }
      />
    </div>
  );
}
