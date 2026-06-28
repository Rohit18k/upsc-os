"use client";

import { useState, useRef, useEffect } from "react";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/auth-store";
import {
  MessageSquare,
  Sparkles,
  Send,
  Loader2,
  BookOpen,
  HelpCircle,
  FileText,
  User,
} from "lucide-react";

interface Message {
  id: string;
  sender: "student" | "tutor";
  text: string;
  citation?: string;
  actions?: string[];
}

export default function AITutorPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "init",
      sender: "tutor",
      text: "Hello! I am your UPSC Socratic Tutor. I analyze your Digital Twin telemetry profile to guide your understanding.\n\nHow can I help you master your Polity or Economy concepts today?"
    }
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [activeMode, setActiveMode] = useState<string>("socratic");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (customText?: string) => {
    const textToSend = customText || inputMessage;
    if (!textToSend.trim()) return;

    // Append student message
    const studentMsg: Message = {
      id: `stud_${uuid()}`,
      sender: "student",
      text: textToSend
    };
    setMessages((prev) => [...prev, studentMsg]);
    setInputMessage("");
    setIsSending(true);

    try {
      // Call Socratic backend endpoint
      const res = await api.post<any>("/api/v1/tutor/chat", {
        message: textToSend,
        mode: activeMode
      });
      
      const replyData = res.data;
      
      const tutorMsg: Message = {
        id: `tutor_${uuid()}`,
        sender: "tutor",
        text: replyData.reply,
        citation: replyData.citation,
        actions: replyData.suggested_actions
      };
      
      setMessages((prev) => [...prev, tutorMsg]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          id: `tutor_err_${uuid()}`,
          sender: "tutor",
          text: "I apologize, but I encountered an error retrieving your digital twin data. Let's try again."
        }
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const handleQuickTrigger = (text: string, mode: string) => {
    setActiveMode(mode);
    handleSendMessage(text);
  };

  const uuid = () => Math.random().toString(36).substring(2, 9);

  return (
    <div className="h-[78vh] flex flex-col animate-in fade-in duration-300">
      {/* Header */}
      <div className="border-b border-zinc-800 pb-4 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-white flex items-center gap-3">
            <MessageSquare className="h-8 w-8 text-indigo-400" /> Socratic AI Tutor
          </h1>
          <p className="text-sm text-zinc-400">Context-grounded assistant guiding concepts, prerequisites, and evaluations.</p>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-8 min-h-0 pt-6">
        {/* Sidebar accelerators */}
        <div className="space-y-4 lg:col-span-1">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-4 space-y-4">
            <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500 flex items-center gap-2">
              <Sparkles className="h-3.5 w-3.5 text-indigo-400" /> Socratic Actions
            </h3>
            
            <div className="flex flex-col gap-2">
              <button
                onClick={() => handleQuickTrigger("Explain Monetary Policy Instruments", "socratic")}
                className="w-full text-left p-3 bg-zinc-950 hover:bg-zinc-900 border border-zinc-850 hover:border-zinc-700 rounded-lg text-xs text-zinc-300 transition"
              >
                Explain Monetary Policy (Socratic)
              </button>

              <button
                onClick={() => handleQuickTrigger("Evaluate my answer about Kesavananda Bharati Preamble ruling", "evaluate")}
                className="w-full text-left p-3 bg-zinc-950 hover:bg-zinc-900 border border-zinc-850 hover:border-zinc-700 rounded-lg text-xs text-zinc-300 transition"
              >
                Evaluate My Kesavananda Essay
              </button>

              <button
                onClick={() => handleQuickTrigger("Explain the Kesavananda Bharati Case significance", "explain")}
                className="w-full text-left p-3 bg-zinc-950 hover:bg-zinc-900 border border-zinc-850 hover:border-zinc-700 rounded-lg text-xs text-zinc-300 transition"
              >
                Explain Kesavananda Case Laws
              </button>
            </div>
          </div>
        </div>

        {/* Chat message pane */}
        <div className="lg:col-span-3 flex flex-col border border-zinc-800 rounded-xl bg-zinc-900/10 overflow-hidden">
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.map((msg) => {
              const isTutor = msg.sender === "tutor";
              return (
                <div key={msg.id} className={`flex gap-4 ${isTutor ? "" : "flex-row-reverse"}`}>
                  {/* User icon */}
                  <div className={`h-8 w-8 rounded-full border flex items-center justify-center text-xs font-semibold flex-shrink-0 ${
                    isTutor ? "bg-zinc-800 border-zinc-700 text-indigo-400" : "bg-indigo-500 border-indigo-400 text-white"
                  }`}>
                    {isTutor ? <Sparkles className="h-4 w-4" /> : <User className="h-4 w-4" />}
                  </div>

                  {/* Bubble */}
                  <div className="space-y-2 max-w-[80%]">
                    <div className={`rounded-xl p-4 text-sm leading-relaxed border ${
                      isTutor ? "bg-zinc-900/40 border-zinc-800 text-zinc-200" : "bg-zinc-950 border-zinc-850 text-white"
                    }`}>
                      <div className="whitespace-pre-wrap">{msg.text}</div>
                    </div>

                    {/* Citations */}
                    {isTutor && msg.citation && (
                      <div className="flex items-center gap-1.5 text-[10px] text-zinc-500 font-mono">
                        <BookOpen className="h-3 w-3 text-zinc-500" />
                        <span>Source Citation: {msg.citation}</span>
                      </div>
                    )}

                    {/* Suggested follow-up actions */}
                    {isTutor && msg.actions && msg.actions.length > 0 && (
                      <div className="flex flex-wrap gap-2 pt-1.5">
                        {msg.actions.map((act) => (
                          <button
                            key={act}
                            onClick={() => handleQuickTrigger(act, activeMode)}
                            className="text-[10px] font-semibold text-indigo-455 bg-indigo-950/20 border border-indigo-900/60 px-2.5 py-1 rounded hover:bg-indigo-950/40 transition"
                          >
                            {act}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
            <div ref={messagesEndRef} />
          </div>

          {/* Form input */}
          <div className="border-t border-zinc-800 p-4 bg-zinc-900/20 flex gap-2">
            <input
              type="text"
              placeholder="Ask the tutor a question about Preamble, RBI or Inflation..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSendMessage();
              }}
              className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm text-zinc-100 placeholder-zinc-650 focus:outline-none focus:border-zinc-700 transition"
              disabled={isSending}
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={isSending || !inputMessage.trim()}
              className="rounded-lg bg-zinc-100 hover:bg-zinc-200 text-zinc-950 p-3 transition disabled:opacity-50 flex items-center justify-center"
            >
              {isSending ? <Loader2 className="h-4 w-4 animate-spin text-zinc-950" /> : <Send className="h-4 w-4" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
