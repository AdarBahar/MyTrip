/**
 * Debug System Demo Page
 * Demonstrates the debug system capabilities
 */

'use client';

import React, { useState } from 'react';
import { DebugPanel, DebugToggle, DebugStatus, ApiMonitor } from '@/components/debug';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { debugManager } from '@/lib/debug';
import { 
  Bug, 
  Play, 
  Zap, 
  AlertTriangle, 
  CheckCircle,
  Clock,
  Globe
} from 'lucide-react';

export default function DebugDemoPage() {
  const [isLoading, setIsLoading] = useState(false);

  // Simulate different types of API calls
  const simulateApiCall = async (type: 'success' | 'error' | 'slow') => {
    setIsLoading(true);
    
    const API_BASE = 'http://localhost:8000';
    
    try {
      switch (type) {
        case 'success':
          // Simulate a successful API call
          await fetch(`${API_BASE}/health`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer demo-token'
            }
          });
          break;
          
        case 'error':
          // Simulate an API error
          await fetch(`${API_BASE}/nonexistent-endpoint`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer demo-token'
            },
            body: JSON.stringify({ test: 'data' })
          });
          break;
          
        case 'slow':
          // Simulate a slow API call
          await new Promise(resolve => setTimeout(resolve, 2000));
          await fetch(`${API_BASE}/health`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json'
            }
          });
          break;
      }
    } catch (error) {
      console.log('Expected error for demo:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <Bug className="h-8 w-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">Debug System Demo</h1>
          </div>
          <DebugStatus />
        </div>
        <p className="text-gray-600">
          Explore the API debugging capabilities with interactive examples
        </p>
      </div>

      {/* Debug Controls */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Bug className="h-5 w-5" />
            <span>Debug Controls</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <h3 className="font-medium">Debug Mode Status</h3>
              <p className="text-sm text-gray-600">
                {debugManager.isDebugEnabled() 
                  ? 'Debug mode is enabled - API calls will be logged'
                  : 'Debug mode is disabled - Enable to see API logging'
                }
              </p>
            </div>
            <DebugToggle position="bottom-right" />
          </div>
          
          <div className="grid md:grid-cols-3 gap-4">
            <Button
              onClick={() => simulateApiCall('success')}
              disabled={isLoading}
              className="flex items-center space-x-2"
            >
              <CheckCircle className="h-4 w-4" />
              <span>Successful Request</span>
            </Button>
            
            <Button
              onClick={() => simulateApiCall('error')}
              disabled={isLoading}
              variant="destructive"
              className="flex items-center space-x-2"
            >
              <AlertTriangle className="h-4 w-4" />
              <span>Error Request</span>
            </Button>
            
            <Button
              onClick={() => simulateApiCall('slow')}
              disabled={isLoading}
              variant="outline"
              className="flex items-center space-x-2"
            >
              <Clock className="h-4 w-4" />
              <span>Slow Request</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* API Monitor */}
      <div className="mb-8">
        <ApiMonitor />
      </div>

      {/* Features Overview */}
      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Globe className="h-5 w-5" />
              <span>API Monitoring</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center space-x-2">
              <Badge variant="outline">Real-time</Badge>
              <span className="text-sm">Request/response logging</span>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant="outline">Timing</Badge>
              <span className="text-sm">Performance monitoring</span>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant="outline">Security</Badge>
              <span className="text-sm">Header sanitization</span>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant="outline">Errors</Badge>
              <span className="text-sm">Error tracking & details</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Zap className="h-5 w-5" />
              <span>Developer Tools</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center space-x-2">
              <Badge variant="outline">Console</Badge>
              <span className="text-sm">Browser console integration</span>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant="outline">UI</Badge>
              <span className="text-sm">Interactive debug panel</span>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant="outline">Persistent</Badge>
              <span className="text-sm">Settings saved across sessions</span>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant="outline">Non-intrusive</Badge>
              <span className="text-sm">Zero impact on production</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Instructions */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Play className="h-5 w-5" />
            <span>How to Use</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div className="flex items-start space-x-3">
              <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                1
              </div>
              <div>
                <h4 className="font-medium">Enable Debug Mode</h4>
                <p className="text-sm text-gray-600">
                  Click the debug toggle button to enable API monitoring
                </p>
              </div>
            </div>
            
            <div className="flex items-start space-x-3">
              <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                2
              </div>
              <div>
                <h4 className="font-medium">Make API Calls</h4>
                <p className="text-sm text-gray-600">
                  Use the buttons above to simulate different types of API requests
                </p>
              </div>
            </div>
            
            <div className="flex items-start space-x-3">
              <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                3
              </div>
              <div>
                <h4 className="font-medium">View Debug Panel</h4>
                <p className="text-sm text-gray-600">
                  Click the debug button in the bottom-right corner to see API call details
                </p>
              </div>
            </div>
            
            <div className="flex items-start space-x-3">
              <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                4
              </div>
              <div>
                <h4 className="font-medium">Inspect Details</h4>
                <p className="text-sm text-gray-600">
                  Click on any API call to see detailed request/response information
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Integration Example */}
      <Card>
        <CardHeader>
          <CardTitle>Integration Example</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="bg-gray-100 p-4 rounded-lg text-sm overflow-auto">
{`// Add to any page
import { DebugPanel } from '@/components/debug';

function MyPage() {
  return (
    <div>
      {/* Your page content */}
      
      {/* Add debug panel */}
      <DebugPanel />
    </div>
  );
}`}
          </pre>
        </CardContent>
      </Card>

      {/* Debug Panel */}
      <DebugPanel />
    </div>
  );
}
