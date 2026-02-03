/**
 * Enhanced Command Palette with Meilisearch Integration
 * Instant search across all data with typo tolerance
 */

import { useEffect, useState, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Command } from 'cmdk'
import { useMeilisearch } from '@/lib/meilisearch'
import { trackBreedingEvent } from '@/lib/posthog'

// Navigation items (pages)
const NAV_ITEMS = [
  { path: '/dashboard', label: 'Dashboard', icon: '📊', section: 'Navigation' },
  { path: '/germplasm', label: 'Germplasm', icon: '🌱', section: 'Navigation' },
  { path: '/trials', label: 'Trials', icon: '🧪', section: 'Navigation' },
  { path: '/observations', label: 'Observations', icon: '📋', section: 'Navigation' },
  { path: '/traits', label: 'Traits', icon: '🔬', section: 'Navigation' },
  { path: '/crosses', label: 'Crosses', icon: '🧬', section: 'Navigation' },
  { path: '/genomic-selection', label: 'Genomic Selection', icon: '🧬', section: 'Navigation' },
  { path: '/analytics', label: 'Analytics', icon: '📊', section: 'Navigation' },
  { path: '/ai-assistant', label: 'AI Assistant', icon: '💬', section: 'Navigation' },
  { path: '/wasm-genomics', label: 'WASM Genomics', icon: '⚡', section: 'Navigation' },
  { path: '/settings', label: 'Settings', icon: '⚙️', section: 'Navigation' },
]

// Quick actions
const QUICK_ACTIONS = [
  { id: 'new-observation', label: 'Record Observation', icon: '➕', path: '/observations/collect', section: 'Actions' },
  { id: 'new-germplasm', label: 'Add Germplasm', icon: '🌱', path: '/germplasm/new', section: 'Actions' },
  { id: 'new-cross', label: 'Create Cross', icon: '🧬', path: '/crosses/new', section: 'Actions' },
  { id: 'scan-barcode', label: 'Scan Barcode', icon: '📱', path: '/scanner', section: 'Actions' },
  { id: 'run-analysis', label: 'Run Analysis', icon: '📊', path: '/wasm-genomics', section: 'Actions' },
  { id: 'sync-data', label: 'Sync Data', icon: '🔄', path: '/data-sync', section: 'Actions' },
]

interface EnhancedCommandPaletteProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function EnhancedCommandPalette({ open, onOpenChange }: EnhancedCommandPaletteProps) {
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const [recentItems, setRecentItems] = useState<string[]>([])
  
  // Meilisearch integration
  const { query, setQuery, results: searchResults, isSearching, isConnected } = useMeilisearch()

  // Load recent items
  useEffect(() => {
    if (open) {
      const stored = localStorage.getItem('bijmantra-recent-nav')
      if (stored) {
        setRecentItems(JSON.parse(stored))
      }
      // Track command palette open
      trackBreedingEvent('COMMAND_PALETTE_OPENED')
    }
  }, [open])

