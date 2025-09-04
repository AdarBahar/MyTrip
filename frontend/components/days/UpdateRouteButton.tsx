"use client";

import { useState } from 'react'
import { RefreshCcw } from 'lucide-react'

export default function UpdateRouteButton({ dayId, onUpdated }: { dayId: string, onUpdated?: (loc: any) => void }) {
  const [busy, setBusy] = useState(false)

  const handleClick = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (busy) return
    setBusy(true)
    try {
      const { throttledComputeDayRoute, commitDayRouteWithFallback, getDayActiveSummary } = await import('@/lib/api/routing')
      const preview = await throttledComputeDayRoute(dayId, { optimize: true })
      await commitDayRouteWithFallback(dayId, preview.preview_token, 'Default', { optimize: false })
      const s = await getDayActiveSummary(dayId)
      const loc = {
        start: (s.start as any) || null,
        end: (s.end as any) || null,
        route_total_km: s.route_total_km ?? undefined,
        route_total_min: s.route_total_min ?? undefined,
        route_coordinates: s.route_coordinates ?? undefined,
      }
      // Broadcast first so global listeners update even if a local callback fails
      try { window.dispatchEvent(new CustomEvent('day-summary-updated', { detail: { dayId, loc } })) } catch {}
      try { onUpdated && onUpdated(loc) } catch {}
    } catch (e) {
      // swallow; UI shows disabled state during run
    } finally {
      setBusy(false)
    }
  }

  return (
    <button
      type="button"
      className="inline-flex items-center gap-1 text-[11px] text-blue-600 hover:underline disabled:opacity-50"
      onClick={handleClick}
      disabled={busy}
      title="Recompute and save the route"
    >
      <RefreshCcw className="w-3.5 h-3.5" /> {busy ? 'Updating…' : 'Update route'}
    </button>
  )
}

