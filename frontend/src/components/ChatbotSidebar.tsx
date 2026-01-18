import React, { useEffect, useRef, useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Send, Sparkles, FileText, Wand2 } from "lucide-react";
import { BACKEND_URL } from "@/config";
import { useDocumentStore } from "@/store/useDocumentStore";
import { getSessionId } from "@/utils/session";

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
    sender: "user" | "bot";
    text: string;
    images?: Image[];
  }

  const getImageUrl = (path: string) => {
    if (!path) return "";
    if (path.startsWith("http")) return path;
    if (!path.startsWith("/")) return `${BACKEND_URL}/${path}`;
    return `${BACKEND_URL}${path}`;
  };

  const { documents, activeDocId, setSelection } = useDocumentStore();

  const currentDocument = activeDocId
    ? documents.find((doc) => doc.id === activeDocId)
    : null;

  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "bot",
      text: `Hey buddy 👋🎓\nUpload + Analyze the PDF, then use **1-Minute Recap** or ask me anything ✅`,
    },
  ]);

  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleGenerateSummary = async () => {
    if (!currentDocument) {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "⚠️ Please upload and select a document first ✅" },
      ]);
      return;
    }

    if (isLoading) return;
    setIsLoading(true);

    setMessages((prev) => [
      ...prev,
      { sender: "bot", text: "✨ Creating your 1-minute recap... ⏳" },
    ]);

    try {
      const sessionId = getSessionId();

      const response = await fetch(
        `${BACKEND_URL}/summary?sessionId=${sessionId}`,
        {
          method: "GET",
        }
      );

      if (!response.ok) throw new Error(`HTTP error: ${response.status}`);

      const data = await response.json();

      setMessages((prev) => {
        const updated = [...prev];
        if (
          updated.length > 0 &&
          updated[updated.length - 1].text.includes("Creating your 1-minute recap")
        ) {
          updated.pop();
        }
        return [...updated, { sender: "bot", text: data.response }];
      });
    } catch (error) {
      console.error("Error fetching summary:", error);
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "Sorry buddy 😅 recap failed. Try again." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async (customText?: string) => {
    const finalText = (customText ?? input).trim();
    if (!finalText || isLoading) return;

    const userMessage: Message = { sender: "user", text: finalText };
    setMessages((prevMessages) => [...prevMessages, userMessage]);

    setInput("");
    setIsLoading(true);

    setSelection({ text: finalText, page: 1, rect: null });

    try {
      if (!currentDocument) {
        throw new Error("No document is currently loaded");
      }

      const sessionId = getSessionId();

      const response = await fetch(
        `${BACKEND_URL}/chatbot?sessionId=${sessionId}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: finalText }),
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `HTTP error! status: ${response.status}, message: ${errorText}`
        );
      }

      const data = await response.json();

      const botMessage: Message = {
        sender: "bot",
        text: data.response,
        images: data.relevant_images || [],
      };

      setMessages((prevMessages) => [...prevMessages, botMessage]);
    } catch (error: any) {
      console.error("Error sending message to chatbot:", error);

      let errorMessage = "Sorry buddy 😅 I couldn’t respond. Try again.";

      if (error.message.includes("No document is currently loaded")) {
        errorMessage = "📄 Please upload and Analyze a document first ✅";
      }

      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "bot", text: errorMessage },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const quickActions = [
    {
      label: "1-Minute Recap",
      icon: Sparkles,
      onClick: handleGenerateSummary,
    },
    {
      label: "Important Questions",
      icon: FileText,
      onClick: () =>
        handleSendMessage(
          "Give me 5 important exam questions from this PDF with answers."
        ),
    },
    {
      label: "Key Formulas",
      icon: Wand2,
      onClick: () =>
        handleSendMessage("Extract important formulas + explain each briefly."),
    },
  ];

  return (
    <div className="w-96 border-r border-border bg-background flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between gap-2">
          <div className="flex flex-col">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              🎓 Study Chat
            </h2>
            <p className="text-xs text-muted-foreground truncate max-w-[250px]">
              {currentDocument ? `📄 ${currentDocument.name}` : "No PDF selected"}
            </p>
          </div>

          <div className="text-xs px-2 py-1 rounded-full border border-border text-muted-foreground">
            {isLoading ? "Thinking..." : "Ready ✅"}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-3 flex flex-wrap gap-2">
          {quickActions.map((btn, idx) => (
            <Button
              key={idx}
              variant="secondary"
              size="sm"
              className="rounded-full text-xs"
              disabled={isLoading || !currentDocument}
              onClick={btn.onClick}
            >
              <btn.icon className="w-4 h-4 mr-2" />
              {btn.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, index) => {
          const isUser = msg.sender === "user";

          return (
            <div
              key={index}
              className={`flex ${isUser ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[78%] rounded-2xl px-4 py-3 shadow-sm border ${
                  isUser
                    ? "bg-primary text-primary-foreground border-primary/20"
                    : "bg-muted/60 text-foreground border-border"
                }`}
              >
                {!isUser && (
                  <p className="text-[11px] text-muted-foreground mb-1">
                    IntelliPDF Tutor 🤖
                  </p>
                )}

                <p className="text-sm leading-relaxed whitespace-pre-wrap">
                  {msg.text}
                </p>

                {msg.images && msg.images.length > 0 && (
                  <div className="mt-3 space-y-3">
                    {msg.images.map((image, imgIndex) => (
                      <div
                        key={imgIndex}
                        className="rounded-xl overflow-hidden border border-border bg-background"
                      >
                        <img
                          src={getImageUrl(image.path)}
                          alt={image.caption || `Image from page ${image.page}`}
                          className="w-full h-auto cursor-pointer hover:opacity-90 transition"
                          onClick={() =>
                            setSelection({ text: "", page: image.page, rect: null })
                          }
                        />

                        <div className="p-2">
                          <p className="text-xs text-muted-foreground">
                            📌 Page {image.page}{" "}
                            {image.caption ? `• ${image.caption}` : ""}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-2">
          <Input
            placeholder="Ask anything…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSendMessage();
            }}
            className="flex-1 rounded-full"
            disabled={isLoading}
          />

          <Button
            onClick={() => handleSendMessage()}
            size="icon"
            className="rounded-full"
            disabled={isLoading || !input.trim()}
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
