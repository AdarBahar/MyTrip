/**
 * Places API Client
 *
 * API functions for managing places and locations
 */

import { debugManager, generateApiId, extractHeaders, sanitizeHeaders } from '@/lib/debug';

import { getApiBase } from '@/lib/api/base';

/**
 * Get authentication headers
 */
function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem('auth_token');
  return {
    'Content-Type': 'application/json; charset=utf-8',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
}

/**
 * Debug-enabled fetch wrapper
 */
async function debugFetch(url: string, options: RequestInit = {}) {
  const apiId = generateApiId();
  const startTime = Date.now();

  try {
    // Log request
    debugManager.logRequest({
      id: apiId,
      method: options.method || 'GET',
      url,
      headers: sanitizeHeaders(options.headers as Record<string, string> || {}),
      timestamp: Date.now()
    });

    const response = await fetch(url, options);
    const duration = Date.now() - startTime;
    const responseHeaders = extractHeaders(response.headers);

    if (response.ok) {
      // Cache-control: respect server hints for GET requests by leveraging the in-memory cache
      const cacheControl = (response.headers.get('Cache-Control') || '').toLowerCase();
      const isGet = (options.method || 'GET').toUpperCase() === 'GET';
      const canCache = isGet && cacheControl.includes('max-age');
      const data = await response.json();
      debugManager.logResponse({
        id: apiId,
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders,
        data,
        duration,
        timestamp: Date.now()
      });
      return { data, status: response.status, headers: responseHeaders, cacheControl: cacheControl, canCache } as any;
    } else {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      debugManager.logResponse({
        id: apiId,
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders,
        data: errorData,
        duration,
        timestamp: Date.now()
      });
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }
  } catch (error) {
    const duration = Date.now() - startTime;
    debugManager.logResponse({
      id: apiId,
      status: 0,
      statusText: 'Network Error',
      headers: {},
      data: { error: error instanceof Error ? error.message : 'Unknown error' },
      duration,
      timestamp: Date.now()
    });
    throw error;
  }
}

