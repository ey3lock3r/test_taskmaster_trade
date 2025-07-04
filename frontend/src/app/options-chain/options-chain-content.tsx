"use client";

import React, { useState } from 'react';
import {
  Search,
  Calendar,
  Filter,
  Download,
  ChevronDown,
  ChevronUp,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

// Interfaces
interface OptionContract {
  symbol: string;
  strike: number;
  expiry: string;
  type: 'call' | 'put';
  bid: number;
  ask: number;
  volume: number;
  openInterest: number;
  iv: number;
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
}

export default function OptionsChain() {
  const [symbol, setSymbol] = useState('AAPL');
  const [expiry, setExpiry] = useState('2024-12-20');
  const [selectedType, setSelectedType] = useState('all'); // 'call', 'put', 'all'

  const optionContracts: OptionContract[] = [
    {
      symbol: 'AAPL', strike: 150, expiry: '2024-12-20', type: 'call',
      bid: 10.50, ask: 10.70, volume: 1200, openInterest: 5000,
      iv: 0.25, delta: 0.65, gamma: 0.03, theta: -0.05, vega: 0.15
    },
    {
      symbol: 'AAPL', strike: 155, expiry: '2024-12-20', type: 'call',
      bid: 7.80, ask: 8.00, volume: 900, openInterest: 4200,
      iv: 0.24, delta: 0.55, gamma: 0.04, theta: -0.06, vega: 0.14
    },
    {
      symbol: 'AAPL', strike: 160, expiry: '2024-12-20', type: 'call',
      bid: 5.20, ask: 5.40, volume: 1500, openInterest: 6100,
      iv: 0.23, delta: 0.45, gamma: 0.04, theta: -0.07, vega: 0.13
    },
    {
      symbol: 'AAPL', strike: 145, expiry: '2024-12-20', type: 'put',
      bid: 4.10, ask: 4.30, volume: 800, openInterest: 3500,
      iv: 0.28, delta: -0.35, gamma: 0.03, theta: -0.04, vega: 0.16
    },
    {
      symbol: 'AAPL', strike: 140, expiry: '2024-12-20', type: 'put',
      bid: 2.50, ask: 2.70, volume: 600, openInterest: 2800,
      iv: 0.29, delta: -0.25, gamma: 0.02, theta: -0.03, vega: 0.15
    }
  ];

  const filteredContracts = optionContracts.filter(contract => {
    if (selectedType === 'all') return true;
    return contract.type === selectedType;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-foreground">Options Chain</h1>
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <Filter className="w-4 h-4 mr-2" />
            Filters
          </Button>
          <Button>
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Search Options</CardTitle>
          <CardDescription>Find options contracts by symbol and expiry</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="symbol-search">Symbol</Label>
              <Input
                id="symbol-search"
                placeholder="e.g., SPY, QQQ"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="expiry-select">Expiry Date</Label>
              <Select value={expiry} onValueChange={setExpiry}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select expiry" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="2024-12-20">2024-12-20</SelectItem>
                  <SelectItem value="2025-01-17">2025-01-17</SelectItem>
                  <SelectItem value="2025-02-21">2025-02-21</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="type-select">Option Type</Label>
              <Select value={selectedType} onValueChange={setSelectedType}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="All" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="call">Call</SelectItem>
                  <SelectItem value="put">Put</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <Button className="w-full">
            <Search className="w-4 h-4 mr-2" />
            Search Options
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Options Chain for {symbol} ({expiry})</CardTitle>
          <CardDescription>Detailed options contracts data</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Strike</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Bid</TableHead>
                <TableHead>Ask</TableHead>
                <TableHead>Volume</TableHead>
                <TableHead>Open Interest</TableHead>
                <TableHead>IV</TableHead>
                <TableHead>Delta</TableHead>
                <TableHead>Gamma</TableHead>
                <TableHead>Theta</TableHead>
                <TableHead>Vega</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredContracts.map((contract, index) => (
                <TableRow key={index}>
                  <TableCell className="font-medium">{contract.strike}</TableCell>
                  <TableCell>
                    <span className={`font-medium ${contract.type === 'call' ? 'text-green-600' : 'text-red-600'}`}>
                      {contract.type === 'call' ? 'Call' : 'Put'}
                    </span>
                  </TableCell>
                  <TableCell>${contract.bid.toFixed(2)}</TableCell>
                  <TableCell>${contract.ask.toFixed(2)}</TableCell>
                  <TableCell>{contract.volume.toLocaleString()}</TableCell>
                  <TableCell>{contract.openInterest.toLocaleString()}</TableCell>
                  <TableCell>{(contract.iv * 100).toFixed(2)}%</TableCell>
                  <TableCell className={`${contract.delta >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {contract.delta.toFixed(2)}
                  </TableCell>
                  <TableCell>{contract.gamma.toFixed(3)}</TableCell>
                  <TableCell className={`${contract.theta >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {contract.theta.toFixed(3)}
                  </TableCell>
                  <TableCell>{contract.vega.toFixed(3)}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="outline" size="sm">Trade</Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}