  // Focus input when opened
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 0)
    }
  }, [open])

  const handleSelect = useCallback((path: string, type?: string) => {
    // Update recent items
    const updated = [path, ...recentItems.filter(p => p !== path)].slice(0, 5)
    localStorage.setItem('bijmantra-recent-nav', JSON.stringify(updated))
    setRecentItems(updated)
    
    // Track search if query was used
    if (query) {
      trackBreedingEvent('SEARCH_PERFORMED', {
        query,
        resultType: type,
        resultPath: path,
      })
    }
    
    onOpenChange(false)
    setQuery('')
    navigate(path)
  }, [navigate, onOpenChange, recentItems, query, setQuery])

  // Filter nav items based on query
  const filteredNavItems = query
    ? NAV_ITEMS.filter(item => 
        item.label.toLowerCase().includes(query.toLowerCase())
      )
    : NAV_ITEMS.slice(0, 5)

  // Get recent nav items
  const recentNavItems = recentItems
    .map(path => NAV_ITEMS.find(item => item.path === path))
    .filter(Boolean)

  return (
    <Command.Dialog
      open={open}
      onOpenChange={onOpenChange}
      label="Enhanced Command Menu"
      className="fixed inset-0 z-[100]"
    >
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />
      
      {/* Dialog */}
      <div className="fixed left-1/2 top-[15%] -translate-x-1/2 w-full max-w-2xl">
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-2xl border border-gray-200 dark:border-slate-700 overflow-hidden">
          {/* Search Input */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-100 dark:border-slate-700">
            <span className="text-gray-400 dark:text-gray-500">🔍</span>
            <Command.Input
              ref={inputRef}
              value={query}
              onValueChange={setQuery}
              placeholder={isConnected 
                ? "Search germplasm, trials, traits, or type a command..." 
                : "Search pages or type a command..."
              }
              className="flex-1 bg-transparent outline-none text-gray-900 dark:text-gray-100 placeholder:text-gray-400 dark:placeholder:text-gray-500"
            />
            {isSearching && (
              <span className="text-gray-400 dark:text-gray-500 animate-spin">⏳</span>
            )}
            {isConnected && (
              <span className="text-xs text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/30 px-2 py-0.5 rounded-full">
                Instant Search
              </span>
            )}
            <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-1 text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-slate-700 rounded">
              ESC
            </kbd>
          </div>

          {/* Results */}
          <Command.List className="max-h-[60vh] overflow-y-auto p-2">
            <Command.Empty className="py-6 text-center text-gray-500 dark:text-gray-400">
              {isSearching ? 'Searching...' : 'No results found. Try a different search term.'}
            </Command.Empty>

            {/* Meilisearch Results (Data) */}
            {searchResults.length > 0 && (
              <Command.Group heading="Data Results">
                <div className="px-2 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider flex items-center gap-2">
                  <span>📦</span> Data Results
                  <span className="text-green-600 dark:text-green-400">({searchResults.length})</span>
                </div>
                {searchResults.map((result) => (
                  <Command.Item
                    key={`data-${result.type}-${result.id}`}
                    value={`data ${result.title} ${result.subtitle || ''}`}
                    onSelect={() => handleSelect(result.path, result.type)}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-gray-700 dark:text-gray-200 hover:bg-green-50 dark:hover:bg-green-900/30 hover:text-green-700 dark:hover:text-green-400 data-[selected=true]:bg-green-50 dark:data-[selected=true]:bg-green-900/30 data-[selected=true]:text-green-700 dark:data-[selected=true]:text-green-400"
                  >
                    <span className="text-lg">{result.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{result.title}</div>
                      {(result.subtitle || result.description) && (
                        <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                          {result.subtitle}{result.subtitle && result.description ? ' • ' : ''}{result.description}
                        </div>
                      )}
                    </div>
                    <span className="text-xs text-gray-400 dark:text-gray-500 capitalize">{result.type}</span>
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            {/* Quick Actions */}
            {!query && (
              <Command.Group heading="Quick Actions">
                <div className="px-2 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  ⚡ Quick Actions
                </div>
                {QUICK_ACTIONS.map((action) => (
                  <Command.Item
                    key={action.id}
                    value={`action ${action.label}`}
                    onSelect={() => handleSelect(action.path, 'action')}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-gray-700 dark:text-gray-200 hover:bg-blue-50 dark:hover:bg-blue-900/30 hover:text-blue-700 dark:hover:text-blue-400 data-[selected=true]:bg-blue-50 dark:data-[selected=true]:bg-blue-900/30 data-[selected=true]:text-blue-700 dark:data-[selected=true]:text-blue-400"
                  >
                    <span className="text-lg">{action.icon}</span>
                    <span className="font-medium">{action.label}</span>
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            {/* Recent */}
            {!query && recentNavItems.length > 0 && (
              <Command.Group heading="Recent">
                <div className="px-2 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  🕐 Recent
                </div>
                {recentNavItems.map((item) => item && (
                  <Command.Item
                    key={`recent-${item.path}`}
                    value={`recent ${item.label}`}
                    onSelect={() => handleSelect(item.path, 'recent')}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-slate-700 data-[selected=true]:bg-gray-100 dark:data-[selected=true]:bg-slate-700"
                  >
                    <span className="text-lg">{item.icon}</span>
                    <span>{item.label}</span>
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            {/* Navigation */}
            <Command.Group heading="Navigation">
              <div className="px-2 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                🧭 Navigation
              </div>
              {filteredNavItems.map((item) => (
                <Command.Item
                  key={item.path}
                  value={`nav ${item.label}`}
                  onSelect={() => handleSelect(item.path, 'navigation')}
                  className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-slate-700 data-[selected=true]:bg-gray-100 dark:data-[selected=true]:bg-slate-700"
                >
                  <span className="text-lg">{item.icon}</span>
                  <span>{item.label}</span>
                </Command.Item>
              ))}
            </Command.Group>
          </Command.List>

          {/* Footer */}
          <div className="flex items-center justify-between px-4 py-2 border-t border-gray-100 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 text-xs text-gray-500 dark:text-gray-400">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-700 rounded border dark:border-slate-600">↑↓</kbd> Navigate
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-700 rounded border dark:border-slate-600">↵</kbd> Select
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-700 rounded border dark:border-slate-600">ESC</kbd> Close
              </span>
            </div>
            <div className="flex items-center gap-2">
              {isConnected && (
                <span className="text-green-600 dark:text-green-400">⚡ Meilisearch</span>
              )}
              <span>🌱 Bijmantra</span>
            </div>
          </div>
        </div>
      </div>
    </Command.Dialog>
  )
}
