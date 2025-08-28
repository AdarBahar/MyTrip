"use client";
import React, { useEffect, useRef, useState } from 'react'
import type { Place } from '@/lib/api/places'
import { MapPreview as InnerMap } from './map-preview'

export function LazyMapPreview(props: {
  start?: Place | null
  end?: Place | null
  waypoints?: Place[]
  routeCoordinates?: [number, number][] | null
  routes?: { id: string; coordinates: [number, number][], color?: string, width?: number, opacity?: number }[]
  highlightRouteId?: string | null
  height?: number
  className?: string
  interactive?: boolean
  extraMarkers?: { id: string; lat: number; lon: number; color?: string }[]
  overlayText?: string | null
}) {
  const [show, setShow] = useState(false)
  const ref = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const obs = new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (e.isIntersecting) {
          setShow(true)
          obs.disconnect()
          break
        }
      }
    }, { rootMargin: '200px' })
    obs.observe(el)
    return () => obs.disconnect()
  }, [])

  return (
    <div ref={ref} className={props.className} style={{ position: 'relative', height: props.height ?? 240 }}>
      {show ? (
        <InnerMap {...props} />
      ) : (
        <div style={{ position: 'absolute', inset: 0, background: '#f3f4f6' }} />
      )}
    </div>
  )
}

