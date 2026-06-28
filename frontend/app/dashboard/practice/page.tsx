"use client";

import { useEffect, useState } from "react";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/auth-store";
import {
  Award,
  Sparkles,
  CheckCircle,
  FileText,
  Clock,
  RefreshCw,
  Edit3,
} from "lucide-react";

interface PracticeQuiz {
  question: string;
  nodeCode: string;
  options: string[];
  correctIdx: number;
}

const DEMO_QUIZ: PracticeQuiz[] = [
  {
    question: "Which supreme court ruling established that the Preamble is an integral part of the basic structure of the Constitution?",
    nodeCode: "polity_basics_preamble",
    options: ["Berubari Union case (1960)", "Kesavananda Bharati case (1973)", "Golaknath case (1967)", "Minerva Mills case (1980)"],
    correctIdx: 1
  },
  {
    question: "When the Reserve Bank of India (RBI) wishes to reduce credit creation and control inflation, what action does it take?",
    nodeCode: "economy_rbi",
    options: ["Decreases Repo Rate", "Decreases Cash Reserve Ratio (CRR)", "Increases Repo Rate", "Buys government bonds in Open Market Operations"],
    correctIdx: 2
  }
];

export default function PracticePage() {
  const [twin, setTwin] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // MCQ state
  const [mcqIndex, setMcqIndex] = useState(0);
  const [selectedOpt, setSelectedOpt] = useState<number | null>(null);
  const [quizCompleted, setQuizCompleted] = useState(false);
  const [quizLoading, setQuizLoading] = useState(false);

  // Essay state
  const [essayContent, setEssayContent] = useState("");
  const [essayLoading, setEssayLoading] = useState(false);
  const [evaluation, setEvaluation] = useState<string | null>(null);

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

  const handleMCQSubmit = async () => {
    if (selectedOpt === null) return;
    const currentQ = DEMO_QUIZ[mcqIndex];
    const isCorrect = selectedOpt === currentQ.correctIdx;
    
    setQuizLoading(true);
    try {
      // Send event to update twin
      await api.post("/api/v1/student/events", {
        event_type: "PYQSolved",
        payload: {
          questions: [
            {
              node_code: currentQ.nodeCode,
              correct: isCorrect,
              difficulty: 0.5,
              error_category: isCorrect ? null : "conceptual_gap"
            }
          ],
          time_spent: 180.0
        }
      });

      if (mcqIndex + 1 < DEMO_QUIZ.length) {
        setMcqIndex(mcqIndex + 1);
        setSelectedOpt(null);
      } else {
        setQuizCompleted(true);
      }
      await fetchTwinState();
    } catch (e) {
      alert("Failed to submit MCQ solution event.");
    } finally {
      setQuizLoading(false);
    }
  };

  const handleEssayEvaluate = async () => {
    if (!essayContent.trim()) return;
    setEssayLoading(true);
    setEvaluation(null);
    try {
      const res = await api.post<any>("/api/v1/tutor/chat", {
        message: essayContent,
        mode: "evaluate"
      });
      setEvaluation(res.data.reply);
      
      // Log event
      await api.post("/api/v1/student/events", {
        event_type: "AnswerWritten",
        payload: {
          node_code: "economy_monetary_policy",
          word_count: essayContent.split(/\s+/).length,
          time_spent: 1200.0,
          quality_score: 0.75
        }
      });
      await fetchTwinState();
    } catch (e) {
      alert("Failed to evaluate answer.");
    } finally {
      setEssayLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-3">
        <RefreshCw className="h-8 w-8 text-indigo-400 animate-spin" />
        <p className="text-sm text-zinc-400">Querying Performance Logs...</p>
      </div>
    );
  }

  // Subject accuracy values
  const polityAccuracy = twin?.practice_state?.subject_accuracy?.Polity || 0.75;
  const economyAccuracy = twin?.practice_state?.subject_accuracy?.Economy || 0.50;

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-white flex items-center gap-3">
            <Award className="h-8 w-8 text-indigo-400" /> Practice & Evaluation
          </h1>
          <p className="text-sm text-zinc-400">Solve mock questions and submit written answers for evaluation.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Performance breakdowns */}
        <div className="space-y-6">
          {/* SVG Subject Accuracy Bar Chart */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 space-y-6">
            <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500">Subject Accuracy Breakdown</h3>
            <div className="space-y-4">
              {/* Polity bar */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs text-zinc-400 font-medium">
                  <span>Indian Polity</span>
                  <span className="font-mono">{(polityAccuracy * 100).toFixed(0)}%</span>
                </div>
                <div className="h-2 w-full bg-zinc-950 rounded-full overflow-hidden border border-zinc-850">
                  <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${polityAccuracy * 100}%` }}></div>
                </div>
              </div>

              {/* Economy bar */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs text-zinc-400 font-medium">
                  <span>Indian Economy</span>
                  <span className="font-mono">{(economyAccuracy * 100).toFixed(0)}%</span>
                </div>
                <div className="h-2 w-full bg-zinc-950 rounded-full overflow-hidden border border-zinc-850">
                  <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${economyAccuracy * 100}%` }}></div>
                </div>
              </div>
            </div>
          </div>

          {/* Mistake Taxonomy widget */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 space-y-4">
            <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500">Mistake Taxonomy</h3>
            <div className="space-y-3">
              <div className="flex justify-between text-xs border-b border-zinc-850/80 pb-2">
                <span className="text-zinc-400">Conceptual Gaps</span>
                <span className="font-semibold text-white">40%</span>
              </div>
              <div className="flex justify-between text-xs border-b border-zinc-850/80 pb-2">
                <span className="text-zinc-400">Active Recall Slip</span>
                <span className="font-semibold text-white">35%</span>
              </div>
              <div className="flex justify-between text-xs pb-1">
                <span className="text-zinc-400">Elimination Faults</span>
                <span className="font-semibold text-white">25%</span>
              </div>
            </div>
          </div>
        </div>

        {/* MCQ Quiz Panel & Mains Writing */}
        <div className="lg:col-span-2 space-y-8">
          {/* MCQ block */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 space-y-6">
            <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500">Active MCQ Drill</h3>
            
            {quizCompleted ? (
              <div className="py-8 text-center space-y-3">
                <CheckCircle className="h-10 w-10 text-emerald-400 mx-auto" />
                <h4 className="text-sm font-semibold text-white">Drill Session Finished</h4>
                <p className="text-xs text-zinc-400">Your practice results are updated and recorded in the Digital Twin.</p>
                <button
                  onClick={() => {
                    setMcqIndex(0);
                    setSelectedOpt(null);
                    setQuizCompleted(false);
                  }}
                  className="px-4 py-2 bg-zinc-950 border border-zinc-800 text-zinc-300 text-xs font-semibold uppercase tracking-wider rounded hover:bg-zinc-900 transition"
                >
                  Restart Drill
                </button>
              </div>
            ) : (
              <div className="space-y-5">
                <p className="text-sm font-medium text-white leading-relaxed">{DEMO_QUIZ[mcqIndex].question}</p>
                
                <div className="space-y-2">
                  {DEMO_QUIZ[mcqIndex].options.map((opt, oIdx) => (
                    <button
                      key={oIdx}
                      onClick={() => setSelectedOpt(oIdx)}
                      className={`w-full flex items-center gap-3 p-3.5 rounded-lg border text-left text-xs font-medium transition ${
                        selectedOpt === oIdx
                          ? "bg-zinc-850 border-indigo-400 text-white"
                          : "bg-zinc-950 border-zinc-850 text-zinc-400 hover:border-zinc-700"
                      }`}
                    >
                      <span className="h-5 w-5 rounded-full border border-zinc-700 flex items-center justify-center font-semibold text-[10px]">
                        {String.fromCharCode(65 + oIdx)}
                      </span>
                      {opt}
                    </button>
                  ))}
                </div>

                <button
                  onClick={handleMCQSubmit}
                  disabled={selectedOpt === null || quizLoading}
                  className="w-full rounded-lg bg-zinc-100 hover:bg-zinc-200 text-zinc-950 px-4 py-2.5 text-sm font-medium transition disabled:opacity-50"
                >
                  {quizLoading ? "Evaluating..." : "Submit Answer"}
                </button>
              </div>
            )}
          </div>

          {/* Mains Answer Essay Area */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 space-y-6">
            <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500 flex items-center gap-2">
              <Edit3 className="h-4 w-4" /> Mains Answer Writing
            </h3>
            
            <div className="space-y-4">
              <div className="p-3 bg-zinc-950 border border-zinc-850 rounded-lg">
                <span className="text-[9px] uppercase font-mono tracking-widest text-indigo-400">Question Topic: Monetary Policy</span>
                <p className="text-xs font-semibold text-white mt-1">
                  &quot;Analyze the role of the Monetary Policy Committee (MPC) in controlling inflation in India. What are the constraints faced by it?&quot; (150 words)
                </p>
              </div>

              <textarea
                placeholder="Write your analysis here..."
                value={essayContent}
                onChange={(e) => setEssayContent(e.target.value)}
                className="w-full h-40 rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2.5 text-xs text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-zinc-600 transition"
              />

              <button
                onClick={handleEssayEvaluate}
                disabled={essayLoading || !essayContent.trim()}
                className="rounded-lg bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 text-xs font-semibold uppercase tracking-wider transition disabled:opacity-50"
              >
                {essayLoading ? "Evaluating via AI..." : "Evaluate Answer"}
              </button>

              {evaluation && (
                <div className="p-4 rounded-lg bg-zinc-950 border border-zinc-850 space-y-3 font-sans text-xs text-zinc-300 leading-relaxed border-l-4 border-l-indigo-400">
                  <div className="flex items-center gap-2 text-indigo-400">
                    <Sparkles className="h-4 w-4" />
                    <span className="font-semibold uppercase tracking-wider">AI Socratic Evaluation</span>
                  </div>
                  <div className="whitespace-pre-wrap">{evaluation}</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
