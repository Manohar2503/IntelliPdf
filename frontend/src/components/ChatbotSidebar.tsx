import React, { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Send } from 'lucide-react';
import { useDocumentStore } from '@/store/useDocumentStore'; // Import the store

export function ChatbotSidebar() {
  interface Image {
    filename: string;
    page: number;
    path: string;
    caption?: string;
    relevance_score: number;
    ocr_text?: string;
  }

  interface Message {
    sender: string;
    text: string;
    images?: Image[];
  }

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { documents, activeDocId, setSelection } = useDocumentStore(); // Get documents, activeDocId, and setSelection from the store

  // Derive currentDocument from documents and activeDocId
  const currentDocument = activeDocId ? documents.find(doc => doc.id === activeDocId) : null;

  useEffect(() => {
    // Get initial summary when a document is loaded
    const fetchInitialSummary = async () => {
      if (currentDocument) {
        setIsLoading(true);
        try {
          const response = await fetch("http://localhost:8080/summary", {
            method: "GET"
          });

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const data = await response.json();
          setMessages([{ sender: 'bot', text: data.response }]);
        } catch (error) {
          console.error('Error fetching summary:', error);
          setMessages([{ 
            sender: 'bot', 
            text: 'Hello! The document is loaded. How can I help you with it?' 
          }]);
        } finally {
          setIsLoading(false);
        }
      }
    };

    fetchInitialSummary();
  }, [currentDocument]);

  const handleSendMessage = async () => {
    if (input.trim() && !isLoading) {
      const userMessage = { sender: 'user', text: input };
      setMessages((prevMessages) => [...prevMessages, userMessage]);
      setInput('');
      setIsLoading(true);
      setSelection({ text: userMessage.text, page: 1, rect: null }); // Set the chatbot query as selection

      // We don't need to check for document content as backend reads from current_doc.json

      try {
        console.log('Sending query to chatbot:', userMessage.text);
        if (!currentDocument) {
          throw new Error('No document is currently loaded');
        }
        
        const response = await fetch("http://localhost:8080/chatbot", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            query: userMessage.text,
          }),
        });
        console.log('Response status:', response.status);
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error('Error response:', errorText);
          throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
        }

        const data = await response.json();
        console.log('Response data:', data);
        console.log('Images in response:', data.relevant_images);
        const botMessage = {
          sender: 'bot',
          text: data.response,
          images: data.relevant_images || []
        };
        console.log('Bot message with images:', botMessage);
        setMessages((prevMessages) => [...prevMessages, botMessage]);
      } catch (error: any) {
        console.error('Error sending message to chatbot:', error);
        let errorMessage = 'Sorry, I could not get a response. Please try again.';
        if (error.message.includes('No document is currently loaded')) {
          errorMessage = 'Please upload and select a document first.';
        }
        setMessages((prevMessages) => [
          ...prevMessages,
          { sender: 'bot', text: errorMessage },
        ]);
      } finally {
        setIsLoading(false);
      }
    }
  };

  return (
    <div className="w-96 border-r border-border bg-card flex flex-col h-full">
      <div className="p-4 border-b border-border">
        <h2 className="text-lg font-semibold">PDF Chatbot</h2>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex ${
              msg.sender === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[70%] p-3 rounded-lg ${
                msg.sender === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground'
              }`}
            >
              <p>{msg.text}</p>
              {msg.images && msg.images.length > 0 && (
                <div className="mt-2 grid gap-2">
                  {msg.images.map((image, imgIndex) => (
                    <div key={imgIndex} className="relative">
                      <img
                        src={image.path.startsWith('http') ? image.path : `http://localhost:8080${image.path}`}
                        alt={image.caption || `Image from page ${image.page}`}
                        className="rounded-md max-w-full h-auto cursor-pointer hover:opacity-90"
                        onClick={() => {
                          if (setSelection) {
                            setSelection({ text: '', page: image.page, rect: null });
                          }
                        }}
                      />
                      {image.caption && (
                        <p className="text-sm text-muted-foreground mt-1">{image.caption}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      <div className="p-4 border-t border-border flex items-center gap-2">
        <Input
          placeholder="Ask a question about the PDF..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              handleSendMessage();
            }
          }}
          className="flex-1"
          disabled={isLoading}
        />
        <Button onClick={handleSendMessage} size="icon" disabled={isLoading}>
          {isLoading ? '...' : <Send className="w-4 h-4" />}
        </Button>
      </div>
    </div>
  );
}
