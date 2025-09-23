/**
 * AddStopModal Component
 * 
 * Modal for adding a new stop to a day
 */

import React, { useState, useEffect } from 'react';
import { X, MapPin, Search, Plus, Clock, Star, DollarSign } from 'lucide-react';
import { StopWithPlace, createStop, getNextSequenceNumber } from '../../lib/api/stops';
import { Place, searchPlaces, createPlace } from '../../lib/api/places';
import { STOP_TYPE_OPTIONS, STOP_PRIORITIES, StopType, StopPriority } from '../../lib/constants/stopTypes';
import { validateStopTimes } from '../../lib/api/stops';
import { debugManager } from '@/lib/debug';

interface AddStopModalProps {
  tripId: string;
  dayId: string;
  existingStops: StopWithPlace[];
  onClose: () => void;
  onStopAdded: () => void;
}

export default function AddStopModal({
  tripId,
  dayId,
  existingStops,
  onClose,
  onStopAdded
}: AddStopModalProps) {
  const [step, setStep] = useState<'search' | 'details'>('search');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Place[]>([]);
  const [searching, setSearching] = useState(false);
  const [selectedPlace, setSelectedPlace] = useState<Place | null>(null);
  const [creating, setCreating] = useState(false);
  
  // Stop details
  const [stopType, setStopType] = useState<StopType>(StopType.OTHER);
  const [priority, setPriority] = useState<StopPriority>(StopPriority.NICE_TO_HAVE);
  const [arrivalTime, setArrivalTime] = useState('');
  const [departureTime, setDepartureTime] = useState('');
  const [duration, setDuration] = useState('');
  const [notes, setNotes] = useState('');
  const [estimatedCost, setEstimatedCost] = useState('');
  
  const debug = debugManager;

  // Search for places
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    try {
      setSearching(true);
      debug.log('AddStopModal', 'Searching places', { query: searchQuery });
      
      const response = await searchPlaces({
        query: searchQuery.trim(),
        limit: 10
      });
      
      setSearchResults(response.places);
      debug.log('AddStopModal', 'Search results', { count: response.places.length });
      
    } catch (err) {
      debug.error('AddStopModal', 'Search failed', err);
      // TODO: Show error toast
    } finally {
      setSearching(false);
    }
  };

  // Handle place selection
  const handlePlaceSelect = (place: Place) => {
    setSelectedPlace(place);
    setStep('details');
    
    // Auto-set stop type based on place name/address
    const name = place.name.toLowerCase();
    if (name.includes('hotel') || name.includes('motel') || name.includes('inn')) {
      setStopType(StopType.ACCOMMODATION);
    } else if (name.includes('restaurant') || name.includes('cafe') || name.includes('bar')) {
      setStopType(StopType.FOOD);
    } else if (name.includes('museum') || name.includes('park') || name.includes('monument')) {
      setStopType(StopType.ATTRACTION);
    } else if (name.includes('gas') || name.includes('fuel') || name.includes('station')) {
      setStopType(StopType.GAS);
    }
  };

  // Create custom place
  const handleCreateCustomPlace = async () => {
    if (!searchQuery.trim()) return;

    try {
      setSearching(true);
      debug.log('AddStopModal', 'Creating custom place', { name: searchQuery });

      // For custom places without coordinates, we need to geocode first
      // or ask the user to provide coordinates
      throw new Error('Custom places without coordinates are not supported yet. Please search for a specific location.');

    } catch (err) {
      debug.error('AddStopModal', 'Failed to create custom place', err);
      // TODO: Show error toast
      alert('Please search for a specific location with coordinates instead of creating a custom place.');
    } finally {
      setSearching(false);
    }
  };

  // Create stop
  const handleCreateStop = async () => {
    if (!selectedPlace) return;

    // Validate times
    if (arrivalTime && departureTime) {
      const timeValidation = validateStopTimes(arrivalTime, departureTime);
      if (!timeValidation.isValid) {
        // TODO: Show error toast
        debug.error('AddStopModal', 'Invalid times', timeValidation.error);
        return;
      }
    }

    try {
      setCreating(true);
      debug.log('AddStopModal', 'Creating stop', { placeId: selectedPlace.id });
      
      const stopData = {
        place_id: selectedPlace.id,
        seq: getNextSequenceNumber(existingStops),
        kind: 'via' as const,
        stop_type: stopType,
        priority,
        arrival_time: arrivalTime || undefined,
        departure_time: departureTime || undefined,
        duration_minutes: duration ? parseInt(duration) : undefined,
        notes: notes || undefined,
        cost_info: estimatedCost ? { estimated: parseFloat(estimatedCost) } : undefined
      };
      
      await createStop(tripId, dayId, stopData);
      
      debug.log('AddStopModal', 'Stop created successfully');
      onStopAdded();
      
    } catch (err) {
      debug.error('AddStopModal', 'Failed to create stop', err);
      // TODO: Show error toast
    } finally {
      setCreating(false);
    }
  };

  // Handle search on enter
  const handleSearchKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold">Add New Stop</h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="overflow-y-auto max-h-[calc(90vh-80px)]">
          {step === 'search' ? (
            /* Search Step */
            <div className="p-6">
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Search for a place
                </label>
                <div className="flex gap-2">
                  <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <input
                      type="text"
                      id="place-search-input"
                      name="place-search"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyPress={handleSearchKeyPress}
                      placeholder="Restaurant, hotel, attraction..."
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <button
                    onClick={handleSearch}
                    disabled={!searchQuery.trim() || searching}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {searching ? 'Searching...' : 'Search'}
                  </button>
                </div>
              </div>

              {/* Search Results */}
              {searchResults.length > 0 && (
                <div className="space-y-2 mb-6">
                  <h3 className="font-medium text-gray-900">Search Results</h3>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {searchResults.map((place) => (
                      <button
                        key={place.id}
                        onClick={() => handlePlaceSelect(place)}
                        className="w-full text-left p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-start gap-3">
                          <MapPin className="w-4 h-4 text-gray-400 mt-1 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <h4 className="font-medium text-gray-900 truncate">
                              {place.name}
                            </h4>
                            {place.address && (
                              <p className="text-sm text-gray-600 truncate">
                                {(place.meta as any)?.normalized?.display_short || formatShortAddress(place, { showCountry: true })}
                              </p>
                            )}
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Create Custom Place */}
              {searchQuery.trim() && (
                <div className="border-t border-gray-200 pt-4">
                  <button
                    onClick={handleCreateCustomPlace}
                    disabled={searching}
                    className="w-full flex items-center gap-3 p-3 border border-dashed border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <Plus className="w-4 h-4 text-gray-400" />
                    <div className="text-left">
                      <p className="font-medium text-gray-900">
                        Create "{searchQuery}"
                      </p>
                      <p className="text-sm text-gray-600">
                        Add as a custom location
                      </p>
                    </div>
                  </button>
                </div>
              )}
            </div>
          ) : (
            /* Details Step */
            <div className="p-6">
              {/* Selected Place */}
              <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <MapPin className="w-5 h-5 text-gray-400" />
                  <div>
                    <h3 className="font-medium text-gray-900">
                      {selectedPlace?.name}
                    </h3>
                    {selectedPlace?.address && (
                      <p className="text-sm text-gray-600">
                        {(selectedPlace.meta as any)?.normalized?.display_short || formatShortAddress(selectedPlace, { showCountry: true })}
                      </p>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => setStep('search')}
                  className="mt-2 text-sm text-blue-600 hover:text-blue-800"
                >
                  Change location
                </button>
              </div>

              <div className="space-y-6">
                {/* Stop Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Stop Type
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    {STOP_TYPE_OPTIONS.map((type) => (
                      <button
                        key={type.type}
                        onClick={() => setStopType(type.type)}
                        className={`p-3 text-left border rounded-lg transition-colors ${
                          stopType === type.type
                            ? `${type.bgColor} ${type.textColor} border-current`
                            : 'border-gray-200 hover:bg-gray-50'
                        }`}
                      >
                        <div className="font-medium text-sm">{type.label}</div>
                        <div className="text-xs opacity-75">{type.description}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Priority */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Priority
                  </label>
                  <select
                    id="stop-priority"
                    name="stop-priority"
                    value={priority}
                    onChange={(e) => setPriority(parseInt(e.target.value) as StopPriority)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    {Object.values(STOP_PRIORITIES).map((p) => (
                      <option key={p.priority} value={p.priority}>
                        {p.label} - {p.description}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Timing */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Arrival Time
                    </label>
                    <input
                      type="time"
                      value={arrivalTime}
                      onChange={(e) => setArrivalTime(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Departure Time
                    </label>
                    <input
                      type="time"
                      value={departureTime}
                      onChange={(e) => setDepartureTime(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Duration (minutes)
                    </label>
                    <input
                      type="number"
                      value={duration}
                      onChange={(e) => setDuration(e.target.value)}
                      placeholder="60"
                      min="1"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>

                {/* Cost */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Estimated Cost ($)
                  </label>
                  <input
                    type="number"
                    value={estimatedCost}
                    onChange={(e) => setEstimatedCost(e.target.value)}
                    placeholder="25.00"
                    min="0"
                    step="0.01"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Notes */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Notes
                  </label>
                  <textarea
                    id="stop-notes"
                    name="stop-notes"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Any additional notes about this stop..."
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        {step === 'details' && (
          <div className="flex items-center justify-between p-6 border-t border-gray-200">
            <button
              onClick={() => setStep('search')}
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              Back
            </button>
            
            <button
              onClick={handleCreateStop}
              disabled={!selectedPlace || creating}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {creating ? 'Adding Stop...' : 'Add Stop'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
