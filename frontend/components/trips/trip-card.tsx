/**
 * TripCard Component
 *
 * Displays trip information in a card format
 */

'use client'

import React, { useState } from 'react'
import { Calendar, MapPin, MoreVertical, Edit, Trash2 } from 'lucide-react'
import { Trip, TripCardProps } from '@/types/trip'
import { formatTripDate, formatRelativeTime } from '@/lib/utils/date-format'

const statusStyles = {
  draft: { bg: 'bg-gray-100', text: 'text-gray-700', icon: '📝' },
  active: { bg: 'bg-blue-100', text: 'text-blue-700', icon: '✈️' },
  completed: { bg: 'bg-green-100', text: 'text-green-700', icon: '✅' },
  archived: { bg: 'bg-gray-100', text: 'text-gray-600', icon: '📦' }
}

export const TripCard: React.FC<TripCardProps> = ({
  trip,
  onDelete,
  onEdit,
  loading = false
}) => {
  const [isDeleting, setIsDeleting] = useState(false)
  const [showActions, setShowActions] = useState(false)

  const handleDelete = async () => {
    if (isDeleting) return

    const confirmed = window.confirm(
      `Are you sure you want to delete "${trip.title}"?`
    )

    if (!confirmed) return

    setIsDeleting(true)
    try {
      await onDelete(trip.id)
    } catch (error) {
      console.error('Error deleting trip:', error)
    } finally {
      setIsDeleting(false)
    }
  }

  const statusConfig = statusStyles[trip.status]

  return (
    <div className="bg-white rounded-lg border shadow-sm hover:shadow-md transition-shadow">
      <div className="p-6">
        {/* Header */}
        <div className="flex justify-between items-start mb-3">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 truncate">
              {trip.title}
            </h3>
            {trip.destination && (
              <div className="flex items-center text-gray-600 mt-1">
                <MapPin className="h-4 w-4 mr-1" />
                <span className="text-sm">{trip.destination}</span>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="relative">
            <button
              onClick={() => setShowActions(!showActions)}
              className="p-1 rounded hover:bg-gray-100"
            >
              <MoreVertical className="h-5 w-5 text-gray-500" />
            </button>

            {showActions && (
              <div className="absolute right-0 mt-2 w-40 bg-white rounded-md shadow-lg border z-20">
                <div className="py-1">
                  {onEdit && (
                    <button
                      onClick={() => {
                        setShowActions(false)
                        onEdit(trip)
                      }}
                      className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      <Edit className="h-4 w-4 mr-2" />
                      Edit
                    </button>
                  )}

                  <button
                    onClick={() => {
                      setShowActions(false)
                      handleDelete()
                    }}
                    className="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                    disabled={isDeleting}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    {isDeleting ? 'Deleting...' : 'Delete'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Status and date */}
        <div className="space-y-3">
          <span className={`
            inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
            ${statusConfig.bg} ${statusConfig.text}
          `}>
            <span className="mr-1">{statusConfig.icon}</span>
            {trip.status.charAt(0).toUpperCase() + trip.status.slice(1)}
          </span>

          {trip.start_date && (
            <div className="flex items-center text-gray-600">
              <Calendar className="h-4 w-4 mr-2" />
              <span className="text-sm">
                Starts {formatTripDate(trip.start_date)}
              </span>
            </div>
          )}

          {/* Created date */}
          <div className="text-xs text-gray-500 pt-2 border-t border-gray-100">
            Created {formatRelativeTime(trip.created_at)}
          </div>
        </div>
      </div>

      {/* Click outside to close */}
      {showActions && (
        <div
          className="fixed inset-0 z-10"
          onClick={() => setShowActions(false)}
        />
      )}
    </div>
  )
}

export default TripCard
