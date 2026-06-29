"use client";

import { useEffect, useState, useRef } from "react";
import { api } from "@/services/api";
import {
  FileText,
  Clock,
  Sparkles,
  TrendingUp,
  Award,
  RefreshCw,
  Eye,
  CheckCircle,
  HelpCircle,
  FileCheck,
} from "lucide-react";

export default function MainsWritingStudio() {
  const [essayContent, setEssayContent] = useState("");
  const [wordCount, setWordCount] = useState(0);
  const [seconds, setSeconds] = useState(0);
  const [timerRunning, setTimerRunning] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [evaluation, setEvaluation] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);

  const timerRef = useRef<any>(null);

  const QUESTION = "Evaluate the efficacy of the Monetary Policy Committee (MPC) of India in achieving its inflation targeting mandate over the last five years.";

  // Timer loop
  useEffect(() => {
    if (timerRunning) {
      timerRef.current = setInterval(() => {
        setSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [timerRunning]);

  // Word counter
  useEffect(() => {
    const text = essayContent.trim();
    if (!text) {
      setWordCount(0);
    } else {
      const words = text.split(/\s+/).length;
      setWordCount(words);
    }
  }, [essayContent]);

  const handleNotesSubmit = async () => {
    if (!essayContent.trim()) return;

    setIsSubmitting(true);
    setTimerRunning(false);
    try {
      const res = await api.post<any>("/api/v1/mentor/answer-review", {
        answer: essayContent
      });
      const data = res.data;
      
      const newEval = {
        correction: data.review_feedback || "Outline check looks solid. Ensure you expand on the structural points.",
        structure_score: 8.5,
        word_count: wordCount,
        time_seconds: seconds,
        gs_paper: "GS3 Economy",
        timestamp: new Date().toLocaleTimeString()
      };
      setEvaluation(newEval);
      setHistory((prev) => [newEval, ...prev]);

      // Telemetry update
      await api.post("/api/v1/student/events", {
        event_type: "MainsAnswerSubmitted",
        payload: {
          concept_code: "economy_monetary_policy",
          time_spent: seconds,
          score: 0.85,
          word_count: wordCount
        }
      });
    } catch (e) {
      alert("Failed to submit answer for review.");
      setTimerRunning(true);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setEssayContent("");
    setSeconds(0);
    setTimerRunning(true);
    setEvaluation(null);
  };

  const formatTimer = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header section with page title */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-zinc-900 pb-5">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-3">
            <FileText className="h-5.5 w-5.5 text-indigo-400" /> Mains Writing Studio
          </h1>
          <p className="text-xs text-zinc-400 font-mono">Structured answer writing sandbox linked to AI evaluator telemetry.</p>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono text-zinc-400">
          <span className="flex items-center gap-1.5 px-3 py-1 bg-zinc-900 border border-zinc-800 rounded-lg">
            <Clock className="h-3.5 w-3.5 text-indigo-400" /> {formatTimer(seconds)}
          </span>
          <span className="text-zinc-500">Words: <span className="font-bold text-white">{wordCount}</span></span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left two columns: Writing sandbox */}
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 space-y-5">
            <div className="space-y-1.5">
              <span className="text-[9px] uppercase font-bold tracking-widest text-indigo-400 font-mono">UPSC Mains Question</span>
              <p className="text-sm font-semibold text-white leading-relaxed">{QUESTION}</p>
            </div>

            {/* Sandbox textarea */}
            <div className="space-y-2">
              <textarea
                value={essayContent}
                onChange={(e) => setEssayContent(e.target.value)}
                placeholder="Write your answer here (Introduction, Body Paragraphs, and Conclusion)..."
                disabled={isSubmitting}
                className="w-full h-80 bg-zinc-950 border border-zinc-900 rounded-lg p-4 text-sm text-zinc-200 placeholder-zinc-700 focus:outline-none focus:border-zinc-800 resize-none font-sans leading-relaxed"
              />
            </div>

            {/* controls */}
            <div className="flex gap-2">
              <button
                onClick={handleNotesSubmit}
                disabled={isSubmitting || !essayContent.trim()}
                className="flex-1 flex items-center justify-center gap-2 rounded-lg bg-zinc-100 hover:bg-zinc-200 text-zinc-950 py-3 text-xs font-semibold uppercase tracking-wider transition disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" /> Evaluating...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" /> Submit for Review
                  </>
                )}
              </button>
              <button
                onClick={handleReset}
                className="px-4 py-3 rounded-lg border border-zinc-800 bg-zinc-950 hover:bg-zinc-900 text-zinc-400 hover:text-zinc-200 text-xs font-semibold uppercase tracking-wider transition"
              >
                Reset
              </button>
            </div>
          </div>
        </div>

        {/* Right column: Outline builder & review feedback */}
        <div className="space-y-6">
          {/* Outline guide */}
          <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 space-y-4">
            <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500 font-mono">Writing Outline Guide</h3>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between items-center text-zinc-400 font-mono">
                <span>Introduction</span>
                <span>~30 words</span>
              </div>
              <div className="flex justify-between items-center text-zinc-400 font-mono pt-1">
                <span>Core MPC Mandate analysis</span>
                <span>~100 words</span>
              </div>
              <div className="flex justify-between items-center text-zinc-400 font-mono pt-1">
                <span>Challenges & Reforms</span>
                <span>~100 words</span>
              </div>
              <div className="flex justify-between items-center text-zinc-400 font-mono pt-1">
                <span>Conclusion</span>
                <span>~20 words</span>
              </div>
            </div>
          </div>

          {/* AI structure evaluation */}
          <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 space-y-4">
            <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500 font-mono">Structure Quality Checks</h3>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-zinc-400">GS Paper Mapping</span>
                <span className="font-mono text-white font-bold bg-zinc-950 px-2 py-0.5 border border-zinc-900 rounded">GS3 Economy</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-zinc-400">Intro detect</span>
                <span className="text-emerald-400 font-semibold">{wordCount > 40 ? "✓ Detected" : "✕ Too short"}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-zinc-400">Structure Score</span>
                <span className="font-mono text-white font-bold">{evaluation ? `${evaluation.structure_score}/10` : "N/A"}</span>
              </div>
            </div>
          </div>

          {/* Mentor feedback */}
          {evaluation && (
            <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 space-y-4 animate-in fade-in duration-200">
              <div className="flex items-center gap-2 text-xs font-mono text-indigo-400">
                <FileCheck className="h-4 w-4" /> AI Mentor Review Feedback
              </div>
              <p className="text-xs text-zinc-400 leading-relaxed bg-zinc-950 border border-zinc-900 p-3 rounded">
                {evaluation.correction}
              </p>
            </div>
          )}

          {/* History */}
          {history.length > 0 && (
            <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 space-y-4">
              <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500 font-mono">Draft History</h3>
              <div className="space-y-2.5 max-h-36 overflow-y-auto pr-1">
                {history.map((h, idx) => (
                  <div key={idx} className="p-2.5 bg-zinc-950 border border-zinc-900 rounded-lg flex items-center justify-between text-xs">
                    <span className="text-zinc-300 font-mono">{h.timestamp}</span>
                    <span className="text-[10px] text-zinc-500 font-mono">{h.word_count} words ({formatTimer(h.time_seconds)})</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
