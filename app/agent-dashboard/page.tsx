"use client";

import Image from "next/image";
import { useCallback, useEffect, useMemo, useState } from "react";
import type { FormEvent, ReactNode } from "react";

const API_BASE_URL = "http://127.0.0.1:8000";
const AGENT_ID = "ebl-support-agent";
const AGENT_NAME = "EBL Support Agent";

type LiveChatSession = {
  id: number;
  support_session_id: string;
  chat_session_id: string;
  customer_name: string;
  customer_phone: string;
  status: string;
  agent_id: string;
  created_at: string;
  accepted_at: string;
  ended_at: string;
  updated_at: string;
  feedback?: string;
  feedback_at?: string;
};

type LiveChatMessage = {
  id: number;
  support_session_id: string;
  sender_type: string;
  sender_id: string;
  message: string;
  created_at: string;
};

type SessionListResponse = {
  sessions: LiveChatSession[];
};

type SessionResponse = {
  session: LiveChatSession | null;
};

type MessagesResponse = {
  session: LiveChatSession;
  messages: LiveChatMessage[];
};

type IconProps = {
  className?: string;
};

function classNames(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

function parseBackendDate(value: string) {
  if (!value) {
    return null;
  }

  const parsedDate = new Date(value.replace(" ", "T"));

  if (Number.isNaN(parsedDate.getTime())) {
    return null;
  }

  return parsedDate;
}

function formatTime(value: string) {
  const parsedDate = parseBackendDate(value);

  if (!parsedDate) {
    return "Not available";
  }

  return parsedDate.toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatClock(value: string) {
  const parsedDate = parseBackendDate(value);

  if (!parsedDate) {
    return "";
  }

  return parsedDate.toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatWaitTime(value: string) {
  const parsedDate = parseBackendDate(value);

  if (!parsedDate) {
    return "Waiting";
  }

  const minutes = Math.max(0, Math.floor((Date.now() - parsedDate.getTime()) / 60000));

  if (minutes < 1) {
    return "Waiting now";
  }

  if (minutes < 60) {
    return `Waiting ${minutes} min`;
  }

  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;

  return `Waiting ${hours}h ${remainingMinutes}m`;
}

function getInitials(name: string) {
  const words = (name || "Customer").trim().split(/\s+/).filter(Boolean);

  return words
    .slice(0, 2)
    .map((word) => word[0]?.toUpperCase())
    .join("") || "C";
}

function getStatusStyle(status: string) {
  const normalizedStatus = status.toLowerCase();

  if (normalizedStatus === "active") {
    return "border-[#BFE8D5] bg-[#E8F8F0] text-[#006A4E]";
  }

  if (normalizedStatus === "ended") {
    return "border-[#D9DFE2] bg-[#F3F6F7] text-[#4B5B60]";
  }

  return "border-[#F1D78D] bg-[#FFF8D8] text-[#6F5200]";
}

async function readApi<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });

  if (!response.ok) {
    let detail = "Request failed. Please try again.";

    try {
      const payload = (await response.json()) as { detail?: string };
      detail = payload.detail || detail;
    } catch {
      // Keep the friendly fallback if the API does not return JSON.
    }

    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

function QueueIcon({ className = "" }: IconProps) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M7 8h10M7 12h7M7 16h10"
        stroke="currentColor"
        strokeLinecap="round"
        strokeWidth="1.8"
      />
      <path
        d="M4 5.5A1.5 1.5 0 0 1 5.5 4h13A1.5 1.5 0 0 1 20 5.5v13a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 18.5v-13Z"
        stroke="currentColor"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function ChatIcon({ className = "" }: IconProps) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M5 17.5V7a3 3 0 0 1 3-3h8a3 3 0 0 1 3 3v6a3 3 0 0 1-3 3H9l-4 3.5Z"
        stroke="currentColor"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
      <path d="M8.5 8.5h7M8.5 12h4.5" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" />
    </svg>
  );
}

