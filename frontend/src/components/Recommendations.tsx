import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { useDocumentStore } from "@/store/useDocumentStore";
import { AdobeViewerRef } from "./AdobeViewer";
import { BACKEND_URL } from "@/config";
import { Sparkles, BookOpen, ArrowRight, FileSearch } from "lucide-react";

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
  const activeDoc = documents.find((doc) => doc.id === activeDocId);

  const context = selection || activeDoc;

  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingPage, setLoadingPage] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!context) return;

    const fetchRecommendations = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`${BACKEND_URL}/search`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            selected_text: selection?.text || activeDoc?.name || "",
            top_k: 3,
            min_score: 0.3,
          }),
        });

        if (!response.ok) throw new Error(`API error: ${response.statusText}`);

        const data: Recommendation[] = await response.json();
        setRecommendations(data);
      } catch (err: any) {
        setError(err.message || "Something went wrong");
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [context]);

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
          await new Promise((resolve) => setTimeout(resolve, 500));
        }
      }
    } catch (err) {
      console.error("Error jumping to page:", err);
      setLoadingPage(null);
    }
  };

  // ✅ Empty State (no doc / no selection)
  if (!context) {
    return (
      <div className="w-96 border-l border-border bg-background p-4 flex flex-col h-full">
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className="w-5 h-5 text-primary" />
          <h3 className="font-semibold text-foreground">Smart Recommendations</h3>
        </div>

        <div className="flex-1 flex items-center justify-center text-center text-muted-foreground">
          <div>
            <BookOpen className="w-10 h-10 mx-auto mb-3 opacity-60" />
            <p className="text-sm font-medium">No PDF selected</p>
            <p className="text-xs mt-1">
              Upload and analyze a PDF to get study suggestions.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const contextLabel = selection
    ? `Based on your selection`
    : `Based on full document`;

  const contextPreview = selection
    ? `"${selection.text.substring(0, 60)}..."`
    : `"${activeDoc?.name}"`;

  return (
    <div className="w-96 border-l border-border bg-background flex flex-col h-[calc(100vh-64px)]">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <FileSearch className="w-5 h-5 text-primary" />
            <h3 className="font-semibold text-foreground">Smart Recommendations</h3>
          </div>

          <Badge
            variant="secondary"
            className="text-xs rounded-full bg-primary/10 text-primary"
          >
            {loading ? "Loading..." : `${recommendations.length} docs`}
          </Badge>
        </div>

        <p className="text-xs text-muted-foreground mt-2">
          <span className="font-medium text-foreground/90">{contextLabel}:</span>{" "}
          {contextPreview}
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Loading skeleton */}
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="rounded-2xl border border-border bg-muted/30 p-4 animate-pulse"
              >
                <div className="h-4 w-3/4 bg-muted rounded mb-2" />
                <div className="h-3 w-1/2 bg-muted rounded mb-4" />
                <div className="h-9 w-full bg-muted rounded-xl" />
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-10">
            <p className="text-sm font-medium text-red-500">{error}</p>
            <p className="text-xs text-muted-foreground mt-1">
              Try selecting a different text or refresh once.
            </p>
          </div>
        ) : recommendations.length === 0 ? (
          <div className="text-center text-muted-foreground py-10">
            <Sparkles className="w-10 h-10 mx-auto mb-3 opacity-50" />
            <p className="text-sm font-medium">No recommendations yet</p>
            <p className="text-xs mt-1">
              Highlight a paragraph in the PDF to get better results ✅
            </p>
          </div>
        ) : (
          recommendations.map((rec, index) => (
            <Card
              key={`${rec.doc_id}-${index}`}
              className="rounded-2xl border border-border bg-card hover:shadow-md transition"
            >
              <CardContent className="p-4">
                {/* Card Top */}
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-foreground leading-snug">
                      {rec.title}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Source: {rec.source || "Library"}
                    </p>
                  </div>

                  <Badge
                    variant="secondary"
                    className="text-xs rounded-full bg-primary/10 text-primary flex-shrink-0"
                  >
                    {rec.matches.length} matches
                  </Badge>
                </div>

                {/* Matches */}
                <div className="mt-4 space-y-3">
                  {rec.matches.map((match, idx) => {
                    const scorePercent = Math.round((match.score || 0) * 100);

                    return (
                      <div
                        key={idx}
                        className="rounded-xl border border-border bg-muted/20 p-3"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <Badge variant="secondary" className="text-xs rounded-full">
                            📌 Page {match.page_number}
                          </Badge>

                          <span className="text-[11px] text-muted-foreground">
                            Match: {scorePercent}%
                          </span>
                        </div>

                        <p className="text-sm text-foreground mt-2 leading-relaxed">
                          {match.top_snippet}
                        </p>

                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleJumpToPage(rec, match.page_number)}
                          className="mt-3 w-full text-xs rounded-xl flex items-center justify-center gap-2"
                          disabled={loadingPage !== null}
                        >
                          {loadingPage === match.page_number ? (
                            <>
                              <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                              Jumping...
                            </>
                          ) : (
                            <>
                              Open this page <ArrowRight className="w-4 h-4" />
                            </>
                          )}
                        </Button>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Footer Tip */}
      <div className="p-4 border-t border-border">
        <p className="text-[11px] text-muted-foreground">
          ✅ Tip: Selecting 1–2 lines gives better recommendations than selecting
          a full page.
        </p>
      </div>
    </div>
  );
}
