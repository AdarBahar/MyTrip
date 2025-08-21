/**
 * Simple Debug Toggle
 * A very basic, highly visible debug toggle for testing
 */

'use client';

import React, { useState, useEffect } from 'react';
import { debugManager } from '@/lib/debug';

export function SimpleDebugToggle() {
  const [isEnabled, setIsEnabled] = useState(false);
  const [apiCallCount, setApiCallCount] = useState(0);

  useEffect(() => {
    setIsEnabled(debugManager.isDebugEnabled());
    setApiCallCount(debugManager.getApiCalls().length);

    const unsubscribe = debugManager.subscribe((calls) => {
      setApiCallCount(calls.length);
    });

    return unsubscribe;
  }, []);

  const toggleDebug = () => {
    if (isEnabled) {
      debugManager.disable();
      setIsEnabled(false);
    } else {
      debugManager.enable();
      setIsEnabled(true);
    }
  };

  return (
    <div 
      style={{
        position: 'fixed',
        top: '20px',
        right: '20px',
        zIndex: 9999,
        backgroundColor: isEnabled ? '#10b981' : '#6b7280',
        color: 'white',
        padding: '12px 16px',
        borderRadius: '8px',
        cursor: 'pointer',
        fontFamily: 'system-ui, sans-serif',
        fontSize: '14px',
        fontWeight: '600',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        border: '2px solid white'
      }}
      onClick={toggleDebug}
    >
      🐛 DEBUG {isEnabled ? 'ON' : 'OFF'}
      {apiCallCount > 0 && ` (${apiCallCount})`}
    </div>
  );
}

/**
 * Simple Debug Status
 * Shows debug status inline
 */
export function SimpleDebugStatus() {
  const [isEnabled, setIsEnabled] = useState(false);
  const [apiCallCount, setApiCallCount] = useState(0);

  useEffect(() => {
    setIsEnabled(debugManager.isDebugEnabled());
    setApiCallCount(debugManager.getApiCalls().length);

    const unsubscribe = debugManager.subscribe((calls) => {
      setApiCallCount(calls.length);
    });

    return unsubscribe;
  }, []);

  if (!isEnabled) return null;

  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '8px',
      padding: '4px 8px',
      backgroundColor: '#10b981',
      color: 'white',
      borderRadius: '4px',
      fontSize: '12px',
      fontWeight: '600'
    }}>
      🐛 DEBUG ACTIVE
      {apiCallCount > 0 && <span>({apiCallCount} calls)</span>}
    </div>
  );
}
