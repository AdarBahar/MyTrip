"use client";

import React, { useEffect, useMemo, useState } from 'react';
import { Search, MapPin, Hotel, Utensils, Landmark } from 'lucide-react';
import { Place, searchPlaces, geocodeAddress, createPlace, getPlace } from '@/lib/api/places';
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
      const created = await createPlace({ name: picked.name || name, address: picked.address || name, lat: picked.lat, lon: picked.lon, meta: { source: 'inline-add' } });
      placeId = created.id;
    } catch (e) {
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
    onVisualsChange && onVisualsChange('', []);
    if (onAdded) await onAdded();
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <input
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

