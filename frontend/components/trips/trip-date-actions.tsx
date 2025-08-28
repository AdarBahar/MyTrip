/**
 * Trip Date Action Components
 * Components for setting and updating trip start dates
 */

'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Calendar, Edit3, Plus, Clock } from 'lucide-react';
import { DatePickerModal } from './date-picker-modal';
import { updateTripStartDate, formatTripDate, isDateInPast, type Trip } from '@/lib/api/trips';

interface TripDateActionsProps {
  trip: Trip;
  onTripUpdate?: (updatedTrip: Trip) => void;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function TripDateActions({ 
  trip, 
  onTripUpdate, 
  showLabel = true,
  size = 'md' 
}: TripDateActionsProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);

  const hasStartDate = !!trip.start_date;
  const isPastDate = trip.start_date ? isDateInPast(trip.start_date) : false;

  const handleDateUpdate = async (newDate: string | null) => {
    setIsUpdating(true);
    
    try {
      const result = await updateTripStartDate(trip.id, newDate);
      
      if (result.error) {
        throw new Error(result.error);
      }
      
      if (result.data && onTripUpdate) {
        onTripUpdate(result.data);
      }
      
      setIsModalOpen(false);
    } catch (error) {
      console.error('Failed to update trip date:', error);
      throw error; // Let the modal handle the error display
    } finally {
      setIsUpdating(false);
    }
  };

  const getButtonSize = () => {
    switch (size) {
      case 'sm': return { padding: '6px 12px', fontSize: '12px' };
      case 'lg': return { padding: '12px 24px', fontSize: '16px' };
      default: return { padding: '8px 16px', fontSize: '14px' };
    }
  };

  const getIconSize = () => {
    switch (size) {
      case 'sm': return 14;
      case 'lg': return 20;
      default: return 16;
    }
  };

  if (hasStartDate) {
    return (
      <>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          {showLabel && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Calendar size={getIconSize()} style={{ color: '#059669' }} />
                <span style={{ 
                  fontSize: size === 'sm' ? '12px' : size === 'lg' ? '16px' : '14px',
                  fontWeight: '500',
                  color: '#374151'
                }}>
                  Trip starts:
                </span>
                {isPastDate && (
                  <Clock size={12} style={{ color: '#f59e0b' }} title="Past date" />
                )}
              </div>
              <span style={{ 
                fontSize: size === 'sm' ? '14px' : size === 'lg' ? '18px' : '16px',
                fontWeight: '600',
                color: isPastDate ? '#f59e0b' : '#059669'
              }}>
                {formatTripDate(trip.start_date)}
              </span>
            </div>
          )}
          
          <Button
            onClick={() => setIsModalOpen(true)}
            disabled={isUpdating}
            style={{
              backgroundColor: '#f3f4f6',
              color: '#374151',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              cursor: isUpdating ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              ...getButtonSize()
            }}
          >
            <Edit3 size={getIconSize()} />
            Update Date
          </Button>
        </div>

        <DatePickerModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onSave={handleDateUpdate}
          currentDate={trip.start_date}
          title="Update Trip Date"
          description="Change the start date for your trip. This will update all day dates automatically."
          allowClear={true}
        />
      </>
    );
  }

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
        {showLabel && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Calendar size={getIconSize()} style={{ color: '#6b7280' }} />
              <span style={{ 
                fontSize: size === 'sm' ? '12px' : size === 'lg' ? '16px' : '14px',
                fontWeight: '500',
                color: '#6b7280'
              }}>
                Start date:
              </span>
            </div>
            <span style={{ 
              fontSize: size === 'sm' ? '14px' : size === 'lg' ? '18px' : '16px',
              fontWeight: '500',
              color: '#9ca3af',
              fontStyle: 'italic'
            }}>
              Not set
            </span>
          </div>
        )}
        
        <Button
          onClick={() => setIsModalOpen(true)}
          disabled={isUpdating}
          style={{
            backgroundColor: '#059669',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: isUpdating ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            ...getButtonSize()
          }}
        >
          <Plus size={getIconSize()} />
          Set Start Date
        </Button>
      </div>

      <DatePickerModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleDateUpdate}
        currentDate={null}
        title="Set Trip Start Date"
        description="Choose when your trip begins. This will be used to calculate dates for each day of your trip."
        allowClear={false}
      />
    </>
  );
}

/**
 * Compact Trip Date Display
 * Shows just the date with a small edit button
 */
interface CompactTripDateProps {
  trip: Trip;
  onTripUpdate?: (updatedTrip: Trip) => void;
}

export function CompactTripDate({ trip, onTripUpdate }: CompactTripDateProps) {
  return (
    <TripDateActions 
      trip={trip} 
      onTripUpdate={onTripUpdate} 
      showLabel={false} 
      size="sm" 
    />
  );
}

/**
 * Trip Date Badge
 * Shows date as a badge with optional edit functionality
 */
interface TripDateBadgeProps {
  trip: Trip;
  onTripUpdate?: (updatedTrip: Trip) => void;
  editable?: boolean;
}

export function TripDateBadge({ trip, onTripUpdate, editable = false }: TripDateBadgeProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const hasStartDate = !!trip.start_date;
  const isPastDate = trip.start_date ? isDateInPast(trip.start_date) : false;

  const handleDateUpdate = async (newDate: string | null) => {
    try {
      const result = await updateTripStartDate(trip.id, newDate);
      
      if (result.error) {
        throw new Error(result.error);
      }
      
      if (result.data && onTripUpdate) {
        onTripUpdate(result.data);
      }
      
      setIsModalOpen(false);
    } catch (error) {
      console.error('Failed to update trip date:', error);
      throw error;
    }
  };

  const badgeStyle = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
    padding: '4px 8px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: '500',
    cursor: editable ? 'pointer' : 'default',
    backgroundColor: hasStartDate 
      ? (isPastDate ? '#fef3c7' : '#d1fae5')
      : '#f3f4f6',
    color: hasStartDate 
      ? (isPastDate ? '#92400e' : '#065f46')
      : '#6b7280',
    border: `1px solid ${hasStartDate 
      ? (isPastDate ? '#fbbf24' : '#10b981')
      : '#d1d5db'}`
  };

  return (
    <>
      <div
        style={badgeStyle}
        onClick={editable ? () => setIsModalOpen(true) : undefined}
        title={editable ? 'Click to edit date' : undefined}
      >
        <Calendar size={12} />
        {hasStartDate ? formatTripDate(trip.start_date) : 'No date set'}
        {editable && <Edit3 size={10} />}
      </div>

      {editable && (
        <DatePickerModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onSave={handleDateUpdate}
          currentDate={trip.start_date}
          title={hasStartDate ? "Update Trip Date" : "Set Trip Start Date"}
          description={hasStartDate 
            ? "Change the start date for your trip."
            : "Choose when your trip begins."
          }
          allowClear={hasStartDate}
        />
      )}
    </>
  );
}
