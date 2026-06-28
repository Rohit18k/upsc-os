"use client";

import { useEffect, useState } from "react";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/auth-store";
import {
  TrendingUp,
  Sparkles,
  RefreshCw,
  Compass,
  Activity,
  Award,
  BookOpen,
} from "lucide-react";

export default function ImprovePage() {
  const [twin, setTwin] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const twinRes = await api.get<any>("/api/v1/student/twin");
        setTwin(twinRes.data);
        
        const histRes = await api.get<any>("/api/v1/missions/history");
        setHistory(histRes.data);
      } catch (e) {
        // Ignored
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-3">
        <RefreshCw className="h-8 w-8 text-indigo-400 animate-spin" />
        <p className="text-sm text-zinc-400">Querying Digital Twin Projections...</p>
      </div>
    );
  }

  // Derive twin values from backend states
  const readiness = twin?.readiness_score || 0.68;
  const knowledge = twin?.knowledge_state?.topic_mastery?.economy_rbi || 0.65;
  const memory = twin?.behaviour_state?.memory_readiness || 0.72;
  const practice = twin?.practice_state?.subject_accuracy?.Polity || 0.70;
  const behaviour = twin?.behaviour_state?.daily_study_consistency || 0.80;
  const writing = twin?.writing_state?.writing_quality || 0.60;

  // Projection values: expected values over 7, 30, 90 days
  const projectionExpected = [readiness * 100, Math.min(100, readiness * 100 + 4), Math.min(100, readiness * 100 + 12), Math.min(100, readiness * 100 + 25)];
  const projectionLower = [readiness * 100, Math.min(100, readiness * 100 + 1), Math.min(100, readiness * 100 + 4), Math.min(100, readiness * 100 + 10)];
  const projectionUpper = [readiness * 100, Math.min(100, readiness * 100 + 6), Math.min(100, readiness * 100 + 16), Math.min(100, readiness * 100 + 32)];

  // Draw Projection Polygon Area for bounding interval
  const plotW = 500;
  const plotH = 150;
  const daysX = [0, plotW / 3, (plotW / 3) * 2, plotW];
  
  const expectedPoints = projectionExpected.map((val, idx) => `${daysX[idx]},${plotH - (val / 100) * plotH}`);
  const upperPoints = projectionUpper.map((val, idx) => `${daysX[idx]},${plotH - (val / 100) * plotH}`);
  const lowerPoints = projectionLower.map((val, idx) => `${daysX[idx]},${plotH - (val / 100) * plotH}`);
  
  // Create area polygon: upper points list then reverse of lower points list
  const lowerPointsRev = [...lowerPoints].reverse();
  const areaPolygon = `${upperPoints.join(" ")} ${lowerPointsRev.join(" ")}`;

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-white flex items-center gap-3">
          <Activity className="h-8 w-8 text-indigo-400" /> Digital Twin & Predictions
        </h1>
        <p className="text-sm text-zinc-400">Assess cognitive profile readiness signals and predicted learning curves.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Core twin gauges */}
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 space-y-6">
            <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500">Readiness Signals Profile</h3>
            
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-6">
              {[
                { name: "Readiness Index", val: readiness, color: "stroke-indigo-400" },
                { name: "Knowledge mastery", val: knowledge, color: "stroke-emerald-400" },
                { name: "Memory retention", val: memory, color: "stroke-violet-400" },
                { name: "Practice depth", val: practice, color: "stroke-amber-400" },
                { name: "Study consistency", val: behaviour, color: "stroke-rose-400" },
                { name: "Writing quality", val: writing, color: "stroke-blue-400" }
              ].map((sig, idx) => (
                <div key={idx} className="p-4 rounded-lg bg-zinc-950 border border-zinc-850 text-center space-y-3">
                  <div className="relative h-16 w-16 mx-auto">
                    <svg className="h-full w-full" viewBox="0 0 36 36">
                      <circle cx="18" cy="18" r="16" fill="none" stroke="#18181b" strokeWidth="2.5" />
                      <circle cx="18" cy="18" r="16" fill="none" className={`${sig.color} transition-all duration-500`} strokeDasharray={`${sig.val * 100}, 100`} strokeWidth="2.5" strokeLinecap="round" transform="rotate(-90 18 18)" />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center text-xs font-semibold text-white font-mono">
                      {(sig.val * 100).toFixed(0)}%
                    </div>
                  </div>
                  <p className="text-[10px] uppercase font-bold tracking-wider text-zinc-500">{sig.name}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Predictions Envelope Area Graph */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 space-y-4">
            <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500 flex items-center gap-2">
              <TrendingUp className="h-4 w-4" /> 90-Day Performance Projection
            </h3>
            
            <div className="w-full bg-zinc-950 p-4 rounded-lg border border-zinc-850">
              <svg className="w-full h-[150px]" viewBox={`0 0 ${plotW} ${plotH}`}>
                {/* Upper/Lower Bounds Envelope Area */}
                <polygon points={areaPolygon} fill="#818cf8" fillOpacity="0.1" />
                {/* Expected Line */}
                <path d={`M ${expectedPoints.join(" L ")}`} fill="none" stroke="#6366f1" strokeWidth="2" />
                {/* Points */}
                {daysX.map((xVal, dIdx) => (
                  <circle key={dIdx} cx={xVal} cy={plotH - (projectionExpected[dIdx] / 100) * plotH} r="3" fill="#ffffff" />
                ))}
              </svg>
              <div className="flex justify-between text-[9px] text-zinc-500 font-mono mt-2">
                <span>Today ({(readiness * 100).toFixed(0)}%)</span>
                <span>Day 7</span>
                <span>Day 30</span>
                <span>Day 90 (+25%)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Mission History Timeline */}
        <div className="space-y-6">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 space-y-6">
            <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500 flex items-center gap-2">
              <Compass className="h-4 w-4" /> Learning Mission Log
            </h3>

            {history.length === 0 ? (
              <p className="text-xs text-zinc-500 text-center py-6">No previous missions found.</p>
            ) : (
              <div className="relative border-l border-zinc-850 ml-2 pl-4 space-y-5">
                {history.map((item: any, idx: number) => (
                  <div key={item.id} className="relative space-y-1">
                    {/* Timeline dot */}
                    <span className={`absolute -left-[21.5px] top-1.5 h-3 w-3 rounded-full border ${
                      item.status === "completed"
                        ? "bg-green-500 border-green-400"
                        : "bg-zinc-800 border-zinc-700"
                    }`}></span>
                    <h4 className="text-xs font-semibold text-white">{item.title}</h4>
                    <p className="text-[10px] text-zinc-500">{item.goal}</p>
                    <div className="flex gap-2 text-[9px] font-mono mt-1">
                      <span className={item.status === "completed" ? "text-green-400" : "text-zinc-500"}>
                        {item.status}
                      </span>
                      <span className="text-zinc-650">&bull;</span>
                      <span className="text-zinc-500">Duration: {item.estimated_time?.toFixed(1)}h</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
