# 🎯 **UI Route Optimization Integration Prompt**

You are a senior frontend developer building a React/TypeScript trip planning application. Implement a route optimization feature that takes daily trip data (start, stops, end) and optimizes it using the `/routing/optimize` endpoint.

## 📋 **Context & Requirements**

### **Data Structure Understanding**
Your app has this data hierarchy:
- **Trip** → **Days** → **Stops** → **Places**
- Each **Day** has multiple **Stops** with sequence numbers
- Each **Stop** references a **Place** (with lat/lon coordinates)
- Stop types: `start` (seq=1, fixed), `via` (flexible stops), `end` (last, fixed)

### **API Endpoint**
- **URL**: `POST /routing/optimize`
- **Auth**: Bearer JWT token required
- **Purpose**: Optimize stop order using TSP algorithms with real road routing

## 🔄 **Data Transformation Required**

### **Input: Day with Stops**
```typescript
interface DayWithStops {
  id: string;
  trip_id: string;
  seq: number;
  stops: Stop[];
}

interface Stop {
  id: string;
  place_id: string;
  seq: number;
  kind: 'start' | 'via' | 'end';
  fixed: boolean;
  place: {
    id: string;
    name: string;
    address?: string;
    lat: number;
    lon: number; // Note: backend uses "lon", API expects "lng"
  };
}
```

### **Output: Optimization Request**
```typescript
interface OptimizationRequest {
  prompt?: string;
  meta: {
    version: "1.0";
    objective: "time" | "distance";
    vehicle_profile: "car" | "bike" | "foot";
    units: "metric" | "imperial";
    avoid?: ("tolls" | "ferries" | "highways")[];
  };
  data: {
    locations: OptimizationLocation[];
  };
}

interface OptimizationLocation {
  id: string;
  type: "START" | "STOP" | "END";
  name: string;
  lat: number;
  lng: number; // Note: API uses "lng"
  fixed_seq: boolean;
  seq?: number; // Required if fixed_seq=true for STOP
}
```

## 🛠 **Implementation Requirements**

### **1. Data Transformation Function**
```typescript
function transformDayToOptimizationRequest(
  day: DayWithStops,
  options: {
    objective?: 'time' | 'distance';
    vehicleProfile?: 'car' | 'bike' | 'foot';
    avoid?: ('tolls' | 'ferries' | 'highways')[];
    prompt?: string;
  } = {}
): OptimizationRequest {
  // Transform stops to optimization locations
  // Handle coordinate conversion (lon → lng)
  // Map stop kinds: start→START, via→STOP, end→END
  // Preserve fixed sequences
  // Sort by sequence number
}
```

### **2. API Integration Hook**
```typescript
interface UseRouteOptimizationResult {
  optimizeRoute: (day: DayWithStops, options?: OptimizationOptions) => Promise<void>;
  isLoading: boolean;
  result: OptimizationResponse | null;
  error: string | null;
  clearResult: () => void;
}

function useRouteOptimization(): UseRouteOptimizationResult {
  // Handle API calls with proper error handling
  // Manage loading states
  // Parse and validate responses
  // Handle different error types (400, 422, 500)
}
```

### **3. React Component**
```typescript
interface RouteOptimizerProps {
  day: DayWithStops;
  onOptimizationAccepted: (optimizedStops: Stop[]) => Promise<void>;
  onOptimizationRejected: () => void;
}

function RouteOptimizer({ day, onOptimizationAccepted, onOptimizationRejected }: RouteOptimizerProps) {
  // Component implementation with:
  // - Optimization trigger button
  // - Loading states with progress indicators
  // - Results display with before/after comparison
  // - Accept/Reject actions
  // - Error handling with user-friendly messages
}
```

## 🎨 **UI/UX Requirements**

### **Optimization Trigger**
- **Button**: "Optimize Route" with route icon
- **Tooltip**: "Reorder stops for minimum travel time"
- **Disabled states**: When < 3 stops or already optimizing
- **Loading state**: Spinner with "Optimizing route..." text

### **Options Panel** (Optional)
```typescript
interface OptimizationOptions {
  objective: 'time' | 'distance';
  vehicleProfile: 'car' | 'bike' | 'foot';
  avoid: ('tolls' | 'ferries' | 'highways')[];
  prompt?: string;
}
```

### **Results Display**
- **Before/After comparison**: Side-by-side stop lists
- **Metrics**: Total distance, duration, savings
- **Route visualization**: Map with optimized path
- **Stop reordering**: Clear indication of which stops moved
- **Actions**: "Accept Changes" and "Keep Original" buttons

### **Error Handling**
```typescript
interface ErrorDisplay {
  // 400 Bad Request: Schema validation errors
  validationErrors: string[];

  // 422 Unprocessable: Unroutable locations
  routingErrors: string[];

  // Network/Server errors
  systemErrors: string[];

  // User-friendly suggestions
  suggestions: string[];
}
```

## 📡 **API Integration Details**

