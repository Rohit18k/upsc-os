"use client";

import { useState, useRef, useEffect } from "react";
import { api } from "@/services/api";
import {
  MessageSquare,
  Sparkles,
  Send,
  Loader2,
  BookOpen,
  HelpCircle,
  FileText,
  User,
  Mic,
  MicOff,
  Compass,
  Bookmark,
  Pin,
  CheckCircle,
} from "lucide-react";

interface Message {
  id: string;
  sender: "student" | "tutor";
  text: string;
  citation?: string;
  actions?: string[];
}

export default function AIMentorPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "init",
      sender: "tutor",
      text: "Hello! I am your personal UPSC Socratic Mentor. I have analyzed your study telemetry and digital twin graph.\n\nHow can I help you master your Polity or Economy concepts today?"
    }
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [isSending, setIsSending] = useState(false);
  
  // Modes: "socratic", "examiner", "answer-review", "gap-simulation"
  const [activeMode, setActiveMode] = useState<string>("socratic");
  
  // Voice recording skeleton state
  const [isRecording, setIsRecording] = useState(false);

  // Pinned chats / conversation history mock list
  const [pinnedChats, setPinnedChats] = useState<Array<{ id: string; title: string; active: boolean }>>([
    { id: "c_1", title: "Preamble basic structure doctrine", active: true },
    { id: "c_2", title: "RBI credit control policies", active: false },
    { id: "c_3", title: "Article 21 & privacy right boundaries", active: false }
  ]);

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
        text: replyData.reply || "Let's break down this concept step-by-step. What subject area is this related to?",
        citation: replyData.citation || "Polity Basics, Chapter 2",
        actions: replyData.suggested_actions
      };
      
      setMessages((prev) => [...prev, tutorMsg]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          id: `tutor_err_${uuid()}`,
          sender: "tutor",
          text: "I apologize, but I encountered an error communicating with the reasoning server. Let's try rephrasing the question."
        }
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const handleToggleVoice = () => {
    setIsRecording(!isRecording);
    if (!isRecording) {
      // Simulate speech detection input after 3s
      setTimeout(() => {
        setInputMessage("Explain the Basic Structure Doctrine in relation to Kesavananda Bharati case");
        setIsRecording(false);
      }, 3000);
    }
  };

  const uuid = () => Math.random().toString(36).substring(2, 9);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[78vh]">
      {/* Sidebar Chat list */}
      <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-4 flex flex-col justify-between space-y-4">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500 font-mono">Pinned Sessions</h3>
            <Pin className="h-3.5 w-3.5 text-zinc-500" />
          </div>

          <div className="space-y-2">
            {pinnedChats.map((c) => (
              <button
                key={c.id}
                onClick={() => {
                  setPinnedChats(pinnedChats.map((p) => ({ ...p, active: p.id === c.id })));
                  if (c.id === "c_1") {
                    setMessages([
                      { id: "init", sender: "tutor", text: "Welcome back! Let's resume our analysis of the Preamble basic structure doctrine." }
                    ]);
                  } else {
                    setMessages([
                      { id: "init", sender: "tutor", text: `Ready to master: ${c.title}? Ask me any doubts.` }
                    ]);
                  }
                }}
                className={`w-full text-left p-2.5 rounded-lg text-xs font-medium truncate transition ${
                  c.active
                    ? "bg-zinc-900 text-white border border-zinc-800"
                    : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/30"
                }`}
              >
                {c.title}
              </button>
            ))}
          </div>
        </div>

        {/* Shortcuts widgets */}
        <div className="space-y-3 border-t border-zinc-900 pt-4">
          <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider font-mono">Mission Shortcuts</h4>
          <button
            onClick={() => handleSendMessage("Evaluate my weak subjects profile")}
            className="w-full text-left p-2 bg-zinc-950 border border-zinc-900 rounded-lg text-[10px] text-zinc-400 hover:text-white transition"
          >
            Review Weak Concept telemetry
          </button>
          <button
            onClick={() => handleSendMessage("Create a mock evaluation for Polity Basics")}
            className="w-full text-left p-2 bg-zinc-950 border border-zinc-900 rounded-lg text-[10px] text-zinc-400 hover:text-white transition"
          >
            Generate Socratic evaluation
          </button>
        </div>
      </div>

      {/* Main chat interface */}
      <div className="lg:col-span-3 rounded-xl border border-zinc-900 bg-zinc-900/20 flex flex-col justify-between overflow-hidden">
        {/* Chat modes controller header */}
        <div className="flex border-b border-zinc-900 bg-zinc-900/40 p-2 gap-1.5 overflow-x-auto">
          {[
            { id: "socratic", label: "Socratic Coach" },
            { id: "examiner", label: "Examiner Mode" },
            { id: "answer-review", label: "Answer Review" },
            { id: "gap-simulation", label: "Gap Analysis" },
          ].map((mode) => (
            <button
              key={mode.id}
              onClick={() => setActiveMode(mode.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition ${
                activeMode === mode.id
                  ? "bg-zinc-800 text-white border border-zinc-700"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              {mode.label}
            </button>
          ))}
        </div>

        {/* Messages scroll zone */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 max-w-[85%] ${
                msg.sender === "student" ? "ml-auto flex-row-reverse" : "mr-auto"
              }`}
            >
              {/* Profile icon */}
              <div className={`h-8 w-8 rounded-full flex items-center justify-center text-xs font-bold border flex-shrink-0 ${
                msg.sender === "student"
                  ? "bg-zinc-800 border-zinc-700 text-indigo-400"
                  : "bg-indigo-950/20 border-indigo-900 text-indigo-400"
              }`}>
                {msg.sender === "student" ? "S" : "M"}
              </div>

              {/* Message content */}
              <div className="space-y-2">
                <div className={`rounded-xl px-4 py-3 text-xs leading-relaxed ${
                  msg.sender === "student"
                    ? "bg-zinc-900 text-zinc-100 border border-zinc-850"
                    : "bg-zinc-950/40 text-zinc-300 border border-zinc-900"
                }`}>
                  <p className="whitespace-pre-line">{msg.text}</p>
                </div>

                {/* Citation cards */}
                {msg.citation && (
                  <div className="flex items-center gap-1.5 text-[9px] text-zinc-500 font-mono pl-1">
                    <BookOpen className="h-3 w-3" /> Citation: <span className="text-zinc-400">{msg.citation}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
          {isSending && (
            <div className="flex gap-3 max-w-[85%] mr-auto items-center">
              <div className="h-8 w-8 rounded-full bg-indigo-950/20 border border-indigo-900 text-indigo-400 flex items-center justify-center">
                <Loader2 className="h-4.5 w-4.5 animate-spin" />
              </div>
              <p className="text-[10px] text-zinc-500 font-mono animate-pulse">Mentor is formulating thoughts...</p>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input panel with voice mic trigger */}
        <div className="border-t border-zinc-900 p-3 bg-zinc-900/20">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center gap-2"
          >
            {/* Voice microphone trigger button */}
            <button
              type="button"
              onClick={handleToggleVoice}
              className={`p-2.5 rounded-lg border border-zinc-900 transition flex-shrink-0 ${
                isRecording
                  ? "bg-red-950/40 border-red-900 text-red-400 animate-pulse"
                  : "bg-zinc-950 text-zinc-500 hover:text-zinc-300"
              }`}
              title="Voice Ready Mic"
            >
              {isRecording ? <Mic className="h-4.5 w-4.5" /> : <MicOff className="h-4.5 w-4.5" />}
            </button>

            <input
              type="text"
              placeholder={isRecording ? "Listening to your voice input..." : "Ask your mentor or type command shortcuts..."}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              disabled={isSending || isRecording}
              className="flex-1 bg-zinc-950 border border-zinc-900 rounded-lg px-3 py-2.5 text-xs text-zinc-200 placeholder-zinc-700 focus:outline-none focus:border-zinc-800"
            />
            <button
              type="submit"
              disabled={isSending || !inputMessage.trim()}
              className="p-2.5 rounded-lg bg-zinc-100 hover:bg-zinc-200 text-zinc-950 disabled:opacity-50 flex-shrink-0"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
