"use client";

import { translations } from "@/data/translations";
import { useEffect, useRef, useState } from "react";
import type { FormEvent, ReactNode } from "react";

type Message = {
  role: "bot" | "user";
  text: string;
  quickActions?: string[];
  chatId?: number;
  feedback?: FeedbackValue;
  feedbackStatus?: FeedbackStatus;
};

type ChatApiResponse = {
  reply?: string;
  quick_actions?: string[];
  chat_id?: number;
};

type FeedbackValue = "helpful" | "not_helpful";
type FeedbackStatus = "saving" | "saved" | "error";

const chatbotText = translations.en.chatbot;
const CHATBOT_API_URL = "http://127.0.0.1:8000/chat";
const CHATBOT_FEEDBACK_API_URL = "http://127.0.0.1:8000/chat/feedback";
const ERROR_MESSAGE =
  "Sorry, I could not connect to the chatbot server. Please try again later.";

const SESSION_STORAGE_KEY = "eastern_ai_session_id";
const BOT_RESPONSE_DELAY_MS = 1400;

function createSessionId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }

  return `session-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function wait(milliseconds: number) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, milliseconds);
  });
}

function SendIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className={className}
      fill="none"
    >
      <path
        d="M4.75 19.25 20 12 4.75 4.75l2 6.25L13 12l-6.25 1-2 6.25Z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function MinimizeIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className={className}
      fill="none"
    >
      <path
        d="M6 12h12"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
}

function RobotIcon({ className = "h-7 w-7" }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className={className}
      fill="none"
    >
      <path
        d="M12 5V3M8.5 3h7M6.25 10.75C6.25 8.68 7.93 7 10 7h4c2.07 0 3.75 1.68 3.75 3.75v3.5C17.75 16.32 16.07 18 14 18h-4c-2.07 0-3.75-1.68-3.75-3.75v-3.5Z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M9.5 12h.01M14.5 12h.01"
        stroke="currentColor"
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M10 15h4"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
    </svg>
  );
}

function formatMessage(text: string) {
  const pattern =
    /(https?:\/\/[^\s]+|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|\+?\d[\d\s-]{7,}\d|16230)/g;

  return text.split(pattern).map((part, index) => {
    const cleanPart = part.trim();

    if (cleanPart.startsWith("http://") || cleanPart.startsWith("https://")) {
      return (
        <a
          key={index}
          href={cleanPart}
          target="_blank"
          rel="noopener noreferrer"
          className="break-all font-semibold underline underline-offset-2"
        >
          {cleanPart}
        </a>
      );
    }

    if (/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(cleanPart)) {
      return (
        <a
          key={index}
          href={`mailto:${cleanPart}`}
          className="font-semibold underline underline-offset-2"
        >
          {cleanPart}
        </a>
      );
    }

    if (/^(\+?\d[\d\s-]{7,}\d|16230)$/.test(cleanPart)) {
      const phoneNumber = cleanPart.replace(/[^\d+]/g, "");

      return (
        <a
          key={index}
          href={`tel:${phoneNumber}`}
          className="font-semibold underline underline-offset-2"
        >
          {cleanPart}
        </a>
      );
    }

    return part;
  });
}

function isMarkdownTableLine(line: string) {
  const trimmedLine = line.trim();

  return (
    trimmedLine.startsWith("|") &&
    trimmedLine.endsWith("|") &&
    trimmedLine.split("|").length >= 3
  );
}

function isMarkdownTableSeparator(line: string) {
  return /^\|\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|$/.test(line.trim());
}

function splitMarkdownTableRow(line: string) {
  return line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());
}

function renderTableCells(cells: string[], isHeader: boolean, rowKey: string) {
  const renderedCells: ReactNode[] = [];

  for (let index = 0; index < cells.length; index += 1) {
    if (cells[index] === "" && index > 0) {
      continue;
    }

    let colSpan = 1;

    while (index + colSpan < cells.length && cells[index + colSpan] === "") {
      colSpan += 1;
    }

    const sharedClassName =
      "border border-gray-200 px-3 py-2 align-top text-left whitespace-nowrap";
    const cellKey = `${rowKey}-${index}`;
    const cellContent = cells[index] || "\u00A0";

    if (isHeader) {
      renderedCells.push(
        <th
          key={cellKey}
          colSpan={colSpan > 1 ? colSpan : undefined}
          className={`${sharedClassName} bg-gray-50 font-semibold text-gray-900`}
        >
          {formatMessage(cellContent)}
        </th>,
      );
    } else {
      renderedCells.push(
        <td
          key={cellKey}
          colSpan={colSpan > 1 ? colSpan : undefined}
          className={`${sharedClassName} text-gray-700`}
        >
          {formatMessage(cellContent)}
        </td>,
      );
    }
  }

  return renderedCells;
}

function renderMarkdownTable(headers: string[], rows: string[][], key: string) {
  return (
    <div
      key={key}
      className="my-2 max-w-full overflow-x-auto rounded-lg border border-gray-200 bg-white text-gray-800 shadow-sm"
    >
      <table className="min-w-full border-collapse text-xs leading-5">
        <thead>
          <tr>{renderTableCells(headers, true, `${key}-header`)}</tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={`${key}-row-${rowIndex}`}>
              {renderTableCells(row, false, `${key}-row-${rowIndex}`)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function renderMessageContent(text: string) {
  const lines = text.split(/\r?\n/);
  const nodes: ReactNode[] = [];
  let textBuffer: string[] = [];

  const flushTextBuffer = () => {
    if (textBuffer.length === 0) {
      return;
    }

    const textBlock = textBuffer.join("\n");

    if (textBlock.trim()) {
      nodes.push(
        <span key={`text-${nodes.length}`} className="block whitespace-pre-line">
          {formatMessage(textBlock)}
        </span>,
      );
    }

    textBuffer = [];
  };

  let index = 0;

  while (index < lines.length) {
    if (
      isMarkdownTableLine(lines[index]) &&
      index + 1 < lines.length &&
      isMarkdownTableSeparator(lines[index + 1])
    ) {
      flushTextBuffer();

      const headers = splitMarkdownTableRow(lines[index]);
      const rows: string[][] = [];
      index += 2;

      while (index < lines.length && isMarkdownTableLine(lines[index])) {
        rows.push(splitMarkdownTableRow(lines[index]));
        index += 1;
      }

      nodes.push(renderMarkdownTable(headers, rows, `table-${nodes.length}`));
      continue;
    }

    textBuffer.push(lines[index]);
    index += 1;
  }

  flushTextBuffer();

  return nodes;
}

function isFeedbackPromptText(text: string) {
  const normalizedText = text.trim().toLowerCase();

  return (
    normalizedText.startsWith("hello! welcome") ||
    normalizedText.startsWith("hello! how can") ||
    normalizedText.startsWith("which ") ||
    normalizedText.startsWith("please specify") ||
    normalizedText.startsWith("do you want") ||
    normalizedText.startsWith("system error") ||
    normalizedText === ERROR_MESSAGE.toLowerCase()
  );
}

function shouldShowFeedback(message: Message) {
  return Boolean(
    message.role === "bot" &&
      message.chatId &&
      !message.quickActions?.length &&
      !isFeedbackPromptText(message.text),
  );
}

export default function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [hasStartedConversation, setHasStartedConversation] = useState(false);
  const [showEndConfirmation, setShowEndConfirmation] = useState(false);

  const [messages, setMessages] = useState<Message[]>([]);

  const messageListRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const canEndConversation = messages.length > 0;
  const canGoBackToIntro =
    hasStartedConversation && messages.length === 0 && !isLoading;

  useEffect(() => {
    if (!messageListRef.current) {
      return;
    }

    messageListRef.current.scrollTop = messageListRef.current.scrollHeight;
  }, [messages, isOpen, hasStartedConversation, isLoading]);

  useEffect(() => {
    if (
      !isOpen ||
      !hasStartedConversation ||
      isLoading ||
      showEndConfirmation
    ) {
      return;
    }

    inputRef.current?.focus();
  }, [
    isOpen,
    hasStartedConversation,
    isLoading,
    messages.length,
    showEndConfirmation,
  ]);

  const getCurrentSessionId = () => {
    const savedSessionId = localStorage.getItem(SESSION_STORAGE_KEY);

    if (savedSessionId) {
      return savedSessionId;
    }

    const currentSessionId = createSessionId();
    localStorage.setItem(SESSION_STORAGE_KEY, currentSessionId);

    return currentSessionId;
  };

  const handleConfirmEndSession = () => {
    const newSessionId = createSessionId();

    localStorage.setItem(SESSION_STORAGE_KEY, newSessionId);

    setMessages([]);
    setInput("");
    setHasStartedConversation(false);
    setShowEndConfirmation(false);
  };

  const handleStartConversation = () => {
    setHasStartedConversation(true);
    setShowEndConfirmation(false);
  };

  const handleBackToIntro = () => {
    setInput("");
    setHasStartedConversation(false);
    setShowEndConfirmation(false);
  };

  const sendMessage = async (message: string) => {
    const userMessage = message.trim();

    if (!userMessage || isLoading) {
      return;
    }

    const currentSessionId = getCurrentSessionId();
    setHasStartedConversation(true);
    setShowEndConfirmation(false);

    const chatWithUserMessage: Message[] = [
      ...messages,
      { role: "user", text: userMessage },
    ];

    setMessages(chatWithUserMessage);
    setInput("");
    setIsLoading(true);
    const minimumResponseDelay = wait(BOT_RESPONSE_DELAY_MS);

    try {
      const response = await fetch(CHATBOT_API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: userMessage,
          session_id: currentSessionId,
        }),
      });

      if (!response.ok) {
        throw new Error("Chatbot request failed");
      }

      const data = (await response.json()) as ChatApiResponse;
      const botReply = data.reply ?? ERROR_MESSAGE;
      const quickActions = data.quick_actions ?? [];
      const chatId = typeof data.chat_id === "number" ? data.chat_id : undefined;

      await minimumResponseDelay;

      setMessages([
        ...chatWithUserMessage,
        { role: "bot", text: botReply, quickActions, chatId },
      ]);
    } catch {
      await minimumResponseDelay;

      setMessages([
        ...chatWithUserMessage,
        { role: "bot", text: ERROR_MESSAGE },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await sendMessage(input);
  };

  const handleFeedback = async (
    messageIndex: number,
    feedback: FeedbackValue,
  ) => {
    const message = messages[messageIndex];

    if (message?.role !== "bot" || !message.chatId) {
      return;
    }

    const chatId = message.chatId;
    const sessionId = getCurrentSessionId();

    setMessages((currentMessages) =>
      currentMessages.map((currentMessage, index) =>
        index === messageIndex
          ? {
              ...currentMessage,
              feedback,
              feedbackStatus: "saving",
            }
          : currentMessage,
      ),
    );

    try {
      const response = await fetch(CHATBOT_FEEDBACK_API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          chat_id: chatId,
          session_id: sessionId,
          feedback,
        }),
      });

      if (!response.ok) {
        throw new Error("Feedback request failed");
      }

      setMessages((currentMessages) =>
        currentMessages.map((currentMessage, index) =>
          index === messageIndex
            ? {
                ...currentMessage,
                feedback,
                feedbackStatus: "saved",
              }
            : currentMessage,
        ),
      );
    } catch {
      setMessages((currentMessages) =>
        currentMessages.map((currentMessage, index) =>
          index === messageIndex
            ? {
                ...currentMessage,
                feedbackStatus: "error",
              }
            : currentMessage,
        ),
      );
    }
  };

  const renderQuickActionButton = (action: string) => (
    <button
      key={action}
      type="button"
      onClick={() => {
        void sendMessage(action);
      }}
      disabled={isLoading}
      className="rounded-full border border-[#006A4E]/15 bg-white px-3 py-2 text-sm font-medium text-[#006A4E] shadow-sm transition hover:bg-[#006A4E]/5 disabled:cursor-not-allowed disabled:opacity-60"
    >
      {action}
    </button>
  );

  const renderFeedbackButton = (
    label: string,
    feedback: FeedbackValue,
    message: Message,
    messageIndex: number,
  ) => {
    const isSelected = message.feedback === feedback;
    const isSaving = message.feedbackStatus === "saving";

    return (
      <button
        type="button"
        onClick={() => {
          void handleFeedback(messageIndex, feedback);
        }}
        disabled={isSaving}
        className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${
          isSelected
            ? "border-[#006A4E] bg-[#006A4E] text-white"
            : "border-[#006A4E]/20 bg-white text-[#006A4E] hover:bg-[#006A4E]/5"
        }`}
      >
        {label}
      </button>
    );
  };

  const renderFeedbackControls = (message: Message, messageIndex: number) => {
    if (!shouldShowFeedback(message)) {
      return null;
    }

    return (
      <div className="mt-2 flex max-w-[92%] flex-wrap items-center gap-2">
        <span className="text-xs font-medium text-gray-500">Was this helpful?</span>
        {renderFeedbackButton("Helpful", "helpful", message, messageIndex)}
        {renderFeedbackButton(
          "Not helpful",
          "not_helpful",
          message,
          messageIndex,
        )}
        {message.feedbackStatus === "saved" ? (
          <span className="text-xs font-medium text-[#006A4E]">Saved</span>
        ) : null}
        {message.feedbackStatus === "error" ? (
          <span className="text-xs font-medium text-red-600">
            Could not save
          </span>
        ) : null}
      </div>
    );
  };

  const renderTypingIndicator = () => (
    <div
      className="flex items-center gap-2"
      aria-label="Eastern Bank PLC AI Assistant is typing"
      aria-live="polite"
    >
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 border-[#006A4E] bg-white">
        <RobotIcon className="h-7 w-7 text-[#006A4E]" />
      </div>
      <div className="flex items-center gap-1 rounded-2xl bg-white px-3 py-3 shadow-sm">
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#006A4E]" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#006A4E] [animation-delay:120ms]" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#006A4E] [animation-delay:240ms]" />
      </div>
    </div>
  );

  return (
    <>
      <button
        type="button"
        title="Chatbot"
        onClick={() => {
          setIsOpen((current) => {
            if (current) {
              setShowEndConfirmation(false);
            }

            return !current;
          });
        }}
        className="group fixed bottom-5 right-5 z-40 inline-flex h-14 w-14 items-center justify-center rounded-full bg-white p-1 text-white shadow-2xl shadow-[#006A4E]/30 ring-1 ring-[#006A4E]/20 transition hover:-translate-y-0.5 hover:shadow-[#006A4E]/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#006A4E] sm:bottom-6 sm:right-6 sm:h-16 sm:w-16"
        aria-label={isOpen ? chatbotText.close : chatbotText.open}
      >
        <span className="flex h-full w-full items-center justify-center rounded-full bg-gradient-to-br from-[#008A68] to-[#00543E] shadow-inner">
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-white/95 text-[#006A4E] sm:h-10 sm:w-10">
            <RobotIcon className="h-7 w-7 sm:h-8 sm:w-8" />
          </span>
        </span>
        <span className="pointer-events-none absolute bottom-full right-0 mb-3 rounded-md bg-gray-900 px-3 py-1.5 text-xs font-semibold text-white opacity-0 shadow-lg transition group-hover:opacity-100 group-focus-visible:opacity-100">
          Chatbot
        </span>
      </button>

      {isOpen ? (
        <div className="fixed inset-x-3 bottom-4 z-40 max-w-[calc(100vw-1.5rem)] sm:inset-x-auto sm:bottom-5 sm:right-5 sm:w-[360px] sm:max-w-[360px]">
          <div
            className="relative flex flex-col overflow-hidden rounded-[1.25rem] border border-[#006A4E]/10 bg-white shadow-2xl shadow-black/15"
            style={
              hasStartedConversation
                ? { height: "min(520px, calc(100dvh - 2rem))" }
                : undefined
            }
          >
            <div className="flex shrink-0 items-center justify-between gap-3 bg-[#006A4E] px-4 py-3 text-white sm:px-5">
              <div className="flex min-w-0 items-center gap-2">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold sm:text-base">
                    {chatbotText.title}
                  </p>
                  <p className="mt-1 text-sm text-emerald-100">
                    {chatbotText.status}
                  </p>
                </div>
              </div>

              <div className="flex shrink-0 items-center gap-2">
                {canGoBackToIntro ? (
                  <button
                    type="button"
                    onClick={handleBackToIntro}
                    className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-white/10 text-lg font-semibold leading-none transition hover:bg-white/20"
                    aria-label="Back to start"
                    title="Back to start"
                  >
                    {"<"}
                  </button>
                ) : null}

                <button
                  type="button"
                  onClick={() => {
                    setIsOpen(false);
                    setShowEndConfirmation(false);
                  }}
                  className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-white/10 transition hover:bg-white/20"
                  aria-label="Minimize chatbot"
                  title="Minimize chatbot"
                >
                  <MinimizeIcon />
                </button>

                {canEndConversation ? (
                  <button
                    type="button"
                    onClick={() => setShowEndConfirmation(true)}
                    disabled={isLoading}
                    className="rounded-full bg-white/10 px-3 py-2 text-xs font-medium transition hover:bg-white/20 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    End
                  </button>
                ) : null}
              </div>
            </div>

            {hasStartedConversation ? (
              <div className="flex min-h-0 flex-1 flex-col bg-white px-4 py-4 sm:px-5">
                <div
                  ref={messageListRef}
                  className="min-h-0 flex-1 space-y-3 overflow-y-auto pr-1"
                >
                  {messages.map((message, index) => (
                    <div key={`${message.role}-${index}`}>
                      {message.role === "bot" ? (
                        <p className="mb-1 ml-1 text-xs font-medium text-[#006A4E]">
                          Eastern Bank PLC
                        </p>
                      ) : null}
                      <div
                        className={`max-w-[88%] rounded-2xl px-4 py-3 text-sm leading-6 shadow-sm ${
                          message.role === "bot"
                            ? "bg-[#006A4E] text-white"
                            : "ml-auto bg-gray-100 text-gray-700"
                        }`}
                      >
                        {renderMessageContent(message.text)}
                      </div>
                      {renderFeedbackControls(message, index)}
                      {message.role === "bot" &&
                      message.quickActions &&
                      message.quickActions.length > 0 ? (
                        <div className="mt-2 flex max-w-[92%] flex-wrap gap-2">
                          {message.quickActions.map(renderQuickActionButton)}
                        </div>
                      ) : null}
                    </div>
                  ))}

                  {isLoading ? renderTypingIndicator() : null}
                </div>

                <form
                  onSubmit={handleSubmit}
                  className="mt-4 flex items-center gap-3"
                >
                  <input
                    ref={inputRef}
                    type="text"
                    value={input}
                    onChange={(event) => setInput(event.target.value)}
                    placeholder={chatbotText.placeholder}
                    aria-label={chatbotText.placeholder}
                    disabled={isLoading}
                    className="min-w-0 flex-1 rounded-full border border-gray-200 bg-white px-4 py-3 text-sm text-gray-700 outline-none transition focus:border-[#006A4E] focus:ring-2 focus:ring-[#006A4E]/10 disabled:cursor-not-allowed disabled:opacity-60"
                  />

                  <button
                    type="submit"
                    disabled={isLoading}
                    className="inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-[#006A4E] text-white shadow-lg shadow-[#006A4E]/20 transition hover:bg-[#00543E] disabled:cursor-not-allowed disabled:opacity-60"
                    aria-label={chatbotText.send}
                  >
                    <SendIcon />
                  </button>
                </form>
              </div>
            ) : (
              <div className="bg-[#007A5A] px-4 pb-5 pt-6 text-white sm:px-5">
                <div className="space-y-3">
                  <p className="text-3xl font-bold leading-tight">
                    {chatbotText.introTitle}
                  </p>
                  <p className="max-w-[280px] text-sm leading-6 text-emerald-50">
                    {chatbotText.introDescription}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={handleStartConversation}
                  className="mt-7 flex w-full items-center justify-between rounded-lg bg-white px-4 py-4 text-left text-gray-900 shadow-lg shadow-black/10 transition hover:-translate-y-0.5 hover:shadow-xl"
                >
                  <span>
                    <span className="block text-base font-semibold">
                      {chatbotText.startConversation}
                    </span>
                    <span className="mt-1 block text-sm text-gray-500">
                      {chatbotText.responseTime}
                    </span>
                  </span>
                  <span
                    aria-hidden="true"
                    className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-[#006A4E] text-white shadow-md shadow-[#006A4E]/20"
                  >
                    <SendIcon className="h-4 w-4" />
                  </span>
                </button>
              </div>
            )}

            {showEndConfirmation ? (
              <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/30 px-5">
                <div className="w-full max-w-[280px] rounded-xl bg-white p-5 text-gray-900 shadow-2xl">
                  <p className="text-base font-semibold">End chat session?</p>
                  <p className="mt-2 text-sm leading-5 text-gray-600">
                    Do you want to end this conversation?
                  </p>
                  <div className="mt-5 flex gap-2">
                    <button
                      type="button"
                      onClick={() => setShowEndConfirmation(false)}
                      className="flex-1 rounded-full border border-gray-200 px-4 py-2 text-sm font-semibold text-gray-700 transition hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={handleConfirmEndSession}
                      className="flex-1 rounded-full bg-[#006A4E] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#00543E]"
                    >
                      End
                    </button>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}
    </>
  );
}
