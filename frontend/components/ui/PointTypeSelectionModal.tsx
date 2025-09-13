/**
 * Reusable Point Type Selection Modal Component
 * 
 * Generic modal for selecting point types with customizable options.
 * Can be used for route points, waypoints, markers, or any categorized location selection.
 */

import React from 'react'
import { X } from 'lucide-react'

export interface PointTypeOption {
  id: string
  label: string
  description: string
  color: string
  icon?: React.ReactNode
  disabled?: boolean
}

export interface SelectedItem {
  id?: string
  name: string
  lat?: number
  lon?: number
  address?: string
  [key: string]: any
}

export interface PointTypeSelectionModalProps {
  isOpen: boolean
  onClose: () => void
  onSelect: (typeId: string) => void
  
  // Content
  title?: string
  selectedItem: SelectedItem | null
  options: PointTypeOption[]
  
  // Customization
  showSelectedItemDetails?: boolean
  selectedItemLabel?: string
  className?: string
  
  // Custom renderers
  customSelectedItemRenderer?: (item: SelectedItem) => React.ReactNode
  customOptionRenderer?: (option: PointTypeOption, onSelect: () => void) => React.ReactNode
}

// Default point type options for route planning
export const DEFAULT_ROUTE_POINT_TYPES: PointTypeOption[] = [
  {
    id: 'start',
    label: 'Start Point',
    description: 'Beginning of your journey',
    color: 'green',
    icon: <div className="w-3 h-3 bg-green-500 rounded-full"></div>
  },
  {
    id: 'stop',
    label: 'Stop Point',
    description: 'Intermediate destination',
    color: 'blue',
    icon: <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
  },
  {
    id: 'end',
    label: 'End Point',
    description: 'Final destination',
    color: 'red',
    icon: <div className="w-3 h-3 bg-red-500 rounded-full"></div>
  }
]

export default function PointTypeSelectionModal({
  isOpen,
  onClose,
  onSelect,
  title = "Select Point Type",
  selectedItem,
  options,
  showSelectedItemDetails = true,
  selectedItemLabel = "Selected",
  className = "",
  customSelectedItemRenderer,
  customOptionRenderer
}: PointTypeSelectionModalProps) {

  if (!isOpen) return null

  const handleSelect = (typeId: string) => {
    onSelect(typeId)
    onClose()
  }

  const getColorClasses = (color: string) => {
    const colorMap = {
      green: 'border-green-500 bg-green-50 hover:border-green-600',
      blue: 'border-blue-500 bg-blue-50 hover:border-blue-600',
      red: 'border-red-500 bg-red-50 hover:border-red-600',
      yellow: 'border-yellow-500 bg-yellow-50 hover:border-yellow-600',
      purple: 'border-purple-500 bg-purple-50 hover:border-purple-600',
      gray: 'border-gray-500 bg-gray-50 hover:border-gray-600'
    }
    return colorMap[color as keyof typeof colorMap] || colorMap.gray
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className={`bg-white rounded-lg shadow-xl max-w-md w-full mx-4 ${className}`}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Close modal"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6">
          {/* Selected Item Display */}
          {showSelectedItemDetails && selectedItem && (
            <div className="mb-4">
              {customSelectedItemRenderer ? (
                customSelectedItemRenderer(selectedItem)
              ) : (
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">
                    {selectedItemLabel}:
                  </p>
                  <div className="font-medium text-gray-900">{selectedItem.name}</div>
                  {selectedItem.address && (
                    <div className="text-sm text-gray-600 mt-1">{selectedItem.address}</div>
                  )}
                  {selectedItem.lat && selectedItem.lon && (
                    <div className="text-xs text-gray-500 mt-1">
                      {selectedItem.lat.toFixed(6)}, {selectedItem.lon.toFixed(6)}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Point Type Options */}
          <div className="space-y-3">
            {options.map((option) => (
              <div key={option.id}>
                {customOptionRenderer ? (
                  customOptionRenderer(option, () => handleSelect(option.id))
                ) : (
                  <button
                    onClick={() => handleSelect(option.id)}
                    disabled={option.disabled}
                    className={`w-full p-3 text-left border rounded-lg transition-colors ${
                      option.disabled 
                        ? 'border-gray-200 bg-gray-50 opacity-50 cursor-not-allowed'
                        : `border-gray-200 hover:${getColorClasses(option.color)}`
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      {/* Icon */}
                      {option.icon && (
                        <div className="flex-shrink-0">
                          {option.icon}
                        </div>
                      )}
                      
                      {/* Content */}
                      <div className="flex-1">
                        <div className="font-medium text-gray-900">{option.label}</div>
                        <div className="text-sm text-gray-600">{option.description}</div>
                      </div>
                      
                      {/* Disabled indicator */}
                      {option.disabled && (
                        <div className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">
                          Disabled
                        </div>
                      )}
                    </div>
                  </button>
                )}
              </div>
            ))}
          </div>

          {/* No options message */}
          {options.length === 0 && (
            <div className="text-center py-6 text-gray-500">
              <p>No options available</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Utility function to create route point type options with existing points
export const createRoutePointOptions = (existingPoints: { type: string }[] = []) => {
  const hasStart = existingPoints.some(p => p.type === 'start')
  const hasEnd = existingPoints.some(p => p.type === 'end')
  
  return DEFAULT_ROUTE_POINT_TYPES.map(option => ({
    ...option,
    disabled: 
      (option.id === 'start' && hasStart) ||
      (option.id === 'end' && hasEnd)
  }))
}

// Utility function to create custom point type options
export const createCustomPointOptions = (
  types: Array<{
    id: string
    label: string
    description: string
    color?: string
    icon?: React.ReactNode
    disabled?: boolean
  }>
): PointTypeOption[] => {
  return types.map(type => ({
    color: 'blue',
    ...type
  }))
}

// Example usage for different contexts:

// For waypoint selection
export const WAYPOINT_TYPES: PointTypeOption[] = [
  {
    id: 'checkpoint',
    label: 'Checkpoint',
    description: 'Required waypoint to pass through',
    color: 'blue',
    icon: <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
  },
  {
    id: 'optional',
    label: 'Optional Stop',
    description: 'Optional point of interest',
    color: 'yellow',
    icon: <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
  },
  {
    id: 'emergency',
    label: 'Emergency Point',
    description: 'Emergency or safety checkpoint',
    color: 'red',
    icon: <div className="w-3 h-3 bg-red-500 rounded-full"></div>
  }
]

// For marker categorization
export const MARKER_TYPES: PointTypeOption[] = [
  {
    id: 'restaurant',
    label: 'Restaurant',
    description: 'Dining location',
    color: 'green',
    icon: <span className="text-sm">🍽️</span>
  },
  {
    id: 'hotel',
    label: 'Hotel',
    description: 'Accommodation',
    color: 'blue',
    icon: <span className="text-sm">🏨</span>
  },
  {
    id: 'attraction',
    label: 'Attraction',
    description: 'Point of interest',
    color: 'purple',
    icon: <span className="text-sm">🎯</span>
  }
]
