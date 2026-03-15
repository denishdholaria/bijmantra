/**
 * ASTRA Agent Registry
 * 
 * Central registry of all AI agents available in BijMantra.
 * New agents from Antigravity should be added here.
 * 
 * Icons use Lucide icon names for consistency with the app design.
 */

import { AgentDefinition, AgentRegistry } from './types';
import {
  LEGACY_REEVU_LOGO_ICON,
  LEGACY_REEVU_ORCHESTRATOR_ID,
} from '@/lib/legacyReevu';

// Legacy identifiers kept for compatibility until full ID migration lands.

/**
 * REEVU — Primary Agricultural Intelligence
 * Canonical branding; legacy internal ID remains for compatibility.
 * Uses custom SVG logo (V-flame diya design)
 */
const REEVU_AGENT: AgentDefinition = {
  id: LEGACY_REEVU_ORCHESTRATOR_ID,
  name: 'REEVU',
  shortName: 'RVU',
  description: 'Cross-domain agricultural intelligence. Queries breeding data, analyzes trials, and provides research recommendations.',
  icon: LEGACY_REEVU_LOGO_ICON,  // Special case: uses ReevuLogo component
  color: 'emerald',
  capabilities: ['chat', 'query', 'analyze', 'recommend', 'cross-domain'],
  isOrchestrator: true,
  requiresConfig: true,
  domains: ['breeding', 'genetics', 'phenotyping', 'germplasm', 'trials'],
};

/**
 * REEVA (रीवा) — Rural Empowerment through Emerging Value-driven Agro-Intelligence
 * Experimental LangGraph ReAct agent with autonomous reasoning
 */
const REEVA: AgentDefinition = {
  id: 'reeva',
  name: 'REEVA',
  shortName: 'RVA',
  description: 'Experimental reasoning engine using LangGraph ReAct pattern. Autonomous SQL query generation and multi-step reasoning.',
  icon: 'Sprout',  // Lucide icon
  color: 'cyan',
  capabilities: ['chat', 'query', 'analyze', 'execute'],
  endpoint: 'http://localhost:8081/api/chat',
  isExperimental: true,
  domains: ['trials', 'analytics'],
};

/**
 * PRITHVI (पृथ्वी) — Earth/Soil Intelligence (Planned)
 * Soil analysis, nutrient recommendations, environmental factors
 */
const PRITHVI: AgentDefinition = {
  id: 'prithvi',
  name: 'Prithvi',
  shortName: 'PTH',
  description: 'Soil and environmental intelligence. Analyzes soil data, recommends nutrients, and factors climate conditions.',
  icon: 'Mountain',  // Lucide icon
  color: 'amber',
  capabilities: ['chat', 'analyze', 'recommend'],
  isExperimental: true,
  domains: ['soil', 'environment', 'climate'],
};

/**
 * VAYU (वायु) — Climate/Weather Intelligence (Planned)
 * Weather patterns, climate risk, growing degree days
 */
const VAYU: AgentDefinition = {
  id: 'vayu',
  name: 'Vayu',
  shortName: 'VYU',
  description: 'Climate and weather intelligence. Analyzes weather patterns, predicts risks, and calculates growing conditions.',
  icon: 'Wind',  // Lucide icon
  color: 'sky',
  capabilities: ['chat', 'analyze', 'recommend'],
  isExperimental: true,
  domains: ['climate', 'weather', 'phenology'],
};

/**
 * ARTHA (अर्थ) — Economic Intelligence (Planned)
 * Market analysis, cost-benefit, economic viability
 */
const ARTHA: AgentDefinition = {
  id: 'artha',
  name: 'Artha',
  shortName: 'ATH',
  description: 'Agricultural economics intelligence. Market analysis, cost-benefit calculations, and economic viability assessment.',
  icon: 'TrendingUp',  // Lucide icon
  color: 'violet',
  capabilities: ['chat', 'analyze', 'recommend'],
  isExperimental: true,
  domains: ['economics', 'market', 'commercial'],
};

/**
 * The Agent Registry
 */
export const AGENT_REGISTRY: AgentRegistry = {
  agents: [
    REEVU_AGENT,
    REEVA,
    PRITHVI,
    VAYU,
    ARTHA,
  ],
  orchestratorId: LEGACY_REEVU_ORCHESTRATOR_ID,
  version: '1.0.0',
};

/**
 * Get agent by ID
 */
export function getAgent(id: string): AgentDefinition | undefined {
  return AGENT_REGISTRY.agents.find(a => a.id === id);
}

/**
 * Get the orchestrator agent
 */
export function getOrchestrator(): AgentDefinition {
  const orchestrator = AGENT_REGISTRY.agents.find(a => a.isOrchestrator);
  if (!orchestrator) {
    throw new Error('No orchestrator agent defined in registry');
  }
  return orchestrator;
}

/**
 * Get all active (non-experimental or explicitly enabled) agents
 */
export function getActiveAgents(): AgentDefinition[] {
  // For now, return all agents. Later, filter by user preferences
  return AGENT_REGISTRY.agents;
}

/**
 * Get agents by domain
 */
export function getAgentsByDomain(domain: string): AgentDefinition[] {
  return AGENT_REGISTRY.agents.filter(a => a.domains?.includes(domain));
}
