/**
 * Trip Skeleton Components
 * 
 * Provides skeleton loading states for trip-related UI components
 */

'use client'

import React from 'react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'

interface SkeletonProps {
  className?: string
}

const Skeleton: React.FC<SkeletonProps> = ({ className = '' }) => {
  return (
    <div className={`animate-pulse bg-gray-200 rounded ${className}`} />
  )
}

export const TripCardSkeleton: React.FC = () => {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <Skeleton className="h-6 w-3/4 mb-2" />
            <Skeleton className="h-4 w-1/2 mb-3" />
            <div className="flex items-center gap-2">
              <Skeleton className="h-5 w-16 rounded-full" />
              <Skeleton className="h-5 w-20 rounded-full" />
            </div>
          </div>
        </div>
        <Skeleton className="h-4 w-2/3 mt-2" />
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4 mb-4">
          <div className="flex items-center gap-1">
            <Skeleton className="h-4 w-4 rounded" />
            <Skeleton className="h-4 w-16" />
          </div>
          <div className="flex items-center gap-1">
            <Skeleton className="h-4 w-4 rounded" />
            <Skeleton className="h-4 w-12" />
          </div>
        </div>
        
        <Skeleton className="h-3 w-3/4 mb-3" />
        
        <div className="flex gap-2 mb-3">
          <Skeleton className="h-9 flex-1 rounded" />
          <Skeleton className="h-9 w-16 rounded" />
        </div>
        
        <div className="pt-3 border-t border-gray-100">
          <Skeleton className="h-8 w-20 ml-auto rounded" />
        </div>
      </CardContent>
    </Card>
  )
}

export const TripListSkeleton: React.FC<{ count?: number }> = ({ count = 6 }) => {
  return (
    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
      {Array.from({ length: count }, (_, index) => (
        <TripCardSkeleton key={index} />
      ))}
    </div>
  )
}

export const TripPageHeaderSkeleton: React.FC = () => {
  return (
    <div className="flex justify-between items-center mb-8">
      <div>
        <div className="flex items-center space-x-4 mb-2">
          <Skeleton className="h-10 w-48" />
        </div>
        <Skeleton className="h-5 w-80" />
      </div>
      <div className="flex gap-2">
        <Skeleton className="h-10 w-20 rounded" />
        <Skeleton className="h-10 w-40 rounded" />
      </div>
    </div>
  )
}

export default TripListSkeleton
