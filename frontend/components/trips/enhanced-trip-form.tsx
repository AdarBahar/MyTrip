/**
 * Enhanced Trip Form Component
 * 
 * Demonstrates Phase 1 Migration features:
 * - Proper handling of 201 Created responses
 * - Structured error display with field-level validation
 * - Actionable error suggestions
 * - Success messages for different operation types
 */

'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createTrip, deleteTrip, TripCreate, Trip } from '@/lib/api/trips';
import { ErrorDisplay, SuccessDisplay, useAPIResponseHandler } from '@/components/ui/error-display';

interface EnhancedTripFormProps {
  onTripCreated?: (trip: Trip) => void;
  className?: string;
}

interface TripDeleteProps {
  trip: Trip;
  onTripDeleted?: () => void;
  className?: string;
}

/**
 * Enhanced Trip Creation Form
 */
export function EnhancedTripForm({ onTripCreated, className = '' }: EnhancedTripFormProps) {
  const [formData, setFormData] = useState<TripCreate>({
    title: '',
    destination: '',
    start_date: null
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { error, success, handleResponse, clearMessages } = useAPIResponseHandler();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    clearMessages();

    try {
      const response = await createTrip(formData);
      const result = handleResponse(response, `Trip "${formData.title}" created successfully!`);
      
      if (result) {
        // Handle successful creation (201 Created)
        const tripData = result.trip;
        onTripCreated?.(tripData);
        
        // Reset form
        setFormData({ title: '', destination: '', start_date: null });
        
        // Optionally redirect to the new trip
        // router.push(`/trips/${tripData.id}`);
      }
    } catch (err) {
      console.error('Trip creation failed:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (field: keyof TripCreate, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value || null
    }));
    
    // Clear messages when user starts typing
    if (error || success) {
      clearMessages();
    }
  };

  return (
    <div className={`max-w-md mx-auto ${className}`}>
      <h2 className="text-2xl font-bold mb-6">Create New Trip</h2>
      
      {/* Success Message */}
      {success && (
        <SuccessDisplay
          message={success.message}
          type={success.type}
          className="mb-4"
          onDismiss={clearMessages}
        />
      )}

      {/* Error Display */}
      {error && (
        <ErrorDisplay
          error={error}
          className="mb-4"
          showSuggestions={true}
          showRequestId={true}
          onRetry={() => handleSubmit({ preventDefault: () => {} } as React.FormEvent)}
        />
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Title Field */}
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
            Trip Title *
          </label>
          <input
            type="text"
            id="title"
            value={formData.title}
            onChange={(e) => handleInputChange('title', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter trip title"
            required
          />
        </div>

        {/* Destination Field */}
        <div>
          <label htmlFor="destination" className="block text-sm font-medium text-gray-700 mb-1">
            Destination
          </label>
          <input
            type="text"
            id="destination"
            value={formData.destination || ''}
            onChange={(e) => handleInputChange('destination', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Where are you going?"
          />
        </div>

        {/* Start Date Field */}
        <div>
          <label htmlFor="start_date" className="block text-sm font-medium text-gray-700 mb-1">
            Start Date
          </label>
          <input
            type="date"
            id="start_date"
            value={formData.start_date || ''}
            onChange={(e) => handleInputChange('start_date', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isSubmitting || !formData.title.trim()}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {isSubmitting ? 'Creating Trip...' : 'Create Trip'}
        </button>
      </form>

      {/* Demo Information */}
      <div className="mt-6 p-4 bg-gray-50 rounded-md">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Phase 1 Migration Demo</h3>
        <ul className="text-xs text-gray-600 space-y-1">
          <li>✅ Returns 201 Created on success</li>
          <li>✅ Shows structured validation errors</li>
          <li>✅ Displays actionable suggestions</li>
          <li>✅ Includes request tracking</li>
          <li>✅ Field-level error highlighting</li>
        </ul>
      </div>
    </div>
  );
}

/**
 * Enhanced Trip Delete Component
 */
export function EnhancedTripDelete({ trip, onTripDeleted, className = '' }: TripDeleteProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const { error, success, handleResponse, clearMessages } = useAPIResponseHandler();

  const handleDelete = async () => {
    setIsDeleting(true);
    clearMessages();

    try {
      const response = await deleteTrip(trip.id);
      const result = handleResponse(response, `Trip "${trip.title}" deleted successfully!`);
      
      if (result !== null) {
        // Handle successful deletion (204 No Content)
        onTripDeleted?.();
        setShowConfirm(false);
      }
    } catch (err) {
      console.error('Trip deletion failed:', err);
    } finally {
      setIsDeleting(false);
    }
  };

  if (!showConfirm) {
    return (
      <div className={className}>
        <button
          onClick={() => setShowConfirm(true)}
          className="text-red-600 hover:text-red-800 text-sm"
        >
          Delete Trip
        </button>
      </div>
    );
  }

  return (
    <div className={`border border-red-200 rounded-lg p-4 bg-red-50 ${className}`}>
      <h3 className="text-lg font-medium text-red-800 mb-2">Delete Trip</h3>
      
      {/* Success Message */}
      {success && (
        <SuccessDisplay
          message={success.message}
          type={success.type}
          className="mb-4"
          onDismiss={clearMessages}
        />
      )}

      {/* Error Display */}
      {error && (
        <ErrorDisplay
          error={error}
          className="mb-4"
          showSuggestions={true}
          onRetry={handleDelete}
        />
      )}

      <p className="text-sm text-red-700 mb-4">
        Are you sure you want to delete "{trip.title}"? This action cannot be undone.
      </p>

      <div className="flex space-x-3">
        <button
          onClick={handleDelete}
          disabled={isDeleting}
          className="bg-red-600 text-white px-4 py-2 rounded text-sm hover:bg-red-700 disabled:bg-gray-400 transition-colors"
        >
          {isDeleting ? 'Deleting...' : 'Yes, Delete'}
        </button>
        <button
          onClick={() => {
            setShowConfirm(false);
            clearMessages();
          }}
          disabled={isDeleting}
          className="bg-gray-300 text-gray-700 px-4 py-2 rounded text-sm hover:bg-gray-400 transition-colors"
        >
          Cancel
        </button>
      </div>

      {/* Demo Information */}
      <div className="mt-4 p-3 bg-white rounded border">
        <h4 className="text-xs font-medium text-gray-700 mb-1">Delete Demo Features</h4>
        <ul className="text-xs text-gray-600 space-y-1">
          <li>✅ Returns 204 No Content on success</li>
          <li>✅ Empty response body handling</li>
          <li>✅ Proper error handling for failures</li>
        </ul>
      </div>
    </div>
  );
}
