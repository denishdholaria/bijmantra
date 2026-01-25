/**
 * API Key Notice Component
 * 
 * Displays a professional info notice when external API keys are required.
 * Provides guidance on where to obtain keys and how to configure them.
 */

import { Info, ExternalLink, Settings, AlertTriangle } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

// =============================================================================
// External Service Configuration
// =============================================================================

export interface ExternalService {
  id: string
  name: string
  description: string
  envVar: string
  docsUrl: string
  signupUrl: string
  freeTier: boolean
  freeTierDetails?: string
  configPath: string
  category: 'weather' | 'ai' | 'maps' | 'analytics' | 'storage' | 'other'
}

export const EXTERNAL_SERVICES: Record<string, ExternalService> = {
  // Weather Services
  openweathermap: {
    id: 'openweathermap',
    name: 'OpenWeatherMap',
    description: 'Weather data, forecasts, and historical climate information',
    envVar: 'OPENWEATHERMAP_API_KEY',
    docsUrl: 'https://openweathermap.org/api',
    signupUrl: 'https://home.openweathermap.org/users/sign_up',
    freeTier: true,
    freeTierDetails: 'Free tier — 1,000 calls/day, T&C apply',
    configPath: '/settings/integrations',
    category: 'weather',
  },
  visualcrossing: {
    id: 'visualcrossing',
    name: 'Visual Crossing',
    description: 'Historical weather data and climate analysis',
    envVar: 'VISUALCROSSING_API_KEY',
    docsUrl: 'https://www.visualcrossing.com/resources/documentation/',
    signupUrl: 'https://www.visualcrossing.com/sign-up',
    freeTier: true,
    freeTierDetails: 'Free tier — 1,000 records/day, T&C apply',
    configPath: '/settings/integrations',
    category: 'weather',
  },

  // AI Services - Google Gemini first (free API key from AI Studio)
  google_ai: {
    id: 'google_ai',
    name: 'Google Gemini',
    description: 'Free API key from Google AI Studio. Usage limits apply.',
    envVar: 'GOOGLE_AI_API_KEY',
    docsUrl: 'https://ai.google.dev/docs',
    signupUrl: 'https://aistudio.google.com/apikey',
    freeTier: true,
    freeTierDetails: 'Free tier available — usage limits & Google T&C apply',
    configPath: '/settings/ai',
    category: 'ai',
  },
  groq: {
    id: 'groq',
    name: 'Groq',
    description: 'Fast inference for open-source LLMs',
    envVar: 'GROQ_API_KEY',
    docsUrl: 'https://console.groq.com/docs',
    signupUrl: 'https://console.groq.com/',
    freeTier: true,
    freeTierDetails: 'Free tier — rate limits & Groq T&C apply',
    configPath: '/settings/ai',
    category: 'ai',
  },
  openai: {
    id: 'openai',
    name: 'OpenAI',
    description: 'GPT models for AI-powered features',
    envVar: 'OPENAI_API_KEY',
    docsUrl: 'https://platform.openai.com/docs',
    signupUrl: 'https://platform.openai.com/signup',
    freeTier: false,
    freeTierDetails: 'Paid: Requires billing setup',
    configPath: '/settings/ai',
    category: 'ai',
  },
  anthropic: {
    id: 'anthropic',
    name: 'Anthropic Claude',
    description: 'Claude models for AI-powered features',
    envVar: 'ANTHROPIC_API_KEY',
    docsUrl: 'https://docs.anthropic.com/',
    signupUrl: 'https://console.anthropic.com/',
    freeTier: false,
    freeTierDetails: 'Paid: Requires billing setup',
    configPath: '/settings/ai',
    category: 'ai',
  },

  // Maps & Geolocation
  mapbox: {
    id: 'mapbox',
    name: 'Mapbox',
    description: 'Maps, geocoding, and spatial analysis',
    envVar: 'MAPBOX_ACCESS_TOKEN',
    docsUrl: 'https://docs.mapbox.com/',
    signupUrl: 'https://account.mapbox.com/auth/signup/',
    freeTier: true,
    freeTierDetails: 'Free tier — 50K loads/month, T&C apply',
    configPath: '/settings/integrations',
    category: 'maps',
  },

  // Analytics
  nasa_power: {
    id: 'nasa_power',
    name: 'NASA POWER',
    description: 'Solar radiation and meteorological data',
    envVar: 'NASA_POWER_API_KEY',
    docsUrl: 'https://power.larc.nasa.gov/docs/',
    signupUrl: 'https://power.larc.nasa.gov/',
    freeTier: true,
    freeTierDetails: 'Free, no API key required for basic access',
    configPath: '/settings/integrations',
    category: 'analytics',
  },
}

