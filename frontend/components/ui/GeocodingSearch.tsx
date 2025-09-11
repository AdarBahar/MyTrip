'use client'

/**
 * Free-Form Geocoding Search Component
 * 
 * Uses real MapTiler geocoding API for worldwide address search
 * with map integration to display results
 */

import React, { useState, useEffect, useRef, useCallback } from 'react'
import { Search, MapPin, Loader2, X, Globe, Navigation, Map } from 'lucide-react'
import { geocodeAddress, type GeocodingResult } from '@/lib/api/places'

// Types
interface GeocodingSearchProps {
  onLocationSelect?: (result: GeocodingResult) => void
  onCoordinatesSelect?: (lat: number, lng: number, result: GeocodingResult) => void
  placeholder?: string
  className?: string
  disabled?: boolean
  showMap?: boolean
  mapHeight?: number
  autoSearch?: boolean
  minSearchLength?: number
  debounceMs?: number
  maxResults?: number
  language?: string
  supportRTL?: boolean
}

// Detect if text contains Hebrew characters
const containsHebrew = (text: string): boolean => {
  return /[\u0590-\u05FF]/.test(text)
}

// Detect text direction
const getTextDirection = (text: string): 'ltr' | 'rtl' => {
  return containsHebrew(text) ? 'rtl' : 'ltr'
}

