"use client";

import { useEffect, useState } from "react";
import { api } from "@/services/api";
import {
  BookOpen,
  Sparkles,
  ArrowRight,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  HelpCircle,
  FileText,
  Search,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Bookmark,
  Highlighter,
  PlusCircle,
  Send,
  MessageCircle,
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
    x: 150,
    y: 120,
    notes: "The Preamble is the introductory statement of the Constitution, detailing the source, objectives, nature, and date of adoption. It represents sovereign, socialist, secular, democratic, republic values. In the Kesavananda Bharati case, it was ruled as an integral part of the constitution."
  },
  {
    code: "economy_rbi",
    title: "Reserve Bank of India (RBI)",
    subject: "Economy",
    parent: "Banking & Inflation",
    prerequisites: [],
    x: 450,
    y: 100,
    notes: "The RBI is India's central banking institution. Established in 1935 under the RBI Act, it regulates the supply of Indian Rupee, manages monetary policy, controls inflation (under a target of 4% +/- 2%), and acts as the lender of last resort."
  },
  {
    code: "economy_monetary_policy",
    title: "Monetary Policy & Inflation",
    subject: "Economy",
    parent: "Banking & Inflation",
    prerequisites: ["economy_rbi"],
    x: 450,
    y: 240,
    notes: "Monetary Policy refers to the monetary authorities' actions to regulate money supply and credit creation. Quantitative instruments include Repo Rate, Reverse Repo Rate, Cash Reserve Ratio (CRR), and Statutory Liquidity Ratio (SLR)."
  },
  {
    code: "polity_fundamental_rights",
    title: "Fundamental Rights",
    subject: "Polity",
    parent: "Basics of Constitution",
    prerequisites: ["polity_basics_preamble"],
    x: 150,
    y: 240,
    notes: "Fundamental Rights are enshrined in Part III (Articles 12 to 35). They are justiciable and defend the liberty of citizens against state overreach. Major categories include Right to Equality (Art 14-18), Right to Freedom (Art 19-22), and Right to Constitutional Remedies (Art 32)."
  }
];

