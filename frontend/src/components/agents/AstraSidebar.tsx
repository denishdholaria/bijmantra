/**
 * ASTRA (आस्त्र) — Agent Arsenal Sidebar
 * 
 * A unified right-side sidebar housing all AI agents.
 * Mirrors the Mahasarthi design language with reversed diagonal edge.
 * 
 * Features:
 * - Collapsed dock showing agent icons
 * - Expanded panel with agent selection and chat
 * - Central orchestrator (Veena) with specialist delegation
 * - Registry-driven: new agents auto-appear
 * - Keyboard shortcut: Ctrl+. to toggle
 */

import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from '@/lib/utils';
import { 
  ChevronLeft, 
  ChevronRight, 
  Settings, 
  Trash2, 
  Maximize2, 
  Sprout,
  Mountain,
  Wind,
  TrendingUp,
  Swords,
  Crown,
  FlaskConical,
  Send
} from 'lucide-react';
import { AgentDefinition, AgentMessage } from './types';
import { useAgentArsenal } from './useAgentArsenal';
import { VeenaLogo } from '@/components/ai/VeenaTrigger';

// ============================================================================
// Constants
// ============================================================================

const SIDEBAR_WIDTH_OPEN = 420;
const SIDEBAR_WIDTH_COLLAPSED = 56;
const SLASH_OFFSET = 40;

// Lucide icon mapping
const LUCIDE_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  Sprout,
  Mountain,
  Wind,
  TrendingUp,
  Swords,
  FlaskConical,
};

// ============================================================================
// Sub-Components
// ============================================================================

/**
 * Agent Icon Button — Used in collapsed dock
 */
function AgentIconButton({
  agent,
  isActive,
  isProcessing,
  onClick,
}: {
  agent: AgentDefinition;
  isActive: boolean;
  isProcessing: boolean;
  onClick: () => void;
}) {
  const colorMap: Record<string, string> = {
    emerald: 'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 border-emerald-500/30',
    cyan: 'bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/30 border-cyan-500/30',
    amber: 'bg-amber-500/20 text-amber-400 hover:bg-amber-500/30 border-amber-500/30',
    sky: 'bg-sky-500/20 text-sky-400 hover:bg-sky-500/30 border-sky-500/30',
    violet: 'bg-violet-500/20 text-violet-400 hover:bg-violet-500/30 border-violet-500/30',
  };

  const activeColorMap: Record<string, string> = {
    emerald: 'bg-emerald-500 text-white border-emerald-400',
    cyan: 'bg-cyan-500 text-white border-cyan-400',
    amber: 'bg-amber-500 text-white border-amber-400',
    sky: 'bg-sky-500 text-white border-sky-400',
    violet: 'bg-violet-500 text-white border-violet-400',
  };

  // Render the appropriate icon
  const renderIcon = () => {
    if (agent.icon === 'veena-logo') {
      return <VeenaLogo className="w-5 h-5" />;
    }
    const IconComponent = LUCIDE_ICONS[agent.icon];
    if (IconComponent) {
      return <IconComponent className="w-4 h-4" />;
    }
    // Fallback to first letter
    return <span className="text-xs font-bold">{agent.shortName[0]}</span>;
  };

  return (
    <button
      onClick={onClick}
      className={cn(
        'relative w-9 h-9 rounded-lg flex items-center justify-center border',
        'transition-all duration-200',
        'focus:outline-none focus:ring-2 focus:ring-white/30',
        isActive ? activeColorMap[agent.color] : colorMap[agent.color]
      )}
      title={`${agent.name}${agent.isExperimental ? ' (Beta)' : ''}${agent.isOrchestrator ? ' (Main)' : ''}`}
      aria-label={`Switch to ${agent.name} agent`}
    >
      {renderIcon()}
      
      {/* Processing indicator */}
      {isProcessing && (
        <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
      )}
      
      {/* Experimental badge - bottom right dot */}
      {agent.isExperimental && !isActive && (
        <span className="absolute -bottom-0.5 -right-0.5 w-2 h-2 bg-orange-500 rounded-full" />
      )}
    </button>
  );
}

