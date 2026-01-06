/**
 * Login Page - Inspirational Multilingual Design
 * "One Seed. Infinite Worlds."
 * 
 * Featuring wisdom from agricultural cultures worldwide,
 * displayed in their original languages with English translations.
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/auth'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { getWorkspace } from '@/framework/registry/workspaces'

// Multilingual quotes from agricultural cultures worldwide
// Each quote shown in original language + English translation
const quotes = [
  // Sanskrit / India - The philosophical foundation
  {
    original: "योगः कर्मसु कौशलम्",
    translation: "Excellence in action is yoga.",
    source: "Bhagavad Gita 2.50",
    culture: "Sanskrit • India",
    icon: "🙏",
    region: "south-asia"
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

// Statistics - honest about current state, aspirational about vision
const stats = [
  { value: "201", label: "BrAPI Endpoints", sublabel: "100% compliant" },
  { value: "302", label: "Features", sublabel: "built & ready" },
  { value: "24", label: "Cultures", sublabel: "wisdom shared" },
  { value: "Open", label: "Source", sublabel: "transparent code" },
]

// Region colors for visual variety - Prakruti Design System
const regionColors: Record<string, string> = {
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
    <div className="min-h-screen flex">
      {/* Left Panel - Multilingual Inspirational Content */}
      <div className="hidden lg:flex lg:w-1/2 xl:w-3/5 relative overflow-hidden">
        {/* Animated Background Gradient - Prakruti Earth & Leaf */}
        <div className="absolute inset-0 bg-gradient-to-br from-prakruti-patta via-prakruti-patta-dark to-prakruti-mitti-dark">
          {/* Animated circles with region-based colors */}
          <div className={`absolute top-20 left-20 w-72 h-72 bg-gradient-to-br ${regionColor} rounded-full blur-3xl animate-pulse transition-colors duration-1000`} />
          <div className="absolute bottom-20 right-20 w-96 h-96 bg-prakruti-patta-light/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
          <div className="absolute top-1/2 left-1/3 w-64 h-64 bg-prakruti-sona/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }} />
        </div>

        {/* World map pattern overlay (subtle) */}
        <div className="absolute inset-0 opacity-[0.03]">
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
              <div className="w-16 h-16 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center shadow-2xl">
                <span className="text-4xl">🌱</span>
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white">Bijmantra</h1>
                <p className="text-prakruti-patta-pale text-sm">One Seed. Infinite Worlds.</p>
              </div>
            </div>
          </div>

          {/* Middle - Rotating Multilingual Quote */}
          <div className="flex-1 flex items-center justify-center">
            <div 
              className={`max-w-2xl text-center transition-all duration-500 ${
                isQuoteFading ? 'opacity-0 transform translate-y-4' : 'opacity-100 transform translate-y-0'
              }`}
            >
              {/* Icon */}
              <span className="text-6xl mb-6 block drop-shadow-lg">{quote.icon}</span>
              
              {/* Original Language Quote */}
              <blockquote className="text-3xl xl:text-4xl font-medium text-white leading-relaxed mb-4 tracking-wide">
                "{quote.original}"
              </blockquote>
              
              {/* English Translation */}
              <p className="text-xl text-prakruti-patta-pale/90 italic mb-6">
                {quote.translation}
              </p>
              
              {/* Attribution */}
              <div className="flex items-center justify-center gap-3">
                <span className="px-3 py-1 bg-white/10 backdrop-blur-sm rounded-full text-sm text-prakruti-patta-pale border border-white/20">
                  {quote.culture}
                </span>
                <span className="text-prakruti-patta-100/80 text-sm">
                  — {quote.source}
                </span>
              </div>
            </div>
          </div>

          {/* Bottom - Stats and Navigation */}
          <div>
            {/* Stats Grid */}
            <div className="grid grid-cols-4 gap-4 mb-6">
              {stats.map((stat, i) => (
                <div 
                  key={i} 
                  className="text-center p-4 bg-white/10 backdrop-blur-sm rounded-xl border border-white/20 hover:bg-white/15 transition-colors"
                >
                  <div className="text-2xl xl:text-3xl font-bold text-white">{stat.value}</div>
                  <div className="text-xs text-prakruti-patta-pale font-medium mt-1">{stat.label}</div>
                  <div className="text-xs text-prakruti-patta-100/70">{stat.sublabel}</div>
                </div>
              ))}
            </div>
            
            {/* Quote Navigation */}
            <div className="flex items-center justify-center gap-2">
              <button
                onClick={() => {
                  setIsQuoteFading(true)
                  setTimeout(() => {
                    setCurrentQuote((prev) => (prev - 1 + quotes.length) % quotes.length)
                    setIsQuoteFading(false)
                  }, 300)
                }}
                className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors text-white"
                aria-label="Previous quote"
              >
                ←
              </button>
              
              <div className="flex gap-1.5 mx-4">
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
                    className={`h-1.5 rounded-full transition-all duration-300 ${
                      i === currentQuote 
                        ? 'bg-white w-6' 
                        : 'bg-white/30 w-1.5 hover:bg-white/50'
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
                className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors text-white"
                aria-label="Next quote"
              >
                →
              </button>
            </div>
            
            {/* Quote counter */}
            <p className="text-center text-prakruti-patta-100/60 text-xs mt-4">
              {currentQuote + 1} of {quotes.length} • Wisdom from around the world
            </p>
          </div>
        </div>
      </div>

      {/* Right Panel - Login Form */}
      <div className="w-full lg:w-1/2 xl:w-2/5 flex items-center justify-center p-6 sm:p-12 bg-gradient-to-br from-prakruti-dhool-50 via-white to-prakruti-patta-pale/30 dark:from-prakruti-dhool-900 dark:via-prakruti-dhool-900 dark:to-prakruti-patta/10 font-sans">
        <div className="w-full max-w-md animate-fade-in">
          {/* Mobile Logo (hidden on desktop) */}
          <div className="lg:hidden text-center mb-8">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-prakruti-patta to-prakruti-patta-dark rounded-2xl shadow-lg mb-4">
              <span className="text-4xl">🌱</span>
            </div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-prakruti-patta to-prakruti-patta-dark dark:from-prakruti-patta-light dark:to-prakruti-patta bg-clip-text text-transparent">
              Bijmantra
            </h1>
            <p className="text-prakruti-dhool-500 dark:text-prakruti-dhool-400 text-sm mt-1">One Seed. Infinite Worlds.</p>
          </div>

          {/* Welcome Message */}
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-prakruti-dhool-800 dark:text-white">Welcome Back</h2>
            <p className="text-prakruti-dhool-500 dark:text-prakruti-dhool-400 mt-2">
              Continue your journey in plant breeding excellence
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/30 border-l-4 border-red-500 rounded-r-xl animate-slide-in">
              <div className="flex items-center gap-3">
                <span className="text-red-500 text-xl">⚠️</span>
                <p className="text-sm text-red-800 dark:text-red-200 font-medium">{error}</p>
              </div>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-6" autoComplete="off">
            <div>
              <label htmlFor="email" className="block text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2">
                Email Address
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
                  📧
                </span>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="off"
                  className="w-full pl-12 pr-4 py-3.5 bg-white dark:bg-slate-800 text-gray-900 dark:text-white border-2 border-gray-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500/20 focus:border-green-500 transition-all placeholder-gray-400 dark:placeholder-gray-500"
                  placeholder="breeder@example.com"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2">
                Password
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
                  🔐
                </span>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="off"
                  className="w-full pl-12 pr-4 py-3.5 bg-white dark:bg-slate-800 text-gray-900 dark:text-white border-2 border-gray-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500/20 focus:border-green-500 transition-all placeholder-gray-400 dark:placeholder-gray-500"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-prakruti-patta to-prakruti-patta-dark hover:from-prakruti-patta-dark hover:to-prakruti-patta text-white font-semibold py-4 px-6 rounded-xl transition-all transform hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none shadow-xl shadow-prakruti-patta/25 hover:shadow-prakruti-patta/40"
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
                  <span className="text-lg">→</span>
                </span>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="relative my-8">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-prakruti-dhool-200 dark:border-prakruti-dhool-700"></div>
            </div>
            <div className="relative flex justify-center">
              <div className="px-4 bg-gradient-to-r from-prakruti-dhool-50 via-white to-prakruti-patta-pale/30 dark:from-prakruti-dhool-900 dark:via-prakruti-dhool-900 dark:to-prakruti-patta/10 text-center">
                <span className="text-sm text-prakruti-dhool-500 dark:text-prakruti-dhool-300 font-medium">R.E.E.V.A.i</span>
                <p className="text-[10px] text-prakruti-dhool-400 dark:text-prakruti-dhool-500 leading-tight">Rural Empowerment through Emerging<br/>Value-driven Agro-Intelligence</p>
              </div>
            </div>
          </div>

          {/* Features */}
          <div className="grid grid-cols-3 gap-3 mb-8">
            <div className="text-center p-3 bg-prakruti-patta-pale dark:bg-prakruti-patta/20 rounded-xl">
              <span className="text-xl">🔒</span>
              <p className="text-xs text-prakruti-dhool-600 dark:text-prakruti-dhool-300 mt-1 font-medium">Secure</p>
            </div>
            <div className="text-center p-3 bg-prakruti-neela-pale dark:bg-prakruti-neela/20 rounded-xl">
              <span className="text-xl">📱</span>
              <p className="text-xs text-prakruti-dhool-600 dark:text-prakruti-dhool-300 mt-1 font-medium">PWA Ready</p>
            </div>
            <div className="text-center p-3 bg-purple-50 dark:bg-purple-900/30 rounded-xl">
              <span className="text-xl">🌐</span>
              <p className="text-xs text-prakruti-dhool-600 dark:text-prakruti-dhool-300 mt-1 font-medium">BrAPI v2.1</p>
            </div>
          </div>

          {/* Mobile Quote (shown only on mobile) */}
          <div className="lg:hidden bg-gradient-to-r from-prakruti-patta-pale to-prakruti-patta-50 dark:from-prakruti-patta/20 dark:to-prakruti-patta/10 rounded-xl p-4 mb-6 border border-prakruti-patta-100 dark:border-prakruti-patta/30">
            <p className="text-base text-prakruti-patta-dark dark:text-prakruti-patta-pale font-medium text-center mb-1">
              "{quote.original}"
            </p>
            <p className="text-sm text-prakruti-patta dark:text-prakruti-patta-light italic text-center">
              {quote.translation}
            </p>
            <p className="text-xs text-prakruti-patta-light dark:text-prakruti-patta-100 text-center mt-2">
              {quote.culture} • {quote.source}
            </p>
          </div>

          {/* Footer */}
          <div className="text-center space-y-2">
            <p className="text-xs text-prakruti-dhool-400 dark:text-prakruti-dhool-500">
              🌾 Thank you to all those who work in acres, not in hours.
            </p>
            <p className="text-[10px] text-prakruti-dhool-400 dark:text-prakruti-dhool-500">
              © 2025 Bijmantra • Open Source Agricultural Research Platform
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