export default function LearnPage() {
  const [twin, setTwin] = useState<any>(null);
  const [selectedNode, setSelectedNode] = useState<NodeData>(KNOWLEDGE_NODES[0]);
  const [isLoading, setIsLoading] = useState(true);
  const [studyLoading, setStudyLoading] = useState(false);
  const [activeMission, setActiveMission] = useState<any>(null);

  // LXP state
  const [searchQuery, setSearchQuery] = useState("");
  const [zoom, setZoom] = useState(1);
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [highlights, setHighlights] = useState<string[]>([]);
  const [notesInput, setNotesInput] = useState("");
  const [mentorQuestion, setMentorQuestion] = useState("");
  const [mentorReplies, setMentorReplies] = useState<Array<{ q: string; a: string }>>([]);
  const [askLoading, setAskLoading] = useState(false);

  // Flashcards state
  const [flashcardsCount, setFlashcardsCount] = useState(0);

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

  // Sync bookmarks & annotations per node
  useEffect(() => {
    if (!selectedNode) return;
    const bookmarked = localStorage.getItem(`bookmark:${selectedNode.code}`) === "true";
    setIsBookmarked(bookmarked);

    const savedNotes = localStorage.getItem(`notes:${selectedNode.code}`) || "";
    setNotesInput(savedNotes);

    const savedHighlights = JSON.parse(localStorage.getItem(`highlights:${selectedNode.code}`) || "[]");
    setHighlights(savedHighlights);
    
    setMentorReplies([]);
  }, [selectedNode]);

  const handleToggleBookmark = () => {
    const nextState = !isBookmarked;
    setIsBookmarked(nextState);
    localStorage.setItem(`bookmark:${selectedNode.code}`, String(nextState));
  };

  const handleAddHighlight = () => {
    const selectedText = window.getSelection()?.toString();
    if (selectedText && selectedText.trim().length > 0) {
      const nextHighlights = [...highlights, selectedText];
      setHighlights(nextHighlights);
      localStorage.setItem(`highlights:${selectedNode.code}`, JSON.stringify(nextHighlights));
    }
  };

  const handleNotesChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setNotesInput(val);
    localStorage.setItem(`notes:${selectedNode.code}`, val);
  };

  const handleGenerateFlashcard = () => {
    // Simulated generator mapping concept snippets
    setFlashcardsCount((prev) => prev + 1);
    alert(`Flashcard generated for "${selectedNode.title}" and pushed to Revision queue!`);
  };

  const handleAskMentor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mentorQuestion.trim()) return;

    setAskLoading(true);
    const q = mentorQuestion;
    setMentorQuestion("");

    try {
      const res = await api.post<any>("/api/v1/tutor/chat", {
        message: `For the concept '${selectedNode.title}', explain: ${q}`,
        mode: "socratic"
      });
      const reply = res.data?.reply || "I am processing your query. Please focus on core concepts.";
      setMentorReplies((prev) => [...prev, { q, a: reply }]);
    } catch (err) {
      setMentorReplies((prev) => [...prev, { q, a: "Sorry, I could not contact the mentor server right now." }]);
    } finally {
      setAskLoading(false);
    }
  };

  const handleMarkAsRead = async () => {
    if (!selectedNode) return;
    setStudyLoading(true);
    try {
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
      await fetchTwinData();
      alert("Progress synced to Digital Twin graph.");
    } catch (e) {
      alert("Failed to submit telemetry.");
    } finally {
      setStudyLoading(false);
    }
  };

  // Determine node color states based on digital twin telemetry
  const getNodeColor = (nodeCode: string) => {
    // Check if node is active mission node
    const isMission = activeMission?.ordered_tasks?.some((t: any) => t.content_reference.includes(nodeCode));
    if (isMission) return "#fbbf24"; // Gold

    const conceptMastery = twin?.knowledge_state?.concept_mastery || {};
    const mastery = conceptMastery[nodeCode];

    if (mastery !== undefined) {
      return mastery >= 0.7 ? "#10b981" : "#ef4444"; // Completed vs Weak
    }

    // Check prerequisites
    const node = KNOWLEDGE_NODES.find((n) => n.code === nodeCode);
    if (node && node.prerequisites.some((prereq) => (conceptMastery[prereq] || 0) < 0.7)) {
      return "#3f3f46"; // Locked (prereq unfulfilled)
    }

    return "#71717a"; // Unvisited/Default
  };

  const filteredNodes = KNOWLEDGE_NODES.filter((n) =>
    n.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    n.subject.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center border-b border-zinc-900 pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-3">
            <BookOpen className="h-5.5 w-5.5 text-indigo-400" /> Interactive Lesson Reader
          </h1>
          <p className="text-xs text-zinc-400 font-mono">Telemetry-grounded lesson layout & interactive syllabus map.</p>
        </div>

        {/* Node search */}
        <div className="relative w-64">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-zinc-500" />
          <input
            type="text"
            placeholder="Search syllabus..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-zinc-900/60 border border-zinc-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-zinc-200 focus:outline-none focus:border-zinc-700 placeholder-zinc-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left column: Split screen Interactive Reader */}
        <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 flex flex-col justify-between space-y-6 min-h-[70vh]">
          <div className="space-y-5">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-[9px] font-bold font-mono tracking-widest text-indigo-400 uppercase bg-indigo-950/40 border border-indigo-900/80 px-2 py-0.5 rounded">
                  {selectedNode.subject}
                </span>
                <h2 className="text-2xl font-bold text-white mt-3">{selectedNode.title}</h2>
              </div>

              {/* Reader Options */}
              <div className="flex gap-2">
                <button
                  onClick={handleToggleBookmark}
                  className={`p-2 rounded-lg border border-zinc-800 bg-zinc-950 transition ${isBookmarked ? "text-yellow-400" : "text-zinc-500 hover:text-zinc-300"}`}
                  title="Bookmark Lesson"
                >
                  <Bookmark className="h-4 w-4" />
                </button>
                <button
                  onClick={handleAddHighlight}
                  className="p-2 rounded-lg border border-zinc-800 bg-zinc-950 text-zinc-500 hover:text-zinc-300 transition"
                  title="Highlight Selection"
                >
                  <Highlighter className="h-4 w-4" />
                </button>
                <button
                  onClick={handleGenerateFlashcard}
                  className="p-2 rounded-lg border border-zinc-800 bg-zinc-950 text-zinc-500 hover:text-indigo-400 transition"
                  title="Generate Flashcard"
                >
                  <PlusCircle className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Lesson Body Text */}
            <div className="text-sm text-zinc-300 leading-relaxed space-y-4 bg-zinc-950/40 p-4 border border-zinc-900 rounded-lg">
              <p>{selectedNode.notes}</p>
              
              {/* Highlight list */}
              {highlights.length > 0 && (
                <div className="pt-3 border-t border-zinc-900 space-y-2">
                  <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider font-mono">Your Highlights</h4>
                  {highlights.map((h, i) => (
                    <div key={i} className="text-xs italic bg-yellow-950/20 border-l-2 border-yellow-500/50 p-2 rounded text-zinc-300">
                      &quot;{h}&quot;
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Annotations scratchpad */}
            <div className="space-y-2">
              <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider font-mono">Personal Annotations</h4>
              <textarea
                value={notesInput}
                onChange={handleNotesChange}
                placeholder="Type annotations or insights for this concept..."
                className="w-full h-20 bg-zinc-950 border border-zinc-900 rounded-lg p-2.5 text-xs text-zinc-300 placeholder-zinc-700 focus:outline-none focus:border-zinc-800 resize-none font-sans"
              />
            </div>

            {/* Interactive Mentor Q&A */}
            <div className="border-t border-zinc-900 pt-4 space-y-3">
              <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider font-mono">Ask AI Mentor</h4>
              
              {mentorReplies.length > 0 && (
                <div className="space-y-3 max-h-40 overflow-y-auto pr-1">
                  {mentorReplies.map((chat, idx) => (
                    <div key={idx} className="space-y-1">
                      <p className="text-xs font-semibold text-white">Q: {chat.q}</p>
                      <p className="text-xs text-zinc-400 bg-zinc-900/40 p-2 rounded border border-zinc-900">
                        {chat.a}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              <form onSubmit={handleAskMentor} className="flex gap-2">
                <input
                  type="text"
                  placeholder="Ask a question about this doctrine..."
                  value={mentorQuestion}
                  onChange={(e) => setMentorQuestion(e.target.value)}
                  className="flex-1 bg-zinc-950 border border-zinc-900 rounded-lg px-3 py-2 text-xs text-zinc-200 placeholder-zinc-700 focus:outline-none focus:border-zinc-800"
                />
                <button
                  type="submit"
                  disabled={askLoading}
                  className="px-3 py-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-300 disabled:opacity-50"
                >
                  <Send className="h-3.5 w-3.5" />
                </button>
              </form>
            </div>
          </div>

          <div className="pt-4 border-t border-zinc-900 flex justify-between items-center">
            <span className="text-xs text-zinc-500 font-mono">
              Generated: {flashcardsCount} flashcards
            </span>
            <button
              onClick={handleMarkAsRead}
              disabled={studyLoading}
              className="flex items-center gap-2 rounded-lg bg-zinc-100 hover:bg-zinc-200 text-zinc-950 px-4 py-2 text-xs font-semibold transition disabled:opacity-50"
            >
              <CheckCircle className="h-3.5 w-3.5" />
              Mark Concept Completed
            </button>
          </div>
        </div>

        {/* Right column: Interactive Knowledge Graph */}
        <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 flex flex-col justify-between min-h-[70vh]">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500 font-mono">Syllabus Dependency Map</h3>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setZoom((prev) => Math.max(0.5, prev - 0.1))}
                  className="p-1 rounded bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white border border-zinc-800"
                >
                  <ZoomOut className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={() => setZoom((prev) => Math.min(2, prev + 0.1))}
                  className="p-1 rounded bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white border border-zinc-800"
                >
                  <ZoomIn className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={() => setZoom(1)}
                  className="p-1 rounded bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white border border-zinc-800"
                >
                  <RotateCcw className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            {/* SVG Visualizer */}
            <div className="h-[55vh] border border-zinc-900 bg-zinc-950 rounded-lg relative overflow-hidden flex items-center justify-center">
              <svg
                width="100%"
                height="100%"
                className="transition-transform duration-200 ease-out"
                style={{ transform: `scale(${zoom})` }}
              >
                {/* Connection lines */}
                {KNOWLEDGE_NODES.map((node) => {
                  return node.prerequisites.map((prereqCode) => {
                    const prereqNode = KNOWLEDGE_NODES.find((n) => n.code === prereqCode);
                    if (!prereqNode) return null;
                    return (
                      <line
                        key={`${prereqCode}-${node.code}`}
                        x1={prereqNode.x}
                        y1={prereqNode.y}
                        x2={node.x}
                        y2={node.y}
                        stroke="#27272a"
                        strokeWidth="2.5"
                        strokeDasharray="4"
                      />
                    );
                  });
                })}

                {/* Nodes */}
                {filteredNodes.map((node) => {
                  const color = getNodeColor(node.code);
                  const isSelected = selectedNode.code === node.code;
                  return (
                    <g
                      key={node.code}
                      onClick={() => setSelectedNode(node)}
                      className="cursor-pointer group"
                    >
                      <circle
                        cx={node.x}
                        cy={node.y}
                        r={isSelected ? 18 : 14}
                        fill={color}
                        stroke={isSelected ? "#ffffff" : "#18181b"}
                        strokeWidth={isSelected ? 3 : 2}
                        className="transition-all duration-150 group-hover:scale-110"
                      />
                      <text
                        x={node.x}
                        y={node.y + 32}
                        fill={isSelected ? "#ffffff" : "#71717a"}
                        textAnchor="middle"
                        fontSize="9.5"
                        fontWeight={isSelected ? "bold" : "normal"}
                        className="pointer-events-none select-none font-mono"
                      >
                        {node.title.split(" ")[0]}...
                      </text>
                    </g>
                  );
                })}
              </svg>

              {/* Quick colors indicator */}
              <div className="absolute bottom-3 left-3 bg-zinc-900/80 border border-zinc-800 rounded-lg p-2.5 text-[9px] font-mono text-zinc-400 space-y-1.5">
                <div className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-[#fbbf24]" /> Today&apos;s Mission Node
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-[#10b981]" /> Completed Concept
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-[#ef4444]" /> Weak Concept
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-[#3f3f46]" /> Locked (Prereq Missing)
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