/**
 * Agent Selector — Horizontal tabs when expanded
 */
function AgentSelector({
  agents,
  activeAgentId,
  agentStates,
  onSelect,
}: {
  agents: AgentDefinition[];
  activeAgentId: string;
  agentStates: Record<string, { isProcessing: boolean }>;
  onSelect: (id: string) => void;
}) {
  const renderIcon = (agent: AgentDefinition) => {
    if (agent.icon === 'veena-logo') {
      return <VeenaLogo className="w-4 h-4" />;
    }
    const IconComponent = LUCIDE_ICONS[agent.icon];
    if (IconComponent) {
      return <IconComponent className="w-3.5 h-3.5" />;
    }
    return <span className="text-[10px] font-bold">{agent.shortName[0]}</span>;
  };

  return (
    <div className="flex gap-1 p-2 overflow-x-auto scrollbar-thin scrollbar-thumb-white/20 border-b border-white/10">
      {agents.map(agent => (
        <button
          key={agent.id}
          onClick={() => onSelect(agent.id)}
          className={cn(
            'flex items-center gap-1.5 px-2 py-1.5 rounded-lg whitespace-nowrap flex-shrink-0',
            'transition-all duration-200 text-xs',
            activeAgentId === agent.id
              ? 'bg-white/20 text-white border border-white/30'
              : 'bg-white/5 text-slate-400 hover:bg-white/10 border border-transparent'
          )}
        >
          {renderIcon(agent)}
          <span className="font-medium">{agent.name}</span>
          {agent.isExperimental && (
            <span className="text-[8px] px-1 py-0.5 bg-orange-500/40 text-orange-200 rounded font-bold">β</span>
          )}
          {agentStates[agent.id]?.isProcessing && (
            <span className="w-1.5 h-1.5 bg-yellow-400 rounded-full animate-pulse" />
          )}
        </button>
      ))}
    </div>
  );
}

/**
 * Message Bubble
 */
