/**
 * Root Layout Component
 *
 * Core application layout with:
 * - SEO-optimized metadata
 * - Accessibility features
 * - Font optimization
 * - Error boundaries
 */

import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '@/styles/globals.css'
import { Providers } from '@/components/providers'
import { SiteHeader } from '@/components/site-header'
import { MinimalDebugToggle, MinimalDebugPanel } from '@/components/minimal-debug'
import { PageErrorBoundary } from '@/components/ui/error-boundary'

// Optimized font loading
const inter = Inter({
  subsets: ['latin'],
  display: 'swap'
})

// SEO and social media metadata
export const metadata: Metadata = {
  title: {
    default: 'MyTrip - Road Trip Planner',
    template: '%s | MyTrip'
  },
  description: 'Plan your perfect road trip with collaborative route planning and interactive maps.',

  // Social media sharing
  openGraph: {
    title: 'MyTrip - Road Trip Planner',
    description: 'Plan your perfect road trip with collaborative route planning and interactive maps.',
    type: 'website',
    locale: 'en_US'
  },

  twitter: {
    card: 'summary_large_image',
    title: 'MyTrip - Road Trip Planner',
    description: 'Plan your perfect road trip with collaborative route planning and interactive maps.'
  }
}

interface RootLayoutProps {
  children: React.ReactNode
}

export default function RootLayout({ children }: RootLayoutProps) {
  const isDevelopment = process.env.NODE_ENV === 'development'

  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} antialiased`}>
        <PageErrorBoundary>
          <Providers>
            {/* Skip link for accessibility */}
            <a
              href="#main-content"
              className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-blue-600 text-white px-4 py-2 rounded-md z-50"
            >
              Skip to main content
            </a>

            <SiteHeader />

            <main id="main-content" className="min-h-screen">
              {children}
            </main>

            {/* Debug tools - development only */}
            {isDevelopment && (
              <>
                <MinimalDebugToggle />
                <MinimalDebugPanel />
              </>
            )}
          </Providers>
        </PageErrorBoundary>
      </body>
    </html>
  )
}