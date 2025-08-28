/**
 * Debug Test Page
 * Simple page to test debug functionality
 */

'use client';

import React, { useState, useEffect } from 'react';
import { debugManager } from '@/lib/debug';
import { runAllDebugTests } from '@/lib/debug-test';
import { DebugPanel, DebugToggle, DebugStatus, DevIndicator } from '@/components/debug';
import { SimpleDebugStatus } from '@/components/debug/simple-debug-toggle';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function DebugTestPage() {
  const [isDebugEnabled, setIsDebugEnabled] = useState(false);
  const [apiCallCount, setApiCallCount] = useState(0);
  const [testResults, setTestResults] = useState<any>(null);

  useEffect(() => {
    // Check debug status
    setIsDebugEnabled(debugManager.isDebugEnabled());
    setApiCallCount(debugManager.getApiCalls().length);

    // Subscribe to changes
    const unsubscribe = debugManager.subscribe((calls) => {
      setApiCallCount(calls.length);
    });

    return unsubscribe;
  }, []);

  const testApiCall = async () => {
    try {
      // Make a simple API call to test debug logging
      const response = await fetch('/api/health', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      console.log('Test API call made:', response.status);
    } catch (error) {
      console.log('Test API call failed (expected):', error);
    }
  };

  const toggleDebug = () => {
    if (isDebugEnabled) {
      debugManager.disable();
      setIsDebugEnabled(false);
    } else {
      debugManager.enable();
      setIsDebugEnabled(true);
    }
  };

  const runTests = () => {
    const results = runAllDebugTests();
    setTestResults(results);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center space-x-4 mb-8">
        <h1 className="text-3xl font-bold">Debug System Test</h1>
        <SimpleDebugStatus />
      </div>
      
      {/* Debug Status */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Debug Status</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Debug Enabled:</p>
              <p className="font-bold">{isDebugEnabled ? 'YES' : 'NO'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">API Calls:</p>
              <p className="font-bold">{apiCallCount}</p>
            </div>
          </div>
          
          <div className="flex space-x-4">
            <Button onClick={toggleDebug}>
              {isDebugEnabled ? 'Disable Debug' : 'Enable Debug'}
            </Button>
            <Button onClick={testApiCall} variant="outline">
              Test API Call
            </Button>
            <Button onClick={runTests} variant="secondary">
              Run Debug Tests
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Test Results */}
      {testResults && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Test Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Overall Status:</p>
                  <p className={`font-bold ${testResults.overall ? 'text-green-600' : 'text-red-600'}`}>
                    {testResults.overall ? 'PASS' : 'FAIL'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Environment:</p>
                  <p className="font-bold">
                    {testResults.environment.isDevelopment ? 'Development' : 'Production'}
                  </p>
                </div>
              </div>

              <div className="text-sm">
                <p><strong>Client-side:</strong> {testResults.environment.isClient ? '✅' : '❌'}</p>
                <p><strong>localStorage:</strong> {testResults.localStorage.isAvailable ? '✅' : '❌'}</p>
                <p><strong>Debug Manager:</strong> {testResults.debugManager.isWorking ? '✅' : '❌'}</p>
              </div>

              <pre className="bg-gray-100 p-3 rounded text-xs overflow-auto">
                {JSON.stringify(testResults, null, 2)}
              </pre>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Debug Components Test */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Debug Components</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-sm text-gray-600 mb-2">DebugStatus Component:</p>
            <DebugStatus />
          </div>
          
          <div>
            <p className="text-sm text-gray-600 mb-2">DebugToggle Component:</p>
            <DebugToggle position="bottom-left" />
          </div>
        </CardContent>
      </Card>

      {/* Instructions */}
      <Card>
        <CardHeader>
          <CardTitle>How to Test</CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="list-decimal list-inside space-y-2">
            <li>Click "Enable Debug" button above</li>
            <li>Look for debug indicators in the top-right corner of the page</li>
            <li>Click "Test API Call" to generate some API activity</li>
            <li>Look for a floating "Debug" button (usually bottom-right)</li>
            <li>Click the Debug button to see the debug panel</li>
            <li>Check browser console for debug logs</li>
          </ol>
        </CardContent>
      </Card>

      {/* Note: DebugPanel and DevIndicator are in the layout, so they should appear globally */}
    </div>
  );
}