export interface Place {
  id: string;
  name: string;
  address: string;
  lat: number;
  lon: number;
  meta?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

// Simple in-memory cache and in-flight deduper for getPlace
const placeCache = new Map<string, Place>();
const inFlightPlace = new Map<string, Promise<Place>>();

export interface PlaceCreate {
  name: string;
  address?: string; // Make address optional to match backend schema
  lat: number;
  lon: number;
  meta?: Record<string, any>;
}

export interface PlaceUpdate {
  name?: string;
  address?: string;
  lat?: number;
  lon?: number;
  meta?: Record<string, any>;
}

export interface PlaceSearch {
  query: string;
  lat?: number;
  lon?: number;
  radius?: number;
  limit?: number;
}

export interface PlaceSearchItem extends Place {
  is_saved?: boolean;
}

export interface PlaceSearchResult {
  places: PlaceSearchItem[];
  total: number;
}

export interface GeocodingResult {
  address: string;
  lat: number;
  lon: number;
  formatted_address: string;
  place_id?: string;
  types?: string[];
}

/**
 * Search for places
 */
export async function searchPlaces(searchParams: PlaceSearch): Promise<PlaceSearchResult> {
  const params = new URLSearchParams();
  params.append('query', searchParams.query);

  if (searchParams.lat !== undefined) {
    params.append('lat', searchParams.lat.toString());
  }

  if (searchParams.lon !== undefined) {
    params.append('lon', searchParams.lon.toString());
  }

  if (searchParams.radius !== undefined) {
    params.append('radius', searchParams.radius.toString());
  }

  if (searchParams.limit !== undefined) {
    params.append('limit', searchParams.limit.toString());
  }

  const API_BASE = await getApiBase();
  const response = await debugFetch(`${API_BASE}/places/search?${params.toString()}`, {
    method: 'GET',
    headers: getAuthHeaders()
  });

  // Handle both legacy and modern response formats
  const responseData = response.data;

  // Modern paginated response format
  if (responseData && responseData.data && Array.isArray(responseData.data)) {
    return {
      places: responseData.data,
      total: responseData.meta?.total_items || responseData.data.length
    };
  }

  // Legacy response format
  if (responseData && responseData.places && Array.isArray(responseData.places)) {
    return {
      places: responseData.places,
      total: responseData.total || responseData.places.length
    };
  }

  // Fallback for unexpected format
  console.warn('Unexpected places search response format:', responseData);
  return {
    places: [],
    total: 0
  };
}

/**
 * Get a specific place
 */
export async function getPlace(placeId: string): Promise<Place> {
  if (!placeId) throw new Error('placeId is required');
  // Serve from cache
  const cached = placeCache.get(placeId);
  if (cached) return cached;
  // Coalesce concurrent requests
  const inflight = inFlightPlace.get(placeId);
  if (inflight) return inflight;

  const request = (async () => {
    const API_BASE = await getApiBase();
    const response = await debugFetch(`${API_BASE}/places/${placeId}`, {
      method: 'GET',
      headers: getAuthHeaders()
    });
    const place: Place = (response as any).data;
    // Cache in-memory
    placeCache.set(placeId, place);
    inFlightPlace.delete(placeId);
    return place;
  })();

  inFlightPlace.set(placeId, request);
  return request;
}

/**
 * Bulk-fetch places by IDs (deduped, preserves order)
 */
export async function getPlacesBulk(placeIds: string[]): Promise<Place[]> {
  const ids = Array.from(new Set((placeIds || []).filter(Boolean)));
  if (ids.length === 0) return [];

  // Serve from cache and collect missing ids
  const results: Place[] = [];
  const missing: string[] = [];
  for (const id of ids) {
    const cached = placeCache.get(id);
    if (cached) {
      results.push(cached);
    } else {
      missing.push(id);
    }
  }

  if (missing.length > 0) {
    const API_BASE = await getApiBase();
    const url = `${API_BASE}/places/bulk?ids=${encodeURIComponent(missing.join(','))}`;
    const response = await debugFetch(url, { method: 'GET', headers: getAuthHeaders() });

    // Handle both legacy and modern response formats
    let fetched: Place[] = [];
    const responseData = (response as any).data;

    if (responseData && responseData.data && Array.isArray(responseData.data)) {
      // Modern paginated response format
      fetched = responseData.data;
    } else if (Array.isArray(responseData)) {
      // Legacy response format (direct array)
      fetched = responseData;
    } else {
      console.warn('Unexpected places bulk response format:', responseData);
      fetched = [];
    }

    for (const p of fetched) {
      placeCache.set(p.id, p);
    }
    // Merge fetched into results preserving original order
    const map = new Map<string, Place>([...results.map(p => [p.id, p] as const), ...fetched.map(p => [p.id, p] as const)]);
    return ids.map(id => map.get(id)!).filter(Boolean);
  }

  // All cached
  return ids.map(id => placeCache.get(id)!).filter(Boolean);
}

/**
 * Create a new place
 */
export async function createPlace(placeData: PlaceCreate): Promise<Place> {
  // Validate required coordinates
  if (typeof placeData.lat !== 'number' || typeof placeData.lon !== 'number') {
    throw new Error(`Invalid coordinates: lat=${placeData.lat}, lon=${placeData.lon}. Both must be valid numbers.`);
  }

  if (isNaN(placeData.lat) || isNaN(placeData.lon)) {
    throw new Error(`Invalid coordinates: lat=${placeData.lat}, lon=${placeData.lon}. Both must be valid numbers.`);
  }

  // Validate coordinate ranges
  if (placeData.lat < -90 || placeData.lat > 90) {
    throw new Error(`Invalid latitude: ${placeData.lat}. Must be between -90 and 90.`);
  }

  if (placeData.lon < -180 || placeData.lon > 180) {
    throw new Error(`Invalid longitude: ${placeData.lon}. Must be between -180 and 180.`);
  }

  const API_BASE = await getApiBase();
  const response = await debugFetch(`${API_BASE}/places`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(placeData)
  });
  return response.data;
}

