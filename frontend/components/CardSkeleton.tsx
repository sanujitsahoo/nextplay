'use client'

export default function CardSkeleton() {
  return (
    <div className="rounded-xl border-2 border-gray-200 bg-gradient-to-br from-gray-50 to-gray-100/50 p-6 shadow-md relative overflow-hidden">
      {/* Shimmer effect */}
      <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-white/60 to-transparent"></div>
      
      {/* Header */}
      <div className="flex items-start justify-between mb-4 relative z-10">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <div className="h-6 w-24 bg-gray-300 rounded-full animate-pulse"></div>
          </div>
          <div className="h-6 w-3/4 bg-gray-300 rounded mb-2 animate-pulse"></div>
          <div className="h-4 w-1/2 bg-gray-200 rounded animate-pulse"></div>
        </div>
      </div>

      {/* Stats */}
      <div className="flex flex-wrap gap-3 mb-4 relative z-10">
        <div className="h-4 w-24 bg-gray-200 rounded animate-pulse"></div>
        <div className="h-4 w-24 bg-gray-200 rounded animate-pulse"></div>
      </div>

      {/* Benefit */}
      <div className="mb-4 p-3 bg-white/50 rounded-lg relative z-10">
        <div className="h-4 w-full bg-gray-200 rounded mb-2 animate-pulse"></div>
        <div className="h-4 w-5/6 bg-gray-200 rounded animate-pulse"></div>
      </div>

      {/* Button */}
      <div className="h-12 w-full bg-gray-300 rounded-lg animate-pulse relative z-10"></div>
    </div>
  )
}