export default function GeocodingSearch({
  onLocationSelect,
  onCoordinatesSelect,
  placeholder = "Search for any address worldwide...",
  className = "",
  disabled = false,
  showMap = true,
  mapHeight = 300,
  autoSearch = true,
  minSearchLength = 3,
  debounceMs = 300,
  maxResults = 8,
  language = 'en',
  supportRTL = true
}: GeocodingSearchProps) {
  // State
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<GeocodingResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const [error, setError] = useState<string | null>(null)
  const [textDirection, setTextDirection] = useState<'ltr' | 'rtl'>('ltr')
  const [mounted, setMounted] = useState(false)
  const [selectedResult, setSelectedResult] = useState<GeocodingResult | null>(null)

  // Refs
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  // Handle mounting for hydration
  useEffect(() => {
    setMounted(true)
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current)
      }
    }
  }, [])

  // Debounced geocoding search
  const performGeocodingSearch = useCallback(async (searchQuery: string) => {
    if (searchQuery.length < minSearchLength) {
      setResults([])
      setIsOpen(false)
      return
    }

    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    setIsLoading(true)
    setError(null)

    try {
      const geocodingResults = await geocodeAddress(searchQuery)
      
      // Limit results
      const limitedResults = geocodingResults.slice(0, maxResults)
      
      setResults(limitedResults)
      setIsOpen(limitedResults.length > 0)
      
    } catch (err) {
      console.error('Geocoding search error:', err)
      setError(err instanceof Error ? err.message : 'Search failed')
      setResults([])
      setIsOpen(false)
    } finally {
      setIsLoading(false)
    }
  }, [minSearchLength, maxResults])

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setQuery(value)

    // Update text direction for RTL support
    if (supportRTL) {
      setTextDirection(getTextDirection(value))
    }

    // Clear previous debounce
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current)
    }

    if (autoSearch) {
      // Debounce search
      debounceTimeoutRef.current = setTimeout(() => {
        performGeocodingSearch(value)
      }, debounceMs)
    }
  }

  // Handle manual search (for non-auto search mode)
  const handleManualSearch = () => {
    if (query.trim()) {
      performGeocodingSearch(query.trim())
    }
  }

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || results.length === 0) {
      if (e.key === 'Enter' && !autoSearch) {
        handleManualSearch()
      }
      return
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex(prev => (prev + 1) % results.length)
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex(prev => prev <= 0 ? results.length - 1 : prev - 1)
        break
      case 'Enter':
        e.preventDefault()
        if (selectedIndex >= 0 && selectedIndex < results.length) {
          handleResultSelect(results[selectedIndex])
        }
        break
      case 'Escape':
        e.preventDefault()
        setIsOpen(false)
        setSelectedIndex(-1)
        break
    }
  }

  // Handle result selection
  const handleResultSelect = (result: GeocodingResult) => {
    console.log('GeocodingSearch: Result selected:', result.formatted_address || result.address)

    setSelectedResult(result)
    setQuery(result.formatted_address || result.address)
    setIsOpen(false)
    setSelectedIndex(-1)

    // Trigger callbacks
    if (onLocationSelect) {
      console.log('GeocodingSearch: Calling onLocationSelect callback')
      onLocationSelect(result)
    }
    if (onCoordinatesSelect) {
      console.log('GeocodingSearch: Calling onCoordinatesSelect callback')
      onCoordinatesSelect(result.lat, result.lon, result)
    }
  }

  // Clear search
  const clearSearch = () => {
    setQuery('')
    setResults([])
    setIsOpen(false)
    setSelectedIndex(-1)
    setError(null)
    setSelectedResult(null)
    inputRef.current?.focus()
  }

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node
      const isInsideInput = inputRef.current && inputRef.current.contains(target)
      const isInsideDropdown = dropdownRef.current && dropdownRef.current.contains(target)

      if (!isInsideInput && !isInsideDropdown) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div className={`relative ${className}`}>
      {/* Search Input */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Globe className="h-5 w-5 text-gray-400" />
        </div>
        
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => query.length >= minSearchLength && results.length > 0 && setIsOpen(true)}
          placeholder={placeholder}
          disabled={disabled}
          dir={mounted && supportRTL ? textDirection : 'ltr'}
          className={`
            w-full transition-all duration-200
            ${mounted && textDirection === 'rtl' ? 'pr-10 pl-10 text-right' : 'pl-10 pr-10 text-left'}
            py-3 px-4 text-base
            border border-gray-300 rounded-lg bg-white shadow-sm 
            focus:ring-2 focus:ring-blue-500 focus:border-blue-500
            ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:border-gray-400'}
            ${error ? 'border-red-500 focus:ring-red-500 focus:border-red-500' : ''}
          `}
        />

        {/* Right side icons */}
        <div className="absolute inset-y-0 right-0 pr-3 flex items-center" suppressHydrationWarning>
          {mounted && isLoading && (
            <Loader2 className="h-4 w-4 text-gray-400 animate-spin" />
          )}
          {mounted && !isLoading && query && (
            <button
              onClick={clearSearch}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              type="button"
            >
              <X className="h-4 w-4" />
            </button>
          )}
          {!autoSearch && !isLoading && (
            <button
              onClick={handleManualSearch}
              className="ml-2 text-blue-600 hover:text-blue-800 transition-colors"
              type="button"
            >
              <Search className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-2 text-sm text-red-600">
          {error}
        </div>
      )}

      {/* Search Results Dropdown */}
      {isOpen && results.length > 0 && (
        <div
          ref={dropdownRef}
          className="absolute top-full left-0 right-0 z-50 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-64 overflow-y-auto"
        >
          {results.map((result, index) => (
            <div
              key={`${result.lat}-${result.lon}-${index}`}
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                console.log('GeocodingSearch: Dropdown item clicked:', result.formatted_address || result.address)
                handleResultSelect(result)
              }}
              className={`
                flex items-start gap-3 p-3 cursor-pointer border-b last:border-b-0
                ${index === selectedIndex ? 'bg-blue-50' : 'hover:bg-gray-50'}
              `}
            >
              <MapPin className="h-4 w-4 text-gray-400 mt-1 flex-shrink-0" />
              
              <div className="flex-1 min-w-0">
                <div 
                  className="font-medium text-gray-900 truncate"
                  dir={mounted ? getTextDirection(result.formatted_address || result.address) : 'ltr'}
                >
                  {result.formatted_address || result.address}
                </div>
                
                <div className="text-sm text-gray-600 mt-1">
                  <span className="font-mono">
                    {result.lat.toFixed(6)}, {result.lon.toFixed(6)}
                  </span>
                  {result.types && result.types.length > 0 && (
                    <span className="ml-2 text-gray-500">
                      • {result.types.join(', ')}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Map Display */}
      {showMap && selectedResult && (
        <div className="mt-4 border border-gray-200 rounded-lg overflow-hidden">
          <div className="bg-gray-100 px-4 py-2 border-b border-gray-200">
            <div className="flex items-center gap-2">
              <Map className="h-4 w-4 text-gray-600" />
              <span className="text-sm font-medium text-gray-700">Selected Location</span>
            </div>
          </div>
          
          <div 
            className="bg-gray-200 flex items-center justify-center"
            style={{ height: mapHeight }}
          >
            <div className="text-center text-gray-600">
              <Navigation className="h-8 w-8 mx-auto mb-2" />
              <div className="text-sm font-medium">{selectedResult.formatted_address || selectedResult.address}</div>
              <div className="text-xs text-gray-500 mt-1">
                {selectedResult.lat.toFixed(6)}, {selectedResult.lon.toFixed(6)}
              </div>
              <div className="text-xs text-blue-600 mt-2">
                Map integration coming soon
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
