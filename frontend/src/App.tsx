import { useEffect } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Library from "./pages/Library";
import Viewer from "./pages/Viewer";
import SimpleViewer from "./pages/SimpleViewer";
import NotFound from "./pages/NotFound";
import { InsightsProvider } from "./pages/InsightsContext";
import { useDocumentStore } from "./store/useDocumentStore";
import { loadCurrentDocument } from "./utils/documentLoader";

const queryClient = new QueryClient();

const AppContent = () => {
  const { addDocument, setActiveDoc } = useDocumentStore();

  useEffect(() => {
    const fetchDocument = async () => {
      const doc = await loadCurrentDocument();
      if (doc) {
        addDocument(doc);
        setActiveDoc(doc.id);
      }
    };
    fetchDocument();
  }, [addDocument, setActiveDoc]);

  return (
    <InsightsProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/library" replace />} />
          <Route path="/library" element={<Library />} />
          <Route path="/viewer" element={<Viewer />} />
          <Route path="/simple-viewer" element={<SimpleViewer />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </InsightsProvider>
  );
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <AppContent />
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
