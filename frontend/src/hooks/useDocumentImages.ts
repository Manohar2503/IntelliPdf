import { useState, useEffect } from 'react';

interface ImageInfo {
  page: number;
  filename: string;
  path: string;
  width: number;
  height: number;
  format: string;
  size_kb: number;
  ocr_text?: string;
  ai_labels?: Array<{
    label: string;
    confidence: number;
  }>;
  paths?: {
    original: string;
    thumbnail?: string;
    processed?: string;
  };
}

interface ImageStatistics {
  total_count: number;
  total_size_mb: number;
  by_format: Record<string, number>;
  size_distribution: {
    small: number;
    medium: number;
    large: number;
  };
}

export const useDocumentImages = (docId: string | null) => {
  const [images, setImages] = useState<ImageInfo[]>([]);
  const [statistics, setStatistics] = useState<ImageStatistics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const fetchImages = async () => {
      if (!docId) return;
      
      setLoading(true);
      setError(null);
      
      try {
        // Fetch images
        const imagesResponse = await fetch(`/api/images/${docId}`);
        if (!imagesResponse.ok) {
          throw new Error('Failed to fetch images');
        }
        const imagesData = await imagesResponse.json();
        setImages(imagesData);
        
        // Fetch statistics
        const statsResponse = await fetch(`/api/images/${docId}/statistics`);
        if (!statsResponse.ok) {
          throw new Error('Failed to fetch image statistics');
        }
        const statsData = await statsResponse.json();
        setStatistics(statsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };
    
    fetchImages();
  }, [docId]);
  
  return { images, statistics, loading, error };
};