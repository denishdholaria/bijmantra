/**
 * useAgentArsenal — State management hook for the Agent Arsenal
 * 
 * Manages:
 * - Active agent selection
 * - Agent sessions and message history
 * - Agent health status
 * - Sidebar open/collapsed state
 * 
 * Integrates with Veena's backend for the orchestrator agent.
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { AgentDefinition, AgentMessage, AgentSession, AgentState } from './types';
import { AGENT_REGISTRY, getAgent, getOrchestrator } from './registry';

// AI Config storage key (shared with useVeenaChat)
const AI_CONFIG_KEY = 'bijmantra_ai_config_v2';

interface AIConfig {
  mode: 'cloud';
  cloud: { provider: string; apiKey: string; model: string; tested: boolean; lastTestResult?: 'success' | 'error' };
}

const PROVIDER_NAMES: Record<string, string> = {
  google: 'Google Gemini',
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  groq: 'Groq'
};

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
  const [aiConfig, setAiConfig] = useState<AIConfig | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Get active agent definition
  const activeAgent = getAgent(activeAgentId) || getOrchestrator();

  // Load AI config on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(AI_CONFIG_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed && parsed.cloud && typeof parsed.cloud === 'object') {
          setAiConfig({
            mode: 'cloud',
            cloud: {
              provider: parsed.cloud.provider || 'google',
              apiKey: parsed.cloud.apiKey || '',
              model: parsed.cloud.model || 'gemini-2.5-flash',
              tested: parsed.cloud.tested || false,
              lastTestResult: parsed.cloud.lastTestResult
            }
          });
        }
      }
    } catch (e) {
      console.warn('[ASTRA] Error loading AI config:', e);
    }
  }, []);

  // Initialize agent states
  useEffect(() => {
    const states: Record<string, AgentState> = {};
    AGENT_REGISTRY.agents.forEach(agent => {
      // Check if Veena (orchestrator) is configured
      const isConfigured = agent.isOrchestrator && aiConfig?.cloud?.apiKey && aiConfig.cloud.lastTestResult === 'success';
      states[agent.id] = {
        status: agent.requiresConfig && !isConfigured ? 'configuring' : 'ready',
        isProcessing: false,
      };
    });
    setAgentStates(states);
  }, [aiConfig]);

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
      } else if (agent?.isOrchestrator && aiConfig?.cloud?.apiKey) {
        // Veena (orchestrator) - use streaming backend
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const providerName = PROVIDER_NAMES[aiConfig.cloud.provider] || aiConfig.cloud.provider;
        
        // Get conversation history for context
        const currentSession = sessions[activeAgentId];
        const conversationHistory = (currentSession?.messages || []).slice(-10).map(m => ({
          role: m.role,
          content: m.content
        }));

        const response = await fetch(`${apiUrl}/api/v2/chat/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: content,
            conversation_history: conversationHistory,
            include_context: true,
            context_limit: 5,
            preferred_provider: aiConfig.cloud.provider,
            user_api_key: aiConfig.cloud.apiKey,
            user_model: aiConfig.cloud.model,
          }),
        });

        if (!response.ok || !response.body) {
          throw new Error('Network response was not ok');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullResponse = '';
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          buffer += chunk;
          
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed.startsWith('data: ')) continue;

            const dataStr = trimmed.slice(6);
            if (dataStr === '[DONE]') break;

            try {
              const data = JSON.parse(dataStr);
              
              if (data.type === 'start') {
                metadata = { provider: data.provider, model: data.model };
              } else if (data.type === 'chunk') {
                fullResponse += (data.content || '');
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
              } else if (data.type === 'error') {
                fullResponse += `\n[Error: ${data.message}]`;
              }
            } catch (e) {
              console.warn('[ASTRA] Error parsing SSE chunk:', e);
            }
          }
        }
      } else {
        // Agent not configured
        const notConfiguredMsg = agent?.isOrchestrator
          ? '⚠️ **AI not configured**\n\nTo use Veena, please configure an AI provider:\n\n1. Go to **Settings → AI Assistant Setup**\n2. Choose a provider (Google Gemini has a free tier)\n3. Enter your API key and test the connection'
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
  }, [activeAgentId, activeAgent, isProcessing, aiConfig, sessions]);

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
