/**
 * useAgentArsenal — State management hook for the Agent Arsenal
 * 
 * Manages:
 * - Active agent selection
 * - Agent sessions and message history
 * - Agent health status
 * - Sidebar open/collapsed state
 * 
 * Integrates with REEVU backend for the orchestrator agent.
 */

import { useState, useCallback, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { AgentDefinition, AgentMessage, AgentSession, AgentState } from './types';
import { AGENT_REGISTRY, getAgent, getOrchestrator } from './registry';
import { useAuthStore } from '@/store/auth';
import { useWorkspaceStore } from '@/store/workspaceStore';
import {
  getEffectiveReevuBackend,
  getReevuProviderDisplayName,
  requestReevuBackendStatus,
} from '@/lib/reevu-backend-status';
import {
  buildReevuChatStreamRequest,
  readReevuStreamEvents,
} from '@/lib/reevu-chat-stream';
import { useReevuTaskContextStore } from '@/store/reevuTaskContextStore';

interface UseAgentArsenalReturn {
  // Sidebar state
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
  
  // Agent selection
  activeAgentId: string;
  activeAgent: AgentDefinition;
  setActiveAgent: (id: string) => void;
  
  // All agents
  agents: AgentDefinition[];
  
  // Agent states (status, processing, etc.)
  agentStates: Record<string, AgentState>;
  
  // Sessions
  sessions: Record<string, AgentSession>;
  getSession: (agentId: string) => AgentSession;
  
  // Messaging
  sendMessage: (content: string) => Promise<void>;
  clearSession: (agentId: string) => void;
  
  // Current session messages
  messages: AgentMessage[];
  isProcessing: boolean;
}

const STORAGE_KEY = 'bijmantra_agent_arsenal';

interface StoredState {
  activeAgentId: string;
  sessions: Record<string, AgentSession>;
}

function loadStoredState(): StoredState | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      // Rehydrate dates
      Object.values(parsed.sessions || {}).forEach((session: any) => {
        session.startedAt = new Date(session.startedAt);
        session.lastActivity = new Date(session.lastActivity);
        session.messages?.forEach((msg: any) => {
          msg.timestamp = new Date(msg.timestamp);
        });
      });
      return parsed;
    }
  } catch (e) {
    console.warn('Failed to load agent arsenal state:', e);
  }
  return null;
}

function saveState(state: StoredState): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch (e) {
    console.warn('Failed to save agent arsenal state:', e);
  }
}

