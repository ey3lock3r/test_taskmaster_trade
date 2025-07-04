"use client";

import React, { useState } from 'react';
import {
  Plus,
  Search,
  Filter,
  Download,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Eye,
  Edit,
  Trash2
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';

// Interfaces
interface Position {
  id: string;
  symbol: string;
  type: 'stock' | 'option';
  quantity: number;
  avgPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
  broker: string;
  bot?: string;
}

interface Order {
  id: string;
  symbol: string;
  type: 'buy' | 'sell';
  quantity: number;
  price: number;
  status: 'pending' | 'filled' | 'cancelled';
  timestamp: string;
  broker: string;
  bot?: string;
}

export default function OrdersPositions() {
  const [positionFilter, setPositionFilter] = useState('all'); // 'all', 'stock', 'option'
  const [orderFilter, setOrderFilter] = useState('all'); // 'all', 'pending', 'filled', 'cancelled'

  const positions: Position[] = [
    {
      id: 'pos1', symbol: 'AAPL', type: 'stock', quantity: 100, avgPrice: 150.00,
      currentPrice: 155.50, pnl: 550.00, pnlPercent: 3.67, broker: 'TD Ameritrade'
    },
    {
      id: 'pos2', symbol: 'MSFT', type: 'stock', quantity: 50, avgPrice: 300.00,
      currentPrice: 295.00, pnl: -250.00, pnlPercent: -1.67, broker: 'Alpaca', bot: 'Covered Call Bot'
    },
    {
      id: 'pos3', symbol: 'GOOGL', type: 'option', quantity: 5, avgPrice: 10.00,
      currentPrice: 12.50, pnl: 125.00, pnlPercent: 25.00, broker: 'Interactive Brokers'
    }
  ];

  const orders: Order[] = [
    {
      id: 'ord1', symbol: 'TSLA', type: 'buy', quantity: 10, price: 200.00,
      status: 'filled', timestamp: '2024-06-14 09:30 AM', broker: 'TD Ameritrade'
    },
    {
      id: 'ord2', symbol: 'AMZN', type: 'sell', quantity: 5, price: 180.00,
      status: 'pending', timestamp: '2024-06-14 10:00 AM', broker: 'Alpaca', bot: 'Iron Condor Bot'
    },
    {
      id: 'ord3', symbol: 'NVDA', type: 'buy', quantity: 20, price: 100.00,
      status: 'cancelled', timestamp: '2024-06-13 03:00 PM', broker: 'Interactive Brokers'
    }
  ];

  const filteredPositions = positions.filter(pos => {
    if (positionFilter === 'all') return true;
    return pos.type === positionFilter;
  });

  const filteredOrders = orders.filter(order => {
    if (orderFilter === 'all') return true;
    return order.status === orderFilter;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-foreground">Orders & Positions</h1>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          New Order
        </Button>
      </div>

      <Tabs defaultValue="positions" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="positions">Current Positions</TabsTrigger>
          <TabsTrigger value="orders">Trade Orders</TabsTrigger>
        </TabsList>

        <TabsContent value="positions" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Current Positions</CardTitle>
              <CardDescription>Your open stock and options positions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-2">
                <Label htmlFor="position-filter">Filter by Type:</Label>
                <Select value={positionFilter} onValueChange={setPositionFilter}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder="All Types" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    <SelectItem value="stock">Stock</SelectItem>
                    <SelectItem value="option">Option</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Quantity</TableHead>
                    <TableHead>Avg. Price</TableHead>
                    <TableHead>Current Price</TableHead>
                    <TableHead>P&L</TableHead>
                    <TableHead>P&L %</TableHead>
                    <TableHead>Broker</TableHead>
                    <TableHead>Bot</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredPositions.map((pos) => (
                    <TableRow key={pos.id}>
                      <TableCell className="font-medium">{pos.symbol}</TableCell>
                      <TableCell>{pos.type}</TableCell>
                      <TableCell>{pos.quantity}</TableCell>
                      <TableCell>${pos.avgPrice.toFixed(2)}</TableCell>
                      <TableCell>${pos.currentPrice.toFixed(2)}</TableCell>
                      <TableCell className={`${pos.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        ${pos.pnl.toFixed(2)}
                      </TableCell>
                      <TableCell className={`${pos.pnlPercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {pos.pnlPercent.toFixed(2)}%
                      </TableCell>
                      <TableCell>{pos.broker}</TableCell>
                      <TableCell>{pos.bot || 'N/A'}</TableCell>
                      <TableCell className="text-right">
                        <Button variant="outline" size="sm" className="mr-2">
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button variant="destructive" size="sm">
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="orders" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Trade Orders</CardTitle>
              <CardDescription>Your historical and pending trade orders</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-2">
                <Label htmlFor="order-filter">Filter by Status:</Label>
                <Select value={orderFilter} onValueChange={setOrderFilter}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder="All Statuses" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Statuses</SelectItem>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="filled">Filled</SelectItem>
                    <SelectItem value="cancelled">Cancelled</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Quantity</TableHead>
                    <TableHead>Price</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Broker</TableHead>
                    <TableHead>Bot</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredOrders.map((order) => (
                    <TableRow key={order.id}>
                      <TableCell className="font-medium">{order.symbol}</TableCell>
                      <TableCell>{order.type}</TableCell>
                      <TableCell>{order.quantity}</TableCell>
                      <TableCell>${order.price.toFixed(2)}</TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <div className={`w-2.5 h-2.5 rounded-full ${
                            order.status === 'filled' ? 'bg-green-500' :
                            order.status === 'pending' ? 'bg-yellow-500' : 'bg-blue-500'
                          }`} />
                          <span>{order.status}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-muted-foreground text-sm">{order.timestamp}</TableCell>
                      <TableCell>{order.broker}</TableCell>
                      <TableCell>{order.bot || 'N/A'}</TableCell>
                      <TableCell className="text-right">
                        {order.status === 'pending' && (
                          <>
                            <Button variant="outline" size="sm" className="mr-2">
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button variant="destructive" size="sm">
                              <XCircle className="w-4 h-4" />
                            </Button>
                          </>
                        )}
                        {order.status === 'filled' && (
                          <Button variant="outline" size="sm">
                            <Eye className="w-4 h-4" />
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}