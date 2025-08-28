/**
 * Debug Panel Component
 * Shows API requests and responses for development
 */

'use client';

import React, { useState, useEffect } from 'react';
import { debugManager, ApiCall, formatDuration, getStatusColor, getStatusBgColor } from '@/lib/debug';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogDescription,
} from '@/components/ui/dialog';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { 
  Bug, 
  Trash2, 
  ChevronDown, 
  ChevronRight,
  Clock,
  Globe,
  AlertCircle,
  CheckCircle,
  XCircle,
  Eye,
  EyeOff
} from 'lucide-react';

interface DebugPanelProps {
  className?: string;
}

export function DebugPanel({ className = '' }: DebugPanelProps) {
  const [apiCalls, setApiCalls] = useState<ApiCall[]>([]);
  const [isEnabled, setIsEnabled] = useState(false);
  const [selectedCall, setSelectedCall] = useState<ApiCall | null>(null);

  useEffect(() => {
    setIsEnabled(debugManager.isDebugEnabled());
    setApiCalls(debugManager.getApiCalls());

    const unsubscribe = debugManager.subscribe((calls) => {
      setApiCalls(calls);
    });

    return unsubscribe;
  }, []);

  const toggleDebugMode = () => {
    if (isEnabled) {
      debugManager.disable();
      setIsEnabled(false);
    } else {
      debugManager.enable();
      setIsEnabled(true);
    }
  };

  const clearApiCalls = () => {
    debugManager.clearApiCalls();
  };

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
    if (!status) return <Clock className="h-4 w-4 text-gray-400" />;
    if (status >= 400) return <XCircle className="h-4 w-4 text-red-500" />;
    if (status >= 300) return <AlertCircle className="h-4 w-4 text-yellow-500" />;
    return <CheckCircle className="h-4 w-4 text-green-500" />;
  };

  return (
    <div className={`fixed bottom-4 right-4 z-50 ${className}`}>
      <Dialog>
        <DialogTrigger asChild>
          <Button
            variant={isEnabled ? "default" : "outline"}
            size="sm"
            className="shadow-lg"
          >
            <Bug className="h-4 w-4 mr-2" />
            Debug {isEnabled && `(${apiCalls.length})`}
          </Button>
        </DialogTrigger>
        
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between">
              <span className="flex items-center space-x-2">
                <Bug className="h-5 w-5" />
                <span>API Debug Panel</span>
              </span>
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearApiCalls}
                  disabled={apiCalls.length === 0}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Clear
                </Button>
                <Button
                  variant={isEnabled ? "destructive" : "default"}
                  size="sm"
                  onClick={toggleDebugMode}
                >
                  {isEnabled ? (
                    <>
                      <EyeOff className="h-4 w-4 mr-2" />
                      Disable
                    </>
                  ) : (
                    <>
                      <Eye className="h-4 w-4 mr-2" />
                      Enable
                    </>
                  )}
                </Button>
              </div>
            </DialogTitle>
            <DialogDescription className="sr-only" id="debug-panel-desc">
              Shows API requests and responses for development and debugging purposes.
            </DialogDescription>
          </DialogHeader>

          <div className="flex-1 overflow-hidden">
            {!isEnabled ? (
              <div className="flex items-center justify-center h-full text-center">
                <div>
                  <Bug className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Debug Mode Disabled
                  </h3>
                  <p className="text-gray-500 mb-4">
                    Enable debug mode to monitor API requests and responses
                  </p>
                  <Button onClick={toggleDebugMode}>
                    <Eye className="h-4 w-4 mr-2" />
                    Enable Debug Mode
                  </Button>
                </div>
              </div>
            ) : apiCalls.length === 0 ? (
              <div className="flex items-center justify-center h-full text-center">
                <div>
                  <Globe className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    No API Calls Yet
                  </h3>
                  <p className="text-gray-500">
                    API requests and responses will appear here when you interact with the app
                  </p>
                </div>
              </div>
            ) : (
              <div className="h-full overflow-auto space-y-2">
                {apiCalls.map((call) => (
                  <ApiCallCard
                    key={call.id}
                    call={call}
                    onSelect={setSelectedCall}
                    getMethodColor={getMethodColor}
                    getStatusIcon={getStatusIcon}
                  />
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Detailed API Call Dialog */}
      {selectedCall && (
        <ApiCallDetailDialog
          call={selectedCall}
          open={!!selectedCall}
          onOpenChange={(open) => !open && setSelectedCall(null)}
        />
      )}
    </div>
  );
}

interface ApiCallCardProps {
  call: ApiCall;
  onSelect: (call: ApiCall) => void;
  getMethodColor: (method: string) => string;
  getStatusIcon: (status?: number) => React.ReactNode;
}

function ApiCallCard({ call, onSelect, getMethodColor, getStatusIcon }: ApiCallCardProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Card className="cursor-pointer hover:bg-gray-50" onClick={() => onSelect(call)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Badge className={getMethodColor(call.request.method)}>
              {call.request.method}
            </Badge>
            {getStatusIcon(call.response?.status)}
            <span className="font-mono text-sm">
              {call.request.url.replace(/^https?:\/\/[^\/]+/, '')}
            </span>
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            {call.response && (
              <Badge 
                variant="outline" 
                className={getStatusColor(call.response.status)}
              >
                {call.response.status}
              </Badge>
            )}
            <span>{formatDuration(call.duration || 0)}</span>
          </div>
        </div>
      </CardHeader>
    </Card>
  );
}

interface ApiCallDetailDialogProps {
  call: ApiCall;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function ApiCallDetailDialog({ call, open, onOpenChange }: ApiCallDetailDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Badge className={call.request.method === 'GET' ? 'bg-blue-100 text-blue-800' : 
                             call.request.method === 'POST' ? 'bg-green-100 text-green-800' :
                             call.request.method === 'PATCH' ? 'bg-orange-100 text-orange-800' :
                             call.request.method === 'DELETE' ? 'bg-red-100 text-red-800' :
                             'bg-gray-100 text-gray-800'}>
              {call.request.method}
            </Badge>
            <span className="font-mono text-sm">{call.request.url}</span>
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-hidden">
          <Tabs defaultValue="request" className="h-full flex flex-col">
            <TabsList>
              <TabsTrigger value="request">Request</TabsTrigger>
              <TabsTrigger value="response">Response</TabsTrigger>
              <TabsTrigger value="timing">Timing</TabsTrigger>
            </TabsList>
            
            <TabsContent value="request" className="flex-1 overflow-auto">
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Headers</h4>
                  <pre className="bg-gray-100 p-3 rounded text-sm overflow-auto">
                    {JSON.stringify(call.request.headers, null, 2)}
                  </pre>
                </div>
                {call.request.body && (
                  <div>
                    <h4 className="font-medium mb-2">Body</h4>
                    <pre className="bg-gray-100 p-3 rounded text-sm overflow-auto">
                      {JSON.stringify(call.request.body, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </TabsContent>
            
            <TabsContent value="response" className="flex-1 overflow-auto">
              {call.response ? (
                <div className="space-y-4">
                  <div className="flex items-center space-x-4">
                    <Badge className={getStatusColor(call.response.status)}>
                      {call.response.status} {call.response.statusText}
                    </Badge>
                    <span className="text-sm text-gray-500">
                      {formatDuration(call.response.duration)}
                    </span>
                  </div>
                  
                  <div>
                    <h4 className="font-medium mb-2">Headers</h4>
                    <pre className="bg-gray-100 p-3 rounded text-sm overflow-auto">
                      {JSON.stringify(call.response.headers, null, 2)}
                    </pre>
                  </div>
                  
                  {call.response.data && (
                    <div>
                      <h4 className="font-medium mb-2">Data</h4>
                      <pre className="bg-gray-100 p-3 rounded text-sm overflow-auto">
                        {JSON.stringify(call.response.data, null, 2)}
                      </pre>
                    </div>
                  )}
                  
                  {call.response.error && (
                    <div>
                      <h4 className="font-medium mb-2 text-red-600">Error</h4>
                      <pre className="bg-red-50 p-3 rounded text-sm overflow-auto text-red-800">
                        {call.response.error}
                      </pre>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <Clock className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                    <p className="text-gray-500">Waiting for response...</p>
                  </div>
                </div>
              )}
            </TabsContent>
            
            <TabsContent value="timing" className="flex-1 overflow-auto">
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium mb-2">Request Time</h4>
                    <p className="text-sm text-gray-600">
                      {new Date(call.request.timestamp).toLocaleString()}
                    </p>
                  </div>
                  {call.response && (
                    <div>
                      <h4 className="font-medium mb-2">Response Time</h4>
                      <p className="text-sm text-gray-600">
                        {new Date(call.response.timestamp).toLocaleString()}
                      </p>
                    </div>
                  )}
                </div>
                
                {call.duration && (
                  <div>
                    <h4 className="font-medium mb-2">Duration</h4>
                    <p className="text-lg font-mono">{formatDuration(call.duration)}</p>
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </DialogContent>
    </Dialog>
  );
}
