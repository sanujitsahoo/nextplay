'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'

interface HeaderProps {
  babyAge: number
  onAgeChange: (age: number) => void
  onClearAll?: () => void
}

export default function Header({ babyAge, onAgeChange, onClearAll }: HeaderProps) {
  const [showProfile, setShowProfile] = useState(false)
  const [showClearConfirm, setShowClearConfirm] = useState(false)
  const router = useRouter()
  const profileRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(event.target as Node)) {
        setShowProfile(false)
        setShowClearConfirm(false)
      }
    }

    if (showProfile) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showProfile])

  const handleClearAll = () => {
    // Clear all localStorage data
    localStorage.removeItem('babyAge')
    localStorage.removeItem('completedMilestones')
    localStorage.removeItem('journeyMilestones')
    localStorage.removeItem('childName')
    
    // Call optional callback
    if (onClearAll) {
      onClearAll()
    }
    
    // Redirect to landing page
    router.push('/')
  }

  return (
    <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-pastel-purple/20 shadow-sm">
      <div className="container mx-auto px-4 py-4 max-w-6xl">
        <div className="flex items-center justify-between">
          {/* App Name */}
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
              NextPlay
            </h1>
            <span className="text-sm text-gray-500 font-normal">Baby Development</span>
          </div>

          {/* Baby Profile Icon */}
          <div className="relative" ref={profileRef}>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation()
                setShowProfile(!showProfile)
              }}
              className="flex items-center gap-2 px-4 py-2 rounded-full bg-pastel-blue/30 hover:bg-pastel-blue/50 transition-colors cursor-pointer"
              aria-label="Baby Profile"
              aria-expanded={showProfile}
            >
              <svg
                className="w-6 h-6 text-purple-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                />
              </svg>
              <span className="text-sm font-medium text-gray-700 hidden sm:inline">
                Profile
              </span>
            </button>

            {/* Profile Dropdown */}
            {showProfile && (
              <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-pastel-purple/20 p-4 z-50">
                <h3 className="font-semibold text-gray-800 mb-3">Baby Profile</h3>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Age (months)
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="36"
                      step="0.1"
                      value={babyAge}
                      onChange={(e) => {
                        const inputValue = e.target.value
                        // Handle empty input
                        if (inputValue === '' || inputValue === '.') {
                          return
                        }
                        const age = parseFloat(inputValue)
                        if (!isNaN(age) && age >= 0 && age <= 48) {
                          onAgeChange(age)
                        }
                        // localStorage is handled in page.tsx
                      }}
                      className="w-full px-3 py-2 border border-pastel-purple/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-pastel-purple/50"
                    />
                  </div>
                  <div className="pt-2 border-t border-pastel-purple/20 space-y-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        localStorage.removeItem('completedMilestones')
                        localStorage.removeItem('babyAge')
                        localStorage.removeItem('journeyMilestones')
                        window.location.reload()
                      }}
                      className="text-sm text-orange-600 hover:text-orange-700 w-full text-left py-2 px-3 rounded hover:bg-orange-50 transition-colors cursor-pointer"
                      style={{ visibility: 'visible', display: 'block' }}
                    >
                      Reset Progress
                    </button>
                    
                    <div className="relative">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setShowClearConfirm(true)
                        }}
                        className="text-sm text-red-600 hover:text-red-700 w-full text-left py-2 px-3 rounded hover:bg-red-50 transition-colors font-medium flex items-center gap-2 cursor-pointer"
                        style={{ visibility: 'visible', display: 'flex' }}
                      >
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                          />
                        </svg>
                        Clear All & Start Fresh
                      </button>
                      
                      {showClearConfirm && (
                        <>
                          {/* Backdrop */}
                          <div
                            className="fixed inset-0 bg-black/20 z-40"
                            onClick={() => setShowClearConfirm(false)}
                          />
                          
                          {/* Confirmation Dialog */}
                          <div className="absolute right-0 mt-2 w-72 bg-white rounded-lg shadow-xl border border-red-200 p-4 z-50">
                            <div className="flex items-start gap-3 mb-3">
                              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                                <svg
                                  className="w-5 h-5 text-red-600"
                                  fill="none"
                                  stroke="currentColor"
                                  viewBox="0 0 24 24"
                                >
                                  <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                                  />
                                </svg>
                              </div>
                              <div className="flex-1">
                                <h4 className="font-semibold text-gray-800 mb-1">Clear All Data?</h4>
                                <p className="text-sm text-gray-600">
                                  This will delete all your progress, completed milestones, and journey history. This action cannot be undone.
                                </p>
                              </div>
                            </div>
                            <div className="flex gap-2">
                              <button
                                onClick={() => setShowClearConfirm(false)}
                                className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
                              >
                                Cancel
                              </button>
                              <button
                                onClick={() => {
                                  handleClearAll()
                                  setShowClearConfirm(false)
                                }}
                                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
                              >
                                Clear All
                              </button>
                            </div>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}

