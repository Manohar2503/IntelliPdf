import React, { useState, useRef, useEffect } from "react";
import { Lightbulb, ArrowLeft, FileText } from "lucide-react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ChatbotSidebar } from "@/components/ChatbotSidebar";
import { AdobeViewer, AdobeViewerRef } from "@/components/AdobeViewer";
import { Recommendations } from "@/components/Recommendations";
import { InsightsModal } from "@/components/InsightsModal";
import { useDocumentStore } from "@/store/useDocumentStore";
import { useToast } from "@/hooks/use-toast";
import { PdfDoc } from "@/types";

export default function Viewer() {
  const {
    activeDocId,
    documents,
    analysisSet,
    setActiveDoc,
    setSelection,
    addDocument,
  } = useDocumentStore();

  const [showInsights, setShowInsights] = useState(false);
  const viewerRef = useRef<AdobeViewerRef>(null);

  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const mode = searchParams.get("mode"); // simple or full

  const [pdfDocFromUrl, setPdfDocFromUrl] = useState<PdfDoc | null>(null);

  // ✅ Read URL params and add to store if needed
  useEffect(() => {
    const fileUrl = searchParams.get("file");
    const name = searchParams.get("name") || "Document";
    const id = searchParams.get("id") || `viewer_${Date.now()}`;

    if (!fileUrl) return;

    const decodedUrl = decodeURIComponent(fileUrl);

    const existingDoc = documents.find((doc) => doc.id === id);
    if (!existingDoc) {
      const newDoc: PdfDoc = {
        id,
        name,
        url: decodedUrl,
        sizeBytes: 0,
        pages: 0,
        sections: [],
        dateISO: new Date().toISOString(),
        status: "ready",
      };
      addDocument(newDoc);
      setPdfDocFromUrl(newDoc);
    } else {
      setPdfDocFromUrl(existingDoc);
    }

    setActiveDoc(id);
  }, [searchParams, documents, addDocument, setActiveDoc]);

  // Fallback: pick first doc if nothing active
  useEffect(() => {
    if (!activeDocId && analysisSet.length > 0) {
      setActiveDoc(analysisSet[0]);
    }
  }, [activeDocId, analysisSet, setActiveDoc]);

  // Redirect if no analysis set (skip in simple mode)
  useEffect(() => {
    if (mode !== "simple" && analysisSet.length === 0 && !pdfDocFromUrl) {
      toast({
        title: "No documents selected",
        description: "Please select documents for analysis first.",
        variant: "destructive",
      });
      navigate("/library");
    }
  }, [analysisSet.length, navigate, toast, mode, pdfDocFromUrl]);

  const activeDoc = useDocumentStore((state) =>
    state.documents.find((doc) => doc.id === state.activeDocId)
  );

  const pdfToShow = pdfDocFromUrl || activeDoc;

  // ✅ Empty Page UI
  if (!pdfToShow) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center px-6">
        <div className="w-full max-w-md rounded-2xl border border-white/10 bg-white/5 p-6 text-center">
          <div className="w-12 h-12 mx-auto mb-3 rounded-2xl bg-white/10 flex items-center justify-center">
            <FileText className="w-6 h-6 text-white/70" />
          </div>
          <h2 className="text-lg font-semibold text-white">
            No Document Selected
          </h2>
          <p className="text-sm text-white/60 mt-2">
            Please select a PDF from your Library to start studying.
          </p>

          <Button
            onClick={() => navigate("/library?from=viewer")}
            className="mt-5 w-full rounded-xl bg-cyan-500/20 hover:bg-cyan-500/30 text-white border border-cyan-500/20"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Library
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-zinc-950 flex flex-col">
      {/* ✅ Top Toolbar */}
      <div className="border-b border-white/10 bg-zinc-950/70 backdrop-blur-xl px-4 py-3 flex items-center justify-between">
        {/* Left */}
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            onClick={() => navigate("/library?from=viewer")}
            className="rounded-full border-white/10 bg-white/5 text-white hover:bg-white/10"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Library
          </Button>

          <div className="hidden md:flex flex-col">
            <p className="text-sm font-semibold text-white truncate max-w-[420px]">
              📄 {pdfToShow.name}
            </p>
            <p className="text-xs text-white/50">
              Student Mode • Quick recap • Smart Q&A
            </p>
          </div>
        </div>

        {/* Right */}
        {mode !== "simple" && (
          <div className="flex items-center gap-3">
            <Button
              onClick={() => setShowInsights(true)}
              className="rounded-full bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 hover:from-emerald-500/30 hover:to-cyan-500/30 text-white border border-white/10"
            >
              <Lightbulb className="w-4 h-4 mr-2 text-yellow-300" />
              1-Minute Recap
            </Button>
          </div>
        )}
      </div>

      {/* ✅ Main Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left - Chatbot */}
        {mode !== "simple" && <ChatbotSidebar />}

        {/* Center - PDF Viewer */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 relative">
            <div className="absolute inset-0">
              <AdobeViewer
                ref={viewerRef}
                pdfDoc={pdfToShow}
                onSelectionChange={setSelection}
              />
            </div>
          </div>
        </div>

        {/* Right - Recommendations */}
        {mode !== "simple" && <Recommendations viewerRef={viewerRef} />}
      </div>

      {/* Modals */}
      {mode !== "simple" && (
        <InsightsModal
          isOpen={showInsights}
          onClose={() => setShowInsights(false)}
        />
      )}
    </div>
  );
}
