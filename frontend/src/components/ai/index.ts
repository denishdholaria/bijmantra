/**
 * AI Components
 * Human-AI Centric Interface (HMI) for Bijmantra
 */

// Veena - AI Assistant (named after the sacred instrument of Goddess Saraswati)
export { Veena } from './Veena'
export { VeenaWelcome, useVeenaIntroduction } from './VeenaWelcome'
export { VeenaSidebar } from './VeenaSidebar'

// REEVA - Experimental Reasoning Engine (LangGraph ReAct)
export { default as ReevaSidebar } from './ReevaSidebar'

// Legacy export for backward compatibility
export { Veena as NanoAI } from './Veena'

// Voice Command System
export { VoiceCommandProvider, useVoiceCommand } from './VoiceCommand'