// =============================================================================
// Hook Types
// =============================================================================

interface ServiceStatusResponse {
  id: string
  name: string
  category: string
  configured: boolean
  available: boolean
  free_tier: boolean
  env_var: string
  config_path: string
  message?: string
}

interface AllServicesStatusResponse {
  services: Record<string, ServiceStatusResponse>
  summary: Record<string, number>
}

// =============================================================================
// Hooks for checking API key status
// =============================================================================

/**
 * Hook to check if a specific service is configured
 * Fetches status from backend API
 */
export function useServiceStatus(serviceId: keyof typeof EXTERNAL_SERVICES) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['external-service-status', serviceId],
    queryFn: async () => {
      const response = await fetch(`/api/v2/external-services/status/${serviceId}`)
      if (!response.ok) {
        throw new Error('Failed to fetch service status')
      }
      return response.json() as Promise<ServiceStatusResponse>
    },
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    retry: 1,
  })

  return {
    isConfigured: data?.configured ?? false,
    isAvailable: data?.available ?? false,
    isLoading,
    error,
    service: EXTERNAL_SERVICES[serviceId],
    backendStatus: data,
  }
}

/**
 * Hook to check status of all external services
 * Useful for settings pages or dashboards
 */
export function useAllServicesStatus() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['external-services-status'],
    queryFn: async () => {
      const response = await fetch('/api/v2/external-services/status')
      if (!response.ok) {
        throw new Error('Failed to fetch services status')
      }
      return response.json() as Promise<AllServicesStatusResponse>
    },
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    retry: 1,
  })

  return {
    services: data?.services ?? {},
    summary: data?.summary ?? {},
    isLoading,
    error,
    refetch,
  }
}

// =============================================================================
// Components
// =============================================================================

interface ApiKeyNoticeProps {
  serviceId: keyof typeof EXTERNAL_SERVICES
  variant?: 'inline' | 'banner' | 'icon'
  className?: string
  /** If true, hides the notice when service is configured. Default: false (always show) */
  hideWhenConfigured?: boolean
}

/**
 * Displays an API key requirement notice for a specific service
 */
export function ApiKeyNotice({ serviceId, variant = 'inline', className, hideWhenConfigured = false }: ApiKeyNoticeProps) {
  const service = EXTERNAL_SERVICES[serviceId]
  const navigate = useNavigate()
  const { isConfigured, isLoading } = useServiceStatus(serviceId)

  if (!service) {
    console.warn(`Unknown service: ${serviceId}`)
    return null
  }

  // Hide if configured and hideWhenConfigured is true
  if (hideWhenConfigured && isConfigured && !isLoading) {
    return null
  }

  if (variant === 'icon') {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Dialog>
              <DialogTrigger asChild>
                <button className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors">
                  <Info className="w-3 h-3" />
                </button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2">
                    <Settings className="w-5 h-5" />
                    {service.name} Configuration Required
                  </DialogTitle>
                  <DialogDescription>
                    This feature requires an API key to function.
                  </DialogDescription>
                </DialogHeader>
                <ServiceDetails service={service} onConfigure={() => navigate(service.configPath)} />
              </DialogContent>
            </Dialog>
          </TooltipTrigger>
          <TooltipContent>
            <p>API key required - click for details</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    )
  }

  if (variant === 'banner') {
    return (
      <Alert className={className}>
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle className="flex items-center gap-2">
          {service.name} API Key Required
        </AlertTitle>
        <AlertDescription className="mt-2">
          <p className="text-sm mb-3">{service.description}</p>
          <ServiceDetails service={service} onConfigure={() => navigate(service.configPath)} compact />
        </AlertDescription>
      </Alert>
    )
  }

  // Default: inline
  return (
    <div className={`flex items-start gap-3 p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 ${className}`}>
      <Info className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
          {service.name} API Key Required
        </p>
        <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
          {service.description}
        </p>
        <div className="flex flex-wrap gap-2 mt-2">
          <Button size="sm" variant="outline" className="h-7 text-xs" onClick={() => navigate(service.configPath)}>
            <Settings className="w-3 h-3 mr-1" />
            Configure
          </Button>
          <Button size="sm" variant="ghost" className="h-7 text-xs" asChild>
            <a href={service.signupUrl} target="_blank" rel="noopener noreferrer">
              <ExternalLink className="w-3 h-3 mr-1" />
              Get API Key
            </a>
          </Button>
        </div>
      </div>
    </div>
  )
}

