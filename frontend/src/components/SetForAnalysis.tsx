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
    removeDocument, // ✅ ADDED
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

        // ✅ Remove from analysis list
        removeSelectedAnalysisFile(fileId);

        // ✅ ALSO remove from Document Library list
        removeDocument(fileId);

        toast({
          title: "File deleted ✅",
          description: "File removed from analysis set and library.",
        });
      } catch (err: any) {
        toast({
          title: "Delete error",
          description: err.message || "Delete failed",
          variant: "destructive",
        });
      }
    },
    [removeSelectedAnalysisFile, removeDocument, toast]
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
    <Card className="animate-fade-in relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-[#050816]/90 via-[#0b1025]/80 to-[#120b2f]/90 shadow-2xl backdrop-blur-xl">
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
          Set New File for Analysis
        </CardTitle>
        <p className="text-sm text-white/60">
          Upload a single PDF for detailed analysis and insights
        </p>
      </CardHeader>

      <CardContent className="relative space-y-4">
        {/* ✅ Processing UI */}
        {isProcessing && (
          <div className="relative group overflow-hidden p-6 rounded-3xl border border-white/10 bg-white/5 space-y-4 animate-fade-in shadow-xl backdrop-blur-xl">
            <div className="pointer-events-none absolute -top-16 -right-16 h-52 w-52 rounded-full bg-purple-500/20 blur-3xl" />
            <div className="pointer-events-none absolute -bottom-16 -left-16 h-52 w-52 rounded-full bg-cyan-500/20 blur-3xl" />

            <div className="relative flex items-center gap-4">
              <div className="w-11 h-11 rounded-2xl border border-white/10 bg-gradient-to-br from-cyan-400/15 via-purple-500/15 to-fuchsia-500/15 flex items-center justify-center shadow">
                <div className="w-6 h-6 rounded-full border-2 border-cyan-300 border-t-transparent animate-spin" />
              </div>

              <div>
                <p className="text-lg font-extrabold text-white">
                  Processing your PDF... ✅
                </p>
                <p className="text-sm text-white/60">
                  Hover here to see details 👇
                </p>
              </div>
            </div>

            <div className="relative h-2 w-full overflow-hidden rounded-full bg-white/10">
              <div className="h-full w-2/3 rounded-full bg-gradient-to-r from-cyan-300 via-purple-400 to-fuchsia-400 animate-pulse" />
            </div>

            <div className="relative p-4 rounded-2xl bg-black/30 border border-white/10 text-base font-semibold text-white shadow-sm">
              {tips[tipIndex]}
            </div>

            <div className="absolute left-0 top-full mt-3 w-full hidden group-hover:block z-50">
              <div className="p-6 rounded-3xl border border-white/10 bg-gradient-to-br from-[#06091a] via-[#0b1025] to-[#140b33] shadow-2xl space-y-4 backdrop-blur-xl">
                <p className="text-xl font-extrabold text-white">
                  ✨ What’s happening now?
                </p>

                <ul className="list-disc pl-5 text-sm text-white/70 space-y-2">
                  <li>Extracting sections from your PDF</li>
                  <li>Generating embeddings for smart search</li>
                  <li>Preparing document insights</li>
                  <li>Getting everything ready for chatbot + recommendations</li>
                </ul>

                <div className="p-4 rounded-2xl bg-white/5 border border-white/10">
                  <p className="text-sm font-semibold mb-1 text-white/80">
                    📌 Current Tip:
                  </p>
                  <p className="text-base text-white">{tips[tipIndex]}</p>
                </div>

                <p className="text-xs text-white/50">
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
                className="group flex items-center justify-between p-4 rounded-2xl border border-white/10 bg-gradient-to-br from-white/5 to-white/0 shadow-lg backdrop-blur-xl transition-all hover:-translate-y-[1px] hover:shadow-2xl"
              >
                <div>
                  <span className="block text-sm font-semibold text-white">
                    {file.name}
                  </span>
                  <span className="text-xs text-white/60">
                    {formatFileSize(file.sizeBytes)}
                  </span>
                </div>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeFile(file.id, file.url)}
                  aria-label="Remove file"
                  disabled={isProcessing}
                  className="rounded-xl border border-white/10 bg-white/5 text-white/80 hover:bg-red-500/10 hover:text-red-300"
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
                className="flex-1 rounded-2xl border border-white/10 bg-white/5 text-white shadow-lg hover:shadow-xl hover:bg-white/10 transition-all"
                variant="secondary"
                size="sm"
                disabled={isProcessing}
              >
                <Plus className="w-4 h-4 mr-2" /> Set New File
              </Button>

              <Button
                variant="outline"
                onClick={handleClear}
                className="flex-1 rounded-2xl border border-white/10 bg-white/5 text-white/80 shadow-lg hover:shadow-xl hover:bg-red-500/10 hover:text-red-300 transition-all"
                size="sm"
                disabled={isProcessing}
              >
                Clear All Files
              </Button>
            </div>

            <Button
              onClick={handleAnalyze}
              className="w-full rounded-2xl bg-gradient-to-r from-cyan-400 via-purple-500 to-fuchsia-500 text-white font-bold shadow-[0_0_35px_rgba(168,85,247,0.45)] hover:shadow-[0_0_55px_rgba(34,211,238,0.45)] transition-all hover:-translate-y-[1px]"
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
            className="w-full rounded-2xl border border-white/10 bg-white/5 text-white shadow-lg hover:bg-white/10 hover:shadow-xl transition-all"
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
