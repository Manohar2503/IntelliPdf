import React, { useCallback, useState, useEffect } from "react";
import { Plus, X } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useDocumentStore } from "@/store/useDocumentStore";
import { PdfDoc } from "@/types";
import { useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import { BACKEND_URL } from "@/config";
import { getSessionId } from "@/utils/session";

export function SetForAnalysis() {
  const {
    addDocument,
    selectedAnalysisFiles,
    addSelectedAnalysisFile,
    removeSelectedAnalysisFile,
    clearSelectedAnalysisFiles,
    setAnalysisSet,
  } = useDocumentStore();

  const navigate = useNavigate();
  const { toast } = useToast();

  const [isProcessing, setIsProcessing] = useState(false);

  // ✅ tips rotation during processing
  const tips = [
    "📌 Tip: You can select text in the PDF and search for related sections.",
    "⚡ Tip: Use the chatbot to ask questions like 'What is the conclusion?'",
    "🧠 Tip: IntelliPDF finds the most relevant parts using embeddings.",
    "🔍 Tip: Recommendations show the best matching sections instantly.",
    "✅ Tip: Generate Summary when you're ready inside the Chatbot.",
  ];

  const [tipIndex, setTipIndex] = useState(0);

  useEffect(() => {
    if (!isProcessing) return;

    const interval = setInterval(() => {
      setTipIndex((prev) => (prev + 1) % tips.length);
    }, 2500);

    return () => clearInterval(interval);
  }, [isProcessing]);

  // ✅ Upload file
  const handleFiles = useCallback(
    async (files: FileList) => {
      const pdfFiles = Array.from(files).filter(
        (file) => file.type === "application/pdf"
      );

      if (pdfFiles.length === 0) {
        toast({
          title: "No PDF files selected",
          description: "Please select a PDF file for analysis.",
          variant: "destructive",
        });
        return;
      }

      const file = pdfFiles[0];

      try {
        clearSelectedAnalysisFiles();

        const sessionId = getSessionId();

        const formData = new FormData();
        formData.append("sessionId", sessionId); // ✅ IMPORTANT
        formData.append("file", file);

        const res = await fetch(`${BACKEND_URL}/upload/new`, {
          method: "POST",
          body: formData,
        });

        if (!res.ok) throw new Error(`Failed to upload ${file.name}`);

        const data = await res.json();

        const doc: PdfDoc = {
          id: `analysis_${Date.now()}_${Math.random()
            .toString(36)
            .substr(2, 9)}`,
          name: file.name,
          sizeBytes: file.size,
          pages: data?.file?.pages || 0,
          sections: [],
          dateISO: new Date().toISOString(),
          blob: null,
          status: "ready",
          url: `${BACKEND_URL}${data.file.url}`,
        };

        addDocument(doc);
        addSelectedAnalysisFile(doc);

        toast({
          title: "File added ✅",
          description: `${file.name} added for analysis.`,
        });
      } catch (err: any) {
        toast({
          title: "Upload error",
          description: err.message || "Upload failed",
          variant: "destructive",
        });
      }
    },
    [addDocument, addSelectedAnalysisFile, toast, clearSelectedAnalysisFiles]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) handleFiles(e.target.files);
      e.target.value = "";
    },
    [handleFiles]
  );

  // ✅ Delete file
  const removeFile = useCallback(
    async (fileId: string, url: string) => {
      try {
        const sessionId = getSessionId();

        const filename = url.split("/").pop();
        if (!filename) throw new Error("Invalid filename");

        const res = await fetch(
          `${BACKEND_URL}/delete/${filename}?sessionId=${sessionId}`,
          {
            method: "DELETE",
          }
        );

        if (!res.ok) throw new Error("Failed to delete file from backend");

        removeSelectedAnalysisFile(fileId);

        toast({
          title: "File deleted ✅",
          description: "File removed from analysis set and backend.",
        });
      } catch (err: any) {
        toast({
          title: "Delete error",
          description: err.message || "Delete failed",
          variant: "destructive",
        });
      }
    },
    [removeSelectedAnalysisFile, toast]
  );

  // ✅ Process Analyze
  const handleAnalyze = async () => {
    if (selectedAnalysisFiles.length === 0) {
      toast({
        title: "No files selected",
        description: "Please upload a PDF first.",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsProcessing(true);

      toast({
        title: "Processing started...",
        description: "Please wait while we analyze the PDF ✅",
      });

      const sessionId = getSessionId();

      const formData = new FormData();
      formData.append("sessionId", sessionId); // ✅ IMPORTANT

      const processRes = await fetch(`${BACKEND_URL}/process`, {
        method: "POST",
        body: formData,
      });

      if (!processRes.ok) {
        throw new Error("Failed to process PDF");
      }

      toast({
        title: "Processing completed ✅",
        description: "Now opening Viewer...",
      });

      setAnalysisSet(selectedAnalysisFiles.map((f) => f.id));
      navigate("/viewer");
    } catch (err: any) {
      toast({
        title: "Processing error",
        description: err.message || "Something went wrong while processing your PDF",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleClear = () => {
    selectedAnalysisFiles.forEach((file) => removeFile(file.id, file.url));
    clearSelectedAnalysisFiles();
  };

  const formatFileSize = (bytes: number) => {
    if (!bytes) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <Card className="animate-fade-in">
      <CardHeader>
        <CardTitle className="text-lg font-semibold">
          Set New File for Analysis
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          Upload a single PDF for detailed analysis and insights
        </p>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* ✅ Processing UI */}
        {isProcessing && (
          <div className="relative group p-6 rounded-2xl border bg-gradient-to-r from-muted/40 to-muted/10 space-y-4 animate-fade-in shadow-md">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-full border-4 border-primary border-t-transparent animate-spin" />
              <div>
                <p className="text-lg font-semibold">
                  Processing your PDF... ✅
                </p>
                <p className="text-sm text-muted-foreground">
                  Hover here to see details 👇
                </p>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-background border text-base font-medium">
              {tips[tipIndex]}
            </div>

            <div className="absolute left-0 top-full mt-3 w-full hidden group-hover:block z-50">
              <div className="p-6 rounded-2xl border bg-background shadow-2xl space-y-4">
                <p className="text-xl font-bold">✨ What’s happening now?</p>

                <ul className="list-disc pl-5 text-sm text-muted-foreground space-y-2">
                  <li>Extracting sections from your PDF</li>
                  <li>Generating embeddings for smart search</li>
                  <li>Preparing document insights</li>
                  <li>Getting everything ready for chatbot + recommendations</li>
                </ul>

                <div className="p-4 rounded-xl bg-muted border">
                  <p className="text-sm font-semibold mb-1">📌 Current Tip:</p>
                  <p className="text-base">{tips[tipIndex]}</p>
                </div>

                <p className="text-xs text-muted-foreground">
                  ✅ This may take longer for big PDFs (100+ pages). Please wait...
                </p>
              </div>
            </div>
          </div>
        )}

        {/* ✅ Selected file list */}
        {selectedAnalysisFiles.length > 0 && (
          <div className="space-y-2">
            {selectedAnalysisFiles.map((file) => (
              <div
                key={file.id}
                className="flex items-center justify-between p-3 bg-muted/50 rounded-xl border border-border/50 hover:bg-muted transition-colors"
              >
                <div>
                  <span className="text-sm font-medium">{file.name}</span>
                  <span className="text-xs text-muted-foreground ml-2">
                    {formatFileSize(file.sizeBytes)}
                  </span>
                </div>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeFile(file.id, file.url)}
                  aria-label="Remove file"
                  disabled={isProcessing}
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            ))}
          </div>
        )}

        {/* ✅ Buttons */}
        {selectedAnalysisFiles.length > 0 ? (
          <div className="space-y-3 animate-fade-in">
            <div className="flex gap-3">
              <Button
                onClick={() =>
                  document.getElementById("analysis-file-input")?.click()
                }
                className="flex-1 hover-scale"
                variant="secondary"
                size="sm"
                disabled={isProcessing}
              >
                <Plus className="w-4 h-4 mr-2" /> Set New File
              </Button>

              <Button
                variant="outline"
                onClick={handleClear}
                className="flex-1 hover-scale"
                size="sm"
                disabled={isProcessing}
              >
                Clear All Files
              </Button>
            </div>

            <Button
              onClick={handleAnalyze}
              className="w-full hover-scale"
              size="lg"
              disabled={isProcessing}
            >
              {isProcessing ? "Analyzing..." : "Analyze"}
            </Button>
          </div>
        ) : (
          <Button
            onClick={() =>
              document.getElementById("analysis-file-input")?.click()
            }
            className="w-full hover-scale"
            variant="secondary"
            disabled={isProcessing}
          >
            <Plus className="w-4 h-4 mr-2" /> Set New File
          </Button>
        )}

        <input
          id="analysis-file-input"
          type="file"
          multiple
          accept=".pdf"
          className="hidden"
          onChange={handleFileSelect}
          disabled={isProcessing}
        />
      </CardContent>
    </Card>
  );
}
