import React, { useState } from 'react';
import { Search, Eye, Trash2, FileText } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useDocumentStore } from '@/store/useDocumentStore';
import { useNavigate } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';
import { PdfDoc } from '@/types';


export function DocumentLibrary() {
const { documents, removeDocument, setActiveDoc, addDocument } = useDocumentStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [previewDoc, setPreviewDoc] = useState<PdfDoc | null>(null);

  const navigate = useNavigate();
  const { toast } = useToast();

  const filteredDocuments = documents.filter(doc =>

    doc.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

const handlePreview = (doc: any) => {
  // console.log("Preview doc:", doc);

  // Set active document in store
  setActiveDoc(doc.id);
  if (!documents.find((d) => d.id === doc.id)) {
    addDocument(doc);
  }
  const fileUrl = doc.url || (doc.blob && URL.createObjectURL(doc.blob));
  if (!fileUrl) {
    console.error("No URL or blob found for this document:", doc);
    return;
  }
  const encodedUrl = encodeURIComponent(fileUrl);
  const encodedName = encodeURIComponent(doc.name);
  navigate(`/simple-viewer?file=${encodedUrl}&name=${encodedName}&id=${doc.id}`);
};


  const handleDelete = async (docId: string, docName: string) => {
    try {
      // Call backend DELETE endpoint
      const res = await fetch(`http://localhost:8080/delete/${encodeURIComponent(docName)}`, {
        method: "DELETE"
      });
      if (!res.ok) throw new Error("Failed to delete file from server");

      // Remove from frontend store
      removeDocument(docId);

      toast({
        title: "Document deleted",
        description: `${docName} has been removed from your library.`
      });
    } catch (err: any) {
      toast({ title: "Delete error", description: err.message, variant: "destructive" });
    }
  };

  const handleClearAll = async () => {
    for (const doc of documents) {
      try {
        await fetch(`http://localhost:8080/delete/${encodeURIComponent(doc.name)}`, {
          method: "DELETE"
        });
      } catch (err) {
        console.warn(`Failed to delete ${doc.name} from backend`, err);
      }
      removeDocument(doc.id);
    }
    toast({
      title: "All documents cleared",
      description: "All documents have been removed from your library."
    });
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateISO: string) => {
    return new Date(dateISO).toLocaleDateString();
  };

  return (
    <Card className="h-full animate-fade-in">
      <CardHeader>
        <CardTitle className="text-lg font-semibold">Document Library</CardTitle>
        <div className="space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          {documents.length > 0 && (
            <Button
              variant="outline"
              onClick={handleClearAll}
              className="w-full hover-scale"
            >
              Clear All Documents
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {filteredDocuments.length === 0 ? (
          <div className="text-center text-muted-foreground py-8">
            {searchQuery ? 'No documents match your search.' : 'No documents uploaded yet.'}
          </div>
        ) : (
          filteredDocuments.map((doc) => (
            <div
              key={doc.id}
              className="flex items-center gap-3 p-4 border border-border rounded-xl hover:bg-muted/50 hover:shadow-md transition-all duration-300 hover-scale"
            >
              <div className="w-10 h-10 bg-primary/10 rounded-xl flex items-center justify-center flex-shrink-0">
                <FileText className="w-5 h-5 text-primary" />
              </div>

              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-foreground truncate">{doc.name}</h4>
                {/* <p className="text-sm text-muted-foreground">
                  {doc.status === 'processing' ? 'Processing...' : doc.summary}
                </p> */}
                <div className="flex items-center gap-2 mt-1 flex-wrap">
                  <Badge variant="secondary" className="text-xs">{doc.pages} pages</Badge>
                  <Badge variant="secondary" className="text-xs">{doc.sections.length} sections</Badge>
                  <Badge variant="secondary" className="text-xs">{formatDate(doc.uploadedAt)}</Badge>
                  <Badge variant="secondary" className="text-xs">{formatFileSize(doc.sizeBytes)}</Badge>
                </div>
              </div>

              <div className="flex items-center gap-1 flex-shrink-0">
                <Button
                      variant="ghost"
                    size="sm"
                onClick={() => handlePreview(doc)}
                    aria-label="Preview document"
                     >
                    <Eye className="w-4 h-4" />
                    </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDelete(doc.id, doc.name)}
                  aria-label="Delete document"
                >
                  <Trash2 className="w-4 h-4 text-destructive" />
                </Button>
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
