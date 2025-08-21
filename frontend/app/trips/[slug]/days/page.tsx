/**
 * Trip Days Page
 * Displays and manages days for a specific trip
 */

'use client';

import React from 'react';
import { useParams } from 'next/navigation';
import { DaysList } from '@/components/days';
import { DebugPanel, DebugStatus } from '@/components/debug';
import { Day, Trip } from '@/types';

// Mock trip data for demonstration
// In a real app, this would come from your API/state management
const mockTrip: Trip = {
  id: 'trip-123',
  slug: 'california-road-trip',
  title: 'California Road Trip',
  destination: 'California, USA',
  start_date: '2024-06-15', // ISO date string
  timezone: 'America/Los_Angeles',
  status: 'active',
  is_published: false,
  created_by: 'user-123',
  deleted_at: null,
  created_at: '2024-08-21T10:00:00Z',
  updated_at: '2024-08-21T10:00:00Z'
};

export default function TripDaysPage() {
  const params = useParams();
  const tripSlug = params.slug as string;

  const handleDayClick = (day: Day) => {
    // Navigate to day detail page
    console.log('Navigate to day:', day.id);
    // In a real app: router.push(`/trips/${tripSlug}/days/${day.id}`)
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <span>Trips</span>
            <span>/</span>
            <span>{mockTrip.title}</span>
            <span>/</span>
            <span className="text-gray-900 font-medium">Days</span>
          </div>
          <DebugStatus />
        </div>
        <h1 className="text-3xl font-bold text-gray-900">{mockTrip.title}</h1>
        <p className="text-gray-600 mt-1">Plan your day-by-day itinerary</p>
      </div>

      {/* Days Management */}
      <DaysList 
        trip={mockTrip}
        onDayClick={handleDayClick}
        className="max-w-7xl"
      />

      {/* Usage Instructions */}
      <div className="mt-12 p-6 bg-blue-50 rounded-lg border border-blue-200">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">
          Days Management Features
        </h3>
        <div className="grid md:grid-cols-2 gap-4 text-sm text-blue-800">
          <div>
            <h4 className="font-medium mb-2">✅ Implemented Features:</h4>
            <ul className="space-y-1">
              <li>• Dynamic date calculation from trip start date</li>
              <li>• Create, edit, and delete days</li>
              <li>• Rest day management</li>
              <li>• Activity and note tracking</li>
              <li>• Sequence number management</li>
              <li>• Responsive grid layout</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium mb-2">📅 Date Logic:</h4>
            <ul className="space-y-1">
              <li>• Day 1: {mockTrip.start_date} (trip start)</li>
              <li>• Day 2: June 16 (start + 1 day)</li>
              <li>• Day 3: June 17 (start + 2 days)</li>
              <li>• Automatically updates when trip date changes</li>
              <li>• Handles trips without start dates</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Debug Panel */}
      <DebugPanel />
    </div>
  );
}
