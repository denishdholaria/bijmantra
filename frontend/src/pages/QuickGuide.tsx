/**
 * Quick Guide - Interactive Onboarding
 * Step-by-step guide for new users
 */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'

interface GuideStep {
  id: number
  title: string
  description: string
  icon: string
  details: string[]
  action?: { label: string; link: string }
  tip?: string
}

const guideSteps: GuideStep[] = [
  {
    id: 1,
    title: 'Create a Breeding Program',
    description: 'Start by setting up your breeding program',
    icon: '🌾',
    details: [
      'Go to Programs → New Program',
      'Enter program name and abbreviation',
      'Add objective and description',
      'Set the lead person (optional)',
      'Save your program'
    ],
    action: { label: 'Create Program', link: '/programs/new' },
    tip: 'A program is the top-level container for all your breeding activities'
  },
  {
    id: 2,
    title: 'Add Locations',
    description: 'Define where your trials will be conducted',
    icon: '📍',
    details: [
      'Go to Locations → New Location',
      'Enter location name and type',
      'Add GPS coordinates (optional)',
      'Specify country and region',
      'Save the location'
    ],
    action: { label: 'Add Location', link: '/locations/new' },
    tip: 'Locations can be fields, greenhouses, labs, or any research site'
  },
  {
    id: 3,
    title: 'Register Germplasm',
    description: 'Add your genetic material to the system',
    icon: '🌱',
    details: [
      'Go to Germplasm → New Germplasm',
      'Enter germplasm name and ID',
      'Specify species and genus',
      'Add pedigree information (optional)',
      'Include any attributes'
    ],
    action: { label: 'Add Germplasm', link: '/germplasm/new' },
    tip: 'Germplasm can be varieties, lines, populations, or any genetic material'
  },
  {
    id: 4,
    title: 'Define Traits',
    description: 'Set up the traits you want to measure',
    icon: '🔬',
    details: [
      'Go to Traits → New Trait',
      'Enter trait name and description',
      'Select measurement scale (numeric, categorical, etc.)',
      'Define valid values or ranges',
      'Link to ontology terms (optional)'
    ],
    action: { label: 'Create Trait', link: '/traits/new' },
    tip: 'Use standard ontology terms when possible for data interoperability'
  },
  {
    id: 5,
    title: 'Create a Trial',
    description: 'Set up your field experiment',
    icon: '🧪',
    details: [
      'Go to Trials → New Trial',
      'Link to your breeding program',
      'Add trial name and dates',
      'Select location(s)',
      'Define the experimental design'
    ],
    action: { label: 'Create Trial', link: '/trials/new' },
    tip: 'Trials contain one or more studies with specific designs'
  },
  {
    id: 6,
    title: 'Collect Data',
    description: 'Record observations in the field',
    icon: '📋',
    details: [
      'Go to Data Collection',
      'Select your study',
      'Choose traits to measure',
      'Enter observations for each plot',
      'Save and sync data'
    ],
    action: { label: 'Collect Data', link: '/observations/collect' },
    tip: 'Use the Field Book for mobile-friendly data collection'
  },
  {
    id: 7,
    title: 'Analyze Results',
    description: 'Use analysis tools to make decisions',
    icon: '📊',
    details: [
      'View statistics and summaries',
      'Calculate selection indices',
      'Estimate genetic gain',
      'Compare varieties',
      'Generate reports'
    ],
    action: { label: 'View Statistics', link: '/statistics' },
    tip: 'Use AI Assistant for intelligent data analysis'
  },
  {
    id: 8,
    title: 'Make Selections',
    description: 'Select the best performers for advancement',
    icon: '✅',
    details: [
      'Review phenotypic data',
      'Apply selection criteria',
      'Use selection index tools',
      'Mark selected germplasm',
      'Plan crosses for next cycle'
    ],
    action: { label: 'Selection Index', link: '/selectionindex' },
    tip: 'Document your selection decisions for future reference'
  }
]

