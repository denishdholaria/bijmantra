/**
 * Inspiration Museum (Prerna - प्रेरणा)
 * A virtual museum for late-night researchers, scientists, and dreamers
 */
import { useState, useEffect, lazy, Suspense } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { Link } from 'react-router-dom'

// Lazy load Three.js scene to prevent blocking
const InspirationScene = lazy(() => 
  import('@/components/three/InspirationScene')
    .catch(() => ({ default: () => <></> as React.ReactElement }))
)

interface Quote {
  text: string
  author: string
  source?: string
  category: 'perseverance' | 'science' | 'agriculture' | 'wisdom' | 'courage'
}

const quotes: Quote[] = [
  {
    text: "People are often unreasonable, illogical, and self-centered. Forgive them anyway. If you are kind, people may accuse you of selfish ulterior motives. Be kind anyway. If you are successful, you will win some false friends and some true enemies. Succeed anyway. If you are honest and frank, people may cheat you. Be honest and frank anyway. What you spend years building, someone could destroy overnight. Build anyway. If you find serenity and happiness, they may be jealous. Be happy anyway. The good you do today, people will often forget tomorrow. Do good anyway. Give the world the best you have, and it may never be enough. Give the best you've got anyway. You see, in the final analysis it is between you and God; it was never between you and them anyway.",
    author: "Kent M. Keith",
    source: "The Paradoxical Commandments (1968), popularized by Mother Teresa",
    category: 'perseverance'
  },
  {
    text: "The nitrogen in our DNA, the calcium in our teeth, the iron in our blood, the carbon in our apple pies were made in the interiors of collapsing stars. We are made of starstuff.",
    author: "Carl Sagan",
    source: "Cosmos",
    category: 'science'
  },
  {
    text: "The good thing about science is that it's true whether or not you believe in it.",
    author: "Neil deGrasse Tyson",
    category: 'science'
  },
  {
    text: "Agriculture is our wisest pursuit, because it will in the end contribute most to real wealth, good morals, and happiness.",
    author: "Thomas Jefferson",
    category: 'agriculture'
  },
  {
    text: "The farmer has to be an optimist or he wouldn't still be a farmer.",
    author: "Will Rogers",
    category: 'agriculture'
  },
  {
    text: "In the middle of difficulty lies opportunity.",
    author: "Albert Einstein",
    category: 'perseverance'
  },
  {
    text: "It is not the strongest of the species that survives, nor the most intelligent, but the one most responsive to change.",
    author: "Charles Darwin",
    category: 'science'
  },
  {
    text: "The best time to plant a tree was 20 years ago. The second best time is now.",
    author: "Chinese Proverb",
    category: 'wisdom'
  },
  {
    text: "We do not inherit the earth from our ancestors; we borrow it from our children.",
    author: "Native American Proverb",
    category: 'wisdom'
  },
  {
    text: "Nothing in life is to be feared, it is only to be understood. Now is the time to understand more, so that we may fear less.",
    author: "Marie Curie",
    category: 'courage'
  },
  {
    text: "The important thing is not to stop questioning. Curiosity has its own reason for existing.",
    author: "Albert Einstein",
    category: 'science'
  },
  {
    text: "Science knows no country, because knowledge belongs to humanity, and is the torch which illuminates the world.",
    author: "Louis Pasteur",
    category: 'science'
  },
  {
    text: "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन। (You have the right to work, but never to the fruit of work.)",
    author: "Bhagavad Gita",
    source: "Chapter 2, Verse 47",
    category: 'wisdom'
  },
  {
    text: "The seeds we plant today determine the harvest our children will reap tomorrow.",
    author: "Hare Krishna",
    source: "Bijmantra",
    category: 'agriculture'
  },
  {
    text: "I have not failed. I've just found 10,000 ways that won't work.",
    author: "Thomas Edison",
    category: 'perseverance'
  },
  {
    text: "The only way to do great work is to love what you do.",
    author: "Steve Jobs",
    category: 'perseverance'
  },
  {
    text: "Research is what I'm doing when I don't know what I'm doing.",
    author: "Wernher von Braun",
    category: 'science'
  },
  {
    text: "Somewhere, something incredible is waiting to be known.",
    author: "Carl Sagan",
    category: 'science'
  }
]

const categoryColors: Record<string, string> = {
  perseverance: 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300',
  science: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  agriculture: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  wisdom: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  courage: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300'
}

const categoryIcons: Record<string, string> = {
  perseverance: '💪',
  science: '🔬',
  agriculture: '🌾',
  wisdom: '🕯️',
  courage: '🦁'
}