function UserIcon({ className = "" }: IconProps) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM4.5 20a7.5 7.5 0 0 1 15 0"
        stroke="currentColor"
        strokeLinecap="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function PhoneIcon({ className = "" }: IconProps) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M8.5 5.5 10 8.8a1.5 1.5 0 0 1-.3 1.7l-.9.9a10.5 10.5 0 0 0 3.8 3.8l.9-.9a1.5 1.5 0 0 1 1.7-.3l3.3 1.5a1.4 1.4 0 0 1 .8 1.6l-.5 2.2A1.7 1.7 0 0 1 17.1 21 14.1 14.1 0 0 1 3 6.9a1.7 1.7 0 0 1 1.3-1.7l2.2-.5a1.4 1.4 0 0 1 2 1Z"
        stroke="currentColor"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function ClockIcon({ className = "" }: IconProps) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 7v5l3 2" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" />
      <path d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" stroke="currentColor" strokeWidth="1.8" />
    </svg>
  );
}

function SendIcon({ className = "" }: IconProps) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="m4 12 16-7-6 14-3-5-7-2Z"
        stroke="currentColor"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function PowerIcon({ className = "" }: IconProps) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 3v8" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" />
      <path d="M7.2 6.8a7 7 0 1 0 9.6 0" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" />
    </svg>
  );
}

function StatusBadge({ status }: { status: string }) {
  return (
    <span className={classNames("inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold capitalize", getStatusStyle(status))}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {status || "unknown"}
    </span>
  );
}

function MetricCard({
  icon,
  label,
  value,
  helper,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  helper: string;
}) {
  return (
    <div className="agent-dashboard-card rounded-[8px] border border-[#DCE8E4] bg-white px-4 py-3 shadow-sm">
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#E8F8F0] text-[#006A4E]">
          {icon}
        </span>
        <div className="min-w-0">
          <p className="text-xs font-medium text-[#667570]">{label}</p>
          <p className="mt-0.5 truncate text-xl font-bold text-[#10231D]">{value}</p>
        </div>
      </div>
      <p className="mt-3 text-xs leading-5 text-[#667570]">{helper}</p>
    </div>
  );
}

