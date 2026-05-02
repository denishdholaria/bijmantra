/**
 * ASTRA (आस्त्र) — Agent Arsenal
 * 
 * Unified agent management system for BijMantra.
 * Houses all AI agents with a central orchestrator.
 */

// Main sidebar component
export { AstraSidebar } from './AstraSidebar';
export { default } from './AstraSidebar';

// Types
export type {
  AgentDefinition,
  AgentMessage,
  AgentSession,
  AgentState,
  AgentStatus,
  AgentCapability,
  AgentRegistry,
} from './types';

// Registry
export {
  AGENT_REGISTRY,
  getAgent,
  getOrchestrator,
  getActiveAgents,
  getAgentsByDomain,
} from './registry';

// Hook
export { useAgentArsenal } from './useAgentArsenal';
