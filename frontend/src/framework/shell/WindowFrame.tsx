import { useRef, useEffect } from 'react';
import { motion, useDragControls } from 'framer-motion';
import { X, Minus, Square, Maximize2 } from 'lucide-react';
import { useWindowStore, type WindowState } from '@/store/windowStore';
import { cn } from '@/lib/utils';

interface WindowFrameProps {
  window: WindowState;
  children: React.ReactNode;
}

export function WindowFrame({ window, children }: WindowFrameProps) {
  const { 
    closeWindow, 
    focusWindow, 
    minimizeWindow, 
    maximizeWindow, 
    restoreWindow, 
    updateWindowPosition,
    updateWindowSize 
  } = useWindowStore();

  const containerRef = useRef<HTMLDivElement>(null);
  const dragControls = useDragControls();

  // Bring to front on click
  const handleFocus = () => {
    focusWindow(window.id);
  };

  const Icon = window.icon;

  if (window.isMinimized) return null;

  return (
    <motion.div
      ref={containerRef}
      drag={!window.isMaximized}
      dragListener={false} 
      dragControls={dragControls}
      dragMomentum={false}
      dragElastic={0}
      initial={{ 
        x: window.position.x, 
        y: window.position.y, 
        opacity: 0, 
        scale: 0.95 
      }}
      animate={{ 
        x: window.isMaximized ? 0 : window.position.x,
        y: window.isMaximized ? 0 : window.position.y,
        width: window.isMaximized ? '100%' : window.size.width,
        height: window.isMaximized ? '100%' : window.size.height,
        opacity: 1,
        scale: 1,
        zIndex: window.zIndex 
      }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      onDragEnd={(_, info) => {
        if (!window.isMaximized) {
          updateWindowPosition(window.id, { x: info.point.x, y: info.point.y });
        }
      }}
      onPointerDown={handleFocus}
      className={cn(
        "window-frame absolute rounded-xl overflow-hidden flex flex-col shadow-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800",
        window.isMaximized ? "rounded-none inset-0" : ""
      )}
      data-testid="window-frame"
      style={{
        position: 'absolute', // Ensure absolute positioning for drag
      }}
    >
      {/* Title Bar */}
      <div 
        className="flex-none h-10 bg-slate-100 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between px-3 select-none"
        onPointerDown={(e) => {
          dragControls.start(e);
          handleFocus();
        }}
        onDoubleClick={() => window.isMaximized ? restoreWindow(window.id) : maximizeWindow(window.id)}
      >
        <div className="flex items-center gap-2">
          {Icon && <Icon className="w-4 h-4 text-slate-500" />}
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300 truncate max-w-[200px]">
            {window.title}
          </span>
        </div>
        
        <div className="flex items-center gap-1.5" onPointerDown={e => e.stopPropagation()}>
          <button 
            onClick={() => minimizeWindow(window.id)}
            className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-md text-slate-500 transition-colors"
          >
            <Minus className="w-3.5 h-3.5" />
          </button>
          <button 
            onClick={() => window.isMaximized ? restoreWindow(window.id) : maximizeWindow(window.id)}
            className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-md text-slate-500 transition-colors"
          >
            {window.isMaximized ? <Maximize2 className="w-3 h-3" /> : <Square className="w-3 h-3" />}
          </button>
          <button 
            onClick={() => closeWindow(window.id)}
            className="p-1 hover:bg-red-500 hover:text-white rounded-md text-slate-500 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-auto relative bg-white dark:bg-slate-950">
        {/* If it's a route-based app, we might need an iframe or a sub-router. 
            For now, let's assume direct component rendering or simple content.
            Ideally, we use <Outlet /> if we want full routing, but Multi-window routing is hard in React Router v6 without tricky setups.
            For V1 of Window Manager, let's render the passed component or an iframe placeholder.
        */}
        {children}
        
        {/* Overlay to catch clicks when dragging/blur */}
        <div className="absolute inset-0 pointer-events-none" /> 
      </div>
      
      {/* Resize Handle (Bottom Right) */}
      {!window.isMaximized && (
        <div 
          className="absolute bottom-0 right-0 w-6 h-6 cursor-se-resize z-50 flex items-end justify-end p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-tl-lg transition-colors"
          onPointerDown={(e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const startX = e.clientX;
            const startY = e.clientY;
            const startWidth = window.size.width;
            const startHeight = window.size.height;

            const handlePointerMove = (moveEvent: PointerEvent) => {
              const deltaX = moveEvent.clientX - startX;
              const deltaY = moveEvent.clientY - startY;
              
              const newWidth = Math.max(300, startWidth + deltaX);
              const newHeight = Math.max(200, startHeight + deltaY);
              
              updateWindowSize(window.id, { width: newWidth, height: newHeight });
            };

            const handlePointerUp = () => {
              document.removeEventListener('pointermove', handlePointerMove);
              document.removeEventListener('pointerup', handlePointerUp);
            };

            document.addEventListener('pointermove', handlePointerMove);
            document.addEventListener('pointerup', handlePointerUp);
          }}
        >
          {/* Visual Grip Indicator */}
          <svg width="6" height="6" viewBox="0 0 6 6" fill="none" xmlns="http://www.w3.org/2000/svg" className="opacity-40 text-slate-500 dark:text-slate-400">
             <path d="M6 6L0 6L6 0L6 6Z" fill="currentColor"/>
          </svg>
        </div>
      )}
    </motion.div>
  );
}
