/**
 * Phase 1 Migration Demo Page
 * 
 * Demonstrates all the new features from the backend Phase 1 implementation:
 * - HTTP Status Code handling (201 Created, 204 No Content)
 * - Unified error responses with structured format
 * - Field-level validation errors
 * - Actionable error suggestions
 * - Request tracking
 */

'use client';

import React, { useState, useEffect } from 'react';
import { EnhancedTripForm, EnhancedTripDelete } from '@/components/trips/enhanced-trip-form';
import { ErrorDisplay, SuccessDisplay } from '@/components/ui/error-display';
import { listTripsEnhanced, Trip } from '@/lib/api/trips';
import { apiClient } from '@/lib/api/enhanced-client';

export default function MigrationDemoPage() {
  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<any>(null);

  // Load trips on component mount
  useEffect(() => {
    loadTrips();
  }, []);

  const loadTrips = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await listTripsEnhanced();
      if (response.success && response.data) {
        setTrips(response.data.data || []);
      } else {
        setError(response.error);
      }
    } catch (err) {
      setError({
        error_code: 'NETWORK_ERROR',
        message: 'Failed to load trips',
        suggestions: ['Check your internet connection', 'Try refreshing the page']
      });
    } finally {
      setLoading(false);
    }
  };

  const handleTripCreated = (trip: Trip) => {
    setTrips(prev => [trip, ...prev]);
  };

  const handleTripDeleted = () => {
    loadTrips(); // Reload trips after deletion
  };

  const testErrorScenarios = async () => {
    // Test various error scenarios to demonstrate error handling
    const scenarios = [
      {
        name: 'Validation Error',
        test: () => apiClient.post('/trips/', { title: '' }) // Empty title
      },
      {
        name: 'Authentication Error',
        test: async () => {
          // Temporarily remove auth token
          const token = localStorage.getItem('auth_token');
          localStorage.removeItem('auth_token');
          const result = await apiClient.get('/trips/');
          if (token) localStorage.setItem('auth_token', token);
          return result;
        }
      },
      {
        name: 'Not Found Error',
        test: () => apiClient.get('/trips/nonexistent-trip-id')
      }
    ];

    for (const scenario of scenarios) {
      console.log(`\n=== Testing ${scenario.name} ===`);
      try {
        const result = await scenario.test();
        console.log('Result:', result);
      } catch (err) {
        console.log('Error:', err);
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Phase 1 Migration Demo
          </h1>
          <p className="text-gray-600">
            Demonstrating enhanced HTTP status codes and error handling
          </p>
        </div>

        {/* Feature Overview */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">✨ New Features</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-medium text-green-700 mb-2">✅ HTTP Status Codes</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• 201 Created for POST operations</li>
                <li>• 204 No Content for DELETE operations</li>
                <li>• 200 OK for GET/PUT operations</li>
              </ul>
            </div>
            <div>
              <h3 className="font-medium text-blue-700 mb-2">🔧 Enhanced Errors</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Structured error responses</li>
                <li>• Field-level validation errors</li>
                <li>• Actionable suggestions</li>
                <li>• Request tracking with unique IDs</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Trip Creation Form */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <EnhancedTripForm 
              onTripCreated={handleTripCreated}
              className="max-w-none"
            />
          </div>

          {/* Existing Trips */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Your Trips</h2>
              <button
                onClick={loadTrips}
                className="text-blue-600 hover:text-blue-800 text-sm"
              >
                Refresh
              </button>
            </div>

            {loading && (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="text-gray-500 mt-2">Loading trips...</p>
              </div>
            )}

            {error && (
              <ErrorDisplay
                error={error}
                className="mb-4"
                onRetry={loadTrips}
              />
            )}

            {!loading && !error && (
              <div className="space-y-4">
                {trips.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">
                    No trips yet. Create your first trip!
                  </p>
                ) : (
                  trips.map((trip) => (
                    <div key={trip.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="font-medium text-gray-900">{trip.title}</h3>
                          {trip.destination && (
                            <p className="text-sm text-gray-600">📍 {trip.destination}</p>
                          )}
                          <p className="text-xs text-gray-500 mt-1">
                            Status: {trip.status} • Created: {new Date(trip.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <EnhancedTripDelete
                          trip={trip}
                          onTripDeleted={handleTripDeleted}
                        />
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>

        {/* Error Testing Section */}
        <div className="bg-white rounded-lg shadow-sm p-6 mt-8">
          <h2 className="text-xl font-semibold mb-4">🧪 Error Testing</h2>
          <p className="text-gray-600 mb-4">
            Test different error scenarios to see the enhanced error handling in action.
            Check the browser console for detailed error responses.
          </p>
          <button
            onClick={testErrorScenarios}
            className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 transition-colors"
          >
            Run Error Tests
          </button>
        </div>

        {/* API Status */}
        <div className="bg-white rounded-lg shadow-sm p-6 mt-8">
          <h2 className="text-xl font-semibold mb-4">🔗 API Status</h2>
          <APIStatusChecker />
        </div>
      </div>
    </div>
  );
}

/**
 * Component to check API status and demonstrate health endpoint
 */
function APIStatusChecker() {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const checkStatus = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/health');
      setStatus(response);
    } catch (err) {
      setStatus({
        success: false,
        error: {
          error_code: 'NETWORK_ERROR',
          message: 'Failed to connect to API'
        }
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkStatus();
  }, []);

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <span className="text-gray-700">Backend API Status:</span>
        <button
          onClick={checkStatus}
          disabled={loading}
          className="text-blue-600 hover:text-blue-800 text-sm disabled:text-gray-400"
        >
          {loading ? 'Checking...' : 'Check Status'}
        </button>
      </div>

      {status && (
        <div className="bg-gray-50 rounded p-4">
          {status.success ? (
            <div className="flex items-center text-green-700">
              <span className="w-3 h-3 bg-green-500 rounded-full mr-2"></span>
              API is healthy
              {status.data && (
                <span className="ml-2 text-sm text-gray-600">
                  (v{status.data.version})
                </span>
              )}
            </div>
          ) : (
            <div className="flex items-center text-red-700">
              <span className="w-3 h-3 bg-red-500 rounded-full mr-2"></span>
              API is unavailable
            </div>
          )}
          
          <details className="mt-2">
            <summary className="text-sm text-gray-600 cursor-pointer">
              View raw response
            </summary>
            <pre className="text-xs bg-white p-2 rounded mt-2 overflow-auto">
              {JSON.stringify(status, null, 2)}
            </pre>
          </details>
        </div>
      )}
    </div>
  );
}
