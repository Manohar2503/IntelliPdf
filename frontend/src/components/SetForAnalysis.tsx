import React, { useCallback, useState,useEffect } from 'react';
import { Plus, X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useDocumentStore } from '@/store/useDocumentStore';
import { PdfDoc } from '@/types';
import { useNavigate } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';

export function SetForAnalysis() {
  const { 
  addDocument, 
  selectedAnalysisFiles, 
  addSelectedAnalysisFile, 
  removeSelectedAnalysisFile,
  clearSelectedAnalysisFiles,
  setAnalysisSet
} = useDocumentStore();

  const navigate = useNavigate();
  const { toast } = useToast();
  // useEffect(() => {
  //   // Check if the navigation type is "reload"
  //   const navEntries = performance.getEntriesByType("navigation") as PerformanceNavigationTiming[];
  //   const isReload = navEntries.length > 0 && navEntries[0].type === "reload";

  //   if (isReload) {
  //     fetch("http://localhost:8080/deletefolder")
  //       .then((res) => res.json())
  //       .then((data) => console.log("API called on refresh:", data))
  //       .catch((err) => console.error(err));
  //   }
  // }, []);
  const handleFiles = useCallback(async (files: FileList) => {
  const pdfFiles = Array.from(files).filter(file => file.type === 'application/pdf');

  if (pdfFiles.length === 0) {
    toast({ title: "No PDF files selected", description: "Please select PDF files for analysis.", variant: "destructive" });
    return;
  }

  try {
    for (const file of pdfFiles) {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("http://localhost:8080/upload/new", {
        method: "POST",
        body: formData
      });

      if (!res.ok) throw new Error(`Failed to upload ${file.name}`);

      const data = await res.json();

      const doc: PdfDoc = {
        id: `analysis_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        name: file.name,
        sizeBytes: file.size,
        pages: 0,
        sections: [],
        dateISO: new Date().toISOString(),
        blob: null,
        status: 'ready',
        url: data.file.url
      };

      addDocument(doc);
      addSelectedAnalysisFile(doc); // ✅ add to store
    }

    toast({ title: "Files added", description: `${pdfFiles.length} PDF files added for analysis.` });
  } catch (err: any) {
    toast({ title: "Upload error", description: err.message, variant: "destructive" });
  }
}, [addDocument, addSelectedAnalysisFile, toast]);


  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) handleFiles(e.target.files);
    e.target.value = '';
  }, [handleFiles]);

  // New: Remove file from frontend & backend
  const removeFile = useCallback(async (fileId: string, url: string) => {
  try {
    const filename = url.split("/").pop();
    const res = await fetch(`http://localhost:8080/delete/${filename}`, { method: "DELETE" });
    if (!res.ok) throw new Error("Failed to delete file from backend");

    removeSelectedAnalysisFile(fileId); // ✅ remove from store

    toast({
      title: "File deleted",
      description: "File removed from analysis set and backend.",
    });
  } catch (err: any) {
    toast({
      title: "Delete error",
      description: err.message,
      variant: "destructive",
    });
  }
}, [removeSelectedAnalysisFile, toast]);


  const handleAnalyze = async () => {
  if (selectedAnalysisFiles.length === 0) {
    toast({ title: "No files selected", description: "Please select files for analysis.", variant: "destructive" });
    return;
  }

  setAnalysisSet(selectedAnalysisFiles.map(f => f.id));
  navigate('/viewer');
  await fetch("http://localhost:8080/process", { method: "POST" });
};

  const handleClear = () => {
  selectedAnalysisFiles.forEach(file => removeFile(file.id, file.url));
  clearSelectedAnalysisFiles(); // ✅ clear store
};

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Card className="animate-fade-in">
      <CardHeader>
        <CardTitle className="text-lg font-semibold">Set New File for Analysis</CardTitle>
        <p className="text-sm text-muted-foreground">
          Upload a single PDF for detailed analysis and insights
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {selectedAnalysisFiles.length > 0 && (
  <div className="space-y-2">
    {selectedAnalysisFiles.map((file) => (
      <div key={file.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-xl border border-border/50 hover:bg-muted transition-colors">
        <div>
          <span className="text-sm font-medium">{file.name}</span>
          <span className="text-xs text-muted-foreground ml-2">
            {formatFileSize(file.sizeBytes)}
          </span>
        </div>
        <Button variant="ghost" size="sm" onClick={() => removeFile(file.id, file.url)} aria-label="Remove file">
          <X className="w-4 h-4" />
        </Button>
      </div>
    ))}
  </div>
)}

       {selectedAnalysisFiles.length > 0 ? (
  <div className="space-y-3 animate-fade-in">
    <div className="flex gap-3">
      <Button onClick={() => document.getElementById('analysis-file-input')?.click()} className="flex-1 hover-scale" variant="secondary" size="sm">
        <Plus className="w-4 h-4 mr-2" /> Set New File
      </Button>
      <Button variant="outline" onClick={handleClear} className="flex-1 hover-scale" size="sm">
        Clear All Files
      </Button>
    </div>
    <Button onClick={handleAnalyze} className="w-full hover-scale" size="lg">
      Analyze
    </Button>
  </div>
) : (
  <Button onClick={() => document.getElementById('analysis-file-input')?.click()} className="w-full hover-scale" variant="secondary">
    <Plus className="w-4 h-4 mr-2" /> Set New File
  </Button>
)}

        <input id="analysis-file-input" type="file" multiple accept=".pdf" className="hidden" onChange={handleFileSelect} />
      </CardContent>
    </Card>
  );
}
