import { motion } from 'framer-motion';
import { Home, Command, Search, Sparkles } from 'lucide-react';
import { useOSStore } from './store';
import { cn } from '@/lib/utils';

export function CommandBar() {
  const { mode, goHome, toggleSearch } = useOSStore();
  const isHome = mode === 'sanctuary';

  return (
    <div className="fixed bottom-8 left-0 right-0 z-50 flex justify-center pointer-events-none">
      <motion.div
        layout
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ type: "spring", stiffness: 200, damping: 20 }}
        className={cn(
            "pointer-events-auto flex items-center gap-1 p-1.5 rounded-full",
            "bg-prakruti-dhool-900/90 dark:bg-black/80 backdrop-blur-2xl border border-white/10 shadow-2xl shadow-black/20 text-white"
        )}
      >
        {/* Home Button (Contextual) */}
        {!isHome && (
            <motion.button
                initial={{ width: 0, opacity: 0 }}
                animate={{ width: 'auto', opacity: 1 }}
                exit={{ width: 0, opacity: 0 }}
                onClick={goHome}
                className="p-2.5 rounded-full hover:bg-white/10 transition-colors"
                title="Go Home"
            >
                <Home className="w-5 h-5" />
            </motion.button>
        )}

        {/* Separator if home is visible */}
        {!isHome && <div className="w-px h-5 bg-white/20 mx-1" />}

        {/* Search Trigger (The "Pill" Center) */}
        <button
            onClick={() => toggleSearch()}
            className={cn(
                "flex items-center gap-3 px-4 py-2.5 rounded-full hover:bg-white/10 transition-all group",
                isHome ? "pr-6" : "pr-4"
            )}
        >
             <Search className="w-5 h-5 text-white/70 group-hover:text-white" />
             <span className="text-sm font-medium text-white/90">
                 {isHome ? "Where do you want to go?" : "Search..."}
             </span>
             {isHome && (
                 <div className="hidden sm:flex items-center gap-1 ml-4 px-1.5 py-0.5 rounded bg-white/10 text-[10px] font-mono text-white/50">
                     <Command className="w-2.5 h-2.5" />
                     <span>K</span>
                 </div>
             )}
        </button>

        {/* REEVU Indicator (Right) */}
        <div className="pl-2 pr-3 border-l border-white/20 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-prakruti-patta-400 animate-pulse" />
        </div>

      </motion.div>
    </div>
  );
}
