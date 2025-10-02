import React, {
  useEffect,
  useRef,
  useState,
  useImperativeHandle,
  forwardRef,
} from "react";
import { PdfDoc, DocumentSelection } from "@/types";
import { useToast } from "@/hooks/use-toast";

interface AdobeViewerProps {
  pdfDoc: PdfDoc;
  onSelectionChange?: (selection: DocumentSelection | null) => void;
}

export interface AdobeViewerRef {
  openPDF: (url: string, title?: string) => Promise<void>;
  goToPage: (page: number) => void;
  currentPdfUrl?: string;
}

declare global {
  interface Window {
    AdobeDC: any;
  }
}

export const AdobeViewer = forwardRef<AdobeViewerRef, AdobeViewerProps>(
  ({ pdfDoc, onSelectionChange }, ref) => {
    const viewerRef = useRef<HTMLDivElement>(null);
    const adobePreviewRef = useRef<any>(null);
    const adobeViewerInstanceRef = useRef<any>(null);
    const adobeViewRef = useRef<any>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [selectedText, setSelectedText] = useState<string>('');
    const { toast } = useToast();
    const mountedRef = useRef(true);

    useEffect(() => {
      mountedRef.current = true;
      return () => { mountedRef.current = false; };
    }, []);

    /** 🔹 Expose APIs to parent */
    useImperativeHandle(ref, () => ({
      goToPage: (page: number) => {
        if (!adobePreviewRef.current) {
          toast({
            title: "Viewer Not Ready",
            description: "Please wait for the PDF to load completely",
            variant: "destructive",
          });
          return;
        }

        adobePreviewRef.current.getAPIs().then((apis: any) => {
          apis.gotoLocation(page).catch(() => {
            toast({
              title: "Navigation Error",
              description: `Could not navigate to page ${page}`,
              variant: "destructive",
            });
          });
        });
      },

      openPDF: (url: string, name?: string) => {
        return new Promise<void>((resolve, reject) => {
          if (!adobeViewRef.current || !viewerRef.current) {
            return reject("Viewer not ready");
          }

          setIsLoading(true);
          const pdfName = name || url.split("/").pop() || "Document";

          const previewPromise = adobeViewRef.current.previewFile(
            {
              content: { location: { url } },
              metaData: { fileName: pdfName, id: pdfName },
            },
            {
              embedMode: "FULL_WINDOW",
              showAnnotationTools: true,
              showLeftHandPanel: true,
              showDownloadPDF: true,
              showPrintPDF: true,
              showBookmarks: true,
              enableFormFilling: true,
              enableAnnotationAPIs: true,
            }
          );

       previewPromise.then((previewInstance: any) => {
  adobePreviewRef.current = previewInstance;

  // PDF is ready
  previewInstance.registerCallback(
    window.AdobeDC.View.Enum.CallbackType.PREVIEW_READY,
    () => {
      setIsLoading(false);
      console.log("PDF preview ready:", pdfDoc.name);
    }
  );
}) // Added this closing brace and parenthesis
          .catch((err: any) => {
            console.error("❌ Error loading PDF:", err);
            setIsLoading(false);
            reject(err);
          });
        });
      },
    }));

    /** 🔹 Adobe Event Handler (Updated Text Selection) */
    const handleAdobeEvent = (event: any) => {
      if (!event) return;

      switch (event.type) {
       case 'TEXT_SELECTION': {
  const text = event.data?.text || event.data?.selection?.text || '';
  const pageNumber = event.data?.pageNumber || 1;
  const rect = event.data?.rect || { x: 0, y: 0, width: 0, height: 0 };

  if (text.trim()) {
    setSelectedText(text);
    
    // ✅ Add this line to log selected/highlighted text
    console.log("Selected Text:", text, "Page:", pageNumber, "Rect:", rect);

    onSelectionChange?.({
      text,
      page: pageNumber,
      rect,
    });
  }
  break;
}

        case 'ANNOTATION_ADDED':
        case 'ANNOTATION_UPDATED':
        case 'ANNOTATION_DELETED': {
          const annotation = event.data?.annotation;
          onSelectionChange?.({
            text: annotation?.bodyValue || '',
            page: annotation?.target?.location?.pageNumber,
            rect: annotation?.target?.rects?.[0] || null,
          });
          toast({
            title: `Annotation ${event.type.replace('ANNOTATION_', '')}`,
            description: "Annotation updated in document.",
          });
          break;
        }

        case 'PAGE_VIEW_CHANGED':
          console.log('Page changed to:', event.data?.pageNumber);
          break;

        case 'SEARCH_PERFORMED':
          console.log('Search term:', event.data?.searchTerm);
          break;

        case 'DOWNLOAD_INITIATED':
          toast({ title: "Download Started", description: "PDF download started." });
          break;

        case 'PRINT_INITIATED':
          toast({ title: "Print Started", description: "Print dialog opened." });
          break;

        default:
          break;
      }
    };

    /** 🔹 Load SDK + Init Viewer */
    useEffect(() => {
      let mounted = true;

      const loadAdobeSDK = () =>
        new Promise<void>((resolve) => {
          if (window.AdobeDC) return resolve();
          const script = document.createElement("script");
          script.src = "https://acrobatservices.adobe.com/view-sdk/viewer.js";
          script.onload = () => {
            console.log("Adobe SDK loaded");
            resolve();
          };
          document.body.appendChild(script);
        });

      const initViewer = async () => {
        if (!window.AdobeDC) {
          console.log('Adobe SDK not loaded, waiting...');
          let attempts = 0;
          const maxAttempts = 50;
          const checkAdobeSDK = setInterval(() => {
            attempts++;
            if (window.AdobeDC) {
              clearInterval(checkAdobeSDK);
              if (mountedRef.current) initViewer();
            } else if (attempts >= maxAttempts) {
              clearInterval(checkAdobeSDK);
              console.error('Adobe SDK failed to load after 5 seconds');
              if (mountedRef.current) {
                setIsLoading(false);
                toast({
                  title: "SDK Error",
                  description: "Adobe PDF SDK failed to load. Please refresh the page.",
                  variant: "destructive"
                });
              }
            }
          }, 100);
          return;
        }

        if (!viewerRef.current || !mountedRef.current) return;

        try {
          setIsLoading(true);
          await loadAdobeSDK();
          viewerRef.current.innerHTML = "";
        
          const adobeDCView = new window.AdobeDC.View({
            clientId: import.meta.env.VITE_ADOBE_EMBED_API_KEY,
            divId: viewerRef.current.id,
            locale: 'en-US'
          });

          const srcUrl = pdfDoc.url
            ? encodeURI(pdfDoc.url)
            : null; // Removed pdfDoc.blob usage

          if (!srcUrl) {
            console.error("No URL or blob available for PDF:", pdfDoc);
            setIsLoading(false);
            return;
            
          }

          const previewPromise = adobeDCView.previewFile(
            {
              content: { location: { url: srcUrl } },
              metaData: { fileName: pdfDoc.name, id: pdfDoc.id },
            },
            {
              embedMode: "FULL_WINDOW",
              showAnnotationTools: true,
              showLeftHandPanel: true,
              showBookmarks: true,
              showCommentsPanel: true,
              showSearchControl: true,
              showDownloadPDF: true,
              showPrintPDF: true,
              enableFormFilling: true,
              enableAnnotationAPIs: true,
              enableTextSelection: true,
              enableCopyText: true,
              annotationTools: {
                HIGHLIGHT: true, STRIKEOUT: true, UNDERLINE: true, SQUIGGLY: true,
                FREETEXT: true, STICKY_NOTE: true,
                INK: true, LINE: true, ARROW: true,
                RECTANGLE: true, ELLIPSE: true, POLYGON: true, POLYLINE: true,
                STAMP: true, ATTACHMENT: true
              }
            }
          );


          previewPromise.then((previewInstance: any) => {
            adobePreviewRef.current = previewInstance;
            previewInstance.registerCallback(
              window.AdobeDC.View.Enum.CallbackType.PREVIEW_READY,
              () => {
                setIsLoading(false);
                console.log("Default PDF preview ready:", pdfDoc.name);
              }
            );

            adobeViewRef.current.registerCallback(
              window.AdobeDC.View.Enum.CallbackType.EVENT_LISTENER,
              (event: any) => handleAdobeEvent(event)
            );
          });

          adobeViewRef.current = adobeDCView;
          setIsLoading(false);

          



          adobeDCView.registerCallback(
            window.AdobeDC.View.Enum.CallbackType.GET_USER_PROFILE_API,
            () =>
              Promise.resolve({
                code: window.AdobeDC.View.Enum.ApiResponseCode.SUCCESS,
                data: {
                  userProfile: { name: "PDF Intelligence User", firstName: "PDF", lastName: "User" },
                },
              })
          );

          adobeDCView.registerCallback(
            window.AdobeDC.View.Enum.CallbackType.SAVE_API,
            (metaData: any, content: any, options: any) => {
              const blob = new Blob([content], { type: 'application/pdf' });
              const url = URL.createObjectURL(blob);
              const a = window.document.createElement('a');
              a.href = url;
              a.download = `annotated_${metaData.fileName}`;
              a.click();
              URL.revokeObjectURL(url);

              return Promise.resolve({
                code: window.AdobeDC.View.Enum.ApiResponseCode.SUCCESS,
                data: { metaData }
              });
            }
          );

        } catch (error) {
          console.error("Error initializing Adobe viewer:", error);
          if (mounted) {
            setIsLoading(false);
            toast({
              title: "Viewer Error",
              description: "Failed to load PDF viewer. Please try again.",
              variant: "destructive",
            });
          }
        }
      };

      initViewer();

      return () => {
        mounted = false;
        adobeViewRef.current = null;
        adobeViewerInstanceRef.current = null;
        setSelectedText('');
        if (viewerRef.current) viewerRef.current.innerHTML = '';
      };
    }, [pdfDoc.id, pdfDoc.name, pdfDoc, onSelectionChange, toast]);

    const formatFileSize = (bytes: number) => {
      const mb = bytes / (1024 * 1024);
      return mb < 1 ? `${Math.round(mb * 1024)} KB` : `${mb.toFixed(2)} MB`;
    };

    return (
      <div className="w-full h-full flex flex-col">
        <div className="flex justify-between items-center p-4 border-b border-border bg-card">
          <h2 className="font-medium text-foreground truncate">{pdfDoc.name}</h2>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span>{formatFileSize(pdfDoc.sizeBytes)}</span>
            <span>{pdfDoc.pages} pages</span>
            <span className="text-success font-medium">Analysis Complete</span>
          </div>
        </div>
        <div className="flex-1 relative">
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-background">
              <div className="text-center">
                <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                <p className="text-muted-foreground">Loading PDF viewer...</p>
              </div>
            </div>
          )}
          <div
            ref={viewerRef}
            id={`adobe-viewer-${pdfDoc.id}`}
            className="w-full h-full"
            style={{ minHeight: "600px" }}
          />
        </div>
      </div>
    );
  }
);
