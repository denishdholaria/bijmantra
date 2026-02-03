/**
 * Veena Welcome Component
 * Special welcome screen introducing Veena AI assistant
 * 
 * Celebrates the cultural significance of the name Veena:
 * - Sacred instrument of Goddess Saraswati
 * - Symbol of knowledge, music, and arts
 * - Harmony of knowledge and creativity
 * - Jnaana veena (veena of knowledge)
 */

import { useState } from 'react'
import { cn } from '@/lib/utils'

interface VeenaWelcomeProps {
  onClose: () => void
  onStartChat: () => void
}

export function VeenaWelcome({ onClose, onStartChat }: VeenaWelcomeProps) {
  const [currentSlide, setCurrentSlide] = useState(0)

  const slides = [
    {
      title: "Meet Veena",
      subtitle: "Your AI Breeding Assistant",
      content: "Named after the sacred instrument of Goddess Saraswati, Veena embodies the harmony of knowledge and creativity in plant breeding.",
      icon: "🪷",
      gradient: "from-amber-400 to-orange-500"
    },
    {
      title: "Jnaana Veena",
      subtitle: "The Veena of Knowledge",
      content: "Just as Saraswati's veena radiates knowledge in all directions, Veena AI brings wisdom to your breeding decisions with precision and insight.",
      icon: "🎵",
      gradient: "from-orange-400 to-red-500"
    },
    {
      title: "Harmony & Balance",
      subtitle: "Mind, Body, and Soul",
      content: "Veena represents the perfect balance of intellect and emotion, bringing peace, balance, and inner joy to your breeding journey.",
      icon: "⚖️",
      gradient: "from-red-400 to-pink-500"
    },
    {
      title: "Ready to Begin",
      subtitle: "Let's Create Together",
      content: "With Veena by your side, transform your breeding program with the melody of wisdom and the rhythm of innovation.",
      icon: "🌱",
      gradient: "from-pink-400 to-purple-500"
    }
  ]

  const currentSlideData = slides[currentSlide]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-md mx-4 bg-white dark:bg-gray-900 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className={cn(
          "px-6 py-8 text-white bg-gradient-to-br",
          currentSlideData.gradient
        )}>
          <div className="text-center">
            <div className="text-6xl mb-4">{currentSlideData.icon}</div>
            <h2 className="text-2xl font-bold mb-2">{currentSlideData.title}</h2>
            <p className="text-sm opacity-90">{currentSlideData.subtitle}</p>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          <p className="text-gray-700 dark:text-gray-300 leading-relaxed text-center mb-6">
            {currentSlideData.content}
          </p>

          {/* Progress Dots */}
          <div className="flex justify-center gap-2 mb-6">
            {slides.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentSlide(index)}
                className={cn(
                  "w-2 h-2 rounded-full transition-all",
                  index === currentSlide
                    ? "bg-amber-500 w-6"
                    : "bg-gray-300 dark:bg-gray-600 hover:bg-gray-400 dark:hover:bg-gray-500"
                )}
              />
            ))}
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            {currentSlide < slides.length - 1 ? (
              <>
                <button
                  onClick={onClose}
                  className="flex-1 px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
                >
                  Skip
                </button>
                <button
                  onClick={() => setCurrentSlide(currentSlide + 1)}
                  className="flex-1 px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors"
                >
                  Next
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={onClose}
                  className="flex-1 px-4 py-2 text-gray-600 dark:text-gray-400 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  Maybe Later
                </button>
                <button
                  onClick={onStartChat}
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-lg hover:from-amber-600 hover:to-orange-600 transition-all shadow-lg"
                >
                  Start with Veena 🪷
                </button>
              </>
            )}
          </div>
        </div>

        {/* Cultural Note */}
        <div className="px-6 pb-4">
          <div className="text-center text-xs text-gray-500 dark:text-gray-400 border-t border-gray-200 dark:border-gray-700 pt-4">
            <p className="italic">
              "The veena's music is believed to radiate knowledge in all directions,
              with Saraswati's full command over all branches of learning."
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ============================================
   VEENA INTRODUCTION HOOK
   ============================================ */
export function useVeenaIntroduction() {
  const [hasSeenIntro, setHasSeenIntro] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('veena-intro-seen') === 'true'
    }
    return false
  })

  const markIntroSeen = () => {
    setHasSeenIntro(true)
    if (typeof window !== 'undefined') {
      localStorage.setItem('veena-intro-seen', 'true')
    }
  }

  const resetIntro = () => {
    setHasSeenIntro(false)
    if (typeof window !== 'undefined') {
      localStorage.removeItem('veena-intro-seen')
    }
  }

  return {
    hasSeenIntro,
    markIntroSeen,
    resetIntro
  }
}
