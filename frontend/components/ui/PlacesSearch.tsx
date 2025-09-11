'use client'

/**
 * Places Search Component
 * 
 * A reusable search UI component that integrates with the Places API
 * for type-ahead suggestions and place selection.
 */

import React, { useState, useEffect, useRef, useCallback } from 'react'
import { Search, MapPin, Loader2, X, Building, Utensils, Camera, Home, ShoppingBag, Car, Heart, TreePine, Palette, Moon, MoreHorizontal } from 'lucide-react'
import { geocodeAddress, type GeocodingResult } from '@/lib/api/places'

// Types
interface PlaceCoordinates {
  lat: number
  lng: number
}

interface PlaceSuggestion {
  id: string
  name: string
  highlighted: string
  formatted_address: string
  types: string[]
  center: PlaceCoordinates
  distance_m?: number
  confidence: number
  source: string
  categories?: string[]
  score?: number
  distance?: number
  _geocodingResult?: GeocodingResult
}

interface PlaceDetails {
  id: string
  name: string
  formatted_address: string
  types: string[]
  center: PlaceCoordinates
  bbox?: {
    minLat: number
    minLng: number
    maxLat: number
    maxLng: number
  }
  categories: string[]
  score: number
  timezone?: string
  metadata?: {
    country?: string
    postcode?: string
  }
  phone?: string
  website?: string
  rating?: number
  popularity?: number
}

interface PlacesSearchProps {
  onPlaceSelect?: (place: PlaceDetails) => void
  onCoordinatesSelect?: (coordinates: PlaceCoordinates, place: PlaceDetails) => void
  placeholder?: string
  className?: string
  showCategories?: boolean
  categories?: string[]
  countries?: string[]
  proximityBias?: PlaceCoordinates
  radius?: number
  disabled?: boolean
  clearOnSelect?: boolean
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'minimal' | 'bordered'
  language?: string
  supportRTL?: boolean
  useRealGeocoding?: boolean
}

// Category icons mapping
const getCategoryIcon = (types: string[], categories: string[]) => {
  const allTypes = [...types, ...categories].map(t => t.toLowerCase())
  
  if (allTypes.some(t => ['hotel', 'lodging', 'accommodation'].includes(t))) return <Building className="w-4 h-4 text-blue-600" />
  if (allTypes.some(t => ['restaurant', 'food', 'cafe', 'bar'].includes(t))) return <Utensils className="w-4 h-4 text-orange-600" />
  if (allTypes.some(t => ['museum', 'attraction', 'culture', 'gallery'].includes(t))) return <Camera className="w-4 h-4 text-purple-600" />
  if (allTypes.some(t => ['address', 'residential'].includes(t))) return <Home className="w-4 h-4 text-gray-600" />
  if (allTypes.some(t => ['shopping', 'store', 'market'].includes(t))) return <ShoppingBag className="w-4 h-4 text-green-600" />
  if (allTypes.some(t => ['transport', 'gas', 'station'].includes(t))) return <Car className="w-4 h-4 text-red-600" />
  if (allTypes.some(t => ['services', 'hospital', 'bank'].includes(t))) return <Heart className="w-4 h-4 text-pink-600" />
  if (allTypes.some(t => ['nature', 'park', 'beach'].includes(t))) return <TreePine className="w-4 h-4 text-green-700" />
  if (allTypes.some(t => ['culture', 'theater', 'art'].includes(t))) return <Palette className="w-4 h-4 text-indigo-600" />
  if (allTypes.some(t => ['nightlife', 'club', 'entertainment'].includes(t))) return <Moon className="w-4 h-4 text-yellow-600" />
  
  return <MapPin className="w-4 h-4 text-gray-500" />
}

