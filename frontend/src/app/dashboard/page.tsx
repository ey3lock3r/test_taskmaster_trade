"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";

export default function DashboardPage() {
  const [botStatus, setBotStatus] = useState("Loading...");
  const [parameters, setParameters] = useState("Loading...");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState(null);

  const { token } = useAuth();

  const fetchBotData = async () => {
    setLoading(true);
    setError(null);
    try {
      const headers = {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      };

      const statusResponse = await fetch("http://localhost:8000/api/v1/bot/status", { headers });
      if (!statusResponse.ok) {
        throw new Error(`HTTP error! status: ${statusResponse.status}`);
      }
      const statusData = await statusResponse.json();
      setBotStatus(statusData.status);

      const paramsResponse = await fetch("http://localhost:8000/api/v1/bot/parameters?bot_id=1", { headers }); // TODO: Replace hardcoded bot_id with dynamic value
      if (!paramsResponse.ok) {
        throw new Error(`HTTP error! status: ${paramsResponse.status}`);
      }
      const paramsData = await paramsResponse.json();
      setParameters(JSON.stringify(paramsData, null, 2));
    } catch (err: any) {
      console.error("Error fetching data:", err);
      setError(err.message);
      setBotStatus("Error");
      setParameters("Error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBotData();
  }, []);

  const handleStartBot = async () => {
    setActionLoading(true);
    setActionError(null);
    try {
      const headers = {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      };
      const response = await fetch("http://localhost:8000/api/v1/bot/start", {
        method: "POST",
        headers,
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to start bot");
      }
      await fetchBotData(); // Refresh status and parameters
    } catch (err: any) {
      console.error("Action error (start bot):", err);
      setActionError(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleStopBot = async () => {
    setActionLoading(true);
    setActionError(null);
    try {
      const headers = {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      };
      const response = await fetch("http://localhost:8000/api/v1/bot/stop", {
        method: "POST",
        headers,
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to stop bot");
      }
      await fetchBotData(); // Refresh status and parameters
    } catch (err: any) {
      console.error("Action error (stop bot):", err);
      setActionError(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-center">Bot Dashboard</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && <p className="text-red-500 text-center">Error fetching data: {error}</p>}
          {actionError && <p className="text-red-500 text-center">Action error: {actionError}</p>}
          <div className="flex justify-between items-center">
            <p className="text-lg font-medium">Bot Status:</p>
            <span className="text-lg text-gray-500">{loading ? "Loading..." : botStatus}</span>
          </div>
          <div className="flex justify-between items-center">
            <p className="text-lg font-medium">Parameters:</p>
            <pre className="text-sm text-gray-500 overflow-auto">{loading ? "Loading..." : parameters}</pre>
          </div>
          <div className="flex justify-center space-x-4">
            <Button onClick={handleStartBot} disabled={actionLoading}>
              {actionLoading ? "Starting..." : "Start Bot"}
            </Button>
            <Button variant="destructive" onClick={handleStopBot} disabled={actionLoading}>
              {actionLoading ? "Stopping..." : "Stop Bot"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}