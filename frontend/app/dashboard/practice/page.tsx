"use client";

import { useEffect, useState, useRef } from "react";
import { api } from "@/services/api";
import {
  Award,
  Clock,
  RefreshCw,
  Bookmark,
  CheckCircle,
  XCircle,
  HelpCircle,
  BookOpen,
  AlertCircle,
  Heart,
} from "lucide-react";

interface PracticeQuiz {
  id: string;
  question: string;
  nodeCode: string;
  subject: string;
  options: string[];
  correctIdx: number;
  explanation: string;
  difficulty: "Easy" | "Medium" | "Hard";
}

const DEMO_QUIZ: PracticeQuiz[] = [
  {
    id: "pq_1",
    question: "Which supreme court ruling established that the Preamble is an integral part of the basic structure of the Constitution?",
    nodeCode: "polity_basics_preamble",
    subject: "Polity",
    options: ["Berubari Union case (1960)", "Kesavananda Bharati case (1973)", "Golaknath case (1967)", "Minerva Mills case (1980)"],
    correctIdx: 1,
    explanation: "In the Kesavananda Bharati case (1973), the Supreme Court ruled that the Preamble is an integral part of the Constitution and can be amended under Article 368, provided it does not alter basic features.",
    difficulty: "Medium"
  },
  {
    id: "pq_2",
    question: "When the Reserve Bank of India (RBI) wishes to reduce credit creation and control inflation, what action does it take?",
    nodeCode: "economy_rbi",
    subject: "Economy",
    options: ["Decreases Repo Rate", "Decreases Cash Reserve Ratio (CRR)", "Increases Repo Rate", "Buys government bonds in Open Market Operations"],
    correctIdx: 2,
    explanation: "Increasing Repo Rate makes borrowing expensive for commercial banks, reducing money supply in the economy and helping to curb inflationary pressures.",
    difficulty: "Hard"
  },
  {
    id: "pq_3",
    question: "Which article of the Indian Constitution guarantees Right to Constitutional Remedies (the heart and soul of the Constitution)?",
    nodeCode: "polity_fundamental_rights",
    subject: "Polity",
    options: ["Article 14", "Article 19", "Article 21", "Article 32"],
    correctIdx: 3,
    explanation: "Dr. B.R. Ambedkar termed Article 32 (Right to Constitutional Remedies) as the heart and soul of the Constitution, as it empowers citizens to petition the Supreme Court for enforcement of rights.",
    difficulty: "Easy"
  }
];

