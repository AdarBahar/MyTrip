/**
 * Minimal Debug System
 * No external dependencies, just basic React and inline styles
 */

'use client';

import React, { useState, useEffect } from 'react';

// Simple debug manager without external dependencies
class SimpleDebugManager {
  private static instance: SimpleDebugManager;
  private isEnabled: boolean = false;
  private apiCalls: any[] = [];
  private listeners: Set<(calls: any[]) => void> = new Set();

  static getInstance(): SimpleDebugManager {
    if (!SimpleDebugManager.instance) {
      SimpleDebugManager.instance = new SimpleDebugManager();
    }
    return SimpleDebugManager.instance;
  }

  enable(): void {
    this.isEnabled = true;
    if (typeof window !== 'undefined') {
      localStorage.setItem('debug_mode', 'true');
    }
    console.log('🐛 Debug mode ENABLED');
  }

  disable(): void {
    this.isEnabled = false;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('debug_mode');
    }
    console.log('🐛 Debug mode DISABLED');
  }

  isDebugEnabled(): boolean {
    if (typeof window === 'undefined') return false;
    return this.isEnabled || localStorage.getItem('debug_mode') === 'true';
  }

  logApiCall(method: string, url: string, status?: number, duration?: number): void {
    if (!this.isDebugEnabled()) return;

    const call = {
      id: Date.now() + Math.random(),
      method,
      url,
      status,
      duration,
      timestamp: new Date().toISOString()
    };

    this.apiCalls.unshift(call);
    if (this.apiCalls.length > 50) {
      this.apiCalls = this.apiCalls.slice(0, 50);
    }

    this.notifyListeners();
    console.log(`🚀 API ${method} ${url}${status ? ` - ${status}` : ''}${duration ? ` (${duration}ms)` : ''}`);
  }

  getApiCalls(): any[] {
    return this.apiCalls;
  }

  clearApiCalls(): void {
    this.apiCalls = [];
    this.notifyListeners();
  }

  subscribe(listener: (calls: any[]) => void): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => listener(this.apiCalls));
  }
}

const simpleDebugManager = SimpleDebugManager.getInstance();

// Export for use in other components
export { simpleDebugManager };

/**
 * Minimal Debug Toggle
 */
export function MinimalDebugToggle() {
  const [isEnabled, setIsEnabled] = useState(false);
  const [apiCallCount, setApiCallCount] = useState(0);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setIsEnabled(simpleDebugManager.isDebugEnabled());
    setApiCallCount(simpleDebugManager.getApiCalls().length);

    const unsubscribe = simpleDebugManager.subscribe((calls) => {
      setApiCallCount(calls.length);
    });

    return unsubscribe;
  }, []);

  const toggleDebug = () => {
    if (isEnabled) {
      simpleDebugManager.disable();
      setIsEnabled(false);
    } else {
      simpleDebugManager.enable();
      setIsEnabled(true);
    }
  };

  const testApiCall = () => {
    simpleDebugManager.logApiCall('GET', '/test/endpoint', 200, 150);
  };

  if (!mounted) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: '10px',
        right: '10px',
        zIndex: 99999,
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}
    >
      {/* Main toggle button */}
      <div
        onClick={toggleDebug}
        style={{
          backgroundColor: isEnabled ? '#10b981' : '#ef4444',
          color: 'white',
          padding: '8px 12px',
          borderRadius: '6px',
          cursor: 'pointer',
          fontSize: '12px',
          fontWeight: 'bold',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)',
          border: '2px solid white',
          userSelect: 'none',
          marginBottom: '5px'
        }}
        title="Click to toggle debug mode"
      >
        🐛 {isEnabled ? 'DEBUG ON' : 'DEBUG OFF'}
        {apiCallCount > 0 && ` (${apiCallCount})`}
      </div>

      {/* Test button */}
      {isEnabled && (
        <div
          onClick={testApiCall}
          style={{
            backgroundColor: '#3b82f6',
            color: 'white',
            padding: '4px 8px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '10px',
            fontWeight: 'bold',
            textAlign: 'center',
            userSelect: 'none'
          }}
          title="Test API call logging"
        >
          TEST API
        </div>
      )}
    </div>
  );
}

/**
 * Minimal Debug Panel
 */
