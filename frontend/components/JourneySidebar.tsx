'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { Recommendation } from '@/types'

interface JourneySidebarProps {
  journeyMilestones: Recommendation[]
  isOpen: boolean
  onToggle: () => void
}

export default function JourneySidebar({ journeyMilestones, isOpen, onToggle }: JourneySidebarProps) {
  return (
    <>
      {/* Collapsible Tab Button */}
      <button
        onClick={onToggle}
        className="fixed right-0 top-1/2 -translate-y-1/2 z-40 bg-gradient-to-l from-teal-600 to-teal-700 text-white px-4 py-8 rounded-l-lg shadow-lg hover:shadow-xl transition-all duration-300 hover:from-teal-700 hover:to-teal-800"
        style={{ right: 0 }}
        aria-label={isOpen ? 'Collapse Journey' : 'Expand Journey'}
      >
        <div className="flex flex-col items-center gap-2 relative">
          {/* Milestone Count Badge */}
          <div className="absolute -top-2 -left-2 bg-yellow-400 text-teal-900 rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold shadow-md z-50">
            {journeyMilestones.length}
          </div>
          
          <svg
            className={`w-5 h-5 transform transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5l7 7-7 7"
            />
          </svg>
          <span className="text-xs font-semibold writing-vertical-rl text-center">
            Our Journey
          </span>
          {/* Milestone count text below */}
          <span className="text-[10px] text-teal-100 writing-vertical-rl text-center mt-1">
            {journeyMilestones.length} {journeyMilestones.length === 1 ? 'milestone' : 'milestones'}
          </span>
        </div>
      </button>

      {/* Sidebar Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 h-full w-80 bg-white shadow-2xl z-30 overflow-hidden flex flex-col max-w-[90vw]"
            style={{ right: 0 }}
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-teal-600 to-teal-700 text-white p-6 shadow-md flex-shrink-0">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-2xl font-bold">Our Journey</h2>
                <button
                  onClick={onToggle}
                  className="text-white/80 hover:text-white transition-colors flex-shrink-0 ml-2"
                  aria-label="Close sidebar"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
              <div className="flex items-center gap-2">
                <div className="bg-white/20 rounded-full px-3 py-1.5">
                  <p className="text-base font-semibold text-white">
                    {journeyMilestones.length} milestone{journeyMilestones.length !== 1 ? 's' : ''} completed
                  </p>
                </div>
              </div>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
              {journeyMilestones.length === 0 ? (
                <div className="text-center py-12 text-gray-400">
                  <svg
                    className="w-16 h-16 mx-auto mb-4 opacity-50"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"
                    />
                  </svg>
                  <p className="text-sm">No milestones completed yet</p>
                  <p className="text-xs mt-1">Complete activities to see them here!</p>
                </div>
              ) : (
                journeyMilestones.map((milestone, index) => (
                  <motion.div
                    key={milestone.milestone_id}
                    initial={{ opacity: 0, scale: 0.8, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="bg-gradient-to-br from-pastel-green/30 to-pastel-blue/30 rounded-lg p-4 border border-green-200 shadow-sm"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-800 text-sm mb-1 line-clamp-2">
                          {milestone.activity?.title || milestone.milestone_name}
                        </h3>
                        <p className="text-xs text-gray-600 line-clamp-1">
                          {milestone.milestone_name}
                        </p>
                      </div>
                      <div className="flex-shrink-0 ml-2">
                        <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                          <svg
                            className="w-5 h-5 text-green-600"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M5 13l4 4L19 7"
                            />
                          </svg>
                        </div>
                      </div>
                    </div>
                    {milestone.activity?.benefit && (
                      <p className="text-xs text-gray-600 italic mt-2 line-clamp-2">
                        {milestone.activity.benefit}
                      </p>
                    )}
                  </motion.div>
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}

