/**
 * Onboarding Tour Component
 * 
 * Guides new users through the main features of Bijmantra.
 * Shows on first visit and can be replayed from settings.
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Dialog,
  DialogContent,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import {
  Sprout,
  Warehouse,
  Globe,
  Building2,
  Smartphone,
  Keyboard,
  Sparkles,
  ArrowRight,
  ArrowLeft,
  X,
  type LucideIcon,
} from 'lucide-react'

interface TourStep {
  id: string
  title: string
  description: string
  icon: LucideIcon
  color: string
  route?: string
}

const tourSteps: TourStep[] = [
  {
    id: 'welcome',
    title: 'Welcome to Bijmantra! 🌱',
    description: 'Your comprehensive platform for plant breeding, seed management, and agricultural research. Let\'s take a quick tour of the main features.',
    icon: Sprout,
    color: 'from-green-500 to-emerald-500',
  },
  {
    id: 'plant-sciences',
    title: 'Plant Sciences',
    description: 'Manage breeding programs, trials, germplasm, crosses, and genomic data. Track pedigrees, calculate breeding values, and make data-driven selection decisions.',
    icon: Sprout,
    color: 'from-green-500 to-emerald-500',
    route: '/programs',
  },
  {
    id: 'seed-bank',
    title: 'Seed Bank',
    description: 'Conserve genetic resources with vault management, accession tracking, viability testing, and germplasm exchange. MCPD-compliant for international standards.',
    icon: Warehouse,
    color: 'from-amber-500 to-yellow-500',
    route: '/seed-bank',
  },
  {
    id: 'environment',
    title: 'Environment',
    description: 'Monitor weather, climate, soil conditions, and solar radiation. Plan field operations based on environmental data and growing degree days.',
    icon: Globe,
    color: 'from-blue-500 to-cyan-500',
    route: '/earth-systems',
  },
  {
    id: 'seed-commerce',
    title: 'Seed Commerce',
    description: 'Complete seed business operations: lab testing, processing, inventory, dispatch, DUS testing, and variety licensing. Track seed lots from production to sale.',
    icon: Building2,
    color: 'from-indigo-500 to-purple-500',
    route: '/seed-operations',
  },
  {
    id: 'mobile',
    title: 'Mobile-Ready PWA',
    description: 'Use Bijmantra in the field! Install as an app on your phone, work offline, and sync when connected. The bottom navigation and quick action button make field work easy.',
    icon: Smartphone,
    color: 'from-pink-500 to-rose-500',
  },
  {
    id: 'shortcuts',
    title: 'Power User Tips',
    description: 'Press ⌘K to open the command palette for quick navigation. Press ? to see all keyboard shortcuts. Use the search to find anything instantly.',
    icon: Keyboard,
    color: 'from-violet-500 to-purple-500',
  },
  {
    id: 'done',
    title: 'You\'re All Set! 🎉',
    description: 'Start exploring Bijmantra. Check out the Dashboard for an overview, or dive into any module. Need help? Visit the Knowledge section or ask Veena, our AI assistant.',
    icon: Sparkles,
    color: 'from-yellow-500 to-orange-500',
    route: '/dashboard',
  },
]

const TOUR_COMPLETED_KEY = 'bijmantra_tour_completed'

interface OnboardingTourProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onComplete?: () => void
}

export function OnboardingTour({ open, onOpenChange, onComplete }: OnboardingTourProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const navigate = useNavigate()
  
  const step = tourSteps[currentStep]
  const progress = ((currentStep + 1) / tourSteps.length) * 100
  const isLastStep = currentStep === tourSteps.length - 1
  const isFirstStep = currentStep === 0

  const handleNext = () => {
    if (isLastStep) {
      handleComplete()
    } else {
      setCurrentStep(prev => prev + 1)
    }
  }

  const handlePrev = () => {
    if (!isFirstStep) {
      setCurrentStep(prev => prev - 1)
    }
  }

  const handleComplete = () => {
    localStorage.setItem(TOUR_COMPLETED_KEY, 'true')
    onOpenChange(false)
    onComplete?.()
    if (step.route) {
      navigate(step.route)
    }
  }

  const handleSkip = () => {
    localStorage.setItem(TOUR_COMPLETED_KEY, 'true')
    onOpenChange(false)
  }

  const Icon = step.icon

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md p-0 overflow-hidden">
        {/* Header with gradient */}
        <div className={`bg-gradient-to-br ${step.color} p-6 text-white`}>
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
              <Icon className="w-6 h-6" />
            </div>
            <button
              onClick={handleSkip}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              aria-label="Skip tour"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <h2 className="text-xl font-bold mb-2">{step.title}</h2>
          <p className="text-white/90 text-sm leading-relaxed">
            {step.description}
          </p>
        </div>

        {/* Progress and navigation */}
        <div className="p-4">
          <Progress value={progress} className="h-1 mb-4" />
          
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              {currentStep + 1} of {tourSteps.length}
            </div>
            
            <div className="flex items-center gap-2">
              {!isFirstStep && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handlePrev}
                >
                  <ArrowLeft className="w-4 h-4 mr-1" />
                  Back
                </Button>
              )}
              <Button
                size="sm"
                onClick={handleNext}
                className={`bg-gradient-to-r ${step.color} text-white border-0`}
              >
                {isLastStep ? 'Get Started' : 'Next'}
                {!isLastStep && <ArrowRight className="w-4 h-4 ml-1" />}
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

// Hook to manage onboarding tour
// NOTE: Auto-show disabled - users can manually trigger via Help menu
export function useOnboardingTour() {
  const [showTour, setShowTour] = useState(false)

  // Auto-show disabled to reduce interruptions on login
  // useEffect(() => {
  //   const tourCompleted = localStorage.getItem(TOUR_COMPLETED_KEY)
  //   if (!tourCompleted) {
  //     const timer = setTimeout(() => {
  //       setShowTour(true)
  //     }, 1000)
  //     return () => clearTimeout(timer)
  //   }
  // }, [])

  const resetTour = () => {
    localStorage.removeItem(TOUR_COMPLETED_KEY)
    setShowTour(true)
  }

  return {
    showTour,
    setShowTour,
    resetTour,
  }
}

export default OnboardingTour
