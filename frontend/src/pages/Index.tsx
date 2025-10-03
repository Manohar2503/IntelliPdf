import React, { useState } from 'react';
import { SetForAnalysis } from '@/components/SetForAnalysis';
import { DocumentLibrary } from '@/components/DocumentLibrary';
import { SummaryDisplay } from '@/components/SummaryDisplay';
import { LeftSidebar } from '@/components/LeftSidebar'; // Assuming LeftSidebar exists and is used for layout

const Index = () => {
  const [summaryData, setSummaryData] = useState<any>(null);

  const handleSummarizeSuccess = (summary: any) => {
    setSummaryData(summary);
  };

  const handleClearSummary = () => {
    setSummaryData(null);
  };

  return (
    <div className="flex min-h-screen bg-background">
      <LeftSidebar>
        <SetForAnalysis 
          onSummarizeSuccess={handleSummarizeSuccess} 
          onClearSummary={handleClearSummary} 
        />
      </LeftSidebar>
      <main className="flex-1 p-6 lg:p-8">
        {summaryData ? (
          <SummaryDisplay summary={summaryData} onClose={handleClearSummary} />
        ) : (
          <DocumentLibrary />
        )}
      </main>
    </div>
  );
};

export default Index;
