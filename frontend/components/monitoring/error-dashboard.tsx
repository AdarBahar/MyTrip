/**
 * Error Monitoring Dashboard Component
 * 
 * Displays error analytics and patterns for system monitoring
 */

'use client';

import React, { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api/enhanced-client';
import { ErrorDisplay, useAPIResponseHandler } from '@/components/ui/error-display';
import { AlertTriangle, TrendingUp, TrendingDown, Minus, Activity, Users, Clock, AlertCircle } from 'lucide-react';

interface ErrorPattern {
  error_code: string;
  count: number;
  endpoints: string[];
  common_messages: string[];
}

interface ErrorTrends {
  total_errors: number;
  unique_error_codes: number;
  daily_breakdown: Record<string, Record<string, number>>;
  top_error_codes: string[];
  error_rate_trend: 'increasing' | 'decreasing' | 'stable' | 'insufficient_data';
}

interface ErrorReport {
  report_generated: string;
  time_period: string;
  summary: {
    total_errors: number;
    unique_error_codes: number;
    most_common_error: string | null;
  };
  error_patterns: ErrorPattern[];
  trends: ErrorTrends;
}

export function ErrorDashboard() {
  const [report, setReport] = useState<ErrorReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(24);
  const { error, handleResponse } = useAPIResponseHandler();

  const loadErrorReport = async () => {
    setLoading(true);
    
    try {
      const response = await apiClient.get<ErrorReport>(`/monitoring/errors/report?hours=${timeRange}`);
      const result = handleResponse(response);
      
      if (result) {
        setReport(result);
      }
    } catch (err) {
      console.error('Failed to load error report:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadErrorReport();
  }, [timeRange]);

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'increasing':
        return <TrendingUp className="h-4 w-4 text-red-500" />;
      case 'decreasing':
        return <TrendingDown className="h-4 w-4 text-green-500" />;
      case 'stable':
        return <Minus className="h-4 w-4 text-blue-500" />;
      default:
        return <Activity className="h-4 w-4 text-gray-500" />;
    }
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'increasing':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'decreasing':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'stable':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading error analytics...</span>
      </div>
    );
  }

  if (error) {
    return (
      <ErrorDisplay
        error={error}
        onRetry={loadErrorReport}
        className="m-4"
      />
    );
  }

  if (!report) {
    return (
      <div className="text-center p-8 text-gray-500">
        No error data available
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Error Monitoring Dashboard</h1>
          <p className="text-gray-600">System error analytics and patterns</p>
        </div>
        
        <div className="flex items-center space-x-4">
          <select
            id="time-range-select"
            name="time-range"
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            <option value={1}>Last Hour</option>
            <option value={6}>Last 6 Hours</option>
            <option value={24}>Last 24 Hours</option>
            <option value={72}>Last 3 Days</option>
            <option value={168}>Last Week</option>
          </select>
          
          <button
            onClick={loadErrorReport}
            className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center">
            <AlertTriangle className="h-8 w-8 text-red-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Total Errors</p>
              <p className="text-2xl font-bold text-gray-900">{report.summary.total_errors}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center">
            <AlertCircle className="h-8 w-8 text-orange-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Error Types</p>
              <p className="text-2xl font-bold text-gray-900">{report.summary.unique_error_codes}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center">
            <Clock className="h-8 w-8 text-blue-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Time Period</p>
              <p className="text-lg font-bold text-gray-900">{report.time_period}</p>
            </div>
          </div>
        </div>

        <div className={`rounded-lg border p-4 ${getTrendColor(report.trends.error_rate_trend)}`}>
          <div className="flex items-center">
            {getTrendIcon(report.trends.error_rate_trend)}
            <div className="ml-3">
              <p className="text-sm font-medium">Error Trend</p>
              <p className="text-lg font-bold capitalize">{report.trends.error_rate_trend}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Error Patterns */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Error Patterns</h2>
          <p className="text-sm text-gray-600">Most common error types and their frequency</p>
        </div>
        
        <div className="p-6">
          {report.error_patterns.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <AlertCircle className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No error patterns found in this time period</p>
              <p className="text-sm">This is good news! Your API is running smoothly.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {report.error_patterns.map((pattern, index) => (
                <div key={pattern.error_code} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h3 className="font-medium text-gray-900">{pattern.error_code}</h3>
                      <p className="text-sm text-gray-600">{pattern.count} occurrences</p>
                    </div>
                    <span className="bg-red-100 text-red-800 text-xs font-medium px-2.5 py-0.5 rounded">
                      #{index + 1}
                    </span>
                  </div>
                  
                  <div className="space-y-2">
                    <div>
                      <p className="text-xs font-medium text-gray-700 mb-1">Affected Endpoints:</p>
                      <div className="flex flex-wrap gap-1">
                        {pattern.endpoints.map((endpoint) => (
                          <span key={endpoint} className="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded">
                            {endpoint}
                          </span>
                        ))}
                      </div>
                    </div>
                    
                    {pattern.common_messages.length > 0 && (
                      <div>
                        <p className="text-xs font-medium text-gray-700 mb-1">Common Messages:</p>
                        <ul className="text-xs text-gray-600 space-y-1">
                          {pattern.common_messages.slice(0, 2).map((message, idx) => (
                            <li key={idx} className="truncate">• {message}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Top Error Codes */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Top Error Codes</h2>
          <p className="text-sm text-gray-600">Most frequent error types across all endpoints</p>
        </div>
        
        <div className="p-6">
          {report.trends.top_error_codes.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No error codes to display</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {report.trends.top_error_codes.map((code, index) => (
                <div key={code} className="bg-gray-50 rounded-lg p-3">
                  <div className="flex justify-between items-center">
                    <span className="font-medium text-gray-900">{code}</span>
                    <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-1 rounded">
                      #{index + 1}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Report Metadata */}
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="flex justify-between items-center text-sm text-gray-600">
          <span>Report generated: {new Date(report.report_generated).toLocaleString()}</span>
          <span>Time period: {report.time_period}</span>
        </div>
      </div>
    </div>
  );
}

export default ErrorDashboard;