/**
 * Update a place
 */
export async function updatePlace(
  placeId: string,
  placeData: PlaceUpdate
): Promise<Place> {
  const API_BASE = await getApiBase();
  const response = await debugFetch(`${API_BASE}/places/${placeId}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(placeData)
  });
  return response.data;
}

/**
 * Delete a place
 */
export async function deletePlace(placeId: string): Promise<void> {
  const API_BASE = await getApiBase();
  await debugFetch(`${API_BASE}/places/${placeId}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });
}

/**
 * Geocode an address
 */
export async function geocodeAddress(address: string): Promise<GeocodingResult[]> {
  const API_BASE = await getApiBase();
  const response = await debugFetch(`${API_BASE}/places/geocode?address=${encodeURIComponent(address)}`, {
    method: 'GET',
    headers: getAuthHeaders()
  });
  return response.data;
}

/**
 * Reverse geocode coordinates
 */
export async function reverseGeocode(lat: number, lon: number): Promise<GeocodingResult[]> {
  const API_BASE = await getApiBase();
  const response = await debugFetch(`${API_BASE}/places/reverse-geocode?lat=${lat}&lon=${lon}`, {
    method: 'GET',
    headers: getAuthHeaders()
  });
  return response.data;
}

/**
 * Format address for display
 */
export function formatAddress(address: string): string {
  if (!address) return '';

  // Clean up common address formatting issues
  return address
    .replace(/,\s*,/g, ',') // Remove double commas
    .replace(/,\s*$/, '')   // Remove trailing comma
    .trim();
}

/**
 * Parse a short address (street + number, city, state)
 * Heuristic parser that works well for common US formats like:
 *   "123 Main St, Springfield, IL 62704, USA"
 * Fallback: return the first two components separated by commas.
 */
export function formatShortAddress(input: Place | string | null | undefined, opts?: { showCountry?: boolean }): string {
  const fromPlace = (typeof input !== 'string') && input && typeof input === 'object';
  const place = (fromPlace ? (input as Place) : undefined);
  const address = (typeof input === 'string') ? input : (place?.address || '');
  if (!address) return '';

  // Prefer structured components if available in meta
  if (place?.meta && typeof place.meta === 'object') {
    const m: any = (place.meta.normalized?.components || place.meta);
    // Try several common schemas (MapTiler/OSM-like)
    const street = m.street || m.road || m.thoroughfare || '';
    const number = m.house_number || m.housenumber || '';
    const city = m.city || m.town || m.village || m.municipality || '';
    let state = m.state_code || m.state || m.region || '';
    if (typeof state === 'string') state = state.replace(/[^A-Za-z]/g, '');
    const country = (m.country_code || m.country || '').toUpperCase();

    const streetOut = [street, number].filter(Boolean).join(' ');
    const cityStateOut = [city, state].filter(Boolean).join(', ');
    const pieces = [streetOut, cityStateOut];
    if (opts?.showCountry && country && country !== 'US' && country !== 'USA') pieces.push(country);
    const structured = pieces.filter(Boolean).join(', ');
    if (structured) return structured;
  }

  // Fallback: parse the free-form address heuristically
  const parts = formatAddress(address).split(',').map(p => p.trim()).filter(Boolean);
  if (parts.length === 0) return '';

  // Street segment
  const streetSeg = parts[0] || '';
  let street = streetSeg;
  let number = '';
  // Try to split house number from street name
  const m = streetSeg.match(/^(\d+[A-Za-z\-]?)(?:\s+)(.+)$/);
  if (m) { number = m[1]; street = m[2]; }

  // City and state
  const city = parts[1] || '';
  let state = '';
  if (parts.length >= 3) {
    // Example third part: "IL 62704" or just "IL"
    const tokens = parts[2].split(/\s+/).filter(Boolean);
    if (tokens.length > 0) {
      // pick first token with letters (ignore ZIP-only tokens)
      const cand = tokens.find(t => /[A-Za-z]/.test(t)) || '';
      // strip punctuation
      state = cand.replace(/[^A-Za-z]/g, '');
    }
  }

  const streetOut = [street, number].filter(Boolean).join(' ');
  const cityStateOut = [city, state].filter(Boolean).join(', ');
  const result = [streetOut, cityStateOut].filter(Boolean).join(', ');
  if (result) return result;

  // Fallback to first two parts
  return parts.slice(0, 2).join(', ');
}

