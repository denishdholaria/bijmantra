/**
 * ASTRA (आस्त्र) — Agent Arsenal Type Definitions
 * 
 * Central type system for the Agent Arsenal sidebar.
 * Supports multiple specialized agents with a central orchestrator.
 */

export type AgentStatus = 'ready' | 'busy' | 'offline' | 'error' | 'configuring';

export type AgentCapability = 
  | 'chat'           // Can have conversations
  | 'query'          // Can query databases
  | 'analyze'        // Can analyze data
  | 'recommend'      // Can make recommendations
  | 'execute'        // Can execute actions (dangerous)
  | 'cross-domain';  // Can reason across domains

export interface AgentDefinition {
  id: string;
  name: string;
  shortName: string;           // 2-4 char abbreviation for collapsed view
  description: string;
  icon: string;                // Emoji or icon identifier
  color: string;               // Tailwind color class (e.g., 'emerald', 'amber')
  capabilities: AgentCapability[];
  endpoint?: string;           // API endpoint if external
  isOrchestrator?: boolean;    // True for the central coordinating agent
  isExperimental?: boolean;    // Show warning badge
  requiresConfig?: boolean;    // Needs API key setup
  domains?: string[];          // Agricultural domains this agent specializes in
}

export interface AgentMessage {
  id: string;
  agentId: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    provider?: string;
    model?: string;
    sources?: Array<{ doc_type: string; title?: string; doc_id: string }>;
    delegatedTo?: string;      // If orchestrator delegated to another agent
    confidence?: number;
    domains?: string[];
    proposal?: {
      id: number;
      title: string;
      status: string;
      description: string;
    };
  };
}

export interface AgentSession {
  agentId: string;
  messages: AgentMessage[];
  startedAt: Date;
  lastActivity: Date;
}

export interface AgentState {
  status: AgentStatus;
  isProcessing: boolean;
  error?: string;
  lastHealthCheck?: Date;
}

// Registry of all available agents
export interface AgentRegistry {
  agents: AgentDefinition[];
  orchestratorId: string;
  version: string;
}