interface ServiceDetailsProps {
  service: ExternalService
  onConfigure: () => void
  compact?: boolean
}

function ServiceDetails({ service, onConfigure, compact }: ServiceDetailsProps) {
  if (compact) {
    return (
      <div className="flex flex-wrap gap-2">
        <Button size="sm" variant="outline" onClick={onConfigure}>
          <Settings className="w-4 h-4 mr-1" />
          Configure
        </Button>
        <Button size="sm" variant="ghost" asChild>
          <a href={service.signupUrl} target="_blank" rel="noopener noreferrer">
            <ExternalLink className="w-4 h-4 mr-1" />
            Get API Key
          </a>
        </Button>
        {service.freeTier && (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300">
            ✓ {service.freeTierDetails || 'Free tier available'}
          </span>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4 mt-4">
      <div className="grid gap-3">
        <div className="flex items-center justify-between p-3 rounded-lg bg-muted">
          <span className="text-sm text-muted-foreground">Environment Variable</span>
          <code className="text-sm font-mono bg-background px-2 py-1 rounded">{service.envVar}</code>
        </div>
        
        {service.freeTier && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-green-50 dark:bg-green-900/20">
            <span className="text-green-600 dark:text-green-400">✓</span>
            <span className="text-sm text-green-700 dark:text-green-300">
              {service.freeTierDetails || 'Free tier available'}
            </span>
          </div>
        )}
      </div>

      <div className="flex flex-col gap-2">
        <Button onClick={onConfigure} className="w-full">
          <Settings className="w-4 h-4 mr-2" />
          Configure in Settings
        </Button>
        
        <div className="grid grid-cols-2 gap-2">
          <Button variant="outline" asChild>
            <a href={service.signupUrl} target="_blank" rel="noopener noreferrer">
              <ExternalLink className="w-4 h-4 mr-2" />
              Sign Up
            </a>
          </Button>
          <Button variant="outline" asChild>
            <a href={service.docsUrl} target="_blank" rel="noopener noreferrer">
              <ExternalLink className="w-4 h-4 mr-2" />
              Documentation
            </a>
          </Button>
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// Multi-Service Notice
// =============================================================================

interface MultiServiceNoticeProps {
  serviceIds: (keyof typeof EXTERNAL_SERVICES)[]
  title?: string
  className?: string
}

/**
 * Displays a notice for multiple required services
 */
export function MultiServiceNotice({ serviceIds, title, className }: MultiServiceNoticeProps) {
  const services = serviceIds.map(id => EXTERNAL_SERVICES[id]).filter(Boolean)
  const navigate = useNavigate()

  if (services.length === 0) return null

  return (
    <Alert className={className}>
      <Info className="h-4 w-4" />
      <AlertTitle>{title || 'External Services Required'}</AlertTitle>
      <AlertDescription className="mt-2">
        <p className="text-sm mb-3">
          This feature requires configuration of the following external services:
        </p>
        <div className="space-y-2">
          {services.map(service => (
            <div key={service.id} className="flex items-center justify-between p-2 rounded bg-muted">
              <div>
                <span className="text-sm font-medium">{service.name}</span>
                {service.freeTier && (
                  <span className="ml-2 text-xs text-green-600 dark:text-green-400">
                    (Free tier available)
                  </span>
                )}
              </div>
              <Button size="sm" variant="ghost" asChild>
                <a href={service.signupUrl} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="w-3 h-3" />
                </a>
              </Button>
            </div>
          ))}
        </div>
        <Button size="sm" className="mt-3" onClick={() => navigate('/settings/integrations')}>
          <Settings className="w-4 h-4 mr-2" />
          Configure All
        </Button>
      </AlertDescription>
    </Alert>
  )
}

export default ApiKeyNotice
