/**
 * useTrialCreation Hook Unit Tests
 * Basic tests for trial creation hook
 */

import { describe, it, expect } from 'vitest';
import { renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useTrialCreation } from './useTrialCreation';
import type { ReactNode } from 'react';

describe('useTrialCreation', () => {
  const wrapper = ({ children }: { children: ReactNode }) => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };

  it('should initialize with empty state', () => {
    const { result } = renderHook(() => useTrialCreation(), { wrapper });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isEmpty).toBe(true);
    expect(result.current.error).toBe(null);
    expect(result.current.success).toBe(false);
    expect(result.current.createdTrialId).toBeUndefined();
  });

  it('should have createTrial function', () => {
    const { result } = renderHook(() => useTrialCreation(), { wrapper });

    expect(typeof result.current.createTrial).toBe('function');
  });

  it('should have resetState function', () => {
    const { result } = renderHook(() => useTrialCreation(), { wrapper });

    expect(typeof result.current.resetState).toBe('function');
  });
});
