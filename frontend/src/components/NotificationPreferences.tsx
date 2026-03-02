/**
 * Notification Preferences Component
 * 
 * Comprehensive notification settings with categories,
 * delivery methods, and quiet hours configuration.
 */

import { useState, useEffect } from 'react';
import { Bell, Mail, Smartphone, Volume2, Moon, Clock, Check } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';

interface NotificationCategory {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  email: boolean;
  push: boolean;
  inApp: boolean;
}

interface QuietHours {
  enabled: boolean;
  start: string;
  end: string;
  days: string[];
}

interface NotificationPreferencesProps {
  onSave?: (preferences: NotificationPreferencesData) => void;
  initialData?: Partial<NotificationPreferencesData>;
}

export interface NotificationPreferencesData {
  categories: NotificationCategory[];
  quietHours: QuietHours;
  soundEnabled: boolean;
  vibrationEnabled: boolean;
  badgeEnabled: boolean;
}

const DEFAULT_CATEGORIES: NotificationCategory[] = [
  {
    id: 'trials',
    name: 'Trial Updates',
    description: 'New observations, status changes, completions',
    icon: <Bell className="h-4 w-4" />,
    email: true,
    push: true,
    inApp: true,
  },
  {
    id: 'germplasm',
    name: 'Germplasm Alerts',
    description: 'Low stock, viability tests due, new accessions',
    icon: <Bell className="h-4 w-4" />,
    email: true,
    push: true,
    inApp: true,
  },
  {
    id: 'quality',
    name: 'Quality Control',
    description: 'Test results, certificate expiry, failures',
    icon: <Bell className="h-4 w-4" />,
    email: true,
    push: true,
    inApp: true,
  },
  {
    id: 'dispatch',
    name: 'Dispatch & Logistics',
    description: 'Order status, shipping updates, deliveries',
    icon: <Bell className="h-4 w-4" />,
    email: true,
    push: false,
    inApp: true,
  },
  {
    id: 'system',
    name: 'System Notifications',
    description: 'Maintenance, updates, security alerts',
    icon: <Bell className="h-4 w-4" />,
    email: true,
    push: false,
    inApp: true,
  },
  {
    id: 'collaboration',
    name: 'Collaboration',
    description: 'Comments, mentions, shared items',
    icon: <Bell className="h-4 w-4" />,
    email: false,
    push: true,
    inApp: true,
  },
];

const DEFAULT_QUIET_HOURS: QuietHours = {
  enabled: false,
  start: '22:00',
  end: '07:00',
  days: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
};

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

const STORAGE_KEY = 'bijmantra-notification-preferences';

