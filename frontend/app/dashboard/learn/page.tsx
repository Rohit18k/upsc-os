"use client";

import { useEffect, useState } from "react";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/auth-store";
import {
  BookOpen,
  Sparkles,
  ArrowRight,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  HelpCircle,
  FileText,
} from "lucide-react";

interface NodeData {
  code: string;
  title: string;
  subject: string;
  parent: string;
  prerequisites: string[];
  notes: string;
  x: number;
  y: number;
}

const KNOWLEDGE_NODES: NodeData[] = [
  {
    code: "polity_basics_preamble",
    title: "Preamble of the Constitution",
    subject: "Polity",
    parent: "Basics of Constitution",
    prerequisites: [],
    x: 180,
    y: 120,
    notes: "The Preamble is the introductory statement of the Constitution, detailing the source, objectives, nature, and date of adoption. It represents sovereign, socialist, secular, democratic, republic values. In the Kesavananda Bharati case, it was ruled as an integral part of the constitution."
  },
  {
    code: "economy_rbi",
    title: "Reserve Bank of India (RBI)",
    subject: "Economy",
    parent: "Banking & Inflation",
    prerequisites: [],
    x: 480,
    y: 100,
    notes: "The RBI is India's central banking institution. Established in 1935 under the RBI Act, it regulates the supply of Indian Rupee, manages monetary policy, controls inflation (under a target of 4% +/- 2%), and acts as the lender of last resort."
  },
  {
    code: "economy_monetary_policy",
    title: "Monetary Policy & Inflation",
    subject: "Economy",
    parent: "Banking & Inflation",
    prerequisites: ["economy_rbi"],
    x: 480,
    y: 240,
    notes: "Monetary Policy refers to the monetary authorities' actions to regulate money supply and credit creation. Quantitative instruments include Repo Rate, Reverse Repo Rate, Cash Reserve Ratio (CRR), and Statutory Liquidity Ratio (SLR)."
  }
];

