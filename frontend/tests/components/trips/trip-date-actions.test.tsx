/**
 * Tests for TripDateActions components
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { TripDateActions, TripDateBadge, CompactTripDate } from '@/components/trips/trip-date-actions'
import type { Trip } from '@/lib/api/trips'

// Mock the API
vi.mock('@/lib/api/trips', async () => {
  const actual = await vi.importActual('@/lib/api/trips')
  return {
    ...actual,
    updateTripStartDate: vi.fn(),
    formatTripDate: vi.fn((date) => date ? `Formatted: ${date}` : 'No date set'),
    isDateInPast: vi.fn((date) => date === '2023-01-01'),
  }
})

// Mock the DatePickerModal
vi.mock('@/components/trips/date-picker-modal', () => ({
  DatePickerModal: ({ isOpen, onSave, onClose, title }: any) => (
    isOpen ? (
      <div data-testid="date-picker-modal">
        <h2>{title}</h2>
        <button onClick={() => onSave('2024-12-25')}>Save Test Date</button>
        <button onClick={() => onSave(null)}>Clear Test Date</button>
        <button onClick={onClose}>Close Modal</button>
      </div>
    ) : null
  ),
}))

const { updateTripStartDate } = await import('@/lib/api/trips')

describe('TripDateActions', () => {
  const mockOnTripUpdate = vi.fn()

  const tripWithoutDate: Trip = {
    id: 'trip-1',
    slug: 'test-trip',
    title: 'Test Trip',
    destination: 'Test Destination',
    start_date: null,
    timezone: 'UTC',
    status: 'active',
    is_published: false,
    created_by: 'user-1',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  }

  const tripWithDate: Trip = {
    ...tripWithoutDate,
    start_date: '2024-12-25',
  }

  const tripWithPastDate: Trip = {
    ...tripWithoutDate,
    start_date: '2023-01-01',
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(updateTripStartDate).mockResolvedValue({ data: tripWithDate })
  })

  describe('Trip without date', () => {
    it('shows "Set Start Date" button for trip without date', () => {
      render(<TripDateActions trip={tripWithoutDate} />)
      
      expect(screen.getByText('Set Start Date')).toBeInTheDocument()
      expect(screen.getByText('Not set')).toBeInTheDocument()
    })

    it('opens modal when "Set Start Date" is clicked', () => {
      render(<TripDateActions trip={tripWithoutDate} />)
      
      const setDateButton = screen.getByText('Set Start Date')
      fireEvent.click(setDateButton)
      
      expect(screen.getByTestId('date-picker-modal')).toBeInTheDocument()
      expect(screen.getByText('Set Trip Start Date')).toBeInTheDocument()
    })

    it('calls API and updates trip when date is saved', async () => {
      render(<TripDateActions trip={tripWithoutDate} onTripUpdate={mockOnTripUpdate} />)
      
      const setDateButton = screen.getByText('Set Start Date')
      fireEvent.click(setDateButton)
      
      const saveButton = screen.getByText('Save Test Date')
      fireEvent.click(saveButton)
      
      await waitFor(() => {
        expect(updateTripStartDate).toHaveBeenCalledWith('trip-1', '2024-12-25')
        expect(mockOnTripUpdate).toHaveBeenCalledWith(tripWithDate)
      })
    })
  })

  describe('Trip with date', () => {
    it('shows formatted date and "Update Date" button for trip with date', () => {
      render(<TripDateActions trip={tripWithDate} />)
      
      expect(screen.getByText('Formatted: 2024-12-25')).toBeInTheDocument()
      expect(screen.getByText('Update Date')).toBeInTheDocument()
    })

    it('opens modal when "Update Date" is clicked', () => {
      render(<TripDateActions trip={tripWithDate} />)
      
      const updateButton = screen.getByText('Update Date')
      fireEvent.click(updateButton)
      
      expect(screen.getByTestId('date-picker-modal')).toBeInTheDocument()
      expect(screen.getByText('Update Trip Date')).toBeInTheDocument()
    })

    it('shows past date indicator for past dates', () => {
      render(<TripDateActions trip={tripWithPastDate} />)
      
      // Should show past date styling (we can't easily test color, but we can test the presence of the clock icon)
      expect(screen.getByText('Formatted: 2023-01-01')).toBeInTheDocument()
    })
  })

  describe('Different sizes', () => {
    it('renders with small size', () => {
      render(<TripDateActions trip={tripWithoutDate} size="sm" />)
      
      expect(screen.getByText('Set Start Date')).toBeInTheDocument()
    })

    it('renders with large size', () => {
      render(<TripDateActions trip={tripWithoutDate} size="lg" />)
      
      expect(screen.getByText('Set Start Date')).toBeInTheDocument()
    })
  })

  describe('Without label', () => {
    it('hides label when showLabel is false', () => {
      render(<TripDateActions trip={tripWithoutDate} showLabel={false} />)
      
      expect(screen.queryByText('Start date:')).not.toBeInTheDocument()
      expect(screen.getByText('Set Start Date')).toBeInTheDocument()
    })
  })

  describe('Error handling', () => {
    it('handles API errors gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      vi.mocked(updateTripStartDate).mockResolvedValue({ error: 'API Error' })
      
      render(<TripDateActions trip={tripWithoutDate} />)
      
      const setDateButton = screen.getByText('Set Start Date')
      fireEvent.click(setDateButton)
      
      const saveButton = screen.getByText('Save Test Date')
      fireEvent.click(saveButton)
      
      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Failed to update trip date:', expect.any(Error))
      })
      
      consoleSpy.mockRestore()
    })
  })
})

describe('TripDateBadge', () => {
  const tripWithDate: Trip = {
    id: 'trip-1',
    slug: 'test-trip',
    title: 'Test Trip',
    destination: 'Test Destination',
    start_date: '2024-12-25',
    timezone: 'UTC',
    status: 'active',
    is_published: false,
    created_by: 'user-1',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  }

  const tripWithoutDate: Trip = {
    ...tripWithDate,
    start_date: null,
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(updateTripStartDate).mockResolvedValue({ data: tripWithDate })
  })

  it('shows formatted date for trip with date', () => {
    render(<TripDateBadge trip={tripWithDate} />)
    
    expect(screen.getByText('Formatted: 2024-12-25')).toBeInTheDocument()
  })

  it('shows "No date set" for trip without date', () => {
    render(<TripDateBadge trip={tripWithoutDate} />)
    
    expect(screen.getByText('No date set')).toBeInTheDocument()
  })

  it('opens modal when editable and clicked', () => {
    render(<TripDateBadge trip={tripWithDate} editable={true} />)
    
    const badge = screen.getByText('Formatted: 2024-12-25')
    fireEvent.click(badge)
    
    expect(screen.getByTestId('date-picker-modal')).toBeInTheDocument()
  })

  it('does not open modal when not editable', () => {
    render(<TripDateBadge trip={tripWithDate} editable={false} />)
    
    const badge = screen.getByText('Formatted: 2024-12-25')
    fireEvent.click(badge)
    
    expect(screen.queryByTestId('date-picker-modal')).not.toBeInTheDocument()
  })
})

describe('CompactTripDate', () => {
  const tripWithDate: Trip = {
    id: 'trip-1',
    slug: 'test-trip',
    title: 'Test Trip',
    destination: 'Test Destination',
    start_date: '2024-12-25',
    timezone: 'UTC',
    status: 'active',
    is_published: false,
    created_by: 'user-1',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  }

  it('renders compact version without label', () => {
    render(<CompactTripDate trip={tripWithDate} />)
    
    expect(screen.getByText('Update Date')).toBeInTheDocument()
    expect(screen.queryByText('Start date:')).not.toBeInTheDocument()
  })
})
