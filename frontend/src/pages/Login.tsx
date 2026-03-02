/**
 * Login Page - Inspirational Multilingual Design
 * "One Seed. Infinite Worlds."
 * 
 * Featuring wisdom from agricultural cultures worldwide,
 * displayed in their original languages with English translations.
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, EyeOff } from 'lucide-react'
import { useAuthStore } from '@/store/auth'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { getWorkspace } from '@/framework/registry/workspaces'

interface Quote {
  original: string;
  translation: string;
  source: string;
  culture: string;
  icon: string;
  region: string;
}

// Multilingual quotes from agricultural cultures worldwide
// Each quote shown in original language + English translation
const quotes: Quote[] = [
  // Sanskrit / India - Nishkama Karma (Detachment)
  {
    original: "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन",
    translation: "You have the right to perform your duty, but never to the fruits of action.",
    source: "Bhagavad Gita 2.47",
    culture: "Sanskrit • India",
    icon: "🪷",
    region: "india"
  },
  // Sanskrit / India - The philosophical foundation
  {
    original: "योगः कर्मसु कौशलम्",
    translation: "Excellence in action is yoga.",
    source: "Bhagavad Gita 2.50",
    culture: "Sanskrit • India",
    icon: "🪷",
    region: "india"
  },
  // Chinese - Ancient agricultural civilization
  {
    original: "前人栽树，后人乘凉",
    translation: "One generation plants the trees; another gets the shade.",
    source: "Chinese Proverb",
    culture: "中文 • China",
    icon: "🌳",
    region: "east-asia"
  },
  // Japanese - Respect for nature
  {
    original: "実るほど頭を垂れる稲穂かな",
    translation: "The more the rice ripens, the more it bows its head.",
    source: "Japanese Proverb",
    culture: "日本語 • Japan",
    icon: "🌾",
    region: "east-asia"
  },
  // Korean - Patience in farming
  {
    original: "콩 심은 데 콩 나고 팥 심은 데 팥 난다",
    translation: "Plant beans, get beans; plant red beans, get red beans.",
    source: "Korean Proverb",
    culture: "한국어 • Korea",
    icon: "🫘",
    region: "east-asia"
  },
  // Arabic - Middle Eastern wisdom
  {
    original: "ازرع كل يوم تأكل كل يوم",
    translation: "Plant every day, eat every day.",
    source: "Arabic Proverb",
    culture: "العربية • Middle East",
    icon: "🌴",
    region: "middle-east"
  },
  // Persian - Ancient agricultural heritage
  {
    original: "درختی که تلخ است وی را سرشت، گرش برنشانی به باغ بهشت",
    translation: "A tree bitter by nature won't sweeten even in paradise's garden.",
    source: "Saadi Shirazi",
    culture: "فارسی • Persia",
    icon: "🏛️",
    region: "middle-east"
  },
  // Hebrew - Biblical agricultural wisdom
  {
    original: "הַזֹּרְעִים בְּדִמְעָה בְּרִנָּה יִקְצֹרוּ",
    translation: "Those who sow in tears shall reap in joy.",
    source: "Psalms 126:5",
    culture: "עברית • Israel",
    icon: "✡️",
    region: "middle-east"
  },
  // Swahili - East African wisdom
  {
    original: "Mkulima ni mfalme",
    translation: "The farmer is king.",
    source: "Swahili Proverb",
    culture: "Kiswahili • East Africa",
    icon: "👑",
    region: "africa"
  },
  // Amharic - Ethiopian coffee heritage
  {
    original: "የዛሬ ችግኝ የነገ ጥላ",
    translation: "Today's seedling is tomorrow's shade.",
    source: "Ethiopian Proverb",
    culture: "አማርኛ • Ethiopia",
    icon: "☕",
    region: "africa"
  },
  // Yoruba - West African agricultural wisdom
  {
    original: "Ẹni tó bá gbìn ọ̀gẹ̀dẹ̀, yóò jẹ ọ̀gẹ̀dẹ̀",
    translation: "He who plants plantain will eat plantain.",
    source: "Yoruba Proverb",
    culture: "Yorùbá • Nigeria",
    icon: "🍌",
    region: "africa"
  },
  // Spanish - Latin American heritage
  {
    original: "Quien siembra vientos, recoge tempestades",
    translation: "Who sows winds, reaps storms.",
    source: "Spanish Proverb",
    culture: "Español • Latin America",
    icon: "🌪️",
    region: "americas"
  },
  // Quechua - Andean agricultural wisdom (potato origin)
  {
    original: "Tarpuqqa mikhunqa",
    translation: "He who plants will eat.",
    source: "Quechua Wisdom",
    culture: "Quechua • Andes",
    icon: "🥔",
    region: "americas"
  },
  // Portuguese - Brazilian agricultural power
  {
    original: "Quem planta colhe",
    translation: "Who plants, harvests.",
    source: "Brazilian Proverb",
    culture: "Português • Brazil",
    icon: "🇧🇷",
    region: "americas"
  },
  // French - European agricultural tradition
  {
    original: "Petit à petit, l'oiseau fait son nid",
    translation: "Little by little, the bird builds its nest.",
    source: "French Proverb",
    culture: "Français • France",
    icon: "🐦",
    region: "europe"
  },
  // German - Precision and patience
  {
    original: "Was du heute kannst besorgen, das verschiebe nicht auf morgen",
    translation: "Don't put off until tomorrow what you can do today.",
    source: "German Proverb",
    culture: "Deutsch • Germany",
    icon: "⚙️",
    region: "europe"
  },
  // Italian - Mediterranean wisdom
  {
    original: "Chi semina raccoglie",
    translation: "Who sows, reaps.",
    source: "Italian Proverb",
    culture: "Italiano • Italy",
    icon: "🍇",
    region: "europe"
  },
  // Russian - Vast agricultural lands
  {
    original: "Что посеешь, то и пожнёшь",
    translation: "What you sow is what you reap.",
    source: "Russian Proverb",
    culture: "Русский • Russia",
    icon: "🌻",
    region: "europe"
  },
  // Native American - Respect for earth
  {
    original: "We do not inherit the earth from our ancestors",
    translation: "We borrow it from our children.",
    source: "Native American Wisdom",
    culture: "Indigenous • Americas",
    icon: "🦅",
    region: "americas"
  },
  // Bijmantra's own - English
  {
    original: "Thank you to all those who work in acres, not in hours.",
    translation: "For the farmers who feed the world.",
    source: "Bijmantra",
    culture: "English • Global",
    icon: "🌍",
    region: "global"
  },
  // Maori - Pacific agricultural wisdom
  {
    original: "Nāu te rourou, nāku te rourou, ka ora ai te iwi",
    translation: "With your basket and my basket, the people will thrive.",
    source: "Māori Proverb",
    culture: "Te Reo Māori • New Zealand",
    icon: "🥝",
    region: "oceania"
  },
  // Thai - Southeast Asian rice culture
  {
    original: "ปลูกเรือนตามใจผู้อยู่ ผูกอู่ตามใจผู้นอน",
    translation: "Build the house to suit the dweller, hang the cradle to suit the sleeper.",
    source: "Thai Proverb",
    culture: "ไทย • Thailand",
    icon: "🍚",
    region: "southeast-asia"
  },
  // Vietnamese - Rice civilization
  {
    original: "Có công mài sắt, có ngày nên kim",
    translation: "With enough grinding, an iron rod becomes a needle.",
    source: "Vietnamese Proverb",
    culture: "Tiếng Việt • Vietnam",
    icon: "🌾",
    region: "southeast-asia"
  },
    // Tamil / India - Ancient agricultural wisdom
  {
    original: "உழவுக்கும் தொழிலுக்கும் வந்தனை",
    translation: "Salutations to farming and labor.",
    source: "Tamil Wisdom",
    culture: "Tamil • India",
    icon: "🌿",
    region: "south-asia"
  },
]



// Region colors for visual variety - Prakruti Design System
const regionColors: Record<string, string> = {
  'india': 'from-orange-500/20 to-green-500/20',
  'south-asia': 'from-prakruti-sona/20 to-amber-500/20',
  'east-asia': 'from-red-500/20 to-rose-500/20',
  'middle-east': 'from-prakruti-sona/20 to-yellow-500/20',
  'africa': 'from-prakruti-patta/20 to-green-500/20',
  'americas': 'from-prakruti-neela/20 to-indigo-500/20',
  'europe': 'from-purple-500/20 to-violet-500/20',
  'oceania': 'from-cyan-500/20 to-teal-500/20',
  'southeast-asia': 'from-lime-500/20 to-green-500/20',
  'global': 'from-prakruti-patta/20 to-prakruti-patta-light/20',
}

export function Login() {
  const navigate = useNavigate()
  const { login, isLoading, error, clearError } = useAuthStore()
  const { preferences, setActiveWorkspace, dismissGateway } = useWorkspaceStore()
  
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [currentQuote, setCurrentQuote] = useState(0)
  const [isQuoteFading, setIsQuoteFading] = useState(false)

  // Rotate quotes every 10 seconds (longer for reading non-English)
  useEffect(() => {
    const interval = setInterval(() => {
      setIsQuoteFading(true)
      setTimeout(() => {
        setCurrentQuote((prev) => (prev + 1) % quotes.length)
        setIsQuoteFading(false)
      }, 500)
    }, 10000)
    return () => clearInterval(interval)
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()
    
    try {
      await login(email, password)
      
      // Determine where to navigate after login
      // If user has a default workspace and doesn't want to see gateway, go directly there
      if (preferences.defaultWorkspace && !preferences.showGatewayOnLogin) {
        const workspace = getWorkspace(preferences.defaultWorkspace)
        if (workspace) {
          setActiveWorkspace(preferences.defaultWorkspace)
          dismissGateway()
          navigate(workspace.landingRoute, { replace: true })
          return
        }
      }
      
      // Otherwise, show the workspace gateway
      navigate('/gateway', { replace: true })
    } catch (error) {
      // Error is handled by the store
    }
  }

  const quote = quotes[currentQuote]
  const regionColor = regionColors[quote.region] || regionColors['global']

  return (
    <div className="min-h-screen flex bg-slate-50 dark:bg-slate-950">
      {/* Left Panel - Multilingual Inspirational Content */}
      <div className="hidden lg:flex lg:w-1/2 xl:w-3/5 relative overflow-hidden bg-emerald-900 text-white">
        {/* Animated Background Gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-emerald-900 via-emerald-800 to-amber-950">
          {/* Animated circles */}
          <div className={`absolute top-20 left-20 w-72 h-72 bg-gradient-to-br ${regionColor} rounded-full blur-3xl animate-pulse transition-colors duration-1000 opacity-40`} />
          <div className="absolute bottom-20 right-20 w-96 h-96 bg-emerald-500/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
          <div className="absolute top-1/2 left-1/3 w-64 h-64 bg-amber-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }} />
        </div>

        {/* World map pattern overlay (subtle) */}
        <div className="absolute inset-0 opacity-[0.05]">
          <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <pattern id="world-pattern" x="0" y="0" width="25" height="25" patternUnits="userSpaceOnUse">
              <circle cx="12.5" cy="12.5" r="1" fill="white" />
              <circle cx="5" cy="5" r="0.5" fill="white" />
              <circle cx="20" cy="8" r="0.5" fill="white" />
              <circle cx="8" cy="20" r="0.5" fill="white" />
            </pattern>
            <rect width="100%" height="100%" fill="url(#world-pattern)" />
          </svg>
        </div>

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-between p-12 xl:p-16 w-full">
          {/* Top - Logo and Tagline */}
          <div>
            <div className="flex items-center gap-4 mb-4">
              <div className="w-16 h-16 bg-white/10 backdrop-blur-md rounded-2xl flex items-center justify-center shadow-2xl border border-white/10 p-3">
                <img src="/icons/icon-192x192.png" alt="Bijmantra" className="w-full h-full object-contain drop-shadow-md" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white tracking-tight">Bijmantra</h1>
                <p className="text-emerald-100/80 text-sm font-medium">One Seed. Infinite Worlds.</p>
              </div>
            </div>
          </div>

          {/* Middle - Rotating Multilingual Quote */}
          <div className="flex-1 flex items-center justify-center">
            <div 
              className={`max-w-2xl text-center transition-all duration-700 ease-out ${
                isQuoteFading ? 'opacity-0 translate-y-8 blur-sm' : 'opacity-100 translate-y-0 blur-0'
              }`}
            >
              {/* Icon */}
              <span className="text-7xl mb-8 block drop-shadow-2xl filter">{quote.icon}</span>
              
              {/* Original Language Quote */}
              <blockquote className="text-3xl xl:text-5xl font-medium text-white leading-tight mb-6 tracking-wide drop-shadow-sm font-serif">
                "{quote.original}"
              </blockquote>
              
              {/* English Translation */}
              <p className="text-xl text-emerald-100/90 italic mb-8 font-light">
                {quote.translation}
              </p>
              
              {/* Attribution */}
              <div className="flex items-center justify-center gap-3">
                <span className="px-3 py-1 bg-white/10 backdrop-blur-md rounded-full text-sm text-emerald-50 border border-white/20 shadow-sm">
                  {quote.culture}
                </span>
                <span className="text-emerald-200/80 text-sm font-medium">
                  — {quote.source}
                </span>
              </div>
            </div>
          </div>

          {/* Bottom - Quote Navigation */}
          <div>
            <div className="flex items-center justify-center gap-4">
              <button
                onClick={() => {
                  setIsQuoteFading(true)
                  setTimeout(() => {
                    setCurrentQuote((prev) => (prev - 1 + quotes.length) % quotes.length)
                    setIsQuoteFading(false)
                  }, 300)
                }}
                className="p-3 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 transition-all text-white hover:scale-110 active:scale-95"
                aria-label="Previous quote"
              >
                ←
              </button>
              
              <div className="flex gap-2 mx-4">
                {quotes.map((_, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setIsQuoteFading(true)
                      setTimeout(() => {
                        setCurrentQuote(i)
                        setIsQuoteFading(false)
                      }, 300)
                    }}
                    className={`h-1.5 rounded-full transition-all duration-500 ease-in-out ${
                      i === currentQuote 
                        ? 'bg-white w-8 shadow-[0_0_10px_rgba(255,255,255,0.5)]' 
                        : 'bg-white/20 w-1.5 hover:bg-white/40'
                    }`}
                    aria-label={`Go to quote ${i + 1}`}
                  />
                ))}
              </div>
              
              <button
                onClick={() => {
                  setIsQuoteFading(true)
                  setTimeout(() => {
                    setCurrentQuote((prev) => (prev + 1) % quotes.length)
                    setIsQuoteFading(false)
                  }, 300)
                }}
                className="p-3 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 transition-all text-white hover:scale-110 active:scale-95"
                aria-label="Next quote"
              >
                →
              </button>
            </div>
            
            <p className="text-center text-emerald-200/50 text-xs mt-6 font-medium tracking-wider uppercase">
              {currentQuote + 1} of {quotes.length} • Wisdom from around the world
            </p>
          </div>
        </div>
      </div>

      {/* Right Panel - Login Form */}
      <div className="w-full lg:w-1/2 xl:w-2/5 flex items-center justify-center p-6 sm:p-12 relative">
         {/* Subtle background texture for Right Panel */}
         <div className="absolute inset-0 bg-slate-50 dark:bg-slate-950">
            <div className="absolute inset-0 bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] [background-size:16px_16px] opacity-50 dark:opacity-5"></div>
            {/* Gradient Orb */}
            <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-emerald-100/40 dark:bg-emerald-900/10 rounded-full blur-[100px] pointer-events-none" />
            <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-amber-100/40 dark:bg-amber-900/10 rounded-full blur-[100px] pointer-events-none" />
         </div>

        <div className="w-full max-w-md animate-fade-in relative z-10 bg-white/60 dark:bg-slate-900/60 backdrop-blur-xl p-8 rounded-3xl border border-white/20 dark:border-slate-800 shadow-2xl shadow-slate-200/50 dark:shadow-slate-950/50">
          {/* Mobile Logo (hidden on desktop) */}
          <div className="lg:hidden text-center mb-10">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-emerald-900 rounded-2xl shadow-xl mb-4 overflow-hidden p-4">
              <img src="/icons/icon-192x192.png" alt="Bijmantra" className="w-full h-full object-contain filter drop-shadow-md" />
            </div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
              Bijmantra
            </h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm mt-1 font-medium">One Seed. Infinite Worlds.</p>
          </div>

          {/* Welcome Message */}
          <div className="mb-10 text-center lg:text-left">
            <h2 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">Welcome Back</h2>
            <p className="text-slate-500 dark:text-slate-400 mt-2 text-sm">
              Continue your journey in plant breeding excellence
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-8 p-4 bg-red-50 dark:bg-red-900/20 border-l-4 border-red-500 rounded-r-lg animate-slide-in">
              <div className="flex items-center gap-3">
                <span className="text-red-500 text-xl">⚠️</span>
                <p className="text-sm text-red-700 dark:text-red-300 font-medium">{error}</p>
              </div>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-6" autoComplete="off">
            <div className="space-y-2">
              <label htmlFor="email" className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 ml-1">
                Email Address
              </label>
              <div className="relative group">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-emerald-600 dark:group-focus-within:text-emerald-400 transition-colors">
                  📧
                </span>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="off"
                  className="w-full pl-12 pr-4 py-3.5 bg-white dark:bg-slate-800 text-slate-900 dark:text-white border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all placeholder-slate-400 dark:placeholder-slate-500 shadow-sm"
                  placeholder="breeder@example.com"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 ml-1">
                Password
              </label>
              <div className="relative group">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-emerald-600 dark:group-focus-within:text-emerald-400 transition-colors">
                  🔐
                </span>
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="off"
                  className="w-full pl-12 pr-12 py-3.5 bg-white dark:bg-slate-800 text-slate-900 dark:text-white border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all placeholder-slate-400 dark:placeholder-slate-500 shadow-sm"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors p-1"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-600 dark:hover:bg-emerald-500 text-white font-bold py-4 px-6 rounded-xl transition-all transform hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none shadow-lg shadow-emerald-600/20"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-3">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Signing in...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  Sign In
                  <ArrowRightIcon className="h-5 w-5" />
                </span>
              )}
            </button>
          </form>

          {/* Demo Credentials */}
          <div className="mt-8 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800/50 rounded-xl flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-3">
              <span className="text-xl">🔑</span>
              <div>
                <p className="text-xs font-bold text-amber-800 dark:text-amber-200 uppercase tracking-wide">Demo Mode</p>
                <p className="text-[10px] text-amber-600 dark:text-amber-400 mt-0.5">Test the platform instantly</p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => {
                setEmail('demo@bijmantra.org')
                setPassword('Demo123!')
              }}
              className="px-3 py-1.5 text-xs font-bold bg-amber-100 hover:bg-amber-200 dark:bg-amber-800/50 dark:hover:bg-amber-800 text-amber-900 dark:text-amber-100 rounded-lg transition-colors border border-amber-200 dark:border-amber-700"
            >
              Auto-Fill
            </button>
          </div>

          {/* Footer Features */}
          <div className="mt-10 pt-6 border-t border-slate-100 dark:border-slate-800/50">
             <div className="flex justify-center gap-6 text-slate-400 grayscale opacity-70 hover:grayscale-0 hover:opacity-100 transition-all duration-300">
                <div className="flex flex-col items-center gap-1 group">
                    <span className="text-lg bg-slate-100 dark:bg-slate-800 p-2 rounded-lg group-hover:text-emerald-500 group-hover:bg-emerald-50 dark:group-hover:bg-emerald-900/20 transition-colors">🔒</span>
                    <span className="text-[10px] uppercase font-bold tracking-wider">Secure</span>
                </div>
                <div className="flex flex-col items-center gap-1 group">
                    <span className="text-lg bg-slate-100 dark:bg-slate-800 p-2 rounded-lg group-hover:text-emerald-500 group-hover:bg-emerald-50 dark:group-hover:bg-emerald-900/20 transition-colors">📱</span>
                    <span className="text-[10px] uppercase font-bold tracking-wider">PWA</span>
                </div>
                <div className="flex flex-col items-center gap-1 group">
                    <span className="text-lg bg-slate-100 dark:bg-slate-800 p-2 rounded-lg group-hover:text-emerald-500 group-hover:bg-emerald-50 dark:group-hover:bg-emerald-900/20 transition-colors">🌐</span>
                    <span className="text-[10px] uppercase font-bold tracking-wider">BrAPI</span>
                </div>
             </div>
             <p className="text-center text-[10px] text-slate-400 dark:text-slate-600 mt-6">
               © 2025 Bijmantra • Open Source Agricultural Research Platform
             </p>
          </div>

        </div>
      </div>
    </div>
  )
}

function ArrowRightIcon(props: React.SVGProps<SVGSVGElement>) {
    return (
        <svg {...props} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
        </svg>
    )
}
