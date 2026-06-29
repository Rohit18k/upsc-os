"use client";

import { useEffect, useState, useRef } from "react";
import { api } from "@/services/api";
import {
  RefreshCw,
  Sparkles,
  Zap,
  Calendar,
  Layers,
  Clock,
  RotateCcw,
  Check,
  Brain,
  AlertTriangle,
  Award,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface Flashcard {
  id: string;
  nodeCode: string;
  front: string;
  back: string;
}

const DEMO_FLASHCARDS: Flashcard[] = [
  {
    id: "fc_1",
    nodeCode: "economy_rbi",
    front: "What is the primary role of the Reserve Bank of India (RBI) regarding inflation?",
    back: "The RBI manages monetary policy to maintain price stability while keeping growth in mind. The inflation target is set at 4% with an upper tolerance of 6% and lower tolerance of 2%."
  },
  {
    id: "fc_2",
    nodeCode: "economy_monetary_policy",
    front: "Explain the difference between Cash Reserve Ratio (CRR) and Statutory Liquidity Ratio (SLR).",
    back: "CRR requires banks to keep a percentage of their deposits as cash with the RBI. SLR requires banks to maintain a percentage of deposits in liquid assets (gold, government securities) with themselves."
  },
  {
    id: "fc_3",
    nodeCode: "polity_basics_preamble",
    front: "Is the Preamble of the Indian Constitution amendable? Cite the relevant supreme court ruling.",
    back: "Yes, the Preamble can be amended under Article 368, but its 'basic features' cannot be altered. This was ruled in the Kesavananda Bharati case (1973)."
  }
];

export default function RevisePage() {
  const [twin, setTwin] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [cardIndex, setCardIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [sessionActive, setSessionActive] = useState(false);
  const [ratingLoading, setRatingLoading] = useState(false);
  const [scoreAnimation, setScoreAnimation] = useState(false);

  // Recall timer
  const [recallSecondsLeft, setRecallSecondsLeft] = useState(30);
  const [timerRunning, setTimerRunning] = useState(false);
  const timerRef = useRef<any>(null);

  // Streak & stats
  const [streak, setStreak] = useState(5);

  const fetchTwinState = async () => {
    setIsLoading(true);
    try {
      const res = await api.get<any>("/api/v1/student/twin");
      setTwin(res.data);
    } catch (e) {
      // Ignored
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTwinState();
  }, []);

  // Recall timer controls
  useEffect(() => {
    if (timerRunning) {
      timerRef.current = setInterval(() => {
        setRecallSecondsLeft((prev) => {
          if (prev <= 1) {
            clearInterval(timerRef.current);
            setTimerRunning(false);
            setIsFlipped(true); // Auto-reveal on timeout
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [timerRunning]);

  const startSession = () => {
    setSessionActive(true);
    setRecallSecondsLeft(30);
    setTimerRunning(true);
  };

  const handleRatingSubmit = async (rating: number) => {
    const activeCard = DEMO_FLASHCARDS[cardIndex];
    setRatingLoading(true);
    setTimerRunning(false);
    try {
      await api.post("/api/v1/student/events", {
        event_type: "RevisionCompleted",
        payload: {
          node_code: activeCard.nodeCode,
          rating: rating,
          time_spent: 30 - recallSecondsLeft
        }
      });

      setScoreAnimation(true);
      setTimeout(() => setScoreAnimation(false), 800);

      // Transition to next card
      setIsFlipped(false);
      setTimeout(() => {
        setCardIndex((prev) => (prev + 1) % DEMO_FLASHCARDS.length);
        setRecallSecondsLeft(30);
        setTimerRunning(true);
      }, 300);

      // Increment streak
      if (rating >= 3) {
        setStreak((prev) => prev + 1);
      }

      await fetchTwinState();
    } catch (e) {
      alert("Failed to submit active recall rating.");
    } finally {
      setRatingLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-3">
        <RefreshCw className="h-8 w-8 text-indigo-400 animate-spin" />
        <p className="text-sm text-zinc-400 font-mono">Loading active recall queue...</p>
      </div>
    );
  }

  const activeCard = DEMO_FLASHCARDS[cardIndex];
  const weakConcepts = twin?.knowledge_state?.weak_concepts || [];
  const memoryStrength = twin?.memory_readiness ? (twin.memory_readiness * 100).toFixed(0) : "85";

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header section with page title */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-zinc-900 pb-5">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-3">
            <Zap className="h-5.5 w-5.5 text-indigo-400" /> Active Recall Studio
          </h1>
          <p className="text-xs text-zinc-400 font-mono">Spaced repetition engine grounded in digital twin memory decay rates.</p>
        </div>

        {/* Revision Streak indicator */}
        <div className="flex items-center gap-2 px-3 py-1.5 bg-indigo-950/40 border border-indigo-900 rounded-lg text-indigo-400">
          <Zap className="h-4 w-4 animate-pulse fill-indigo-500/20" />
          <span className="text-xs font-bold font-mono">{streak} Day Streak</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left two columns: Interactive Flashcards Workspace */}
        <div className="lg:col-span-2 space-y-6">
          {!sessionActive ? (
            <div className="rounded-xl border border-zinc-900 bg-zinc-900/10 p-10 text-center space-y-5 max-w-md mx-auto mt-10">
              <Brain className="h-12 w-12 text-indigo-400 mx-auto" />
              <div className="space-y-1">
                <h3 className="text-lg font-bold text-white">Anki Review Session</h3>
                <p className="text-xs text-zinc-500 font-mono">Review queue: {DEMO_FLASHCARDS.length} concepts waiting</p>
              </div>
              <p className="text-xs text-zinc-450 leading-relaxed">
                Test your knowledge retrieval using card flips and interval feedback to reset the Ebbinghaus memory decay curve.
              </p>
              <button
                onClick={startSession}
                className="w-full rounded-lg bg-zinc-100 hover:bg-zinc-200 text-zinc-950 py-3 text-xs font-semibold transition"
              >
                Start Active Recall
              </button>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Active Recall Timer and Queue Progress */}
              <div className="flex justify-between items-center text-xs font-mono text-zinc-400">
                <span className="flex items-center gap-2">
                  <Clock className="h-3.5 w-3.5 text-indigo-400" />
                  Recall Timer: <span className="font-bold text-white">{recallSecondsLeft}s</span>
                </span>
                <span>
                  Card {cardIndex + 1} of {DEMO_FLASHCARDS.length}
                </span>
              </div>

              {/* Flashcard container */}
              <div className="relative min-h-[300px] w-full">
                <motion.div
                  onClick={() => setIsFlipped(!isFlipped)}
                  className="w-full h-full min-h-[300px] rounded-xl border border-zinc-900 bg-zinc-900/20 p-8 flex flex-col justify-between cursor-pointer select-none relative overflow-hidden"
                  animate={{ rotateY: isFlipped ? 180 : 0 }}
                  transition={{ duration: 0.4 }}
                >
                  {/* Front Face */}
                  <div className={`space-y-4 ${isFlipped ? "opacity-0 pointer-events-none" : "opacity-100"}`}>
                    <span className="text-[9px] uppercase font-bold tracking-widest text-zinc-500 font-mono">Active Recall Question</span>
                    <p className="text-lg font-semibold text-white leading-relaxed">
                      {activeCard.front}
                    </p>
                    <p className="text-[10px] text-zinc-600 font-mono pt-4">Click to reveal answer</p>
                  </div>

                  {/* Back Face (flipped) */}
                  <div
                    className={`space-y-4 transform scale-x-[-1] absolute inset-0 p-8 flex flex-col justify-between ${
                      isFlipped ? "opacity-100" : "opacity-0 pointer-events-none"
                    }`}
                  >
                    <div className="space-y-2">
                      <span className="text-[9px] uppercase font-bold tracking-widest text-emerald-400 font-mono">Suggested Answer key</span>
                      <p className="text-sm text-zinc-300 leading-relaxed">
                        {activeCard.back}
                      </p>
                    </div>
                    <p className="text-[10px] text-zinc-600 font-mono">Click card to show question again</p>
                  </div>

                  {/* Overlay Animation on grading */}
                  <AnimatePresence>
                    {scoreAnimation && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0 }}
                        className="absolute inset-0 flex items-center justify-center bg-zinc-950/70"
                      >
                        <Check className="h-12 w-12 text-emerald-400" />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              </div>

              {/* Confidence interval grading buttons */}
              {isFlipped && (
                <div className="space-y-3">
                  <h4 className="text-xs uppercase font-bold tracking-wider text-zinc-500 font-mono text-center">Rate Your Retrieval Quality</h4>
                  <div className="grid grid-cols-4 gap-2">
                    <button
                      onClick={() => handleRatingSubmit(1)}
                      disabled={ratingLoading}
                      className="p-3.5 rounded-lg bg-red-950/30 border border-red-900/60 hover:bg-red-950/50 text-red-400 text-xs font-semibold transition disabled:opacity-50"
                    >
                      Again (1)
                    </button>
                    <button
                      onClick={() => handleRatingSubmit(2)}
                      disabled={ratingLoading}
                      className="p-3.5 rounded-lg bg-orange-950/30 border border-orange-900/60 hover:bg-orange-950/50 text-orange-400 text-xs font-semibold transition disabled:opacity-50"
                    >
                      Hard (2)
                    </button>
                    <button
                      onClick={() => handleRatingSubmit(3)}
                      disabled={ratingLoading}
                      className="p-3.5 rounded-lg bg-blue-950/30 border border-blue-900/60 hover:bg-blue-950/50 text-blue-400 text-xs font-semibold transition disabled:opacity-50"
                    >
                      Good (3)
                    </button>
                    <button
                      onClick={() => handleRatingSubmit(4)}
                      disabled={ratingLoading}
                      className="p-3.5 rounded-lg bg-emerald-950/30 border border-emerald-900/60 hover:bg-emerald-950/50 text-emerald-400 text-xs font-semibold transition disabled:opacity-50"
                    >
                      Easy (4)
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right column: Spaced Repetition Calendar & Memory Analytics */}
        <div className="space-y-6">
          {/* Calendar visualizer */}
          <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 space-y-4">
            <div className="flex justify-between items-center text-xs font-mono text-zinc-500">
              <span className="flex items-center gap-1.5">
                <Calendar className="h-4 w-4 text-indigo-400" /> Spaced Repetition Queue
              </span>
              <span>Next 5 days</span>
            </div>

            <div className="grid grid-cols-5 gap-2 pt-2 text-center">
              {[
                { day: "Today", count: DEMO_FLASHCARDS.length },
                { day: "Mon", count: 4 },
                { day: "Tue", count: 2 },
                { day: "Wed", count: 7 },
                { day: "Thu", count: 0 },
              ].map((item, idx) => (
                <div key={idx} className="p-2.5 rounded-lg bg-zinc-950 border border-zinc-900 space-y-1">
                  <span className="text-[9px] text-zinc-500 block font-mono">{item.day}</span>
                  <span className={`text-xs font-bold font-mono ${item.count > 0 ? "text-indigo-400" : "text-zinc-700"}`}>
                    {item.count}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Memory decay gauge */}
          <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 space-y-4">
            <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500 font-mono">Memory Strength</h3>
            
            <div className="flex justify-between items-center">
              <div className="space-y-0.5">
                <p className="text-3xl font-bold text-white font-mono">{memoryStrength}%</p>
                <p className="text-[10px] text-zinc-500 font-mono">Overall retention rating</p>
              </div>
              <div className="h-10 w-10 bg-indigo-950/20 text-indigo-400 rounded-full flex items-center justify-center border border-indigo-900">
                <Layers className="h-5 w-5" />
              </div>
            </div>
          </div>

          {/* Weak prerequisites warning */}
          <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 space-y-4">
            <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500 font-mono">Weak Review Priorities</h3>
            <div className="space-y-3">
              {weakConcepts.length > 0 ? (
                weakConcepts.map((item: any, idx: number) => (
                  <div key={idx} className="p-2.5 bg-zinc-950 border border-zinc-900 rounded-lg flex items-center justify-between text-xs">
                    <span className="text-zinc-300 font-mono">{item}</span>
                    <span className="text-[9px] uppercase font-bold tracking-wider text-red-400 bg-red-950/20 border border-red-900/50 px-1.5 py-0.5 rounded">
                      Critically Weak
                    </span>
                  </div>
                ))
              ) : (
                <div className="p-4 bg-zinc-950/40 rounded-lg border border-zinc-900 text-center space-y-2">
                  <Award className="h-7 w-7 text-indigo-400 mx-auto" />
                  <p className="text-xs text-zinc-500 font-mono leading-relaxed">
                    No critical concept memory leakages detected. Excellent work!
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
