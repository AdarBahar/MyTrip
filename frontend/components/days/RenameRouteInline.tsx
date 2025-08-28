"use client";

import React, { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/use-toast'

export default function RenameRouteInline({ dayId, routeId, currentName, onRenamed }: { dayId: string, routeId: string, currentName: string, onRenamed: () => Promise<void> | void }) {
  const [name, setName] = useState(currentName)
  const [saving, setSaving] = useState(false)
  const { toast } = useToast()

  const save = async () => {
    setSaving(true)
    try {
      const base = (await import('@/lib/api/base')).getApiBase
      const getApiBase = await base()
      const resp = await fetch(`${getApiBase}/routing/days/${dayId}/routes/${routeId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', ...(typeof window !== 'undefined' && localStorage.getItem('auth_token') ? { Authorization: `Bearer ${localStorage.getItem('auth_token')}` } : {}) },
        body: JSON.stringify({ name: name.trim() || null })
      })
      if (!resp.ok) throw new Error(`Failed: ${resp.status}`)
      toast({ title: 'Renamed', description: 'Route name updated.' })
      await onRenamed()
    } catch (e: any) {
      toast({ title: 'Rename failed', description: e?.message || 'Please try again.', variant: 'destructive' })
    } finally { setSaving(false) }
  }

  return (
    <div className="flex items-center gap-2">
      <Input className="h-7 w-48" value={name} onChange={e => setName(e.target.value)} placeholder="Route name" />
      <Button size="sm" variant="outline" onClick={save} disabled={saving || name.trim() === currentName.trim()}>Save</Button>
    </div>
  )
}

