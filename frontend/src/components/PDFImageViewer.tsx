import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

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

interface PDFImagesProps {
  docId: string;
  images: ImageInfo[];
}

const PDFImageViewer: React.FC<PDFImagesProps> = ({ docId, images }) => {
  const [selectedImage, setSelectedImage] = useState<ImageInfo | null>(null);
  
  const renderAILabels = (labels: Array<{ label: string; confidence: number }>) => {
    return labels.map((label, index) => (
      <Badge
        key={index}
        variant="secondary"
        className="mr-2 mb-2"
        title={`Confidence: ${(label.confidence * 100).toFixed(1)}%`}
      >
        {label.label}
      </Badge>
    ));
  };
  
  const renderImageDialog = (image: ImageInfo) => (
    <Dialog>
      <DialogTrigger asChild>
        <Card className="cursor-pointer hover:shadow-lg transition-shadow">
          <CardHeader>
            <CardTitle>Page {image.page}</CardTitle>
            <CardDescription>
              {image.width}x{image.height} {image.format.toUpperCase()}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <img
              src={image.paths?.thumbnail || image.path}
              alt={`Page ${image.page}`}
              className="w-full h-48 object-contain"
            />
          </CardContent>
          <CardFooter className="flex flex-wrap gap-2">
            {image.ai_labels && renderAILabels(image.ai_labels)}
          </CardFooter>
        </Card>
      </DialogTrigger>
      
      <DialogContent className="max-w-4xl">
        <DialogHeader>
          <DialogTitle>Image from Page {image.page}</DialogTitle>
          <DialogDescription>
            {image.width}x{image.height} {image.format.toUpperCase()} ({image.size_kb}KB)
          </DialogDescription>
        </DialogHeader>
        
        <Tabs defaultValue="original">
          <TabsList>
            <TabsTrigger value="original">Original</TabsTrigger>
            <TabsTrigger value="processed">Enhanced</TabsTrigger>
            {image.ocr_text && <TabsTrigger value="ocr">OCR Text</TabsTrigger>}
          </TabsList>
          
          <TabsContent value="original">
            <img
              src={image.paths?.original || image.path}
              alt={`Page ${image.page} Original`}
              className="w-full object-contain"
            />
          </TabsContent>
          
          <TabsContent value="processed">
            <img
              src={image.paths?.processed}
              alt={`Page ${image.page} Enhanced`}
              className="w-full object-contain"
            />
          </TabsContent>
          
          {image.ocr_text && (
            <TabsContent value="ocr">
              <div className="p-4 bg-muted rounded-lg">
                <pre className="whitespace-pre-wrap">{image.ocr_text}</pre>
              </div>
            </TabsContent>
          )}
        </Tabs>
        
        {image.ai_labels && (
          <div className="mt-4">
            <h4 className="text-sm font-semibold mb-2">AI Analysis</h4>
            <div className="flex flex-wrap gap-2">
              {renderAILabels(image.ai_labels)}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
      {images.map((image, index) => (
        <div key={index}>
          {renderImageDialog(image)}
        </div>
      ))}
    </div>
  );
};

export default PDFImageViewer;