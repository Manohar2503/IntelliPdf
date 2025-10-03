import React, { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Send } from 'lucide-react';
import { useDocumentStore } from '@/store/useDocumentStore'; // Import the store

export function ChatbotSidebar() {
  const [messages, setMessages] = useState<{ sender: string; text: string }[]>([]);
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
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Response data:', data);
        setMessages((prevMessages) => [...prevMessages, { sender: 'bot', text: data.response }]);
      } catch (error) {
        console.error('Error sending message to chatbot:', error);
        setMessages((prevMessages) => [
          ...prevMessages,
          { sender: 'bot', text: 'Sorry, I could not get a response. Please try again.' },
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
              {msg.text}
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
