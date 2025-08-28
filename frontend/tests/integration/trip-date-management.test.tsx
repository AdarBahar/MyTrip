/**
 * Integration tests for Trip Date Management System
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { TripDateActions } from '@/components/trips/trip-date-actions'
import type { Trip } from '@/lib/api/trips'

// Mock the entire API module
vi.mock('@/lib/api/trips', async () => {
  const actual = await vi.importActual('@/lib/api/trips')
  return {
    ...actual,
    updateTripStartDate: vi.fn(),
    formatTripDate: (date: string | null | undefined) => {
      if (!date) return 'No date set'
      try {
        return new Date(date).toLocaleDateString('en-US', {
          weekday: 'long',
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        })
      } catch {
        return date
      }
    },
    isDateInPast: (date: string) => {
      if (!date) return false
      try {
        const inputDate = new Date(date)
        const today = new Date()
        today.setHours(0, 0, 0, 0)
        return inputDate < today
      } catch {
        return false
      }
    },
  }
})

// Mock debug system
vi.mock('@/components/minimal-debug', () => ({
  simpleDebugManager: {
    logApiCall: vi.fn(),
  },
}))

const { updateTripStartDate } = await import('@/lib/api/trips')

describe('Trip Date Management Integration', () => {
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

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('completes full flow: set date for trip without date', async () => {
    // Mock successful API response
    const updatedTrip = { ...tripWithoutDate, start_date: '2024-12-25' }
    vi.mocked(updateTripStartDate).mockResolvedValue({ data: updatedTrip })

    render(<TripDateActions trip={tripWithoutDate} onTripUpdate={mockOnTripUpdate} />)

    // Initial state: should show "Set Start Date" button
    expect(screen.getByText('Set Start Date')).toBeInTheDocument()
    expect(screen.getByText('Not set')).toBeInTheDocument()

    // Click "Set Start Date" button
    const setDateButton = screen.getByText('Set Start Date')
    fireEvent.click(setDateButton)

    // Modal should open
    expect(screen.getByText('Set Trip Start Date')).toBeInTheDocument()
    expect(screen.getByLabelText('Start Date')).toBeInTheDocument()

    // Enter a date
    const dateInput = screen.getByLabelText('Start Date')
    fireEvent.change(dateInput, { target: { value: '2024-12-25' } })

    // Should show formatted date preview
    await waitFor(() => {
      expect(screen.getByText(/Wednesday, December 25, 2024/)).toBeInTheDocument()
    })

    // Click save
    const saveButton = screen.getByText('Save Date')
    fireEvent.click(saveButton)

    // Should call API
    await waitFor(() => {
      expect(updateTripStartDate).toHaveBeenCalledWith('trip-1', '2024-12-25')
    })

    // Should call onTripUpdate callback
    expect(mockOnTripUpdate).toHaveBeenCalledWith(updatedTrip)
  })

  it('completes full flow: update existing date', async () => {
    const tripWithDate = { ...tripWithoutDate, start_date: '2024-12-20' }
    const updatedTrip = { ...tripWithDate, start_date: '2024-12-25' }
    vi.mocked(updateTripStartDate).mockResolvedValue({ data: updatedTrip })

    render(<TripDateActions trip={tripWithDate} onTripUpdate={mockOnTripUpdate} />)

    // Should show current date and update button
    expect(screen.getByText('Wednesday, December 20, 2024')).toBeInTheDocument()
    expect(screen.getByText('Update Date')).toBeInTheDocument()

    // Click "Update Date" button
    const updateButton = screen.getByText('Update Date')
    fireEvent.click(updateButton)

    // Modal should open with current date
    expect(screen.getByText('Update Trip Date')).toBeInTheDocument()
    const dateInput = screen.getByLabelText('Start Date') as HTMLInputElement
    expect(dateInput.value).toBe('2024-12-20')

    // Change the date
    fireEvent.change(dateInput, { target: { value: '2024-12-25' } })

    // Save the change
    const saveButton = screen.getByText('Save Date')
    fireEvent.click(saveButton)

    // Should call API with new date
    await waitFor(() => {
      expect(updateTripStartDate).toHaveBeenCalledWith('trip-1', '2024-12-25')
    })

    expect(mockOnTripUpdate).toHaveBeenCalledWith(updatedTrip)
  })

  it('completes full flow: clear existing date', async () => {
    const tripWithDate = { ...tripWithoutDate, start_date: '2024-12-25' }
    const updatedTrip = { ...tripWithDate, start_date: null }
    vi.mocked(updateTripStartDate).mockResolvedValue({ data: updatedTrip })

    render(<TripDateActions trip={tripWithDate} onTripUpdate={mockOnTripUpdate} />)

    // Click "Update Date" button
    const updateButton = screen.getByText('Update Date')
    fireEvent.click(updateButton)

    // Modal should open with clear option
    expect(screen.getByText('Clear Date')).toBeInTheDocument()

    // Click clear
    const clearButton = screen.getByText('Clear Date')
    fireEvent.click(clearButton)

    // Should call API with null
    await waitFor(() => {
      expect(updateTripStartDate).toHaveBeenCalledWith('trip-1', null)
    })

    expect(mockOnTripUpdate).toHaveBeenCalledWith(updatedTrip)
  })

  it('handles API errors gracefully', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.mocked(updateTripStartDate).mockResolvedValue({ error: 'Failed to update trip' })

    render(<TripDateActions trip={tripWithoutDate} onTripUpdate={mockOnTripUpdate} />)

    // Open modal and try to save
    const setDateButton = screen.getByText('Set Start Date')
    fireEvent.click(setDateButton)

    const dateInput = screen.getByLabelText('Start Date')
    fireEvent.change(dateInput, { target: { value: '2024-12-25' } })

    const saveButton = screen.getByText('Save Date')
    fireEvent.click(saveButton)

    // Should show error in modal
    await waitFor(() => {
      expect(screen.getByText('Failed to update trip')).toBeInTheDocument()
    })

    // Should not call onTripUpdate
    expect(mockOnTripUpdate).not.toHaveBeenCalled()

    consoleSpy.mockRestore()
  })

  it('validates date input and prevents invalid submissions', async () => {
    render(<TripDateActions trip={tripWithoutDate} onTripUpdate={mockOnTripUpdate} />)

    // Open modal
    const setDateButton = screen.getByText('Set Start Date')
    fireEvent.click(setDateButton)

    // Enter invalid date
    const dateInput = screen.getByLabelText('Start Date')
    fireEvent.change(dateInput, { target: { value: 'invalid-date' } })

    // Try to save
    const saveButton = screen.getByText('Save Date')
    fireEvent.click(saveButton)

    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText('Please enter a valid date')).toBeInTheDocument()
    })

    // Should not call API
    expect(updateTripStartDate).not.toHaveBeenCalled()
    expect(mockOnTripUpdate).not.toHaveBeenCalled()
  })

  it('shows loading state during API call', async () => {
    // Create a promise that we can control
    let resolvePromise: (value: any) => void
    const apiPromise = new Promise((resolve) => {
      resolvePromise = resolve
    })
    vi.mocked(updateTripStartDate).mockReturnValue(apiPromise)

    render(<TripDateActions trip={tripWithoutDate} onTripUpdate={mockOnTripUpdate} />)

    // Open modal and enter date
    const setDateButton = screen.getByText('Set Start Date')
    fireEvent.click(setDateButton)

    const dateInput = screen.getByLabelText('Start Date')
    fireEvent.change(dateInput, { target: { value: '2024-12-25' } })

    // Click save
    const saveButton = screen.getByText('Save Date')
    fireEvent.click(saveButton)

    // Should show loading state
    expect(screen.getByText('Saving...')).toBeInTheDocument()
    expect(saveButton).toBeDisabled()

    // Resolve the promise
    resolvePromise!({ data: { ...tripWithoutDate, start_date: '2024-12-25' } })

    // Loading state should disappear
    await waitFor(() => {
      expect(screen.queryByText('Saving...')).not.toBeInTheDocument()
    })
  })

  it('closes modal after successful save', async () => {
    const updatedTrip = { ...tripWithoutDate, start_date: '2024-12-25' }
    vi.mocked(updateTripStartDate).mockResolvedValue({ data: updatedTrip })

    render(<TripDateActions trip={tripWithoutDate} onTripUpdate={mockOnTripUpdate} />)

    // Open modal
    const setDateButton = screen.getByText('Set Start Date')
    fireEvent.click(setDateButton)

    expect(screen.getByText('Set Trip Start Date')).toBeInTheDocument()

    // Enter date and save
    const dateInput = screen.getByLabelText('Start Date')
    fireEvent.change(dateInput, { target: { value: '2024-12-25' } })

    const saveButton = screen.getByText('Save Date')
    fireEvent.click(saveButton)

    // Modal should close after successful save
    await waitFor(() => {
      expect(screen.queryByText('Set Trip Start Date')).not.toBeInTheDocument()
    })
  })

  it('allows canceling modal without making changes', () => {
    render(<TripDateActions trip={tripWithoutDate} onTripUpdate={mockOnTripUpdate} />)

    // Open modal
    const setDateButton = screen.getByText('Set Start Date')
    fireEvent.click(setDateButton)

    expect(screen.getByText('Set Trip Start Date')).toBeInTheDocument()

    // Cancel
    const cancelButton = screen.getByText('Cancel')
    fireEvent.click(cancelButton)

    // Modal should close
    expect(screen.queryByText('Set Trip Start Date')).not.toBeInTheDocument()

    // No API calls should be made
    expect(updateTripStartDate).not.toHaveBeenCalled()
    expect(mockOnTripUpdate).not.toHaveBeenCalled()
  })
})