### **Request Headers**
```typescript
const headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'Authorization': `Bearer ${authToken}`,
};
```

### **Error Response Handling**
```typescript
interface ApiErrorResponse {
  version: string;
  errors: Array<{
    code: string;
    message: string;
  }>;
}

// Handle specific error codes:
// - MULTIPLE_START: More than one start location
// - MISSING_END: No end location provided
// - FIXED_CONFLICT: Conflicting fixed sequences
// - DISCONNECTED_GRAPH: Locations not routable
```

### **Success Response Processing**
```typescript
interface OptimizationResponse {
  version: string;
  objective: string;
  units: string;
  ordered: OptimizedLocation[];
  summary: {
    stop_count: number;
    total_distance_km: number;
    total_duration_min: number;
  };
  geometry: {
    format: "geojson";
    route: {
      type: "LineString";
      coordinates: [number, number][]; // [lng, lat]
    };
    bounds: {
      min_lat: number;
      min_lng: number;
      max_lat: number;
      max_lng: number;
    };
  };
  diagnostics: {
    warnings: string[];
    assumptions: string[];
    computation_notes: string[];
  };
}
```

## 🔄 **Data Flow & State Management**

### **1. Optimization Flow**
```typescript
const handleOptimizeRoute = async () => {
  try {
    setIsLoading(true);
    setError(null);

    // Transform day data to optimization request
    const request = transformDayToOptimizationRequest(day, options);

    // Call optimization API
    const response = await fetch('/routing/optimize', {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      // Handle error responses
      const errorData = await response.json();
      throw new OptimizationError(errorData);
    }

    const result = await response.json();
    setResult(result);

    // Show results to user for approval

  } catch (error) {
    setError(handleOptimizationError(error));
  } finally {
    setIsLoading(false);
  }
};
```

### **2. Result Processing**
```typescript
const transformOptimizationResult = (
  result: OptimizationResponse,
  originalStops: Stop[]
): Stop[] => {
  // Map optimized locations back to stop objects
  // Preserve stop IDs and other metadata
  // Update sequence numbers based on optimization
  // Return reordered stops array
};
```

### **3. Backend Updates**
```typescript
const applyOptimization = async (optimizedStops: Stop[]) => {
  try {
    // Update stop sequences in backend
    await updateStopsOrder(day.id, optimizedStops);

    // Update local state
    onOptimizationAccepted(optimizedStops);

    // Show success message
    showNotification('Route optimized successfully!');

  } catch (error) {
    showNotification('Failed to save optimization', 'error');
  }
};
```

## 🎯 **Component Structure**

```typescript
function RouteOptimizer({ day, onOptimizationAccepted, onOptimizationRejected }: RouteOptimizerProps) {
  const { optimizeRoute, isLoading, result, error, clearResult } = useRouteOptimization();
  const [options, setOptions] = useState<OptimizationOptions>(defaultOptions);
  const [showResults, setShowResults] = useState(false);

  return (
    <div className="route-optimizer">
      {/* Optimization Trigger */}
      <OptimizationTrigger
        onOptimize={() => optimizeRoute(day, options)}
        disabled={isLoading || day.stops.length < 3}
        isLoading={isLoading}
      />

      {/* Options Panel */}
      <OptimizationOptions
        options={options}
        onChange={setOptions}
        collapsed={!showAdvanced}
      />

      {/* Loading State */}
      {isLoading && <OptimizationProgress />}

      {/* Error Display */}
      {error && <ErrorDisplay error={error} onRetry={() => optimizeRoute(day, options)} />}

      {/* Results Display */}
      {result && (
        <OptimizationResults
          original={day.stops}
          optimized={result}
          onAccept={() => applyOptimization(result)}
          onReject={() => clearResult()}
        />
      )}
    </div>
  );
}
```

## ✅ **Acceptance Criteria**

1. **✅ Data Transformation**: Correctly converts day/stops to optimization format
2. **✅ API Integration**: Handles all response types (200, 400, 422, 500)
3. **✅ Loading States**: Shows progress during optimization
4. **✅ Error Handling**: User-friendly error messages with retry options
5. **✅ Results Display**: Clear before/after comparison with metrics
6. **✅ User Actions**: Accept/reject optimization with backend updates
7. **✅ Accessibility**: Keyboard navigation, screen reader support
8. **✅ Performance**: Debounced requests, efficient re-renders
9. **✅ TypeScript**: Full type safety with proper interfaces
10. **✅ Testing**: Unit tests for transformation and API integration

## 🚀 **Implementation Notes**

- **Coordinate Conversion**: Backend uses `lon`, API expects `lng`
- **Sequence Preservation**: Fixed stops maintain their positions
- **Error Recovery**: Allow retry with different options
- **Optimistic Updates**: Show results immediately, rollback on failure
- **Caching**: Cache optimization results for same input
- **Analytics**: Track optimization usage and success rates

Build a production-ready feature that provides excellent user experience while handling all edge cases gracefully!