export function Inspiration() {
  const [featuredQuote, setFeaturedQuote] = useState<Quote>(quotes[0])
  const [filter, setFilter] = useState<string | null>(null)
  const [show3D, setShow3D] = useState(true)

  useEffect(() => {
    // Rotate featured quote every 30 seconds
    const interval = setInterval(() => {
      const randomIndex = Math.floor(Math.random() * quotes.length)
      setFeaturedQuote(quotes[randomIndex])
    }, 30000)
    return () => clearInterval(interval)
  }, [])

  const filteredQuotes = filter 
    ? quotes.filter(q => q.category === filter)
    : quotes

  const getTimeGreeting = () => {
    const hour = new Date().getHours()
    if (hour >= 0 && hour < 5) return { text: "Burning the midnight oil?", emoji: "🌙", isNight: true }
    if (hour >= 5 && hour < 12) return { text: "Early bird catches the worm!", emoji: "🌅", isNight: false }
    if (hour >= 12 && hour < 17) return { text: "Afternoon focus time", emoji: "☀️", isNight: false }
    if (hour >= 17 && hour < 21) return { text: "Evening dedication", emoji: "🌆", isNight: false }
    return { text: "Night owl at work", emoji: "🦉", isNight: true }
  }

  const greeting = getTimeGreeting()

  return (
    <div className="relative min-h-screen">
      {/* 3D Background Scene */}
      {show3D && (
        <Suspense fallback={null}>
          <div className="fixed inset-0 -z-10 bg-gradient-to-b from-slate-900 via-indigo-950 to-slate-900">
            <InspirationScene />
          </div>
        </Suspense>
      )}
      
      {/* 3D Toggle Button - Top right to avoid Veena conflict */}
      <div className="fixed top-20 right-4 z-40">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShow3D(!show3D)}
          className={cn(
            "bg-background/80 backdrop-blur shadow-lg",
            show3D && "bg-indigo-600 text-white border-indigo-500 hover:bg-indigo-700"
          )}
        >
          {show3D ? '✨ 3D On' : '✨ 3D Off'}
        </Button>
      </div>

      <div className={`space-y-8 animate-fade-in max-w-5xl mx-auto relative z-10 ${show3D ? 'text-white' : ''}`}>
        {/* Hero Section */}
        <div className="text-center py-8">
          <div className="w-24 h-24 bg-gradient-to-br from-rose-500 to-orange-500 rounded-2xl flex items-center justify-center shadow-xl mx-auto mb-6 animate-pulse">
            <span className="text-5xl">🏛️</span>
          </div>
          <h1 className={`text-4xl lg:text-5xl font-bold ${show3D ? 'text-white drop-shadow-lg' : 'bg-gradient-to-r from-rose-600 to-orange-600 bg-clip-text text-transparent'}`}>
            Prerna (प्रेरणा)
          </h1>
          <p className={`text-2xl font-medium mt-3 ${show3D ? 'text-white/90' : 'text-foreground'}`}>
            The Inspiration Museum
          </p>
          <p className={`text-base mt-2 ${show3D ? 'text-white/70' : 'text-muted-foreground'}`}>
            For those who work when the world sleeps
          </p>
          <div className="flex items-center justify-center gap-2 mt-4">
            <Badge variant="secondary" className={`text-sm ${show3D ? 'bg-white/20 text-white border-white/30' : ''}`}>
              {greeting.emoji} {greeting.text}
            </Badge>
          </div>
        </div>

        {/* Featured Quote */}
        <Card className={`border-2 ${show3D ? 'bg-black/40 backdrop-blur-md border-rose-500/30' : 'border-rose-200 dark:border-rose-800 bg-gradient-to-br from-rose-50 via-pink-50 to-orange-50 dark:from-rose-950/30 dark:via-pink-950/30 dark:to-orange-950/30'}`}>
          <CardHeader className="text-center pb-2">
            <CardTitle className={`text-lg ${show3D ? 'text-rose-300' : 'text-rose-800 dark:text-rose-300'}`}>✨ Featured Inspiration</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`rounded-xl p-6 max-w-3xl mx-auto ${show3D ? 'bg-white/10 backdrop-blur' : 'bg-white/80 dark:bg-slate-800/80'}`}>
              <p className={`leading-relaxed italic text-center text-lg ${show3D ? 'text-white' : 'text-foreground'}`}>
                "{featuredQuote.text}"
              </p>
              <p className={`text-center text-sm mt-4 ${show3D ? 'text-white/70' : 'text-muted-foreground'}`}>
                — <span className="font-semibold">{featuredQuote.author}</span>
                {featuredQuote.source && <span className="block text-xs mt-1">{featuredQuote.source}</span>}
              </p>
              <div className="flex justify-center mt-4">
                <Badge className={categoryColors[featuredQuote.category]}>
                  {categoryIcons[featuredQuote.category]} {featuredQuote.category}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Late Night Message */}
        <Card className={`border-2 ${show3D ? 'bg-black/40 backdrop-blur-md border-indigo-500/30' : 'border-indigo-200 dark:border-indigo-800 bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-950/30 dark:to-purple-950/30'}`}>
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <span className="text-4xl">🌙</span>
              <h3 className={`text-xl font-semibold ${show3D ? 'text-indigo-300' : 'text-indigo-800 dark:text-indigo-300'}`}>
                To the Late-Night Researcher
              </h3>
              <p className={`max-w-2xl mx-auto leading-relaxed ${show3D ? 'text-white/90' : 'text-foreground'}`}>
                If you're reading this at 2 AM in a quiet lab, or 3 AM debugging code, or 4 AM 
                analyzing data — know that you're part of a long tradition of dedicated souls 
                who pushed the boundaries of human knowledge while the world slept.
              </p>
              <p className={`italic ${show3D ? 'text-white/70' : 'text-muted-foreground'}`}>
                Marie Curie worked late nights. Mendel tended his peas in solitude. 
                Darwin wrote by candlelight. You're in good company.
              </p>
              <p className={`font-semibold ${show3D ? 'text-indigo-300' : 'text-indigo-700 dark:text-indigo-400'}`}>
                Your work matters. Keep going. 💪
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Category Filter */}
        <div className="flex flex-wrap justify-center gap-2">
          <Button 
            variant={filter === null ? "default" : "outline"} 
            size="sm"
            onClick={() => setFilter(null)}
            className={show3D && filter !== null ? 'bg-white/10 border-white/30 text-white hover:bg-white/20' : ''}
          >
            All
          </Button>
          {Object.keys(categoryColors).map(cat => (
            <Button 
              key={cat}
              variant={filter === cat ? "default" : "outline"} 
              size="sm"
              onClick={() => setFilter(cat)}
              className={show3D && filter !== cat ? 'bg-white/10 border-white/30 text-white hover:bg-white/20' : ''}
            >
              {categoryIcons[cat]} {cat.charAt(0).toUpperCase() + cat.slice(1)}
            </Button>
          ))}
        </div>

        {/* Quote Gallery */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredQuotes.map((quote, index) => (
            <Card key={index} className={`hover:shadow-lg transition-shadow ${show3D ? 'bg-black/40 backdrop-blur-md border-white/20' : ''}`}>
              <CardContent className="pt-6">
                <p className={`italic leading-relaxed ${show3D ? 'text-white/90' : 'text-foreground'}`}>
                  "{quote.text.length > 200 ? quote.text.substring(0, 200) + '...' : quote.text}"
                </p>
                <div className="flex items-center justify-between mt-4">
                  <p className={`text-sm ${show3D ? 'text-white/70' : 'text-muted-foreground'}`}>
                    — {quote.author}
                  </p>
                  <Badge className={categoryColors[quote.category]} variant="secondary">
                    {categoryIcons[quote.category]}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Contribute Section */}
        <Card className={show3D ? 'bg-black/40 backdrop-blur-md border-white/20' : ''}>
          <CardHeader>
            <CardTitle className={`flex items-center gap-2 ${show3D ? 'text-white' : ''}`}>
              <span>💡</span> Share Your Inspiration
            </CardTitle>
            <CardDescription className={show3D ? 'text-white/70' : ''}>
              Know a quote that kept you going during tough times?
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className={`mb-4 ${show3D ? 'text-white/80' : 'text-muted-foreground'}`}>
              This museum grows with contributions from researchers worldwide. 
              If you have a quote, story, or piece of wisdom that helped you through 
              late nights and challenging research, we'd love to include it.
            </p>
            <Button variant="outline" className={show3D ? 'border-white/30 text-white hover:bg-white/20' : ''}>
              <span className="mr-2">📧</span> Submit a Quote
            </Button>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center py-8 space-y-4">
          <p className={`text-lg italic ${show3D ? 'text-white/80' : 'text-muted-foreground'}`}>
            🌾 Thank you to all those who work in acres, not in hours.
          </p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Link to="/about">
              <Button variant="outline" className={show3D ? 'border-white/30 text-white hover:bg-white/20' : ''}>
                <span className="mr-2">📖</span> About Bijmantra
              </Button>
            </Link>
            <Link to="/dashboard">
              <Button className={show3D ? 'bg-white/20 hover:bg-white/30 text-white' : ''}>
                <span className="mr-2">🏠</span> Back to Work
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
