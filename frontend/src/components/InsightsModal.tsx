import React, { useEffect } from "react";
import { Lightbulb, Search, Zap } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Card, CardContent } from "@/components/ui/card";
import { useInsights } from "../pages/InsightsContext";
import { useDocumentStore } from "@/store/useDocumentStore";
import { BACKEND_URL } from "@/config";
import { getSessionId } from "@/utils/session"; // ✅ ADD THIS

interface InsightsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function InsightsModal({ isOpen, onClose }: InsightsModalProps) {
  const { setInsights } = useInsights();
  const { selection, activeDocId, documents } = useDocumentStore();

  const activeDoc = activeDocId
    ? documents.find((doc) => doc.id === activeDocId)
    : null;

  const insightText = selection?.text || activeDoc?.name || "";

  const { data, isLoading } = useQuery({
    queryKey: ["insights", insightText],
    queryFn: async () => {
      const sessionId = getSessionId(); // ✅ GET SESSION ID

      const res = await fetch(
        `${BACKEND_URL}/insights?sessionId=${sessionId}`, // ✅ FIXED URL
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            selected_text: insightText, // ✅ backend expects this key
            top_k: 3,
          }),
        }
      );

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`Failed to fetch insights: ${res.status} - ${errText}`);
      }

      return res.json();
    },
    enabled: isOpen && !!insightText.trim(), // ✅ also avoid calling when empty
  });

  const insights = data?.insights;

  useEffect(() => {
    if (insights) {
      setInsights(insights);
    }
  }, [insights, setInsights]);

  const sections = [
    {
      title: "Main Points (1-Minute Recap)",
      icon: Lightbulb,
      accent: "from-pink-500 to-red-500",
      items: insights?.key_insights || [],
    },
    {
      title: "Quick Facts",
      icon: Search,
      accent: "from-cyan-500 to-blue-500",
      items: insights?.did_you_know || [],
    },
    {
      title: "Connections / Related Ideas",
      icon: Zap,
      accent: "from-purple-500 to-indigo-500",
      items: insights?.inspirations || [],
    },
  ];

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-5xl max-h-[85vh] overflow-hidden p-0 border-0 bg-transparent shadow-none">
        <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-zinc-950/70 backdrop-blur-xl shadow-2xl">
          <div className="absolute inset-0 opacity-40 pointer-events-none">
            <div className="absolute -top-40 -left-40 w-96 h-96 bg-purple-500/30 rounded-full blur-3xl" />
            <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-cyan-500/30 rounded-full blur-3xl" />
          </div>

          <div className="relative flex flex-col max-h-[85vh]">
            <DialogHeader className="px-6 py-5 border-b border-white/10 flex flex-row items-center justify-between">
              <DialogTitle className="flex items-center gap-3 text-lg font-semibold text-white">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center shadow-md">
                  <Lightbulb className="w-5 h-5 text-white" />
                </div>

                <div className="flex flex-col leading-tight">
                  <span className="text-white">1-Minute Recap</span>
                  <span className="text-xs text-white/50 font-normal">
                    Learn faster • Revise smarter • Save time
                  </span>
                </div>
              </DialogTitle>

              <div className="hidden md:block max-w-[340px] text-xs text-white/60 truncate text-right">
                {insightText ? `Recap For: ${insightText}` : "No text selected"}
              </div>
            </DialogHeader>

            <div className="flex-1 overflow-y-auto px-6 py-6">
              {isLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {sections.map((_, i) => (
                    <div
                      key={i}
                      className="rounded-2xl border border-white/10 bg-white/5 p-5 animate-pulse"
                    >
                      <div className="flex items-center gap-3 mb-4">
                        <div className="w-10 h-10 bg-white/10 rounded-xl" />
                        <div className="h-4 w-40 bg-white/10 rounded-md" />
                      </div>

                      <div className="space-y-3">
                        <div className="h-3 w-full bg-white/10 rounded-md" />
                        <div className="h-3 w-5/6 bg-white/10 rounded-md" />
                        <div className="h-3 w-4/6 bg-white/10 rounded-md" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {sections.map((section, index) => (
                    <Card
                      key={index}
                      className="group rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md hover:bg-white/10 transition-all duration-300"
                    >
                      <CardContent className="p-5">
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center gap-3">
                            <div
                              className={`w-10 h-10 rounded-xl bg-gradient-to-br ${section.accent} flex items-center justify-center shadow-md`}
                            >
                              <section.icon className="w-5 h-5 text-white" />
                            </div>

                            <div className="flex flex-col">
                              <span className="text-sm font-semibold text-white">
                                {section.title}
                              </span>
                              <span className="text-xs text-white/50">
                                {section.items.length} points
                              </span>
                            </div>
                          </div>

                          <div
                            className={`h-1.5 w-10 rounded-full bg-gradient-to-r ${section.accent} opacity-70 group-hover:opacity-100 transition`}
                          />
                        </div>

                        {section.items.length > 0 ? (
                          <ul className="space-y-3">
                            {section.items.map((item: string, idx: number) => (
                              <li
                                key={idx}
                                className="text-sm text-white/85 leading-relaxed rounded-xl border border-white/10 bg-black/20 p-3 hover:bg-black/30 transition"
                              >
                                ✅ {item}
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p className="text-sm text-white/40 italic">
                            No recap points found yet.
                          </p>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>

            <div className="px-6 py-4 border-t border-white/10 flex items-center justify-between">
              <p className="text-xs text-white/40">IntelliPDF • Student Mode 🎓</p>
              <p className="text-xs text-white/40">
                Tip: Highlight text for best recap
              </p>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
