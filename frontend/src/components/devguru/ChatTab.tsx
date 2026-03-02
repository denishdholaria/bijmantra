import { Dispatch, SetStateAction, RefObject } from 'react'
import { ChatMessage, ResearchProject } from '@/types/devguru'
import { sendChatMessage } from '@/services/devguru'
import { cn } from '@/lib/utils'

interface ChatTabProps {
  activeProject: ResearchProject | undefined
  chatMessages: ChatMessage[]
  setChatMessages: Dispatch<SetStateAction<ChatMessage[]>>
  chatInput: string
  setChatInput: Dispatch<SetStateAction<string>>
  isSending: boolean
  setIsSending: Dispatch<SetStateAction<boolean>>
  messagesEndRef: RefObject<HTMLDivElement | null>
  activeProjectId: string | null
}

export function ChatTab({ activeProject, chatMessages, setChatMessages, chatInput, setChatInput, isSending, setIsSending, messagesEndRef, activeProjectId }: ChatTabProps) {
  const handleSendMessage = async () => {
    if (!chatInput.trim() || isSending) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: chatInput.trim(),
      timestamp: new Date()
    }

    setChatMessages(prev => [...prev, userMessage])
    const query = chatInput.trim()
    setChatInput('')
    setIsSending(true)

    try {
      const response = await sendChatMessage(query, activeProjectId || undefined, chatMessages)
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.message,
        timestamp: new Date(),
        sources: response.sources,
        reasoning: response.reasoning
      }
      setChatMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'I apologize, but I encountered an error. Please ensure the backend is running and your AI provider is configured.',
        timestamp: new Date()
      }
      setChatMessages(prev => [...prev, errorMessage])
    } finally {
      setIsSending(false)
    }
  }

  return (
    <>
      {/* Chat Header */}
      <div className="px-4 py-2 border-b border-gray-100 dark:border-gray-700/50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-lg">🎓</span>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {activeProject ? `Context: ${activeProject.title}` : 'Select a project for personalized guidance'}
          </p>
        </div>
        <button
          onClick={() => setChatMessages([{
            id: Date.now().toString(),
            role: 'assistant',
            content: 'Conversation cleared. How can I help with your research today?',
            timestamp: new Date()
          }])}
          className="text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          Clear
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {chatMessages.map(message => (
          <div key={message.id} className={cn('flex', message.role === 'user' ? 'justify-end' : 'justify-start')}>
            <div className={cn(
              'max-w-[80%] rounded-xl px-4 py-3',
              message.role === 'user'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
            )}>

              {/* Reasoning Trace (Savant) */}
              {message.reasoning && (
                <details className="mb-2">
                  <summary className="text-[10px] font-medium text-purple-600 dark:text-purple-400 cursor-pointer hover:underline select-none">
                    💭 View Reasoning Process
                  </summary>
                  <div className="mt-1 p-2 bg-white/50 dark:bg-gray-800/50 rounded border border-gray-200 dark:border-gray-600 text-[10px] font-mono text-gray-600 dark:text-gray-300 whitespace-pre-wrap">
                    {message.reasoning}
                  </div>
                </details>
              )}

              <p className="text-sm whitespace-pre-wrap">{message.content}</p>

              {/* RAG Sources */}
              {message.sources && message.sources.length > 0 && (
                <div className="mt-3 pt-2 border-t border-gray-200/50 dark:border-gray-600/50">
                  <p className="text-[9px] uppercase font-bold text-gray-500 mb-1.5">Sources Used:</p>
                  <div className="space-y-1.5">
                    {message.sources.map((src, idx) => (
                      <div key={idx} className="bg-white/60 dark:bg-gray-800/60 p-1.5 rounded border border-gray-200 dark:border-gray-600 textxs">
                         <div className="flex items-center gap-1.5 mb-0.5">
                            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300">
                              {src.doc_type.toUpperCase()}
                            </span>
                            <span className="text-[10px] font-medium text-gray-800 dark:text-gray-200 truncate">
                              {src.title}
                            </span>
                         </div>
                         <p className="text-[10px] text-gray-600 dark:text-gray-400 line-clamp-1 italic">
                           "{src.content.substring(0, 100)}..."
                         </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <p className={cn(
                'text-[10px] mt-1',
                message.role === 'user' ? 'opacity-70' : 'text-gray-400 dark:text-gray-500'
              )}>
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </div>
        ))}
        {isSending && (
          <div className="flex items-center gap-2 text-gray-500">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
            <span className="text-xs">DevGuru is thinking...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700">
        <div className="flex gap-2 overflow-x-auto pb-2">
          {[
            { label: '📊 Timeline Check', action: 'How am I doing on my timeline?' },
            { label: '📝 Next Steps', action: 'What should I focus on next?' },
            { label: '📚 Literature Help', action: 'Help me with my literature review' },
            { label: '✍️ Writing Tips', action: 'Give me writing tips for my thesis' },
            { label: '🎯 Milestone Update', action: 'I want to update my milestone progress' },
          ].map(qa => (
            <button
              key={qa.label}
              onClick={() => setChatInput(qa.action)}
              className="flex-shrink-0 px-3 py-1.5 text-[10px] font-medium text-purple-700 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-full hover:bg-purple-100 dark:hover:bg-purple-900/40 transition-colors"
            >
              {qa.label}
            </button>
          ))}
        </div>
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Ask DevGuru about your research..."
            className="flex-1 bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg px-4 py-2.5 text-sm text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          <button
            onClick={handleSendMessage}
            disabled={!chatInput.trim() || isSending}
            className={cn(
              'p-2.5 rounded-lg transition-all',
              chatInput.trim() && !isSending
                ? 'bg-purple-600 text-white hover:bg-purple-700'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
            )}
          >
            ➤
          </button>
        </div>
      </div>
    </>
  )
}
