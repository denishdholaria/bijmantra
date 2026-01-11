/**
 * Mahasarthi Sidebar Component
 * 
 * Production sidebar with diagonal edge design.
 * Integrates with MahasarthiNavigation for actual navigation content.
 * 
 * Features:
 * - Diagonal/slashed edge with glowing stroke
 * - Smooth collapse/expand transitions
 * - Mobile responsive with overlay + swipe gesture
 * - WCAG 2.1 AA compliant with skip link and focus trap
 * - Keyboard shortcuts [ and ] to toggle
 * - Hover-to-expand option
 * - Integrates with Mahasarthi navigation system
 */

import { Link } from 'react-router-dom';
import { useEffect, useRef, useCallback, useState } from 'react';
import { PanelLeftClose, PanelLeft } from 'lucide-react';
import { cn } from '@/lib/utils';

// ============================================================================
// Constants
// ============================================================================

const SIDEBAR_WIDTH_OPEN = 256; // 16rem = w-64
const SIDEBAR_WIDTH_COLLAPSED = 64; // 4rem = w-16
const SLASH_OFFSET_OPEN = 40;
const SLASH_OFFSET_COLLAPSED = 10;
const SWIPE_THRESHOLD = 50; // pixels to trigger swipe close
const HOVER_EXPAND_DELAY = 300; // ms delay before hover expand

// ============================================================================
// Types
// ============================================================================

interface MahasarthiSidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  mobileOpen: boolean;
  onMobileClose: () => void;
  children: React.ReactNode;
  enableHoverExpand?: boolean; // Optional hover-to-expand behavior
}

// ============================================================================
// Component
// ============================================================================

