/**
 * Providers Component
 *
 * Application context providers:
 * - React Query for data fetching and caching
 * - Toast notifications for user feedback
 */

'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { useState } from 'react'
import { ToastProvider } from '@/components/ui/use-toast'

interface ProvidersProps {
  children: React.ReactNode
}

export function Providers({ children }: ProvidersProps) {
  const [queryClient] = useState(() =>
    new QueryClient({
      defaultOptions: {
        queries: {
          staleTime: 60 * 1000, // 1 minute
          retry: (failureCount, error: any) => {
            // Don't retry 4xx errors
            if (error?.status >= 400 && error?.status < 500) return false
            return failureCount < 2
          },
          refetchOnWindowFocus: false
        }
      }
    })
  )

  const isDevelopment = process.env.NODE_ENV === 'development'

  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        {children}
      </ToastProvider>
      {isDevelopment && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  )
}