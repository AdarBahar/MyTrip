'use client';

import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { DaysList } from '@/components/days';
import { getDaysSummary, DayLocationsSummary } from '@/lib/api/days';
import { DebugPanel, DebugStatus } from '@/components/debug';
import { Day } from '@/types';
import { Trip } from '@/lib/api/trips';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';
import { fetchWithAuth } from '@/lib/auth';
import { getApiBase } from '@/lib/api/base';

export default function TripDaysPage() {
  const params = useParams();
  const router = useRouter();
  const tripSlug = params.slug as string;

  const [trip, setTrip] = useState<Trip | null>(null);
  const [dayLocations, setDayLocations] = useState<Record<string, { start?: any; end?: any; route_total_km?: number; route_total_min?: number; route_coordinates?: [number, number][] }>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check authentication
    const token = localStorage.getItem('auth_token');
    if (!token) {
      router.push('/login');
      return;
    }

    fetchTripDetails();
  }, [tripSlug]);

  const fetchTripDetails = async () => {
    try {
      const apiBaseUrl = await getApiBase();

      // First, get all trips to find the one with matching slug
      const tripsResponse = await fetchWithAuth(`${apiBaseUrl}/trips/`);
      if (!tripsResponse.ok) throw new Error(`Failed to fetch trips: ${tripsResponse.status}`);
      const tripsData = await tripsResponse.json();
      const foundTrip = tripsData.trips.find((t: Trip) => t.slug === tripSlug);
      if (!foundTrip) { setError('Trip not found'); return; }

      // Fetch trip details and days summary in parallel
      const [tripResponse, summaryResp] = await Promise.all([
        fetchWithAuth(`${apiBaseUrl}/trips/${foundTrip.id}`),
        (async () => {
          try {
            const s = await getDaysSummary(foundTrip.id);
            return s.data || null;
          } catch { return null; }
        })()
      ]);

      if (!tripResponse.ok) throw new Error(`Failed to fetch trip details: ${tripResponse.status}`);
      const tripData = await tripResponse.json();
      setTrip(tripData);

      if (summaryResp) {
        const locs = summaryResp.locations as DayLocationsSummary[];
        const map: Record<string, { start?: any; end?: any; route_total_km?: number; route_total_min?: number; route_coordinates?: [number, number][] }> = {};
        for (const l of locs) map[l.day_id] = {
          start: l.start || null,
          end: l.end || null,
          route_total_km: l.route_total_km ?? undefined,
          route_total_min: l.route_total_min ?? undefined,
          route_coordinates: l.route_coordinates ?? undefined,
        };
        setDayLocations(map);
      }
    } catch (err) {
      console.error('Error fetching trip details:', err);
      setError(err instanceof Error ? err.message : 'Failed to load trip details');
    } finally {
      setLoading(false);
    }
  };

  const handleDayClick = (day: Day) => {
    // Navigate to day detail page
    console.log('Navigate to day:', day.id);
    // In a real app: router.push(`/trips/${tripSlug}/days/${day.id}`)
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading trip details...</p>
        </div>
      </div>
    );
  }

  if (error || !trip) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Trip Not Found</h1>
          <p className="text-gray-600 mb-6">{error || 'The requested trip could not be found.'}</p>
          <Button asChild>
            <Link href="/trips">Back to Trips</Link>
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <Button variant="outline" size="sm" asChild>
                <Link href={`/trips/${trip.slug}`}>
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Trip
                </Link>
              </Button>
            </div>
            <DebugStatus />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">{trip.title}</h1>
          <p className="text-gray-600 mt-1">Plan your day-by-day itinerary</p>
        </div>

        {/* Days Management */}
        <DaysList
          trip={trip}
          onDayClick={handleDayClick}
          className="max-w-7xl"
          // Prefill locations so DaysList renders immediately
          // DaysList will still react to edits and refresh dayLocations internally
          // but this provides initial content for first paint
          prefilledLocations={dayLocations}
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
                <li>• Real-time API integration</li>
                <li>• Loading and error states</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-2">📅 Date Logic:</h4>
              <ul className="space-y-1">
                {trip.start_date ? (
                  <>
                    <li>• Day 1: {new Date(trip.start_date).toLocaleDateString()} (trip start)</li>
                    <li>• Day 2: {new Date(new Date(trip.start_date).getTime() + 24 * 60 * 60 * 1000).toLocaleDateString()} (start + 1 day)</li>
                    <li>• Day 3: {new Date(new Date(trip.start_date).getTime() + 2 * 24 * 60 * 60 * 1000).toLocaleDateString()} (start + 2 days)</li>
                  </>
                ) : (
                  <li>• Set a trip start date to see calculated day dates</li>
                )}
                <li>• Automatically updates when trip date changes</li>
                <li>• Handles trips without start dates</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Debug Panel */}
        <DebugPanel />
      </div>
    </div>
  );
}
