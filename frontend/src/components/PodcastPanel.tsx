import React, { useState, useRef } from 'react';
import { Mic, Play, Pause, SkipBack, SkipForward, Download } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useDocumentStore } from '@/store/useDocumentStore';
import { aiService } from '@/mocks/ai';
import { useToast } from '@/hooks/use-toast';
import { useContext } from "react";
import { useInsights } from "../pages/InsightsContext"; // ✅ import context

interface PodcastPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function PodcastPanel({ isOpen, onClose }: PodcastPanelProps) {
  const { activeDocId, documents, selection } = useDocumentStore();
  const { toast } = useToast();
  const { insights } = useInsights(); // ✅ use context
  
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [podcastContent, setPodcastContent] = useState<string>('');
  
  const audioRef = useRef<HTMLAudioElement>(null);
  
  const activeDoc = documents.find(doc => doc.id === activeDocId);
  // Prioritize selection, fall back to full document  
  const context = selection || activeDoc;

  // Generate content description based on what's being podcasted
  const getContentDescription = () => {
    if (selection) {
      return `Selected text from page ${selection.page}: "${selection.text.substring(0, 150)}..."`;
    }
    if (activeDoc) {
      return `Full document: "${activeDoc.name}" (${activeDoc.pages} pages)`;
    }
    return 'No content available';
  };

  const generatePodcastMutation = useMutation({
  mutationFn: async () => {
    const response = await fetch("http://localhost:8080/podcast", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
            selected_text: "The Course Camarguaise is a traditional bullfighting sport unique to the Camargue region. Unlike Spanish bullfighting, the objective is not to harm the bull but to remove ribbons and other decorations from its horns. The razeteurs, or participants, demonstrate agility and bravery as they dodge the bull's charges.",
        insights,
      }),
    });

    if (!response.ok) {
      throw new Error("Failed to generate podcast");
    }

    return response.json();
  },
  onSuccess: (data) => {
      setAudioUrl(`http://localhost:8080${data.audio_url}`); // directly from backend
    toast({
      title: "Podcast Generated",
      description: "Your podcast is ready!",
    });
  },
  onError: () => {
    toast({
      title: "Generation Failed",
      description: "Failed to generate podcast. Please try again.",
      variant: "destructive",
    });
  },
});

  const handleGeneratePodcast = () => {
    generatePodcastMutation.mutate();
  };

  const handlePlayPause = () => {
    if (!audioRef.current) return;
    
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
    }
  };

  const handleSeek = (event: React.MouseEvent<HTMLDivElement>) => {
    if (!audioRef.current) return;
    
    const rect = event.currentTarget.getBoundingClientRect();
    const percent = (event.clientX - rect.left) / rect.width;
    const seekTime = percent * duration;
    
    audioRef.current.currentTime = seekTime;
    setCurrentTime(seekTime);
  };

  const handleSkip = (seconds: number) => {
    if (!audioRef.current) return;
    
    const newTime = Math.max(0, Math.min(duration, currentTime + seconds));
    audioRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const handleDownload = async () => {
  if (audioUrl) {
    const response = await fetch(audioUrl);
    if (!response.ok) {
      console.error("Failed to fetch audio file");
      return;
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = `podcast-${activeDoc?.name || "document"}.mp3`;
    document.body.appendChild(a);
    a.click();
    a.remove();

    window.URL.revokeObjectURL(url);
  }
};

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-card rounded-xl shadow-xl max-w-md w-full mx-4">
        <Card className="border-0 shadow-none">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-semibold flex items-center gap-2">
                <Mic className="w-5 h-5 text-primary" />
                AI-Generated Podcast
              </CardTitle>
              <Button variant="ghost" size="sm" onClick={onClose}>
                ×
              </Button>
            </div>
          </CardHeader>
          
          <CardContent className="space-y-6">
            {/* Content Description */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg border border-blue-200">
              <h4 className="font-semibold text-blue-900 mb-2">Podcast Content:</h4>
              <p className="text-sm text-blue-800">{getContentDescription()}</p>
            </div>

            {!audioUrl ? (
              <div className="text-center">
                <Button
                  onClick={handleGeneratePodcast}
                  disabled={generatePodcastMutation.isPending || !context}
                  size="lg"
                  className="w-full bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600"
                >
                  {generatePodcastMutation.isPending ? (
                    <>
                      <div className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin mr-2" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Mic className="w-4 h-4 mr-2" />
                      Generate Podcast
                    </>
                  )}
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between text-sm text-muted-foreground mb-2">
                    <span>Document Podcast</span>
                    <span>{formatTime(duration)}</span>
                  </div>
                  
                  <div 
                    className="w-full bg-muted rounded-full h-2 cursor-pointer"
                    onClick={handleSeek}
                  >
                    <div 
                      className="bg-primary h-2 rounded-full transition-all"
                      style={{ width: `${(currentTime / duration) * 100}%` }}
                    />
                  </div>
                  
                  <div className="flex justify-between text-xs text-muted-foreground mt-1">
                    <span>{formatTime(currentTime)}</span>
                    <span>/ {formatTime(duration)}</span>
                  </div>
                </div>

                <div className="flex items-center justify-center gap-4">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleSkip(-10)}
                  >
                    <SkipBack className="w-4 h-4" />
                  </Button>
                  
                  <Button
                    variant="default"
                    size="sm"
                    onClick={handlePlayPause}
                    className="w-12 h-12 rounded-full"
                  >
                    {isPlaying ? (
                      <Pause className="w-5 h-5" />
                    ) : (
                      <Play className="w-5 h-5" />
                    )}
                  </Button>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleSkip(10)}
                  >
                    <SkipForward className="w-4 h-4" />
                  </Button>
                </div>

                <Button
                  variant="outline"
                  onClick={handleDownload}
                  className="w-full"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download Podcast Audio
                </Button>

               <audio
  ref={audioRef}
  src={audioUrl || undefined}
  onTimeUpdate={handleTimeUpdate}
  onLoadedMetadata={handleLoadedMetadata}
  onEnded={() => setIsPlaying(false)}
  className="hidden"
/>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}