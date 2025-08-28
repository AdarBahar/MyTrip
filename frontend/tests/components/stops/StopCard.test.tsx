/**
 * Tests for StopCard component
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import StopCard from '../../../components/stops/StopCard';
import { StopType, StopPriority } from '../../../lib/constants/stopTypes';
import * as stopsApi from '../../../lib/api/stops';

// Mock the stops API
vi.mock('../../../lib/api/stops', () => ({
  deleteStop: vi.fn()
}));

// Mock the debug hook
vi.mock('../../../lib/debug', () => ({
  useDebug: () => ({
    log: vi.fn(),
    error: vi.fn()
  })
}));

const mockStopsApi = vi.mocked(stopsApi);

describe('StopCard', () => {
  const mockStop = {
    id: 'stop1',
    day_id: 'day1',
    trip_id: 'trip1',
    place_id: 'place1',
    seq: 1,
    kind: 'via' as const,
    fixed: false,
    notes: 'Great lunch spot',
    stop_type: StopType.FOOD,
    arrival_time: '12:00:00',
    departure_time: '13:30:00',
    duration_minutes: 90,
    priority: StopPriority.NICE_TO_HAVE,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    place: {
      id: 'place1',
      name: 'Amazing Restaurant',
      address: '123 Main St, City, State',
      lat: 40.7128,
      lon: -74.0060
    },
    booking_info: {
      confirmation: 'ABC123',
      status: 'confirmed'
    },
    contact_info: {
      phone: '555-1234',
      website: 'https://example.com'
    },
    cost_info: {
      estimated: 25.50
    }
  };

  const defaultProps = {
    stop: mockStop,
    tripId: 'trip1',
    dayId: 'day1',
    onUpdate: vi.fn(),
    onDelete: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders stop information correctly', () => {
    render(<StopCard {...defaultProps} />);

    expect(screen.getByText('Amazing Restaurant')).toBeInTheDocument();
    expect(screen.getByText('123 Main St, City, State')).toBeInTheDocument();
    expect(screen.getByText('Food & Drink')).toBeInTheDocument();
    expect(screen.getByText('#1')).toBeInTheDocument();
  });

  it('displays timing information', () => {
    render(<StopCard {...defaultProps} />);

    expect(screen.getByText('12:00 PM')).toBeInTheDocument();
    expect(screen.getByText('1h 30m')).toBeInTheDocument();
  });

  it('displays cost information', () => {
    render(<StopCard {...defaultProps} />);

    expect(screen.getByText('$25.5')).toBeInTheDocument();
  });

  it('shows notes preview', () => {
    render(<StopCard {...defaultProps} />);

    expect(screen.getByText('Great lunch spot')).toBeInTheDocument();
  });

  it('toggles detailed view when clock icon is clicked', () => {
    render(<StopCard {...defaultProps} />);

    // Details should not be visible initially
    expect(screen.queryByText('Timing')).not.toBeInTheDocument();

    // Click the clock icon to show details
    const clockButton = screen.getByTitle('Toggle details');
    fireEvent.click(clockButton);

    // Details should now be visible
    expect(screen.getByText('Timing')).toBeInTheDocument();
    expect(screen.getByText('Contact')).toBeInTheDocument();
    expect(screen.getByText('Booking')).toBeInTheDocument();
    expect(screen.getByText('Cost')).toBeInTheDocument();
  });

  it('displays detailed timing information when expanded', () => {
    render(<StopCard {...defaultProps} />);

    // Expand details
    const clockButton = screen.getByTitle('Toggle details');
    fireEvent.click(clockButton);

    expect(screen.getByText('Arrival:')).toBeInTheDocument();
    expect(screen.getByText('Departure:')).toBeInTheDocument();
    expect(screen.getByText('Duration:')).toBeInTheDocument();
  });

  it('displays contact information when expanded', () => {
    render(<StopCard {...defaultProps} />);

    // Expand details
    const clockButton = screen.getByTitle('Toggle details');
    fireEvent.click(clockButton);

    expect(screen.getByText('555-1234')).toBeInTheDocument();
    expect(screen.getByText('Website')).toBeInTheDocument();
  });

  it('displays booking information when expanded', () => {
    render(<StopCard {...defaultProps} />);

    // Expand details
    const clockButton = screen.getByTitle('Toggle details');
    fireEvent.click(clockButton);

    expect(screen.getByText('ABC123')).toBeInTheDocument();
    expect(screen.getByText('Confirmed')).toBeInTheDocument();
  });

  it('calls onUpdate when edit button is clicked', () => {
    const onUpdate = vi.fn();
    render(<StopCard {...defaultProps} onUpdate={onUpdate} />);

    const editButton = screen.getByTitle('Edit stop');
    fireEvent.click(editButton);

    expect(onUpdate).toHaveBeenCalled();
  });

  it('shows delete confirmation when delete button is clicked', () => {
    render(<StopCard {...defaultProps} />);

    const deleteButton = screen.getByTitle('Delete stop');
    fireEvent.click(deleteButton);

    expect(screen.getByText('Delete this stop?')).toBeInTheDocument();
    expect(screen.getByText('This action cannot be undone.')).toBeInTheDocument();
  });

  it('cancels delete when cancel button is clicked', () => {
    render(<StopCard {...defaultProps} />);

    // Show delete confirmation
    const deleteButton = screen.getByTitle('Delete stop');
    fireEvent.click(deleteButton);

    // Cancel delete
    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    expect(screen.queryByText('Delete this stop?')).not.toBeInTheDocument();
  });

  it('deletes stop when confirmed', async () => {
    const onDelete = vi.fn();
    mockStopsApi.deleteStop.mockResolvedValue();

    render(<StopCard {...defaultProps} onDelete={onDelete} />);

    // Show delete confirmation
    const deleteButton = screen.getByTitle('Delete stop');
    fireEvent.click(deleteButton);

    // Confirm delete
    const confirmButton = screen.getByText('Delete');
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockStopsApi.deleteStop).toHaveBeenCalledWith('trip1', 'day1', 'stop1');
      expect(onDelete).toHaveBeenCalled();
    });
  });

  it('handles delete error gracefully', async () => {
    mockStopsApi.deleteStop.mockRejectedValue(new Error('Delete failed'));

    render(<StopCard {...defaultProps} />);

    // Show delete confirmation
    const deleteButton = screen.getByTitle('Delete stop');
    fireEvent.click(deleteButton);

    // Confirm delete
    const confirmButton = screen.getByText('Delete');
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockStopsApi.deleteStop).toHaveBeenCalled();
      // Should not call onDelete on error
      expect(defaultProps.onDelete).not.toHaveBeenCalled();
    });
  });

  it('renders without place information', () => {
    const stopWithoutPlace = {
      ...mockStop,
      place: undefined
    };

    render(<StopCard {...defaultProps} stop={stopWithoutPlace} />);

    expect(screen.getByText('Unnamed Location')).toBeInTheDocument();
  });

  it('renders without optional fields', () => {
    const minimalStop = {
      ...mockStop,
      notes: undefined,
      arrival_time: undefined,
      departure_time: undefined,
      duration_minutes: undefined,
      booking_info: undefined,
      contact_info: undefined,
      cost_info: undefined
    };

    render(<StopCard {...defaultProps} stop={minimalStop} />);

    expect(screen.getByText('Amazing Restaurant')).toBeInTheDocument();
    expect(screen.getByText('Food & Drink')).toBeInTheDocument();
  });

  it('shows priority badge for non-default priority', () => {
    const highPriorityStop = {
      ...mockStop,
      priority: StopPriority.MUST_SEE
    };

    render(<StopCard {...defaultProps} stop={highPriorityStop} />);

    expect(screen.getByText('Must See')).toBeInTheDocument();
  });

  it('does not show priority badge for default priority', () => {
    render(<StopCard {...defaultProps} />);

    expect(screen.queryByText('Nice to Have')).not.toBeInTheDocument();
  });

  it('renders with drag handle props', () => {
    const dragHandleProps = {
      'data-rbd-drag-handle-draggable-id': 'stop1',
      'data-rbd-drag-handle-context-id': 'context1'
    };

    render(<StopCard {...defaultProps} dragHandleProps={dragHandleProps} />);

    // The drag handle should have the props applied
    const dragHandle = screen.getByRole('button', { name: /drag/i });
    expect(dragHandle).toHaveAttribute('data-rbd-drag-handle-draggable-id', 'stop1');
  });
});
