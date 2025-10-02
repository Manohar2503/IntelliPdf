import React, { useState, useRef, useEffect } from 'react';
import { Lightbulb, Mic, ArrowLeft } from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ChatbotSidebar } from '@/components/ChatbotSidebar';
import { AdobeViewer, AdobeViewerRef } from '@/components/AdobeViewer';
import { Recommendations } from '@/components/Recommendations';
import { InsightsModal } from '@/components/InsightsModal';
import { PodcastPanel } from '@/components/PodcastPanel';
import { useDocumentStore } from '@/store/useDocumentStore';
import { useToast } from '@/hooks/use-toast';
import { PdfDoc } from '@/types';

export default function Viewer() {
  const { activeDocId, documents, analysisSet, setActiveDoc, setSelection, addDocument } =
    useDocumentStore();
  const [showInsights, setShowInsights] = useState(false);
  const [showPodcast, setShowPodcast] = useState(false);
  const viewerRef = useRef<AdobeViewerRef>(null);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const mode = searchParams.get('mode'); // 👈 already there

  const [pdfDocFromUrl, setPdfDocFromUrl] = useState<PdfDoc | null>(null);

  // ✅ Read URL params and add to store if needed
  useEffect(() => {
    const fileUrl = searchParams.get('file');
    const name = searchParams.get('name') || 'Document';
    const id = searchParams.get('id') || `viewer_${Date.now()}`;

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
        status: 'ready',
      };
      addDocument(newDoc);
      setPdfDocFromUrl(newDoc);
    } else {
      setPdfDocFromUrl(existingDoc);
    }

    setActiveDoc(id);
  }, [searchParams, documents, addDocument, setActiveDoc]);

  // Fallback: pick first document if nothing active
  useEffect(() => {
    if (!activeDocId && analysisSet.length > 0) {
      setActiveDoc(analysisSet[0]);
    }
  }, [activeDocId, analysisSet, setActiveDoc]);

  // Redirect if no analysis set (skip this in simple mode)
  useEffect(() => {
    if (mode !== 'simple' && analysisSet.length === 0 && !pdfDocFromUrl) {
      toast({
        title: 'No documents selected',
        description: 'Please select documents for analysis first.',
        variant: 'destructive',
      });
      navigate('/library');
    }
  }, [analysisSet.length, navigate, toast, mode, pdfDocFromUrl]);

  const activeDoc = useDocumentStore((state) =>
    state.documents.find((doc) => doc.id === state.activeDocId)
  );

  const pdfToShow = pdfDocFromUrl || activeDoc;

  if (!pdfToShow) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold mb-2">No Document Selected</h2>
          <p className="text-muted-foreground mb-4">Please select a document to view.</p>
          <Button onClick={() => navigate('/library?from=viewer')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Library
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-background flex flex-col">
      {/* Top toolbar */}
      <div className="bg-card border-b border-border px-4 py-2 flex items-center justify-between">
        <Button
          variant="ghost"
          onClick={() => navigate('/library?from=viewer')}
          className="flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Library
        </Button>

        {/* 👇 Hide insights/podcast if simple mode */}
        {mode !== 'simple' && (
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="lg"
              onClick={() => setShowInsights(true)}
              className="relative w-14 h-14 rounded-full bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600 shadow-lg hover:shadow-xl transition-all duration-300"
              aria-label="View insights"
            >
              <Lightbulb className="w-7 h-7 text-white drop-shadow-lg" />
            </Button>
            <Button
              variant="ghost"
              size="lg"
              onClick={() => setShowPodcast(true)}
              className="relative w-14 h-14 rounded-full bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600 shadow-lg hover:shadow-xl transition-all duration-300"
              aria-label="Generate podcast"
            >
              <Mic className="w-7 h-7 text-white drop-shadow-lg" />
            </Button>
          </div>
        )}
      </div>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">

        {/* Center - PDF Viewer */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 relative">
            <AdobeViewer
              ref={viewerRef}
              pdfDoc={pdfToShow}
              onSelectionChange={setSelection}
            />
          </div>
        </div>

        {/* Left sidebar - Chatbot */}
        {mode !== 'simple' && <ChatbotSidebar />}


        {/* Right sidebar - Recommendations */}
        {mode !== 'simple' && <Recommendations viewerRef={viewerRef} />}
      </div>

      {/* Modals */}
      {mode !== 'simple' && (
        <>
          <InsightsModal isOpen={showInsights} onClose={() => setShowInsights(false)} />
          <PodcastPanel isOpen={showPodcast} onClose={() => setShowPodcast(false)} />
        </>
      )}
    </div>
  );
}
