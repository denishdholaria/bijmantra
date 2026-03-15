/**
 * Team Chat Component
 * Real-time messaging for breeding teams
 * 
 * Features:
 * - Direct messages
 * - Group channels
 * - @mentions
 * - File sharing
 * - REEVU AI integration
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import {
  LEGACY_REEVU_NOTIFICATION_TYPE,
  LEGACY_REEVU_ORCHESTRATOR_ID,
} from '@/lib/legacyReevu'
import { cn } from '@/lib/utils'
import { getUserColor, getInitials } from './RealtimePresence'

// Legacy IDs/types remain as `veena` for compatibility with stored/session data.
const LEGACY_REEVU_CHANNEL_ID = LEGACY_REEVU_ORCHESTRATOR_ID
const LEGACY_REEVU_USER_ID = LEGACY_REEVU_ORCHESTRATOR_ID
const LEGACY_REEVU_CHANNEL_TYPE = LEGACY_REEVU_NOTIFICATION_TYPE

// ============================================
// TYPES
// ============================================

interface User {
  id: string
  name: string
  email: string
  avatar?: string
  status: 'online' | 'away' | 'offline'
}

interface Message {
  id: string
  channelId: string
  userId: string
  userName: string
  userAvatar?: string
  content: string
  timestamp: Date
  type: 'text' | 'file' | 'system' | typeof LEGACY_REEVU_CHANNEL_TYPE
  mentions?: string[]
  reactions?: { emoji: string; users: string[] }[]
  attachments?: { name: string; url: string; type: string }[]
}

interface Channel {
  id: string
  name: string
  type: 'direct' | 'group' | 'trial' | typeof LEGACY_REEVU_CHANNEL_TYPE
  icon?: string
  members: string[]
  unreadCount: number
  lastMessage?: Message
}

// ============================================
// MESSAGE BUBBLE
// ============================================

interface MessageBubbleProps {
  message: Message
  isOwn: boolean
  showAvatar: boolean
}

function MessageBubble({ message, isOwn, showAvatar }: MessageBubbleProps) {
  const userColor = getUserColor(message.userId)

  return (
    <div className={cn(
      'flex gap-2 mb-3',
      isOwn ? 'flex-row-reverse' : 'flex-row'
    )}>
      {/* Avatar */}
      {showAvatar && !isOwn ? (
        <div
          className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium text-white flex-shrink-0"
          style={{ backgroundColor: userColor }}
        >
          {message.userAvatar ? (
            <img src={message.userAvatar} alt="" className="w-full h-full rounded-full" />
          ) : (
            getInitials(message.userName)
          )}
        </div>
      ) : (
        <div className="w-8 flex-shrink-0" />
      )}

      {/* Message Content */}
      <div className={cn(
        'max-w-[70%] rounded-2xl px-4 py-2',
        isOwn
          ? 'bg-amber-500 text-white rounded-br-md'
          : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white rounded-bl-md',
        message.type === LEGACY_REEVU_CHANNEL_TYPE && 'bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900/30 dark:to-orange-900/30 border border-amber-200 dark:border-amber-800'
      )}>
        {/* Sender name for group chats */}
        {!isOwn && showAvatar && (
          <div className="text-xs font-medium mb-1" style={{ color: userColor }}>
            {message.userName}
            {message.type === LEGACY_REEVU_CHANNEL_TYPE && ' 🪷'}
          </div>
        )}

        {/* Message text */}
        <p className="text-sm whitespace-pre-wrap break-words">
          {message.content}
        </p>

        {/* Attachments */}
        {message.attachments && message.attachments.length > 0 && (
          <div className="mt-2 space-y-1">
            {message.attachments.map((att, idx) => (
              <a
                key={idx}
                href={att.url}
                className="flex items-center gap-2 text-xs underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                📎 {att.name}
              </a>
            ))}
          </div>
        )}

        {/* Timestamp */}
        <div className={cn(
          'text-[10px] mt-1',
          isOwn ? 'text-white/70' : 'text-gray-500'
        )}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>

        {/* Reactions */}
        {message.reactions && message.reactions.length > 0 && (
          <div className="flex gap-1 mt-2">
            {message.reactions.map((reaction, idx) => (
              <span
                key={idx}
                className="text-xs bg-white/20 dark:bg-black/20 px-1.5 py-0.5 rounded-full"
              >
                {reaction.emoji} {reaction.users.length}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ============================================
// CHANNEL LIST
// ============================================

interface ChannelListProps {
  channels: Channel[]
  activeChannelId: string
  onSelectChannel: (channelId: string) => void
}

function ChannelList({ channels, activeChannelId, onSelectChannel }: ChannelListProps) {
  const groupedChannels = {
    direct: channels.filter(c => c.type === 'direct'),
    group: channels.filter(c => c.type === 'group'),
    trial: channels.filter(c => c.type === 'trial'),
    reevu: channels.filter(c => c.type === LEGACY_REEVU_CHANNEL_TYPE)
  }

  return (
    <div className="w-64 border-r border-gray-200 dark:border-gray-700 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <h2 className="font-semibold text-gray-900 dark:text-white">Messages</h2>
      </div>

      {/* Channel Groups */}
      <div className="flex-1 overflow-y-auto p-2">
        {/* REEVU AI */}
        {groupedChannels.reevu.length > 0 && (
          <div className="mb-4">
            <div className="text-xs font-medium text-gray-500 dark:text-gray-400 px-2 mb-1">
              🪷 AI ASSISTANT
            </div>
            {groupedChannels.reevu.map(channel => (
              <ChannelItem
                key={channel.id}
                channel={channel}
                isActive={channel.id === activeChannelId}
                onClick={() => onSelectChannel(channel.id)}
              />
            ))}
          </div>
        )}

        {/* Direct Messages */}
        {groupedChannels.direct.length > 0 && (
          <div className="mb-4">
            <div className="text-xs font-medium text-gray-500 dark:text-gray-400 px-2 mb-1">
              DIRECT MESSAGES
            </div>
            {groupedChannels.direct.map(channel => (
              <ChannelItem
                key={channel.id}
                channel={channel}
                isActive={channel.id === activeChannelId}
                onClick={() => onSelectChannel(channel.id)}
              />
            ))}
          </div>
        )}

        {/* Trial Channels */}
        {groupedChannels.trial.length > 0 && (
          <div className="mb-4">
            <div className="text-xs font-medium text-gray-500 dark:text-gray-400 px-2 mb-1">
              TRIALS
            </div>
            {groupedChannels.trial.map(channel => (
              <ChannelItem
                key={channel.id}
                channel={channel}
                isActive={channel.id === activeChannelId}
                onClick={() => onSelectChannel(channel.id)}
              />
            ))}
          </div>
        )}

        {/* Group Channels */}
        {groupedChannels.group.length > 0 && (
          <div className="mb-4">
            <div className="text-xs font-medium text-gray-500 dark:text-gray-400 px-2 mb-1">
              CHANNELS
            </div>
            {groupedChannels.group.map(channel => (
              <ChannelItem
                key={channel.id}
                channel={channel}
                isActive={channel.id === activeChannelId}
                onClick={() => onSelectChannel(channel.id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function ChannelItem({ 
  channel, 
  isActive, 
  onClick 
}: { 
  channel: Channel
  isActive: boolean
  onClick: () => void 
}) {
  const icons: Record<Channel['type'], string> = {
    direct: '👤',
    group: '#',
    trial: '🧪',
    [LEGACY_REEVU_CHANNEL_TYPE]: '🪷'
  }

  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-left transition-colors',
        isActive
          ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
          : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'
      )}
    >
      <span className="text-sm">{channel.icon || icons[channel.type]}</span>
      <span className="flex-1 text-sm truncate">{channel.name}</span>
      {channel.unreadCount > 0 && (
        <span className="w-5 h-5 bg-amber-500 text-white text-xs rounded-full flex items-center justify-center">
          {channel.unreadCount}
        </span>
      )}
    </button>
  )
}

// ============================================
// MAIN CHAT COMPONENT
// ============================================

interface TeamChatProps {
  currentUserId: string
  currentUserName: string
  className?: string
}

export function TeamChat({ currentUserId, currentUserName, className }: TeamChatProps) {
  const [channels, setChannels] = useState<Channel[]>([
    {
      id: LEGACY_REEVU_CHANNEL_ID,
      name: 'REEVU AI',
      type: LEGACY_REEVU_CHANNEL_TYPE,
      icon: '🪷',
      members: [currentUserId],
      unreadCount: 0
    },
    {
      id: 'trial-wheat-2024',
      name: 'Wheat Trial 2024',
      type: 'trial',
      members: [currentUserId, 'user-2', 'user-3'],
      unreadCount: 2
    },
    {
      id: 'general',
      name: 'General',
      type: 'group',
      members: [currentUserId, 'user-2', 'user-3', 'user-4'],
      unreadCount: 0
    },
    {
      id: 'dm-sharma',
      name: 'Dr. Sharma',
      type: 'direct',
      members: [currentUserId, 'user-2'],
      unreadCount: 1
    }
  ])

  const [activeChannelId, setActiveChannelId] = useState<string>(LEGACY_REEVU_CHANNEL_ID)
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      channelId: LEGACY_REEVU_CHANNEL_ID,
      userId: LEGACY_REEVU_USER_ID,
      userName: 'REEVU',
      content: 'Namaste! 🙏 I\'m REEVU, your AI breeding assistant. How can I help you today?\n\nYou can ask me about:\n• Trial performance and analysis\n• Germplasm recommendations\n• Crossing strategies\n• Data quality issues\n• Weather impacts',
      timestamp: new Date(Date.now() - 60000),
      type: LEGACY_REEVU_CHANNEL_TYPE
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Filter messages for active channel
  const channelMessages = messages.filter(m => m.channelId === activeChannelId)
  const activeChannel = channels.find(c => c.id === activeChannelId)

  // Send message
  const sendMessage = useCallback(() => {
    if (!inputValue.trim()) return

    const newMessage: Message = {
      id: Date.now().toString(),
      channelId: activeChannelId,
      userId: currentUserId,
      userName: currentUserName,
      content: inputValue.trim(),
      timestamp: new Date(),
      type: 'text'
    }

    setMessages(prev => [...prev, newMessage])
    setInputValue('')

    // Simulate REEVU response
    if (activeChannelId === LEGACY_REEVU_CHANNEL_ID) {
      setIsTyping(true)
      setTimeout(() => {
        const reevuResponse: Message = {
          id: (Date.now() + 1).toString(),
          channelId: LEGACY_REEVU_CHANNEL_ID,
          userId: LEGACY_REEVU_USER_ID,
          userName: 'REEVU',
          content: generateReevuResponse(inputValue.trim()),
          timestamp: new Date(),
          type: LEGACY_REEVU_CHANNEL_TYPE
        }
        setMessages(prev => [...prev, reevuResponse])
        setIsTyping(false)
      }, 1500)
    }
  }, [inputValue, activeChannelId, currentUserId, currentUserName])

  return (
    <div className={cn('flex h-[600px] bg-card text-card-foreground rounded-xl border border-border overflow-hidden', className)}>
      {/* Channel List */}
      <ChannelList
        channels={channels}
        activeChannelId={activeChannelId}
        onSelectChannel={setActiveChannelId}
      />

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Channel Header */}
        <div className="px-4 py-3 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg">
              {activeChannel?.icon || (activeChannel?.type === 'trial' ? '🧪' : '#')}
            </span>
            <h3 className="font-semibold text-gray-900 dark:text-white">
              {activeChannel?.name}
            </h3>
            {activeChannel?.type === LEGACY_REEVU_CHANNEL_TYPE && (
              <span className="text-xs bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 px-2 py-0.5 rounded-full">
                AI Assistant
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">
              {activeChannel?.members.length} members
            </span>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4">
          {channelMessages.map((message, idx) => {
            const prevMessage = channelMessages[idx - 1]
            const showAvatar = !prevMessage || prevMessage.userId !== message.userId

            return (
              <MessageBubble
                key={message.id}
                message={message}
                isOwn={message.userId === currentUserId}
                showAvatar={showAvatar}
              />
            )
          })}

          {/* Typing indicator */}
          {isTyping && (
            <div className="flex items-center gap-2 text-gray-500 text-sm">
              <span className="flex gap-1">
                <span className="w-2 h-2 bg-amber-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-amber-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-amber-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </span>
              <span>REEVU is typing...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-border">
          <div className="flex items-center gap-2">
            <button className="p-2 text-muted-foreground hover:text-foreground transition-colors">
              📎
            </button>
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
              placeholder={activeChannelId === LEGACY_REEVU_CHANNEL_ID ? 'Ask REEVU anything...' : 'Type a message...'}
              className="flex-1 px-4 py-2 bg-muted border-0 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
            <button
              onClick={sendMessage}
              disabled={!inputValue.trim()}
              className={cn(
                'p-2 rounded-full transition-colors',
                inputValue.trim()
                  ? 'bg-amber-500 text-white hover:bg-amber-600'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-400'
              )}
            >
              ➤
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ============================================
// REEVU RESPONSE GENERATOR
// ============================================

function generateReevuResponse(input: string): string {
  const lowerInput = input.toLowerCase()

  if (lowerInput.includes('trial') && (lowerInput.includes('summary') || lowerInput.includes('status'))) {
    return '📊 Here\'s your trial summary:\n\n• **Active Trials**: 24 across 5 locations\n• **Observations This Week**: 1,847\n• **Data Quality Score**: 94%\n\nThe wheat variety trial at Location A is showing promising results with 15% above-average yield. Would you like me to generate a detailed report?'
  }

  if (lowerInput.includes('yield') || lowerInput.includes('predict')) {
    return '🎯 Based on current data and weather patterns, I predict:\n\n• **Trial T-2024-15**: +12% yield increase (87% confidence)\n• **Key Factors**: Favorable moisture, optimal temperature\n• **Risk**: Minor heat stress expected in week 3\n\nWould you like me to run a detailed analysis?'
  }

  if (lowerInput.includes('cross') || lowerInput.includes('parent')) {
    return '🧬 I\'ve analyzed your germplasm and recommend these crosses:\n\n1. **Line A-2847 × Line B-1923**\n   - Predicted gain: +15% disease resistance\n   - Genetic distance: 0.42\n   - Confidence: 92%\n\n2. **Line C-3156 × Line D-2089**\n   - Predicted gain: +8% yield\n   - Complementarity: High\n\nShall I create a crossing plan?'
  }

  if (lowerInput.includes('weather')) {
    return '🌤️ Weather outlook for your locations:\n\n• **Location A**: Favorable conditions, no concerns\n• **Location B**: ⚠️ Heavy rain (45mm) expected in 48 hours\n• **Location C**: Heat wave possible next week\n\nI recommend completing pollinations at Location B before the rain event.'
  }

  if (lowerInput.includes('help') || lowerInput.includes('what can')) {
    return '🪷 I can help you with:\n\n• **Trial Analysis** - Performance summaries, comparisons\n• **Predictions** - Yield forecasts, crossing outcomes\n• **Recommendations** - Parent selection, advancement decisions\n• **Data Quality** - Issue detection, validation\n• **Weather** - Impact analysis, activity planning\n• **Search** - Find germplasm, protocols, trials\n\nJust ask me anything about your breeding program!'
  }

  return `I understand you\'re asking about "${input}". Let me help you with that.\n\nBased on your breeding program data, I can provide insights on trials, germplasm, predictions, and more. Could you be more specific about what you\'d like to know?`
}

export default TeamChat
