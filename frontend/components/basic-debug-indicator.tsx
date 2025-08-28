/**
 * Basic Debug Indicator
 * Simple component with minimal dependencies
 */

'use client';

import React, { useState, useEffect } from 'react';

export function BasicDebugIndicator() {
  const [debugEnabled, setDebugEnabled] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    
    // Check if debug mode is enabled
    if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
      const stored = localStorage.getItem('debug_mode');
      setDebugEnabled(stored === 'true');
    }
  }, []);

  const toggleDebug = () => {
    if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
      const newState = !debugEnabled;
      setDebugEnabled(newState);
      
      if (newState) {
        localStorage.setItem('debug_mode', 'true');
        console.log('🐛 Debug mode ENABLED');
      } else {
        localStorage.removeItem('debug_mode');
        console.log('🐛 Debug mode DISABLED');
      }
    }
  };

  // Don't render on server side
  if (!mounted) {
    return null;
  }

  return (
    <>
      {/* Always visible debug toggle */}
      <div
        onClick={toggleDebug}
        style={{
          position: 'fixed',
          top: '10px',
          right: '10px',
          zIndex: 99999,
          backgroundColor: debugEnabled ? '#10b981' : '#ef4444',
          color: 'white',
          padding: '8px 12px',
          borderRadius: '6px',
          cursor: 'pointer',
          fontSize: '12px',
          fontWeight: 'bold',
          fontFamily: 'system-ui, -apple-system, sans-serif',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)',
          border: '2px solid white',
          userSelect: 'none'
        }}
        title="Click to toggle debug mode"
      >
        🐛 {debugEnabled ? 'DEBUG ON' : 'DEBUG OFF'}
      </div>

      {/* Debug status indicator */}
      {debugEnabled && (
        <div
          style={{
            position: 'fixed',
            top: '50px',
            right: '10px',
            zIndex: 99998,
            backgroundColor: '#1f2937',
            color: '#10b981',
            padding: '6px 10px',
            borderRadius: '4px',
            fontSize: '11px',
            fontFamily: 'system-ui, -apple-system, sans-serif',
            boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
            border: '1px solid #10b981'
          }}
        >
          DEBUG MODE ACTIVE
        </div>
      )}

      {/* Console message */}
      {mounted && (
        <script
          dangerouslySetInnerHTML={{
            __html: `
              console.log('🐛 Basic Debug Indicator loaded');
              console.log('🐛 Look for debug toggle in top-right corner');
              console.log('🐛 Current debug state: ${debugEnabled}');
            `
          }}
        />
      )}
    </>
  );
}
