/**
 * Enhanced Error Display Components for Phase 1 Migration
 * 
 * Displays structured error responses with:
 * - Error messages with proper styling
 * - Field-level validation errors
 * - Actionable suggestions
 * - Request tracking information
 */

import React from 'react';
import { AlertCircle, Info, Lightbulb, Copy, CheckCircle } from 'lucide-react';
import { APIError, APIClientError } from '@/lib/api/enhanced-client';

interface ErrorDisplayProps {
  error: APIError | APIClientError | string;
  className?: string;
  showSuggestions?: boolean;
  showRequestId?: boolean;
  onRetry?: () => void;
}

interface FieldErrorsProps {
  fieldErrors: Record<string, string[]>;
  className?: string;
}

interface SuggestionsProps {
  suggestions: string[];
  className?: string;
}

/**
 * Main error display component
 */
export function ErrorDisplay({ 
  error, 
  className = '', 
  showSuggestions = true, 
  showRequestId = false,
  onRetry 
}: ErrorDisplayProps) {
  // Handle different error types
  let apiError: APIError;
  let requestId: string | undefined;

  if (typeof error === 'string') {
    apiError = {
      error_code: 'GENERIC_ERROR',
      message: error,
      suggestions: ['Please try again or contact support if the problem persists']
    };
  } else if (error instanceof APIClientError) {
    apiError = error.error;
    requestId = error.requestId;
  } else {
    apiError = error;
  }

  const getErrorIcon = () => {
    switch (apiError.error_code) {
      case 'VALIDATION_ERROR':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      case 'AUTHENTICATION_REQUIRED':
      case 'PERMISSION_DENIED':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      case 'RESOURCE_NOT_FOUND':
        return <Info className="h-5 w-5 text-blue-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-red-500" />;
    }
  };

  const getErrorBorderColor = () => {
    switch (apiError.error_code) {
      case 'VALIDATION_ERROR':
        return 'border-yellow-200';
      case 'AUTHENTICATION_REQUIRED':
      case 'PERMISSION_DENIED':
        return 'border-red-200';
      case 'RESOURCE_NOT_FOUND':
        return 'border-blue-200';
      default:
        return 'border-red-200';
    }
  };

  const copyRequestId = () => {
    if (requestId) {
      navigator.clipboard.writeText(requestId);
    }
  };

  return (
    <div className={`rounded-lg border ${getErrorBorderColor()} bg-white p-4 ${className}`}>
      {/* Main error message */}
      <div className="flex items-start space-x-3">
        {getErrorIcon()}
        <div className="flex-1">
          <h3 className="text-sm font-medium text-gray-900">
            {apiError.message}
          </h3>
          
          {/* Error code for debugging */}
          <p className="mt-1 text-xs text-gray-500">
            Error Code: {apiError.error_code}
          </p>

          {/* Request ID for tracking */}
          {showRequestId && requestId && (
            <div className="mt-2 flex items-center space-x-2">
              <span className="text-xs text-gray-500">Request ID:</span>
              <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">
                {requestId}
              </code>
              <button
                onClick={copyRequestId}
                className="text-xs text-blue-600 hover:text-blue-800"
                title="Copy Request ID"
              >
                <Copy className="h-3 w-3" />
              </button>
            </div>
          )}

          {/* Field-level errors */}
          {apiError.field_errors && Object.keys(apiError.field_errors).length > 0 && (
            <div className="mt-3">
              <FieldErrors fieldErrors={apiError.field_errors} />
            </div>
          )}

          {/* Suggestions */}
          {showSuggestions && apiError.suggestions && apiError.suggestions.length > 0 && (
            <div className="mt-3">
              <Suggestions suggestions={apiError.suggestions} />
            </div>
          )}

          {/* Retry button */}
          {onRetry && (
            <div className="mt-3">
              <button
                onClick={onRetry}
                className="text-sm bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 transition-colors"
              >
                Try Again
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Field-level error display
 */
export function FieldErrors({ fieldErrors, className = '' }: FieldErrorsProps) {
  return (
    <div className={`space-y-2 ${className}`}>
      <h4 className="text-sm font-medium text-gray-700 flex items-center">
        <AlertCircle className="h-4 w-4 mr-1 text-yellow-500" />
        Field Errors:
      </h4>
      <div className="space-y-1">
        {Object.entries(fieldErrors).map(([field, errors]) => (
          <div key={field} className="text-sm">
            <span className="font-medium text-gray-600">
              {field.replace('body.', '').replace('_', ' ')}:
            </span>
            <ul className="ml-2 list-disc list-inside text-red-600">
              {errors.map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Suggestions display
 */
export function Suggestions({ suggestions, className = '' }: SuggestionsProps) {
  return (
    <div className={`space-y-2 ${className}`}>
      <h4 className="text-sm font-medium text-gray-700 flex items-center">
        <Lightbulb className="h-4 w-4 mr-1 text-blue-500" />
        Suggestions:
      </h4>
      <ul className="space-y-1">
        {suggestions.map((suggestion, index) => (
          <li key={index} className="text-sm text-gray-600 flex items-start">
            <span className="text-blue-500 mr-2">•</span>
            {suggestion}
          </li>
        ))}
      </ul>
    </div>
  );
}

/**
 * Success message component for 201/204 responses
 */
interface SuccessDisplayProps {
  message: string;
  type?: 'created' | 'deleted' | 'updated';
  className?: string;
  onDismiss?: () => void;
}

export function SuccessDisplay({ 
  message, 
  type = 'updated', 
  className = '',
  onDismiss 
}: SuccessDisplayProps) {
  const getSuccessMessage = () => {
    switch (type) {
      case 'created':
        return `✅ Created: ${message}`;
      case 'deleted':
        return `🗑️ Deleted: ${message}`;
      case 'updated':
        return `📝 Updated: ${message}`;
      default:
        return message;
    }
  };

  return (
    <div className={`rounded-lg border border-green-200 bg-green-50 p-4 ${className}`}>
      <div className="flex items-start space-x-3">
        <CheckCircle className="h-5 w-5 text-green-500" />
        <div className="flex-1">
          <p className="text-sm font-medium text-green-800">
            {getSuccessMessage()}
          </p>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-green-500 hover:text-green-700"
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Hook for handling API responses with proper error/success display
 */
export function useAPIResponseHandler() {
  const [error, setError] = React.useState<APIError | null>(null);
  const [success, setSuccess] = React.useState<{ message: string; type: 'created' | 'deleted' | 'updated' } | null>(null);

  // Note: in TSX files, generic arrow functions like `<T>(...) =>`
  // are parsed as JSX. Use a function declaration to avoid parsing issues.
  function handleResponse<T>(response: any, successMessage?: string) {
    if (response.success) {
      setError(null);
      if (successMessage) {
        const type = response.created ? 'created' : response.deleted ? 'deleted' : 'updated';
        setSuccess({ message: successMessage, type });
      }
      return response.data;
    } else {
      setSuccess(null);
      setError(response.error);
      return null;
    }
  }

  const clearMessages = () => {
    setError(null);
    setSuccess(null);
  };

  return {
    error,
    success,
    handleResponse,
    clearMessages,
    setError,
    setSuccess
  };
}
