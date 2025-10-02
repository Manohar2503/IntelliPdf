export interface PdfDoc {
  id: string;
  name: string;
  filePath: string;
  sizeBytes: number;
  uploadedAt: string;
  title?: string;
  pages?: number; // Add pages property
  sections: any[];
  content?: string; // Add content property
  summary?: string;
  url?: string; // Add url property for direct access
}
export interface DocumentSelection {
  text: string;
  page: number;
  rect?: DOMRect;
}

export interface Recommendation {
  id: string;
  title: string;
  description: string;
  page: number;
  match: number;
  pdf_url: string;
}

export interface Insights {
  keyInsights: string[];
  didYouKnow: string[];
  contradictions: string[];
  connections: string[];
}

export interface PodcastAudio {
  blob: Blob;
  duration: number;
  url: string;
}
