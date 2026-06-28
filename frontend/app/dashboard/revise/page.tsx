"use client";

import { useEffect, useState } from "react";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/auth-store";
import {
  RefreshCw,
  Sparkles,
  Award,
  Zap,
  TrendingDown,
  Calendar,
  Layers,
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

  const handleRatingSubmit = async (rating: number) => {
    const activeCard = DEMO_FLASHCARDS[cardIndex];
    setRatingLoading(true);
    try {
      // Log event
      await api.post("/api/v1/student/events", {
        event_type: "RevisionCompleted",
        payload: {
          node_code: activeCard.nodeCode,
          rating: rating,
          time_spent: 45.0
        }
      });

      // Show success animation
      setScoreAnimation(true);
      setTimeout(() => setScoreAnimation(false), 800);

      // Move to next card
      setIsFlipped(false);
      setTimeout(() => {
        setCardIndex((prev) => (prev + 1) % DEMO_FLASHCARDS.length);
      }, 200);

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
        <p className="text-sm text-zinc-400">Syncing Memory Database...</p>
      </div>
    );
  }

  const memoryReadiness = twin?.behaviour_state?.memory_readiness || 0.72;
  const activeItemsCount = Object.keys(twin?.memory_state?.items || {}).length || 2;

  // Generate Forgetting Curve SVG Path: R = e^(-t/S)
  const curveWidth = 400;
  const curveHeight = 120;
  let points = [];
  for (let x = 0; x <= curveWidth; x += 10) {
    const t = (x / curveWidth) * 30; // 30 days
    // half-life stability of roughly 7 days
    const R = Math.pow(2, -t / 7);
    const y = curveHeight - R * curveHeight;
    points.push(`${x},${y}`);
  }
  const svgPath = `M ${points.join(" L ")}`;

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-white flex items-center gap-3">
            <RefreshCw className="h-8 w-8 text-indigo-400" /> Active Recall & Spaced Repetition
          </h1>
          <p className="text-sm text-zinc-400">Counteract the forgetting curve using SM-2 recall algorithms.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Memory Stats Column */}
        <div className="space-y-6">
          {/* Memory strength gauge */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 space-y-6">
            <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500">Memory Strength Summary</h3>
            <div className="flex items-center gap-6">
              <div className="relative h-20 w-20 flex-shrink-0">
                <svg className="h-full w-full" viewBox="0 0 36 36">
                  <path
                    className="stroke-zinc-800"
                    strokeWidth="3.5"
                    fill="none"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                  <path
                    className="stroke-indigo-400 transition-all duration-500"
                    strokeDasharray={`${memoryReadiness * 100}, 100`}
                    strokeWidth="3.5"
                    strokeLinecap="round"
                    fill="none"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center text-sm font-semibold text-white font-mono">
                  {(memoryReadiness * 100).toFixed(0)}%
                </div>
              </div>

              <div>
                <p className="text-sm font-semibold text-white">Retention Capacity</p>
                <p className="text-xs text-zinc-400 mt-1">
                  Active retention score derived from event logs. You have **{activeItemsCount}** concepts currently tracked in Spaced Repetition.
                </p>
              </div>
            </div>
          </div>

          {/* Forgetting Curve Line Chart */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 space-y-4">
            <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500 flex items-center gap-2">
              <TrendingDown className="h-4 w-4" /> Forgetting Curve Model
            </h3>
            <div className="w-full bg-zinc-950 p-4 rounded-lg border border-zinc-850">
              <svg className="w-full h-[120px]" viewBox={`0 0 ${curveWidth} ${curveHeight}`}>
                {/* Grid Lines */}
                <line x1="0" y1={curveHeight / 2} x2={curveWidth} y2={curveHeight / 2} stroke="#18181b" strokeWidth="1" />
                <path d={svgPath} fill="none" stroke="#818cf8" strokeWidth="2" />
                <circle cx={curveWidth / 4} cy={curveHeight - Math.pow(2, -7.5/7)*curveHeight} r="4" fill="#a78bfa" />
              </svg>
              <div className="flex justify-between text-[9px] text-zinc-500 font-mono mt-2">
                <span>Today (R=100%)</span>
                <span>Day 15</span>
                <span>Day 30 (R=5%)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Active Recall Flipper */}
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500 flex items-center gap-2">
                <Layers className="h-4 w-4" /> Recall Card ({cardIndex + 1}/{DEMO_FLASHCARDS.length})
              </h3>
              <span className="text-[10px] text-zinc-400 font-semibold bg-zinc-850 px-2 py-0.5 rounded border border-zinc-800">
                SM-2 Active
              </span>
            </div>

            {/* Flashcard container */}
            <div className="h-64 relative cursor-pointer" onClick={() => setIsFlipped(!isFlipped)}>
              <AnimatePresence mode="wait">
                {!isFlipped ? (
                  <motion.div
                    key="front"
                    initial={{ rotateY: -90, opacity: 0 }}
                    animate={{ rotateY: 0, opacity: 1 }}
                    exit={{ rotateY: 90, opacity: 0 }}
                    transition={{ duration: 0.25 }}
                    className="absolute inset-0 flex flex-col justify-center items-center p-8 rounded-xl border border-zinc-800 bg-zinc-950 text-center hover:border-zinc-700 transition"
                  >
                    <span className="text-[9px] uppercase font-mono tracking-widest text-indigo-400 mb-4">Question</span>
                    <p className="text-base font-medium text-white leading-relaxed">{DEMO_FLASHCARDS[cardIndex].front}</p>
                    <span className="text-[10px] text-zinc-500 mt-6 uppercase tracking-wider font-bold">Click card to reveal answer</span>
                  </motion.div>
                ) : (
                  <motion.div
                    key="back"
                    initial={{ rotateY: 90, opacity: 0 }}
                    animate={{ rotateY: 0, opacity: 1 }}
                    exit={{ rotateY: -90, opacity: 0 }}
                    transition={{ duration: 0.25 }}
                    className="absolute inset-0 flex flex-col justify-between p-6 rounded-xl border border-zinc-800 bg-zinc-900/40 text-center hover:border-zinc-700 transition"
                  >
                    <div>
                      <span className="text-[9px] uppercase font-mono tracking-widest text-emerald-400">Answer Explanation</span>
                      <p className="text-sm text-zinc-300 leading-relaxed mt-4">{DEMO_FLASHCARDS[cardIndex].back}</p>
                    </div>
                    <span className="text-[10px] text-zinc-500 uppercase tracking-wider font-bold">Select recall rating below</span>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Recall Rating Controls */}
            <div className="space-y-3 pt-2">
              <h4 className="text-xs font-semibold text-zinc-400 text-center">How well did you recall this?</h4>
              <div className="grid grid-cols-5 gap-2">
                {[
                  { rate: 1, label: "Forgot", color: "hover:bg-red-950/40 hover:border-red-900 text-red-400" },
                  { rate: 2, label: "Barely", color: "hover:bg-amber-950/40 hover:border-amber-900 text-amber-400" },
                  { rate: 3, label: "Good", color: "hover:bg-zinc-800 hover:border-zinc-700 text-zinc-300" },
                  { rate: 4, label: "Easy", color: "hover:bg-indigo-950/40 hover:border-indigo-900 text-indigo-400" },
                  { rate: 5, label: "Perfect", color: "hover:bg-emerald-950/40 hover:border-emerald-900 text-emerald-400" }
                ].map((item) => (
                  <button
                    key={item.rate}
                    onClick={() => handleRatingSubmit(item.rate)}
                    disabled={ratingLoading}
                    className={`flex flex-col items-center py-2 bg-zinc-950 border border-zinc-850 rounded-lg text-xs font-semibold tracking-wider transition ${item.color}`}
                  >
                    <Zap className="h-4.5 w-4.5 mb-1" />
                    <span>{item.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
