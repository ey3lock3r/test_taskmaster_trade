"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import OptionsTradingApp from "./options-trading-app";

export default function Home() {
  const { token } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!token) {
      router.push("/login");
    }
  }, [token, router]);

  if (!token) {
    return null; // Or a loading spinner
  }

  return <OptionsTradingApp />;
}