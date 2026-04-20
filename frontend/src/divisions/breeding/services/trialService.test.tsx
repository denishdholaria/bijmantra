/**
 * TrialService Unit Tests
 * Basic tests for trial service
 */

import { describe, it, expect } from 'vitest';
import { trialService } from './trialService';

describe('TrialService', () => {
  it('should have createTrial method', () => {
    expect(typeof trialService.createTrial).toBe('function');
  });

  it('should have getTrial method', () => {
    expect(typeof trialService.getTrial).toBe('function');
  });

  it('should have getTrials method', () => {
    expect(typeof trialService.getTrials).toBe('function');
  });
});