export function useAgentArsenal(): UseAgentArsenalReturn {
  const location = useLocation();
  const activeWorkspaceId = useWorkspaceStore(state => state.activeWorkspaceId);
  const routeTaskContextOverride = useReevuTaskContextStore(
    state => state.routeContexts[location.pathname],
  );
  const [isOpen, setIsOpen] = useState(false);
  
  // Load initial state
  const storedState = loadStoredState();
  const [activeAgentId, setActiveAgentId] = useState(
    storedState?.activeAgentId || getOrchestrator().id
  );
  const [sessions, setSessions] = useState<Record<string, AgentSession>>(
    storedState?.sessions || {}
  );
  const [agentStates, setAgentStates] = useState<Record<string, AgentState>>({});
  const [isProcessing, setIsProcessing] = useState(false);

  // Get active agent definition
  const activeAgent = getAgent(activeAgentId) || getOrchestrator();

  // Initialize agent states
  useEffect(() => {
    const states: Record<string, AgentState> = {};
    AGENT_REGISTRY.agents.forEach(agent => {
      states[agent.id] = {
        status: agent.requiresConfig && !agent.isOrchestrator ? 'configuring' : 'ready',
        isProcessing: false,
      };
    });
    setAgentStates(states);
  }, []);

  // Persist state changes
  useEffect(() => {
    saveState({ activeAgentId, sessions });
  }, [activeAgentId, sessions]);

  // Get or create session for an agent
  const getSession = useCallback((agentId: string): AgentSession => {
    if (sessions[agentId]) {
      return sessions[agentId];
    }
    const newSession: AgentSession = {
      agentId,
      messages: [],
      startedAt: new Date(),
      lastActivity: new Date(),
    };
    setSessions(prev => ({ ...prev, [agentId]: newSession }));
    return newSession;
  }, [sessions]);

  // Set active agent
  const setActiveAgent = useCallback((id: string) => {
    const agent = getAgent(id);
    if (agent) {
      setActiveAgentId(id);
      getSession(id); // Ensure session exists
    }
  }, [getSession]);

  // Clear session for an agent
  const clearSession = useCallback((agentId: string) => {
    setSessions(prev => {
      const newSessions = { ...prev };
      delete newSessions[agentId];
      return newSessions;
    });
  }, []);

  // Send message to active agent
  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isProcessing) return;

    const userMessage: AgentMessage = {
      id: `msg_${Date.now()}_user`,
      agentId: activeAgentId,
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    };

    // Add user message to session
    setSessions(prev => {
      const session = prev[activeAgentId] || {
        agentId: activeAgentId,
        messages: [],
        startedAt: new Date(),
        lastActivity: new Date(),
      };
      return {
        ...prev,
        [activeAgentId]: {
          ...session,
          messages: [...session.messages, userMessage],
          lastActivity: new Date(),
        },
      };
    });

    setIsProcessing(true);
    setAgentStates(prev => ({
      ...prev,
      [activeAgentId]: { ...prev[activeAgentId], isProcessing: true },
    }));

    // Create assistant message placeholder
    const assistantMsgId = `msg_${Date.now()}_assistant`;
    
    try {
      const agent = getAgent(activeAgentId);
      let metadata: AgentMessage['metadata'] = { provider: agent?.name };

      // Add placeholder assistant message
      setSessions(prev => ({
        ...prev,
        [activeAgentId]: {
          ...prev[activeAgentId],
          messages: [...prev[activeAgentId].messages, {
            id: assistantMsgId,
            agentId: activeAgentId,
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            metadata,
          }],
          lastActivity: new Date(),
        },
      }));

      if (agent?.endpoint) {
        // External agent (like REEVA) - non-streaming
        const res = await fetch(agent.endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: content }),
        });
        if (!res.ok) throw new Error(`Agent error: ${res.statusText}`);
        const data = await res.json();
        const response = data.response || data.message || 'No response';
        
        setSessions(prev => ({
          ...prev,
          [activeAgentId]: {
            ...prev[activeAgentId],
            messages: prev[activeAgentId].messages.map(msg =>
              msg.id === assistantMsgId
                ? { ...msg, content: response, metadata: { provider: agent.name, model: 'LangGraph ReAct' } }
                : msg
            ),
            lastActivity: new Date(),
          },
        }));
      } else if (agent?.isOrchestrator) {
        const token = useAuthStore.getState().token;
        if (!token) {
          throw new Error('Login required. Please sign in again to use REEVU.');
        }

        const reevuStatus = await requestReevuBackendStatus(fetch, token);
        if (reevuStatus.authRequired) {
          throw new Error('Session expired. Please sign in again to continue using REEVU.');
        }

        const effectiveBackend = getEffectiveReevuBackend(reevuStatus);
        if (!effectiveBackend.ready) {
          throw new Error('Managed REEVU backend is not AI-ready. Configure a server-side provider in AI Settings.');
        }

        const providerName = getReevuProviderDisplayName(reevuStatus.provider, 'Managed backend');

        const currentSession = sessions[activeAgentId];
        const conversationHistory = (currentSession?.messages || []).map(m => ({
          role: m.role,
          content: m.content,
        }));

        metadata = {
          provider: providerName,
          model: reevuStatus.model || 'auto',
        };

        const response = await fetch('/api/v2/chat/stream', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(buildReevuChatStreamRequest({
            message: content,
            messages: conversationHistory,
            pathname: location.pathname,
            search: location.search,
            activeWorkspaceId,
            routeTaskContextOverride,
          })),
        });

        if (!response.ok || !response.body) {
          const errorText = await response.text();
          throw new Error(`Chat error: ${response.status}${errorText ? ` - ${errorText}` : ''}`);
        }

        let fullResponse = '';
        for await (const event of readReevuStreamEvents(response.body)) {
          if (event.type === 'start') {
            metadata = {
              ...metadata,
              provider: event.provider || providerName,
              model: event.model || metadata?.model,
            };
          } else if (event.type === 'chunk') {
            fullResponse += event.content;
            setSessions(prev => ({
              ...prev,
              [activeAgentId]: {
                ...prev[activeAgentId],
                messages: prev[activeAgentId].messages.map(msg =>
                  msg.id === assistantMsgId
                    ? { ...msg, content: fullResponse, metadata }
                    : msg
                ),
              },
            }));
          } else if (event.type === 'proposal_created') {
            setSessions(prev => ({
              ...prev,
              [activeAgentId]: {
                ...prev[activeAgentId],
                messages: prev[activeAgentId].messages.map(msg =>
                  msg.id === assistantMsgId
                    ? { ...msg, metadata: { ...metadata, proposal: event.data } }
                    : msg
                ),
              },
            }));
          } else if (event.type === 'error') {
            throw new Error(event.message || 'Stream error');
          }
        }

        setSessions(prev => ({
          ...prev,
          [activeAgentId]: {
            ...prev[activeAgentId],
            messages: prev[activeAgentId].messages.map(msg =>
              msg.id === assistantMsgId
                ? { ...msg, content: fullResponse, metadata }
                : msg
            ),
            lastActivity: new Date(),
          },
        }));
      } else {
        // Agent not configured
        const notConfiguredMsg = agent?.isOrchestrator
          ? '⚠️ **Managed REEVU backend is not AI-ready**\n\nTo use REEVU, configure a server-side provider in **AI Settings**. Browser-side BYOK is no longer the canonical app path.'
          : `⚠️ **${agent?.name || 'Agent'} is not yet available**\n\nThis agent is planned for future development.`;
        
        setSessions(prev => ({
          ...prev,
          [activeAgentId]: {
            ...prev[activeAgentId],
            messages: prev[activeAgentId].messages.map(msg =>
              msg.id === assistantMsgId
                ? { ...msg, content: notConfiguredMsg, metadata: { provider: 'System' } }
                : msg
            ),
            lastActivity: new Date(),
          },
        }));
      }
    } catch (error) {
      const errorContent = `Error: ${error instanceof Error ? error.message : 'Unknown error'}`;
      setSessions(prev => ({
        ...prev,
        [activeAgentId]: {
          ...prev[activeAgentId],
          messages: prev[activeAgentId].messages.map(msg =>
            msg.id === assistantMsgId
              ? { ...msg, content: errorContent, metadata: { provider: activeAgent.name } }
              : msg
          ),
          lastActivity: new Date(),
        },
      }));
    } finally {
      setIsProcessing(false);
      setAgentStates(prev => ({
        ...prev,
        [activeAgentId]: { ...prev[activeAgentId], isProcessing: false },
      }));
    }
  }, [activeAgentId, activeAgent, isProcessing, sessions, location.pathname, location.search, activeWorkspaceId, routeTaskContextOverride]);

  // Current session messages
  const messages = sessions[activeAgentId]?.messages || [];

  return {
    isOpen,
    setIsOpen,
    activeAgentId,
    activeAgent,
    setActiveAgent,
    agents: AGENT_REGISTRY.agents,
    agentStates,
    sessions,
    getSession,
    sendMessage,
    clearSession,
    messages,
    isProcessing,
  };
}
