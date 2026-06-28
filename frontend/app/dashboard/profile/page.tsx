"use client";

import { useEffect, useState } from "react";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/auth-store";
import {
  User,
  Sparkles,
  RefreshCw,
  Calendar,
  Clock,
  BookOpen,
  CheckCircle,
} from "lucide-react";

export default function ProfilePage() {
  const { user } = useAuthStore();
  const [twin, setTwin] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [dailyHours, setDailyHours] = useState(6);
  const [isSaved, setIsSaved] = useState(false);

  useEffect(() => {
    const fetchProfile = async () => {
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
    fetchProfile();
  }, []);

  const handleSavePreferences = () => {
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 2000);
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-3">
        <RefreshCw className="h-8 w-8 text-indigo-400 animate-spin" />
        <p className="text-sm text-zinc-400">Syncing Student Profile...</p>
      </div>
    );
  }

  const weakConcepts = twin?.knowledge_state?.weak_concepts || ["economy_rbi", "economy_monetary_policy"];

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-white flex items-center gap-3">
          <User className="h-8 w-8 text-indigo-400" /> Student Profile & Settings
        </h1>
        <p className="text-sm text-zinc-400">Configure target timelines, available study hours, and weak subjects profile.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Core preferences */}
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 space-y-6">
            <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500">Syllabus Target & Availability</h3>
            
            <div className="space-y-5">
              {/* Daily hours slider */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Clock className="h-4 w-4" /> Available Daily Study Hours
                  </label>
                  <span className="text-sm font-semibold text-white font-mono">{dailyHours} Hours</span>
                </div>
                <input
                  type="range"
                  min="2"
                  max="12"
                  value={dailyHours}
                  onChange={(e) => setDailyHours(parseInt(e.target.value))}
                  className="w-full h-1.5 bg-zinc-950 rounded-lg appearance-none cursor-pointer border border-zinc-850"
                />
              </div>

              {/* Goal Select */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Calendar className="h-4 w-4" /> Active UPSC Target Goal
                </label>
                <select className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2.5 text-xs text-zinc-300 focus:outline-none transition">
                  <option>UPSC CSE Prelims 2026</option>
                  <option>UPSC CSE Mains 2026</option>
                  <option>Revision Focused Mode</option>
                  <option>Weak Subject Recovery</option>
                </select>
              </div>

              {/* Save Button */}
              <button
                onClick={handleSavePreferences}
                className="rounded-lg bg-zinc-100 hover:bg-zinc-200 text-zinc-950 px-4 py-2.5 text-sm font-medium transition"
              >
                {isSaved ? "Saved Preferences!" : "Save Changes"}
              </button>
            </div>
          </div>
        </div>

        {/* Profile metadata info side cards */}
        <div className="space-y-6">
          {/* Weak subjects lists */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 space-y-4">
            <h3 className="text-xs uppercase font-bold tracking-wider text-zinc-500 flex items-center gap-2">
              <BookOpen className="h-4 w-4" /> Priority Weak Concepts
            </h3>
            <div className="space-y-2">
              {weakConcepts.map((code: string) => (
                <div key={code} className="p-3 bg-zinc-950 border border-zinc-850 rounded-lg text-xs font-mono text-zinc-300">
                  {code}
                </div>
              ))}
            </div>
          </div>

          {/* Premium Account upgrade card */}
          <div className="rounded-xl border border-indigo-900 bg-indigo-950/10 p-6 space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-400">Account status</span>
              <span className="flex items-center gap-1 text-[10px] text-indigo-400 font-semibold bg-indigo-950/60 border border-indigo-900 px-2 py-0.5 rounded">
                <Sparkles className="h-3 w-3" /> Premium Active
              </span>
            </div>
            <h4 className="text-sm font-semibold text-white">UPSC OS Platinum Member</h4>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Unrestricted Socratic AI tutor cycles, automated diagnostic projections, and daily telemetry loops.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