// Generate session token
const generateSessionToken = () => `st_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

// Detect if text contains Hebrew characters
const containsHebrew = (text: string): boolean => {
  return /[\u0590-\u05FF]/.test(text)
}

// Detect text direction
const getTextDirection = (text: string): 'ltr' | 'rtl' => {
  return containsHebrew(text) ? 'rtl' : 'ltr'
}

// Convert geocoding result to place suggestion
const geocodingToSuggestion = (result: GeocodingResult, query: string): PlaceSuggestion => {
  const name = result.formatted_address || result.address

  // Create better highlighting that preserves case
  const highlighted = name.replace(
    new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'),
    '<b>$1</b>'
  )

  // Generate a unique ID for geocoding results
  const geocodingId = result.place_id || `geocoding_${result.lat}_${result.lon}_${Date.now()}`

  return {
    id: geocodingId,
    name: name,
    highlighted: highlighted,
    formatted_address: name,
    center: { lat: result.lat, lng: result.lon },
    types: result.types || ['address'],
    confidence: 1.0,
    source: 'geocoding',
    categories: result.types || ['address'],
    score: 1.0,
    distance: undefined,
    // Store original geocoding result for reference
    _geocodingResult: result
  }
}

export default function PlacesSearch({
  onPlaceSelect,
  onCoordinatesSelect,
  placeholder = "Search for places, addresses, or points of interest...",
  className = "",
  showCategories = true,
  categories,
  countries,
  proximityBias,
  radius,
  disabled = false,
  clearOnSelect = true,
  size = 'md',
  variant = 'default',
  language = 'en',
  supportRTL = true,
  useRealGeocoding = false
}: PlacesSearchProps) {
  // State
  const [query, setQuery] = useState('')
  const [suggestions, setSuggestions] = useState<PlaceSuggestion[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const [sessionToken] = useState(() => generateSessionToken())
  const [error, setError] = useState<string | null>(null)
  const [textDirection, setTextDirection] = useState<'ltr' | 'rtl'>('ltr')
  const [mounted, setMounted] = useState(false)

  // Refs
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // Size classes
  const sizeClasses = {
    sm: 'text-sm py-2 px-3',
    md: 'text-base py-3 px-4',
    lg: 'text-lg py-4 px-5'
  }

  // Variant classes
  const variantClasses = {
    default: 'border border-gray-300 rounded-lg bg-white shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
    minimal: 'border-0 border-b-2 border-gray-200 rounded-none bg-transparent focus:border-blue-500',
    bordered: 'border-2 border-gray-300 rounded-xl bg-white shadow-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
  }

  // Debounced search function
  const debouncedSearch = useCallback(async (searchQuery: string) => {
    if (searchQuery.length < 2) {
      setSuggestions([])
      setIsOpen(false)
      return
    }

    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController()

    setIsLoading(true)
    setError(null)

    try {
      let suggestions: PlaceSuggestion[] = []

      if (useRealGeocoding) {
        // Use real geocoding API
        console.log('PlacesSearch: Using real geocoding for query:', searchQuery)
        const geocodingResults = await geocodeAddress(searchQuery)
        suggestions = geocodingResults.slice(0, 8).map(result => geocodingToSuggestion(result, searchQuery))
        console.log('PlacesSearch: Got', suggestions.length, 'geocoding results')
      } else {
        // Use mock places API
        console.log('PlacesSearch: Using mock places API for query:', searchQuery)

        // Build query parameters
        const params = new URLSearchParams({
          q: searchQuery,
          session_token: sessionToken,
          limit: '8'
        })

        if (proximityBias) {
          params.append('lat', proximityBias.lat.toString())
          params.append('lng', proximityBias.lng.toString())
        }

        if (radius) {
          params.append('radius', radius.toString())
        }

        if (categories && categories.length > 0) {
          params.append('categories', categories.join(','))
        }

        if (countries && countries.length > 0) {
          params.append('countries', countries.join(','))
        }

        // Set language parameter
        params.append('lang', language)

        // Make API request
        const response = await fetch(`/api/places/v1/places/suggest?${params}`, {
          signal: abortControllerRef.current.signal,
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth_token') || 'fake_token_01K365YF7N0QVENA3HQZKGH7XA'}`
          }
        })

        if (!response.ok) {
          throw new Error(`Search failed: ${response.status}`)
        }

        const data = await response.json()
        suggestions = data.suggestions || []
      }

      setSuggestions(suggestions)
      setIsOpen(suggestions.length > 0)
      setSelectedIndex(-1)

    } catch (error: any) {
      if (error.name !== 'AbortError') {
        console.error('Search error:', error)
        setError('Search failed. Please try again.')
        setSuggestions([])
      }
    } finally {
      setIsLoading(false)
    }
  }, [sessionToken, proximityBias, radius, categories, countries, language, useRealGeocoding])

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

    // Debounce search
    debounceTimeoutRef.current = setTimeout(() => {
      debouncedSearch(value)
    }, 200)
  }

  // Handle place selection
  const handlePlaceSelect = async (suggestion: PlaceSuggestion) => {
    try {
      setIsLoading(true)
      console.log('PlacesSearch: Handling place selection for:', suggestion.name)
      console.log('PlacesSearch: Real geocoding mode:', useRealGeocoding)

      let placeDetails: PlaceDetails

      if (useRealGeocoding) {
        // For real geocoding, we already have all the data we need in the suggestion
        console.log('PlacesSearch: Using geocoding data directly')
        placeDetails = {
          id: suggestion.id,
          name: suggestion.name,
          formatted_address: suggestion.formatted_address,
          types: suggestion.types,
          center: suggestion.center,
          categories: suggestion.categories,
          score: suggestion.score,
          // Add any additional metadata if available
          metadata: {
            country: suggestion.types.includes('country') ? suggestion.name : undefined
          }
        }
      } else {
        // For mock data, fetch full place details from API
        console.log('PlacesSearch: Fetching place details from API for ID:', suggestion.id)
        const response = await fetch(`/api/places/v1/places/${suggestion.id}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth_token') || 'fake_token_01K365YF7N0QVENA3HQZKGH7XA'}`
          }
        })

        if (!response.ok) {
          throw new Error(`Failed to fetch place details: ${response.status}`)
        }

        placeDetails = await response.json()
      }

      console.log('PlacesSearch: Final place details:', placeDetails)

      // Call callbacks
      if (onPlaceSelect) {
        console.log('PlacesSearch: Calling onPlaceSelect callback')
        onPlaceSelect(placeDetails)
      }

      if (onCoordinatesSelect) {
        console.log('PlacesSearch: Calling onCoordinatesSelect callback')
        onCoordinatesSelect(placeDetails.center, placeDetails)
      }

      // Update UI
      if (clearOnSelect) {
        setQuery('')
        setSuggestions([])
      } else {
        setQuery(suggestion.name)
      }

      setIsOpen(false)
      setSelectedIndex(-1)

    } catch (error) {
      console.error('Error handling place selection:', error)
      setError('Failed to select place')
    } finally {
      setIsLoading(false)
    }
  }

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || suggestions.length === 0) return

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex(prev => 
          prev < suggestions.length - 1 ? prev + 1 : prev
        )
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex(prev => prev > 0 ? prev - 1 : -1)
        break
      case 'Enter':
        e.preventDefault()
        if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
          handlePlaceSelect(suggestions[selectedIndex])
        }
        break
      case 'Escape':
        setIsOpen(false)
        setSelectedIndex(-1)
        inputRef.current?.blur()
        break
    }
  }

  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        !inputRef.current?.contains(event.target as Node)
      ) {
        setIsOpen(false)
        setSelectedIndex(-1)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

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

  // Clear search
  const clearSearch = () => {
    setQuery('')
    setSuggestions([])
    setIsOpen(false)
    setSelectedIndex(-1)
    setError(null)
    inputRef.current?.focus()
  }

  return (
    <div className={`relative ${className}`}>
      {/* Search Input */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-5 w-5 text-gray-400" />
        </div>
        
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => query.length >= 2 && suggestions.length > 0 && setIsOpen(true)}
          placeholder={placeholder}
          disabled={disabled}
          dir={mounted && supportRTL ? textDirection : 'ltr'}
          className={`
            w-full transition-all duration-200
            ${mounted && textDirection === 'rtl' ? 'pr-10 pl-10 text-right' : 'pl-10 pr-10 text-left'}
            ${sizeClasses[size]}
            ${variantClasses[variant]}
            ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:border-gray-400'}
            ${error ? 'border-red-500 focus:ring-red-500 focus:border-red-500' : ''}
          `}
        />

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
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-1 text-sm text-red-600">
          {error}
        </div>
      )}

      {/* Suggestions Dropdown */}
      {isOpen && (suggestions.length > 0 || isLoading) && (
        <div
          ref={dropdownRef}
          className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-80 overflow-y-auto"
        >
          {suggestions.map((suggestion, index) => (
            <div
              key={suggestion.id}
              onClick={() => handlePlaceSelect(suggestion)}
              className={`
                px-4 py-3 cursor-pointer border-b border-gray-100 last:border-b-0
                hover:bg-gray-50 transition-colors
                ${selectedIndex === index ? 'bg-blue-50 border-blue-200' : ''}
              `}
            >
              <div className="flex items-start gap-3">
                {/* Category Icon */}
                <div className="flex-shrink-0 mt-0.5">
                  {getCategoryIcon(suggestion.types, [])}
                </div>

                {/* Place Info */}
                <div className="flex-1 min-w-0">
                  <div
                    className="font-medium text-gray-900 truncate"
                    dir={mounted ? getTextDirection(suggestion.name) : 'ltr'}
                    dangerouslySetInnerHTML={{ __html: suggestion.highlighted }}
                  />
                  <div
                    className="text-sm text-gray-600 truncate"
                    dir={mounted ? getTextDirection(suggestion.formatted_address) : 'ltr'}
                  >
                    {suggestion.formatted_address}
                  </div>
                  
                  {/* Categories and Distance */}
                  <div className="flex items-center gap-2 mt-1">
                    {showCategories && suggestion.types.length > 0 && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                        {suggestion.types[0]}
                      </span>
                    )}
                    {suggestion.distance_m && (
                      <span className="text-xs text-gray-500">
                        {suggestion.distance_m < 1000 
                          ? `${suggestion.distance_m}m` 
                          : `${(suggestion.distance_m / 1000).toFixed(1)}km`
                        }
                      </span>
                    )}
                  </div>
                </div>

                {/* Confidence Score */}
                <div className="flex-shrink-0">
                  <div className="text-xs text-gray-400">
                    {Math.round(suggestion.confidence * 100)}%
                  </div>
                </div>
              </div>
            </div>
          ))}

          {/* No Results */}
          {!isLoading && suggestions.length === 0 && query.length >= 2 && (
            <div className="px-4 py-6 text-center text-gray-500">
              <MapPin className="h-8 w-8 mx-auto mb-2 text-gray-300" />
              <div className="text-sm font-medium">No places found</div>
              <div className="text-xs">Try a different search term</div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
