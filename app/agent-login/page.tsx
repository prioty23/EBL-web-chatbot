"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import { useState } from "react";
import type { FormEvent } from "react";

const API_BASE_URL = "http://127.0.0.1:8000";
const AGENT_STORAGE_KEY = "ebl_live_chat_agent";

type AgentProfile = {
  agent_id: string;
  name: string;
  email: string;
  is_active: boolean;
};

type AgentLoginResponse = {
  message: string;
  agent: AgentProfile;
};

async function loginAgent(email: string, password: string) {
  const response = await fetch(`${API_BASE_URL}/agent/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    let detail = "Unable to sign in. Please check your credentials.";

    try {
      const payload = (await response.json()) as { detail?: string };
      detail = payload.detail || detail;
    } catch {
      // Keep the friendly fallback if the API does not return JSON.
    }

    throw new Error(detail);
  }

  return response.json() as Promise<AgentLoginResponse>;
}

export default function AgentLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError("");
    setIsSubmitting(true);

    try {
      const data = await loginAgent(email.trim(), password);
      window.localStorage.setItem(AGENT_STORAGE_KEY, JSON.stringify(data.agent));
      router.replace("/agent-dashboard");
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "Unable to sign in.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[linear-gradient(135deg,#F4F7F6_0%,#E7F0ED_100%)] px-4 py-8 text-[#10231D]">
      <section className="w-full max-w-md overflow-hidden rounded-[8px] border border-[#DCE8E4] bg-white shadow-xl shadow-[#006A4E]/10">
        <div className="bg-gradient-to-r from-[#00543E] via-[#006A4E] to-[#004E3A] px-6 py-6 text-white">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 overflow-hidden">
              <Image
                src="/ebl-logo.png"
                alt="Eastern Bank PLC logo"
                width={1216}
                height={1477}
                priority
                className="h-12 w-12 object-cover object-top"
              />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-emerald-100">
                Eastern Bank PLC.
              </p>
              <h1 className="mt-0.5 text-2xl font-bold leading-tight">
                Agent Login
              </h1>
            </div>
          </div>
          <p className="mt-4 text-sm leading-6 text-emerald-50">
            Sign in to manage EBL live chat support requests.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 px-6 py-6">
          {error ? (
            <div className="rounded-[8px] border border-[#F1C4C4] bg-[#FFF4F4] px-4 py-3 text-sm font-semibold text-[#8A1F1F]">
              {error}
            </div>
          ) : null}

          <div>
            <label htmlFor="agent-email" className="text-sm font-semibold text-[#20332D]">
              Email
            </label>
            <input
              id="agent-email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="support@ebl.com"
              autoComplete="email"
              required
              className="mt-2 min-h-12 w-full rounded-[8px] border border-[#C9D7D3] bg-white px-4 text-sm text-[#20332D] outline-none transition duration-200 placeholder:text-[#8A9894] focus:border-[#006A4E] focus:ring-2 focus:ring-[#006A4E]/10"
            />
          </div>

          <div>
            <label htmlFor="agent-password" className="text-sm font-semibold text-[#20332D]">
              Password
            </label>
            <input
              id="agent-password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter password"
              autoComplete="current-password"
              required
              className="mt-2 min-h-12 w-full rounded-[8px] border border-[#C9D7D3] bg-white px-4 text-sm text-[#20332D] outline-none transition duration-200 placeholder:text-[#8A9894] focus:border-[#006A4E] focus:ring-2 focus:ring-[#006A4E]/10"
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="inline-flex min-h-12 w-full items-center justify-center rounded-full bg-[#006A4E] px-5 text-sm font-bold text-white shadow-md shadow-[#006A4E]/15 transition duration-200 hover:-translate-y-0.5 hover:bg-[#00543E] active:scale-[0.98] disabled:cursor-not-allowed disabled:bg-[#9FB8B0] disabled:shadow-none disabled:hover:translate-y-0 disabled:active:scale-100"
          >
            {isSubmitting ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </section>
    </main>
  );
}
