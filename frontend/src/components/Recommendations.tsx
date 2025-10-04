import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useDocumentStore } from '@/store/useDocumentStore';
import { AdobeViewerRef } from './AdobeViewer';

interface RecommendationsProps {
  viewerRef: React.RefObject<AdobeViewerRef>;
}

interface Match {
  section: string;
  page_number: number;
  snippets: string[];
  top_snippet: string;
  score: number;
}

interface Recommendation {
  doc_id: string;
  title: string;
  pdf_url: string;
  source: string;
  matches: Match[];
}

export function Recommendations({ viewerRef }: RecommendationsProps) {
  const { selection, activeDocId, documents } = useDocumentStore();
  const activeDoc = documents.find(doc => doc.id === activeDocId);

  const context = selection || activeDoc;

  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!context) return;

    const fetchRecommendations = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch("http://localhost:8080/search", {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            selected_text: selection?.text || activeDoc?.name || '', // Dynamically set selected_text
            top_k: 3,
            min_score: 0.3
          }),
        });

        if (!response.ok) {
          throw new Error(`API error: ${response.statusText}`);
        }

        const data: Recommendation[] = await response.json();
        setRecommendations(data);
      } catch (err: any) {
        setError(err.message || 'Something went wrong');
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [context]);

const [loadingPage, setLoadingPage] = useState<number | null>(null);

const handleJumpToPage = async (rec: Recommendation, page: number) => {
  if (!viewerRef.current || !rec.pdf_url) return;

  try {
    setLoadingPage(page);
    let attempts = 0;
    const maxAttempts = 3;

    while (attempts < maxAttempts) {
      try {
        await viewerRef.current.goToPage(page);
        setLoadingPage(null);
        return;
      } catch (error) {
        attempts++;
        if (attempts === maxAttempts) throw error;
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }
  } catch (err) {
    console.error("Error jumping to page:", err);
    setLoadingPage(null);
  }
};





  if (!context) {
    return (
      <div className="w-96 bg-card border-l border-border p-4">
        <h3 className="font-semibold text-foreground mb-4">Recommendations</h3>
        <div className="text-center text-muted-foreground py-8">
          <p className="text-sm">No document available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-96 bg-card border-l border-border flex flex-col h-[calc(100vh-64px)]">
      <div className="p-4 border-b border-border">
        <h3 className="font-semibold text-foreground mb-2">Recommendations</h3>
        {selection ? (
          <p className="text-xs text-muted-foreground">
            Based on selected text: "{selection.text.substring(0, 50)}..."
          </p>
        ) : (
          <p className="text-xs text-muted-foreground">
            Based on overall document: "{activeDoc?.name}"
          </p>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="animate-pulse">
                <CardContent className="p-4">
                  <div className="h-4 bg-muted rounded mb-2"></div>
                  <div className="h-3 bg-muted rounded w-3/4 mb-3"></div>
                  <div className="h-8 bg-muted rounded"></div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : error ? (
          <div className="text-center text-red-500 py-8">{error}</div>
        ) : recommendations.length === 0 ? (
          <div className="text-center text-muted-foreground py-8">
            <p className="text-sm">No recommendations available for this selection</p>
          </div>
        ) : (
          recommendations.map((rec, index) => (
            <Card key={`${rec.doc_id}-${index}`} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-sm font-medium leading-tight">
                    {rec.title}
                  </CardTitle>
                  <Badge 
                    variant="secondary" 
                    className="text-xs bg-primary/10 text-primary flex-shrink-0"
                  >
                    {rec.matches.length} matches
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="pt-0 space-y-2">
                {rec.matches.map((match, idx) => (
                  <div key={idx} className="p-2 border rounded bg-muted/5">
                    <p className="text-xs font-medium">Page {match.page_number}</p>
                    <p className="text-sm">{match.top_snippet}</p>
                   <Button
  size="sm"
  variant="outline"
  onClick={() => handleJumpToPage(rec, match.page_number)}
  className="mt-1 w-full text-xs relative"
  disabled={loadingPage !== null}
>
  {loadingPage === match.page_number ? (
    <>
      <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin mr-2" />
      Loading...
    </>
  ) : (
    `Jump to Page ${match.page_number}`
  )}
</Button>
                  </div>
                ))}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
