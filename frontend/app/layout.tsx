import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'NextPlay - Baby Development Activities',
  description: 'Personalized baby development milestone recommendations with play activities',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

