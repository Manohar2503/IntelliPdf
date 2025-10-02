import React, { useEffect } from 'react';
import { ArrowLeft } from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { AdobeViewer } from '@/components/AdobeViewer';
import { useDocumentStore } from '@/store/useDocumentStore';
import { useToast } from '@/hooks/use-toast';

export default function SimpleViewer() {
  const { activeDocId, documents } = useDocumentStore();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const mode = searchParams.get('mode');

  const activeDoc = documents.find(doc => doc.id === activeDocId);

  // If no active document, redirect to library
  useEffect(() => {
    if (!activeDoc) {
      toast({
        title: "No document selected",
        description: "Please select a document to view.",
        variant: "destructive"
      });
      navigate('/library');
    }
  }, [activeDoc, navigate, toast]);

  if (!activeDoc) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold mb-2">No Document Selected</h2>
          <p className="text-muted-foreground mb-4">Please select a document to view.</p>
          <Button onClick={() => navigate('/library')}>
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
          onClick={() => navigate('/library')}
          className="flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Library
        </Button>
        
        <h1 className="text-lg font-semibold">PDF Viewer</h1>
        <div></div>
      </div>

      {/* PDF Viewer */}
      <div className="flex-1 overflow-hidden">
        <AdobeViewer
          pdfDoc={activeDoc}
        />
      </div>
    </div>
  );
}