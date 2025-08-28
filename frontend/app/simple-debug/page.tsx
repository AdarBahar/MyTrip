/**
 * Simple Debug Test Page
 * Basic test without complex imports
 */

'use client';

import React, { useState, useEffect } from 'react';

export default function SimpleDebugPage() {
  const [debugEnabled, setDebugEnabled] = useState(false);

  useEffect(() => {
    // Simple test of localStorage
    const stored = localStorage.getItem('debug_mode');
    setDebugEnabled(stored === 'true');
  }, []);

  const toggleDebug = () => {
    const newState = !debugEnabled;
    setDebugEnabled(newState);
    if (newState) {
      localStorage.setItem('debug_mode', 'true');
    } else {
      localStorage.removeItem('debug_mode');
    }
    console.log('Debug toggled:', newState);
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Simple Debug Test</h1>
      
      <div style={{ 
        marginBottom: '20px',
        padding: '20px',
        border: '2px solid #ccc',
        borderRadius: '8px',
        backgroundColor: '#f9f9f9'
      }}>
        <h2>Debug Status</h2>
        <p><strong>Debug Enabled:</strong> {debugEnabled ? 'YES' : 'NO'}</p>
        <button 
          onClick={toggleDebug}
          style={{
            padding: '10px 20px',
            backgroundColor: debugEnabled ? '#10b981' : '#6b7280',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '16px'
          }}
        >
          {debugEnabled ? 'Disable Debug' : 'Enable Debug'}
        </button>
      </div>

      <div style={{ 
        marginBottom: '20px',
        padding: '20px',
        border: '2px solid #ccc',
        borderRadius: '8px',
        backgroundColor: '#f0f8ff'
      }}>
        <h2>Environment Info</h2>
        <p><strong>Window exists:</strong> {typeof window !== 'undefined' ? 'YES' : 'NO'}</p>
        <p><strong>LocalStorage available:</strong> {typeof localStorage !== 'undefined' ? 'YES' : 'NO'}</p>
        <p><strong>Current URL:</strong> {typeof window !== 'undefined' ? window.location.href : 'N/A'}</p>
      </div>

      <div style={{ 
        marginBottom: '20px',
        padding: '20px',
        border: '2px solid #ccc',
        borderRadius: '8px',
        backgroundColor: '#fff5f5'
      }}>
        <h2>Instructions</h2>
        <ol>
          <li>This page should be accessible at: <code>http://localhost:3000/simple-debug</code></li>
          <li>Click the "Enable Debug" button above</li>
          <li>Check the browser console for log messages</li>
          <li>The button should change color when clicked</li>
        </ol>
      </div>

      {/* Simple floating debug indicator */}
      {debugEnabled && (
        <div style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          backgroundColor: '#10b981',
          color: 'white',
          padding: '10px 15px',
          borderRadius: '8px',
          fontSize: '14px',
          fontWeight: 'bold',
          zIndex: 9999,
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
        }}>
          🐛 DEBUG ACTIVE
        </div>
      )}
    </div>
  );
}
