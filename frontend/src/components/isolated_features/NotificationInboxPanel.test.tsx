import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { NotificationInboxPanel } from './NotificationInboxPanel';
import { useNotifications } from '@/components/notifications/NotificationSystem';

import { LEGACY_REEVU_NOTIFICATION_TYPE } from '@/lib/legacyReevu';

// Mock the useNotifications hook
vi.mock('@/components/notifications/NotificationSystem', () => ({
  useNotifications: vi.fn(),
}));

// Mock the legacyReevu module
vi.mock('@/lib/legacyReevu', () => ({
  LEGACY_REEVU_NOTIFICATION_TYPE: 'reevu-legacy-type'
}));

describe('NotificationInboxPanel', () => {
  const mockNotifications = [
    {
      id: '1',
      type: 'info',
      title: 'Test Notification',
      message: 'This is a test message',
      timestamp: new Date(),
      read: false,
      source: 'System'
    },
    {
      id: '2',
      type: LEGACY_REEVU_NOTIFICATION_TYPE,
      title: 'AI Insight',
      message: 'REEVU has found something',
      timestamp: new Date(),
      read: false,
      source: 'REEVU'
    }
  ];

  const mockMarkAsRead = vi.fn();
  const mockMarkAllAsRead = vi.fn();
  const mockClearNotification = vi.fn();
  const mockAddNotification = vi.fn();
  const mockClearAll = vi.fn();
  const mockUpdatePreferences = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useNotifications).mockReturnValue({
      notifications: mockNotifications,
      unreadCount: 2,
      preferences: {
        pushEnabled: true,
        emailEnabled: false,
        soundEnabled: true,
        categories: {
          [LEGACY_REEVU_NOTIFICATION_TYPE]: true,
          collaboration: true,
          data: true,
          weather: true,
          system: true,
        },
      },
      addNotification: mockAddNotification,
      markAsRead: mockMarkAsRead,
      markAllAsRead: mockMarkAllAsRead,
      clearNotification: mockClearNotification,
      clearAll: mockClearAll,
      updatePreferences: mockUpdatePreferences,
    } as ReturnType<typeof useNotifications>);
  });

  it('renders the component with notifications', () => {
    render(<NotificationInboxPanel />);

    expect(screen.getByText('Notifications')).toBeInTheDocument();
    expect(screen.getByText('Test Notification')).toBeInTheDocument();
    expect(screen.getByText('AI Insight')).toBeInTheDocument();
    expect(screen.getByText('REEVU INSIGHT')).toBeInTheDocument();
  });

  it('filters notifications by search query', () => {
    render(<NotificationInboxPanel />);

    const searchInput = screen.getByPlaceholderText('Search notifications...');
    fireEvent.change(searchInput, { target: { value: 'AI Insight' } });

    expect(screen.getByText('AI Insight')).toBeInTheDocument();
    expect(screen.queryByText('Test Notification')).not.toBeInTheDocument();
  });

  it('calls markAllAsRead when the button is clicked', () => {
    render(<NotificationInboxPanel />);

    const markAllReadBtn = screen.getByLabelText('Mark all as read');
    fireEvent.click(markAllReadBtn);

    expect(mockMarkAllAsRead).toHaveBeenCalled();
  });

  it('calls markAsRead when a notification is clicked', () => {
    render(<NotificationInboxPanel />);

    const notificationItem = screen.getByText('Test Notification');
    fireEvent.click(notificationItem);

    expect(mockMarkAsRead).toHaveBeenCalledWith('1');
  });

  it('displays empty state when no notifications match filters', () => {
    render(<NotificationInboxPanel />);

    const searchInput = screen.getByPlaceholderText('Search notifications...');
    fireEvent.change(searchInput, { target: { value: 'non-existent' } });

    expect(screen.getByText('No notifications found')).toBeInTheDocument();
  });
});
