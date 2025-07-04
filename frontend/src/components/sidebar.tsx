"use client";

import React, { useState, useEffect } from 'react';
// import { motion, AnimatePresence } from 'framer-motion';
import {
  Settings,
  BarChart3,
  Activity,
  Home,
  FileText,
  Menu,
  X,
  ChevronLeft,
  ChevronRight,
  LogOut
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface NavigationItem {
  id: string;
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  href: string;
  badge?: string;
}

// Sidebar Component
const navigationItems: NavigationItem[] = [
  { id: "dashboard", name: "Dashboard", icon: Home, href: "/dashboard" },
  { id: "configuration", name: "Configuration", icon: Settings, href: "/configuration" },
  { id: "options-chain", name: "Options Chain", icon: BarChart3, href: "/options-chain" },
  { id: "orders-positions", name: "Orders & Positions", icon: FileText, href: "/orders-positions" },
  { id: "backtest", name: "Backtest", icon: Activity, href: "/backtest" },
];

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
}

export default function Sidebar({ activeTab, setActiveTab, isCollapsed, setIsCollapsed }: SidebarProps) {
  const [isOpen, setIsOpen] = useState(true);


  const toggleSidebar = () => setIsOpen(!isOpen);
  const toggleCollapse = () => setIsCollapsed(!isCollapsed);

  const handleItemClick = (itemId: string) => {
    setActiveTab(itemId);
    if (window.innerWidth < 768) {
      setIsOpen(false);
    }
  };

  return (
    <>
      <button
        onClick={toggleSidebar}
        className="fixed top-6 left-6 z-50 p-3 rounded-lg bg-background shadow-md border border-border md:hidden hover:bg-muted transition-all duration-200"
        aria-label="Toggle sidebar"
      >
        {isOpen ?
          <X className="h-5 w-5 text-foreground" /> :
          <Menu className="h-5 w-5 text-foreground" />
        }
      </button>

      {isOpen && (
        <div
          className="fixed inset-0 bg-black/40 backdrop-blur-sm z-30 md:hidden transition-opacity duration-300"
          onClick={toggleSidebar}
        />
      )}

      <div
        className={`
          fixed top-0 left-0 h-full bg-background border-r border-border z-40 transition-all duration-300 ease-in-out flex flex-col
          ${isOpen ? "translate-x-0" : "-translate-x-full"}
          ${isCollapsed ? "w-20" : "w-72"}
          md:translate-x-0
        `}
      >
        <div className="flex items-center justify-between p-5 border-b border-border bg-muted/30">
          {!isCollapsed && (
            <div className="flex items-center space-x-2.5">
              <div className="w-9 h-9 bg-primary rounded-lg flex items-center justify-center shadow-sm">
                <span className="text-primary-foreground font-bold text-base">OT</span>
              </div>
              <div className="flex flex-col">
                <span className="font-semibold text-foreground text-base">Options Trader</span>
                <span className="text-xs text-muted-foreground">Pro Platform</span>
              </div>
            </div>
          )}

          {isCollapsed && (
            <div className="w-9 h-9 bg-primary rounded-lg flex items-center justify-center mx-auto shadow-sm">
              <span className="text-primary-foreground font-bold text-base">OT</span>
            </div>
          )}

          <button
            onClick={toggleCollapse}
            className="hidden md:flex p-1.5 rounded-md hover:bg-muted transition-all duration-200"
            aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {isCollapsed ? (
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronLeft className="h-4 w-4 text-muted-foreground" />
            )}
          </button>
        </div>

        <nav className="flex-1 px-3 py-2 overflow-y-auto">
          <ul className="space-y-0.5">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;

              return (
                <li key={item.id}>
                  <button
                    onClick={() => handleItemClick(item.id)}
                    className={`
                      w-full flex items-center space-x-2.5 px-3 py-2.5 rounded-md text-left transition-all duration-200 group
                      ${isActive
                        ? "bg-primary/10 text-primary"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground"
                      }
                      ${isCollapsed ? "justify-center px-2" : ""}
                    `}
                    title={isCollapsed ? item.name : undefined}
                  >
                    <div className="flex items-center justify-center min-w-[24px]">
                      <Icon
                        className={`
                          h-4.5 w-4.5 flex-shrink-0
                          ${isActive
                            ? "text-primary"
                            : "text-muted-foreground group-hover:text-foreground"
                          }
                        `}
                      />
                    </div>
                    
                    {!isCollapsed && (
                      <div className="flex items-center justify-between w-full">
                        <span className={`text-sm ${isActive ? "font-medium" : "font-normal"}`}>{item.name}</span>
                        {item.badge && (
                          <Badge variant={isActive ? "default" : "secondary"} className="text-xs">
                            {item.badge}
                          </Badge>
                        )}
                      </div>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="mt-auto border-t border-border">
          <div className="p-3">
            <button
              className={`
                w-full flex items-center rounded-md text-left transition-all duration-200 group
                text-destructive hover:bg-destructive/10
                ${isCollapsed ? "justify-center p-2.5" : "space-x-2.5 px-3 py-2.5"}
              `}
              title={isCollapsed ? "Logout" : undefined}
            >
              <LogOut className="h-4.5 w-4.5 flex-shrink-0" />
              {!isCollapsed && <span className="text-sm">Logout</span>}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}