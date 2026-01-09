'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Toast from '@/components/Toast'

interface IntakeResponse {
  child_name: string | null
  age_months: number | null
  completed_milestone_ids: string[]
  needs_clarification: boolean
  follow_up_question: string | null
}

export default function LandingPage() {
  const [ageMonths, setAgeMonths] = useState<string>('')
  const [story, setStory] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [followUpQuestion, setFollowUpQuestion] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validate numeric age input
    const age = parseFloat(ageMonths)
    if (!ageMonths.trim() || isNaN(age) || age < 0 || age > 48) {
      setFollowUpQuestion('Please enter a valid age between 0 and 48 months.')
      return
    }

    if (!story.trim()) {
      setFollowUpQuestion('Please tell us about your baby\'s recent win or what they\'re starting to do.')
      return
    }

    setIsProcessing(true)
    setError(null)
    setFollowUpQuestion(null)

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      
      // POST only the story text to /intake endpoint to extract milestones
      let data: IntakeResponse
      
      try {
        console.log('Calling API:', `${apiUrl}/intake`)
        const response = await fetch(`${apiUrl}/intake`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            description: story.trim(),
          }),
        })

        console.log('API Response status:', response.status, response.statusText)

        if (!response.ok) {
          // Get error details from response
          let errorMessage = 'Failed to process intake'
          try {
            const errorData = await response.json()
            errorMessage = errorData.detail || errorMessage
            console.error('API Error Response:', errorData)
          } catch {
            // If response isn't JSON, try to get text
            try {
              const errorText = await response.text()
              errorMessage = errorText || errorMessage
              console.error('API Error Text:', errorText)
            } catch {
              errorMessage = `Server error (${response.status})`
              console.error('API Error - Could not parse response')
            }
          }
          
          // If Intake Specialist is unavailable, proceed with manual age only
          if (response.status === 503 || errorMessage.includes('Intake Specialist is not available')) {
            console.warn('Intake Specialist unavailable, proceeding with manual age only')
            data = {
              child_name: null,
              age_months: null,
              completed_milestone_ids: [],
              needs_clarification: false,
              follow_up_question: null
            }
          } else {
            throw new Error(errorMessage)
          }
        } else {
          data = await response.json()
          console.log('API Success:', data)
        }
      } catch (fetchError) {
        // Network errors - log and rethrow
        console.error('Fetch Error:', fetchError)
        if (fetchError instanceof TypeError && fetchError.message.includes('Failed to fetch')) {
          // CORS or network error
          console.error('This is likely a CORS or network connectivity issue')
        }
        throw fetchError
      }

      // Use manual ageMonths directly, combine with LLM-extracted milestones
      const babyAge = age // Use the numeric input directly
      
      // Store child name if extracted
      if (data.child_name) {
        localStorage.setItem('childName', data.child_name)
      }
      
      // Store manual age and LLM-extracted milestones (empty if intake failed)
      localStorage.setItem('babyAge', babyAge.toString())
      localStorage.setItem('completedMilestones', JSON.stringify(data.completed_milestone_ids || []))

      // Redirect to dashboard immediately
      router.push('/dashboard')
    } catch (err) {
      console.error('Error processing intake:', err)
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      
      // Show more specific error messages for common issues
      let userFriendlyMessage = 'Our specialist is taking a quick nap. Please try again in a moment.'
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      
      if (errorMessage.includes('503') || errorMessage.includes('Intake Specialist is not available')) {
        userFriendlyMessage = 'The intake specialist is currently unavailable. Please ensure the backend is properly configured with OPENAI_API_KEY.'
      } else if (errorMessage.includes('500') || errorMessage.includes('Error processing intake')) {
        userFriendlyMessage = 'There was an issue processing your description. Please try again or check your connection.'
      } else if (errorMessage.includes('Failed to fetch') || errorMessage.includes('NetworkError') || errorMessage.includes('CORS')) {
        // More helpful message for network/CORS issues
        if (apiUrl.includes('localhost')) {
          userFriendlyMessage = 'Unable to connect to the backend. If you\'re on the deployed site, please ensure NEXT_PUBLIC_API_URL is configured in Vercel.'
        } else {
          userFriendlyMessage = `Unable to connect to the backend at ${apiUrl}. Please check the connection or try again later.`
        }
      }
      
      setError(userFriendlyMessage)
      setIsProcessing(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 via-amber-50/80 to-orange-50 flex items-center justify-center px-4 py-12">
      {/* Toast for errors */}
      {error && (
        <Toast
          message={error}
          onClose={() => setError(null)}
        />
      )}

      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-800 mb-3">
            NextPlay
          </h1>
          <p className="text-lg text-gray-600">
            Personalized play activities for your baby's development
          </p>
        </div>

        {/* Main form card */}
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl p-6 md:p-8 border border-amber-100">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Follow-up question message */}
            {followUpQuestion && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 animate-in">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0">
                    <svg
                      className="w-5 h-5 text-amber-600 mt-0.5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  </div>
                  <p className="text-sm text-amber-800 flex-1">{followUpQuestion}</p>
                </div>
              </div>
            )}

            {/* Age input */}
            <div>
              <label htmlFor="ageMonths" className="block text-sm font-medium text-gray-700 mb-2">
                How many months old is your baby? <span className="text-red-500">*</span>
              </label>
              <input
                id="ageMonths"
                type="number"
                min="0"
                max="48"
                step="0.5"
                value={ageMonths}
                onChange={(e) => setAgeMonths(e.target.value)}
                placeholder="e.g., 6 or 6.5"
                className="w-full px-4 py-3 border-2 border-amber-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent text-gray-800 placeholder-gray-400 bg-white transition-all duration-200"
                disabled={isProcessing}
                required
              />
            </div>

            {/* Story input */}
            <div>
              <label htmlFor="story" className="block text-sm font-medium text-gray-700 mb-2">
                Tell us a recent win or what they are starting to do
              </label>
              <textarea
                id="story"
                value={story}
                onChange={(e) => setStory(e.target.value)}
                placeholder="Tell us a recent win or what they are starting to do..."
                className="w-full h-48 px-4 py-3 border-2 border-amber-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent resize-none text-gray-800 placeholder-gray-400 bg-white transition-all duration-200"
                disabled={isProcessing}
              />
              <p className="mt-2 text-xs text-gray-500">
                Example: "She can sit without support and she's starting to crawl."
              </p>
            </div>

            {/* Submit button */}
            <button
              type="submit"
              disabled={isProcessing || !ageMonths.trim() || !story.trim()}
              className="w-full bg-gradient-to-r from-teal-600 to-teal-700 hover:from-teal-700 hover:to-teal-800 text-white font-semibold py-4 px-6 rounded-lg shadow-lg text-base transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed enabled:hover:shadow-xl enabled:hover:scale-[1.02] enabled:active:scale-[0.98]"
              style={{ 
                minHeight: '48px'
              }}
            >
              {isProcessing ? (
                <>
                  <svg
                    className="animate-spin h-5 w-5"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  <span>Matching milestones...</span>
                </>
              ) : (
                <span>Let&apos;s Play</span>
              )}
            </button>
          </form>
        </div>

        {/* Footer note */}
        <p className="text-center text-sm text-gray-500 mt-6">
          Your information is processed securely and used only to provide personalized recommendations.
        </p>
      </div>
    </div>
  )
}
