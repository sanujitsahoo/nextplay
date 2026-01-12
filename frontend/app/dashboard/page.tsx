'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Header from '@/components/Header'
import DailyRecommendations from '@/components/DailyRecommendations'
import LoadingSkeleton from '@/components/LoadingSkeleton'
import JourneySidebar from '@/components/JourneySidebar'
import type { Recommendation } from '@/types'

export default function Dashboard() {
  const router = useRouter()
  const [completedMilestones, setCompletedMilestones] = useState<string[]>([])
  const [babyAge, setBabyAge] = useState<number>(3.0) // Default age
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [journeyMilestones, setJourneyMilestones] = useState<Recommendation[]>([])
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [animatingMilestone, setAnimatingMilestone] = useState<string | null>(null)
  const [refillingSlots, setRefillingSlots] = useState<Set<string>>(new Set())

  // Load data from localStorage on mount and check if we should redirect
  useEffect(() => {
    const savedAge = localStorage.getItem('babyAge')
    if (!savedAge) {
      router.push('/')
      return
    }
    
    const age = parseFloat(savedAge)
    if (isNaN(age) || age < 0 || age > 48) {
      router.push('/')
      return
    }
    
    setBabyAge(age)
    
    // Load completed milestones from localStorage
    const saved = localStorage.getItem('completedMilestones')
    if (saved) {
      try {
        setCompletedMilestones(JSON.parse(saved))
      } catch (e) {
        console.error('Error parsing completed milestones from localStorage:', e)
      }
    }
    
    // Load journey milestones from localStorage
    const savedJourney = localStorage.getItem('journeyMilestones')
    if (savedJourney) {
      try {
        setJourneyMilestones(JSON.parse(savedJourney))
      } catch (e) {
        console.error('Error parsing journey milestones from localStorage:', e)
      }
    }
  }, [router])

  // Fetch recommendations function
  const fetchRecommendations = useCallback(async (slotId?: string, overrideCompleted?: string[]) => {
    // If refilling a specific slot, don't set global loading
    if (!slotId) {
      setLoading(true)
    }
    setError(null)

    try {
      // Normalize API URL (remove trailing slash to prevent double slashes)
      const apiUrlBase = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/+$/, '')
      const apiUrl = `${apiUrlBase}/recommend`
      
      // Use overrideCompleted if provided (for refills), otherwise use current state
      const completedIds = overrideCompleted || completedMilestones
      
      console.log('Fetching recommendations:', { babyAge, completedIds, apiUrlBase, slotId })
      
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          baby_age_months: Number(babyAge), // Ensure it's a number, not a string
          completed_milestone_ids: completedIds,
        }),
      })

      console.log('Response status:', response.status, response.statusText)

      if (!response.ok) {
        const errorText = await response.text()
        console.error('API error response:', errorText)
        throw new Error(`API error: ${response.statusText} - ${errorText}`)
      }

      const data = await response.json()
      console.log('Received recommendations:', data)
      const newRecommendations = data.recommendations || []
      
      console.log('Processed recommendations:', newRecommendations.length)
      
      if (slotId) {
        // Refilling a specific slot - find a recommendation not already in the list
        setRecommendations(prev => {
          const existingIds = new Set(prev.map((r: Recommendation) => r.milestone_id))
          const availableRec = newRecommendations.find((r: Recommendation) => !existingIds.has(r.milestone_id))
          
          if (availableRec) {
            // Replace the slot with the new recommendation
            const filtered = prev.filter((r: Recommendation) => r.milestone_id !== slotId)
            return [...filtered, availableRec].slice(0, 3) // Ensure max 3 cards
          }
          
          // If no new recommendation found, just remove the slot
          // Don't show skeleton indefinitely - accept fewer cards
          console.warn(`No new recommendation found for slot ${slotId}, removing slot`)
          return prev.filter((r: Recommendation) => r.milestone_id !== slotId)
        })
        
        // Remove refilling state - always remove even if no recommendation found
        setRefillingSlots(prev => {
          const next = new Set(prev)
          next.delete(slotId)
          return next
        })
      } else {
        // Initial load or full refresh
        setRecommendations(newRecommendations)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch recommendations'
      setError(errorMessage)
      console.error('Error fetching recommendations:', err)
      if (!slotId) {
        setRecommendations([])
        setLoading(false)
      }
    } finally {
      if (!slotId) {
        setLoading(false)
      }
    }
  }, [babyAge, completedMilestones])

  // Fetch recommendations when baby age or completed milestones change
  useEffect(() => {
    if (babyAge > 0) {
      fetchRecommendations()
    }
  }, [fetchRecommendations, babyAge])

  const handleMilestoneComplete = async (milestone: Recommendation) => {
    const milestoneId = milestone.milestone_id
    
    // Set animating milestone for animation effect
    setAnimatingMilestone(milestoneId)
    
    // Mark this slot as refilling (shows skeleton loader)
    setRefillingSlots(prev => new Set(prev).add(milestoneId))
    
    // Remove from recommendations immediately (triggers exit animation)
    setRecommendations((prev) => prev.filter((rec) => rec.milestone_id !== milestoneId))
    
    // Update completed milestones state and localStorage
    const updatedCompleted = [...completedMilestones, milestoneId]
    setCompletedMilestones(updatedCompleted)
    localStorage.setItem('completedMilestones', JSON.stringify(updatedCompleted))
    
    // Add to journey milestones with animation (after a short delay for visual effect)
    setTimeout(() => {
      setJourneyMilestones((prev) => {
        const updated = [...prev, milestone]
        localStorage.setItem('journeyMilestones', JSON.stringify(updated))
        return updated
      })
    }, 100)
    
    // Wait for the exit animation to complete, then fetch new recommendation
    // Pass the updated completed list explicitly to avoid stale closure issues
    setTimeout(async () => {
      // Clear animating state
      setAnimatingMilestone(null)
      
      // Fetch new recommendation to fill the slot using the updated completed list
      await fetchRecommendations(milestoneId, updatedCompleted)
    }, 600) // Wait for exit animation (~600ms)
  }

  const handleAgeChange = (newAge: number) => {
    setBabyAge(newAge)
    localStorage.setItem('babyAge', newAge.toString())
  }

  return (
    <div className="min-h-screen relative">
      <Header 
        babyAge={babyAge} 
        onAgeChange={handleAgeChange}
        onClearAll={() => {
          // Clear state
          setCompletedMilestones([])
          setJourneyMilestones([])
          setRecommendations([])
          setBabyAge(3.0)
        }}
      />
      <main className={`container mx-auto px-4 py-6 pb-24 transition-all duration-300 ${sidebarOpen ? 'pr-4 md:pr-80' : ''} max-w-4xl`}>
        {loading ? (
          <LoadingSkeleton />
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <p className="text-red-700 font-medium mb-2">Unable to load recommendations</p>
            <p className="text-red-600 text-sm mb-4">{error}</p>
            <button
              onClick={() => fetchRecommendations()}
              className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
            >
              Try Again
            </button>
          </div>
        ) : (
          <DailyRecommendations
            recommendations={recommendations}
            babyAgeMonths={babyAge}
            completedMilestoneIds={completedMilestones}
            onMilestoneComplete={handleMilestoneComplete}
            animatingMilestoneId={animatingMilestone}
            refillingSlots={refillingSlots}
          />
        )}
      </main>
      
      {/* Journey Sidebar */}
      <JourneySidebar
        journeyMilestones={journeyMilestones}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />
      
      {/* Footer with feedback link */}
      <footer className="w-full py-4 px-4 text-center border-t border-gray-200 bg-white/50 backdrop-blur-sm">
        <a
          href="https://forms.gle/ePxZfCME9Ng1eYyQ9"
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-teal-600 hover:text-teal-700 underline transition-colors"
        >
          Provide Feedback
        </a>
      </footer>
    </div>
  )
}

