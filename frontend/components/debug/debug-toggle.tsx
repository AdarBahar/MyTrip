/**
 * Debug Toggle Component
 * Simple floating button to enable/disable debug mode
 */

'use client';

import React, { useState, useEffect } from 'react';
import { debugManager } from '@/lib/debug';
import { Button } from '@/components/ui/button';
import { Bug, Eye, EyeOff } from 'lucide-react';

interface DebugToggleProps {
  className?: string;
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
}

export function DebugToggle({ 
  className = '', 
  position = 'bottom-left' 
}: DebugToggleProps) {
  const [isEnabled, setIsEnabled] = useState(false);

  useEffect(() => {
    setIsEnabled(debugManager.isDebugEnabled());
  }, []);

  const toggleDebugMode = () => {
    if (isEnabled) {
      debugManager.disable();
      setIsEnabled(false);
    } else {
      debugManager.enable();
      setIsEnabled(true);
    }
  };

  const getPositionClasses = () => {
    switch (position) {
      case 'bottom-right':
        return 'bottom-4 right-4';
      case 'bottom-left':
        return 'bottom-4 left-4';
      case 'top-right':
        return 'top-4 right-4';
      case 'top-left':
        return 'top-4 left-4';
      default:
        return 'bottom-4 left-4';
    }
  };

  return (
    <div className={`fixed ${getPositionClasses()} z-50 ${className}`}>
      <Button
        variant={isEnabled ? "default" : "outline"}
        size="sm"
        onClick={toggleDebugMode}
        className="shadow-lg"
        title={isEnabled ? "Disable Debug Mode" : "Enable Debug Mode"}
      >
        <Bug className="h-4 w-4 mr-2" />
        {isEnabled ? (
          <>
            <EyeOff className="h-4 w-4" />
            <span className="sr-only">Disable Debug</span>
          </>
        ) : (
          <>
            <Eye className="h-4 w-4" />
            <span className="sr-only">Enable Debug</span>
          </>
        )}
      </Button>
    </div>
  );
}

/**
 * Debug Status Indicator
 * Shows current debug status in the UI
 */
export function DebugStatus({ className = '' }: { className?: string }) {
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
    <div className={`inline-flex items-center space-x-2 text-sm ${className}`}>
      <div className="flex items-center space-x-1">
        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
        <span className="text-green-600 font-medium">Debug Mode</span>
      </div>
      {apiCallCount > 0 && (
        <span className="text-gray-500">
          {apiCallCount} API call{apiCallCount !== 1 ? 's' : ''}
        </span>
      )}
    </div>
  );
}
