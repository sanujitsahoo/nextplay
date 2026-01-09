'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import PlayCard from './PlayCard'
import CardSkeleton from './CardSkeleton'
import type { Recommendation } from '@/types'

interface DailyRecommendationsProps {
  recommendations: Recommendation[]
  babyAgeMonths: number
  completedMilestoneIds: string[]
  onMilestoneComplete: (milestone: Recommendation) => void
  animatingMilestoneId?: string | null
  refillingSlots?: Set<string>
}

export default function DailyRecommendations({
  recommendations,
  babyAgeMonths,
  completedMilestoneIds,
  onMilestoneComplete,
  animatingMilestoneId,
  refillingSlots = new Set(),
}: DailyRecommendationsProps) {
  const [windowDimensions, setWindowDimensions] = useState({ width: 1920, height: 1080 })

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setWindowDimensions({ width: window.innerWidth, height: window.innerHeight })
      
      const handleResize = () => {
        setWindowDimensions({ width: window.innerWidth, height: window.innerHeight })
      }
      
      window.addEventListener('resize', handleResize)
      return () => window.removeEventListener('resize', handleResize)
    }
  }, [])

  if (recommendations.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">No recommendations available at this time.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-800 mb-2">Daily Recommendations</h2>
        <p className="text-gray-600">
          Personalized play activities for your {babyAgeMonths.toFixed(1)} month old
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-1">
        <AnimatePresence mode="popLayout">
          {/* Render existing recommendations */}
          {recommendations.map((rec) => (
            <motion.div
              key={rec.milestone_id}
              layout
              initial={{ opacity: 0, y: 50, scale: 0.9 }}
              animate={
                animatingMilestoneId === rec.milestone_id
                  ? {
                      opacity: 0,
                      scale: 0.8,
                      x: windowDimensions.width > 768 ? windowDimensions.width - 320 : windowDimensions.width - 80,
                      y: windowDimensions.height / 2,
                      transition: {
                        duration: 0.6,
                        ease: 'easeInOut',
                      },
                    }
                  : { opacity: 1, y: 0, scale: 1 }
              }
              exit={
                animatingMilestoneId === rec.milestone_id
                  ? {
                      opacity: 0,
                      scale: 0.8,
                      x: windowDimensions.width > 768 ? windowDimensions.width - 320 : windowDimensions.width - 80,
                      y: windowDimensions.height / 2,
                      transition: {
                        duration: 0.6,
                        ease: 'easeInOut',
                      },
                    }
                  : { opacity: 0, scale: 0.9, y: -20, transition: { duration: 0.3 } }
              }
              transition={{ duration: 0.4, ease: 'easeOut' }}
            >
              <PlayCard
                category={rec.category}
                title={rec.activity?.title || rec.milestone_name}
                milestoneName={rec.milestone_name}
                benefit={rec.activity?.benefit || ''}
                instructions={rec.activity?.instructions || []}
                materials={rec.activity?.materials || []}
                probability={rec.probability}
                foundationScore={rec.foundation_score}
                masteryAge={rec.mastery_age}
                milestoneId={rec.milestone_id}
                onComplete={() => onMilestoneComplete(rec)}
                isCompleted={completedMilestoneIds.includes(rec.milestone_id)}
              />
            </motion.div>
          ))}
          
          {/* Render skeleton cards for refilling slots (only while actively fetching) */}
          {Array.from(refillingSlots).map((slotId) => (
            <motion.div
              key={`skeleton-${slotId}`}
              initial={{ opacity: 0, y: 50, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9, y: -20 }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
            >
              <CardSkeleton />
            </motion.div>
          ))}
          
          {/* Only show placeholders for empty slots if we have fewer than 3 recommendations
              and we're not actively refilling. This prevents infinite skeleton loops. */}
          {refillingSlots.size === 0 && recommendations.length < 3 && (
            <>
              {Array.from({ length: 3 - recommendations.length }).map((_, index) => (
                <motion.div
                  key={`placeholder-${index}`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.9, y: -20 }}
                  transition={{ duration: 0.4, ease: 'easeOut' }}
                >
                  <CardSkeleton />
                </motion.div>
              ))}
            </>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

