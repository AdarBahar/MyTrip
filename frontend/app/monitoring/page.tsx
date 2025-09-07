/**
 * Error Monitoring Page
 * 
 * Comprehensive error analytics and system monitoring dashboard
 */

'use client';

import React, { useState } from 'react';
import ErrorDashboard from '@/components/monitoring/error-dashboard';
import { Shield, Activity, AlertTriangle, TrendingUp } from 'lucide-react';

export default function MonitoringPage() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const tabs = [
    {
      id: 'dashboard',
      name: 'Error Dashboard',
      icon: Activity,
      description: 'Real-time error analytics and patterns'
    },
    {
      id: 'security',
      name: 'Security Monitor',
      icon: Shield,
      description: 'Authentication and permission errors'
    },
    {
      id: 'performance',
      name: 'Performance',
      icon: TrendingUp,
      description: 'API performance and reliability metrics'
    },
    {
      id: 'alerts',
      name: 'Alert Rules',
      icon: AlertTriangle,
      description: 'Configure monitoring alerts and thresholds'
    }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <ErrorDashboard />;
      case 'security':
        return <SecurityMonitor />;
      case 'performance':
        return <PerformanceMonitor />;
      case 'alerts':
        return <AlertConfiguration />;
      default:
        return <ErrorDashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">System Monitoring</h1>
          <p className="text-gray-600">
            Monitor API health, error patterns, and system performance in real-time
          </p>
        </div>

        {/* Navigation Tabs */}
        <div className="bg-white rounded-lg shadow-sm mb-8">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <Icon className="h-5 w-5 mr-2" />
                    {tab.name}
                  </button>
                );
              })}
            </nav>
          </div>
          
          {/* Tab Description */}
          <div className="px-6 py-3 bg-gray-50">
            <p className="text-sm text-gray-600">
              {tabs.find(tab => tab.id === activeTab)?.description}
            </p>
          </div>
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          {renderTabContent()}
        </div>
      </div>
    </div>
  );
}

// Placeholder components for other tabs
function SecurityMonitor() {
  return (
    <div className="text-center py-12">
      <Shield className="h-16 w-16 text-gray-300 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">Security Monitoring</h3>
      <p className="text-gray-600 mb-6">
        Track authentication failures, permission denials, and security-related errors
      </p>
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-md mx-auto">
        <p className="text-sm text-blue-800">
          🚧 Coming in Phase 3: Advanced security monitoring with threat detection and anomaly analysis
        </p>
      </div>
    </div>
  );
}

function PerformanceMonitor() {
  return (
    <div className="text-center py-12">
      <TrendingUp className="h-16 w-16 text-gray-300 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">Performance Monitoring</h3>
      <p className="text-gray-600 mb-6">
        Monitor API response times, throughput, and performance trends
      </p>
      <div className="bg-green-50 border border-green-200 rounded-lg p-4 max-w-md mx-auto">
        <p className="text-sm text-green-800">
          🚧 Coming in Phase 3: Real-time performance metrics with response time analysis and bottleneck detection
        </p>
      </div>
    </div>
  );
}

function AlertConfiguration() {
  return (
    <div className="text-center py-12">
      <AlertTriangle className="h-16 w-16 text-gray-300 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">Alert Configuration</h3>
      <p className="text-gray-600 mb-6">
        Set up automated alerts for error thresholds and system anomalies
      </p>
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 max-w-md mx-auto">
        <p className="text-sm text-yellow-800">
          🚧 Coming in Phase 3: Configurable alerts with email/Slack notifications and custom thresholds
        </p>
      </div>
    </div>
  );
}
