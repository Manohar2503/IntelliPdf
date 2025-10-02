// src/context/InsightsContext.tsx
import React, { createContext, useContext, useState, ReactNode } from "react";

interface InsightsData {
  key_insights?: string[];
  did_you_know?: string[];
  contradictions?: string[];
  inspirations?: string[];
}

interface InsightsContextType {
  insights: InsightsData | null;
  setInsights: (data: InsightsData) => void;
}

const InsightsContext = createContext<InsightsContextType | undefined>(undefined);

export const InsightsProvider = ({ children }: { children: ReactNode }) => {
  const [insights, setInsights] = useState<InsightsData | null>(null);

  return (
    <InsightsContext.Provider value={{ insights, setInsights }}>
      {children}
    </InsightsContext.Provider>
  );
};

export const useInsights = () => {
  const context = useContext(InsightsContext);
  if (!context) {
    throw new Error("useInsights must be used within an InsightsProvider");
  }
  return context;
};
