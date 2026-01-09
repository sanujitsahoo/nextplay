'use client'

import { useState, useRef } from 'react'
import ConfettiBurst from './ConfettiBurst'

interface PlayCardProps {
  category: 'foundational' | 'likely' | 'challenge'
  title: string
  milestoneName: string
  benefit: string
  instructions: string[]
  materials: string[]
  probability: number
  foundationScore: number
  masteryAge: number | null
  milestoneId: string
  onComplete: () => void
  isCompleted: boolean
}

export default function PlayCard({
  category,
  title,
  milestoneName,
  benefit,
  instructions,
  materials,
  probability,
  foundationScore,
  masteryAge,
  milestoneId,
  onComplete,
  isCompleted,
}: PlayCardProps) {
  const [showDetails, setShowDetails] = useState(false)
  const [isCompleting, setIsCompleting] = useState(false)
  const [showConfetti, setShowConfetti] = useState(false)
  const [buttonText, setButtonText] = useState<'I did this!' | 'Awesome! ✨'>('I did this!')
  const cardRef = useRef<HTMLDivElement>(null)

  const categoryColors = {
    foundational: {
      border: 'border-amber-400',
      bg: 'bg-[#FFFBEB]',  // Soft amber background
      badge: 'bg-amber-400 text-amber-900',
      badgeText: 'Foundational Skill',
    },
    likely: {
      border: 'border-category-likely',
      bg: 'bg-category-likely/10',
      badge: 'bg-category-likely text-blue-800',
      badgeText: 'Likely',
    },
    challenge: {
      border: 'border-category-challenge',
      bg: 'bg-category-challenge/10',
      badge: 'bg-category-challenge text-purple-800',
      badgeText: 'Challenge',
    },
  }

  const colors = categoryColors[category]

  const handleComplete = async () => {
    // Immediately disable button and change text to success state
    setIsCompleting(true)
    setButtonText('Awesome! ✨')
    
    // Trigger confetti burst
    setShowConfetti(true)
    
    // Wait 200ms for success state to sink in, then trigger flight animation
    setTimeout(() => {
      onComplete()
      // Reset states after animation
      setTimeout(() => {
        setIsCompleting(false)
        setButtonText('I did this!')
        setShowConfetti(false)
      }, 100)
    }, 200) // Brief delay to let success state sink in
  }

  return (
    <>
      {/* Confetti Burst - positioned relative to card */}
      {showConfetti && (
        <ConfettiBurst 
          trigger={showConfetti}
          onComplete={() => setShowConfetti(false)}
          cardRef={cardRef}
        />
      )}
      <div
        ref={cardRef}
        className={`rounded-xl border-2 ${colors.border} ${colors.bg} p-6 shadow-md hover:shadow-lg transition-all duration-300 relative ${
          isCompleted ? 'opacity-60' : ''
        }`}
      >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span
              className={`px-3 py-1 rounded-full text-xs font-semibold ${colors.badge}`}
            >
              {colors.badgeText}
            </span>
            {isCompleted && (
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800">
                Completed
              </span>
            )}
          </div>
          <h3 className="text-xl font-bold text-gray-800 mb-1">{title}</h3>
          <p className={`text-sm ${category === 'foundational' ? 'text-[#D97706]' : 'text-gray-600'}`}>{milestoneName}</p>
        </div>
      </div>

      {/* Stats */}
      <div className="flex flex-wrap gap-3 mb-4 text-xs text-gray-600">
        {masteryAge && (
          <span className="flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {masteryAge.toFixed(1)} months
          </span>
        )}
        <span className="flex items-center gap-1">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          {(probability * 100).toFixed(0)}% match
        </span>
      </div>

      {/* Benefit */}
      {benefit && (
        <div className="mb-4 p-3 bg-white/50 rounded-lg">
          <p className="text-sm text-gray-700 italic">{benefit}</p>
        </div>
      )}

      {/* Expandable Details */}
      <button
        onClick={() => setShowDetails(!showDetails)}
        className="w-full text-left text-sm font-medium text-gray-700 hover:text-gray-900 mb-4 flex items-center justify-between"
      >
        <span>{showDetails ? 'Hide' : 'Show'} Activity Details</span>
        <svg
          className={`w-5 h-5 transform transition-transform ${showDetails ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {showDetails && (
        <div className="space-y-4 mb-4">
          {/* Materials */}
          {materials.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Materials Needed:</h4>
              <div className="flex flex-wrap gap-2">
                {materials.map((material, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-white/70 rounded-full text-sm text-gray-700"
                  >
                    {material}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Instructions */}
          {instructions.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-2">How to Play:</h4>
              <ol className="list-decimal list-inside space-y-2">
                {instructions.map((instruction, index) => (
                  <li key={index} className="text-sm text-gray-700 pl-2">
                    {instruction}
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
      )}

      {/* Complete Button */}
      {!isCompleted && (
        <button
          onClick={handleComplete}
          disabled={isCompleting}
          className={`w-full py-3 px-4 rounded-lg font-semibold text-white transition-all duration-200 ${
            isCompleting
              ? `bg-gradient-to-r ${
                  category === 'foundational'
                    ? 'from-amber-400 to-amber-500'
                    : category === 'likely'
                    ? 'from-blue-400 to-cyan-400'
                    : 'from-purple-400 to-indigo-400'
                } cursor-not-allowed opacity-90`
              : `bg-gradient-to-r ${
                  category === 'foundational'
                    ? 'from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700'
                    : category === 'likely'
                    ? 'from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600'
                    : 'from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600'
                } hover:shadow-lg transform hover:scale-[1.02] active:scale-[0.98]`
          }`}
        >
          <span className="flex items-center justify-center gap-2">
            {buttonText === 'Awesome! ✨' ? (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Awesome! ✨
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                I did this!
              </>
            )}
          </span>
        </button>
      )}

      {isCompleted && (
        <div className="w-full py-3 px-4 rounded-lg font-semibold text-center bg-green-100 text-green-800">
          ✓ Activity Completed
        </div>
      )}
      </div>
    </>
  )
}

