import React, { useState, useEffect } from 'react';
import { CurrentPositionsTable, Position } from '@/components/current-positions-table';

const CurrentPositionsPage = () => {
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPositions = async () => {
      try {
        const response = await fetch('/api/trading/positions'); // Assuming API proxy or direct access
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: Position[] = await response.json();
        setPositions(data);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    fetchPositions();
  }, []);

  if (loading) {
    return (
      <div className="container mx-auto py-10">
        <h1 className="text-3xl font-bold mb-6">Current Positions</h1>
        <div className="border rounded-md p-4">
          <p className="text-gray-500">Loading current positions...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto py-10">
        <h1 className="text-3xl font-bold mb-6">Current Positions</h1>
        <div className="border rounded-md p-4 text-red-500">
          <p>Error: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-10">
      <h1 className="text-3xl font-bold mb-6">Current Positions</h1>
      <div className="border rounded-md p-4">
        {positions.length === 0 ? (
          <p className="text-gray-500">No current positions found.</p>
        ) : (
          <CurrentPositionsTable data={positions} />
        )}
      </div>
    </div>
  );
};

export default CurrentPositionsPage;