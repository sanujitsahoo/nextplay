/**
 * Shared TypeScript type definitions for NextPlay frontend
 */

export interface Recommendation {
  milestone_id: string
  milestone_name: string
  probability: number
  discovery_score: number
  foundation_score: number  // Renamed from urgency_score
  category: 'foundational' | 'likely' | 'challenge'
  mastery_age: number | null
  activity: {
    title: string
    materials: string[]
    instructions: string[]
    benefit: string
  } | null
}

