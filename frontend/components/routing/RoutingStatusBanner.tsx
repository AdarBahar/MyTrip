"use client";

import { useState, useEffect } from 'react'
import { AlertTriangle, Clock, MapPin, RefreshCw } from 'lucide-react'

interface RoutingStatusBannerProps {
  dayId: string
  onRetry?: () => void
}

export default function RoutingStatusBanner({ dayId, onRetry }: RoutingStatusBannerProps) {
  const [status, setStatus] = useState<'normal' | 'rate_limited' | 'coverage_issue' | 'service_down'>('normal')
  const [retryCountdown, setRetryCountdown] = useState<number>(0)
  const [lastError, setLastError] = useState<string>('')

  useEffect(() => {
    const handleRoutingError = (event: CustomEvent) => {
      if (event.detail?.dayId !== dayId) return
      
      const error = event.detail?.error
      const message = error?.message || ''
      
      setLastError(message)
      
      if (error?.status === 429 || message.includes('rate limit')) {
        setStatus('rate_limited')
        setRetryCountdown(60) // 1 minute countdown
      } else if (message.includes('coverage area') || message.includes('out of bounds')) {
        setStatus('coverage_issue')
        setRetryCountdown(120) // 2 minute countdown
      } else if (error?.status >= 500) {
        setStatus('service_down')
        setRetryCountdown(180) // 3 minute countdown
      }
    }

    const handleRoutingSuccess = (event: CustomEvent) => {
      if (event.detail?.dayId !== dayId) return
      setStatus('normal')
      setRetryCountdown(0)
      setLastError('')
    }

    window.addEventListener('routing-error', handleRoutingError as EventListener)
    window.addEventListener('routing-success', handleRoutingSuccess as EventListener)

    return () => {
      window.removeEventListener('routing-error', handleRoutingError as EventListener)
      window.removeEventListener('routing-success', handleRoutingSuccess as EventListener)
    }
  }, [dayId])

  useEffect(() => {
    if (retryCountdown > 0) {
      const timer = setTimeout(() => {
        setRetryCountdown(prev => prev - 1)
      }, 1000)
      return () => clearTimeout(timer)
    } else if (retryCountdown === 0 && status !== 'normal') {
      setStatus('normal')
    }
  }, [retryCountdown, status])

  if (status === 'normal') return null

  const getStatusConfig = () => {
    switch (status) {
      case 'rate_limited':
        return {
          icon: <Clock className="w-4 h-4" />,
          title: 'Routing temporarily paused',
          description: 'Too many requests - taking a short break',
          color: 'bg-yellow-50 border-yellow-200 text-yellow-800',
          iconColor: 'text-yellow-600'
        }
      case 'coverage_issue':
        return {
          icon: <MapPin className="w-4 h-4" />,
          title: 'Location coverage limitation',
          description: 'Some locations are outside our primary coverage area',
          color: 'bg-blue-50 border-blue-200 text-blue-800',
          iconColor: 'text-blue-600'
        }
      case 'service_down':
        return {
          icon: <AlertTriangle className="w-4 h-4" />,
          title: 'Routing service unavailable',
          description: 'External routing services are temporarily down',
          color: 'bg-red-50 border-red-200 text-red-800',
          iconColor: 'text-red-600'
        }
      default:
        return {
          icon: <AlertTriangle className="w-4 h-4" />,
          title: 'Routing issue',
          description: 'Temporary routing problem',
          color: 'bg-gray-50 border-gray-200 text-gray-800',
          iconColor: 'text-gray-600'
        }
    }
  }

  const config = getStatusConfig()
  const minutes = Math.floor(retryCountdown / 60)
  const seconds = retryCountdown % 60

  return (
    <div className={`rounded-lg border p-3 mb-4 ${config.color}`}>
      <div className="flex items-start gap-3">
        <div className={config.iconColor}>
          {config.icon}
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium">{config.title}</h4>
          <p className="text-sm opacity-90 mt-1">{config.description}</p>
          
          {retryCountdown > 0 && (
            <div className="flex items-center gap-2 mt-2">
              <div className="text-xs opacity-75">
                Auto-retry in {minutes > 0 ? `${minutes}m ` : ''}{seconds}s
              </div>
              <div className="flex-1 bg-white bg-opacity-50 rounded-full h-1">
                <div 
                  className="bg-current h-1 rounded-full transition-all duration-1000"
                  style={{ width: `${((180 - retryCountdown) / 180) * 100}%` }}
                />
              </div>
            </div>
          )}
          
          {status === 'coverage_issue' && (
            <div className="mt-2 text-xs opacity-75">
              <strong>Tip:</strong> Try using locations within Israel/Palestine for best results, or use major cities and landmarks for international destinations.
            </div>
          )}
          
          {status === 'rate_limited' && (
            <div className="mt-2 text-xs opacity-75">
              <strong>Tip:</strong> Consider using fewer stops or try again during off-peak hours.
            </div>
          )}
        </div>
        
        {onRetry && retryCountdown === 0 && (
          <button
            onClick={onRetry}
            className="flex items-center gap-1 px-2 py-1 text-xs bg-white bg-opacity-50 hover:bg-opacity-75 rounded transition-colors"
          >
            <RefreshCw className="w-3 h-3" />
            Retry
          </button>
        )}
      </div>
    </div>
  )
}
