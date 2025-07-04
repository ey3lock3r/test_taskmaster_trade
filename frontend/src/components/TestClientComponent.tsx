"use client";

import React, { useEffect } from 'react';

export default function TestClientComponent() {
  console.log("TestClientComponent rendered on client!");

  useEffect(() => {
    console.log("TestClientComponent useEffect fired!");
    return () => console.log("TestClientComponent unmounted!");
  }, []);

  return (
    <div style={{ 
      position: 'fixed', 
      top: '0', 
      left: '0', 
      width: '200px', 
      height: '100vh', 
      backgroundColor: 'blue', 
      color: 'white', 
      zIndex: '9999' 
    }}>
      Test Sidebar
    </div>
  );
}