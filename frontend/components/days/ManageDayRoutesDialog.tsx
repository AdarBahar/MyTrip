"use client";

import React, { useEffect, useMemo, useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { listSavedRoutes, activateRouteVersion, setPrimaryRouteVersion, computeDayRoute, commitDayRoute, type RouteVersion } from '@/lib/api/routing'
import { Input } from '@/components/ui/input'
import RenameRouteInline from './RenameRouteInline'
import { useToast } from '@/components/ui/use-toast'

export default function ManageDayRoutesDialog({ dayId, open, onOpenChange, onRoutesChanged }: { dayId: string, open: boolean, onOpenChange: (v: boolean) => void, onRoutesChanged?: (rv?: RouteVersion) => void | Promise<void> }) {
  const { toast } = useToast()
  const [routes, setRoutes] = useState<RouteVersion[]>([])
  const [loading, setLoading] = useState(false)
  const [computing, setComputing] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const res = await listSavedRoutes(dayId)
      setRoutes(res.routes || [])
    } catch (e: any) {
      toast({ title: 'Failed to load routes', description: e?.message || 'Please try again.', variant: 'destructive' })
    } finally { setLoading(false) }
  }

  useEffect(() => { if (open) load() }, [open])

  const onActivate = async (rv: RouteVersion) => {
    try {
      const updated = await activateRouteVersion(dayId, rv.id)
      toast({ title: 'Default route updated', description: updated.name || `Version ${updated.version}` })
      await load()
      if (onRoutesChanged) await onRoutesChanged(updated)
    } catch (e: any) {
      toast({ title: 'Failed to set default', description: e?.message || 'Please try again.', variant: 'destructive' })
    }
  }
  const onPrimary = async (rv: RouteVersion) => {
    try {
      const updated = await setPrimaryRouteVersion(dayId, rv.id)
      toast({ title: 'Primary route updated', description: updated.name || `Version ${updated.version}` })
      await load()
      if (onRoutesChanged) await onRoutesChanged(updated)
    } catch (e: any) {
      toast({ title: 'Failed to set primary', description: e?.message || 'Please try again.', variant: 'destructive' })
    }
  }

  const detectNewRoute = (before: RouteVersion[] = [], after: RouteVersion[] = []) => {
    const beforeIds = new Set(before.map(r => r.id))
    if (after.length > before.length) return true
    for (const r of after) { if (!beforeIds.has(r.id)) return true }
    const maxVBefore = Math.max(0, ...before.map(r => r.version || 0))
    const maxVAfter = Math.max(0, ...after.map(r => r.version || 0))
    return maxVAfter > maxVBefore
  }

  const onAddNew = async (opts: { avoidTolls?: boolean, avoidHighways?: boolean, name?: string }) => {
    setComputing(true)
    try {
      // Baseline list to detect saved route even if commit response cannot be read (CORS/glitch)
      let before: RouteVersion[] = []
      try { before = (await listSavedRoutes(dayId)).routes || [] } catch {}

      const { throttledComputeDayRoute } = await import('@/lib/api/routing')
      const preview = await throttledComputeDayRoute(dayId, { optimize: false, avoidTolls: opts.avoidTolls, avoidHighways: opts.avoidHighways })
      try {
        const { commitDayRouteWithFallback } = await import('@/lib/api/routing')
        const created: RouteVersion = await commitDayRouteWithFallback(dayId, preview.preview_token, opts.name, { optimize: false, avoidTolls: opts.avoidTolls, avoidHighways: opts.avoidHighways })
        toast({ title: 'New route saved', description: opts.name || 'Route version saved' })
        await load()
        if (onRoutesChanged) await onRoutesChanged(created)
      } catch (e: any) {
        // Fallback: if server saved but browser couldn't read response, confirm via list
        let after: RouteVersion[] = []
        try { after = (await listSavedRoutes(dayId)).routes || [] } catch {}
        const active = after.find(r => r.is_active) || after[0]
        if (detectNewRoute(before, after) && active) {
          toast({ title: 'New route saved', description: opts.name || 'Route version saved' })
          setRoutes(after)
          if (onRoutesChanged) await onRoutesChanged(active)
        } else {
          const status = e?.status || e?.response?.status
          const msg = status === 429 ? 'Rate-limited by routing provider. Please try again later.' : (e?.message || 'Please try again.')
          toast({ title: 'Failed to add route', description: msg, variant: 'destructive' })
        }
      }
    } finally { setComputing(false) }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Manage routes</DialogTitle>
            {computing && (
              <div className="text-xs text-blue-600">Computing route…</div>
            )}

        </DialogHeader>
        <div className="space-y-3">
          {loading ? (
            <div className="text-sm text-gray-500">Loading routes…</div>
          ) : routes.length === 0 ? (
            <div className="text-sm text-gray-500">No saved routes yet.</div>
          ) : (
            <ul className="divide-y">
              {routes.map(r => (
                <React.Fragment key={r.id}>
                  <li className="py-2 flex items-center justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm truncate">{r.name || `Version ${r.version}`}</span>
                        {r.is_active && <Badge variant="outline" className="text-[10px]">Default</Badge>}
                        {r.is_primary && <Badge variant="outline" className="text-[10px]">Primary</Badge>}
                      </div>
                      <div className="text-xs text-gray-600">
                        {r.total_km ? `${Math.round(r.total_km)} km` : ''} {r.total_min ? `• ${Math.round(r.total_min)} min` : ''}
                        {r.totals?.options && (
                          <span className="ml-2 text-gray-500">{r.totals.options.avoid_tolls ? 'No-tolls' : 'Tolls ok'}{r.totals.options.avoid_highways ? ' • Avoid highways' : ''}</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {!r.is_active && (
                        <Button variant="secondary" size="sm" onClick={() => onActivate(r)}>Set default</Button>
                      )}
                      {!r.is_primary && (
                        <Button variant="outline" size="sm" onClick={() => onPrimary(r)}>Mark primary</Button>
                      )}
                    </div>
                  </li>
                  <li className="pb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500">Rename:</span>
                      <RenameRouteInline dayId={dayId} routeId={r.id} currentName={r.name || ''} onRenamed={load} />
                    </div>
                  </li>
                </React.Fragment>
              ))}
            </ul>
          )}

          <div className="border-t pt-3 space-y-2">
            <div className="text-sm font-medium">Add new route</div>
            <div className="flex items-center gap-2">
              <Button disabled={computing} onClick={() => onAddNew({ avoidTolls: false, avoidHighways: false, name: 'Default' })}>Default</Button>
              <Button variant="secondary" disabled={computing} onClick={() => onAddNew({ avoidTolls: true, name: 'No tolls' })}>No tolls</Button>
              <Button variant="secondary" disabled={computing} onClick={() => onAddNew({ avoidHighways: true, name: 'Avoid highways' })}>Avoid highways</Button>
            </div>
            <div className="text-[11px] text-gray-500">Routes are saved and won’t recompute unless you add a new one or change default.</div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

