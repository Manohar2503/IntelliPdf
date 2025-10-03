import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface SummaryDisplayProps {
  summary: {
    brief_summary: string;
    section_summaries?: { heading: string; summary: string }[];
  } | null;
  onClose: () => void; // Function to close the summary display
}

export function SummaryDisplay({ summary, onClose }: SummaryDisplayProps) {
  if (!summary) {
    return null; // Or a loading spinner, or a message
  }

  return (
    <Card className="animate-fade-in h-full">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg font-semibold">Document Summary</CardTitle>
        <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
          &times; {/* Close button */}
        </button>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h3 className="font-semibold mb-2">Brief Summary</h3>
          <p className="text-sm text-muted-foreground">{summary.brief_summary}</p>
        </div>
        {summary.section_summaries && summary.section_summaries.length > 0 && (
          <div>
            <h3 className="font-semibold mb-2">Section Summaries</h3>
            <div className="space-y-2">
              {summary.section_summaries.map((section, index) => (
                <div key={index} className="border rounded-lg p-3">
                  <h4 className="font-medium text-sm mb-1">{section.heading}</h4>
                  <p className="text-sm text-muted-foreground">{section.summary}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
