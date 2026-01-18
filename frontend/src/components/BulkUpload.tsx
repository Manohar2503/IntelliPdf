import React, { useCallback } from "react";
import { Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useDocumentStore } from "@/store/useDocumentStore";
import { PdfDoc } from "@/types";
import { useToast } from "@/hooks/use-toast";
import { BACKEND_URL } from "@/config";

export function BulkUpload() {
  const { addDocument, removeDocument } = useDocumentStore();
  const { toast } = useToast();

  const handleFiles = useCallback(
    async (files: FileList) => {
      const pdfFiles = Array.from(files).filter(
        (file) => file.type === "application/pdf"
      );

      if (pdfFiles.length === 0) {
        toast({
          title: "No PDF files selected",
          description: "Please select PDF files to upload.",
          variant: "destructive",
        });
        return;
      }

      if (pdfFiles.length > 20) {
        toast({
          title: "Too many files",
          description: "Maximum 20 files allowed at once.",
          variant: "destructive",
        });
        return;
      }

      try {
        const formData = new FormData();
        pdfFiles.forEach((file) => formData.append("files", file));

        // ✅ FIXED fetch URL
        const res = await fetch(`${BACKEND_URL}/upload/bulk`, {
          method: "POST",
          body: formData,
        });

        if (!res.ok) throw new Error("Bulk upload failed");
        const data = await res.json();

        // ✅ Add uploaded docs to frontend store
        data.files.forEach((fileData: any) => {
          const doc: PdfDoc = {
            id: fileData.id, // ✅ use backend-generated id
            name: fileData.name,
            sizeBytes: fileData.sizeBytes,
            pages: fileData.pages,
            sections: [],
            dateISO: new Date().toISOString(),
            blob: pdfFiles.find((f) => f.name === fileData.name) || null,
            status: "ready",
            url: fileData.url,
          };

          addDocument(doc);
        });

        toast({
          title: "Files uploaded",
          description: `${pdfFiles.length} PDF files uploaded successfully.`,
        });
      } catch (err: any) {
        toast({
          title: "Upload error",
          description: err.message,
          variant: "destructive",
        });
      }
    },
    [addDocument, toast]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      if (e.dataTransfer.files.length > 0) handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) handleFiles(e.target.files);
      e.target.value = "";
    },
    [handleFiles]
  );

  // ✅ Delete document from frontend & backend
  const handleDelete = useCallback(
    async (doc: PdfDoc) => {
      try {
        const filename = doc.url?.split("/").pop();
        if (!filename) throw new Error("Invalid file URL");

        const res = await fetch(`${BACKEND_URL}/delete/${filename}`, {
          method: "DELETE",
        });

        if (!res.ok) throw new Error("Failed to delete file from backend");

        removeDocument(doc.id);

        toast({
          title: "Document deleted",
          description: `${doc.name} deleted from library and backend.`,
        });
      } catch (err: any) {
        toast({
          title: "Delete error",
          description: err.message,
          variant: "destructive",
        });
      }
    },
    [removeDocument, toast]
  );

  return (
    <Card className="animate-fade-in">
      <CardHeader>
        <CardTitle className="text-lg font-semibold">Bulk Upload PDFs</CardTitle>
      </CardHeader>

      <CardContent>
        <div
          className="border-2 border-dashed border-border rounded-xl p-8 text-center hover:border-primary/50 transition-colors cursor-pointer"
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onClick={() => document.getElementById("bulk-file-input")?.click()}
        >
          <Upload className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">
            Drop PDFs here or click to browse
          </h3>
          <p className="text-sm text-muted-foreground mb-6">
            Up to 20 PDFs at once • Maximum 35 total
          </p>
          <Button variant="default" size="lg">
            Select Files
          </Button>
        </div>

        <input
          id="bulk-file-input"
          type="file"
          multiple
          accept=".pdf"
          className="hidden"
          onChange={handleFileSelect}
        />
      </CardContent>
    </Card>
  );
}
