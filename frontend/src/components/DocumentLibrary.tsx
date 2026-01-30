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
import { BACKEND_URL } from '@/config';

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
      const res = await fetch(`${BACKEND_URL}/delete/${encodeURIComponent(docName)}`, {
        method: "DELETE"
      });
      if (!res.ok) throw new Error("Failed to delete file from server");

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
        await fetch(`${BACKEND_URL}/delete/${encodeURIComponent(doc.name)}`, {
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
    <Card className="h-full animate-fade-in relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-[#050816]/90 via-[#0b1025]/80 to-[#120b2f]/90 shadow-2xl backdrop-blur-xl">
      {/* ✨ glow orbs */}
      <div className="pointer-events-none absolute -top-24 -left-24 h-60 w-60 rounded-full bg-cyan-500/20 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-24 -right-24 h-60 w-60 rounded-full bg-fuchsia-500/20 blur-3xl" />

      {/* ✨ tiny stars */}
      <div className="pointer-events-none absolute inset-0 opacity-40">
        <div className="absolute left-10 top-10 h-1 w-1 rounded-full bg-white shadow-[0_0_12px_2px_rgba(255,255,255,0.7)] animate-pulse" />
        <div className="absolute right-16 top-14 h-[2px] w-[2px] rounded-full bg-cyan-300 shadow-[0_0_14px_3px_rgba(34,211,238,0.8)] animate-pulse" />
        <div className="absolute left-1/2 top-8 h-[2px] w-[2px] rounded-full bg-purple-300 shadow-[0_0_14px_3px_rgba(216,180,254,0.85)] animate-pulse" />
      </div>

      <CardHeader className="relative pb-3">
        <CardTitle className="text-xl font-extrabold tracking-tight text-white">
          Document Library
        </CardTitle>

        <div className="space-y-3">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-white/50" />
            <Input
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 rounded-2xl border border-white/10 bg-white/5 text-white placeholder:text-white/40 shadow-lg backdrop-blur-xl focus-visible:ring-2 focus-visible:ring-cyan-400/40"
            />
          </div>

          {/* Clear all */}
          {documents.length > 0 && (
            <Button
              variant="outline"
              onClick={handleClearAll}
              className="w-full rounded-2xl border border-white/10 bg-white/5 text-white/80 shadow-lg hover:shadow-xl hover:bg-red-500/10 hover:text-red-300 transition-all"
            >
              Clear All Documents
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="relative space-y-3">
        {filteredDocuments.length === 0 ? (
          <div className="text-center text-white/60 py-10 rounded-3xl border border-white/10 bg-white/5 shadow-lg backdrop-blur-xl">
            {searchQuery ? 'No documents match your search.' : 'No documents uploaded yet.'}
          </div>
        ) : (
          filteredDocuments.map((doc) => (
            <div
              key={doc.id}
              className="group flex items-center gap-3 p-4 rounded-3xl border border-white/10 bg-gradient-to-br from-white/5 to-white/0 shadow-lg backdrop-blur-xl transition-all duration-300 hover:-translate-y-[1px] hover:shadow-2xl"
            >
              {/* File Icon */}
              <div className="relative flex-shrink-0">
                <div className="absolute -inset-1 rounded-2xl bg-gradient-to-r from-cyan-400/30 via-purple-500/25 to-fuchsia-500/30 blur-xl opacity-70" />
                <div className="relative w-11 h-11 rounded-2xl border border-white/10 bg-white/5 flex items-center justify-center shadow">
                  <FileText className="w-5 h-5 text-cyan-300" />
                </div>
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <h4 className="font-semibold text-white truncate">
                  {doc.name}
                </h4>

                <div className="flex items-center gap-2 mt-2 flex-wrap">
                  <Badge
                    variant="secondary"
                    className="text-[11px] rounded-full border border-white/10 bg-white/5 text-white/70"
                  >
                    {doc.pages} pages
                  </Badge>

                  <Badge
                    variant="secondary"
                    className="text-[11px] rounded-full border border-white/10 bg-white/5 text-white/70"
                  >
                    {doc.sections.length} sections
                  </Badge>

                  <Badge
                    variant="secondary"
                    className="text-[11px] rounded-full border border-white/10 bg-white/5 text-white/70"
                  >
                    {formatDate(doc.uploadedAt)}
                  </Badge>

                  <Badge
                    variant="secondary"
                    className="text-[11px] rounded-full border border-white/10 bg-white/5 text-white/70"
                  >
                    {formatFileSize(doc.sizeBytes)}
                  </Badge>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2 flex-shrink-0">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handlePreview(doc)}
                  aria-label="Preview document"
                  className="rounded-2xl border border-white/10 bg-white/5 text-white/80 shadow hover:bg-white/10 hover:text-cyan-200 transition-all"
                >
                  <Eye className="w-4 h-4" />
                </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDelete(doc.id, doc.name)}
                  aria-label="Delete document"
                  className="rounded-2xl border border-white/10 bg-white/5 text-white/80 shadow hover:bg-red-500/10 hover:text-red-300 transition-all"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
