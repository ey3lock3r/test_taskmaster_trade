"use client";

import React from 'react';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  Target,
  RefreshCw,
  Play,
  Pause
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

// Interfaces
interface PortfolioMetrics {
  totalValue: number;
  dailyPnL: number;
  dailyPnLPercent: number;
  totalPnL: number;
  totalPnLPercent: number;
  buyingPower: number;
}

interface BotMetrics {
  id: string;
  name: string;
  status: 'active' | 'paused' | 'stopped';
  strategy: string;
  dailyPnL: number;
  totalPnL: number;
  winRate: number;
  trades: number;
}

export default function Dashboard() {
  const portfolioMetrics: PortfolioMetrics = {
    totalValue: 125430.50,
    dailyPnL: 2340.25,
    dailyPnLPercent: 1.9,
    totalPnL: 15430.50,
    totalPnLPercent: 14.0,
    buyingPower: 45230.75
  };

  const botMetrics: BotMetrics[] = [
    {
      id: '1',
      name: 'Iron Condor Bot',
      status: 'active',
      strategy: 'Iron Condor',
      dailyPnL: 450.25,
      totalPnL: 3240.50,
      winRate: 78.5,
      trades: 24
    },
    {
      id: '2',
      name: 'Covered Call Bot',
      status: 'active',
      strategy: 'Covered Call',
      dailyPnL: 320.75,
      totalPnL: 2180.25,
      winRate: 82.3,
      trades: 18
    },
    {
      id: '3',
      name: 'Put Spread Bot',
      status: 'paused',
      strategy: 'Put Spread',
      dailyPnL: -125.50,
      totalPnL: 890.75,
      winRate: 65.2,
      trades: 12
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
        <Button>
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh Data
        </Button>
      </div>

      {/* Portfolio Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Portfolio</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${portfolioMetrics.totalValue.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              +{portfolioMetrics.totalPnLPercent}% from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Daily P&L</CardTitle>
            {portfolioMetrics.dailyPnL >= 0 ? (
              <TrendingUp className="h-4 w-4 text-green-600" />
            ) : (
              <TrendingDown className="h-4 w-4 text-red-600" />
            )}
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${portfolioMetrics.dailyPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ${portfolioMetrics.dailyPnL.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              {portfolioMetrics.dailyPnLPercent >= 0 ? '+' : ''}{portfolioMetrics.dailyPnLPercent}% today
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total P&L</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${portfolioMetrics.totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ${portfolioMetrics.totalPnL.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              {portfolioMetrics.totalPnLPercent >= 0 ? '+' : ''}{portfolioMetrics.totalPnLPercent}% all time
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Buying Power</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${portfolioMetrics.buyingPower.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              Available for trading
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Bot Performance */}
      <Card>
        <CardHeader>
          <CardTitle>Bot Performance</CardTitle>
          <CardDescription>Real-time performance metrics for your trading bots</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {botMetrics.map((bot) => (
              <div key={bot.id} className="flex items-center justify-between p-4 border border-border rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${
                      bot.status === 'active' ? 'bg-green-500' :
                      bot.status === 'paused' ? 'bg-yellow-500' : 'bg-red-500'
                    }`} />
                    <span className="font-medium">{bot.name}</span>
                  </div>
                  <Badge variant="outline">{bot.strategy}</Badge>
                </div>
                <div className="flex items-center space-x-6 text-sm">
                  <div className="text-center">
                    <div className="text-muted-foreground">Daily P&L</div>
                    <div className={`font-medium ${bot.dailyPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      ${bot.dailyPnL.toLocaleString()}
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-muted-foreground">Total P&L</div>
                    <div className={`font-medium ${bot.totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      ${bot.totalPnL.toLocaleString()}
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-muted-foreground">Win Rate</div>
                    <div className="font-medium">{bot.winRate}%</div>
                  </div>
                  <div className="text-center">
                    <div className="text-muted-foreground">Trades</div>
                    <div className="font-medium">{bot.trades}</div>
                  </div>
                  <Button size="sm" variant={bot.status === 'active' ? 'outline' : 'default'}>
                    {bot.status === 'active' ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}