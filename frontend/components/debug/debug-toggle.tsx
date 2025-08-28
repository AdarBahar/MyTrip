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
  draggable?: boolean; // allow dragging anywhere on screen
  storageKey?: string; // persist position
}

export function DebugToggle({
  className = '',
  position = 'bottom-left',
  draggable = true,
  storageKey = 'debug-toggle-pos',
}: DebugToggleProps) {
  const [isEnabled, setIsEnabled] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [pos, setPos] = useState<{x:number,y:number}|null>(null);
  const [dragging, setDragging] = useState(false);
  const [offset, setOffset] = useState<{dx:number,dy:number}>({dx:0,dy:0});

  useEffect(() => {
    setIsEnabled(debugManager.isDebugEnabled());
    setMounted(true);
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
            case 'top-right': return { x: window.innerWidth - 140, y: margin };
            case 'top-left': return { x: margin, y: margin };
            case 'bottom-right': return { x: window.innerWidth - 140, y: window.innerHeight - 56 };
            case 'bottom-left':
            default:
              return { x: margin, y: window.innerHeight - 56 };
          }
        })();
        setPos(initial);
        try { localStorage.setItem(storageKey, JSON.stringify(initial)); } catch {}
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
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
        const width = 140; // approx button width
        const height = 40; // approx button height
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
      className={`${!draggable ? `fixed ${getPositionClasses()}` : 'fixed'} z-50 ${className}`}
      style={draggable && mounted && pos ? { left: pos.x, top: pos.y } as React.CSSProperties : undefined}
      onMouseDown={onMouseDown}
    >
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
