"use client";

import { useEffect, useState, useRef } from "react";
import { api } from "@/services/api";
import {
  Compass,
  Play,
  Pause,
  RotateCcw,
  Sparkles,
  CheckCircle,
  HelpCircle,
  TrendingUp,
  Activity,
  Hourglass,
  Clock,
  BookOpen,
  ArrowRight,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function MissionControlPage() {
  const [mission, setMission] = useState<any>(null);
  const [explanation, setExplanation] = useState<any>(null);
  const [showExplainModal, setShowExplainModal] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  // Focus & Break Timers State
  const [isFocusActive, setIsFocusActive] = useState(false);
  const [focusTimeLeft, setFocusTimeLeft] = useState(25 * 60); // 25 mins
  const [isBreakActive, setIsBreakActive] = useState(false);
  const [breakTimeLeft, setBreakTimeLeft] = useState(5 * 60); // 5 mins

  // Notes state
  const [notes, setNotes] = useState("");

  // Confetti / Completion Animation Trigger
  const [showCelebration, setShowCelebration] = useState(false);

  const focusTimerRef = useRef<any>(null);
  const breakTimerRef = useRef<any>(null);

  const fetchMissionData = async () => {
    setIsLoading(true);
    try {
      const data = await api.get<any>("/api/v1/missions/today");
      setMission(data.data);
      if (data.data?.status === "completed") {
        setShowCelebration(true);
      }
    } catch (e) {
      setMission(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMissionData();
    const savedNotes = localStorage.getItem("mission_notes");
    if (savedNotes) setNotes(savedNotes);
  }, []);

  // Notes sync
  const handleNotesChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setNotes(val);
    localStorage.setItem("mission_notes", val);
  };

  // Focus Timer Logic
  useEffect(() => {
    if (isFocusActive) {
      focusTimerRef.current = setInterval(() => {
        setFocusTimeLeft((prev) => {
          if (prev <= 1) {
            clearInterval(focusTimerRef.current);
            setIsFocusActive(false);
            alert("Focus session complete! Time to take a break.");
            return 25 * 60;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      if (focusTimerRef.current) clearInterval(focusTimerRef.current);
    }
    return () => {
      if (focusTimerRef.current) clearInterval(focusTimerRef.current);
    };
  }, [isFocusActive]);

  // Break Timer Logic
  useEffect(() => {
    if (isBreakActive) {
      breakTimerRef.current = setInterval(() => {
        setBreakTimeLeft((prev) => {
          if (prev <= 1) {
            clearInterval(breakTimerRef.current);
            setIsBreakActive(false);
            alert("Break session finished! Let's get back to work.");
            return 5 * 60;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      if (breakTimerRef.current) clearInterval(breakTimerRef.current);
    }
    return () => {
      if (breakTimerRef.current) clearInterval(breakTimerRef.current);
    };
  }, [isBreakActive]);

  const handleCompleteMission = async () => {
    if (!mission) return;
    setActionLoading(true);
    try {
      await api.post(`/api/v1/missions/${mission.id}/complete`);
      setShowCelebration(true);
      await fetchMissionData();
    } catch (e) {
      alert("Failed to complete mission.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleSkipMission = async () => {
    if (!mission) return;
    if (!confirm("Are you sure you want to skip today's mission? This will trigger dynamic replanning.")) return;
    setActionLoading(true);
    try {
      await api.post(`/api/v1/missions/${mission.id}/skip`);
      await fetchMissionData();
    } catch (e) {
      alert("Failed to skip mission.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleRecalculateMission = async () => {
    setActionLoading(true);
    try {
      await api.post("/api/v1/missions/recalculate");
      await fetchMissionData();
    } catch (e) {
      alert("Failed to recalculate mission.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleExplainMission = async () => {
    if (!mission) return;
    try {
      const data = await api.get<any>(`/api/v1/missions/explain/${mission.id}`);
      setExplanation(data.data);
      setShowExplainModal(true);
    } catch (e) {
      alert("Failed to get explanation.");
    }
  };

  const formatTime = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const s = secs % 60;
    return `${mins.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-3">
        <RefreshCw className="h-8 w-8 text-indigo-400 animate-spin" />
        <p className="text-sm text-zinc-400 font-mono">Loading active study state...</p>
      </div>
    );
  }

  // Calculate task progression percentage
  const totalTasks = mission?.ordered_tasks?.length || 0;
  const isCompleted = mission?.status === "completed";
  const progressPercent = isCompleted ? 100 : totalTasks > 0 ? 40 : 0; // Simple task completion indicator

  return (
    <div className="relative space-y-8 animate-in fade-in duration-300">
      {/* Celebration overlay */}
      <AnimatePresence>
        {showCelebration && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowCelebration(false)}
            className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-zinc-950/90 backdrop-blur-md cursor-pointer"
          >
            <motion.div
              initial={{ scale: 0.8, y: 50 }}
              animate={{ scale: 1, y: 0 }}
              transition={{ type: "spring", damping: 15 }}
              className="text-center space-y-4 max-w-md p-6"
            >
              <div className="h-20 w-20 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-full flex items-center justify-center mx-auto shadow-[0_0_50px_rgba(99,102,241,0.2)]">
                <CheckCircle className="h-10 w-10 animate-bounce" />
              </div>
              <h2 className="text-3xl font-bold tracking-tight text-white">Mission Accomplished!</h2>
              <p className="text-sm text-zinc-400">
                You successfully completed today&apos;s scheduled learning goals. Telemetry signals have been processed.
              </p>
              <div className="pt-4 text-xs font-mono text-indigo-400 uppercase tracking-widest animate-pulse">
                Click anywhere to close
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header section with page title */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-zinc-900 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            <Compass className="h-6 w-6 text-indigo-400" /> Mission Control
          </h1>
          <p className="text-xs text-zinc-400 font-mono mt-0.5">Focus, study, and track your metrics live.</p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRecalculateMission}
            disabled={actionLoading}
            className="flex items-center gap-2 px-3 py-2 text-xs font-medium text-zinc-400 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 rounded-lg hover:text-white transition disabled:opacity-50"
          >
            <RefreshCw className={`h-3 w-3 ${actionLoading ? "animate-spin" : ""}`} />
            Recalculate
          </button>
        </div>
      </div>

      {!mission ? (
        <div className="rounded-xl border border-zinc-900 bg-zinc-900/10 p-8 text-center space-y-4 max-w-lg mx-auto mt-10">
          <AlertTriangle className="h-10 w-10 text-amber-500 mx-auto" />
          <h3 className="text-lg font-medium text-white">No Active Mission</h3>
          <p className="text-xs text-zinc-400 font-mono leading-relaxed">
            You don&apos;t have any learning tasks scheduled for today. Run the Optimization Engine to generate a plan.
          </p>
          <button
            onClick={handleRecalculateMission}
            className="rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 text-xs font-semibold transition"
          >
            Generate Today&apos;s Plan
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left: Workspace */}
          <div className="lg:col-span-2 space-y-6">
            <div className="space-y-1">
              <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-400 bg-indigo-950/40 border border-indigo-900/80 px-2 py-0.5 rounded">
                {mission.type} Study Block
              </span>
              <h2 className="text-3xl font-bold tracking-tight text-white mt-3">{mission.title}</h2>
              <p className="text-sm text-zinc-400">{mission.goal}</p>
            </div>

            {/* Distraction-Free Workspace Current Task */}
            <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 space-y-5">
              <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500 font-mono">Current Objective</h3>
              
              {mission.ordered_tasks?.length > 0 ? (
                <div className="space-y-4">
                  <div className="p-4 rounded-lg bg-zinc-950 border border-zinc-900 space-y-2">
                    <div className="flex justify-between items-start">
                      <span className="text-[10px] uppercase tracking-wider font-bold font-mono text-zinc-500">Active Task</span>
                      <span className="text-[10px] uppercase font-bold font-mono text-indigo-400 flex items-center gap-1">
                        <BookOpen className="h-3 w-3" /> Reading
                      </span>
                    </div>
                    <p className="text-base font-semibold text-white">
                      {mission.ordered_tasks[0].description}
                    </p>
                    <p className="text-xs text-zinc-500 font-mono">Reference: {mission.ordered_tasks[0].content_reference}</p>
                  </div>

                  {mission.ordered_tasks.length > 1 && (
                    <div className="p-4 rounded-lg bg-zinc-900/10 border border-zinc-900 opacity-60 space-y-1.5">
                      <span className="text-[10px] uppercase tracking-wider font-bold font-mono text-zinc-500">Next Objective</span>
                      <div className="flex items-center justify-between">
                        <p className="text-xs font-medium text-zinc-300">
                          {mission.ordered_tasks[1].description}
                        </p>
                        <ArrowRight className="h-4.5 w-4.5 text-zinc-500" />
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-sm text-zinc-400">All objectives finished.</p>
              )}
            </div>

            {/* Action controls */}
            <div className="flex flex-col sm:flex-row gap-3">
              {mission.status === "assigned" ? (
                <>
                  <button
                    onClick={handleCompleteMission}
                    disabled={actionLoading}
                    className="flex-1 flex items-center justify-center gap-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-3 text-sm font-semibold transition disabled:opacity-50 shadow-[0_0_30px_rgba(99,102,241,0.15)]"
                  >
                    <CheckCircle className="h-4.5 w-4.5" />
                    Complete Mission
                  </button>
                  <button
                    onClick={handleSkipMission}
                    disabled={actionLoading}
                    className="flex-1 flex items-center justify-center gap-2 rounded-lg border border-zinc-800 bg-zinc-950 hover:bg-zinc-900 text-zinc-300 px-4 py-3 text-sm font-semibold transition disabled:opacity-50"
                  >
                    Skip Block
                  </button>
                </>
              ) : (
                <div className="w-full text-center py-3 text-sm font-semibold uppercase tracking-wider text-emerald-400 bg-emerald-950/20 border border-emerald-900/50 rounded-lg">
                  ✓ Block Completed Successfully
                </div>
              )}
              <button
                onClick={handleExplainMission}
                className="flex items-center justify-center gap-2 px-4 py-3 rounded-lg border border-zinc-800 bg-zinc-900/40 text-zinc-300 hover:bg-zinc-800 hover:text-white text-sm font-semibold transition"
              >
                <HelpCircle className="h-4.5 w-4.5" />
                Explain Strategy
              </button>
            </div>

            {/* Mission Notes section */}
            <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 space-y-4">
              <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500 font-mono">Workspace Scratchpad</h3>
              <textarea
                value={notes}
                onChange={handleNotesChange}
                placeholder="Jot down key takeaways, reminders, or questions to ask the mentor..."
                className="w-full h-32 bg-zinc-950 border border-zinc-900 rounded-lg p-3 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-zinc-700 font-sans resize-none"
              />
            </div>
          </div>

          {/* Right: Metrics & Timers */}
          <div className="space-y-6">
            {/* Focus & Break Timers */}
            <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 space-y-6">
              <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500 font-mono">Timeboxing Controls</h3>
              
              <div className="grid grid-cols-2 gap-4">
                {/* Focus box */}
                <div className="p-4 rounded-lg bg-zinc-950 border border-zinc-900 text-center space-y-3">
                  <div className="flex items-center justify-center gap-1.5 text-zinc-400">
                    <Clock className="h-3.5 w-3.5 text-indigo-400" />
                    <span className="text-xs font-semibold uppercase tracking-wide">Focus Session</span>
                  </div>
                  <div className="text-2xl font-bold font-mono text-white">
                    {formatTime(focusTimeLeft)}
                  </div>
                  <div className="flex justify-center gap-2">
                    <button
                      onClick={() => setIsFocusActive(!isFocusActive)}
                      className="p-1.5 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300"
                    >
                      {isFocusActive ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
                    </button>
                    <button
                      onClick={() => {
                        setIsFocusActive(false);
                        setFocusTimeLeft(25 * 60);
                      }}
                      className="p-1.5 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-500 hover:text-zinc-300"
                    >
                      <RotateCcw className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>

                {/* Break box */}
                <div className="p-4 rounded-lg bg-zinc-950 border border-zinc-900 text-center space-y-3">
                  <div className="flex items-center justify-center gap-1.5 text-zinc-400">
                    <Hourglass className="h-3.5 w-3.5 text-emerald-400" />
                    <span className="text-xs font-semibold uppercase tracking-wide">Break</span>
                  </div>
                  <div className="text-2xl font-bold font-mono text-white">
                    {formatTime(breakTimeLeft)}
                  </div>
                  <div className="flex justify-center gap-2">
                    <button
                      onClick={() => setIsBreakActive(!isBreakActive)}
                      className="p-1.5 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300"
                    >
                      {isBreakActive ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
                    </button>
                    <button
                      onClick={() => {
                        setIsBreakActive(false);
                        setBreakTimeLeft(5 * 60);
                      }}
                      className="p-1.5 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-500 hover:text-zinc-300"
                    >
                      <RotateCcw className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Live Progress Ring Widget */}
            <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 flex items-center justify-between">
              <div className="space-y-1">
                <h4 className="text-xs uppercase font-bold tracking-wider text-zinc-500 font-mono">Today's Progress</h4>
                <p className="text-2xl font-bold text-white font-mono">{progressPercent}%</p>
                <p className="text-[10px] text-zinc-500 font-mono">Block completion tracking</p>
              </div>

              <div className="relative h-16 w-16">
                <svg className="w-full h-full transform -rotate-90">
                  <circle
                    cx="32"
                    cy="32"
                    r="28"
                    stroke="#18181b"
                    strokeWidth="4"
                    fill="transparent"
                  />
                  <circle
                    cx="32"
                    cy="32"
                    r="28"
                    stroke="#6366f1"
                    strokeWidth="4"
                    fill="transparent"
                    strokeDasharray={175}
                    strokeDashoffset={175 - (175 * progressPercent) / 100}
                    className="transition-all duration-500"
                  />
                </svg>
              </div>
            </div>

            {/* Expected Gains */}
            <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 space-y-6">
              <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500 font-mono">Expected Gains</h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-lg bg-zinc-950 border border-zinc-900 text-center space-y-1">
                  <TrendingUp className="h-5 w-5 text-indigo-400 mx-auto" />
                  <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wide">Readiness Gain</p>
                  <p className="text-2xl font-bold text-white font-mono">+{mission.expected_readiness_gain?.toFixed(1)}</p>
                </div>
                
                <div className="p-4 rounded-lg bg-zinc-950 border border-zinc-900 text-center space-y-1">
                  <Activity className="h-5 w-5 text-emerald-400 mx-auto" />
                  <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wide">Expected Marks</p>
                  <p className="text-2xl font-bold text-white font-mono">+{mission.expected_mastery_gain?.toFixed(0)}</p>
                </div>
              </div>

              {/* Time remaining */}
              <div className="flex justify-between items-center p-4 rounded-lg bg-zinc-950 border border-zinc-900">
                <div className="space-y-0.5">
                  <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wide">Estimated duration</p>
                  <p className="text-lg font-bold text-white font-mono">{mission.estimated_time?.toFixed(1)} Hours</p>
                </div>
                <div className="h-9 w-9 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-400">
                  <Hourglass className="h-4.5 w-4.5" />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Socratic Explain Modal */}
      {showExplainModal && explanation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-950/80 backdrop-blur-sm">
          <div className="w-full max-w-xl rounded-xl border border-zinc-900 bg-zinc-900 p-6 shadow-2xl space-y-5 max-h-[85vh] overflow-y-auto animate-in fade-in zoom-in-95 duration-200">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-[9px] uppercase font-extrabold tracking-widest text-indigo-400 font-mono">Cognitive Explanations</span>
                <h3 className="text-lg font-semibold text-white mt-1">Why am I studying this today?</h3>
              </div>
              <button
                onClick={() => setShowExplainModal(false)}
                className="text-zinc-500 hover:text-zinc-300 font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4 text-sm text-zinc-300">
              <p className="p-3 bg-zinc-950 border border-zinc-850 rounded-lg text-zinc-400">
                {explanation.overall_why}
              </p>

              <div className="space-y-3">
                <h4 className="text-xs uppercase font-bold tracking-wider text-zinc-500">Task-by-Task Socratic Trace</h4>
                {explanation.task_explanations?.map((exp: any, idx: number) => (
                  <div key={idx} className="p-4 rounded-lg bg-zinc-950 border border-zinc-850 space-y-2">
                    <p className="text-xs font-semibold text-white">{exp.description}</p>
                    <p className="text-xs text-zinc-400"><span className="text-indigo-400 font-medium">Why selected:</span> {exp.why_selected}</p>
                    <p className="text-xs text-zinc-450"><span className="text-zinc-500 font-medium">Prerequisite satisfies:</span> {exp.prerequisite_satisfied}</p>
                    <p className="text-[10px] text-emerald-400 font-mono">{exp.expected_readiness_gain}</p>
                  </div>
                ))}
              </div>

              <div className="border-t border-zinc-800 pt-3">
                <p className="text-xs text-zinc-500">
                  <span className="text-amber-400 font-medium">Risk Addressed:</span> {explanation.risk_addressed}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
