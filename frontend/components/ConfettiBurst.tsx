'use client'

import { useEffect, useState, useRef } from 'react'

interface ConfettiBurstProps {
  trigger: boolean
  onComplete?: () => void
  cardRef?: React.RefObject<HTMLDivElement>
}

export default function ConfettiBurst({ trigger, onComplete, cardRef }: ConfettiBurstProps) {
  const [particles, setParticles] = useState<Array<{
    id: number
    x: number
    y: number
    delay: number
    duration: number
    color: string
    translateX: number
    translateY: number
    rotate: number
  }>>([])
  const [position, setPosition] = useState<{ top: number; left: number } | null>(null)

  useEffect(() => {
    if (trigger && cardRef?.current) {
      // Get card position relative to viewport
      const rect = cardRef.current.getBoundingClientRect()
      const centerX = rect.left + rect.width / 2
      const centerY = rect.top + rect.height / 2
      
      setPosition({ left: centerX, top: centerY })
      
      // Generate 30 confetti particles
      const newParticles = Array.from({ length: 30 }, (_, i) => {
        const angle = (Math.random() * 360) * (Math.PI / 180)
        const velocity = 80 + Math.random() * 60
        const translateX = Math.cos(angle) * velocity
        const translateY = Math.sin(angle) * velocity
        
        return {
          id: i,
          x: 50 + (Math.random() - 0.5) * 20, // Center with slight variation
          y: 50 + (Math.random() - 0.5) * 20,
          delay: Math.random() * 0.1,
          duration: 0.8 + Math.random() * 0.4,
          color: ['#FFD700', '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE'][
            Math.floor(Math.random() * 8)
          ],
          translateX,
          translateY,
          rotate: Math.random() * 720,
        }
      })
      
      setParticles(newParticles)
      
      // Clean up after animation completes
      const timeout = setTimeout(() => {
        setParticles([])
        setPosition(null)
        if (onComplete) {
          onComplete()
        }
      }, 1500)
      
      return () => clearTimeout(timeout)
    }
  }, [trigger, onComplete, cardRef])

  if (particles.length === 0 || !position) return null

  return (
    <>
      <div 
        className="fixed pointer-events-none z-50"
        style={{
          left: `${position.left}px`,
          top: `${position.top}px`,
          transform: 'translate(-50%, -50%)',
          width: '200px',
          height: '200px',
        }}
      >
        {particles.map((particle) => (
          <div
            key={particle.id}
            className="absolute w-2 h-2 rounded-full"
            style={{
              left: `${particle.x}%`,
              top: `${particle.y}%`,
              backgroundColor: particle.color,
              animation: `confetti-burst ${particle.duration}s ease-out ${particle.delay}s forwards`,
              transformOrigin: 'center',
              '--translate-x': particle.translateX,
              '--translate-y': particle.translateY,
              '--rotate': `${particle.rotate}deg`,
            } as React.CSSProperties}
          />
        ))}
      </div>
      <style jsx global>{`
        @keyframes confetti-burst {
          0% {
            transform: translate(0, 0) rotate(0deg) scale(1);
            opacity: 1;
          }
          100% {
            transform: translate(
              calc(var(--translate-x, 0) * 1px),
              calc(var(--translate-y, 0) * 1px)
            ) rotate(var(--rotate, 0deg)) scale(0);
            opacity: 0;
          }
        }
      `}</style>
    </>
  )
}
