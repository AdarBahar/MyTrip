"use client";

import { useState } from 'react'
import { RefreshCcw } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'
import { RoutingError } from '@/lib/api/routing'

export default function UpdateRouteButton({ dayId, onUpdated }: { dayId: string, onUpdated?: (loc: any) => void }) {
  const [busy, setBusy] = useState(false)
  const { toast } = useToast()

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
    } catch (e: any) {
      // Log error and show enhanced user feedback
      console.error('Route update failed:', e);

      if (e instanceof RoutingError) {
        const userMessage = e.getUserMessage();
        const description = userMessage.steps
          ? `${userMessage.description}\n\nNext steps:\n${userMessage.steps.map(step => `• ${step}`).join('\n')}`
          : userMessage.description;

        toast({
          title: userMessage.title,
          description: description,
          variant: 'destructive',
          duration: 8000  // Longer duration for actionable messages
        });
      } else {
        // Fallback for non-routing errors
        toast({
          title: 'Route update failed',
          description: e?.message || 'Please try again later.',
          variant: 'destructive'
        });
      }
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