export function MahasarthiSidebar({
  collapsed,
  onToggle,
  mobileOpen,
  onMobileClose,
  children,
  enableHoverExpand = false,
}: MahasarthiSidebarProps) {
  const width = collapsed ? SIDEBAR_WIDTH_COLLAPSED : SIDEBAR_WIDTH_OPEN;
  const slashOffset = collapsed ? SLASH_OFFSET_COLLAPSED : SLASH_OFFSET_OPEN;
  
  // Refs for touch handling and focus trap
  const sidebarRef = useRef<HTMLElement>(null);
  const touchStartX = useRef<number>(0);
  const touchCurrentX = useRef<number>(0);
  const hoverTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [isHoverExpanded, setIsHoverExpanded] = useState(false);
  
  // Effective collapsed state (respects hover expand)
  const effectiveCollapsed = collapsed && !isHoverExpanded;
  const effectiveWidth = effectiveCollapsed ? SIDEBAR_WIDTH_COLLAPSED : SIDEBAR_WIDTH_OPEN;
  const effectiveSlashOffset = effectiveCollapsed ? SLASH_OFFSET_COLLAPSED : SLASH_OFFSET_OPEN;

  // ========================================================================
  // Keyboard Shortcuts: [ and ] to toggle sidebar
  // ========================================================================
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if user is typing in an input
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }
      
      if (e.key === '[' || e.key === ']') {
        e.preventDefault();
        onToggle();
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onToggle]);

  // ========================================================================
  // Mobile Swipe Gesture Handler
  // ========================================================================
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
    touchCurrentX.current = e.touches[0].clientX;
  }, []);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    touchCurrentX.current = e.touches[0].clientX;
  }, []);

  const handleTouchEnd = useCallback(() => {
    const deltaX = touchStartX.current - touchCurrentX.current;
    // Swipe left to close
    if (deltaX > SWIPE_THRESHOLD && mobileOpen) {
      onMobileClose();
    }
  }, [mobileOpen, onMobileClose]);

  // ========================================================================
  // Hover Expand (Desktop only)
  // ========================================================================
  const handleMouseEnter = useCallback(() => {
    if (!enableHoverExpand || !collapsed) return;
    
    hoverTimeoutRef.current = setTimeout(() => {
      setIsHoverExpanded(true);
    }, HOVER_EXPAND_DELAY);
  }, [enableHoverExpand, collapsed]);

  const handleMouseLeave = useCallback(() => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
      hoverTimeoutRef.current = null;
    }
    setIsHoverExpanded(false);
  }, []);

  // Cleanup hover timeout on unmount
  useEffect(() => {
    return () => {
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
      }
    };
  }, []);

  // ========================================================================
  // Focus Trap for Mobile (when open)
  // ========================================================================
  useEffect(() => {
    if (!mobileOpen || !sidebarRef.current) return;

    const sidebar = sidebarRef.current;
    const focusableElements = sidebar.querySelectorAll<HTMLElement>(
      'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );
    
    if (focusableElements.length === 0) return;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };

    // Focus first element when opened
    firstElement.focus();

    document.addEventListener('keydown', handleTabKey);
    return () => document.removeEventListener('keydown', handleTabKey);
  }, [mobileOpen]);

  return (
    <>
      {/* Skip to Content Link - WCAG Accessibility */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-[100] focus:px-4 focus:py-2 focus:bg-emerald-600 focus:text-white focus:rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-400"
      >
        Skip to main content
      </a>

      {/* Mobile Overlay with backdrop blur */}
      {mobileOpen && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden" 
          onClick={onMobileClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        ref={sidebarRef}
        role="navigation"
        aria-label="Main navigation"
        className={cn(
          "fixed left-0 top-0 h-full z-50 flex flex-col",
          "transition-all duration-300 ease-out motion-reduce:transition-none",
          // Mobile: slide in/out
          mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
        style={{ width: effectiveWidth }}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        {/* SVG Background with Slashed Edge - Simplified for performance */}
        <svg
          viewBox={`0 0 ${effectiveWidth} 1000`}
          preserveAspectRatio="none"
          className="absolute inset-0 h-full transition-all duration-300 motion-reduce:transition-none pointer-events-none"
          style={{ width: effectiveWidth }}
          aria-hidden="true"
        >
          <defs>
            {/* Main gradient - ALWAYS dark slate for sidebar regardless of theme
                The sidebar is designed to be dark with light text, independent of page theme */}
            <linearGradient id="slashSidebarGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#0f172a" />
              <stop offset="40%" stopColor="#1e293b" />
              <stop offset="100%" stopColor="#0f172a" />
            </linearGradient>
            
            {/* Edge glow gradient - emerald/cyan accent */}
            <linearGradient id="slashEdgeGlow" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.1" />
              <stop offset="30%" stopColor="#10b981" stopOpacity="0.7" />
              <stop offset="50%" stopColor="#06b6d4" stopOpacity="0.9" />
              <stop offset="70%" stopColor="#10b981" stopOpacity="0.7" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0.1" />
            </linearGradient>
          </defs>
          
          {/* Main shape - slashed rectangle (contained within width) */}
          <path 
            d={`M0 0 L${effectiveWidth - 3} 0 L${effectiveWidth - effectiveSlashOffset - 3} 1000 L0 1000 Z`}
            fill="url(#slashSidebarGradient)"
            className="transition-all duration-300 motion-reduce:transition-none"
          />
          
          {/* Glowing edge - single sharp line */}
          <path 
            d={`M${effectiveWidth - 3} 0 L${effectiveWidth - effectiveSlashOffset - 3} 1000`}
            stroke="url(#slashEdgeGlow)"
            strokeWidth="2"
            fill="none"
            className="transition-all duration-300 motion-reduce:transition-none"
          />
        </svg>

        {/* Content Container */}
        <div className="relative z-10 h-full flex flex-col text-slate-200">
          {/* Header with Logo and Toggle */}
          <div className={cn(
            "h-14 flex items-center border-b border-white/10 flex-shrink-0 px-3",
            effectiveCollapsed ? "justify-center" : "justify-between"
          )}>
            {!effectiveCollapsed ? (
              <Link to="/dashboard" className="flex items-center gap-2 group">
                <span className="text-emerald-400 font-mono text-xl font-bold transition-transform duration-200 group-hover:scale-110">/</span>
                <span className="text-base font-semibold text-white tracking-tight">
                  Bijmantra
                </span>
              </Link>
            ) : (
              <Link to="/dashboard" className="flex items-center justify-center">
                <span className="text-emerald-400 font-mono text-xl font-bold transition-transform duration-200 hover:scale-110">/</span>
              </Link>
            )}
            
            {/* Toggle button - visible on desktop when expanded */}
            {!effectiveCollapsed && (
              <button
                onClick={onToggle}
                aria-label="Collapse sidebar (or press [ or ])"
                aria-expanded={true}
                className={cn(
                  "p-2 rounded-lg hover:bg-white/10 transition-colors",
                  "focus:outline-none focus:ring-2 focus:ring-emerald-500/50",
                  "hidden lg:flex items-center justify-center"
                )}
              >
                <PanelLeftClose className="w-4 h-4 transition-transform duration-200 hover:scale-110" />
              </button>
            )}
          </div>

          {/* Toggle button when collapsed - separate row */}
          {effectiveCollapsed && (
            <div className="flex justify-center py-2 border-b border-white/10">
              <button
                onClick={onToggle}
                aria-label="Expand sidebar (or press [ or ])"
                aria-expanded={false}
                className={cn(
                  "p-2 rounded-lg hover:bg-white/10 transition-colors",
                  "focus:outline-none focus:ring-2 focus:ring-emerald-500/50",
                  "hidden lg:flex items-center justify-center"
                )}
              >
                <PanelLeft className="w-4 h-4 transition-transform duration-200 hover:scale-110" />
              </button>
            </div>
          )}

          {/* Navigation Content - passed as children */}
          {/* Right padding keeps scrollbar away from diagonal edge */}
          <div 
            className="flex-1 overflow-y-auto overflow-x-hidden pr-3"
            style={{ 
              scrollbarWidth: 'thin', 
              scrollbarColor: '#10b981 transparent',
              marginRight: effectiveCollapsed ? 0 : 8,
            }}
          >
            {/* Pass effective collapsed state to children */}
            {typeof children === 'function' 
              ? (children as (props: { collapsed: boolean }) => React.ReactNode)({ collapsed: effectiveCollapsed })
              : children
            }
          </div>

          {/* Footer */}
          <div className="flex-shrink-0 p-2 border-t border-white/10">
            {!effectiveCollapsed && (
              <div className="px-2 py-1 text-[10px] text-slate-500 uppercase tracking-wider flex items-center justify-between">
                <span>preview-1</span>
                <span className="text-slate-600">[ ] toggle</span>
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}

export default MahasarthiSidebar;
