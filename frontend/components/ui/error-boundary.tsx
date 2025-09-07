/**
 * Enhanced Error Boundary Components
 * 
 * Provides comprehensive error handling for React component trees
 * with user-friendly fallbacks and error reporting
 */

'use client';

import React, { Component, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react';

interface ErrorInfo {
  componentStack: string;
  errorBoundary?: string;
  errorBoundaryStack?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
  eventId?: string;
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  showDetails?: boolean;
  level?: 'page' | 'section' | 'component';
}

// Generic Error Boundary
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error,
      eventId: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error Boundary caught an error:', error, errorInfo);
    
    this.setState({
      errorInfo
    });

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Report to error tracking service (e.g., Sentry)
    this.reportError(error, errorInfo);
  }

  private reportError = (error: Error, errorInfo: ErrorInfo) => {
    // In a real app, you would send this to your error tracking service
    const errorReport = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      eventId: this.state.eventId
    };

    // Example: Send to error tracking service
    // Sentry.captureException(error, { contexts: { react: errorInfo } });
    
    console.error('Error Report:', errorReport);
  };

  private handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  private handleReload = () => {
    window.location.reload();
  };

  private handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default fallback based on error level
      return this.renderDefaultFallback();
    }

    return this.props.children;
  }

  private renderDefaultFallback() {
    const { level = 'component', showDetails = false } = this.props;
    const { error, errorInfo, eventId } = this.state;

    if (level === 'page') {
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6 text-center">
            <AlertTriangle className="h-16 w-16 text-red-500 mx-auto mb-4" />
            <h1 className="text-xl font-bold text-gray-900 mb-2">
              Oops! Something went wrong
            </h1>
            <p className="text-gray-600 mb-6">
              We encountered an unexpected error. Our team has been notified and is working on a fix.
            </p>
            
            <div className="space-y-3">
              <button
                onClick={this.handleRetry}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 flex items-center justify-center"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </button>
              
              <button
                onClick={this.handleReload}
                className="w-full bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700 flex items-center justify-center"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Reload Page
              </button>
              
              <button
                onClick={this.handleGoHome}
                className="w-full border border-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-50 flex items-center justify-center"
              >
                <Home className="h-4 w-4 mr-2" />
                Go Home
              </button>
            </div>

            {showDetails && error && (
              <details className="mt-6 text-left">
                <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
                  <Bug className="inline h-4 w-4 mr-1" />
                  Technical Details
                </summary>
                <div className="mt-2 p-3 bg-gray-100 rounded text-xs font-mono text-gray-700 overflow-auto max-h-32">
                  <div className="mb-2">
                    <strong>Error:</strong> {error.message}
                  </div>
                  <div className="mb-2">
                    <strong>Event ID:</strong> {eventId}
                  </div>
                  {error.stack && (
                    <div>
                      <strong>Stack:</strong>
                      <pre className="whitespace-pre-wrap">{error.stack}</pre>
                    </div>
                  )}
                </div>
              </details>
            )}
          </div>
        </div>
      );
    }

    if (level === 'section') {
      return (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Section Error
          </h3>
          <p className="text-gray-600 mb-4">
            This section encountered an error and couldn't load properly.
          </p>
          <button
            onClick={this.handleRetry}
            className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 flex items-center mx-auto"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </button>
        </div>
      );
    }

    // Component level (default)
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 text-center">
        <AlertTriangle className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
        <p className="text-sm text-gray-700 mb-2">
          Component failed to load
        </p>
        <button
          onClick={this.handleRetry}
          className="text-xs bg-yellow-600 text-white px-3 py-1 rounded hover:bg-yellow-700"
        >
          Retry
        </button>
      </div>
    );
  }
}

// Specialized Error Boundaries

export class PageErrorBoundary extends Component<
  Omit<ErrorBoundaryProps, 'level'>,
  ErrorBoundaryState
> {
  render() {
    return (
      <ErrorBoundary {...this.props} level="page">
        {this.props.children}
      </ErrorBoundary>
    );
  }
}

export class SectionErrorBoundary extends Component<
  Omit<ErrorBoundaryProps, 'level'>,
  ErrorBoundaryState
> {
  render() {
    return (
      <ErrorBoundary {...this.props} level="section">
        {this.props.children}
      </ErrorBoundary>
    );
  }
}

export class ComponentErrorBoundary extends Component<
  Omit<ErrorBoundaryProps, 'level'>,
  ErrorBoundaryState
> {
  render() {
    return (
      <ErrorBoundary {...this.props} level="component">
        {this.props.children}
      </ErrorBoundary>
    );
  }
}

// HOC for wrapping components with error boundaries
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<ErrorBoundaryProps, 'children'>
) {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
}

// Hook for error reporting in functional components
export const useErrorHandler = () => {
  const reportError = React.useCallback((error: Error, errorInfo?: any) => {
    console.error('Manual error report:', error, errorInfo);
    
    // Report to error tracking service
    const errorReport = {
      message: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      additionalInfo: errorInfo
    };

    // Send to error tracking service
    console.error('Error Report:', errorReport);
  }, []);

  return { reportError };
};

export default ErrorBoundary;
