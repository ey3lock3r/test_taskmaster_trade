"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { TradeHistoryTable, TradeOrder } from "@/components/trade-history-table";
import { useAuth } from "@/context/AuthContext";
import axios from "axios";

export default function TradeHistoryPage() {
  const { accessToken } = useAuth();
  const [tradeOrders, setTradeOrders] = useState<TradeOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [symbolFilter, setSymbolFilter] = useState("");
  const [startDateFilter, setStartDateFilter] = useState("");
  const [endDateFilter, setEndDateFilter] = useState("");

  useEffect(() => {
    const fetchTradeOrders = async () => {
      if (!accessToken) {
        setError("Authentication required.");
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        if (symbolFilter) params.append("symbol", symbolFilter);
        if (startDateFilter) params.append("start_date", startDateFilter);
        if (endDateFilter) params.append("end_date", endDateFilter);

        const response = await axios.get(
          `http://localhost:8000/trading/orders?${params.toString()}`,
          {
            headers: {
              Authorization: `Bearer ${accessToken}`,
            },
          }
        );
        setTradeOrders(response.data);
      } catch (err) {
        console.error("Failed to fetch trade orders:", err);
        setError("Failed to load trade history. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    fetchTradeOrders();
  }, [accessToken, symbolFilter, startDateFilter, endDateFilter]);

  const handleApplyFilters = () => {
    // Effect hook will re-run when filter states change
  };

  return (
    <div className="flex min-h-screen w-full flex-col bg-muted/40">
      <div className="flex flex-col sm:gap-4 sm:py-4 sm:pl-14">
        <main className="grid flex-1 items-start gap-4 p-4 sm:px-6 sm:py-0 md:gap-8 lg:grid-cols-3 xl:grid-cols-3">
          <div className="grid auto-rows-max items-start gap-4 md:gap-8 lg:col-span-2">
            <Card className="sm:col-span-2">
              <CardHeader className="pb-3">
                <CardTitle>Trade History</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-muted-foreground">
                  <div className="mb-4 flex gap-2">
                    <div>
                      <Label htmlFor="search">Search Symbol</Label>
                      <Input
                        id="search"
                        type="text"
                        placeholder="AAPL"
                        value={symbolFilter}
                        onChange={(e) => setSymbolFilter(e.target.value)}
                      />
                    </div>
                    <div>
                      <Label htmlFor="startDate">Start Date</Label>
                      <Input
                        id="startDate"
                        type="date"
                        value={startDateFilter}
                        onChange={(e) => setStartDateFilter(e.target.value)}
                      />
                    </div>
                    <div>
                      <Label htmlFor="endDate">End Date</Label>
                      <Input
                        id="endDate"
                        type="date"
                        value={endDateFilter}
                        onChange={(e) => setEndDateFilter(e.target.value)}
                      />
                    </div>
                    <Button className="self-end" onClick={handleApplyFilters}>
                      Apply Filters
                    </Button>
                  </div>
                  {loading && <p>Loading trade history...</p>}
                  {error && <p className="text-red-500">{error}</p>}
                  {!loading && !error && (
                    <TradeHistoryTable data={tradeOrders} />
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
}