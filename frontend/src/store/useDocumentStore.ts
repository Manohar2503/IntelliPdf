import { create } from 'zustand';
import { PdfDoc, DocumentSelection } from '@/types';

interface DocumentStore {
  // Library state
  documents: PdfDoc[];
  addDocument: (doc: PdfDoc) => void;
  removeDocument: (id: string) => void;
  updateDocument: (id: string, updates: Partial<PdfDoc>) => void;
  
  // Analysis se
selectedAnalysisFiles: PdfDoc[];
setSelectedAnalysisFiles: (files: PdfDoc[]) => void;
addSelectedAnalysisFile: (file: PdfDoc) => void;
removeSelectedAnalysisFile: (id: string) => void;
clearSelectedAnalysisFiles: () => void;

  
  analysisSet: string[];
  setAnalysisSet: (docIds: string[]) => void;
  
  addToAnalysisSet: (docId: string) => void;
  removeFromAnalysisSet: (docId: string) => void;
  clearAnalysisSet: () => void;
  
  // Active document in viewer
  activeDocId: string | null;
  setActiveDoc: (docId: string | null) => void;
  
  // Selection state
  selection: DocumentSelection | null;
  setSelection: (selection: DocumentSelection | null) => void;
  
  // Stats
  documentsToday: number;
  storageUsed: number;
  maxStorage: number;
}

export const useDocumentStore = create<DocumentStore>((set, get) => ({
  // Library state
  documents: [],
  addDocument: (doc) => set((state) => ({ 
    documents: [...state.documents, doc],
    documentsToday: state.documentsToday + 1,
    storageUsed: state.storageUsed + (doc.sizeBytes / (1024 * 1024))
  })),
  removeDocument: (id) => set((state) => {
    const doc = state.documents.find(d => d.id === id);
    return {
      documents: state.documents.filter(d => d.id !== id),
      analysisSet: state.analysisSet.filter(docId => docId !== id),
      activeDocId: state.activeDocId === id ? null : state.activeDocId,
      storageUsed: doc ? state.storageUsed - (doc.sizeBytes / (1024 * 1024)) : state.storageUsed
    };
  }),
  updateDocument: (id, updates) => set((state) => ({
    documents: state.documents.map(doc => 
      doc.id === id ? { ...doc, ...updates } : doc
    )
  })),
  selectedAnalysisFiles: [],
setSelectedAnalysisFiles: (files) => set({ selectedAnalysisFiles: files }),
addSelectedAnalysisFile: (file) => set((state) => ({
  selectedAnalysisFiles: [...state.selectedAnalysisFiles, file]
})),
removeSelectedAnalysisFile: (id) => set((state) => ({
  selectedAnalysisFiles: state.selectedAnalysisFiles.filter(f => f.id !== id)
})),
clearSelectedAnalysisFiles: () => set({ selectedAnalysisFiles: [] }),
  // Analysis set
  analysisSet: [],
  setAnalysisSet: (docIds) => set({ analysisSet: docIds }),
  addToAnalysisSet: (docId) => set((state) => ({
    analysisSet: [...state.analysisSet.filter(id => id !== docId), docId]
  })),
  removeFromAnalysisSet: (docId) => set((state) => ({
    analysisSet: state.analysisSet.filter(id => id !== docId)
  })),
  clearAnalysisSet: () => set({ analysisSet: [] }),
  
  // Active document
  activeDocId: null,
  setActiveDoc: (docId) => set({ activeDocId: docId }),
  
  // Selection state
  selection: null,
  setSelection: (selection) => set({ selection }),
  
  // Stats
  documentsToday: 0,
  storageUsed: 0,
  maxStorage: 35
}));