function MessageBubble({ message, agentColor }: { message: AgentMessage; agentColor: string }) {
  const isUser = message.role === 'user';

  const colorMap: Record<string, string> = {
    emerald: 'from-emerald-500 to-teal-600',
    cyan: 'from-cyan-500 to-blue-600',
    amber: 'from-amber-500 to-orange-600',
    sky: 'from-sky-500 to-blue-600',
    violet: 'from-violet-500 to-purple-600',
  };

  return (
    <div className={cn('flex', isUser ? 'justify-end' : 'justify-start')}>
      <div className={cn(
        'max-w-[85%] rounded-2xl px-4 py-3',
        isUser
          ? `bg-gradient-to-br ${colorMap[agentColor]} text-white shadow-md`
          : 'bg-slate-700/50 text-slate-100 shadow-sm border border-slate-600/50'
      )}>
        {isUser ? (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="text-sm leading-relaxed prose prose-invert prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>
        )}
        
        {/* Metadata */}
        {!isUser && message.metadata?.provider && (
          <p className="text-[9px] opacity-60 mt-2">
            via {message.metadata.provider}
            {message.metadata.model ? ` • ${message.metadata.model}` : ''}
          </p>
        )}
        
        <span className={cn('text-[9px] block mt-1', isUser ? 'opacity-70' : 'text-slate-500')}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function AstraSidebar() {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [input, setInput] = useState('');

  const {
    isOpen,
    setIsOpen,
    activeAgent,
    setActiveAgent,
    agents,
    agentStates,
    messages,
    sendMessage,
    clearSession,
    isProcessing,
  } = useAgentArsenal();

  // Keyboard shortcut: Ctrl+. to toggle
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === '.') {
        e.preventDefault();
        setIsOpen(!isOpen);
      }
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, setIsOpen]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [isOpen]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (input.trim()) {
      sendMessage(input);
      setInput('');
    }
  };

  const effectiveWidth = isOpen ? SIDEBAR_WIDTH_OPEN : SIDEBAR_WIDTH_COLLAPSED;

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed top-0 right-0 h-full z-50 flex flex-col',
          'transition-all duration-300 ease-out'
        )}
        style={{ width: effectiveWidth }}
      >
        {/* SVG Background with Reversed Slashed Edge */}
        <svg
          viewBox={`0 0 ${effectiveWidth + 10} 1000`}
          preserveAspectRatio="none"
          className="absolute inset-0 h-full transition-all duration-300 pointer-events-none"
          style={{ width: effectiveWidth + 10, left: -10 }}
          aria-hidden="true"
        >
          <defs>
            {/* Main gradient - slightly different from left sidebar */}
            <linearGradient id="astraGradient" x1="100%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#0f172a" />
              <stop offset="40%" stopColor="#1e293b" />
              <stop offset="100%" stopColor="#0f172a" />
            </linearGradient>
            
            {/* Edge glow - amber/gold theme for agents */}
            <linearGradient id="astraEdgeGlow" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.1" />
              <stop offset="30%" stopColor="#f59e0b" stopOpacity="0.7" />
              <stop offset="50%" stopColor="#fbbf24" stopOpacity="0.9" />
              <stop offset="70%" stopColor="#f59e0b" stopOpacity="0.7" />
              <stop offset="100%" stopColor="#f59e0b" stopOpacity="0.1" />
            </linearGradient>
          </defs>
          
          {/* Main shape - reversed slash (goes other way) */}
          <path 
            d={`M10 0 L${effectiveWidth + 10} 0 L${effectiveWidth + 10} 1000 L${isOpen ? SLASH_OFFSET + 10 : 10} 1000 Z`}
            fill="url(#astraGradient)"
            className="transition-all duration-300"
          />
          
          {/* Glowing edge */}
          <path 
            d={`M10 0 L${isOpen ? SLASH_OFFSET + 10 : 10} 1000`}
            stroke="url(#astraEdgeGlow)"
            strokeWidth="3"
            fill="none"
            className="transition-all duration-300"
          />
        </svg>

        {/* Content */}
        <div className="relative z-10 h-full flex flex-col text-slate-200">
          {/* Header */}
          <div className={cn(
            'h-14 flex items-center border-b border-white/10 flex-shrink-0',
            isOpen ? 'px-4 justify-between' : 'justify-center'
          )}>
            {isOpen ? (
              <>
                <div className="flex items-center gap-2">
                  <Swords className="w-5 h-5 text-amber-400" />
                  <div>
                    <h2 className="text-sm font-semibold text-white">ASTRA</h2>
                    <p className="text-[10px] text-slate-400">Agent Arsenal</p>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => navigate('/ai-settings')}
                    className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                    title="AI Settings"
                    aria-label="Open AI Settings"
                  >
                    <Settings className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setIsOpen(false)}
                    className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                    title="Collapse (Esc)"
                    aria-label="Collapse sidebar"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </>
            ) : (
              <button
                onClick={() => setIsOpen(true)}
                className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                title="Expand Agent Arsenal (Ctrl+.)"
                aria-label="Expand Agent Arsenal"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Agent Dock (collapsed) or Selector (expanded) */}
          {isOpen ? (
            <AgentSelector
              agents={agents}
              activeAgentId={activeAgent.id}
              agentStates={agentStates}
              onSelect={setActiveAgent}
            />
          ) : (
            <div className="flex flex-col items-center gap-2 py-3 border-b border-white/10">
              {agents.map(agent => (
                <AgentIconButton
                  key={agent.id}
                  agent={agent}
                  isActive={activeAgent.id === agent.id}
                  isProcessing={agentStates[agent.id]?.isProcessing || false}
                  onClick={() => {
                    setActiveAgent(agent.id);
                    setIsOpen(true);
                  }}
                />
              ))}
            </div>
          )}

          {/* Active Agent Info (expanded only) */}
          {isOpen && (
            <div className="px-3 py-2 border-b border-white/10 bg-white/5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 min-w-0">
                  <div className="w-7 h-7 flex-shrink-0 flex items-center justify-center">
                    {activeAgent.icon === 'veena-logo' ? (
                      <VeenaLogo className="w-7 h-7" />
                    ) : LUCIDE_ICONS[activeAgent.icon] ? (
                      (() => {
                        const Icon = LUCIDE_ICONS[activeAgent.icon];
                        return <Icon className="w-4 h-4" />;
                      })()
                    ) : (
                      <span className="text-sm font-bold">{activeAgent.shortName[0]}</span>
                    )}
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="font-medium text-white text-sm">{activeAgent.name}</span>
                      {activeAgent.isOrchestrator && (
                        <span className="text-[8px] px-1 py-0.5 bg-amber-500/30 text-amber-300 rounded flex items-center gap-0.5">
                          <Crown className="w-2 h-2" /> Main
                        </span>
                      )}
                      {activeAgent.isExperimental && (
                        <span className="text-[8px] px-1 py-0.5 bg-orange-500/30 text-orange-300 rounded">
                          Beta
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex gap-0.5 flex-shrink-0">
                  <button
                    onClick={() => clearSession(activeAgent.id)}
                    className="p-1.5 hover:bg-white/10 rounded transition-colors"
                    title="Clear conversation"
                    aria-label="Clear conversation"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => navigate(`/${activeAgent.id}`)}
                    className="p-1.5 hover:bg-white/10 rounded transition-colors"
                    title="Open full page"
                    aria-label="Open full page"
                  >
                    <Maximize2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Messages (expanded only) */}
          {isOpen && (
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 ? (
                <div className="text-center py-8 text-slate-400">
                  <div className="w-16 h-16 mx-auto mb-3 flex items-center justify-center">
                    {activeAgent.icon === 'veena-logo' ? (
                      <VeenaLogo className="w-16 h-16 opacity-50" />
                    ) : LUCIDE_ICONS[activeAgent.icon] ? (
                      (() => {
                        const Icon = LUCIDE_ICONS[activeAgent.icon];
                        return <Icon className="w-12 h-12 opacity-50" />;
                      })()
                    ) : (
                      <span className="text-4xl font-bold opacity-50">{activeAgent.shortName}</span>
                    )}
                  </div>
                  <p className="text-sm font-medium">Ask {activeAgent.name}</p>
                  <p className="text-xs mt-1 text-slate-500">{activeAgent.description}</p>
                  {activeAgent.domains && (
                    <div className="flex flex-wrap justify-center gap-1 mt-3">
                      {activeAgent.domains.map(domain => (
                        <span key={domain} className="text-[9px] px-2 py-0.5 bg-white/10 rounded-full">
                          {domain}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                messages.map(msg => (
                  <MessageBubble key={msg.id} message={msg} agentColor={activeAgent.color} />
                ))
              )}
              {isProcessing && (
                <div className="flex items-center gap-2 text-slate-400">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-amber-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-amber-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-amber-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                  <span className="text-xs">{activeAgent.name} is thinking...</span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}

          {/* Input (expanded only) */}
          {isOpen && (
            <div className="p-4 border-t border-white/10">
              <div className="flex items-center gap-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                  placeholder={`Ask ${activeAgent.name}...`}
                  className="flex-1 bg-white/10 border border-white/20 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                />
                <button
                  onClick={handleSend}
                  disabled={!input.trim() || isProcessing}
                  className={cn(
                    'p-2.5 rounded-xl transition-all',
                    input.trim() && !isProcessing
                      ? 'bg-amber-500 text-white hover:bg-amber-600 shadow-md'
                      : 'bg-white/10 text-slate-500 cursor-not-allowed'
                  )}
                  aria-label="Send message"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
              <p className="text-[9px] text-slate-500 mt-2 text-center">
                Ctrl+. to toggle • Esc to close
              </p>
            </div>
          )}

          {/* Footer (collapsed only) */}
          {!isOpen && (
            <div className="mt-auto p-2 border-t border-white/10">
              <button
                onClick={() => setIsOpen(true)}
                className="w-full p-2 text-amber-400 hover:bg-white/10 rounded-lg transition-colors flex items-center justify-center"
                title="Open Agent Arsenal"
                aria-label="Open Agent Arsenal"
              >
                <Swords className="w-5 h-5" />
              </button>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}

export default AstraSidebar;
