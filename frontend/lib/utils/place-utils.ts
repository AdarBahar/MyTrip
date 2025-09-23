/**
 * Place utility functions for handling different place data formats
 */

export interface PlaceCoordinates {
  lat: number;
  lng: number;
}

export interface PlaceDetails {
  id: string;
  name: string;
  formatted_address: string;
  types: string[];
  center: PlaceCoordinates;
  bbox?: {
    minLat: number;
    minLng: number;
    maxLat: number;
    maxLng: number;
  };
  categories: string[];
  score: number;
  timezone?: string;
  metadata?: {
    country?: string;
    postcode?: string;
  };
  phone?: string;
  website?: string;
  rating?: number;
  popularity?: number;
  address?: string;
  meta?: Record<string, any>;
}

export interface Place {
  id: string;
  name: string;
  address?: string;
  lat: number;
  lon: number;
  meta?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface PlaceCreateData {
  name: string;
  address?: string;
  lat: number;
  lon: number;
  meta?: Record<string, any>;
}

/**
 * Convert PlaceDetails or Place object to PlaceCreateData format
 * Handles both PlaceDetails (with center.lat/lng) and Place (with lat/lon) formats
 */
export function convertToPlaceCreateData(
  place: PlaceDetails | Place | any,
  source: string = 'unknown'
): PlaceCreateData {
  let placeData: PlaceCreateData;
  
  // Check if this is a PlaceDetails object (has center.lat/lng)
  if (place.center && typeof place.center.lat === 'number' && typeof place.center.lng === 'number') {
    // PlaceDetails format - extract coordinates from center
    placeData = {
      name: place.name,
      address: place.formatted_address || place.address,
      lat: place.center.lat,
      lon: place.center.lng,
      meta: { 
        source,
        types: place.types,
        place_id: place.id,
        categories: place.categories,
        score: place.score,
        ...place.meta 
      }
    };
  } else if (typeof place.lat === 'number' && typeof place.lon === 'number') {
    // Place format - use coordinates directly
    placeData = {
      name: place.name,
      address: place.address,
      lat: place.lat,
      lon: place.lon,
      meta: { source, ...place.meta }
    };
  } else {
    // Invalid format - throw error with details
    throw new Error(
      `Invalid place format: Expected coordinates in 'center.lat/lng' or 'lat/lon' format. ` +
      `Received: ${JSON.stringify({ 
        hasCenter: !!place.center, 
        centerLat: place.center?.lat, 
        centerLng: place.center?.lng,
        lat: place.lat, 
        lon: place.lon 
      })}`
    );
  }
  
  // Validate coordinates
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
  
  return placeData;
}

/**
 * Check if a place object has valid coordinates
 */
export function hasValidCoordinates(place: any): boolean {
  // Check PlaceDetails format (center.lat/lng)
  if (place.center && typeof place.center.lat === 'number' && typeof place.center.lng === 'number') {
    return !isNaN(place.center.lat) && !isNaN(place.center.lng) &&
           place.center.lat >= -90 && place.center.lat <= 90 &&
           place.center.lng >= -180 && place.center.lng <= 180;
  }
  
  // Check Place format (lat/lon)
  if (typeof place.lat === 'number' && typeof place.lon === 'number') {
    return !isNaN(place.lat) && !isNaN(place.lon) &&
           place.lat >= -90 && place.lat <= 90 &&
           place.lon >= -180 && place.lon <= 180;
  }
  
  return false;
}

/**
 * Get coordinates from a place object in a consistent format
 */
export function getPlaceCoordinates(place: any): { lat: number; lon: number } | null {
  // Check PlaceDetails format (center.lat/lng)
  if (place.center && typeof place.center.lat === 'number' && typeof place.center.lng === 'number') {
    return { lat: place.center.lat, lon: place.center.lng };
  }
  
  // Check Place format (lat/lon)
  if (typeof place.lat === 'number' && typeof place.lon === 'number') {
    return { lat: place.lat, lon: place.lon };
  }
  
  return null;
}

/**
 * Debug helper to log place object structure
 */
export function debugPlaceStructure(place: any, context: string = ''): void {
  console.log(`${context} Place structure:`, {
    id: place.id,
    name: place.name,
    hasCenter: !!place.center,
    centerLat: place.center?.lat,
    centerLng: place.center?.lng,
    lat: place.lat,
    lon: place.lon,
    address: place.address,
    formatted_address: place.formatted_address,
    types: place.types,
    meta: place.meta
  });
}
