/**
 * Reusable Route Results Panel Component
 * 
 * Displays route computation results including map, metrics, optimization savings,
 * and route segments. Completely generic and reusable for any route display context.
 */

import React from 'react'
import dynamic from 'next/dynamic'

// Dynamic map import to avoid SSR issues
const RouteBreakdownMap = dynamic(
  () => import('@/components/test/RouteBreakdownMap'),
  { ssr: false }
)

export interface RoutePoint {
  lat: number
  lon: number
  name: string
}

export interface RouteSegment {
  from_point?: RoutePoint
  to_point?: RoutePoint
  from_name?: string
  to_name?: string
  distance_km: number
  duration_min: number
  segment_type?: string
  geometry?: any
  instructions?: any[]
}

export interface OptimizationSavings {
  distance_km_saved: number
  duration_min_saved: number
  distance_improvement_percent: number
  duration_improvement_percent: number
}

export interface RouteResultsData {
  start?: RoutePoint
  end?: RoutePoint
  total_distance_km: number
  total_duration_min: number
  segments?: RouteSegment[]
  optimization_savings?: OptimizationSavings
  geometry?: any
  computed_at?: string
  route_persisted?: boolean
  persistence_reason?: string
}

export interface RouteResultsPanelProps {
  title?: string
  data: RouteResultsData
  
  // Map configuration
  showMap?: boolean
  mapHeight?: number
  mapCenter?: [number, number]
  mapZoom?: number
  
  // Display options
  showSummary?: boolean
  showOptimizationResults?: boolean
  showSegments?: boolean
  showPersistenceInfo?: boolean
  
  // Customization
  className?: string
  summaryLayout?: 'grid' | 'horizontal' | 'vertical'
  
  // Custom renderers
  customSummaryRenderer?: (data: RouteResultsData) => React.ReactNode
  customOptimizationRenderer?: (savings: OptimizationSavings) => React.ReactNode
  customSegmentRenderer?: (segment: RouteSegment, index: number) => React.ReactNode
}

export default function RouteResultsPanel({
  title = "Route Results",
  data,
  showMap = true,
  mapHeight = 400,
  mapCenter,
  mapZoom = 12,
  showSummary = true,
  showOptimizationResults = true,
  showSegments = true,
  showPersistenceInfo = false,
  className = "",
  summaryLayout = 'grid',
  customSummaryRenderer,
  customOptimizationRenderer,
  customSegmentRenderer
}: RouteResultsPanelProps) {

  // Determine map center from data if not provided
  const effectiveMapCenter = mapCenter || (data.start ? [data.start.lat, data.start.lon] : undefined)

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
        
        {/* Persistence Info */}
        {showPersistenceInfo && data.route_persisted !== undefined && (
          <div className={`text-xs px-2 py-1 rounded-full ${
            data.route_persisted 
              ? 'text-green-600 bg-green-50' 
              : 'text-gray-600 bg-gray-50'
          }`}>
            {data.route_persisted ? '💾 Route Saved' : '📝 Not Saved'}
          </div>
        )}
      </div>
      
      {/* Map */}
      {showMap && (
        <div className="mb-6">
          <RouteBreakdownMap
            breakdown={data}
            center={effectiveMapCenter}
            zoom={mapZoom}
            height={mapHeight}
          />
        </div>
      )}

      {/* Summary */}
      {showSummary && (
        <div className="mb-6">
          {customSummaryRenderer ? (
            customSummaryRenderer(data)
          ) : (
            <div className={`gap-4 mb-4 ${
              summaryLayout === 'grid' ? 'grid grid-cols-2' :
              summaryLayout === 'horizontal' ? 'flex' :
              'space-y-4'
            }`}>
              {/* Distance */}
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {(data.total_distance_km || 0).toFixed(1)} km
                </div>
                <div className="text-sm text-blue-800">Total Distance</div>
              </div>
              
              {/* Duration */}
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {Math.round(data.total_duration_min || 0)} min
                </div>
                <div className="text-sm text-green-800">Total Duration</div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Optimization Results */}
      {showOptimizationResults && data.optimization_savings && (
        <div className="mb-6">
          {customOptimizationRenderer ? (
            customOptimizationRenderer(data.optimization_savings)
          ) : (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xl">🚀</span>
                <h3 className="font-semibold text-yellow-800">Route Optimization Results</h3>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="font-medium text-yellow-800">Distance Saved</div>
                  <div className="text-yellow-700">
                    {data.optimization_savings.distance_km_saved.toFixed(2)} km
                    ({data.optimization_savings.distance_improvement_percent.toFixed(1)}% improvement)
                  </div>
                </div>
                <div>
                  <div className="font-medium text-yellow-800">Time Saved</div>
                  <div className="text-yellow-700">
                    {Math.round(data.optimization_savings.duration_min_saved)} min
                    ({data.optimization_savings.duration_improvement_percent.toFixed(1)}% improvement)
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Route Segments */}
      {showSegments && data.segments && data.segments.length > 0 && (
        <div>
          <h3 className="font-medium text-gray-900 mb-3">Route Segments</h3>
          <div className="space-y-2">
            {data.segments.map((segment, index) => (
              <div key={index}>
                {customSegmentRenderer ? (
                  customSegmentRenderer(segment, index)
                ) : (
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="font-medium">
                          {segment.from_point?.name || segment.from_name || 'Unknown'} → {segment.to_point?.name || segment.to_name || 'Unknown'}
                        </div>
                        <div className="text-sm text-gray-600">
                          {(segment.distance_km || 0).toFixed(1)} km • {Math.round(segment.duration_min || 0)} min
                        </div>
                        {segment.segment_type && (
                          <div className="text-xs text-gray-500 mt-1">
                            Type: {segment.segment_type}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Persistence Details */}
      {showPersistenceInfo && data.persistence_reason && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <div className="text-sm text-gray-600">
            <span className="font-medium">Persistence Status:</span> {data.persistence_reason}
          </div>
          {data.computed_at && (
            <div className="text-xs text-gray-500 mt-1">
              Computed at: {new Date(data.computed_at).toLocaleString()}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// Export additional utility components for custom rendering
export const RouteSummaryCard = ({ 
  value, 
  unit, 
  label, 
  color = 'blue',
  className = "" 
}: {
  value: string | number
  unit: string
  label: string
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple'
  className?: string
}) => (
  <div className={`text-center p-3 bg-${color}-50 rounded-lg ${className}`}>
    <div className={`text-2xl font-bold text-${color}-600`}>
      {value} {unit}
    </div>
    <div className={`text-sm text-${color}-800`}>{label}</div>
  </div>
)

export const OptimizationBadge = ({ 
  savings, 
  type = 'distance' 
}: { 
  savings: OptimizationSavings
  type: 'distance' | 'duration' 
}) => {
  const value = type === 'distance' ? savings.distance_km_saved : savings.duration_min_saved
  const percent = type === 'distance' ? savings.distance_improvement_percent : savings.duration_improvement_percent
  const unit = type === 'distance' ? 'km' : 'min'
  
  return (
    <div className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-medium">
      <span>🚀</span>
      <span>-{type === 'distance' ? value.toFixed(2) : Math.round(value)} {unit}</span>
      <span>({percent.toFixed(1)}%)</span>
    </div>
  )
}