export function QuickGuide() {
  const [currentStep, setCurrentStep] = useState(0)
  const [completedSteps, setCompletedSteps] = useState<number[]>([])

  const progress = (completedSteps.length / guideSteps.length) * 100

  const toggleComplete = (stepId: number) => {
    setCompletedSteps(prev => 
      prev.includes(stepId) 
        ? prev.filter(id => id !== stepId)
        : [...prev, stepId]
    )
  }

  const currentStepData = guideSteps[currentStep]

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Quick Start Guide</h1>
          <p className="text-muted-foreground mt-1">Get started with Bijmantra in 8 easy steps</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-sm font-medium">{completedSteps.length} of {guideSteps.length} complete</p>
            <Progress value={progress} className="w-32 h-2" />
          </div>
          <Link to="/help">
            <Button variant="outline">📚 Help Center</Button>
          </Link>
        </div>
      </div>

      {/* Progress Overview */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-2">
            {guideSteps.map((step, index) => (
              <Button
                key={step.id}
                variant={currentStep === index ? 'default' : completedSteps.includes(step.id) ? 'secondary' : 'outline'}
                size="sm"
                onClick={() => setCurrentStep(index)}
                className="relative"
              >
                {completedSteps.includes(step.id) && (
                  <span className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full flex items-center justify-center text-white text-xs">✓</span>
                )}
                {step.icon} Step {step.id}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Current Step Detail */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-4xl">{currentStepData.icon}</span>
                <div>
                  <Badge variant="outline" className="mb-1">Step {currentStepData.id}</Badge>
                  <CardTitle>{currentStepData.title}</CardTitle>
                  <CardDescription>{currentStepData.description}</CardDescription>
                </div>
              </div>
              <Button
                variant={completedSteps.includes(currentStepData.id) ? 'secondary' : 'outline'}
                onClick={() => toggleComplete(currentStepData.id)}
              >
                {completedSteps.includes(currentStepData.id) ? '✓ Completed' : 'Mark Complete'}
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <h4 className="font-medium mb-3">How to do it:</h4>
              <ol className="space-y-2">
                {currentStepData.details.map((detail, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="flex-shrink-0 w-6 h-6 bg-primary/10 text-primary rounded-full flex items-center justify-center text-sm font-medium">
                      {i + 1}
                    </span>
                    <span>{detail}</span>
                  </li>
                ))}
              </ol>
            </div>

            {currentStepData.tip && (
              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-sm">
                  <span className="font-medium text-blue-800">💡 Pro Tip:</span>{' '}
                  <span className="text-blue-700">{currentStepData.tip}</span>
                </p>
              </div>
            )}

            <div className="flex items-center justify-between pt-4 border-t">
              <Button
                variant="outline"
                onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
                disabled={currentStep === 0}
              >
                ← Previous
              </Button>
              <div className="flex gap-2">
                {currentStepData.action && (
                  <Link to={currentStepData.action.link}>
                    <Button>{currentStepData.action.label} →</Button>
                  </Link>
                )}
              </div>
              <Button
                variant="outline"
                onClick={() => setCurrentStep(Math.min(guideSteps.length - 1, currentStep + 1))}
                disabled={currentStep === guideSteps.length - 1}
              >
                Next →
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Sidebar */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">All Steps</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {guideSteps.map((step, index) => (
                <button
                  key={step.id}
                  onClick={() => setCurrentStep(index)}
                  className={`w-full text-left p-2 rounded-lg transition-colors flex items-center gap-2 ${
                    currentStep === index 
                      ? 'bg-primary text-primary-foreground' 
                      : completedSteps.includes(step.id)
                        ? 'bg-green-50 text-green-700'
                        : 'hover:bg-muted'
                  }`}
                >
                  <span>{step.icon}</span>
                  <span className="text-sm flex-1">{step.title}</span>
                  {completedSteps.includes(step.id) && <span>✓</span>}
                </button>
              ))}
            </CardContent>
          </Card>

          <Card className="border-green-200 bg-green-50">
            <CardContent className="pt-4">
              <div className="text-center">
                <span className="text-3xl">🤖</span>
                <h4 className="font-medium mt-2">Need Help?</h4>
                <p className="text-sm text-muted-foreground mt-1">
                  Ask our AI assistant for guidance
                </p>
                <Link to="/ai-assistant">
                  <Button size="sm" className="mt-3">Ask AI</Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Completion Message */}
      {completedSteps.length === guideSteps.length && (
        <Card className="border-green-200 bg-green-50">
          <CardContent className="pt-6">
            <div className="text-center">
              <span className="text-6xl">🎉</span>
              <h3 className="text-xl font-bold mt-4 text-green-800">Congratulations!</h3>
              <p className="text-green-700 mt-2">
                You've completed the Quick Start Guide. You're ready to start breeding!
              </p>
              <div className="flex justify-center gap-3 mt-4">
                <Link to="/dashboard">
                  <Button>Go to Dashboard</Button>
                </Link>
                <Link to="/help">
                  <Button variant="outline">Explore More</Button>
                </Link>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
