import { useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useContextMenuStore, type ContextMenuItem } from '@/store/contextMenuStore'
import { cn } from '@/lib/utils'
import { ChevronRight } from 'lucide-react'

// Hook for easy integration
export function useContextMenu(items: ContextMenuItem[]) {
  const { openContextMenu } = useContextMenuStore()

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    openContextMenu(e.clientX, e.clientY, items)
  }

  return { onContextMenu: handleContextMenu }
}

// Main Component
export function ContextMenu() {
  const { isOpen, position, items, closeContextMenu } = useContextMenuStore()
  const menuRef = useRef<HTMLDivElement>(null)

  // Close on click outside
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        closeContextMenu()
      }
    }
    
    // Also close on window resize/blur
    const handleResize = () => closeContextMenu()
    
    if (isOpen) {
      document.addEventListener('mousedown', handleClick)
      window.addEventListener('resize', handleResize)
    }
    
    return () => {
      document.removeEventListener('mousedown', handleClick)
      window.removeEventListener('resize', handleResize)
    }
  }, [isOpen, closeContextMenu])

  // Adjust position to keep on screen
  // (Simplified for now, can add viewport aware logic later)
  const adjustedX = position.x
  const adjustedY = position.y

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          ref={menuRef}
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          transition={{ duration: 0.1, ease: 'easeOut' }}
          className="fixed z-[1100] min-w-[180px] overflow-hidden rounded-xl border border-slate-200/50 bg-white/80 p-1.5 shadow-xl backdrop-blur-xl dark:border-slate-800/50 dark:bg-slate-900/80"
          style={{ left: adjustedX, top: adjustedY }}
        >
          {items.map((item, idx) => (
            <ContextMenuItemRow key={idx} item={item} onClose={closeContextMenu} />
          ))}
        </motion.div>
      )}
    </AnimatePresence>
  )
}

function ContextMenuItemRow({ item, onClose }: { item: ContextMenuItem; onClose: () => void }) {
  if (item.separator) {
    return <div className="my-1 h-px bg-slate-200 dark:bg-slate-700" />
  }

  const Icon = item.icon

  return (
    <button
      onClick={() => {
        if (!item.disabled) {
          item.action()
          onClose()
        }
      }}
      disabled={item.disabled}
      className={cn(
        "flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-xs font-medium transition-colors",
        item.danger 
          ? "text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20" 
          : "text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800",
        item.disabled && "opacity-50 cursor-not-allowed"
      )}
    >
      {Icon && <Icon className="h-4 w-4 opacity-70" />}
      <span className="flex-1 text-left">{item.label}</span>
      {item.shortcut && (
        <span className="text-[10px] text-slate-400">{item.shortcut}</span>
      )}
      {item.submenu && <ChevronRight className="h-3 w-3 opacity-50" />}
    </button>
  )
}
