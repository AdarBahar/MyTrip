/**
 * API Monitor Component
 * Real-time API activity monitoring for development
 */

'use client';

import React, { useState, useEffect } from 'react';
import { debugManager, ApiCall, formatDuration, getStatusColor } from '@/lib/debug';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Activity, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  TrendingUp,
  Zap,
  Globe
} from 'lucide-react';

interface ApiMonitorProps {
  className?: string;
  maxItems?: number;
}

export function ApiMonitor({ className = '', maxItems = 10 }: ApiMonitorProps) {
  const [apiCalls, setApiCalls] = useState<ApiCall[]>([]);
  const [isEnabled, setIsEnabled] = useState(false);

  useEffect(() => {
    setIsEnabled(debugManager.isDebugEnabled());
    setApiCalls(debugManager.getApiCalls().slice(0, maxItems));

    const unsubscribe = debugManager.subscribe((calls) => {
      setApiCalls(calls.slice(0, maxItems));
    });

    return unsubscribe;
  }, [maxItems]);

  const getStats = () => {
    const total = apiCalls.length;
    const successful = apiCalls.filter(call => 
      call.response && call.response.status >= 200 && call.response.status < 400
    ).length;
    const errors = apiCalls.filter(call => 
      call.response && call.response.status >= 400
    ).length;
    const pending = apiCalls.filter(call => !call.response).length;
    const avgDuration = apiCalls
      .filter(call => call.duration)
      .reduce((sum, call) => sum + (call.duration || 0), 0) / 
      (apiCalls.filter(call => call.duration).length || 1);

    return { total, successful, errors, pending, avgDuration };
  };

  const stats = getStats();

  if (!isEnabled) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Activity className="h-5 w-5 text-gray-400" />
            <span>API Monitor</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Globe className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500 mb-4">Debug mode is disabled</p>
            <Button 
              onClick={() => {
                debugManager.enable();
                setIsEnabled(true);
              }}
              size="sm"
            >
              Enable API Monitoring
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Activity className="h-5 w-5 text-green-600" />
            <span>API Monitor</span>
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          </div>
          <Badge variant="outline">{stats.total} calls</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="flex items-center justify-center space-x-1 mb-1">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <span className="text-2xl font-bold text-green-600">{stats.successful}</span>
            </div>
            <p className="text-xs text-gray-500">Success</p>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center space-x-1 mb-1">
              <XCircle className="h-4 w-4 text-red-600" />
              <span className="text-2xl font-bold text-red-600">{stats.errors}</span>
            </div>
            <p className="text-xs text-gray-500">Errors</p>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center space-x-1 mb-1">
              <Clock className="h-4 w-4 text-yellow-600" />
              <span className="text-2xl font-bold text-yellow-600">{stats.pending}</span>
            </div>
            <p className="text-xs text-gray-500">Pending</p>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center space-x-1 mb-1">
              <Zap className="h-4 w-4 text-blue-600" />
              <span className="text-2xl font-bold text-blue-600">
                {Math.round(stats.avgDuration)}
              </span>
            </div>
            <p className="text-xs text-gray-500">Avg ms</p>
          </div>
        </div>

        {/* Recent API Calls */}
        {apiCalls.length === 0 ? (
          <div className="text-center py-8">
            <Globe className="h-8 w-8 text-gray-400 mx-auto mb-2" />
            <p className="text-gray-500 text-sm">No API calls yet</p>
            <p className="text-gray-400 text-xs">Interact with the app to see API activity</p>
          </div>
        ) : (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-700 flex items-center space-x-2">
              <TrendingUp className="h-4 w-4" />
              <span>Recent Activity</span>
            </h4>
            <div className="space-y-1 max-h-64 overflow-y-auto">
              {apiCalls.map((call) => (
                <ApiCallItem key={call.id} call={call} />
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface ApiCallItemProps {
  call: ApiCall;
}

function ApiCallItem({ call }: ApiCallItemProps) {
  const getMethodColor = (method: string) => {
    switch (method.toUpperCase()) {
      case 'GET': return 'bg-blue-100 text-blue-800';
      case 'POST': return 'bg-green-100 text-green-800';
      case 'PUT': return 'bg-yellow-100 text-yellow-800';
      case 'PATCH': return 'bg-orange-100 text-orange-800';
      case 'DELETE': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status?: number) => {
    if (!status) return <Clock className="h-3 w-3 text-gray-400" />;
    if (status >= 400) return <XCircle className="h-3 w-3 text-red-500" />;
    if (status >= 300) return <AlertTriangle className="h-3 w-3 text-yellow-500" />;
    return <CheckCircle className="h-3 w-3 text-green-500" />;
  };

  const endpoint = call.request.url.replace(/^https?:\/\/[^\/]+/, '');
  const timeAgo = new Date(call.request.timestamp).toLocaleTimeString();

  return (
    <div className="flex items-center justify-between p-2 bg-gray-50 rounded text-xs">
      <div className="flex items-center space-x-2 flex-1 min-w-0">
        <Badge className={`${getMethodColor(call.request.method)} text-xs px-1 py-0`}>
          {call.request.method}
        </Badge>
        {getStatusIcon(call.response?.status)}
        <span className="font-mono truncate flex-1 min-w-0" title={endpoint}>
          {endpoint}
        </span>
      </div>
      
      <div className="flex items-center space-x-2 text-gray-500">
        {call.response && (
          <Badge 
            variant="outline" 
            className={`text-xs ${getStatusColor(call.response.status)}`}
          >
            {call.response.status}
          </Badge>
        )}
        <span className="text-xs">
          {call.duration ? formatDuration(call.duration) : timeAgo}
        </span>
      </div>
    </div>
  );
}

/**
 * Compact API Monitor for smaller spaces
 */
export function CompactApiMonitor({ className = '' }: { className?: string }) {
  const [apiCalls, setApiCalls] = useState<ApiCall[]>([]);
  const [isEnabled, setIsEnabled] = useState(false);

  useEffect(() => {
    setIsEnabled(debugManager.isDebugEnabled());
    setApiCalls(debugManager.getApiCalls().slice(0, 5));

    const unsubscribe = debugManager.subscribe((calls) => {
      setApiCalls(calls.slice(0, 5));
    });

    return unsubscribe;
  }, []);

  if (!isEnabled) return null;

  const recentCall = apiCalls[0];
  const errorCount = apiCalls.filter(call => 
    call.response && call.response.status >= 400
  ).length;

  return (
    <div className={`inline-flex items-center space-x-2 text-sm ${className}`}>
      <div className="flex items-center space-x-1">
        <Activity className="h-4 w-4 text-green-600" />
        <span className="text-green-600 font-medium">{apiCalls.length}</span>
      </div>
      
      {errorCount > 0 && (
        <div className="flex items-center space-x-1">
          <XCircle className="h-4 w-4 text-red-500" />
          <span className="text-red-500 font-medium">{errorCount}</span>
        </div>
      )}
      
      {recentCall && (
        <div className="text-gray-500">
          Last: {recentCall.request.method} {recentCall.request.url.split('/').pop()}
        </div>
      )}
    </div>
  );
}
