/**
 * Tests for DatePickerModal component
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { DatePickerModal } from '@/components/trips/date-picker-modal'

// Mock the debug system
vi.mock('@/components/minimal-debug', () => ({
  simpleDebugManager: {
    logApiCall: vi.fn(),
  },
}))

describe('DatePickerModal', () => {
  const mockOnClose = vi.fn()
  const mockOnSave = vi.fn()

  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    onSave: mockOnSave,
    title: 'Test Date Picker',
    description: 'Test description',
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockOnSave.mockResolvedValue(undefined)
  })

  it('renders when open', () => {
    render(<DatePickerModal {...defaultProps} />)
    
    expect(screen.getByText('Test Date Picker')).toBeInTheDocument()
    expect(screen.getByText('Test description')).toBeInTheDocument()
    expect(screen.getByLabelText('Start Date')).toBeInTheDocument()
    expect(screen.getByText('Save Date')).toBeInTheDocument()
    expect(screen.getByText('Cancel')).toBeInTheDocument()
  })

  it('does not render when closed', () => {
    render(<DatePickerModal {...defaultProps} isOpen={false} />)
    
    expect(screen.queryByText('Test Date Picker')).not.toBeInTheDocument()
  })

  it('displays current date when provided', () => {
    const currentDate = '2024-12-25'
    render(<DatePickerModal {...defaultProps} currentDate={currentDate} />)
    
    const dateInput = screen.getByLabelText('Start Date') as HTMLInputElement
    expect(dateInput.value).toBe(currentDate)
  })

  it('shows formatted date preview when valid date is entered', async () => {
    render(<DatePickerModal {...defaultProps} />)
    
    const dateInput = screen.getByLabelText('Start Date')
    fireEvent.change(dateInput, { target: { value: '2024-12-25' } })
    
    await waitFor(() => {
      expect(screen.getByText(/Wednesday, December 25, 2024/)).toBeInTheDocument()
    })
  })

  it('calls onSave with selected date when save button is clicked', async () => {
    render(<DatePickerModal {...defaultProps} />)
    
    const dateInput = screen.getByLabelText('Start Date')
    const saveButton = screen.getByText('Save Date')
    
    fireEvent.change(dateInput, { target: { value: '2024-12-25' } })
    fireEvent.click(saveButton)
    
    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalledWith('2024-12-25')
    })
  })

  it('calls onSave with null when clear button is clicked', async () => {
    render(<DatePickerModal {...defaultProps} currentDate="2024-12-25" allowClear={true} />)
    
    const clearButton = screen.getByText('Clear Date')
    fireEvent.click(clearButton)
    
    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalledWith(null)
    })
  })

  it('calls onClose when cancel button is clicked', () => {
    render(<DatePickerModal {...defaultProps} />)
    
    const cancelButton = screen.getByText('Cancel')
    fireEvent.click(cancelButton)
    
    expect(mockOnClose).toHaveBeenCalled()
  })

  it('calls onClose when clicking outside modal', () => {
    render(<DatePickerModal {...defaultProps} />)
    
    const backdrop = screen.getByText('Test Date Picker').closest('div')?.parentElement
    if (backdrop) {
      fireEvent.click(backdrop)
      expect(mockOnClose).toHaveBeenCalled()
    }
  })

  it('calls onClose when X button is clicked', () => {
    render(<DatePickerModal {...defaultProps} />)

    // Find the X button by looking for the button with X icon
    const buttons = screen.getAllByRole('button')
    const closeButton = buttons.find(button => button.textContent?.includes('×') || button.querySelector('svg'))

    if (closeButton) {
      fireEvent.click(closeButton)
      expect(mockOnClose).toHaveBeenCalled()
    }
  })

  it('shows error message when save fails', async () => {
    const errorMessage = 'Failed to save date'
    mockOnSave.mockRejectedValue(new Error(errorMessage))
    
    render(<DatePickerModal {...defaultProps} />)
    
    const dateInput = screen.getByLabelText('Start Date')
    const saveButton = screen.getByText('Save Date')
    
    fireEvent.change(dateInput, { target: { value: '2024-12-25' } })
    fireEvent.click(saveButton)
    
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
  })

  it('shows loading state when saving', async () => {
    let resolvePromise: (value: unknown) => void
    const savePromise = new Promise((resolve) => {
      resolvePromise = resolve
    })
    mockOnSave.mockReturnValue(savePromise)
    
    render(<DatePickerModal {...defaultProps} />)
    
    const dateInput = screen.getByLabelText('Start Date')
    const saveButton = screen.getByText('Save Date')
    
    fireEvent.change(dateInput, { target: { value: '2024-12-25' } })
    fireEvent.click(saveButton)
    
    // Should show loading state
    expect(screen.getByText('Saving...')).toBeInTheDocument()
    expect(saveButton).toBeDisabled()
    
    // Resolve the promise
    resolvePromise!(undefined)
    
    await waitFor(() => {
      expect(screen.queryByText('Saving...')).not.toBeInTheDocument()
    })
  })

  it('validates date format and shows error for invalid dates', async () => {
    render(<DatePickerModal {...defaultProps} />)
    
    const dateInput = screen.getByLabelText('Start Date')
    const saveButton = screen.getByText('Save Date')
    
    // Enter invalid date
    fireEvent.change(dateInput, { target: { value: 'invalid-date' } })
    fireEvent.click(saveButton)
    
    await waitFor(() => {
      expect(screen.getByText('Please enter a valid date')).toBeInTheDocument()
    })
    
    expect(mockOnSave).not.toHaveBeenCalled()
  })

  it('disables save button for invalid dates', () => {
    render(<DatePickerModal {...defaultProps} />)
    
    const dateInput = screen.getByLabelText('Start Date')
    const saveButton = screen.getByText('Save Date')
    
    fireEvent.change(dateInput, { target: { value: 'invalid-date' } })
    
    expect(saveButton).toBeDisabled()
  })

  it('does not show clear button when allowClear is false', () => {
    render(<DatePickerModal {...defaultProps} currentDate="2024-12-25" allowClear={false} />)
    
    expect(screen.queryByText('Clear Date')).not.toBeInTheDocument()
  })

  it('shows clear button when allowClear is true and currentDate exists', () => {
    render(<DatePickerModal {...defaultProps} currentDate="2024-12-25" allowClear={true} />)
    
    expect(screen.getByText('Clear Date')).toBeInTheDocument()
  })

  it('resets form when modal reopens', () => {
    const { rerender } = render(<DatePickerModal {...defaultProps} isOpen={false} />)
    
    // Open modal and enter date
    rerender(<DatePickerModal {...defaultProps} isOpen={true} />)
    
    const dateInput = screen.getByLabelText('Start Date') as HTMLInputElement
    fireEvent.change(dateInput, { target: { value: '2024-12-25' } })
    
    // Close and reopen modal
    rerender(<DatePickerModal {...defaultProps} isOpen={false} />)
    rerender(<DatePickerModal {...defaultProps} isOpen={true} currentDate="2024-01-01" />)
    
    // Should reset to currentDate
    expect(dateInput.value).toBe('2024-01-01')
  })

  it('sets minimum date to today', () => {
    render(<DatePickerModal {...defaultProps} />)
    
    const dateInput = screen.getByLabelText('Start Date') as HTMLInputElement
    const today = new Date().toISOString().split('T')[0]
    
    expect(dateInput.min).toBe(today)
  })
})
