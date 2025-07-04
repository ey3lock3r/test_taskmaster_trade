"use client";

import React, { useState } from 'react';
import dynamic from 'next/dynamic';

const Sidebar = dynamic(() => import("@/components/sidebar"), { ssr: false });
import Dashboard from "./dashboard/dashboard-content";
import Configuration from "./configuration/configuration-content";
import OptionsChain from "./options-chain/options-chain-content";
import OrdersPositions from "./orders-positions/orders-positions-content";
import Backtest from "./backtest/backtest-content";

export default function OptionsTradingApp() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'configuration':
        return <Configuration />;
      case 'options-chain':
        return <OptionsChain />;
      case 'orders-positions':
        return <OrdersPositions />;
      case 'backtest':
        return <Backtest />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isCollapsed={isSidebarCollapsed}
        setIsCollapsed={setIsSidebarCollapsed}
      />
      
      <div
        className="flex flex-col flex-1"
        style={{
          marginLeft: isSidebarCollapsed ? '80px' : '288px',
          transition: 'margin-left 0.3s ease-in-out',
        }}
      >
        <main className="flex-1 overflow-auto p-8 pt-20 md:pt-8">
          {renderContent()}
        </main>
      </div>
    </div>
  );
}