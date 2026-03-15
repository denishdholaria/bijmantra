import { motion, AnimatePresence } from 'framer-motion';
import { useOSStore } from './store';
import { REGISTERED_APPS } from '../registry/moduleRegistry';
import { Suspense } from 'react';

export function FocusView() {
  const { mode, activeAppId } = useOSStore();
  const app = REGISTERED_APPS.find(a => a.id === activeAppId);

  // We keep the component mounted but hidden/inert when searching to preserve state?
  // No, for "Sanctuary" vibe, we mount/unmount.

  const isActive = mode === 'focus' || (mode === 'search' && activeAppId);

  return (
    <AnimatePresence mode="wait">
        {isActive && app && (
            <motion.div
                key="focus-container"
                initial={{ opacity: 0, scale: 0.95, y: 40 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 40, transition: { duration: 0.2 } }}
                transition={{ type: "spring", damping: 25, stiffness: 200 }}
                className="absolute inset-0 z-10 flex flex-col bg-background"
            >
                {/* Immersive Full Screen Content */}
                <div className="flex-1 w-full h-full overflow-hidden">
                    <Suspense fallback={<LoadingScreen app={app} />}>
                        {app.component && <app.component />}
                    </Suspense>
                </div>
            </motion.div>
        )}
    </AnimatePresence>
  );
}

function LoadingScreen({ app }: { app: any }) {
    return (
        <div className="flex flex-col items-center justify-center w-full h-full bg-background/50 backdrop-blur-xl">
             <div className="p-4 rounded-full bg-primary/5 mb-4 animate-pulse">
                <app.icon className="w-8 h-8 text-primary/50" />
             </div>
             <p className="text-sm text-muted-foreground font-medium">Opening {app.title}...</p>
        </div>
    )
}
