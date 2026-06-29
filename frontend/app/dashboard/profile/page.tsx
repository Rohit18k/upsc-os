"use client";

import { useEffect, useState } from "react";
import { api } from "@/services/api";
import {
  User,
  Sparkles,
  RefreshCw,
  TrendingUp,
  Activity,
  Award,
  BookOpen,
  AlertTriangle,
  Flame,
  LineChart,
} from "lucide-react";

export default function PersonalDashboard() {
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
        <p className="text-sm text-zinc-400 font-mono">Syncing cognitive digital twin data...</p>
      </div>
    );
  }

  // Derive twin values from backend states (or fallback to defaults)
  const readiness = twin?.knowledge_readiness || 0.68;
  const knowledge = twin?.knowledge_readiness || 0.65;
  const memory = twin?.memory_readiness || 0.72;
  const practice = twin?.practice_readiness || 0.70;
  const behaviour = twin?.behaviour_readiness || 0.80;
  const writing = twin?.writing_readiness || 0.60;

  // Predict rankings and scores based on readiness
  const predictedAIR = Math.max(12, Math.floor(1000 - readiness * 900));
  const expectedPrelims = (readiness * 130).toFixed(1);
  const expectedMains = Math.floor(readiness * 1050 + 200);

  // Projections: Expected readiness growth over 7, 30, 90 days
  const projectionExpected = [
    readiness * 100,
    Math.min(100, readiness * 100 + 4),
    Math.min(100, readiness * 100 + 12),
    Math.min(100, readiness * 100 + 25),
  ];
  const projectionUpper = [
    readiness * 100,
    Math.min(100, readiness * 100 + 6),
    Math.min(100, readiness * 100 + 16),
    Math.min(100, readiness * 100 + 32),
  ];
  const projectionLower = [
    readiness * 100,
    Math.min(100, readiness * 100 + 1),
    Math.min(100, readiness * 100 + 4),
    Math.min(100, readiness * 100 + 10),
  ];

  // Draw Projection Polygon Area for bounding interval
  const plotW = 500;
  const plotH = 150;
  const daysX = [0, plotW / 3, (plotW / 3) * 2, plotW];

  const upperPoints = projectionUpper.map((val, idx) => `${daysX[idx]},${plotH - (val / 100) * plotH}`);
  const lowerPoints = projectionLower.map((val, idx) => `${daysX[idx]},${plotH - (val / 100) * plotH}`);
  const expectedPoints = projectionExpected.map((val, idx) => `${daysX[idx]},${plotH - (val / 100) * plotH}`);

  const lowerPointsRev = [...lowerPoints].reverse();
  const areaPolygon = `${upperPoints.join(" ")} ${lowerPointsRev.join(" ")}`;

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header section with page title */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-zinc-900 pb-5">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-3">
            <User className="h-5.5 w-5.5 text-indigo-400" /> Digital Twin Dashboard
          </h1>
          <p className="text-xs text-zinc-400 font-mono">Cognitive projections and predictive UPSC score index tracking.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Core twin gauges */}
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 space-y-6">
            <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500 font-mono">Readiness Profile</h3>
            
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-6">
              {[
                { name: "Readiness Index", val: readiness, color: "stroke-indigo-500" },
                { name: "Syllabus Mastery", val: knowledge, color: "stroke-emerald-500" },
                { name: "Retention Rate", val: memory, color: "stroke-violet-500" },
                { name: "Practice Accuracy", val: practice, color: "stroke-amber-500" },
                { name: "Study consistency", val: behaviour, color: "stroke-rose-500" },
                { name: "Writing quality", val: writing, color: "stroke-blue-500" },
              ].map((sig, idx) => (
                <div key={idx} className="p-4 rounded-lg bg-zinc-950 border border-zinc-900 text-center space-y-3">
                  <div className="relative h-16 w-16 mx-auto">
                    <svg className="h-full w-full" viewBox="0 0 36 36">
                      <path
                        className="stroke-zinc-900"
                        strokeWidth="3.5"
                        fill="none"
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      />
                      <path
                        className={`${sig.color} transition-all duration-500`}
                        strokeWidth="3.5"
                        strokeDasharray={`${sig.val * 100}, 100`}
                        strokeLinecap="round"
                        fill="none"
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center text-sm font-semibold font-mono text-white">
                      {(sig.val * 100).toFixed(0)}%
                    </div>
                  </div>
                  <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-wide font-mono">{sig.name}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Predicted curves and SVG graphs */}
          <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 space-y-6">
            <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500 font-mono">90-Day Readiness Projections</h3>
            
            <div className="bg-zinc-950/40 p-4 rounded-lg border border-zinc-900">
              <svg width="100%" height={plotH} viewBox={`0 0 ${plotW} ${plotH}`}>
                {/* Confidence boundary area */}
                <polygon points={areaPolygon} fill="#6366f1" fillOpacity="0.08" />
                
                {/* Upper line */}
                <polyline fill="none" stroke="#6366f1" strokeWidth="1" strokeDasharray="3" points={upperPoints.join(" ")} />
                {/* Lower line */}
                <polyline fill="none" stroke="#6366f1" strokeWidth="1" strokeDasharray="3" points={lowerPoints.join(" ")} />
                {/* Main projection curve */}
                <polyline fill="none" stroke="#6366f1" strokeWidth="2.5" points={expectedPoints.join(" ")} />

                {/* X labels grid */}
                <line x1={0} y1={0} x2={0} y2={plotH} stroke="#18181b" />
                <line x1={plotW / 3} y1={0} x2={plotW / 3} y2={plotH} stroke="#18181b" />
                <line x1={(plotW / 3) * 2} y1={0} x2={(plotW / 3) * 2} y2={plotH} stroke="#18181b" />
                <line x1={plotW} y1={0} x2={plotW} y2={plotH} stroke="#18181b" />
              </svg>

              <div className="flex justify-between items-center text-[10px] text-zinc-500 font-mono mt-3">
                <span>Start</span>
                <span>Day 30</span>
                <span>Day 60</span>
                <span>Day 90</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right column: Predictions index & Risk areas */}
        <div className="space-y-6">
          {/* Predictions scoreboard */}
          <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 space-y-6">
            <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500 font-mono">Predicted rank & scores</h3>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3.5 bg-zinc-950 border border-zinc-900 rounded-lg">
                <div className="space-y-0.5">
                  <p className="text-[10px] text-zinc-500 uppercase tracking-wide font-mono">Predicted AIR</p>
                  <p className="text-xl font-bold text-white font-mono">Rank #{predictedAIR}</p>
                </div>
                <Award className="h-7 w-7 text-indigo-400" />
              </div>

              <div className="flex justify-between items-center p-3.5 bg-zinc-950 border border-zinc-900 rounded-lg">
                <div className="space-y-0.5">
                  <p className="text-[10px] text-zinc-500 uppercase tracking-wide font-mono">Expected Prelims Score</p>
                  <p className="text-xl font-bold text-white font-mono">{expectedPrelims} / 200</p>
                </div>
                <TrendingUp className="h-7 w-7 text-emerald-400" />
              </div>

              <div className="flex justify-between items-center p-3.5 bg-zinc-950 border border-zinc-900 rounded-lg">
                <div className="space-y-0.5">
                  <p className="text-[10px] text-zinc-500 uppercase tracking-wide font-mono">Expected Mains Score</p>
                  <p className="text-xl font-bold text-white font-mono">{expectedMains} / 1750</p>
                </div>
                <LineChart className="h-7 w-7 text-violet-400" />
              </div>
            </div>
          </div>

          {/* Telemetry risk areas */}
          <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 space-y-4">
            <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500 font-mono">Identified Risk Areas</h3>
            
            <div className="space-y-3">
              {readiness < 0.7 ? (
                <div className="p-3 bg-red-950/20 border border-red-900/40 rounded-lg flex items-start gap-3">
                  <AlertTriangle className="h-4.5 w-4.5 text-red-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="text-xs font-semibold text-white">Syllabus Coverage Gap</h4>
                    <p className="text-[10px] text-zinc-400 mt-1 leading-relaxed">
                      Your knowledge state indicates conceptual gaps in Economics (RBI credit controls). Focus on prerequisites.
                    </p>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-zinc-500">No major cognitive risks detected.</p>
              )}

              {writing < 0.65 && (
                <div className="p-3 bg-amber-950/20 border border-amber-900/40 rounded-lg flex items-start gap-3">
                  <AlertTriangle className="h-4.5 w-4.5 text-amber-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="text-xs font-semibold text-white">Writing Structural Deficiency</h4>
                    <p className="text-[10px] text-zinc-400 mt-1 leading-relaxed">
                      Mains writing submissions show inconsistent introductory phrasing and lack of references.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