function DetailRow({
  icon,
  label,
  value,
}: {
  icon: ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex min-w-0 items-start gap-3 border-b border-[#EEF2F1] py-3 last:border-b-0">
      <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#F1F7F5] text-[#006A4E]">
        {icon}
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-semibold uppercase tracking-[0.06em] text-[#7C8A86]">{label}</p>
        <p className="mt-1 break-words text-sm font-semibold leading-5 text-[#20332D] [overflow-wrap:anywhere]">
          {value || "Not available"}
        </p>
      </div>
    </div>
  );
}

export default function AgentDashboardPage() {
  const [waitingSessions, setWaitingSessions] = useState<LiveChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<LiveChatSession | null>(null);
  const [selectedSession, setSelectedSession] = useState<LiveChatSession | null>(null);
  const [messages, setMessages] = useState<LiveChatMessage[]>([]);
  const [draftMessage, setDraftMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [isAgentAvailable, setIsAgentAvailable] = useState(true);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const selectedSessionId = selectedSession?.support_session_id || "";
  const canSendMessage = selectedSession?.status === "active" && draftMessage.trim().length > 0;

  const queueSummary = useMemo(() => {
    if (activeSession) {
      return "One active support chat is in progress.";
    }

    if (waitingSessions.length === 0) {
      return "No customer is waiting right now.";
    }

    return `${waitingSessions.length} customer${waitingSessions.length > 1 ? "s are" : " is"} waiting.`;
  }, [activeSession, waitingSessions.length]);

  const selectedCustomerName = selectedSession?.customer_name || "No customer selected";
  const hasActiveChat = Boolean(activeSession);

  const loadMessages = useCallback(async (supportSessionId: string) => {
    const data = await readApi<MessagesResponse>(
      `/live-chat/sessions/${encodeURIComponent(supportSessionId)}/messages?limit=100`,
    );

    setSelectedSession(data.session);
    setMessages(data.messages);
  }, []);

  const refreshDashboard = useCallback(async () => {
    try {
      const [waitingData, activeData] = await Promise.all([
        readApi<SessionListResponse>("/live-chat/sessions/waiting?limit=50"),
        readApi<SessionResponse>("/live-chat/sessions/active"),
      ]);

      setWaitingSessions(waitingData.sessions);
      setActiveSession(activeData.session);

      if (activeData.session) {
        setSelectedSession((currentSession) => currentSession || activeData.session);
      }

      setError("");
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "Unable to load dashboard.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const initialRefreshTimer = window.setTimeout(() => {
      void refreshDashboard();
    }, 0);

    const refreshTimer = window.setInterval(() => {
      void refreshDashboard();
    }, 5000);

    return () => {
      window.clearTimeout(initialRefreshTimer);
      window.clearInterval(refreshTimer);
    };
  }, [refreshDashboard]);

  useEffect(() => {
    if (!selectedSessionId) {
      return;
    }

    const initialMessageTimer = window.setTimeout(() => {
      void loadMessages(selectedSessionId).catch((currentError) => {
        setError(currentError instanceof Error ? currentError.message : "Unable to load messages.");
      });
    }, 0);

    const messageTimer = window.setInterval(() => {
      void loadMessages(selectedSessionId).catch((currentError) => {
        setError(currentError instanceof Error ? currentError.message : "Unable to load messages.");
      });
    }, 2500);

    return () => {
      window.clearTimeout(initialMessageTimer);
      window.clearInterval(messageTimer);
    };
  }, [loadMessages, selectedSessionId]);

  async function acceptSession(session: LiveChatSession) {
    setError("");
    setNotice("");

    if (!isAgentAvailable) {
      setError("Set your status to Online before accepting a customer chat.");
      return;
    }

    try {
      const data = await readApi<SessionResponse>(
        `/live-chat/sessions/${encodeURIComponent(session.support_session_id)}/accept`,
        {
          method: "POST",
          body: JSON.stringify({ agent_id: AGENT_ID }),
        },
      );

      setActiveSession(data.session);
      setSelectedSession(data.session);
      setNotice("Chat accepted. You can now reply to the customer.");
      await refreshDashboard();
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "Unable to accept chat.");
    }
  }

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!selectedSession || !canSendMessage) {
      return;
    }

    const nextMessage = draftMessage.trim();
    setIsSending(true);
    setError("");

    try {
      await readApi(
        `/live-chat/sessions/${encodeURIComponent(selectedSession.support_session_id)}/messages`,
        {
          method: "POST",
          body: JSON.stringify({
            sender_type: "agent",
            sender_id: AGENT_ID,
            message: nextMessage,
          }),
        },
      );

      setDraftMessage("");
      await loadMessages(selectedSession.support_session_id);
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "Unable to send message.");
    } finally {
      setIsSending(false);
    }
  }

  async function endSession() {
    if (!selectedSession) {
      return;
    }

    setError("");
    setNotice("");

    try {
      const data = await readApi<SessionResponse>(
        `/live-chat/sessions/${encodeURIComponent(selectedSession.support_session_id)}/end`,
        {
          method: "POST",
          body: JSON.stringify({ ended_by: AGENT_ID }),
        },
      );

      setSelectedSession(data.session);
      setActiveSession(null);
      setNotice("Chat session ended.");
      await refreshDashboard();
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "Unable to end chat.");
    }
  }

  return (
    <>
      <style jsx global>{`
        @keyframes agent-dashboard-in {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes agent-message-in {
          from {
            opacity: 0;
            transform: translateY(8px) scale(0.985);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }

        @keyframes agent-pulse {
          0% {
            box-shadow: 0 0 0 0 rgba(0, 106, 78, 0.28);
          }
          70% {
            box-shadow: 0 0 0 12px rgba(0, 106, 78, 0);
          }
          100% {
            box-shadow: 0 0 0 0 rgba(0, 106, 78, 0);
          }
        }

        .agent-dashboard-card {
          animation: agent-dashboard-in 220ms ease-out both;
        }

        .agent-message {
          animation: agent-message-in 180ms ease-out both;
        }

        .agent-new-session {
          animation: agent-pulse 1.8s ease-out infinite;
        }

        @media (prefers-reduced-motion: reduce) {
          .agent-dashboard-card,
          .agent-message,
          .agent-new-session {
            animation: none;
          }
        }
      `}</style>

      <main className="min-h-screen bg-[#F4F7F6] text-[#10231D]">
        <header className="bg-gradient-to-r from-[#00543E] via-[#006A4E] to-[#004E3A] px-4 py-3 text-white shadow-lg shadow-[#006A4E]/20 sm:px-6 lg:px-8">
          <div className="mx-auto flex w-full max-w-7xl flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex min-w-0 items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden">
                <Image
                  src="/ebl-logo.png"
                  alt="Eastern Bank PLC logo"
                  width={1216}
                  height={1477}
                  priority
                  className="h-10 w-10 object-cover object-top"
                />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold uppercase tracking-[0.12em] text-emerald-100">
                  Eastern Bank PLC.
                </p>
                <h1 className="mt-0.5 text-xl font-bold leading-tight sm:text-2xl">
                  EBL Live Chat Support
                </h1>
              </div>
            </div>

            <div className="w-full rounded-[8px] border border-white/15 bg-white/[0.08] px-4 py-2 text-sm shadow-sm backdrop-blur lg:w-[330px]">
              <div className="flex items-center justify-between gap-4">
                <div className="min-w-0">
                  <p className="text-xs font-medium text-emerald-50/75">Signed in as</p>
                  <p className="mt-0.5 truncate text-sm font-bold text-white">{AGENT_NAME}</p>
                </div>
                <button
                  type="button"
                  onClick={() => setIsAgentAvailable((currentValue) => !currentValue)}
                  className={classNames(
                    "inline-flex min-h-8 shrink-0 items-center gap-2 rounded-full border px-3 text-xs font-bold transition duration-200 active:scale-[0.98]",
                    isAgentAvailable
                      ? "border-[#76E6A6]/45 bg-[#E8F8F0] text-[#00543E] hover:bg-white"
                      : "border-white/20 bg-white/10 text-emerald-50 hover:bg-white/15",
                  )}
                  aria-pressed={isAgentAvailable}
                >
                  <span
                    className={classNames(
                      "h-2.5 w-2.5 rounded-full",
                      isAgentAvailable ? "bg-[#14B86A]" : "bg-[#BAC7C2]",
                    )}
                  />
                  {isAgentAvailable ? "Online" : "Offline"}
                </button>
              </div>
              <p className="mt-2 text-xs font-medium text-emerald-50/75">
                {isAgentAvailable ? "Ready to accept customer chats." : "Not accepting new chats right now."}
              </p>
            </div>
          </div>
        </header>

        <div className="mx-auto flex w-full max-w-7xl flex-col gap-5 px-4 py-5 sm:px-6 lg:px-8">
          <section className="grid gap-3 sm:grid-cols-3">
            <MetricCard
              icon={<QueueIcon className="h-5 w-5" />}
              label="Waiting Queue"
              value={String(waitingSessions.length)}
              helper={queueSummary}
            />
            <MetricCard
              icon={<ChatIcon className="h-5 w-5" />}
              label="Active Chat"
              value={hasActiveChat ? "1" : "0"}
              helper={hasActiveChat ? "One customer is connected." : "No active conversation."}
            />
            <MetricCard
              icon={<UserIcon className="h-5 w-5" />}
              label="Selected Customer"
              value={selectedSession ? selectedCustomerName : "-"}
              helper={selectedSession ? `Status: ${selectedSession.status}` : "Choose a customer to begin."}
            />
          </section>

          {(error || notice) && (
            <section
              className={classNames(
                "agent-dashboard-card rounded-[8px] border px-4 py-3 text-sm font-semibold shadow-sm",
                error
                  ? "border-[#F1C4C4] bg-[#FFF4F4] text-[#8A1F1F]"
                  : "border-[#C8D8DD] bg-[#EEF4F6] text-[#223A42]",
              )}
            >
              {error || notice}
            </section>
          )}

          <section className="grid min-h-[680px] gap-5 xl:grid-cols-[330px_minmax(0,1fr)_320px]">
            <aside className="agent-dashboard-card flex min-h-[520px] flex-col overflow-hidden rounded-[8px] border border-[#DCE8E4] bg-white shadow-sm">
              <div className="flex items-center justify-between border-b border-[#E5EFEC] bg-white px-5 py-4">
                <div className="min-w-0">
                  <h2 className="text-base font-bold text-[#10231D]">Queue</h2>
                  <p className="mt-1 text-xs text-[#667570]">Oldest requests appear first.</p>
                </div>
                <span className="inline-flex h-8 min-w-8 items-center justify-center rounded-full bg-[#006A4E] px-2 text-sm font-bold text-white">
                  {waitingSessions.length}
                </span>
              </div>

              <div className="min-h-0 flex-1 overflow-y-auto p-3">
                {isLoading ? (
                  <p className="rounded-[8px] border border-dashed border-[#D1DFDB] bg-[#F8FBFA] px-4 py-6 text-sm text-[#667570]">
                    Loading support queue...
                  </p>
                ) : waitingSessions.length === 0 ? (
                  <div className="rounded-[8px] border border-dashed border-[#D1DFDB] bg-[#F8FBFA] px-4 py-8 text-center text-sm leading-6 text-[#667570]">
                    No waiting customer right now.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {waitingSessions.map((session, index) => {
                      const isSelected = selectedSessionId === session.support_session_id;

                      return (
                        <div
                          key={session.support_session_id}
                          className={classNames(
                            "group relative w-full rounded-[8px] border p-4 text-left transition duration-200 hover:-translate-y-0.5 hover:border-[#006A4E]/70 hover:bg-[#F5FBF8] hover:shadow-md",
                            isSelected
                              ? "border-[#006A4E] bg-[#EFFAF5] shadow-sm"
                              : "border-[#E2ECE9] bg-white",
                            index === 0 ? "agent-new-session" : "",
                          )}
                        >
                          <button
                            type="button"
                            onClick={() => {
                              setMessages([]);
                              setSelectedSession(session);
                            }}
                            className="block w-full text-left"
                          >
                            <div className="flex min-w-0 items-start gap-3">
                              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-[#DDEFE8] text-sm font-bold text-[#006A4E] ring-1 ring-[#006A4E]/10">
                                {getInitials(session.customer_name)}
                              </div>
                              <div className="min-w-0 flex-1">
                                <div className="flex min-w-0 items-start justify-between gap-2">
                                  <div className="min-w-0">
                                    <p className="truncate text-sm font-bold text-[#10231D]">
                                      {session.customer_name || "Customer"}
                                    </p>
                                    <p className="mt-1 break-words text-xs font-medium text-[#667570]">
                                      {session.customer_phone || "No phone"}
                                    </p>
                                  </div>
                                  <span className="rounded-full bg-[#FFF8D8] px-2.5 py-1 text-[11px] font-bold text-[#6F5200]">
                                    New
                                  </span>
                                </div>

                                <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-[#667570]">
                                  <ClockIcon className="h-3.5 w-3.5" />
                                  <span>{formatWaitTime(session.created_at)}</span>
                                </div>
                              </div>
                            </div>
                          </button>

                          <button
                            type="button"
                            onClick={() => {
                              void acceptSession(session);
                            }}
                            disabled={!isAgentAvailable}
                            className="ml-[60px] mt-4 inline-flex min-h-9 items-center justify-center rounded-full bg-[#006A4E] px-4 text-xs font-bold text-white shadow-sm transition duration-200 hover:bg-[#00543E] active:scale-[0.98] disabled:cursor-not-allowed disabled:bg-[#9FB8B0] disabled:hover:bg-[#9FB8B0]"
                          >
                            Accept
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </aside>

            <section className="agent-dashboard-card flex min-h-[620px] min-w-0 flex-col overflow-hidden rounded-[8px] border border-[#DCE8E4] bg-white shadow-sm">
              {selectedSession ? (
                <>
                  <div className="flex flex-col gap-4 border-b border-[#E5EFEC] bg-white px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="h-2.5 w-2.5 rounded-full bg-[#006A4E]" />
                        <h2 className="text-base font-bold text-[#10231D]">Active Chat</h2>
                        <StatusBadge status={selectedSession.status} />
                      </div>
                      <p className="mt-1 truncate text-sm font-medium text-[#667570]">
                        {selectedSession.customer_name || "Customer"} / {selectedSession.customer_phone || "No phone"}
                      </p>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      {selectedSession.status === "waiting" ? (
                          <button
                            type="button"
                            onClick={() => void acceptSession(selectedSession)}
                            disabled={!isAgentAvailable}
                            className="inline-flex min-h-10 items-center justify-center rounded-full bg-[#006A4E] px-4 text-sm font-bold text-white shadow-sm transition duration-200 hover:-translate-y-0.5 hover:bg-[#00543E] active:scale-[0.98] disabled:cursor-not-allowed disabled:bg-[#9FB8B0] disabled:hover:translate-y-0 disabled:hover:bg-[#9FB8B0]"
                          >
                            Accept Chat
                          </button>
                      ) : null}
                      {selectedSession.status === "active" ? (
                        <button
                          type="button"
                          onClick={() => void endSession()}
                          className="inline-flex min-h-10 items-center gap-2 rounded-full bg-[#F4C430] px-5 text-sm font-bold text-[#302500] shadow-sm shadow-[#B78C00]/15 transition duration-200 hover:-translate-y-0.5 hover:bg-[#E9B600] active:scale-[0.98]"
                        >
                          <PowerIcon className="h-4 w-4" />
                          End Session
                        </button>
                      ) : null}
                    </div>
                  </div>

                  <div className="min-h-0 flex-1 space-y-4 overflow-y-auto bg-[linear-gradient(180deg,#F8FBFA_0%,#FFFFFF_100%)] px-4 py-5">
                    {messages.length === 0 ? (
                      <div className="mx-auto mt-16 max-w-md rounded-[8px] border border-dashed border-[#D1DFDB] bg-white px-5 py-8 text-center text-sm leading-6 text-[#667570] shadow-sm">
                        No messages yet. Accept the chat and wait for the customer message, or send the first support greeting.
                      </div>
                    ) : (
                      messages.map((chatMessage, index) => {
                        const isAgent = chatMessage.sender_type === "agent";
                        const isSystem = chatMessage.sender_type === "system";

                        return (
                          <div
                            key={chatMessage.id}
                            className={classNames(
                              "agent-message flex",
                              isAgent ? "justify-end" : "justify-start",
                            )}
                            style={{ animationDelay: `${Math.min(index, 6) * 20}ms` }}
                          >
                            <div
                              className={classNames(
                                "min-w-0 max-w-[82%] rounded-[8px] px-4 py-3 text-sm leading-6 shadow-sm [overflow-wrap:anywhere]",
                                isSystem
                                  ? "border border-[#C8D8DD] bg-[#EEF4F6] font-medium text-[#223A42]"
                                  : isAgent
                                    ? "bg-[#006A4E] text-white"
                                    : "border border-[#E2ECE9] bg-white text-[#20332D]",
                              )}
                            >
                              <p className="whitespace-pre-wrap break-words">{chatMessage.message}</p>
                              <p
                                className={classNames(
                                  "mt-2 text-[11px] font-medium",
                                  isAgent ? "text-white/75" : "text-[#7C8A86]",
                                )}
                              >
                                {isSystem ? "System" : isAgent ? "Agent" : "Customer"}
                                {formatClock(chatMessage.created_at) ? ` / ${formatClock(chatMessage.created_at)}` : ""}
                              </p>
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>

                  <form onSubmit={sendMessage} className="border-t border-[#E5EFEC] bg-white p-4">
                    <div className="flex flex-col gap-3 sm:flex-row">
                      <input
                        value={draftMessage}
                        onChange={(event) => setDraftMessage(event.target.value)}
                        disabled={selectedSession.status !== "active" || isSending}
                        placeholder={
                          selectedSession.status === "active"
                            ? "Type your message..."
                            : "Accept the chat before replying"
                        }
                        className="min-h-12 flex-1 rounded-full border border-[#C9D7D3] bg-white px-4 text-sm text-[#20332D] outline-none transition duration-200 placeholder:text-[#8A9894] focus:border-[#006A4E] focus:ring-2 focus:ring-[#006A4E]/10 disabled:cursor-not-allowed disabled:bg-[#F2F5F4] disabled:text-[#7C8A86]"
                      />
                      <button
                        type="submit"
                        disabled={!canSendMessage || isSending}
                        className="inline-flex min-h-12 items-center justify-center gap-2 rounded-full bg-[#006A4E] px-6 text-sm font-bold text-white shadow-md shadow-[#006A4E]/15 transition duration-200 hover:-translate-y-0.5 hover:bg-[#00543E] active:scale-[0.98] disabled:cursor-not-allowed disabled:bg-[#9FB8B0] disabled:shadow-none disabled:hover:translate-y-0 disabled:active:scale-100"
                      >
                        <SendIcon className="h-4 w-4" />
                        {isSending ? "Sending..." : "Send"}
                      </button>
                    </div>
                  </form>
                </>
              ) : (
                <div className="flex flex-1 items-center justify-center p-6">
                  <div className="max-w-md text-center">
                    <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-[#E8F8F0] text-[#006A4E]">
                      <ChatIcon className="h-7 w-7" />
                    </div>
                    <h2 className="mt-4 text-xl font-bold text-[#10231D]">Select a customer</h2>
                    <p className="mt-2 text-sm leading-6 text-[#667570]">
                      Choose a waiting customer from the queue to view details, accept the chat, and start replying.
                    </p>
                  </div>
                </div>
              )}
            </section>

            <aside className="agent-dashboard-card flex min-h-[520px] flex-col overflow-hidden rounded-[8px] border border-[#DCE8E4] bg-white shadow-sm">
              <div className="border-b border-[#E5EFEC] bg-white px-5 py-4">
                <h2 className="text-base font-bold text-[#10231D]">Customer Details</h2>
                <p className="mt-1 text-xs text-[#667570]">Session information for the selected chat.</p>
              </div>

              {selectedSession ? (
                <div className="flex min-h-0 flex-1 flex-col">
                  <div className="border-b border-[#EEF2F1] px-5 py-5">
                    <div className="flex items-center gap-4">
                      <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-[#DDEFE8] text-lg font-bold text-[#006A4E] ring-1 ring-[#006A4E]/10">
                        <UserIcon className="h-8 w-8" />
                      </div>
                      <div className="min-w-0">
                        <p className="truncate text-lg font-bold text-[#10231D]">
                          {selectedSession.customer_name || "Customer"}
                        </p>
                        <div className="mt-2">
                          <StatusBadge status={selectedSession.status} />
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="min-h-0 flex-1 overflow-y-auto px-5 py-2">
                    <DetailRow
                      icon={<PhoneIcon className="h-4 w-4" />}
                      label="Mobile Number"
                      value={selectedSession.customer_phone}
                    />
                    <DetailRow
                      icon={<ClockIcon className="h-4 w-4" />}
                      label="Requested At"
                      value={formatTime(selectedSession.created_at)}
                    />
                    <DetailRow
                      icon={<ChatIcon className="h-4 w-4" />}
                      label="Accepted At"
                      value={formatTime(selectedSession.accepted_at)}
                    />
                    <DetailRow
                      icon={<PowerIcon className="h-4 w-4" />}
                      label="Ended At"
                      value={formatTime(selectedSession.ended_at)}
                    />
                    <DetailRow
                      icon={<UserIcon className="h-4 w-4" />}
                      label="Agent ID"
                      value={selectedSession.agent_id || AGENT_ID}
                    />
                    <DetailRow
                      icon={<QueueIcon className="h-4 w-4" />}
                      label="Session ID"
                      value={selectedSession.support_session_id}
                    />
                    {selectedSession.feedback ? (
                      <DetailRow
                        icon={<ChatIcon className="h-4 w-4" />}
                        label="Customer Feedback"
                        value={selectedSession.feedback.replace("_", " ")}
                      />
                    ) : null}
                  </div>
                </div>
              ) : (
                <div className="flex flex-1 items-center justify-center px-5 py-8 text-center text-sm leading-6 text-[#667570]">
                  Customer details will appear after selecting a queue item.
                </div>
              )}
            </aside>
          </section>
        </div>
      </main>
    </>
  );
}
