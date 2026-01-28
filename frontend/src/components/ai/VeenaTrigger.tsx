/**
 * VeenaTrigger - The Floating V-Flame Logo
 *
 * A V-shaped flame logo like a lamp/diya in the bottom-right corner.
 */

import { cn } from "@/lib/utils";

interface VeenaTriggerProps {
  isOpen: boolean;
  onClick: () => void;
  isReady: boolean;
  isProcessing: boolean;
  className?: string;
}

// V-Flame Logo - Like a lamp with flame rising from V
export function VeenaLogo({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 100 120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <defs>
        <linearGradient id="flameGradient" x1="0%" y1="100%" x2="0%" y2="0%">
          <stop offset="0%" stopColor="#059669" />
          <stop offset="30%" stopColor="#10b981" />
          <stop offset="60%" stopColor="#fbbf24" />
          <stop offset="100%" stopColor="#f59e0b" />
        </linearGradient>
        <radialGradient id="flameGlow">
          <stop offset="0%" stopColor="#fbbf24" stopOpacity="0.8" />
          <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
        </radialGradient>
      </defs>
      
      {/* Glow effect */}
      <circle cx="50" cy="40" r="40" fill="url(#flameGlow)" opacity="0.4" />
      
      {/* V-shaped base (lamp) */}
      <path
        d="M 30 90 L 50 110 L 70 90"
        stroke="url(#flameGradient)"
        strokeWidth="6"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      
      {/* Flame rising from V */}
      <g>
        {/* Outer flame */}
        <path
          d="M 50 90 Q 35 70, 40 50 Q 42 35, 50 20 Q 58 35, 60 50 Q 65 70, 50 90 Z"
          fill="url(#flameGradient)"
          opacity="0.8"
        />
        
        {/* Inner flame (brighter) */}
        <path
          d="M 50 85 Q 40 70, 43 55 Q 45 45, 50 30 Q 55 45, 57 55 Q 60 70, 50 85 Z"
          fill="#fbbf24"
          opacity="0.9"
        />
        
        {/* Core (brightest) */}
        <ellipse
          cx="50"
          cy="60"
          rx="8"
          ry="15"
          fill="#fef3c7"
        />
        
        {/* Spark at tip */}
        <circle
          cx="50"
          cy="20"
          r="4"
          fill="#fef3c7"
        />
      </g>
      
      {/* V letter outline for definition */}
      <path
        d="M 32 92 L 50 108 L 68 92"
        stroke="#10b981"
        strokeWidth="2"
        fill="none"
        opacity="0.6"
      />
    </svg>
  );
}

export function VeenaTrigger({
  isOpen,
  onClick,
  isReady,
  isProcessing,
  className,
}: VeenaTriggerProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        // Base positioning - fixed bottom-right corner, above mobile nav
        "fixed bottom-20 right-4 z-50 lg:bottom-4",
        // Size
        "w-16 h-16 lg:w-20 lg:h-20",
        // Hide when sidebar is open
        isOpen && "pointer-events-none opacity-0",
        // Transition
        "transition-all duration-300 ease-out",
        // Hover effect
        "hover:scale-110",
        // Remove background
        "bg-transparent",
        className
      )}
      title="Ask Veena (Ctrl+/)"
      aria-label="Open Veena AI Assistant"
    >
      {/* V-Flame Logo with pulsating effect */}
      <VeenaLogo
        className={cn(
          "w-full h-full",
          "drop-shadow-[0_0_16px_rgba(251,191,36,0.8)]",
          isProcessing && "animate-pulse drop-shadow-[0_0_24px_rgba(251,191,36,1)]"
        )}
      />
    </button>
  );
}
