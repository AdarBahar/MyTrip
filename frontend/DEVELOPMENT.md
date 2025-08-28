# Development Guide

This guide covers the development tools and debugging features available in the MyTrip application.

## Debug System Overview

The application includes a comprehensive debug system for monitoring API interactions, performance, and troubleshooting during development.

### ✅ Integrated Pages

The debug system is now integrated across all major pages:

#### **Global Integration**
- **Root Layout**: DebugPanel and DevIndicator available on all pages
- **Development Indicator**: Shows DEV/DEBUG badges in top-right corner
- **API Monitoring**: Real-time API call tracking and performance metrics

#### **Page-Specific Integration**
- **Login Page** (`/login`): Debug status indicator, API call monitoring for authentication
- **Trips List** (`/trips`): Debug status in header, monitors trip fetching APIs
- **Trip Detail** (`/trips/[slug]`): Debug status, monitors trip data and updates
- **Days Management** (`/trips/[slug]/days`): Full debug integration with Days API monitoring
- **Debug Demo** (`/debug-demo`): Interactive demonstration of all debug features

### 🔧 Debug Features Available

#### **1. API Request/Response Monitoring**
```typescript
// All API calls are automatically logged when debug mode is enabled
const response = await fetchWithAuth('/api/trips');
// Logs: Request headers, body, timing
// Logs: Response status, data, duration
```

#### **2. Real-time Performance Monitoring**
- Request duration tracking
- Average response time calculation
- Slow request identification (>1000ms)
- Error rate monitoring

#### **3. Development Environment Indicators**
- **DEV Badge**: Shows when running in development mode
- **DEBUG Badge**: Shows when debug mode is active
- **API Counter**: Shows number of API calls made
- **Performance Metrics**: Average response time, error count

#### **4. Interactive Debug Panel**
- Floating debug button with API call counter
- Detailed request/response inspection
- Tabbed interface for request, response, and timing data
- Status indicators and method badges

## How to Use During Development

### **1. Enable Debug Mode**

**Option A: Use the Development Indicator**
- Look for the DEV/DEBUG badges in the top-right corner
- Click the eye icon to enable/disable debug mode

**Option B: Use the Debug Panel**
- Click the "Debug" button (usually bottom-right)
- Click "Enable Debug Mode" in the panel

**Option C: Programmatically**
```typescript
import { debugManager } from '@/lib/debug';

// Enable debug mode
debugManager.enable();

// Disable debug mode
debugManager.disable();

// Check if enabled
const isEnabled = debugManager.isDebugEnabled();
```

### **2. Monitor API Interactions**

Once debug mode is enabled:

1. **Real-time Console Logging**
   ```
   🚀 API Request: POST /trips/123/days
     Request ID: api_1692622800000_abc123
     Headers: {...}
     Body: {...}

   🟢 API Response: 201 Created (150ms)
     Request ID: api_1692622800000_abc123
     Data: {...}
   ```

2. **Debug Panel Interface**
   - Click the debug button to see all API calls
   - Click any API call for detailed inspection
   - View request/response data, headers, timing

3. **API Monitor Widget**
   - Shows real-time statistics (success, errors, pending)
   - Displays recent API activity
   - Performance metrics and trends

### **3. Debug API Issues**

#### **Identify Failed Requests**
- Red status indicators show failed requests
- Error details available in debug panel
- Console logs show error messages and stack traces

#### **Performance Bottlenecks**
- Yellow indicators show slow requests (>1000ms)
- Average response time displayed in monitor
- Duration tracking for all requests

#### **Authentication Issues**
- Authorization headers are masked for security
- Login/logout API calls are tracked
- Token refresh attempts are logged

### **4. Development Workflow**

#### **Daily Development**
1. Start the development server
2. Enable debug mode using the indicator
3. Interact with the application normally
4. Monitor API calls in real-time
5. Use debug panel to investigate issues

#### **Debugging Specific Issues**
1. Reproduce the issue with debug mode enabled
2. Check the debug panel for failed requests
3. Inspect request/response data
4. Look for timing issues or error patterns
5. Use console logs for immediate feedback

#### **Performance Testing**
1. Enable debug mode
2. Perform typical user workflows
3. Monitor average response times
4. Identify slow requests
5. Check for error patterns

## API Integration

### **Automatic Integration**

All API calls are automatically logged when using:
- `fetchWithAuth()` - For authenticated requests
- `debugFetch()` - For general requests (in Days API)

### **Manual Integration**

For custom API calls:
```typescript
import { debugManager, generateApiId, extractHeaders, sanitizeHeaders } from '@/lib/debug';

async function customApiCall() {
  const apiId = generateApiId();
  const startTime = Date.now();
  
  // Log request
  debugManager.logRequest({
    id: apiId,
    timestamp: startTime,
    method: 'POST',
    url: '/api/custom',
    headers: sanitizeHeaders({ 'Content-Type': 'application/json' }),
    body: { data: 'example' }
  });

  try {
    const response = await fetch('/api/custom', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: 'example' })
    });

    const endTime = Date.now();
    const data = await response.json();

    // Log response
    debugManager.logResponse({
      id: apiId,
      timestamp: endTime,
      status: response.status,
      statusText: response.statusText,
      headers: sanitizeHeaders(extractHeaders(response.headers)),
      data,
      duration: endTime - startTime
    });

    return data;
  } catch (error) {
    // Log error
    debugManager.logResponse({
      id: apiId,
      timestamp: Date.now(),
      status: 0,
      statusText: 'Network Error',
      headers: {},
      error: error.message,
      duration: Date.now() - startTime
    });
    throw error;
  }
}
```

## Security Features

### **Header Sanitization**
Sensitive headers are automatically masked:
- `Authorization`: `Bearer ***************`
- `Cookie`: `***************`
- `X-API-Key`: `***************`

### **Development Only**
- Debug features are designed for development
- No sensitive data exposure in production
- Debug state is stored locally only

## Components Reference

### **DebugPanel**
Full-featured debug interface with API call list and detailed views.
```tsx
<DebugPanel />
```

### **DevIndicator**
Development environment indicator with debug toggle.
```tsx
<DevIndicator position="top-right" showApiCount={true} />
```

### **ApiMonitor**
Real-time API monitoring widget with statistics.
```tsx
<ApiMonitor maxItems={10} />
```

### **DebugStatus**
Simple debug status indicator for headers.
```tsx
<DebugStatus />
```

### **PerformanceMonitor**
Performance metrics display.
```tsx
<PerformanceMonitor />
```

## Best Practices

1. **Always enable debug mode during development**
2. **Monitor API calls when implementing new features**
3. **Check performance metrics regularly**
4. **Use debug panel to investigate issues**
5. **Clear API call history periodically during long sessions**
6. **Disable debug mode when not needed to reduce overhead**

## Troubleshooting

### **Debug Mode Not Working**
- Check browser console for errors
- Verify localStorage permissions
- Try refreshing the page

### **API Calls Not Appearing**
- Ensure debug mode is enabled
- Check that API calls use `fetchWithAuth` or `debugFetch`
- Verify network connectivity

### **Performance Issues**
- Clear API call history if too many calls are stored
- Disable debug mode when not needed
- Check for memory leaks in long-running sessions

## Demo and Testing

Visit `/debug-demo` for an interactive demonstration of all debug features:
- Enable/disable debug mode
- Simulate different types of API calls
- Explore the debug panel interface
- Learn about integration patterns