export function NotificationPreferences({ onSave, initialData }: NotificationPreferencesProps) {
  const [categories, setCategories] = useState<NotificationCategory[]>(
    initialData?.categories || DEFAULT_CATEGORIES
  );
  const [quietHours, setQuietHours] = useState<QuietHours>(
    initialData?.quietHours || DEFAULT_QUIET_HOURS
  );
  const [soundEnabled, setSoundEnabled] = useState(initialData?.soundEnabled ?? true);
  const [vibrationEnabled, setVibrationEnabled] = useState(initialData?.vibrationEnabled ?? true);
  const [badgeEnabled, setBadgeEnabled] = useState(initialData?.badgeEnabled ?? true);
  const [hasChanges, setHasChanges] = useState(false);

  // Load from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored && !initialData) {
      try {
        const data = JSON.parse(stored);
        if (data.categories) setCategories(data.categories);
        if (data.quietHours) setQuietHours(data.quietHours);
        if (data.soundEnabled !== undefined) setSoundEnabled(data.soundEnabled);
        if (data.vibrationEnabled !== undefined) setVibrationEnabled(data.vibrationEnabled);
        if (data.badgeEnabled !== undefined) setBadgeEnabled(data.badgeEnabled);
      } catch {
        // Ignore parse errors
      }
    }
  }, [initialData]);

  const updateCategory = (id: string, field: 'email' | 'push' | 'inApp', value: boolean) => {
    setCategories(prev =>
      prev.map(cat => (cat.id === id ? { ...cat, [field]: value } : cat))
    );
    setHasChanges(true);
  };

  const toggleAllForMethod = (method: 'email' | 'push' | 'inApp', value: boolean) => {
    setCategories(prev => prev.map(cat => ({ ...cat, [method]: value })));
    setHasChanges(true);
  };

  const toggleQuietHoursDay = (day: string) => {
    setQuietHours(prev => ({
      ...prev,
      days: prev.days.includes(day)
        ? prev.days.filter(d => d !== day)
        : [...prev.days, day],
    }));
    setHasChanges(true);
  };

  const handleSave = () => {
    const data: NotificationPreferencesData = {
      categories,
      quietHours,
      soundEnabled,
      vibrationEnabled,
      badgeEnabled,
    };

    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    onSave?.(data);
    setHasChanges(false);
    toast.success('Notification preferences saved');
  };

  const allEmailEnabled = categories.every(c => c.email);
  const allPushEnabled = categories.every(c => c.push);
  const allInAppEnabled = categories.every(c => c.inApp);

  return (
    <div className="space-y-6">
      {/* Delivery Methods Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            Notification Channels
          </CardTitle>
          <CardDescription>Choose how you want to receive notifications</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-muted-foreground" />
                <span className="font-medium">Email</span>
              </div>
              <Switch
                checked={allEmailEnabled}
                onCheckedChange={(v) => toggleAllForMethod('email', v)}
              />
            </div>
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center gap-2">
                <Smartphone className="h-4 w-4 text-muted-foreground" />
                <span className="font-medium">Push</span>
              </div>
              <Switch
                checked={allPushEnabled}
                onCheckedChange={(v) => toggleAllForMethod('push', v)}
              />
            </div>
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center gap-2">
                <Bell className="h-4 w-4 text-muted-foreground" />
                <span className="font-medium">In-App</span>
              </div>
              <Switch
                checked={allInAppEnabled}
                onCheckedChange={(v) => toggleAllForMethod('inApp', v)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Category Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Notification Categories</CardTitle>
          <CardDescription>Fine-tune notifications for each category</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Header */}
            <div className="grid grid-cols-[1fr,80px,80px,80px] gap-4 text-sm font-medium text-muted-foreground">
              <div>Category</div>
              <div className="text-center">Email</div>
              <div className="text-center">Push</div>
              <div className="text-center">In-App</div>
            </div>
            
            <Separator />

            {/* Categories */}
            {categories.map((category) => (
              <div
                key={category.id}
                className="grid grid-cols-[1fr,80px,80px,80px] gap-4 items-center py-2"
              >
                <div>
                  <p className="font-medium">{category.name}</p>
                  <p className="text-sm text-muted-foreground">{category.description}</p>
                </div>
                <div className="flex justify-center">
                  <Switch
                    checked={category.email}
                    onCheckedChange={(v) => updateCategory(category.id, 'email', v)}
                  />
                </div>
                <div className="flex justify-center">
                  <Switch
                    checked={category.push}
                    onCheckedChange={(v) => updateCategory(category.id, 'push', v)}
                  />
                </div>
                <div className="flex justify-center">
                  <Switch
                    checked={category.inApp}
                    onCheckedChange={(v) => updateCategory(category.id, 'inApp', v)}
                  />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Sound & Vibration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Volume2 className="h-5 w-5" />
            Sound & Feedback
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label>Notification Sounds</Label>
              <p className="text-sm text-muted-foreground">Play sound for notifications</p>
            </div>
            <Switch
              checked={soundEnabled}
              onCheckedChange={(v) => { setSoundEnabled(v); setHasChanges(true); }}
            />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <Label>Vibration</Label>
              <p className="text-sm text-muted-foreground">Vibrate on mobile devices</p>
            </div>
            <Switch
              checked={vibrationEnabled}
              onCheckedChange={(v) => { setVibrationEnabled(v); setHasChanges(true); }}
            />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <Label>Badge Count</Label>
              <p className="text-sm text-muted-foreground">Show unread count on app icon</p>
            </div>
            <Switch
              checked={badgeEnabled}
              onCheckedChange={(v) => { setBadgeEnabled(v); setHasChanges(true); }}
            />
          </div>
        </CardContent>
      </Card>

      {/* Quiet Hours */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Moon className="h-5 w-5" />
            Quiet Hours
          </CardTitle>
          <CardDescription>Pause notifications during specific times</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label>Enable Quiet Hours</Label>
              <p className="text-sm text-muted-foreground">Mute notifications during set times</p>
            </div>
            <Switch
              checked={quietHours.enabled}
              onCheckedChange={(v) => {
                setQuietHours(prev => ({ ...prev, enabled: v }));
                setHasChanges(true);
              }}
            />
          </div>

          {quietHours.enabled && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    Start Time
                  </Label>
                  <Select
                    value={quietHours.start}
                    onValueChange={(v) => {
                      setQuietHours(prev => ({ ...prev, start: v }));
                      setHasChanges(true);
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Array.from({ length: 24 }, (_, i) => {
                        const hour = i.toString().padStart(2, '0');
                        return (
                          <SelectItem key={hour} value={`${hour}:00`}>
                            {hour}:00
                          </SelectItem>
                        );
                      })}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    End Time
                  </Label>
                  <Select
                    value={quietHours.end}
                    onValueChange={(v) => {
                      setQuietHours(prev => ({ ...prev, end: v }));
                      setHasChanges(true);
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Array.from({ length: 24 }, (_, i) => {
                        const hour = i.toString().padStart(2, '0');
                        return (
                          <SelectItem key={hour} value={`${hour}:00`}>
                            {hour}:00
                          </SelectItem>
                        );
                      })}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Active Days</Label>
                <div className="flex gap-2">
                  {DAYS.map((day) => (
                    <Button
                      key={day}
                      variant={quietHours.days.includes(day) ? 'default' : 'outline'}
                      size="sm"
                      className="w-10"
                      onClick={() => toggleQuietHoursDay(day)}
                    >
                      {day.slice(0, 1)}
                    </Button>
                  ))}
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={!hasChanges}>
          <Check className="h-4 w-4 mr-2" />
          Save Preferences
        </Button>
      </div>
    </div>
  );
}

// Hook for accessing notification preferences
export function useNotificationPreferences() {
  const [preferences, setPreferences] = useState<NotificationPreferencesData | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setPreferences(JSON.parse(stored));
      } catch {
        // Ignore
      }
    }
  }, []);

  const shouldNotify = (categoryId: string, method: 'email' | 'push' | 'inApp'): boolean => {
    if (!preferences) return true;

    // Check quiet hours
    if (preferences.quietHours.enabled) {
      const now = new Date();
      const currentHour = now.getHours();
      const currentDay = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][now.getDay()];
      
      if (preferences.quietHours.days.includes(currentDay)) {
        const startHour = parseInt(preferences.quietHours.start.split(':')[0]);
        const endHour = parseInt(preferences.quietHours.end.split(':')[0]);
        
        if (startHour > endHour) {
          // Overnight quiet hours (e.g., 22:00 - 07:00)
          if (currentHour >= startHour || currentHour < endHour) {
            return false;
          }
        } else {
          // Same-day quiet hours
          if (currentHour >= startHour && currentHour < endHour) {
            return false;
          }
        }
      }
    }

    // Check category preference
    const category = preferences.categories.find(c => c.id === categoryId);
    if (category) {
      return category[method];
    }

    return true;
  };

  return {
    preferences,
    shouldNotify,
    soundEnabled: preferences?.soundEnabled ?? true,
    vibrationEnabled: preferences?.vibrationEnabled ?? true,
    badgeEnabled: preferences?.badgeEnabled ?? true,
  };
}
