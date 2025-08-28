"use client";
import { useEffect, useRef } from 'react'
import { listSavedRoutes, computeDayRoute, commitDayRoute } from '@/lib/api/routing'

/**
 * Auto-generate and save a default route when a day has start & end but no saved routes yet.
 * Guards:
 * - Only runs when start+end exist and there are 0 routes
 * - Only one in-flight per day via seen set
 * - Best-effort; errors are swallowed
 */
export function useAutoRoute(dayId: string | null | undefined, hasStartEnd: boolean) {
  const seen = useRef<Set<string>>(new Set())

  useEffect(() => {
    if (!dayId || !hasStartEnd) return
    if (seen.current.has(dayId)) return
    ;(async () => {
      try {
        const routes = (await listSavedRoutes(dayId)).routes || []
        if (routes.length > 0) { seen.current.add(dayId); return }
        const preview = await computeDayRoute(dayId, { optimize: false })
        await commitDayRoute(dayId, preview.preview_token, 'Default')
      } catch {}
      finally {
        seen.current.add(dayId)
      }
    })()
  }, [dayId, hasStartEnd])
}

