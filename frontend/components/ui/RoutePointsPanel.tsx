/**
 * Reusable Route Points Panel Component
 * 
 * Displays and manages a list of route points with full CRUD operations.
 * Completely generic and reusable across different route management contexts.
 */

import React from 'react'
import { Search, Plus, X } from 'lucide-react'

export interface RoutePoint {
  id: string
  name: string
  lat: number
  lon: number
  type: 'start' | 'stop' | 'end'
  fixed?: boolean
  seq?: number
}

export interface RoutePointsActions {
  onAddPoint?: () => void
  onRemovePoint?: (pointId: string) => void
  onToggleFixed?: (pointId: string, currentFixed: boolean) => void
  onDebugAction?: () => void
}

export interface RoutePointsPanelProps {
  title?: string
  points: RoutePoint[]
  loading?: boolean
  actions?: RoutePointsActions
  
  // Status indicators
  persistenceStatus?: {
    saved: boolean
    message: string
  }
  
  // Auto-compute controls
  autoCompute?: {
    enabled: boolean
    onToggle: () => void
  }
  
  // Action buttons
  primaryAction?: {
    label: string
    onClick: () => void
    disabled?: boolean
    loading?: boolean
  }
  
  secondaryAction?: {
    label: string
    onClick: () => void
    disabled?: boolean
    loading?: boolean
    icon?: React.ReactNode
  }
  
  // Requirements and messages
  requirementMessage?: string
  statusMessage?: string
  
  // Customization
  showDebugButton?: boolean
  showFixToggle?: boolean
  sortPoints?: boolean
  className?: string
}

