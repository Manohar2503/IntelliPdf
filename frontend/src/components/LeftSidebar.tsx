import React, { useState } from 'react';
import { Search, FileText, Trash2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useDocumentStore } from '@/store/useDocumentStore';
import { useToast } from '@/hooks/use-toast';

export function LeftSidebar() {
  const { documents, analysisSet, activeDocId, setActiveDoc, removeFromAnalysisSet, removeDocument } = useDocumentStore();
  const [searchQuery, setSearchQuery] = useState('');
  const { toast } = useToast();

  const analysisDocuments = documents.filter(doc => analysisSet.includes(doc.id));
  const filteredDocuments = analysisDocuments.filter(doc =>
    doc.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleDocumentSelect = (docId: string) => {
    setActiveDoc(docId);
  };

  const handleRemoveFromAnalysis = (docId: string, docName: string) => {
    removeFromAnalysisSet(docId);
    if (activeDocId === docId) {
      const remainingDocs = analysisSet.filter(id => id !== docId);
      setActiveDoc(remainingDocs.length > 0 ? remainingDocs[0] : null);
    }
    toast({
      title: "Document removed",
      description: `${docName} has been removed from analysis set.`
    });
  };

  return (
    <div className="w-80 bg-card border-r border-border flex flex-col h-full">
      <div className="p-4 border-b border-border">
        <h3 className="font-semibold text-foreground mb-3">Analysis Set</h3>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search files..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {filteredDocuments.length === 0 ? (
          <div className="p-4 text-center text-muted-foreground">
            {analysisSet.length === 0 
              ? 'No files in analysis set'
              : 'No files match your search'
            }
          </div>
        ) : (
          <div className="p-2">
            {filteredDocuments.map((doc) => (
              <div
                key={doc.id}
                className={`p-3 rounded-lg cursor-pointer transition-colors mb-2 ${
                  activeDocId === doc.id
                    ? 'bg-primary/10 border border-primary/20'
                    : 'hover:bg-muted/50'
                }`}
                onClick={() => handleDocumentSelect(doc.id)}
              >
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-primary/10 rounded flex items-center justify-center flex-shrink-0 mt-0.5">
                    <FileText className="w-4 h-4 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-foreground text-sm truncate mb-1">
                      {doc.name}
                    </h4>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="text-xs">
                        {doc.pages} pages
                      </Badge>
                      {activeDocId === doc.id && (
                        <Badge variant="default" className="text-xs">
                          Active
                        </Badge>
                      )}
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemoveFromAnalysis(doc.id, doc.name);
                    }}
                    className="flex-shrink-0"
                    aria-label="Remove from analysis"
                  >
                    <Trash2 className="w-3 h-3 text-destructive" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}