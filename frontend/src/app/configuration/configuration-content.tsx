"use client";

import React, { useState, useEffect } from 'react';
import {
  Settings,
  Key,
  Plug,
  Zap,
  RefreshCw,
  Save,
  AlertCircle,
  CheckCircle,
  XCircle,
  Eye,
  EyeOff,
  TestTube,
  Edit,
  Trash2
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { format } from 'date-fns'; // For date formatting

// Interfaces matching backend schemas
interface Broker {
  id: number;
  name: string;
  base_url: string;
  streaming_url: string;
  is_live_mode: boolean;
}

interface BrokerageConnection {
  id: number;
  user_id: number;
  broker_id: number;
  api_key?: string; // Optional, as it's encrypted in DB and might not be returned
  api_secret?: string; // Optional
  access_token?: string;
  refresh_token?: string;
  expires_at?: string; // ISO format string
  connection_status: string;
  last_connected?: string; // ISO format string
  broker: Broker; // Nested broker object
}

interface StrategyParameter {
  id: string;
  name: string;
  type: 'number' | 'string' | 'boolean' | 'select';
  value: any;
  options?: string[];
  description: string;
}

// Connection Status Constants (mirroring src/constants.py)
const CONNECTION_STATUS_CONNECTED = "connected";
const CONNECTION_STATUS_DISCONNECTED = "disconnected";
const CONNECTION_STATUS_ERROR = "error";
const CONNECTION_STATUS_PENDING = "pending";
const CONNECTION_STATUS_TESTING = "testing";
const CONNECTION_STATUS_INVALID_CREDENTIALS = "invalid_credentials";
const CONNECTION_STATUS_BROKER_UNAVAILABLE = "broker_unavailable";

export default function Configuration() {
  const [selectedBrokerId, setSelectedBrokerId] = useState<string>('');
  const [apiKey, setApiKey] = useState<string>('');
  const [apiSecret, setApiSecret] = useState<string>('');
  const [showApiKey, setShowApiKey] = useState<boolean>(false);
  const [showApiSecret, setShowApiSecret] = useState<boolean>(false);
  const [brokers, setBrokers] = useState<Broker[]>([]);
  const [existingConnections, setExistingConnections] = useState<BrokerageConnection[]>([]);
  const [connectionMessage, setConnectionMessage] = useState<string | null>(null);
  const [connectionMessageType, setConnectionMessageType] = useState<'success' | 'error' | 'info' | null>(null);

  const strategyParameters: StrategyParameter[] = [
    {
      id: '1',
      name: 'Risk Per Trade (%)',
      type: 'number',
      value: 1.5,
      description: 'Percentage of total portfolio value to risk per trade.'
    },
    {
      id: '2',
      name: 'Max Daily Loss ($)',
      type: 'number',
      value: 500,
      description: 'Maximum dollar amount allowed to lose in a single trading day.'
    },
    {
      id: '3',
      name: 'Auto Trade Enabled',
      type: 'boolean',
      value: true,
      description: 'Enable or disable automatic trade execution by bots.'
    },
    {
      id: '4',
      name: 'Default Strategy',
      type: 'select',
      value: 'Iron Condor',
      options: ['Iron Condor', 'Covered Call', 'Put Spread'],
      description: 'The default strategy to use for new bot instances.'
    }
  ];

  // Fetch brokers on component mount
  useEffect(() => {
    fetchBrokers();
    const accessToken = localStorage.getItem('access_token');
    if (accessToken) {
      fetchConnections();
    } else {
      console.warn("No access token found, skipping fetchConnections.");
      setConnectionMessage("Please log in to view and manage brokerage connections.");
      setConnectionMessageType("info");
    }
  }, []);

  const fetchBrokers = async () => {
    try {
      const response = await fetch('/api/v1/brokers', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data: Broker[] = await response.json();
      setBrokers(data);
      if (data.length > 0) {
        setSelectedBrokerId(String(data[0].id)); // Set default selected broker
      }
    } catch (error) {
      console.error("Failed to fetch brokers:", error);
      setConnectionMessage("Failed to load brokers. Please try again.");
      setConnectionMessageType("error");
    }
  };

  const fetchConnections = async () => {
    try {
      const response = await fetch('/api/v1/brokerage_connections', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data: BrokerageConnection[] = await response.json();
      setExistingConnections(data);
    } catch (error) {
      console.error("Failed to fetch existing connections:", error);
      setConnectionMessage("Failed to load existing connections. Please try again.");
      setConnectionMessageType("error");
    }
  };

  const handleTestConnection = async () => {
    if (!selectedBrokerId || (!apiKey && !apiSecret)) {
      setConnectionMessage("Please fill in all required fields (Broker and at least one of API Key/Secret).");
      setConnectionMessageType("error");
      return;
    }

    setConnectionMessage("Testing connection...");
    setConnectionMessageType("info");

    try {
      const response = await fetch('/api/v1/brokerage_connections/test', { // Assuming a new test endpoint
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          broker_id: parseInt(selectedBrokerId),
          api_key: apiKey || null,
          api_secret: apiSecret || null,
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `HTTP error! status: ${response.status}`);
      }

      setConnectionMessage("Connection test successful!");
      setConnectionMessageType("success");
    } catch (error: any) {
      console.error("Failed to test connection:", error);
      setConnectionMessage(`Connection test failed: ${error.message || "Unknown error"}`);
      setConnectionMessageType("error");
    }
  };

  const handleAddConnection = async () => {
    if (!selectedBrokerId || (!apiKey && !apiSecret)) {
      setConnectionMessage("Please fill in all required fields (Broker and at least one of API Key/Secret).");
      setConnectionMessageType("error");
      return;
    }

    setConnectionMessage("Attempting to add and test connection...");
    setConnectionMessageType("info");

    try {
      const response = await fetch('/api/v1/brokerage_connections', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          broker_id: parseInt(selectedBrokerId),
          api_key: apiKey || null,
          api_secret: apiSecret || null,
          // For now, access_token, refresh_token, token_expires_at are not directly from user input
          // They would typically come from an OAuth flow or be generated by the backend after initial key/secret validation
          access_token: null,
          refresh_token: null,
          token_expires_at: null
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `HTTP error! status: ${response.status}`);
      }

      setConnectionMessage("Connection added and tested successfully!");
      setConnectionMessageType("success");
      setApiKey('');
      setApiSecret('');
      fetchConnections(); // Refresh the list of connections
    } catch (error: any) {
      console.error("Failed to add connection:", error);
      setConnectionMessage(`Failed to add connection: ${error.message || "Unknown error"}`);
      setConnectionMessageType("error");
    }
  };

  const handleSaveParameters = () => {
    alert('Strategy parameters saved!');
  };

  const handleEditConnection = (connectionId: number) => {
    alert(`Edit connection with ID: ${connectionId}`);
    // TODO: Implement actual edit logic, e.g., open a dialog with pre-filled data
  };

  const handleDeleteConnection = async (connectionId: number) => {
    if (!confirm("Are you sure you want to delete this connection?")) {
      return;
    }

    setConnectionMessage("Deleting connection...");
    setConnectionMessageType("info");

    try {
      const response = await fetch(`/api/v1/brokerage_connections/${connectionId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      setConnectionMessage("Connection deleted successfully!");
      setConnectionMessageType("success");
      fetchConnections(); // Refresh the list of connections
    } catch (error: any) {
      console.error("Failed to delete connection:", error);
      setConnectionMessage(`Failed to delete connection: ${error.message || "Unknown error"}`);
      setConnectionMessageType("error");
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case CONNECTION_STATUS_CONNECTED:
        return 'bg-green-500';
      case CONNECTION_STATUS_DISCONNECTED:
        return 'bg-yellow-500';
      case CONNECTION_STATUS_ERROR:
      case CONNECTION_STATUS_INVALID_CREDENTIALS:
      case CONNECTION_STATUS_BROKER_UNAVAILABLE:
        return 'bg-red-500';
      case CONNECTION_STATUS_PENDING:
      case CONNECTION_STATUS_TESTING:
        return 'bg-blue-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-foreground">Configuration</h1>
        <Button onClick={fetchConnections}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh Connections
        </Button>
      </div>

      <Tabs defaultValue="brokers" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="brokers">Broker Connections</TabsTrigger>
          <TabsTrigger value="bots">Bot Configuration</TabsTrigger>
        </TabsList>

        <TabsContent value="brokers" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Broker Connections</CardTitle>
              <CardDescription>Configure your broker API connections</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                {connectionMessage && (
                  <div className={`p-3 rounded-md text-sm ${
                    connectionMessageType === 'success' ? 'bg-green-100 text-green-800' :
                    connectionMessageType === 'error' ? 'bg-red-100 text-red-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {connectionMessage}
                  </div>
                )}
                <div className="space-y-2">
                  <Label htmlFor="broker-select">Select Broker</Label>
                  <Select value={selectedBrokerId} onValueChange={setSelectedBrokerId}>
                    <SelectTrigger className="w-auto min-w-[150px]"> {/* Adjusted width */}
                      <SelectValue placeholder="Select a broker" />
                    </SelectTrigger>
                    <SelectContent>
                      {brokers.map((broker) => (
                        <SelectItem key={broker.id} value={String(broker.id)}>
                          {broker.name} ({broker.is_live_mode ? 'Live' : 'Paper'})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="api-key">API Key</Label>
                  <div className="relative">
                    <Input
                      id="api-key"
                      type={showApiKey ? "text" : "password"}
                      placeholder="Enter API Key"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 py-1"
                      onClick={() => setShowApiKey(!showApiKey)}
                    >
                      {showApiKey ? (
                        <EyeOff className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <Eye className="h-4 w-4 text-muted-foreground" />
                      )}
                    </Button>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="api-secret">API Secret</Label>
                  <div className="relative">
                    <Input
                      id="api-secret"
                      type={showApiSecret ? "text" : "password"}
                      placeholder="Enter API Secret"
                      value={apiSecret}
                      onChange={(e) => setApiSecret(e.target.value)}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 py-1"
                      onClick={() => setShowApiSecret(!showApiSecret)}
                    >
                      {showApiSecret ? (
                        <EyeOff className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <Eye className="h-4 w-4 text-muted-foreground" />
                      )}
                    </Button>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <Button onClick={handleAddConnection} className="flex-1">
                    <Plug className="w-4 h-4 mr-2" />
                    Add Connection
                  </Button>
                  <Button onClick={handleTestConnection} variant="outline" className="flex-1">
                    <TestTube className="w-4 h-4 mr-2" />
                    Test Connection
                  </Button>
                </div>
              </div>

              <div className="border-t border-border pt-6">
                <h3 className="text-lg font-semibold mb-4">Existing Connections</h3>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Broker</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Last Connected</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {existingConnections.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={4} className="text-center text-muted-foreground">
                          No connections found. Add a new one above!
                        </TableCell>
                      </TableRow>
                    ) : (
                      existingConnections.map((conn) => (
                        <TableRow key={conn.id}>
                          <TableCell className="font-medium">{conn.broker.name} ({conn.broker.is_live_mode ? 'Live' : 'Paper'})</TableCell>
                          <TableCell>
                            <div className="flex items-center space-x-2">
                              <div className={`w-2.5 h-2.5 rounded-full ${getStatusColor(conn.connection_status)}`} />
                              <span>{conn.connection_status}</span>
                            </div>
                          </TableCell>
                          <TableCell className="text-muted-foreground text-sm">
                            {conn.last_connected ? format(new Date(conn.last_connected), 'yyyy-MM-dd HH:mm') : 'N/A'}
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end space-x-2">
                              <Button variant="outline" size="sm" title="Test Connection">
                                <RefreshCw className="w-4 h-4" />
                              </Button>
                              <Button variant="outline" size="sm" title="Edit Connection" onClick={() => handleEditConnection(conn.id)}>
                                <Edit className="w-4 h-4" />
                              </Button>
                              <Button variant="destructive" size="sm" title="Delete Connection" onClick={() => handleDeleteConnection(conn.id)}>
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="bots" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Bot Strategy Parameters</CardTitle>
              <CardDescription>Configure global parameters for your trading bots</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {strategyParameters.map((param) => (
                <div key={param.id} className="space-y-2">
                  <Label htmlFor={`param-${param.id}`} className="flex items-center justify-between">
                    <span>{param.name}</span>
                    <span className="text-xs text-muted-foreground">{param.description}</span>
                  </Label>
                  {param.type === 'number' && (
                    <Input
                      id={`param-${param.id}`}
                      type="number"
                      value={param.value}
                      onChange={(e) => console.log(e.target.value)} // Placeholder for state management
                    />
                  )}
                  {param.type === 'string' && (
                    <Input
                      id={`param-${param.id}`}
                      type="text"
                      value={param.value}
                      onChange={(e) => console.log(e.target.value)} // Placeholder for state management
                    />
                  )}
                  {param.type === 'boolean' && (
                    <Switch
                      id={`param-${param.id}`}
                      checked={param.value}
                      onCheckedChange={(checked) => console.log(checked)} // Placeholder for state management
                    />
                  )}
                  {param.type === 'select' && param.options && (
                    <Select value={param.value} onValueChange={(value) => console.log(value)}> {/* Placeholder */}
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder={`Select ${param.name}`} />
                      </SelectTrigger>
                      <SelectContent>
                        {param.options.map(option => (
                          <SelectItem key={option} value={option}>{option}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                </div>
              ))}
              <Button onClick={handleSaveParameters} className="w-full">
                <Save className="w-4 h-4 mr-2" />
                Save Parameters
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}