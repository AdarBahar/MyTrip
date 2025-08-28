/**
 * Development Environment Indicator
 * Shows when the app is running in development mode with debug features
 */

'use client';

import React, { useState, useEffect } from 'react';
import { debugManager } from '@/lib/debug';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Bug, 
  Code, 
  Eye, 
  EyeOff,
  Settings,
  Activity
} from 'lucide-react';

interface DevIndicatorProps {
  className?: string;
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
  showApiCount?: boolean;
  draggable?: boolean;
  storageKey?: string;
}

export function DevIndicator({
  className = '',
  position = 'top-right',
  showApiCount = true,
  draggable = true,
  storageKey = 'dev-indicator-pos',
}: DevIndicatorProps) {
  const [isDebugEnabled, setIsDebugEnabled] = useState(false);
  const [apiCallCount, setApiCallCount] = useState(0);
  const [isDevelopment, setIsDevelopment] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [pos, setPos] = useState<{x:number,y:number}|null>(null);
  const [dragging, setDragging] = useState(false);
  const [offset, setOffset] = useState<{dx:number,dy:number}>({dx:0,dy:0});

  useEffect(() => {
    // Check if we're in development mode
    setIsDevelopment(process.env.NODE_ENV === 'development');
    setMounted(true);

    setIsDebugEnabled(debugManager.isDebugEnabled());
    setApiCallCount(debugManager.getApiCalls().length);

    const unsubscribe = debugManager.subscribe((calls) => {
      setApiCallCount(calls.length);
    });

    if (draggable && typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem(storageKey);
        if (saved) {
          const parsed = JSON.parse(saved);
          if (typeof parsed?.x === 'number' && typeof parsed?.y === 'number') {
            setPos({x: parsed.x, y: parsed.y});
          }
        }
      } catch {}
      if (!pos) {
        const margin = 16;
        const initial = (() => {
          switch (position) {
            case 'top-right': return { x: window.innerWidth - 120, y: margin };
            case 'top-left': return { x: margin, y: margin };
            case 'bottom-right': return { x: window.innerWidth - 120, y: window.innerHeight - 56 };
            case 'bottom-left':
            default:
              return { x: margin, y: window.innerHeight - 56 };
          }
        })();
        setPos(initial);
        try { localStorage.setItem(storageKey, JSON.stringify(initial)); } catch {}
      }
    }

    return unsubscribe;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggleDebugMode = () => {
    if (isDebugEnabled) {
      debugManager.disable();
      setIsDebugEnabled(false);
    } else {
      debugManager.enable();
      setIsDebugEnabled(true);
    }
  };

  const getPositionClasses = () => {
    switch (position) {
      case 'top-left':
        return 'top-4 left-4';
      case 'top-right':
        return 'top-4 right-4';
      case 'bottom-left':
        return 'bottom-4 left-4';
      case 'bottom-right':
        return 'bottom-4 right-4';
      default:
        return 'top-4 right-4';
    }
  };

  // Only show in development or when debug is enabled
  if (!isDevelopment && !isDebugEnabled) {
    return null;
  }

  const onMouseDown: React.MouseEventHandler<HTMLDivElement> = (e) => {
    if (!draggable) return;
    const target = e.currentTarget.getBoundingClientRect();
    setDragging(true);
    setOffset({ dx: e.clientX - target.left, dy: e.clientY - target.top });
    e.preventDefault();
  };

  useEffect(() => {
    if (!dragging) return;
    const onMove = (e: MouseEvent) => {
      setPos(prev => {
        const margin = 8;
        const width = 120; // approx width of badges
        const height = 36; // approx height of badges row
        const x = Math.max(margin, Math.min((e.clientX - offset.dx), window.innerWidth - width - margin));
        const y = Math.max(margin, Math.min((e.clientY - offset.dy), window.innerHeight - height - margin));
        const p = { x, y };
        try { localStorage.setItem(storageKey, JSON.stringify(p)); } catch {}
        return p;
      });
    };
    const onUp = () => setDragging(false);
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
  }, [dragging, offset.dx, offset.dy, storageKey, draggable]);

  return (
    <div
      className={`${!draggable ? `fixed ${getPositionClasses()}` : 'fixed'} z-40 ${className}`}
      style={draggable && mounted && pos ? { left: pos.x, top: pos.y } as React.CSSProperties : undefined}
      onMouseDown={onMouseDown}
    >
      <div className="flex items-center space-x-2">
        {/* Development Mode Badge */}
        {isDevelopment && (
          <Badge variant="outline" className="bg-yellow-50 border-yellow-200 text-yellow-800">
            <Code className="h-3 w-3 mr-1" />
            DEV
          </Badge>
        )}

        {/* Debug Mode Badge */}
        {isDebugEnabled && (
          <Badge variant="outline" className="bg-green-50 border-green-200 text-green-800">
            <Bug className="h-3 w-3 mr-1" />
            DEBUG
            {showApiCount && apiCallCount > 0 && (
              <span className="ml-1 px-1 bg-green-200 rounded text-xs">
                {apiCallCount}
              </span>
            )}
          </Badge>
        )}

        {/* Debug Toggle Button */}
        <Button
          variant="outline"
          size="sm"
          onClick={toggleDebugMode}
          className="h-7 px-2"
          title={isDebugEnabled ? "Disable Debug Mode" : "Enable Debug Mode"}
        >
          {isDebugEnabled ? (
            <EyeOff className="h-3 w-3" />
          ) : (
            <Eye className="h-3 w-3" />
          )}
        </Button>
      </div>
    </div>
  );
}

/**
 * Inline Development Status
 * Shows development status inline with other content
 */
export function DevStatus({ className = '' }: { className?: string }) {
  const [isDebugEnabled, setIsDebugEnabled] = useState(false);
  const [apiCallCount, setApiCallCount] = useState(0);
  const [isDevelopment, setIsDevelopment] = useState(false);

  useEffect(() => {
    setIsDevelopment(process.env.NODE_ENV === 'development');
    setIsDebugEnabled(debugManager.isDebugEnabled());
    setApiCallCount(debugManager.getApiCalls().length);

    const unsubscribe = debugManager.subscribe((calls) => {
      setApiCallCount(calls.length);
    });

    return unsubscribe;
  }, []);

  if (!isDevelopment && !isDebugEnabled) {
    return null;
  }

  return (
    <div className={`inline-flex items-center space-x-2 text-sm ${className}`}>
      {isDevelopment && (
        <div className="flex items-center space-x-1">
          <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
          <span className="text-yellow-600 font-medium">Development</span>
        </div>
      )}
      
      {isDebugEnabled && (
        <div className="flex items-center space-x-1">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-green-600 font-medium">Debug Active</span>
          {apiCallCount > 0 && (
            <span className="text-gray-500">
              ({apiCallCount} API call{apiCallCount !== 1 ? 's' : ''})
            </span>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Performance Monitor
 * Shows basic performance metrics when debug is enabled
 */
export function PerformanceMonitor({ className = '' }: { className?: string }) {
  const [isDebugEnabled, setIsDebugEnabled] = useState(false);
  const [apiCalls, setApiCalls] = useState<any[]>([]);

  useEffect(() => {
    setIsDebugEnabled(debugManager.isDebugEnabled());
    setApiCalls(debugManager.getApiCalls());

    const unsubscribe = debugManager.subscribe((calls) => {
      setApiCalls(calls);
    });

    return unsubscribe;
  }, []);

  if (!isDebugEnabled || apiCalls.length === 0) {
    return null;
  }

  const completedCalls = apiCalls.filter(call => call.duration);
  const avgDuration = completedCalls.reduce((sum, call) => sum + call.duration, 0) / completedCalls.length;
  const slowCalls = completedCalls.filter(call => call.duration > 1000).length;
  const errorCalls = apiCalls.filter(call => call.response && call.response.status >= 400).length;

  return (
    <div className={`inline-flex items-center space-x-4 text-xs text-gray-600 ${className}`}>
      <div className="flex items-center space-x-1">
        <Activity className="h-3 w-3" />
        <span>Avg: {Math.round(avgDuration)}ms</span>
      </div>
      
      {slowCalls > 0 && (
        <div className="flex items-center space-x-1 text-yellow-600">
          <Settings className="h-3 w-3" />
          <span>{slowCalls} slow</span>
        </div>
      )}
      
      {errorCalls > 0 && (
        <div className="flex items-center space-x-1 text-red-600">
          <Bug className="h-3 w-3" />
          <span>{errorCalls} error{errorCalls !== 1 ? 's' : ''}</span>
        </div>
      )}
    </div>
  );
}
