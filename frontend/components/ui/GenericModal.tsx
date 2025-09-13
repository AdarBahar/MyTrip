/**
 * Reusable Generic Modal Component
 * 
 * Flexible modal component that can be used for any content type including
 * forms, confirmations, content display, and complex interactions.
 */

import React, { useEffect } from 'react'
import { X } from 'lucide-react'

export interface ModalAction {
  label: string
  onClick: () => void
  variant?: 'primary' | 'secondary' | 'danger' | 'success'
  disabled?: boolean
  loading?: boolean
  icon?: React.ReactNode
}

export interface GenericModalProps {
  isOpen: boolean
  onClose: () => void
  
  // Content
  title?: string
  subtitle?: string
  children: React.ReactNode
  
  // Actions
  actions?: ModalAction[]
  showCloseButton?: boolean
  closeOnBackdropClick?: boolean
  closeOnEscape?: boolean
  
  // Styling
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
  className?: string
  headerClassName?: string
  bodyClassName?: string
  footerClassName?: string
  
  // Behavior
  preventClose?: boolean
  zIndex?: number
  
  // Custom renderers
  customHeader?: React.ReactNode
  customFooter?: React.ReactNode
}

export default function GenericModal({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  actions = [],
  showCloseButton = true,
  closeOnBackdropClick = true,
  closeOnEscape = true,
  size = 'md',
  className = "",
  headerClassName = "",
  bodyClassName = "",
  footerClassName = "",
  preventClose = false,
  zIndex = 50,
  customHeader,
  customFooter
}: GenericModalProps) {

  // Handle escape key
  useEffect(() => {
    if (!isOpen || !closeOnEscape || preventClose) return

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, closeOnEscape, preventClose, onClose])

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }

    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  if (!isOpen) return null

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && closeOnBackdropClick && !preventClose) {
      onClose()
    }
  }

  const handleClose = () => {
    if (!preventClose) {
      onClose()
    }
  }

  const getSizeClasses = () => {
    const sizeMap = {
      sm: 'max-w-sm',
      md: 'max-w-md',
      lg: 'max-w-lg',
      xl: 'max-w-xl',
      full: 'max-w-full mx-4'
    }
    return sizeMap[size]
  }

  const getActionVariantClasses = (variant: ModalAction['variant'] = 'secondary') => {
    const variantMap = {
      primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
      secondary: 'bg-gray-100 text-gray-700 hover:bg-gray-200 focus:ring-gray-500',
      danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
      success: 'bg-green-600 text-white hover:bg-green-700 focus:ring-green-500'
    }
    return variantMap[variant]
  }

  return (
    <div 
      className={`fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-${zIndex}`}
      onClick={handleBackdropClick}
    >
      <div className={`bg-white rounded-lg shadow-xl w-full ${getSizeClasses()} ${className}`}>
        {/* Header */}
        {(customHeader || title || showCloseButton) && (
          <div className={`flex items-center justify-between p-4 border-b border-gray-200 ${headerClassName}`}>
            {customHeader || (
              <div className="flex-1">
                {title && (
                  <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
                )}
                {subtitle && (
                  <p className="text-sm text-gray-600 mt-1">{subtitle}</p>
                )}
              </div>
            )}
            
            {showCloseButton && (
              <button
                onClick={handleClose}
                disabled={preventClose}
                className={`text-gray-400 hover:text-gray-600 transition-colors ${
                  preventClose ? 'opacity-50 cursor-not-allowed' : ''
                }`}
                aria-label="Close modal"
              >
                <X className="h-5 w-5" />
              </button>
            )}
          </div>
        )}

        {/* Body */}
        <div className={`p-6 ${bodyClassName}`}>
          {children}
        </div>

        {/* Footer */}
        {(customFooter || actions.length > 0) && (
          <div className={`flex items-center justify-end gap-3 p-4 border-t border-gray-200 ${footerClassName}`}>
            {customFooter || (
              <>
                {actions.map((action, index) => (
                  <button
                    key={index}
                    onClick={action.onClick}
                    disabled={action.disabled || action.loading}
                    className={`
                      px-4 py-2 rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2
                      disabled:opacity-50 disabled:cursor-not-allowed
                      ${getActionVariantClasses(action.variant)}
                      ${action.icon ? 'flex items-center gap-2' : ''}
                    `}
                  >
                    {action.icon && <span>{action.icon}</span>}
                    {action.loading ? 'Loading...' : action.label}
                  </button>
                ))}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// Utility function to create common modal actions
export const createModalActions = {
  cancel: (onCancel: () => void): ModalAction => ({
    label: 'Cancel',
    onClick: onCancel,
    variant: 'secondary'
  }),
  
  confirm: (onConfirm: () => void, loading = false): ModalAction => ({
    label: 'Confirm',
    onClick: onConfirm,
    variant: 'primary',
    loading
  }),
  
  delete: (onDelete: () => void, loading = false): ModalAction => ({
    label: 'Delete',
    onClick: onDelete,
    variant: 'danger',
    loading
  }),
  
  save: (onSave: () => void, loading = false): ModalAction => ({
    label: 'Save',
    onClick: onSave,
    variant: 'primary',
    loading
  }),
  
  create: (onCreate: () => void, loading = false): ModalAction => ({
    label: 'Create',
    onClick: onCreate,
    variant: 'success',
    loading
  })
}

// Specialized modal components using GenericModal

export const ConfirmationModal = ({
  isOpen,
  onClose,
  onConfirm,
  title = "Confirm Action",
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  variant = 'primary',
  loading = false
}: {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  title?: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'primary' | 'danger'
  loading?: boolean
}) => (
  <GenericModal
    isOpen={isOpen}
    onClose={onClose}
    title={title}
    size="sm"
    actions={[
      createModalActions.cancel(onClose),
      {
        label: confirmLabel,
        onClick: onConfirm,
        variant,
        loading
      }
    ]}
  >
    <p className="text-gray-600">{message}</p>
  </GenericModal>
)

export const FormModal = ({
  isOpen,
  onClose,
  onSubmit,
  title,
  children,
  submitLabel = "Submit",
  loading = false,
  preventClose = false
}: {
  isOpen: boolean
  onClose: () => void
  onSubmit: () => void
  title: string
  children: React.ReactNode
  submitLabel?: string
  loading?: boolean
  preventClose?: boolean
}) => (
  <GenericModal
    isOpen={isOpen}
    onClose={onClose}
    title={title}
    preventClose={preventClose}
    actions={[
      createModalActions.cancel(onClose),
      createModalActions.save(onSubmit, loading)
    ]}
  >
    {children}
  </GenericModal>
)

export const InfoModal = ({
  isOpen,
  onClose,
  title,
  children,
  size = 'md'
}: {
  isOpen: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl'
}) => (
  <GenericModal
    isOpen={isOpen}
    onClose={onClose}
    title={title}
    size={size}
    actions={[
      {
        label: 'Close',
        onClick: onClose,
        variant: 'secondary'
      }
    ]}
  >
    {children}
  </GenericModal>
)
