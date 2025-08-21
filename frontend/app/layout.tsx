import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '@/styles/globals.css'
import { Providers } from '@/components/providers'
import { DebugPanel, DevIndicator } from '@/components/debug'
import { SimpleDebugToggle } from '@/components/debug/simple-debug-toggle'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'RoadTrip Planner',
  description: 'Plan your perfect road trip with collaborative route planning and interactive maps',
  keywords: ['road trip', 'travel', 'route planning', 'maps', 'collaboration'],
  authors: [{ name: 'RoadTrip Planner Team' }],
  viewport: 'width=device-width, initial-scale=1',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          {children}
          {/* Global Debug Panel - Available on all pages during development */}
          <DebugPanel />
          {/* Development Environment Indicator */}
          <DevIndicator position="top-right" showApiCount={true} />
          {/* Simple Debug Toggle - Highly visible for testing */}
          <SimpleDebugToggle />
        </Providers>
      </body>
    </html>
  )
}