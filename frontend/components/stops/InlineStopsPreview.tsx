/**
 * InlineStopsPreview
 * Compact, read-focused stops list for a day, displayed under a DayCard
 * - Shows optimized display order (does not alter DB order)
 * - Labels fixed stops
 * - Shows "Add a stop" when empty and a compact button at the bottom (until limit)
 */

'use client'

import React, { useEffect, useMemo, useState } from 'react'
import { MapPin, Plus } from 'lucide-react'
import { listStops, type StopWithPlace } from '@/lib/api/stops'
import { computeDayRoute } from '@/lib/api/routing'
import AddStopModal from '@/components/stops/AddStopModal'
import InlineAddStop from '@/components/stops/InlineAddStop'

interface InlineStopsPreviewProps {
  tripId: string
  dayId: string
  daySeq?: number
  className?: string
  maxVisible?: number // how many to show inline before "+N more"
  maxStops?: number // limit before hiding the add button
  onChange?: (stops: StopWithPlace[]) => Promise<void> | void // called after stop add with latest stops
  onVisualsChange?: (query: string, markers: { id: string; lat: number; lon: number }[]) => void
  dayCenter?: { lat: number; lon: number } | null
}

export default function InlineStopsPreview({
  tripId,
  dayId,
  daySeq,
  className = '',
  maxVisible = 5,
  maxStops = 20,
  onChange,
  onVisualsChange,
  dayCenter,
}: InlineStopsPreviewProps) {
  const [stops, setStops] = useState<StopWithPlace[]>([])
  const [optimizedIds, setOptimizedIds] = useState<string[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showAdd, setShowAdd] = useState(false)
  const [inlineAddMode, setInlineAddMode] = useState(false)

  async function load() {
    try {
      setLoading(true)
      setError(null)
      const resp = await listStops(tripId, dayId, { includePlaces: true })
      const s = resp.stops as StopWithPlace[]
      setStops(s)
      // Compute display order (optimized) if there are 3+ points
      if (s.length >= 3) {
        try {
          const preview = await computeDayRoute(dayId, { optimize: true })
          setOptimizedIds(preview.proposed_order || null)
        } catch (e) {
          setOptimizedIds(null)
        }
      } else {
        setOptimizedIds(null)
      }
    } catch (e: any) {
      setError(e?.message || 'Failed to load stops')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load(); onVisualsChange && onVisualsChange('', []); }, [tripId, dayId])

  const displayStops = useMemo(() => {
    if (!optimizedIds || optimizedIds.length === 0) return stops
    // Reorder by proposed_order; keep only those ids found
    const byId = new Map(stops.map(s => [s.id, s] as const))
    const reordered: StopWithPlace[] = []
    for (const id of optimizedIds) {
      const st = byId.get(id)
      if (st) reordered.push(st)
    }
    // Append any stops not in proposed_order (defensive)
    for (const s of stops) {
      if (!reordered.find(r => r.id === s.id)) reordered.push(s)
    }
    return reordered
  }, [stops, optimizedIds])

  const visibleStops = displayStops.slice(0, Math.max(0, maxVisible))
  const remaining = Math.max(0, displayStops.length - visibleStops.length)
  const canAdd = stops.length < maxStops

  const handleStopAdded = async () => {
    setShowAdd(false)
    // Reload to get the authoritative stops list (with embedded places)
    await load()
    // Use the freshly loaded stops, not the stale state captured at call time
    try {
      const resp = await listStops(tripId, dayId, { includePlaces: true })
      const latest = resp.stops as StopWithPlace[]
      setStops(latest)
      try { window.dispatchEvent(new CustomEvent('stops-mutated', { detail: { dayId } })) } catch {}
      if (onChange) await onChange(latest)
    } catch {
      if (onChange) await onChange(stops)
    }
  }

  if (loading) {
    return (
      <div className={`border rounded-md p-3 ${className}`}>
        <div className="h-4 bg-gray-100 rounded w-1/2 animate-pulse mb-2" />
        <div className="h-4 bg-gray-100 rounded w-2/3 animate-pulse mb-2" />
        <div className="h-4 bg-gray-100 rounded w-1/3 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className={`border rounded-md p-3 ${className}`}>
        <div className="text-sm text-red-700">{error}</div>
      </div>
    )
  }

  if (stops.length === 0) {
    return (
      <div className={`border rounded-md p-3 ${className}`}>
        {!inlineAddMode ? (
          <div className="text-center">
            <MapPin className="w-6 h-6 text-gray-400 mx-auto mb-2" />
            <div className="text-sm text-gray-600">No stops yet for Day {daySeq ?? ''}</div>
            <button
              onClick={() => setInlineAddMode(true)}
              className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
            >
              <Plus className="w-4 h-4" /> Add a stop
            </button>
          </div>
        ) : (
          <InlineAddStop tripId={tripId} dayId={dayId} dayCenter={dayCenter} onAdded={handleStopAdded} onCancel={() => setInlineAddMode(false)} onVisualsChange={onVisualsChange} />
        )}
      </div>
    )
  }

  return (
    <div className={`border rounded-md p-3 ${className}`}>
      <div className="space-y-2">
        {visibleStops.map((s) => (
          <div key={s.id} className="flex items-center justify-between text-sm">
            <div className="min-w-0 flex-1 truncate">
              <span className="text-gray-800 font-medium truncate">
                {s.place?.name || 'Unnamed'}
              </span>
              {s.place?.address && (
                <span className="text-gray-500 truncate"> — {(s.place.meta as any)?.normalized?.display_short || s.place.address}</span>
              )}
            </div>
            {/* Fixed label */}
            {(s.fixed || s.kind === 'start' || s.kind === 'end') && (
              <span className="ml-2 text-[10px] px-2 py-0.5 rounded-full border bg-gray-50 text-gray-600">Fixed</span>
            )}
          </div>
        ))}
        {remaining > 0 && (
          <div className="text-xs text-gray-500">+{remaining} more stops</div>
        )}
      </div>

      {/* Footer actions */}
      {canAdd && (
        <div className="pt-2">
          {!inlineAddMode ? (
            <button
              onClick={() => setInlineAddMode(true)}
              className="inline-flex items-center gap-2 px-2.5 py-1.5 text-xs bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              <Plus className="w-3.5 h-3.5" /> Add a stop
            </button>
          ) : (
            <InlineAddStop tripId={tripId} dayId={dayId} dayCenter={dayCenter} onAdded={handleStopAdded} onCancel={() => setInlineAddMode(false)} onVisualsChange={onVisualsChange} />
          )}
        </div>
      )}
    </div>
  )
}

