/**
 * Date Picker Modal Component
 * Reusable modal for setting and updating trip start dates
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Calendar, X, Check, AlertCircle } from 'lucide-react';
import { simpleDebugManager } from '@/components/minimal-debug';

interface DatePickerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (date: string | null) => Promise<void>;
  currentDate?: string | null;
  title?: string;
  description?: string;
  allowClear?: boolean;
}

export function DatePickerModal({
  isOpen,
  onClose,
  onSave,
  currentDate,
  title = "Set Trip Date",
  description = "Choose the start date for your trip",
  allowClear = false
}: DatePickerModalProps) {
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize date when modal opens
  useEffect(() => {
    if (isOpen) {
      setSelectedDate(currentDate || '');
      setError(null);
    }
  }, [isOpen, currentDate]);

  const handleSave = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Validate date
      if (selectedDate && !isValidDate(selectedDate)) {
        setError('Please enter a valid date');
        setIsLoading(false);
        return;
      }

      // Log debug information
      simpleDebugManager.logApiCall(
        'PATCH', 
        '/trips/[id]', 
        undefined, 
        undefined
      );

      await onSave(selectedDate || null);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update date');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = async () => {
    if (!allowClear) return;
    
    setIsLoading(true);
    setError(null);

    try {
      await onSave(null);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to clear date');
    } finally {
      setIsLoading(false);
    }
  };

  const isValidDate = (dateString: string): boolean => {
    if (!dateString) return true; // Empty is valid
    const date = new Date(dateString);
    return !isNaN(date.getTime()) && dateString.match(/^\d{4}-\d{2}-\d{2}$/);
  };

  const formatDateForDisplay = (dateString: string): string => {
    if (!dateString) return '';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  const getTodayDate = (): string => {
    return new Date().toISOString().split('T')[0];
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 50,
        padding: '20px'
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <Card 
        style={{ 
          width: '100%', 
          maxWidth: '500px',
          backgroundColor: 'white',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
        }}
      >
        <CardHeader>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <CardTitle style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Calendar size={20} />
                {title}
              </CardTitle>
              <p style={{ color: '#6b7280', fontSize: '14px', marginTop: '4px' }}>
                {description}
              </p>
            </div>
            <Button
              onClick={onClose}
              style={{
                background: 'none',
                border: 'none',
                padding: '8px',
                cursor: 'pointer',
                borderRadius: '4px'
              }}
            >
              <X size={20} />
            </Button>
          </div>
        </CardHeader>

        <CardContent style={{ padding: '24px' }}>
          {/* Date Input */}
          <div style={{ marginBottom: '20px' }}>
            <label 
              htmlFor="trip-date"
              style={{ 
                display: 'block', 
                fontSize: '14px', 
                fontWeight: '500', 
                marginBottom: '8px',
                color: '#374151'
              }}
            >
              Start Date
            </label>
            <input
              id="trip-date"
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              min={getTodayDate()}
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                fontSize: '16px',
                backgroundColor: 'white'
              }}
            />
            
            {/* Date Preview */}
            {selectedDate && isValidDate(selectedDate) && (
              <p style={{ 
                fontSize: '14px', 
                color: '#059669', 
                marginTop: '8px',
                fontWeight: '500'
              }}>
                📅 {formatDateForDisplay(selectedDate)}
              </p>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '12px',
              backgroundColor: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: '6px',
              marginBottom: '20px'
            }}>
              <AlertCircle size={16} style={{ color: '#dc2626' }} />
              <span style={{ color: '#dc2626', fontSize: '14px' }}>{error}</span>
            </div>
          )}

          {/* Action Buttons */}
          <div style={{ 
            display: 'flex', 
            gap: '12px', 
            justifyContent: 'flex-end',
            flexWrap: 'wrap'
          }}>
            {allowClear && currentDate && (
              <Button
                onClick={handleClear}
                disabled={isLoading}
                style={{
                  backgroundColor: '#f3f4f6',
                  color: '#374151',
                  border: '1px solid #d1d5db',
                  padding: '8px 16px',
                  borderRadius: '6px',
                  fontSize: '14px',
                  cursor: isLoading ? 'not-allowed' : 'pointer'
                }}
              >
                Clear Date
              </Button>
            )}
            
            <Button
              onClick={onClose}
              disabled={isLoading}
              style={{
                backgroundColor: '#f3f4f6',
                color: '#374151',
                border: '1px solid #d1d5db',
                padding: '8px 16px',
                borderRadius: '6px',
                fontSize: '14px',
                cursor: isLoading ? 'not-allowed' : 'pointer'
              }}
            >
              Cancel
            </Button>
            
            <Button
              onClick={handleSave}
              disabled={isLoading || (selectedDate && !isValidDate(selectedDate))}
              style={{
                backgroundColor: '#059669',
                color: 'white',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '6px',
                fontSize: '14px',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              {isLoading ? (
                <>
                  <div style={{
                    width: '16px',
                    height: '16px',
                    border: '2px solid #ffffff',
                    borderTop: '2px solid transparent',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                  }} />
                  Saving...
                </>
              ) : (
                <>
                  <Check size={16} />
                  Save Date
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* CSS Animation */}
      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
