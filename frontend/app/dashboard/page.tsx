"use client";

import { useEffect, useState } from "react";
import { api } from "@/services/api";
import {
  Sparkles,
  CheckCircle,
  Play,
  Hourglass,
  Activity,
  ChevronRight,
  TrendingUp,
  RefreshCw,
  XCircle,
  AlertTriangle,
  HelpCircle,
} from "lucide-react";

export default function MissionControlPage() {
  const [mission, setMission] = useState<any>(null);
  const [explanation, setExplanation] = useState<any>(null);
  const [showExplainModal, setShowExplainModal] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchMissionData = async () => {
    setIsLoading(true);
    try {
      const data = await api.get<any>("/api/v1/missions/today");
      setMission(data.data);
    } catch (e) {
      setMission(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMissionData();
  }, []);

  const handleCompleteMission = async () => {
    if (!mission) return;
    setActionLoading(true);
    try {
      await api.post(`/api/v1/missions/${mission.id}/complete`);
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

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-3">
        <RefreshCw className="h-8 w-8 text-indigo-400 animate-spin" />
        <p className="text-sm text-zinc-400">Consulting Cognitive Engine...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header section with page title */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-white flex items-center gap-3">
            <CompassIcon className="h-8 w-8 text-indigo-400" /> Mission Control
          </h1>
          <p className="text-sm text-zinc-400">Daily learning execution layer for UPSC preparation.</p>
        </div>

        <button
          onClick={handleRecalculateMission}
          disabled={actionLoading}
          className="flex items-center gap-2 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-zinc-400 bg-zinc-900 border border-zinc-800 rounded-lg hover:text-white hover:border-zinc-700 transition disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${actionLoading ? "animate-spin" : ""}`} />
          Recalculate Mission
        </button>
      </div>

      {!mission ? (
        <div className="rounded-xl border border-zinc-850 bg-zinc-900/20 p-8 text-center space-y-4">
          <AlertTriangle className="h-10 w-10 text-amber-500 mx-auto" />
          <h3 className="text-lg font-medium text-white">No Active Mission</h3>
          <p className="text-sm text-zinc-400 max-w-sm mx-auto">
            You don&apos;t have any learning tasks scheduled for today. Run the Optimization Engine to generate a plan.
          </p>
          <button
            onClick={handleRecalculateMission}
            className="rounded-lg bg-zinc-100 hover:bg-zinc-200 text-zinc-950 px-4 py-2 text-sm font-medium transition"
          >
            Generate Today&apos;s Plan
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Mission Card */}
          <div className="lg:col-span-2 space-y-6">
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 space-y-6">
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-400 bg-indigo-950/40 border border-indigo-900/80 px-2 py-0.5 rounded">
                    {mission.type} Mission
                  </span>
                  <h2 className="text-xl font-semibold text-white mt-2">{mission.title}</h2>
                  <p className="text-sm text-zinc-400 mt-1">{mission.goal}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border ${
                    mission.difficulty_level === "challenge"
                      ? "text-red-400 bg-red-950/40 border-red-900"
                      : mission.difficulty_level === "recovery"
                      ? "text-amber-400 bg-amber-950/40 border-amber-900"
                      : "text-zinc-400 bg-zinc-900/80 border-zinc-800"
                  }`}>
                    {mission.difficulty_level}
                  </span>
                </div>
              </div>

              {/* Task Checklist */}
              <div className="space-y-3">
                <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500">Tasks Checklist</h3>
                {mission.ordered_tasks?.map((task: any) => (
                  <div
                    key={task.id}
                    className="flex items-center justify-between p-3.5 rounded-lg bg-zinc-950 border border-zinc-850"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`h-4.5 w-4.5 rounded-full flex items-center justify-center border ${
                        mission.status === "completed"
                          ? "bg-indigo-500 border-indigo-400 text-white"
                          : "border-zinc-700"
                      }`}>
                        {mission.status === "completed" && <CheckCircle className="h-3 w-3" />}
                      </div>
                      <div>
                        <p className={`text-sm font-medium ${mission.status === "completed" ? "text-zinc-500 line-through" : "text-zinc-200"}`}>
                          {task.description}
                        </p>
                        <p className="text-[10px] text-zinc-500 font-mono mt-0.5">Reference: {task.content_reference}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 text-xs font-mono text-zinc-400">
                      <span className="flex items-center gap-1">
                        <Hourglass className="h-3.5 w-3.5 text-zinc-500" />
                        {task.time_estimate}h
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Actions row */}
              <div className="flex flex-col sm:flex-row gap-3 pt-2">
                {mission.status === "assigned" ? (
                  <>
                    <button
                      onClick={handleCompleteMission}
                      disabled={actionLoading}
                      className="flex-1 flex items-center justify-center gap-2 rounded-lg bg-zinc-100 hover:bg-zinc-200 text-zinc-950 px-4 py-2.5 text-sm font-medium transition disabled:opacity-50"
                    >
                      <CheckCircle className="h-4 w-4" />
                      Complete Mission
                    </button>
                    <button
                      onClick={handleSkipMission}
                      disabled={actionLoading}
                      className="flex-1 flex items-center justify-center gap-2 rounded-lg border border-zinc-800 bg-zinc-950 hover:bg-zinc-900 text-zinc-300 px-4 py-2.5 text-sm font-medium transition disabled:opacity-50"
                    >
                      <XCircle className="h-4 w-4" />
                      Skip & Reschedule
                    </button>
                  </>
                ) : (
                  <div className="w-full text-center py-2 text-xs font-semibold uppercase tracking-wider text-green-400 bg-green-950/20 border border-green-900/50 rounded-lg">
                    ✓ Completed Successfully
                  </div>
                )}
                <button
                  onClick={handleExplainMission}
                  className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border border-zinc-800 bg-zinc-900/40 text-zinc-300 hover:bg-zinc-800 hover:text-white text-sm transition"
                >
                  <HelpCircle className="h-4 w-4" />
                  Explain Layout
                </button>
              </div>
            </div>
          </div>

          {/* Side stats / Expected Gains widgets */}
          <div className="space-y-6">
            {/* Gains widget */}
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 space-y-6">
              <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500">Expected Mission Gains</h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-lg bg-zinc-950 border border-zinc-850 text-center space-y-1.5">
                  <TrendingUp className="h-5 w-5 text-indigo-400 mx-auto" />
                  <p className="text-xs font-medium text-zinc-400">Readiness Boost</p>
                  <p className="text-2xl font-semibold text-white font-mono">+{mission.expected_readiness_gain?.toFixed(1)}</p>
                </div>
                
                <div className="p-4 rounded-lg bg-zinc-950 border border-zinc-850 text-center space-y-1.5">
                  <Activity className="h-5 w-5 text-emerald-400 mx-auto" />
                  <p className="text-xs font-medium text-zinc-400">Mastery Gain</p>
                  <p className="text-2xl font-semibold text-white font-mono">+{mission.expected_mastery_gain?.toFixed(0)}%</p>
                </div>
              </div>

              {/* Time remaining estimate */}
              <div className="flex justify-between items-center p-4 rounded-lg bg-zinc-950 border border-zinc-850">
                <div className="space-y-0.5">
                  <p className="text-xs font-medium text-zinc-400">Estimated Duration</p>
                  <p className="text-lg font-semibold text-white font-mono">{mission.estimated_time?.toFixed(1)} Hours</p>
                </div>
                <div className="h-10 w-10 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-400">
                  <Hourglass className="h-5 w-5" />
                </div>
              </div>
            </div>

            {/* Cognitive telemetry bottlenecks */}
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 space-y-4">
              <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500">Reasoning Engine Signal</h3>
              <div className="space-y-3">
                <div className="p-3 bg-zinc-950 rounded-lg border border-zinc-850 flex items-start gap-3">
                  <Sparkles className="h-4 w-4 text-indigo-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="text-xs font-semibold text-white">Active Deficiency Trace</h4>
                    <p className="text-xs text-zinc-400 mt-1">
                      Priority is configured to study weak prerequisite nodes before dependent chapters.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Socratic Explain Modal */}
      {showExplainModal && explanation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-950/80 backdrop-blur-sm">
          <div className="w-full max-w-xl rounded-xl border border-zinc-800 bg-zinc-900 p-6 shadow-2xl space-y-5 max-h-[85vh] overflow-y-auto animate-in fade-in zoom-in-95 duration-200">
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

function CompassIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <circle cx="12" cy="12" r="10" />
      <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" />
    </svg>
  );
}
