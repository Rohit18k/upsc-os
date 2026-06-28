"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useRouter } from "next/navigation";
import { authService } from "@/services/auth";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/auth-store";
import { Sparkles, Loader2, ArrowRight } from "lucide-react";

const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const router = useRouter();
  const { setTokens, setUser } = useAuthStore();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const response = await authService.login(data);
      setTokens(response.tokens.accessToken, response.tokens.refreshToken);
      setUser(response.user);
      router.push("/dashboard");
    } catch (err: any) {
      setErrorMsg(err.message || "Invalid email or password");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setDemoLoading(true);
    setErrorMsg(null);
    const demoEmail = "demo_student@upscos.io";
    const demoPassword = "password123";

    try {
      // 1. Try registering the demo student (ignore if exists)
      try {
        await authService.register({
          email: demoEmail,
          password: demoPassword,
          fullName: "Demo Student",
        });
      } catch (e) {
        // Assume student already registered
      }

      // 2. Perform Login
      const response = await authService.login({
        email: demoEmail,
        password: demoPassword,
      });
      setTokens(response.tokens.accessToken, response.tokens.refreshToken);
      setUser(response.user);

      // 3. Seed UPSC Knowledge Graph and Digital Twin Telemetry via real events
      const authHeaders = { Authorization: `Bearer ${response.tokens.accessToken}` };
      
      // Seed first Polity knowledge node in database if not present
      try {
        // Seed nodes
        await api.post("/api/v1/student/events", {
          event_type: "DocumentUploaded",
          payload: {
            topics: ["polity", "polity_basics", "polity_basics_preamble", "polity_basics_fr", "economy", "economy_inflation", "economy_monetary_policy", "economy_rbi"]
          }
        }, { headers: authHeaders });

        await api.post("/api/v1/student/events", {
          event_type: "LessonCompleted",
          payload: {
            node_code: "polity_basics_preamble",
            confidence: 0.8,
            difficulty: 0.3,
            time_spent: 900.0,
            content_type: "text"
          }
        }, { headers: authHeaders });

        await api.post("/api/v1/student/events", {
          event_type: "PYQSolved",
          payload: {
            questions: [
              { node_code: "polity_basics_preamble", correct: true, difficulty: 0.4 },
              { node_code: "polity_basics_preamble", correct: true, difficulty: 0.4 },
              { node_code: "polity_basics_preamble", correct: false, difficulty: 0.5, error_category: "conceptual_gap" }
            ],
            time_spent: 600.0
          }
        }, { headers: authHeaders });

        await api.post("/api/v1/student/events", {
          event_type: "RevisionCompleted",
          payload: {
            node_code: "polity_basics_preamble",
            rating: 4,
            time_spent: 300.0
          }
        }, { headers: authHeaders });
      } catch (seedErr) {
        // Seeding issues are non-blocking
      }

      router.push("/dashboard");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to initialize demo session");
    } finally {
      setDemoLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-950 text-zinc-50 font-sans selection:bg-zinc-800">
      <div className="w-full max-w-md space-y-8 px-8 py-10 rounded-2xl border border-zinc-800 bg-zinc-900/40 backdrop-blur-md shadow-2xl">
        <div className="text-center space-y-2">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-zinc-800/80 border border-zinc-700 text-zinc-200">
            <Sparkles className="h-6 w-6 text-indigo-400" />
          </div>
          <h1 className="text-3xl font-semibold tracking-tight text-white">UPSC OS</h1>
          <p className="text-sm text-zinc-400">One Platform. Absolute Mastery.</p>
        </div>

        {errorMsg && (
          <div className="rounded-lg bg-red-950/40 border border-red-900/60 p-3 text-sm text-red-200 text-center">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          <div className="space-y-1.5">
            <label htmlFor="email" className="text-xs font-medium uppercase tracking-wider text-zinc-400">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              {...register("email")}
              className="w-full rounded-lg border border-zinc-800 bg-zinc-950/80 px-3 py-2.5 text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition"
              placeholder="student@upscos.io"
            />
            {errors.email && (
              <p className="text-xs text-red-400 mt-1">{errors.email.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <label htmlFor="password" className="text-xs font-medium uppercase tracking-wider text-zinc-400">
              Password
            </label>
            <input
              id="password"
              type="password"
              {...register("password")}
              className="w-full rounded-lg border border-zinc-800 bg-zinc-950/80 px-3 py-2.5 text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition"
              placeholder="••••••••"
            />
            {errors.password && (
              <p className="text-xs text-red-400 mt-1">{errors.password.message}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading || demoLoading}
            className="w-full rounded-lg bg-zinc-100 hover:bg-zinc-200 text-zinc-950 px-4 py-2.5 text-sm font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" /> Signing in...
              </>
            ) : (
              "Sign in to Dashboard"
            )}
          </button>
        </form>

        <div className="relative flex py-2 items-center">
          <div className="flex-grow border-t border-zinc-800"></div>
          <span className="flex-shrink mx-4 text-zinc-500 text-xs font-semibold uppercase tracking-wider">or</span>
          <div className="flex-grow border-t border-zinc-800"></div>
        </div>

        <button
          onClick={handleDemoLogin}
          disabled={isLoading || demoLoading}
          className="w-full rounded-lg border border-zinc-800 bg-zinc-950 hover:bg-zinc-900 hover:border-zinc-700 text-indigo-400 px-4 py-2.5 text-sm font-medium transition-all duration-200 disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {demoLoading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin text-indigo-400" />
              <span>Seeding telemetry & logging in...</span>
            </>
          ) : (
            <>
              <span>Instant Demo Account Login</span>
              <ArrowRight className="h-4 w-4" />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