export default function RoutePointsPanel({
  title = "Route Points",
  points,
  loading = false,
  actions,
  persistenceStatus,
  autoCompute,
  primaryAction,
  secondaryAction,
  requirementMessage,
  statusMessage,
  showDebugButton = false,
  showFixToggle = true,
  sortPoints = true,
  className = ""
}: RoutePointsPanelProps) {
  
  // Sort points if requested
  const displayPoints = sortPoints 
    ? [...points].sort((a, b) => {
        const order = { start: 0, stop: 1, end: 2 }
        return order[a.type] - order[b.type]
      })
    : points

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
        <div className="flex items-center gap-2">
          {actions?.onAddPoint && (
            <button
              onClick={actions.onAddPoint}
              className="flex items-center gap-1 px-3 py-1 text-sm bg-purple-600 text-white rounded-md hover:bg-purple-700"
            >
              <Search className="h-4 w-4" />
              Add Point
            </button>
          )}
          
          {showDebugButton && actions?.onDebugAction && (
            <button
              onClick={actions.onDebugAction}
              className="flex items-center gap-1 px-3 py-1 text-sm bg-orange-600 text-white rounded-md hover:bg-orange-700"
            >
              🐛 Debug
            </button>
          )}
        </div>
      </div>

      {/* Loading State */}
      {loading ? (
        <div className="text-center py-6">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-600 mx-auto"></div>
          <p className="text-gray-600 mt-2">Loading route points...</p>
        </div>
      ) : points.length === 0 ? (
        /* Empty State */
        <div className="text-center py-6 text-gray-500">
          <Search className="h-8 w-8 mx-auto mb-2 text-gray-400" />
          <p>No route points added yet</p>
          <p className="text-sm">Click "Add Point" to start building your route</p>
        </div>
      ) : (
        /* Points List */
        <div className="space-y-3">
          {/* Status Bar */}
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-gray-900">
              {title} ({points.length})
            </h4>
            <div className="flex items-center gap-2">
              {/* Persistence Status */}
              {persistenceStatus && (
                <div className={`text-xs px-2 py-1 rounded-full ${
                  persistenceStatus.saved 
                    ? 'text-green-600 bg-green-50' 
                    : 'text-gray-600 bg-gray-50'
                }`}>
                  {persistenceStatus.saved ? '💾 Saved to database' : '📝 Not saved yet'}
                </div>
              )}
              
              {/* Auto-compute Toggle */}
              {autoCompute && (
                <button
                  onClick={autoCompute.onToggle}
                  className={`text-xs px-2 py-1 rounded-full border ${
                    autoCompute.enabled
                      ? 'text-blue-600 bg-blue-50 border-blue-200'
                      : 'text-gray-600 bg-gray-50 border-gray-200'
                  }`}
                  title={autoCompute.enabled ? 'Auto-compute enabled' : 'Auto-compute disabled'}
                >
                  {autoCompute.enabled ? '🔄 Auto' : '⏸️ Manual'}
                </button>
              )}
            </div>
          </div>
          
          {/* Points */}
          {displayPoints.map((point, index) => (
            <div
              key={point.id}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border-l-4"
              style={{
                borderLeftColor:
                  point.type === 'start' ? '#10b981' :
                  point.type === 'end' ? '#ef4444' : '#3b82f6'
              }}
            >
              <div className="flex items-center gap-3 flex-1">
                <div className="flex items-center gap-2">
                  {/* Point Type Indicator */}
                  <div className={`w-4 h-4 rounded-full flex items-center justify-center text-white text-xs font-bold ${
                    point.type === 'start' ? 'bg-green-500' :
                    point.type === 'end' ? 'bg-red-500' : 'bg-blue-500'
                  }`}>
                    {point.type === 'start' ? 'S' : point.type === 'end' ? 'E' : index}
                  </div>
                  
                  {/* Type Label */}
                  <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                    {point.type}
                  </div>
                  
                  {/* Fixed Badge */}
                  {point.fixed && (
                    <div className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full font-medium">
                      FIXED
                    </div>
                  )}
                </div>
                
                {/* Point Details */}
                <div className="flex-1">
                  <div className="font-medium text-gray-900">
                    {point.name}
                  </div>
                  <div className="text-xs text-gray-600">
                    {point.lat.toFixed(6)}, {point.lon.toFixed(6)}
                  </div>
                </div>
              </div>
              
              {/* Actions */}
              <div className="flex items-center gap-2">
                {/* Fix/Unfix Toggle */}
                {showFixToggle && point.type === 'stop' && actions?.onToggleFixed && (
                  <button
                    onClick={() => actions.onToggleFixed!(point.id, point.fixed || false)}
                    className={`px-2 py-1 text-xs rounded transition-colors ${
                      point.fixed
                        ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                    title={point.fixed ? 'Unfix stop (allow optimization)' : 'Fix stop (prevent optimization)'}
                  >
                    {point.fixed ? '🔒' : '🔓'}
                  </button>
                )}
                
                {/* Remove Button */}
                {actions?.onRemovePoint && (
                  <button
                    onClick={() => actions.onRemovePoint!(point.id)}
                    className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                    title="Remove point"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Action Buttons Section */}
      {(primaryAction || secondaryAction || requirementMessage || statusMessage) && points.length >= 2 && (
        <div className="mt-4 pt-4 border-t border-gray-200 space-y-3">
          {/* Primary Action */}
          {primaryAction && (
            <button
              onClick={primaryAction.onClick}
              disabled={primaryAction.disabled || primaryAction.loading}
              className="w-full py-2 px-4 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
            >
              {primaryAction.loading ? 'Processing...' : primaryAction.label}
            </button>
          )}

          {/* Secondary Action */}
          {secondaryAction && (
            <button
              onClick={secondaryAction.onClick}
              disabled={secondaryAction.disabled || secondaryAction.loading}
              className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {secondaryAction.icon && <span>{secondaryAction.icon}</span>}
              {secondaryAction.loading ? 'Processing...' : secondaryAction.label}
            </button>
          )}

          {/* Requirement Message */}
          {requirementMessage && (
            <p className="text-sm text-gray-500 text-center">
              {requirementMessage}
            </p>
          )}

          {/* Status Message */}
          {statusMessage && (
            <div className="mt-3 p-2 bg-gray-50 rounded-md">
              <div className="text-xs text-gray-600">
                <span className="font-medium">Status:</span> {statusMessage}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
