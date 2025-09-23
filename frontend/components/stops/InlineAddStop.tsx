"use client";

import React, { useEffect, useMemo, useState } from 'react';
import { Search, MapPin, Hotel, Utensils, Landmark } from 'lucide-react';
import { Place, searchPlaces, geocodeAddress, createPlace, getPlace } from '@/lib/api/places';
import { convertToPlaceCreateData, debugPlaceStructure } from '@/lib/utils/place-utils';
import { createStop, listStops, getNextSequenceNumber, type StopWithPlace } from '@/lib/api/stops';
import { Button } from '@/components/ui/button';

interface InlineAddStopProps {
  tripId: string;
  dayId: string;
  dayCenter?: { lat: number; lon: number } | null; // use to scope search
  onAdded?: () => Promise<void> | void;
  onCancel?: () => void;
  onVisualsChange?: (query: string, markers: { id: string; lat: number; lon: number }[]) => void;
}

export default function InlineAddStop({ tripId, dayId, dayCenter, onAdded, onCancel, onVisualsChange }: InlineAddStopProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Place[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [picked, setPicked] = useState<Place | null>(null);
  const [customName, setCustomName] = useState('');

  useEffect(() => { setResults([]); setPicked(null); setCustomName(''); setError(null); onVisualsChange && onVisualsChange('', []); }, [dayId]);

  const runSearch = async () => {
    try {
      setLoading(true); setError(null);
      const params: any = { query: query.trim(), limit: 8 };
      if (dayCenter) { params.lat = dayCenter.lat; params.lon = dayCenter.lon; params.radius = 20000; }
      // If looks like address (has digits or comma), first try geocoding and merge
      const items: Place[] = [];
      if (/\d|,/.test(params.query)) {
        try {
          const geos = await geocodeAddress(params.query);
          items.push(...geos.map(g => ({ id: g.place_id || `${g.lat},${g.lon}`, name: g.formatted_address, address: g.address || g.formatted_address, lat: g.lat, lon: g.lon, created_at: '', updated_at: '' })));
        } catch {}
      }
      const found = await searchPlaces(params);
      items.push(...found.places);
      // de-dupe by id or lat/lon
      const key = (p: Place) => `${p.id}|${p.lat.toFixed(5)},${p.lon.toFixed(5)}`;
      const uniq = Array.from(new Map(items.map(p => [key(p), p])).values());
      setResults(uniq);
      onVisualsChange && onVisualsChange(query, uniq.map(p => ({ id: p.id, lat: p.lat, lon: p.lon })));
    } catch (e: any) {
      setError(e?.message || 'Search failed');
    } finally { setLoading(false); }
  };

  const addPicked = async () => {
    if (!picked) return;
    // Make sure we have a name (custom up to 50 chars) - fall back to place name
    const name = (customName || picked.name || 'New Stop').slice(0, 50);
    const existing = await listStops(tripId, dayId);
    const seq = getNextSequenceNumber(existing.stops as any);

    // Ensure place exists in backend; prefer creating to avoid 404 noise for external IDs
    let placeId = picked.id;
    try {
      // Debug: Log the original place structure
      debugPlaceStructure(picked, 'InlineAddStop: Original place');

      // Convert place to create format with validation
      const placeData = convertToPlaceCreateData(picked, 'inline_add');

      // Override name if custom name provided
      if (customName) {
        placeData.name = customName;
      }

      // Debug: Log the converted place data
      console.log('InlineAddStop: Creating place with data:', placeData);

      const created = await createPlace(placeData);
      placeId = created.id;
    } catch (e) {
      console.error('InlineAddStop: Failed to create place:', e);
      // If create fails (e.g., duplicate constraints), last attempt: keep original id
    }

    try {
      await createStop(tripId, dayId, { place_id: placeId, kind: 'via', seq, fixed: false, notes: '', priority: 2 });
    } catch (e: any) {
      // Retry once with next available seq (handles rare sequence conflicts)
      try {
        const latest = await listStops(tripId, dayId);
        const nextSeq = getNextSequenceNumber(latest.stops as any);
        if (nextSeq !== seq) {
          await createStop(tripId, dayId, { place_id: placeId, kind: 'via', seq: nextSeq, fixed: false, notes: '', priority: 2 });
        } else {
          throw e;
        }
      } catch (e2: any) {
        setError(e2?.message || 'Failed to create stop');
        return;
      }
    }

    // Immediately recompute+commit so maps and totals reflect the new stop
    try {
      const { throttledComputeDayRoute, commitDayRouteWithFallback, getDayActiveSummary } = await import('@/lib/api/routing')
      const preview = await throttledComputeDayRoute(dayId, { optimize: true })
      await commitDayRouteWithFallback(dayId, preview.preview_token, 'Default', { optimize: false })
      // Broadcast updated summary
      try {
        const s = await getDayActiveSummary(dayId)
        const loc = {
          start: s.start || null,
          end: s.end || null,
          route_total_km: s.route_total_km ?? undefined,
          route_total_min: s.route_total_min ?? undefined,
          route_coordinates: s.route_coordinates ?? undefined,
        }
        window.dispatchEvent(new CustomEvent('day-summary-updated', { detail: { dayId, loc } }))
      } catch {}
    } catch (e: any) {
      // Log routing errors instead of silently swallowing them
      console.error('Auto-route computation failed after adding stop:', e);

      // Show user feedback for routing failures
      if (e?.status === 429) {
        // Rate limit errors are already handled by the routing API
        console.warn('Routing rate limited after adding stop');
      } else {
        console.warn('Route computation failed after adding stop, user can manually recompute');
      }
    }

    onVisualsChange && onVisualsChange('', []);
    try { window.dispatchEvent(new CustomEvent('stops-mutated', { detail: { dayId } })) } catch {}
    if (onAdded) await onAdded();
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <input
            id="stop-search-input"
            name="stop-search"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') runSearch(); }}
            placeholder="Search hotel, restaurant, address..."
            className="w-full border rounded-md px-3 py-2 pr-8 text-sm"
          />
          <Search className="w-4 h-4 text-gray-400 absolute right-2 top-2.5" />
        </div>
        <Button variant="secondary" disabled={loading || !query.trim()} onClick={runSearch}>
          Search
        </Button>
        {onCancel && (
          <Button variant="ghost" onClick={onCancel} className="text-xs">Cancel</Button>
        )}
      </div>

      {error && <div className="text-xs text-red-600">{error}</div>}

      {picked && (
        <div className="flex items-center gap-2">
          <input
            id="stop-custom-name"
            name="stop-custom-name"
            value={customName}
            onChange={e => setCustomName(e.target.value.slice(0, 50))}
            placeholder="Add a custom name (optional, 50 chars)"
            className="flex-1 border rounded-md px-2 py-1 text-xs"
          />
          <Button onClick={addPicked} disabled={loading} className="text-xs">Add stop</Button>
        </div>
      )}

      <div className="grid grid-cols-1 gap-2">
        {loading ? (
          <div className="text-xs text-gray-500">Searching...</div>
        ) : results.length > 0 ? (
          results.map(r => (
            <button key={`${r.id}-${r.lat}-${r.lon}`} onClick={() => setPicked(r)} className={`text-left border rounded-md px-3 py-2 hover:bg-gray-50 ${picked?.id === r.id ? 'ring-2 ring-blue-500' : ''}`}>
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-gray-500" />
                <div className="min-w-0">
                  <div className="font-medium text-sm truncate">{r.name || 'Unnamed'}</div>
                  <div className="text-xs text-gray-600 truncate">{r.address}</div>
                </div>
              </div>
            </button>
          ))
        ) : query.trim() ? (
          <div className="text-xs text-gray-500">No results.</div>
        ) : null}
      </div>
    </div>
  );
}

