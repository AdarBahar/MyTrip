/**
 * Location Picker Component
 * Search and select places for trip locations
 */

'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Search, MapPin, Loader2, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { searchPlaces, geocodeAddress, type Place, type PlaceSearchItem, type GeocodingResult, formatShortAddress } from '@/lib/api/places';

interface LocationPickerProps {
  value?: Place | null;
  onChange: (place: Place | null) => void;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

export function LocationPicker({ 
  value, 
  onChange, 
  placeholder = "Search for a location...",
  className = "",
  disabled = false 
}: LocationPickerProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<(PlaceSearchItem | GeocodingResult)[]>([]);
  const [loading, setLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [allowShow, setAllowShow] = useState(true);
  const rootRef = useRef<HTMLDivElement>(null);
  const blurTimeoutRef = useRef<number | null>(null);

  // Close suggestions when clicking outside this component
  useEffect(() => {
    const onDocMouseDown = (e: MouseEvent) => {
      if (!rootRef.current) return;
      if (!rootRef.current.contains(e.target as Node)) {
        setShowResults(false);
      }
    };
    document.addEventListener('mousedown', onDocMouseDown);
    return () => document.removeEventListener('mousedown', onDocMouseDown);
  }, []);

  // Update query when value changes externally
  useEffect(() => {
    if (value) {
      setQuery(value.name || value.address || '');
    } else {
      setQuery('');
    }
  }, [value]);

  const searchLocations = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim() || searchQuery.length < 3) {
      setResults([]);
      setShowResults(false);
      return;
    }

    setLoading(true);
    try {
      // Try places search first
      const placesResponse = await searchPlaces({ 
        query: searchQuery,
        limit: 5 
      });
      
      // Try geocoding as backup
      const geocodeResponse = await geocodeAddress(searchQuery);
      
      // Combine results, prioritizing places
      const combinedResults = [
        ...(placesResponse.places || []),
        ...(geocodeResponse || []).slice(0, 3) // Limit geocoding results
      ];

      setResults(combinedResults);
      if (allowShow) {
        setShowResults(true);
      }
    } catch (error) {
      console.error('Location search error:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [allowShow]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      searchLocations(query);
    }, 300);

    return () => clearTimeout(timer);
  }, [query, searchLocations]);

  const handleSelect = (item: Place | GeocodingResult) => {
    // Convert GeocodingResult to Place format if needed
    const place: Place = 'id' in item ? item : {
      id: `geocode_${Date.now()}`, // Temporary ID for geocoded results
      name: item.display_name || item.address || 'Unknown Location',
      address: item.address || item.display_name || '',
      lat: item.lat,
      lon: item.lon,
      meta: { source: 'geocoding', ...item },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    onChange(place);
    setQuery(place.name || place.address);
    setAllowShow(false);
    setResults([]);
    setShowResults(false);
  };

  const handleClear = () => {
    onChange(null);
    setQuery('');
    setResults([]);
    setShowResults(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newQuery = e.target.value;
    setQuery(newQuery);
    setAllowShow(true);

    if (!newQuery.trim()) {
      onChange(null);
      setResults([]);
      setShowResults(false);
    }
  };

  return (
    <div ref={rootRef} className={`relative ${className}`}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
        <Input
          value={query}
          onChange={handleInputChange}
          placeholder={placeholder}
          disabled={disabled}
          className="pl-10 pr-10"
          onKeyDown={(e) => { if (e.key === 'Escape') setShowResults(false); }}
          onFocus={() => {
            // Cancel any pending blur-close and reopen only if allowed
            if (blurTimeoutRef.current) { window.clearTimeout(blurTimeoutRef.current); blurTimeoutRef.current = null; }
            if (allowShow && results.length > 0) {
              setShowResults(true);
            }
          }}
          onBlur={() => {
            // Close shortly after blur to allow suggestion clicks to fire first
            if (blurTimeoutRef.current) window.clearTimeout(blurTimeoutRef.current);
            blurTimeoutRef.current = window.setTimeout(() => {
              setShowResults(false);
            }, 150);
          }}
        />
        {loading && (
          <Loader2 className="absolute right-8 top-1/2 transform -translate-y-1/2 h-4 w-4 animate-spin text-gray-400" />
        )}
        {value && !disabled && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClear}
            className="absolute right-1 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0 hover:bg-gray-100"
          >
            <X className="h-3 w-3" />
          </Button>
        )}
      </div>

      {/* Search Results */}
      {showResults && results.length > 0 && (
        <Card className="absolute top-full left-0 right-0 z-50 mt-1 max-h-64 overflow-y-auto">
          <CardContent className="p-0">
            {results.map((item, index) => {
              const isPlace = 'id' in item;
              const name = isPlace ? item.name : (item.display_name || item.address);
              const address = isPlace ? item.address : item.address;
              
              return (
                <div
                  key={isPlace ? item.id : `geocode_${index}`}
                  onMouseDown={() => handleSelect(item)}
                  className="flex items-start space-x-3 p-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0"
                >
                  <MapPin className="h-4 w-4 text-gray-400 mt-1 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {name}
                    </p>
                    {address && address !== name && (
                      <p className="text-xs text-gray-500 truncate">
                        {('meta' in item && (item as any).meta?.normalized?.display_short) || formatShortAddress(address, { showCountry: true })}
                      </p>
                    )}
                    <div className="flex items-center space-x-2 mt-1">
                      <Badge variant="outline" className="text-xs">
                        {isPlace ? (item.is_saved ? 'Saved Place' : 'Place') : 'Map Result'}
                      </Badge>
                      <span className="text-xs text-gray-400">
                        {item.lat.toFixed(4)}, {item.lon.toFixed(4)}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}

      {/* No Results */}
      {showResults && results.length === 0 && query.length >= 3 && !loading && (
        <Card className="absolute top-full left-0 right-0 z-50 mt-1">
          <CardContent className="p-4 text-center text-gray-500">
            <MapPin className="h-8 w-8 mx-auto mb-2 text-gray-300" />
            <p className="text-sm">No locations found</p>
            <p className="text-xs text-gray-400 mt-1">
              Try a different search term
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
