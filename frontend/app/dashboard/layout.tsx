"use client";

import React, { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuthStore } from "@/store/auth-store";
import { useTheme } from "next-themes";
import { api } from "@/services/api";
import {
  Compass,
  BookOpen,
  RefreshCw,
  Award,
  TrendingUp,
  MessageSquare,
  User,
  LogOut,
  Sun,
  Moon,
  Search,
  Settings,
  Sparkles,
  Command,
} from "lucide-react";

interface SidebarItem {
  name: string;
  href: string;
  icon: React.ComponentType<any>;
  shortcut: string;
}

const SIDEBAR_ITEMS: SidebarItem[] = [
  { name: "Mission Control", href: "/dashboard", icon: Compass, shortcut: "G + M" },
  { name: "Learn", href: "/dashboard/learn", icon: BookOpen, shortcut: "G + L" },
  { name: "Revise", href: "/dashboard/revise", icon: RefreshCw, shortcut: "G + R" },
  { name: "Practice", href: "/dashboard/practice", icon: Award, shortcut: "G + P" },
  { name: "Improve", href: "/dashboard/improve", icon: TrendingUp, shortcut: "G + I" },
  { name: "AI Tutor", href: "/dashboard/tutor", icon: MessageSquare, shortcut: "G + T" },
  { name: "Profile", href: "/dashboard/profile", icon: User, shortcut: "G + S" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { accessToken, logout, user } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Command palette state
  const [isCommandOpen, setIsCommandOpen] = useState(false);
  const [commandQuery, setCommandQuery] = useState("");

  // Ensure themed components are rendered only after client mount
  useEffect(() => {
    setMounted(true);
  }, []);

  // Redirect check
  useEffect(() => {
    if (!accessToken) {
      router.push("/login");
    }
  }, [accessToken, router]);

  // Keyboard Shortcuts Listener
  useEffect(() => {
    let lastKey = "";
    const handleKeyDown = (e: KeyboardEvent) => {
      // Toggle Command Palette (CMD + K / Ctrl + K)
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsCommandOpen((prev) => !prev);
        return;
      }

      // Escape to close Command Palette
      if (e.key === "Escape") {
        setIsCommandOpen(false);
        return;
      }

      // Check for navigation shortcuts (e.g., G followed by key)
      const key = e.key.toLowerCase();
      if (lastKey === "g") {
        let targetHref = "";
        if (key === "m") targetHref = "/dashboard";
        else if (key === "l") targetHref = "/dashboard/learn";
        else if (key === "r") targetHref = "/dashboard/revise";
        else if (key === "p") targetHref = "/dashboard/practice";
        else if (key === "i") targetHref = "/dashboard/improve";
        else if (key === "t") targetHref = "/dashboard/tutor";
        else if (key === "s") targetHref = "/dashboard/profile";

        if (targetHref) {
          e.preventDefault();
          router.push(targetHref);
          lastKey = "";
          return;
        }
      }
      lastKey = key;
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [router]);

  if (!mounted || !accessToken) {
    return (
      <div className="flex h-screen items-center justify-center bg-zinc-950 text-indigo-400">
        <RefreshCw className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  const handleRecalculatePlan = async () => {
    try {
      await api.post("/api/v1/optimization/recalculate");
      await api.post("/api/v1/missions/recalculate");
      setIsCommandOpen(false);
      window.location.reload(); // Refresh data immediately
    } catch (e) {
      alert("Failed to recalculate optimizations.");
    }
  };

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  // Filter commands for palette
  const filteredCommands = SIDEBAR_ITEMS.filter((item) =>
    item.name.toLowerCase().includes(commandQuery.toLowerCase())
  );

  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-100 font-sans selection:bg-zinc-800">
      {/* Sidebar navigation */}
      <aside className="w-64 border-r border-zinc-800 bg-zinc-900/20 flex flex-col justify-between p-5">
        <div className="space-y-8">
          {/* Logo & Meta title */}
          <div className="flex items-center gap-3 px-2">
            <Sparkles className="h-5 w-5 text-indigo-400" />
            <span className="font-semibold tracking-wide text-white uppercase text-sm">UPSC OS v0.1</span>
          </div>

          {/* Quick command search trigger */}
          <button
            onClick={() => setIsCommandOpen(true)}
            className="w-full flex items-center justify-between px-3 py-2 bg-zinc-900/60 border border-zinc-800 rounded-lg text-xs text-zinc-400 hover:border-zinc-700 hover:text-zinc-200 transition"
          >
            <span className="flex items-center gap-2">
              <Search className="h-3.5 w-3.5" />
              Search & Commands...
            </span>
            <kbd className="px-1.5 py-0.5 rounded bg-zinc-800 text-[10px] text-zinc-500 font-mono border border-zinc-700">⌘K</kbd>
          </button>

          {/* Sidebar Menu items */}
          <nav className="space-y-1">
            {SIDEBAR_ITEMS.map((item) => {
              const isActive = pathname === item.href;
              return (
                <button
                  key={item.href}
                  onClick={() => router.push(item.href)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition duration-150 ${
                    isActive
                      ? "bg-zinc-800/80 text-white border border-zinc-700"
                      : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/50"
                  }`}
                >
                  <span className="flex items-center gap-3">
                    <item.icon className={`h-4.5 w-4.5 ${isActive ? "text-indigo-400" : "text-zinc-500"}`} />
                    {item.name}
                  </span>
                  <span className="text-[10px] font-mono text-zinc-600 hidden group-hover:block">{item.shortcut}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* User profile footer */}
        <div className="border-t border-zinc-800 pt-4 flex flex-col gap-3">
          <div className="flex items-center gap-3 px-2">
            <div className="h-8 w-8 rounded-full bg-zinc-800 flex items-center justify-center text-sm font-semibold text-indigo-400 border border-zinc-700">
              {user?.fullName?.charAt(0) || "S"}
            </div>
            <div className="truncate">
              <p className="text-xs font-semibold text-zinc-200 truncate">{user?.fullName || "Student"}</p>
              <p className="text-[10px] text-zinc-500 truncate">{user?.email}</p>
            </div>
          </div>

          <div className="flex gap-2">
            {/* Theme toggle */}
            <button
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="flex-1 flex justify-center py-2 bg-zinc-900/60 border border-zinc-800 rounded-lg hover:bg-zinc-800/80 hover:border-zinc-700 transition"
              title="Toggle Theme"
            >
              {theme === "dark" ? <Sun className="h-4 w-4 text-zinc-400" /> : <Moon className="h-4 w-4 text-zinc-400" />}
            </button>
            {/* Logout button */}
            <button
              onClick={handleLogout}
              className="flex-1 flex justify-center py-2 bg-red-950/20 border border-red-900/40 text-red-400 rounded-lg hover:bg-red-950/40 hover:border-red-900/60 transition"
              title="Sign Out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main page content area */}
      <main className="flex-1 flex flex-col overflow-hidden bg-zinc-950 text-zinc-100">
        <div className="flex-1 overflow-y-auto px-10 py-8 bg-gradient-to-b from-zinc-900/10 to-zinc-950">
          <div className="max-w-6xl mx-auto space-y-8">
            {children}
          </div>
        </div>
      </main>

      {/* COMMAND PALETTE MODAL (CMD + K) */}
      {isCommandOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] px-4 bg-zinc-950/80 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-xl border border-zinc-850 bg-zinc-900 shadow-2xl overflow-hidden animate-in fade-in duration-200">
            {/* Search Input */}
            <div className="flex items-center gap-3 px-4 border-b border-zinc-800">
              <Command className="h-4 w-4 text-zinc-400" />
              <input
                type="text"
                placeholder="Search tabs, commands or actions..."
                value={commandQuery}
                onChange={(e) => setCommandQuery(e.target.value)}
                className="w-full py-4 bg-transparent text-sm focus:outline-none text-zinc-100 placeholder-zinc-500"
                autoFocus
              />
            </div>

            {/* List Option Commands */}
            <div className="p-2 max-h-72 overflow-y-auto space-y-1">
              <div className="px-3 py-1 text-[10px] uppercase font-bold tracking-wider text-zinc-500">Navigation</div>
              {filteredCommands.map((item) => (
                <button
                  key={item.href}
                  onClick={() => {
                    router.push(item.href);
                    setIsCommandOpen(false);
                  }}
                  className="w-full flex items-center justify-between px-3 py-2 text-sm text-zinc-300 hover:text-white hover:bg-zinc-850 rounded-lg transition"
                >
                  <span className="flex items-center gap-3">
                    <item.icon className="h-4 w-4 text-zinc-400" />
                    {item.name}
                  </span>
                  <span className="text-[10px] font-mono text-zinc-500">{item.shortcut}</span>
                </button>
              ))}

              <div className="px-3 py-2 border-t border-zinc-800/80 mt-2 text-[10px] uppercase font-bold tracking-wider text-zinc-500">Actions</div>
              <button
                onClick={handleRecalculatePlan}
                className="w-full flex items-center gap-3 px-3 py-2 text-sm text-indigo-400 hover:text-indigo-300 hover:bg-zinc-850 rounded-lg transition text-left"
              >
                <RefreshCw className="h-4 w-4" />
                Recalculate Study Plan & Mission
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