export default function LearnPage() {
  const [twin, setTwin] = useState<any>(null);
  const [selectedNode, setSelectedNode] = useState<NodeData>(KNOWLEDGE_NODES[0]);
  const [isLoading, setIsLoading] = useState(true);
  const [studyLoading, setStudyLoading] = useState(false);
  const [activeMission, setActiveMission] = useState<any>(null);

  const fetchTwinData = async () => {
    setIsLoading(true);
    try {
      const twinRes = await api.get<any>("/api/v1/student/twin");
      setTwin(twinRes.data);
      
      const missionRes = await api.get<any>("/api/v1/missions/today");
      setActiveMission(missionRes.data);
    } catch (e) {
      // Ignored
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTwinData();
  }, []);

  const handleMarkAsRead = async () => {
    if (!selectedNode) return;
    setStudyLoading(true);
    try {
      // Publish event to update Digital Twin
      await api.post("/api/v1/student/events", {
        event_type: "LessonCompleted",
        payload: {
          node_code: selectedNode.code,
          confidence: 0.85,
          difficulty: selectedNode.prerequisites.length > 0 ? 0.6 : 0.3,
          time_spent: 1200.0,
          content_type: "text"
        }
      });
      // Re-fetch twin state
      await fetchTwinData();
    } catch (e) {
      alert("Failed to submit study lesson event.");
    } finally {
      setStudyLoading(false);
    }
  };

  const handleContinueLearning = () => {
    if (!activeMission || !activeMission.ordered_tasks) return;
    // Find the first uncompleted task reference
    const firstTask = activeMission.ordered_tasks.find((t: any) => t.status !== "completed");
    if (firstTask) {
      const matchNode = KNOWLEDGE_NODES.find((n) => n.code === firstTask.content_reference);
      if (matchNode) {
        setSelectedNode(matchNode);
      }
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-3">
        <LoaderIcon className="h-8 w-8 text-indigo-400 animate-spin" />
        <p className="text-sm text-zinc-400">Loading Knowledge Graph...</p>
      </div>
    );
  }

  const masteries = twin?.knowledge_state?.concept_mastery || {};

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-white flex items-center gap-3">
            <BookOpen className="h-8 w-8 text-indigo-400" /> Learn & Explore
          </h1>
          <p className="text-sm text-zinc-400">Navigate syllabus concepts and verify prerequisite dependencies.</p>
        </div>

        {activeMission && (
          <button
            onClick={handleContinueLearning}
            className="flex items-center gap-2 rounded-lg bg-zinc-100 hover:bg-zinc-200 text-zinc-950 px-4 py-2 text-sm font-medium transition"
          >
            <span>Continue Learning Mission</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Knowledge Graph SVG Explorer */}
        <div className="lg:col-span-2 space-y-4">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-5 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500">Interactive Knowledge Graph</h3>
              <div className="flex gap-4 text-[10px] text-zinc-500 font-medium">
                <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-emerald-500"></span> Mastered (&gt;80%)</span>
                <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-amber-500"></span> In Progress</span>
                <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-red-500"></span> Weak (&lt;60%)</span>
              </div>
            </div>

            {/* SVG Visualizer */}
            <div className="relative aspect-[16/9] w-full rounded-lg bg-zinc-950 border border-zinc-850 overflow-hidden">
              <svg className="w-full h-full" viewBox="0 0 680 340">
                {/* Connections / Edges */}
                {KNOWLEDGE_NODES.map((node) => {
                  return node.prerequisites.map((prereqCode) => {
                    const parentNode = KNOWLEDGE_NODES.find((n) => n.code === prereqCode);
                    if (!parentNode) return null;
                    return (
                      <line
                        key={`${parentNode.code}-${node.code}`}
                        x1={parentNode.x}
                        y1={parentNode.y}
                        x2={node.x}
                        y2={node.y}
                        stroke="#27272a"
                        strokeWidth="2.5"
                        strokeDasharray="4 4"
                      />
                    );
                  });
                })}

                {/* Subject groups backgrounds or tags */}
                <text x="180" y="50" textAnchor="middle" fill="#52525b" fontSize="10" fontWeight="bold" letterSpacing="1">POLITY</text>
                <text x="480" y="50" textAnchor="middle" fill="#52525b" fontSize="10" fontWeight="bold" letterSpacing="1">ECONOMY</text>

                {/* Nodes */}
                {KNOWLEDGE_NODES.map((node) => {
                  const mastery = masteries[node.code] || 0.0;
                  const isSelected = selectedNode.code === node.code;
                  
                  // Color codes
                  let nodeColor = "stroke-zinc-700 fill-zinc-900";
                  let dotColor = "bg-zinc-500";
                  if (mastery >= 0.8) {
                    nodeColor = isSelected ? "stroke-emerald-400 fill-emerald-950/20" : "stroke-emerald-800 fill-emerald-950/10";
                    dotColor = "bg-emerald-500";
                  } else if (mastery >= 0.6) {
                    nodeColor = isSelected ? "stroke-amber-400 fill-amber-950/20" : "stroke-amber-800 fill-amber-950/10";
                    dotColor = "bg-amber-500";
                  } else if (mastery > 0.0) {
                    nodeColor = isSelected ? "stroke-red-400 fill-red-950/20" : "stroke-red-800 fill-red-950/10";
                    dotColor = "bg-red-500";
                  } else if (isSelected) {
                    nodeColor = "stroke-indigo-400 fill-zinc-900";
                  }

                  return (
                    <g
                      key={node.code}
                      className="cursor-pointer group"
                      onClick={() => setSelectedNode(node)}
                    >
                      <rect
                        x={node.x - 75}
                        y={node.y - 25}
                        width="150"
                        height="50"
                        rx="8"
                        className={`transition-all duration-200 ${nodeColor} ${isSelected ? "stroke-[2px]" : "stroke-[1px] hover:stroke-zinc-500"}`}
                      />
                      <text
                        x={node.x}
                        y={node.y - 2}
                        textAnchor="middle"
                        fill={isSelected ? "#ffffff" : "#a1a1aa"}
                        fontSize="9.5"
                        fontWeight="semibold"
                      >
                        {node.title.length > 22 ? `${node.title.substring(0, 19)}...` : node.title}
                      </text>
                      <text
                        x={node.x}
                        y={node.y + 12}
                        textAnchor="middle"
                        fill="#52525b"
                        fontSize="8.5"
                        fontFamily="monospace"
                      >
                        Mastery: {(mastery * 100).toFixed(0)}%
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>
          </div>
        </div>

        {/* Selected Concept Lesson detail Sidebar */}
        <div className="space-y-6">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 space-y-6">
            <div>
              <span className="text-[9px] uppercase font-mono tracking-widest text-indigo-400">
                {selectedNode.subject} &bull; {selectedNode.parent}
              </span>
              <h3 className="text-lg font-semibold text-white mt-1">{selectedNode.title}</h3>
            </div>

            {/* Check Prerequisites */}
            {selectedNode.prerequisites.length > 0 && (
              <div className="p-3 bg-red-950/20 border border-red-950 rounded-lg flex items-start gap-2.5">
                <AlertCircle className="h-4 w-4 text-red-400 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="text-xs font-semibold text-red-200">Prerequisite Warning</h4>
                  <p className="text-[10px] text-zinc-400 mt-1">
                    This concept requires mastery of **Reserve Bank of India (RBI)** before continuing.
                  </p>
                </div>
              </div>
            )}

            {/* Content summary */}
            <div className="space-y-3">
              <h4 className="text-xs uppercase font-bold tracking-wider text-zinc-500 flex items-center gap-2">
                <FileText className="h-3.5 w-3.5" /> Concept Summary
              </h4>
              <p className="text-xs text-zinc-300 leading-relaxed bg-zinc-950 p-3.5 rounded-lg border border-zinc-850">
                {selectedNode.notes}
              </p>
            </div>

            {/* AI Generated Study Guide */}
            <div className="p-4 rounded-lg bg-zinc-950 border border-zinc-850 space-y-2">
              <h4 className="text-xs font-semibold text-white flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5 text-indigo-400" /> AI Syllabus Notes
              </h4>
              <ul className="text-[10px] text-zinc-400 space-y-1.5 list-disc pl-4">
                <li>Key focus areas for UPSC Prelims.</li>
                <li>Frequently queried in Mains GS-3 &amp; GS-2 papers.</li>
                <li>Prerequisites: Ensure core banking structures are completed first.</li>
              </ul>
            </div>

            <button
              onClick={handleMarkAsRead}
              disabled={studyLoading}
              className="w-full flex items-center justify-center gap-2 rounded-lg bg-zinc-100 hover:bg-zinc-200 text-zinc-950 px-4 py-2.5 text-sm font-medium transition disabled:opacity-50"
            >
              {studyLoading ? (
                <>
                  <LoaderIcon className="h-4 w-4 animate-spin" /> Submitting...
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4" />
                  Mark Lesson as Read
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function LoaderIcon(props: React.SVGProps<SVGSVGElement>) {
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
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}
