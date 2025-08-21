# Debug System

A comprehensive debugging system for monitoring API requests and responses during development.

## Features

### ✅ API Request/Response Monitoring
- **Real-time logging**: Captures all API calls with detailed information
- **Request details**: Method, URL, headers, body
- **Response details**: Status, headers, data, errors
- **Timing information**: Request/response timestamps and duration
- **Error tracking**: Network errors and API errors

### ✅ Debug Panel UI
- **Floating debug button**: Easy access from any page
- **Detailed API call list**: Chronological view of all API calls
- **Interactive dialogs**: Click to view full request/response details
- **Tabbed interface**: Organized view of request, response, and timing data
- **Status indicators**: Visual status codes and method badges

### ✅ Privacy & Security
- **Header sanitization**: Automatically masks sensitive headers (Authorization, API keys)
- **Local storage**: Debug state persisted across sessions
- **Development only**: Designed for development environment use

## Quick Start

### Basic Integration

```tsx
import { DebugPanel } from '@/components/debug';

function MyPage() {
  return (
    <div>
      {/* Your page content */}
      
      {/* Add debug panel */}
      <DebugPanel />
    </div>
  );
}
```

### Simple Debug Toggle

```tsx
import { DebugToggle } from '@/components/debug';

function Layout() {
  return (
    <div>
      {/* Your layout */}
      
      {/* Add debug toggle in corner */}
      <DebugToggle position="bottom-right" />
    </div>
  );
}
```

### Debug Status Indicator

```tsx
import { DebugStatus } from '@/components/debug';

function Header() {
  return (
    <header className="flex justify-between items-center">
      <h1>My App</h1>
      
      {/* Show debug status when enabled */}
      <DebugStatus />
    </header>
  );
}
```

## API Integration

The debug system automatically wraps your API calls when you use the enhanced fetch function:

```tsx
// In your API files, replace fetch with debugFetch
import { debugFetch } from '@/lib/debug';

async function fetchData() {
  // This will be automatically logged when debug mode is enabled
  const response = await debugFetch('/api/data', {
    method: 'GET',
    headers: { 'Authorization': 'Bearer token' }
  });
  
  return response.json();
}
```

### Existing API Integration

The Days API (`/lib/api/days.ts`) is already integrated with the debug system. All API calls will be automatically logged when debug mode is enabled.

## Debug Manager API

### Enable/Disable Debug Mode

```tsx
import { debugManager } from '@/lib/debug';

// Enable debug mode
debugManager.enable();

// Disable debug mode
debugManager.disable();

// Check if debug mode is enabled
const isEnabled = debugManager.isDebugEnabled();
```

### Manual Logging

```tsx
import { debugManager, generateApiId } from '@/lib/debug';

// Log a custom API request
const apiId = generateApiId();
debugManager.logRequest({
  id: apiId,
  timestamp: Date.now(),
  method: 'POST',
  url: '/api/custom',
  headers: { 'Content-Type': 'application/json' },
  body: { data: 'example' }
});

// Log the response
debugManager.logResponse({
  id: apiId,
  timestamp: Date.now(),
  status: 200,
  statusText: 'OK',
  headers: { 'Content-Type': 'application/json' },
  data: { result: 'success' },
  duration: 150
});
```

### Subscribe to API Calls

```tsx
import { debugManager } from '@/lib/debug';

function MyDebugComponent() {
  const [apiCalls, setApiCalls] = useState([]);

  useEffect(() => {
    // Subscribe to API call updates
    const unsubscribe = debugManager.subscribe((calls) => {
      setApiCalls(calls);
    });

    return unsubscribe;
  }, []);

  return (
    <div>
      <h3>API Calls: {apiCalls.length}</h3>
      {/* Render API calls */}
    </div>
  );
}
```

## Components

### DebugPanel

Full-featured debug panel with API call list and detailed views.

```tsx
<DebugPanel 
  className="custom-debug-panel" 
/>
```

**Props:**
- `className?: string` - Additional CSS classes

### DebugToggle

Simple toggle button for enabling/disabling debug mode.

```tsx
<DebugToggle 
  position="bottom-right"
  className="custom-toggle"
/>
```

**Props:**
- `position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left'` - Button position
- `className?: string` - Additional CSS classes

### DebugStatus

Status indicator showing when debug mode is active.

```tsx
<DebugStatus className="debug-status" />
```

**Props:**
- `className?: string` - Additional CSS classes

## Data Types

### ApiCall Structure

```typescript
interface ApiCall {
  id: string;
  request: ApiRequest;
  response?: ApiResponse;
  startTime: number;
  endTime?: number;
  duration?: number;
}

interface ApiRequest {
  id: string;
  timestamp: number;
  method: string;
  url: string;
  headers: Record<string, string>;
  body?: any;
}

interface ApiResponse {
  id: string;
  timestamp: number;
  status: number;
  statusText: string;
  headers: Record<string, string>;
  data?: any;
  error?: string;
  duration: number;
}
```

## Security Features

### Header Sanitization

Sensitive headers are automatically masked:

```typescript
// Original headers
{
  "Authorization": "Bearer abc123token",
  "X-API-Key": "secret-key",
  "Content-Type": "application/json"
}

// Sanitized for display
{
  "Authorization": "***************",
  "X-API-Key": "**********",
  "Content-Type": "application/json"
}
```

### Sensitive Headers List

The following headers are automatically sanitized:
- `authorization`
- `cookie`
- `x-api-key`

## Usage Examples

### Development Workflow

1. **Enable debug mode** using the toggle button
2. **Interact with your app** to generate API calls
3. **View API calls** in the debug panel
4. **Click on any call** to see detailed request/response data
5. **Use timing information** to identify slow requests
6. **Check error details** for failed requests

### Debugging API Issues

```tsx
// 1. Enable debug mode
debugManager.enable();

// 2. Make API calls through your app
// 3. Check the debug panel for:
//    - Request headers and body
//    - Response status and data
//    - Error messages
//    - Request timing

// 4. Use console logs for immediate feedback
// All API calls are also logged to the browser console
```

### Performance Monitoring

```tsx
// Monitor API performance
const slowCalls = debugManager.getApiCalls()
  .filter(call => call.duration && call.duration > 1000);

console.log('Slow API calls:', slowCalls);
```

## Best Practices

1. **Enable debug mode during development** to monitor all API interactions
2. **Use the debug panel** to inspect failed requests and responses
3. **Check timing information** to identify performance bottlenecks
4. **Clear API calls periodically** to avoid memory buildup during long sessions
5. **Disable debug mode in production** (it's designed for development only)

## Browser Console Integration

When debug mode is enabled, all API calls are also logged to the browser console with:
- 🚀 Request logs with method, URL, headers, and body
- 🟢 Successful response logs with status, data, and timing
- 🔴 Error response logs with error details
- 🟡 Warning logs for slow requests

## Dependencies

- React 18+
- Next.js 13+ (App Router)
- Tailwind CSS
- shadcn/ui components
- Lucide React icons

## Contributing

When adding new API endpoints:
1. Use `debugFetch` instead of regular `fetch`
2. Ensure sensitive headers are added to the sanitization list
3. Test debug logging in development
4. Update documentation with new API patterns
