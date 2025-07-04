"use client";

import React, { useState } from 'react';
import {
  Play,
  Pause,
  RefreshCw,
  BarChart3,
  Download,
  Filter,
  Clock,
  TrendingUp,
  TrendingDown
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

// Interfaces
interface BacktestResult {
  id: string;
  botName: string;
  strategy: string;
  period: string;
  totalReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  totalTrades: number;
  avgTrade: number;
}

export default function Backtest() {
  const [strategy, setStrategy] = useState('Iron Condor');
  const [startDate, setStartDate] = useState('2023-01-01');
  const [endDate, setEndDate] = useState('2023-12-31');
  const [progress, setProgress] = useState(0);
  const [isRunning, setIsRunning] = useState(false);

  const backtestResults: BacktestResult[] = [
    {
      id: 'bt1', botName: 'Iron Condor Bot', strategy: 'Iron Condor', period: '2023-01-01 to 2023-12-31',
      totalReturn: 18.5, sharpeRatio: 1.2, maxDrawdown: -8.2, winRate: 75.0, totalTrades: 120, avgTrade: 15.20
    },
    {
      id: 'bt2', botName: 'Covered Call Bot', strategy: 'Covered Call', period: '2023-01-01 to 2023-12-31',
      totalReturn: 12.3, sharpeRatio: 0.9, maxDrawdown: -5.5, winRate: 88.0, totalTrades: 90, avgTrade: 10.50
    },
    {
      id: 'bt3', botName: 'Put Spread Bot', strategy: 'Put Spread', period: '2023-01-01 to 2023-12-31',
      totalReturn: 22.1, sharpeRatio: 1.5, maxDrawdown: -10.1, winRate: 70.0, totalTrades: 150, avgTrade: 18.70
    }
  ];

  const handleRunBacktest = () => {
    setIsRunning(true);
    setProgress(0);
    let currentProgress = 0;
    const interval = setInterval(() => {
      currentProgress += 10;
      setProgress(currentProgress);
      if (currentProgress >= 100) {
        clearInterval(interval);
        setIsRunning(false);
        alert('Backtest completed!');
      }
    }, 200);
  };

  const handleStopBacktest = () => {
    setIsRunning(false);
    setProgress(0);
    alert('Backtest stopped.');
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-foreground">Backtest Strategies</h1>
        <Button variant="outline">
          <Download className="w-4 h-4 mr-2" />
          Export Results
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Run New Backtest</CardTitle>
          <CardDescription>Test your trading strategies against historical data</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="strategy-select">Strategy</Label>
              <Select value={strategy} onValueChange={setStrategy}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select a strategy" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Iron Condor">Iron Condor</SelectItem>
                  <SelectItem value="Covered Call">Covered Call</SelectItem>
                  <SelectItem value="Put Spread">Put Spread</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="start-date">Start Date</Label>
              <Input
                id="start-date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="end-date">End Date</Label>
              <Input
                id="end-date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label>Backtest Progress</Label>
            <Progress value={progress} className="w-full" />
            <div className="text-sm text-muted-foreground text-right">{progress}% Complete</div>
          </div>
          <div className="flex space-x-2">
            <Button onClick={handleRunBacktest} disabled={isRunning} className="flex-1">
              <Play className="w-4 h-4 mr-2" />
              Run Backtest
            </Button>
            <Button onClick={handleStopBacktest} disabled={!isRunning} variant="outline" className="flex-1">
              <Pause className="w-4 h-4 mr-2" />
              Stop Backtest
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Backtest History</CardTitle>
          <CardDescription>Review past backtest results</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Bot Name</TableHead>
                <TableHead>Strategy</TableHead>
                <TableHead>Period</TableHead>
                <TableHead>Total Return</TableHead>
                <TableHead>Sharpe Ratio</TableHead>
                <TableHead>Max Drawdown</TableHead>
                <TableHead>Win Rate</TableHead>
                <TableHead>Total Trades</TableHead>
                <TableHead>Avg. Trade P&L</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {backtestResults.map((result) => (
                <TableRow key={result.id}>
                  <TableCell className="font-medium">{result.botName}</TableCell>
                  <TableCell>{result.strategy}</TableCell>
                  <TableCell>{result.period}</TableCell>
                  <TableCell className={`${result.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {result.totalReturn.toFixed(2)}%
                  </TableCell>
                  <TableCell>{result.sharpeRatio.toFixed(2)}</TableCell>
                  <TableCell className={`${result.maxDrawdown >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {result.maxDrawdown.toFixed(2)}%
                  </TableCell>
                  <TableCell>{result.winRate.toFixed(1)}%</TableCell>
                  <TableCell>{result.totalTrades}</TableCell>
                  <TableCell className={`${result.avgTrade >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    ${result.avgTrade.toFixed(2)}
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