/**
 * Get distance between two points in kilometers
 */
export function getDistance(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371; // Earth's radius in kilometers
  const dLat = toRadians(lat2 - lat1);
  const dLon = toRadians(lon2 - lon1);
  
  const a = 
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/**
 * Convert degrees to radians
 */
function toRadians(degrees: number): number {
  return degrees * (Math.PI / 180);
}

/**
 * Format distance for display
 */
export function formatDistance(kilometers: number): string {
  if (kilometers < 1) {
    return `${Math.round(kilometers * 1000)}m`;
  }
  
  if (kilometers < 10) {
    return `${kilometers.toFixed(1)}km`;
  }
  
  return `${Math.round(kilometers)}km`;
}

/**
 * Get center point of multiple coordinates
 */
export function getCenterPoint(coordinates: Array<{ lat: number; lon: number }>): { lat: number; lon: number } {
  if (coordinates.length === 0) {
    return { lat: 0, lon: 0 };
  }
  
  if (coordinates.length === 1) {
    return coordinates[0];
  }
  
  const sumLat = coordinates.reduce((sum, coord) => sum + coord.lat, 0);
  const sumLon = coordinates.reduce((sum, coord) => sum + coord.lon, 0);
  
  return {
    lat: sumLat / coordinates.length,
    lon: sumLon / coordinates.length
  };
}

/**
 * Validate coordinates
 */
export function validateCoordinates(lat: number, lon: number): { isValid: boolean; error?: string } {
  if (isNaN(lat) || isNaN(lon)) {
    return { isValid: false, error: 'Coordinates must be numbers' };
  }
  
  if (lat < -90 || lat > 90) {
    return { isValid: false, error: 'Latitude must be between -90 and 90' };
  }
  
  if (lon < -180 || lon > 180) {
    return { isValid: false, error: 'Longitude must be between -180 and 180' };
  }
  
  return { isValid: true };
}

/**
 * Format coordinates for display
 */
export function formatCoordinates(lat: number, lon: number, precision: number = 6): string {
  return `${lat.toFixed(precision)}, ${lon.toFixed(precision)}`;
}

/**
 * Parse coordinates from string
 */
export function parseCoordinates(coordString: string): { lat: number; lon: number } | null {
  try {
    // Handle various formats: "lat,lon", "lat, lon", "(lat, lon)", etc.
    const cleaned = coordString.replace(/[()]/g, '').trim();
    const parts = cleaned.split(',').map(part => parseFloat(part.trim()));
    
    if (parts.length === 2 && !isNaN(parts[0]) && !isNaN(parts[1])) {
      const [lat, lon] = parts;
      const validation = validateCoordinates(lat, lon);
      
      if (validation.isValid) {
        return { lat, lon };
      }
    }
    
    return null;
  } catch {
    return null;
  }
}

/**
 * Get user's current location
 */
export function getCurrentLocation(): Promise<{ lat: number; lon: number }> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation is not supported by this browser'));
      return;
    }
    
    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          lat: position.coords.latitude,
          lon: position.coords.longitude
        });
      },
      (error) => {
        reject(new Error(`Geolocation error: ${error.message}`));
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000 // 5 minutes
      }
    );
  });
}