export function MinimalDebugPanel() {
  const [isEnabled, setIsEnabled] = useState(false);
  const [apiCalls, setApiCalls] = useState<any[]>([]);
  const [showPanel, setShowPanel] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setIsEnabled(simpleDebugManager.isDebugEnabled());
    setApiCalls(simpleDebugManager.getApiCalls());

    const unsubscribe = simpleDebugManager.subscribe((calls) => {
      setApiCalls(calls);
    });

    return unsubscribe;
  }, []);

  if (!mounted || !isEnabled) return null;

  return (
    <>
      {/* Panel toggle button */}
      <div
        onClick={() => setShowPanel(!showPanel)}
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          zIndex: 99998,
          backgroundColor: '#1f2937',
          color: 'white',
          padding: '10px 15px',
          borderRadius: '8px',
          cursor: 'pointer',
          fontSize: '14px',
          fontWeight: 'bold',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          fontFamily: 'system-ui, -apple-system, sans-serif'
        }}
      >
        🐛 Debug Panel ({apiCalls.length})
      </div>

      {/* Debug panel */}
      {showPanel && (
        <div
          style={{
            position: 'fixed',
            bottom: '80px',
            right: '20px',
            width: '400px',
            maxHeight: '500px',
            backgroundColor: 'white',
            border: '1px solid #ccc',
            borderRadius: '8px',
            boxShadow: '0 10px 25px rgba(0, 0, 0, 0.2)',
            zIndex: 99997,
            fontFamily: 'system-ui, -apple-system, sans-serif',
            overflow: 'hidden'
          }}
        >
          {/* Header */}
          <div
            style={{
              backgroundColor: '#1f2937',
              color: 'white',
              padding: '10px 15px',
              fontSize: '14px',
              fontWeight: 'bold',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
          >
            <span>API Calls ({apiCalls.length})</span>
            <div>
              <button
                onClick={() => simpleDebugManager.clearApiCalls()}
                style={{
                  backgroundColor: '#ef4444',
                  color: 'white',
                  border: 'none',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '10px',
                  cursor: 'pointer',
                  marginRight: '5px'
                }}
              >
                Clear
              </button>
              <button
                onClick={() => setShowPanel(false)}
                style={{
                  backgroundColor: '#6b7280',
                  color: 'white',
                  border: 'none',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '10px',
                  cursor: 'pointer'
                }}
              >
                ✕
              </button>
            </div>
          </div>

          {/* API calls list */}
          <div
            style={{
              maxHeight: '400px',
              overflowY: 'auto',
              padding: '10px'
            }}
          >
            {apiCalls.length === 0 ? (
              <div style={{ textAlign: 'center', color: '#6b7280', padding: '20px' }}>
                No API calls yet
              </div>
            ) : (
              apiCalls.map((call) => (
                <div
                  key={call.id}
                  style={{
                    padding: '8px',
                    marginBottom: '5px',
                    backgroundColor: '#f9f9f9',
                    borderRadius: '4px',
                    fontSize: '12px',
                    borderLeft: `3px solid ${
                      call.status >= 400 ? '#ef4444' : 
                      call.status >= 300 ? '#f59e0b' : 
                      call.status >= 200 ? '#10b981' : '#6b7280'
                    }`
                  }}
                >
                  <div style={{ fontWeight: 'bold', marginBottom: '2px' }}>
                    <span
                      style={{
                        backgroundColor: 
                          call.method === 'GET' ? '#3b82f6' :
                          call.method === 'POST' ? '#10b981' :
                          call.method === 'PUT' ? '#f59e0b' :
                          call.method === 'DELETE' ? '#ef4444' : '#6b7280',
                        color: 'white',
                        padding: '2px 6px',
                        borderRadius: '3px',
                        fontSize: '10px',
                        marginRight: '8px'
                      }}
                    >
                      {call.method}
                    </span>
                    {call.url}
                  </div>
                  <div style={{ color: '#6b7280', fontSize: '10px' }}>
                    {call.status && `Status: ${call.status}`}
                    {call.duration && ` • Duration: ${call.duration}ms`}
                    {` • ${new Date(call.timestamp).toLocaleTimeString()}`}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </>
  );
}

/**
 * Minimal Debug Status
 */
export function MinimalDebugStatus() {
  const [isEnabled, setIsEnabled] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setIsEnabled(simpleDebugManager.isDebugEnabled());
  }, []);

  if (!mounted || !isEnabled) return null;

  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '8px',
        padding: '4px 8px',
        backgroundColor: '#10b981',
        color: 'white',
        borderRadius: '4px',
        fontSize: '12px',
        fontWeight: 'bold'
      }}
    >
      🐛 DEBUG ACTIVE
    </div>
  );
}
