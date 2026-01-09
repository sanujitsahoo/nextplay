'use client'

export default function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <div className="h-8 w-64 bg-gray-200 rounded-lg mx-auto mb-2 animate-pulse"></div>
        <div className="h-5 w-48 bg-gray-200 rounded-lg mx-auto animate-pulse"></div>
      </div>

      {/* Skeleton cards */}
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className="rounded-xl border-2 border-gray-200 bg-gray-50/50 p-6 shadow-md animate-pulse"
        >
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <div className="h-6 w-20 bg-gray-300 rounded-full"></div>
              </div>
              <div className="h-6 w-3/4 bg-gray-300 rounded mb-2"></div>
              <div className="h-4 w-1/2 bg-gray-200 rounded"></div>
            </div>
          </div>

          {/* Stats */}
          <div className="flex flex-wrap gap-3 mb-4">
            <div className="h-4 w-24 bg-gray-200 rounded"></div>
            <div className="h-4 w-24 bg-gray-200 rounded"></div>
          </div>

          {/* Benefit */}
          <div className="mb-4 p-3 bg-white/50 rounded-lg">
            <div className="h-4 w-full bg-gray-200 rounded mb-2"></div>
            <div className="h-4 w-5/6 bg-gray-200 rounded"></div>
          </div>

          {/* Button */}
          <div className="h-12 w-full bg-gray-300 rounded-lg"></div>
        </div>
      ))}
    </div>
  )
}

