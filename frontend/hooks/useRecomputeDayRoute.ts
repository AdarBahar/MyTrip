import { useCallback, useEffect } from 'react'
import { computeDayRoute } from '@/lib/api/routing'
import { useToast } from '@/components/ui/use-toast'

export function useRecomputeDayRoute(onSuccess: (dayId: string, preview: any) => void) {
  const { toast } = useToast()

  useEffect(() => {
    const handler = async (evt: any) => {
      const dayId = evt?.detail?.dayId
      if (!dayId) return
      try {
        const preview = await computeDayRoute(dayId, { optimize: false })
        onSuccess(dayId, preview)
        toast({ title: 'Route updated', description: 'Preview route has been recomputed.' })
      } catch (e: any) {
        if (e?.status === 429) {
          toast({ title: 'Routing temporarily unavailable', description: 'Rate-limited by routing provider. Please try again in about a minute.', variant: 'destructive' })
        } else {
          toast({ title: 'Failed to recompute route', description: 'Please try again later.', variant: 'destructive' })
        }
      }
    }
    window.addEventListener('recompute-day-route', handler)
    return () => window.removeEventListener('recompute-day-route', handler)
  }, [onSuccess, toast])
}