export default function PracticePage() {
  const [twin, setTwin] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Timed quiz state
  const [sessionActive, setSessionActive] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedOpt, setSelectedOpt] = useState<number | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [timerRunning, setTimerRunning] = useState(false);
  const timerRef = useRef<any>(null);

  // Score states (Negative marking)
  const [score, setScore] = useState(0);
  const [correctCount, setCorrectCount] = useState(0);
  const [incorrectCount, setIncorrectCount] = useState(0);

  // Mistake Notebook & Bookmarks
  const [mistakes, setMistakes] = useState<Array<{ question: string; explanation: string; nodeCode: string }>>([]);
  const [bookmarks, setBookmarks] = useState<string[]>([]);

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

  const startQuiz = () => {
    setSessionActive(true);
    setSeconds(0);
    setTimerRunning(true);
    setCurrentIndex(0);
    setSelectedOpt(null);
    setSubmitted(false);
    setScore(0);
    setCorrectCount(0);
    setIncorrectCount(0);
  };

  const handleToggleBookmark = (id: string) => {
    if (bookmarks.includes(id)) {
      setBookmarks(bookmarks.filter((b) => b !== id));
    } else {
      setBookmarks([...bookmarks, id]);
    }
  };

  const handleSubmitAnswer = async () => {
    if (selectedOpt === null || submitted) return;

    setSubmitted(true);
    const activeQ = DEMO_QUIZ[currentIndex];
    const isCorrect = selectedOpt === activeQ.correctIdx;

    if (isCorrect) {
      setCorrectCount((prev) => prev + 1);
      setScore((prev) => prev + 2.0); // +2 for correct
    } else {
      setIncorrectCount((prev) => prev + 1);
      setScore((prev) => prev - 0.66); // -0.66 penalty
      
      // Store in Mistake Notebook
      setMistakes((prev) => [
        ...prev,
        { question: activeQ.question, explanation: activeQ.explanation, nodeCode: activeQ.nodeCode }
      ]);
    }

    try {
      // Record answer event to update Twin telemetry
      await api.post("/api/v1/student/events", {
        event_type: "PYQSolved",
        payload: {
          questions: [
            {
              node_code: activeQ.nodeCode,
              correct: isCorrect,
              difficulty: activeQ.difficulty === "Easy" ? 0.3 : activeQ.difficulty === "Medium" ? 0.6 : 0.9,
              error_category: isCorrect ? null : "conceptual_gap"
            }
          ],
          time_spent: 60.0
        }
      });
      await fetchTwinState();
    } catch (err) {
      console.warn("Failed to sync event to telemetry server.");
    }
  };

  const handleNextQuestion = () => {
    if (currentIndex + 1 < DEMO_QUIZ.length) {
      setCurrentIndex((prev) => prev + 1);
      setSelectedOpt(null);
      setSubmitted(false);
    } else {
      setTimerRunning(false);
      alert("Practice block completed! Your results have been computed.");
    }
  };

  const formatTimer = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const activeQ = DEMO_QUIZ[currentIndex];

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header section with page title */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-zinc-900 pb-5">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-3">
            <Award className="h-5.5 w-5.5 text-indigo-400" /> MCQ & PYQ Practice Studio
          </h1>
          <p className="text-xs text-zinc-400 font-mono">Real-time scoring engine simulating UPSC penalty structures.</p>
        </div>

        {sessionActive && (
          <div className="flex items-center gap-4 text-xs font-mono text-zinc-400">
            <span className="flex items-center gap-1.5 px-3 py-1 bg-zinc-900 border border-zinc-800 rounded-lg">
              <Clock className="h-3.5 w-3.5 text-indigo-400" /> {formatTimer(seconds)}
            </span>
            <span className="text-zinc-500">Score: <span className="font-bold text-white">{score.toFixed(2)}</span></span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Practice Workspace */}
        <div className="lg:col-span-2 space-y-6">
          {!sessionActive ? (
            <div className="rounded-xl border border-zinc-900 bg-zinc-900/10 p-10 text-center space-y-5 max-w-md mx-auto mt-10">
              <Award className="h-12 w-12 text-indigo-400 mx-auto" />
              <div className="space-y-1">
                <h3 className="text-lg font-bold text-white">Timed UPSC Prelims MCQ Session</h3>
                <p className="text-xs text-zinc-500 font-mono">Negative marking enabled (1/3rd penalty)</p>
              </div>
              <p className="text-xs text-zinc-450 leading-relaxed">
                Practice official UPSC syllabus questions. Answer explanations, concept links, and difficulty metrics update dynamically.
              </p>
              <button
                onClick={startQuiz}
                className="w-full rounded-lg bg-zinc-100 hover:bg-zinc-200 text-zinc-950 py-3 text-xs font-semibold transition"
              >
                Start Practice Block
              </button>
            </div>
          ) : (
            <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 space-y-6">
              <div className="flex justify-between items-start">
                <div className="space-y-1">
                  <span className="text-[9px] uppercase font-bold font-mono tracking-widest text-indigo-400 bg-indigo-950/40 border border-indigo-900/80 px-2 py-0.5 rounded">
                    {activeQ.subject} • {activeQ.difficulty}
                  </span>
                  <p className="text-sm font-semibold text-white mt-3 leading-relaxed">
                    {activeQ.question}
                  </p>
                </div>

                <button
                  onClick={() => handleToggleBookmark(activeQ.id)}
                  className={`p-2 rounded-lg border border-zinc-800 bg-zinc-950 transition ${
                    bookmarks.includes(activeQ.id) ? "text-yellow-400" : "text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  <Bookmark className="h-4 w-4" />
                </button>
              </div>

              {/* Options selection */}
              <div className="space-y-2">
                {activeQ.options.map((opt, idx) => {
                  const isSelected = selectedOpt === idx;
                  const isCorrectAnswer = idx === activeQ.correctIdx;
                  
                  let borderClass = "border-zinc-850 hover:border-zinc-800 bg-zinc-950/40";
                  if (isSelected) borderClass = "border-indigo-500 bg-indigo-950/20 text-white";
                  if (submitted) {
                    if (isCorrectAnswer) borderClass = "border-emerald-500 bg-emerald-950/20 text-white";
                    else if (isSelected) borderClass = "border-red-500 bg-red-950/20 text-white";
                  }

                  return (
                    <button
                      key={idx}
                      onClick={() => !submitted && setSelectedOpt(idx)}
                      disabled={submitted}
                      className={`w-full flex items-center gap-3 p-3.5 rounded-lg border text-left text-xs transition duration-150 ${borderClass}`}
                    >
                      <span className="font-mono text-zinc-500">{String.fromCharCode(65 + idx)}.</span>
                      <span className="text-zinc-200">{opt}</span>
                    </button>
                  );
                })}
              </div>

              {/* Explanation overlay */}
              {submitted && (
                <div className="p-4 rounded-lg bg-zinc-950 border border-zinc-900 space-y-3">
                  <div className="flex items-start gap-2.5 text-xs text-zinc-300">
                    <HelpCircle className="h-4 w-4 text-indigo-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <h4 className="font-semibold text-white">Answer Explanation</h4>
                      <p className="mt-1 leading-relaxed text-zinc-450">{activeQ.explanation}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-[10px] text-indigo-400 font-mono pt-1">
                    <BookOpen className="h-3.5 w-3.5" /> Concept link: <span>{activeQ.nodeCode}</span>
                  </div>
                </div>
              )}

              {/* Submitting controls */}
              <div className="pt-2">
                {!submitted ? (
                  <button
                    onClick={handleSubmitAnswer}
                    disabled={selectedOpt === null}
                    className="w-full py-3 bg-zinc-100 hover:bg-zinc-200 text-zinc-950 rounded-lg text-xs font-semibold tracking-wider uppercase transition disabled:opacity-50"
                  >
                    Submit Answer
                  </button>
                ) : (
                  <button
                    onClick={handleNextQuestion}
                    className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold tracking-wider uppercase transition"
                  >
                    {currentIndex + 1 < DEMO_QUIZ.length ? "Next Question" : "Complete Block"}
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right Panel: Heatmaps & Mistake Notebook */}
        <div className="space-y-6">
          {/* Subject heatmap */}
          <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 space-y-4">
            <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500 font-mono">Subject Heatmap</h3>
            <div className="grid grid-cols-2 gap-3 pt-1">
              {[
                { subject: "Polity", score: "88% Accuracy", fill: "bg-emerald-950/20 text-emerald-400 border-emerald-900/40" },
                { subject: "Economy", score: "62% Accuracy", fill: "bg-amber-950/20 text-amber-400 border-amber-900/40" },
                { subject: "History", score: "N/A (Unvisited)", fill: "bg-zinc-950 border-zinc-900 text-zinc-600" },
                { subject: "Geography", score: "N/A (Unvisited)", fill: "bg-zinc-950 border-zinc-900 text-zinc-600" },
              ].map((item, idx) => (
                <div key={idx} className={`p-3 rounded-lg border text-center space-y-1.5 ${item.fill}`}>
                  <span className="text-[10px] font-bold block">{item.subject}</span>
                  <span className="text-[9px] font-mono block">{item.score}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Difficulty breakdown */}
          <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 space-y-4">
            <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500 font-mono">Accuracy by Difficulty</h3>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between items-center text-zinc-400">
                <span>Easy</span>
                <span className="text-white font-bold">100%</span>
              </div>
              <div className="w-full bg-zinc-950 h-1.5 rounded overflow-hidden">
                <div className="bg-emerald-500 h-full w-[100%]" />
              </div>

              <div className="flex justify-between items-center text-zinc-400 pt-1">
                <span>Medium</span>
                <span className="text-white font-bold">75%</span>
              </div>
              <div className="w-full bg-zinc-950 h-1.5 rounded overflow-hidden">
                <div className="bg-indigo-500 h-full w-[75%]" />
              </div>

              <div className="flex justify-between items-center text-zinc-400 pt-1">
                <span>Hard</span>
                <span className="text-white font-bold">42%</span>
              </div>
              <div className="w-full bg-zinc-950 h-1.5 rounded overflow-hidden">
                <div className="bg-red-500 h-full w-[42%]" />
              </div>
            </div>
          </div>

          {/* Mistake Notebook */}
          <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 space-y-4">
            <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500 font-mono">Mistake Notebook</h3>
            <div className="space-y-3">
              {mistakes.length > 0 ? (
                mistakes.map((m, idx) => (
                  <div key={idx} className="p-3 bg-zinc-950 border border-zinc-900 rounded-lg space-y-1.5 text-xs">
                    <p className="font-semibold text-white line-clamp-2">{m.question}</p>
                    <p className="text-[10px] text-zinc-500 font-mono">Prereq: {m.nodeCode}</p>
                  </div>
                ))
              ) : (
                <div className="p-4 bg-zinc-950/40 rounded-lg border border-zinc-900 text-center space-y-2">
                  <AlertCircle className="h-7 w-7 text-zinc-650 mx-auto" />
                  <p className="text-xs text-zinc-500 font-mono leading-relaxed">
                    No incorrect answers stored in this review block.
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
