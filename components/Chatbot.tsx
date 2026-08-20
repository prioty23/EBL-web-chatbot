"use client";

import { translations } from "@/data/translations";
import { useEffect, useRef, useState } from "react";
import type { ChangeEvent, FormEvent, ReactNode } from "react";

type Message = {
  role: "bot" | "user";
  text: string;
  menuOnly?: boolean;
  source?: string;
  quickActions?: string[];
  chatId?: number;
  liveChatSupportSessionId?: string;
  feedback?: FeedbackValue;
  feedbackStatus?: FeedbackStatus;
};

type ChatApiResponse = {
  reply?: string;
  source?: string;
  quick_actions?: string[];
  chat_id?: number;
};

type LiveChatSession = {
  support_session_id?: string;
  status?: string;
  agent_is_typing?: boolean;
  customer_is_typing?: boolean;
};

type LiveChatApiResponse = {
  message?: string;
  session?: LiveChatSession;
};

type LiveChatMessage = {
  id: number;
  sender_type: "agent" | "customer" | "system";
  message: string;
  created_at?: string;
};

type LiveChatMessagesApiResponse = {
  session?: LiveChatSession;
  messages?: LiveChatMessage[];
};

type LiveChatAvailabilityApiResponse = {
  has_available_agent?: boolean;
  available_agent_count?: number;
  message?: string;
};

type HumanSupportStep = "confirm" | "details" | null;
type ViewTransitionDirection = "forward" | "back";

type SendMessageOptions = {
  silentUserMessage?: boolean;
  replaceLatestBotMessage?: boolean;
};

type FeedbackValue = "helpful" | "not_helpful";
type FeedbackStatus = "saving" | "saved" | "error";

type ComplaintCellContact = {
  name: string;
  designation: string;
  email: string;
  phone: string;
};

type ComplaintCellSection = {
  title: string;
  contacts: ComplaintCellContact[];
};

type ComplaintCellDetails = {
  title: string;
  email: string;
  enquiry: string;
  onlineForm: string;
  source: string;
  sections: ComplaintCellSection[];
};

type OngoingOffer = {
  title: string;
  description: string;
  image: string;
  details: string;
};

const chatbotText = translations.en.chatbot;
const CHATBOT_API_URL = "http://127.0.0.1:8000/chat";
const CHATBOT_FEEDBACK_API_URL = "http://127.0.0.1:8000/chat/feedback";
const LIVE_CHAT_SESSION_API_URL = "http://127.0.0.1:8000/live-chat/sessions";
const LIVE_CHAT_AVAILABILITY_API_URL =
  "http://127.0.0.1:8000/live-chat/availability";
const ERROR_MESSAGE =
  "Sorry, I could not connect to the chatbot server. Please try again later.";
const HUMAN_SUPPORT_ACTION = "Human Support";
const HUMAN_SUPPORT_CONFIRM_ACTION = "Yes";
const HUMAN_SUPPORT_DECLINE_ACTION = "No";
const HUMAN_SUPPORT_CONFIRM_MESSAGE =
  "To contact an EBL Support Agent, please click Yes.";
const HUMAN_SUPPORT_COLLECTION_MESSAGE =
  "To ensure service quality and for future reference, your chat may be stored or monitored.\n\nBefore transferring you to an EBL Support Agent, please provide your name and mobile number.";
const HUMAN_SUPPORT_NAME_REQUIRED_MESSAGE = "Please enter your name.";
const HUMAN_SUPPORT_INVALID_PHONE_MESSAGE =
  "Please enter a valid Bangladeshi mobile number, for example 017XXXXXXXX or +88017XXXXXXXX.";
const HUMAN_SUPPORT_TRANSFER_MESSAGE =
  "Thanks. We have received your details.";
const HUMAN_SUPPORT_WAITING_MESSAGE =
  "An EBL Support Agent will join the chat as soon as possible.";
const HUMAN_SUPPORT_BUSY_MESSAGE =
  "Our EBL support agents are currently busy. Please wait a little longer, or try again later if the matter is not urgent.";
const HUMAN_SUPPORT_UNAVAILABLE_MESSAGE =
  "All EBL Support Agents are unavailable at the moment. You can use Complaint Cell for formal complaints or Contact Us for general support.";
const HUMAN_SUPPORT_SEND_ERROR_MESSAGE =
  "Sorry, I could not send your message to the support agent. Please try again.";
const HUMAN_SUPPORT_MESSAGE_SOURCES = new Set([
  "live-chat-agent",
  "live-chat-support-agent",
]);
const HUMAN_SUPPORT_FALLBACK_QUICK_ACTIONS = ["Complaint Cell", "Contact Us"];
const LIVE_CHAT_SESSION_STORAGE_KEY = "eastern_ai_live_chat_session_id";
const LIVE_CHAT_MESSAGE_POLL_MS = 2500;
const LIVE_CHAT_TYPING_SIGNAL_MS = 1500;
const LIVE_CHAT_TYPING_IDLE_MS = 3000;
const LIVE_CHAT_BUSY_NOTICE_MS = 180000;
const SUPPORT_ACTION = "Support";
const MAIN_MENU_QUICK_ACTIONS = [
  "Open an Account",
  "Loan Information",
  "Card Information",
  "Ongoing Offer",
  "Schedule of Charges",
  "Interest Rate",
  SUPPORT_ACTION,
  "Locate Us",
];
const DISTRICT_QUICK_ACTIONS = [
  "Dhaka Division",
  "Bagerhat",
  "Barishal",
  "Bogura",
  "Brahmanbaria",
  "Chattogram",
  "Cox's Bazar",
  "Cumilla",
  "Dhaka",
  "Faridpur",
  "Feni",
  "Gazipur",
  "Jashore",
  "Kishoreganj",
  "Khulna",
  "Moulvibazar",
  "Mymensingh",
  "Narayanganj",
  "Narsingdi",
  "Noakhali",
  "Rajshahi",
  "Rangpur",
  "Sylhet",
  "Tangail",
];
const BRANCH_AREA_QUICK_ACTIONS = [
  "Agrabad",
  "Banani",
  "Bashundhara",
  "Bhulta",
  "Board Bazar",
  "Chouhatta",
  "Chowmuhani",
  "Dhanmondi",
  "Fenchuganj",
  "Fulbarigate",
  "Gulshan",
  "Halishahar",
  "Jubilee Road",
  "Khatungonj",
  "Khulna",
  "Khulshi",
  "Maijdee",
  "Mawna",
  "Mirpur",
  "Motijheel",
  "Mouchak",
  "Muradpur",
  "Narayangonj",
  "New Market",
  "O.R. Nizam Road",
  "Ponchoboti",
  "Shantinagar",
  "Sonargaon",
  "Upashahar",
  "Uttara",
];
const SCOPED_BACK_MESSAGE = "Back";
const COMPLAINT_CELL_DEFAULT_EMAIL = "ccs.cmc@ebl-bd.com";
const COMPLAINT_CELL_DEFAULT_FORM = "https://dgzip.ebl-bd.com/query/";
const COMPLAINT_CELL_DEFAULT_FOOTER =
  "Please enquire us from 10am to 5pm, SUN-THU, (Except Holidays) Or For 24 hours Contact Center: please call 16230 (from any mobile), +8809677716230 (from any local & overseas number)";

const SESSION_STORAGE_KEY = "eastern_ai_session_id";
const BOT_RESPONSE_DELAY_MS = 1400;
const WIDGET_CLOSE_ANIMATION_MS = 180;
const SCHEDULE_CHARGE_MENU_SOURCES = new Set([
  "schedule-charges-menu",
  "schedule-charges-category-menu",
  "retail-charge-menu",
  "sme-charge-menu",
  "corporate-charge-menu",
  "card-charge-menu",
]);
const INTEREST_RATE_MENU_SOURCES = new Set([
  "interest-rate-router",
  "deposit-rate-database",
  "lending-rate-database",
]);
const CARD_INFORMATION_MENU_SOURCES = new Set(["card-router"]);
const ACCOUNT_MENU_SOURCES = new Set(["account-router"]);
const LOAN_MENU_SOURCES = new Set(["loan-router"]);
const BRANCH_LOCATOR_MENU_SOURCES = new Set(["branch-locator-agent"]);
const SUPPORT_MENU_SOURCES = new Set(["support-router"]);
const CAMPAIGN_MENU_SOURCES = new Set(["campaign-router"]);
const ONGOING_OFFERS_MESSAGE_SOURCES = new Set(["ongoing-offers-agent"]);

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

function normalizeBangladeshMobileNumber(phoneNumber: string) {
  let digits = phoneNumber.replace(/\D/g, "");

  if (digits.startsWith("00880")) {
    digits = digits.slice(2);
  }

  if (digits.startsWith("8801") && digits.length === 13) {
    digits = `0${digits.slice(3)}`;
  }

  if (/^01[3-9]\d{8}$/.test(digits)) {
    return digits;
  }

  return "";
}

async function getLiveChatAvailability() {
  const response = await fetch(LIVE_CHAT_AVAILABILITY_API_URL);

  if (!response.ok) {
    return null;
  }

  return response.json() as Promise<LiveChatAvailabilityApiResponse>;
}

async function getApiErrorMessage(response: Response, fallbackMessage: string) {
  try {
    const payload = (await response.json()) as {
      detail?: string;
      message?: string;
    };

    return payload.detail || payload.message || fallbackMessage;
  } catch {
    return fallbackMessage;
  }
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

function ClockIcon({ className = "h-3.5 w-3.5" }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className={className}
      fill="none"
    >
      <circle cx="12" cy="12" r="8.25" stroke="currentColor" strokeWidth="1.8" />
      <path
        d="M12 7.75v4.75l3 1.75"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function DistrictPinIcon({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className={className}
      fill="none"
    >
      <path
        d="M12 20s5.25-4.35 5.25-9.15a5.25 5.25 0 0 0-10.5 0C6.75 15.65 12 20 12 20Z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <path
        d="M12 12.5a1.9 1.9 0 1 0 0-3.8 1.9 1.9 0 0 0 0 3.8Z"
        stroke="currentColor"
        strokeWidth="1.8"
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

function QuickActionIcon({
  action,
  className = "h-4 w-4",
}: {
  action: string;
  className?: string;
}) {
  const normalizedAction = action.toLowerCase();

  if (
    normalizedAction.includes("open account") ||
    normalizedAction.includes("open an account")
  ) {
    return (
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        className={className}
        fill="none"
      >
        <path
          d="M4 10.5 12 5l8 5.5M6.5 10.5V18M10 10.5V18M14 10.5V18M17.5 10.5V18M4.5 18h15"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  }

  if (normalizedAction.includes("loan")) {
    return (
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        className={className}
        fill="none"
      >
        <path
          d="M7 14.5h6.75a2.25 2.25 0 0 0 0-4.5H11M7 14.5l2.5-2.5M7 14.5 9.5 17M5 19.5h14M16.5 7.5a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  }

  if (normalizedAction.includes("card")) {
    return (
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        className={className}
        fill="none"
      >
        <rect
          x="4"
          y="6.5"
          width="16"
          height="11"
          rx="2"
          stroke="currentColor"
          strokeWidth="1.8"
        />
        <path
          d="M4 10h16M7.5 14h3"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
        />
      </svg>
    );
  }

  if (normalizedAction.includes("branch") || normalizedAction.includes("locate")) {
    return (
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        className={className}
        fill="none"
      >
        <path
          d="M12 20s6-4.85 6-10a6 6 0 0 0-12 0c0 5.15 6 10 6 10Z"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinejoin="round"
        />
        <path
          d="M12 12.25a2.25 2.25 0 1 0 0-4.5 2.25 2.25 0 0 0 0 4.5Z"
          stroke="currentColor"
          strokeWidth="1.8"
        />
      </svg>
    );
  }

  if (normalizedAction.includes("schedule")) {
    return (
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        className={className}
        fill="none"
      >
        <path
          d="M7 4.5h7l3 3v12H7a2 2 0 0 1-2-2v-11a2 2 0 0 1 2-2Z"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinejoin="round"
        />
        <path
          d="M14 4.5V8h3M8 12h7M8 15.5h5"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  }

  if (normalizedAction.includes("interest")) {
    return (
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        className={className}
        fill="none"
      >
        <path
          d="M7.5 16.5 16.5 7.5M8 9a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3ZM16 18a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Z"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
        />
      </svg>
    );
  }

  if (
    normalizedAction.includes("offer") ||
    normalizedAction.includes("campaign")
  ) {
    return (
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        className={className}
        fill="none"
      >
        <path
          d="M5 7.5A2.5 2.5 0 0 1 7.5 5h4.25c.66 0 1.3.26 1.77.73l5 5a2.5 2.5 0 0 1 0 3.54l-4.25 4.25a2.5 2.5 0 0 1-3.54 0l-5-5A2.5 2.5 0 0 1 5 11.75V7.5Z"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinejoin="round"
        />
        <path
          d="M9 9h.01M9 15l6-6"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  }

  if (normalizedAction.includes("complaint")) {
    return (
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        className={className}
        fill="none"
      >
        <path
          d="M7 4.5h7l3 3v12H7a2 2 0 0 1-2-2v-11a2 2 0 0 1 2-2Z"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinejoin="round"
        />
        <path
          d="M14 4.5V8h3M11 10.5v4M11 17h.01"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  }

  if (normalizedAction.includes("human support")) {
    return (
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        className={className}
        fill="none"
      >
        <path
          d="M5 12a7 7 0 0 1 14 0v3.5A2.5 2.5 0 0 1 16.5 18H15"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M5 12v2.5A1.5 1.5 0 0 0 6.5 16H8v-5H6.5A1.5 1.5 0 0 0 5 12.5M19 12v2.5a1.5 1.5 0 0 1-1.5 1.5H16v-5h1.5A1.5 1.5 0 0 1 19 12.5M12 18h3"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  }

  if (
    normalizedAction === "support" ||
    normalizedAction === "help support" ||
    normalizedAction === "help & support" ||
    normalizedAction === "help and support"
  ) {
    return (
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        className={className}
        fill="none"
      >
        <path
          d="M5.75 11.5a6.25 6.25 0 0 1 12.5 0v2.75A3.75 3.75 0 0 1 14.5 18H13"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M5.75 11.75v2a1.5 1.5 0 0 0 1.5 1.5h1v-5h-1a1.5 1.5 0 0 0-1.5 1.5ZM18.25 11.75v2a1.5 1.5 0 0 1-1.5 1.5h-1v-5h1a1.5 1.5 0 0 1 1.5 1.5ZM11.5 18h1.5"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  }

  if (normalizedAction.includes("contact")) {
    return (
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        className={className}
        fill="none"
      >
        <path
          d="M8.5 5.5 10 9l-2 1.5c1 2.1 2.4 3.5 5.5 5.5l1.5-2 3.5 1.5v2.25c0 .7-.55 1.25-1.25 1.25C9.55 19 5 14.45 5 6.75c0-.7.55-1.25 1.25-1.25H8.5Z"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  }

  return null;
}

function ExternalLinkIcon({ className = "h-3.5 w-3.5" }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className={className}
      fill="none"
    >
      <path
        d="M14 5h5v5M19 5l-8 8M19 14v3.5A1.5 1.5 0 0 1 17.5 19h-11A1.5 1.5 0 0 1 5 17.5v-11A1.5 1.5 0 0 1 6.5 5H10"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function getReadableLinkLabel(url: string) {
  try {
    const parsedUrl = new URL(url);
    const hostname = parsedUrl.hostname.toLowerCase();
    const pathname = parsedUrl.pathname.toLowerCase();

    if (hostname.includes("dgzip.ebl-bd.com") || pathname.includes("query")) {
      return "Open complaint form";
    }

    if (pathname.includes("branches")) {
      return "View branch page";
    }

    if (pathname.includes("interest")) {
      return "View interest rates";
    }

    if (pathname.includes("schedule")) {
      return "View schedule";
    }

    if (pathname.includes("whats-new")) {
      return "Offer Details";
    }

    if (hostname.includes("ebl.com.bd")) {
      return "Open EBL page";
    }
  } catch {
    return "Open link";
  }

  return "Open link";
}

function splitTrailingPunctuation(value: string) {
  const match = value.match(/^(.*?)([),.;:!?]+)$/);

  if (!match) {
    return { link: value, trailingText: "" };
  }

  return {
    link: match[1],
    trailingText: match[2],
  };
}

function formatMessage(text: string) {
  const pattern =
    /(https?:\/\/[^\s]+|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|\+?\d[\d\s-]{7,}\d|16230)/g;

  return text.split(pattern).map((part, index) => {
    const cleanPart = part.trim();

    if (cleanPart.startsWith("http://") || cleanPart.startsWith("https://")) {
      const { link, trailingText } = splitTrailingPunctuation(cleanPart);

      return (
        <span key={index} className="inline-flex max-w-full items-center gap-1">
          <a
            href={link}
            target="_blank"
            rel="noopener noreferrer"
            title={link}
            className="inline-flex max-w-full items-center gap-1 rounded-full border border-[#005B96]/20 bg-white px-2.5 py-1 text-xs font-semibold leading-none text-[#004C7D] no-underline shadow-sm transition hover:border-[#FFC629]/70 hover:bg-[#FFF8D8]"
          >
            <span className="min-w-0 truncate">{getReadableLinkLabel(link)}</span>
            <ExternalLinkIcon className="h-3.5 w-3.5 shrink-0" />
          </a>
          {trailingText}
        </span>
      );
    }

    if (/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(cleanPart)) {
      return (
        <a
          key={index}
          href={`mailto:${cleanPart}`}
          className="break-words font-semibold underline underline-offset-2 [overflow-wrap:anywhere]"
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
          className="break-words font-semibold underline underline-offset-2 [overflow-wrap:anywhere]"
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

function renderCorporateChargeCellContent(cellContent: string) {
  const parts = cellContent
    .split(";")
    .map((part) => part.trim())
    .filter(Boolean);

  if (parts.length <= 1) {
    return formatMessage(cellContent);
  }

  return (
    <span className="block min-w-0 space-y-1 break-words [overflow-wrap:anywhere]">
      {parts.map((part, index) => (
        <span key={`${part}-${index}`} className="block min-w-0">
          {formatMessage(part)}
        </span>
      ))}
    </span>
  );
}

function isCorporateChargeTable(headers: string[]) {
  const normalizedHeaders = headers.map((header) => header.toLowerCase());

  return (
    normalizedHeaders.length === 3 &&
    normalizedHeaders[0] === "particulars" &&
    normalizedHeaders[1] === "onshore banking charges" &&
    normalizedHeaders[2] === "offshore banking charges"
  );
}

function messageHasCorporateChargeTable(text: string) {
  const lines = text.split(/\r?\n/);

  for (let index = 0; index < lines.length - 1; index += 1) {
    if (
      isMarkdownTableLine(lines[index]) &&
      isMarkdownTableSeparator(lines[index + 1]) &&
      isCorporateChargeTable(splitMarkdownTableRow(lines[index]))
    ) {
      return true;
    }
  }

  return false;
}

function normalizeTableColumns(headers: string[], rows: string[][]) {
  const columnCount = Math.max(
    headers.length,
    ...rows.map((row) => row.length),
  );

  return {
    headers: Array.from(
      { length: columnCount },
      (_, index) => headers[index]?.trim() || `Value ${index}`,
    ),
    rows: rows.map((row) =>
      Array.from({ length: columnCount }, (_, index) => row[index]?.trim() || ""),
    ),
  };
}

function renderTableCellValue(value: string, isCorporateCharge: boolean) {
  if (!value) {
    return <span className="text-gray-400">N/A</span>;
  }

  return isCorporateCharge
    ? renderCorporateChargeCellContent(value)
    : formatMessage(value);
}

function renderTableRowCard(
  headers: string[],
  row: string[],
  key: string,
  isCorporateCharge: boolean,
) {
  const title = row[0] || headers[0] || "Details";
  const details = headers.slice(1).map((header, index) => ({
    label: header,
    value: row[index + 1] || "",
  }));

  return (
    <div
      key={key}
      className={
        isCorporateCharge
          ? "min-w-0 overflow-hidden rounded-xl border border-blue-100 bg-white text-gray-800 shadow-sm"
          : "min-w-0 overflow-hidden rounded-xl border border-gray-200 bg-white text-gray-800 shadow-sm"
      }
    >
      <div
        className={
          isCorporateCharge
            ? "border-b border-blue-100 bg-blue-50 px-3 py-2.5"
            : "border-b border-gray-200 bg-gray-50 px-3 py-2.5"
        }
      >
        <p className="min-w-0 break-words text-xs font-semibold text-gray-500 [overflow-wrap:anywhere]">
          {formatMessage(headers[0] || "Details")}
        </p>
        <p
          className={
            isCorporateCharge
              ? "mt-0.5 min-w-0 break-words text-sm font-semibold leading-5 text-[#004C7D] [overflow-wrap:anywhere]"
              : "mt-0.5 min-w-0 break-words text-sm font-semibold leading-5 text-gray-900 [overflow-wrap:anywhere]"
          }
        >
          {formatMessage(title)}
        </p>
      </div>

      {details.length > 0 ? (
        <dl className="divide-y divide-gray-100">
          {details.map((detail, index) => (
            <div
              key={`${key}-detail-${index}`}
              className="grid min-w-0 gap-1 px-3 py-2.5"
            >
              <dt className="min-w-0 break-words text-xs font-semibold leading-5 text-gray-500 [overflow-wrap:anywhere]">
                {formatMessage(detail.label)}
              </dt>
              <dd className="min-w-0 break-words text-sm leading-5 text-gray-800 [overflow-wrap:anywhere]">
                {renderTableCellValue(detail.value, isCorporateCharge)}
              </dd>
            </div>
          ))}
        </dl>
      ) : null}
    </div>
  );
}

function renderMarkdownTable(headers: string[], rows: string[][], key: string) {
  const isCorporateCharge = isCorporateChargeTable(headers);
  const normalizedTable = normalizeTableColumns(headers, rows);

  return (
    <div key={key} className="my-2 max-w-full space-y-2 break-words [overflow-wrap:anywhere]">
      {normalizedTable.rows.map((row, rowIndex) =>
        renderTableRowCard(
          normalizedTable.headers,
          row,
          `${key}-row-${rowIndex}`,
          isCorporateCharge,
        ),
      )}
    </div>
  );
}

function isSourceMetadataLine(line: string) {
  return /^Source:\s+EBL\s+/i.test(line.trim());
}

function isLastUpdatedMetadataLine(line: string) {
  return /^Last updated:/i.test(line.trim());
}

function renderSourceMetadataBlock(sourceLine: string, updatedLine: string, key: string) {
  const sourceText = sourceLine.replace(/^Source:\s*/i, "").trim();
  const updatedText = updatedLine.replace(/^Last updated:\s*/i, "").trim();

  return (
    <div
      key={key}
      className="mt-3 rounded-xl border border-[#F2D46B] bg-[#FFF7D6] px-3 py-2.5 text-[#4B3A00] shadow-sm"
    >
      <p className="text-xs font-semibold leading-5">
        <span>Source: </span>
        <span>{formatMessage(sourceText)}</span>
      </p>
      <p className="mt-0.5 text-xs font-semibold leading-5">
        <span>Last updated: </span>
        <span>{formatMessage(updatedText)}</span>
      </p>
    </div>
  );
}

function parseOngoingOffersContent(text: string) {
  const blocks = text
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean);
  const offers: OngoingOffer[] = [];

  for (const block of blocks) {
    if (!/^offer:/i.test(block)) {
      continue;
    }

    const lines = block.split(/\r?\n/).map((line) => line.trim());
    const offer: OngoingOffer = {
      title: "",
      description: "",
      image: "",
      details: "",
    };

    for (const line of lines) {
      if (/^title:/i.test(line)) {
        offer.title = line.replace(/^title:\s*/i, "").trim();
      }

      if (/^description:/i.test(line)) {
        offer.description = line.replace(/^description:\s*/i, "").trim();
      }

      if (/^image:/i.test(line)) {
        offer.image = line.replace(/^image:\s*/i, "").trim();
      }

      if (/^details:/i.test(line)) {
        offer.details = line.replace(/^details:\s*/i, "").trim();
      }
    }

    if (offer.title) {
      offers.push(offer);
    }
  }

  return offers;
}

function renderOngoingOffersContent(text: string, onBack: () => void) {
  const offers = parseOngoingOffersContent(text);

  if (!offers.length) {
    return renderMessageContent(text);
  }

  return (
    <div className="space-y-3">
      <div className="space-y-3">
        {offers.map((offer, index) => (
          <div
            key={`${offer.title}-${index}`}
            className="overflow-hidden rounded-xl border border-[#D7E5EC] bg-white text-[#123047] shadow-sm"
          >
            {offer.image ? (
              <div className="w-full bg-white">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={offer.image}
                  alt={offer.title}
                  className="block h-auto w-full"
                  loading="lazy"
                />
              </div>
            ) : null}
            <div className="space-y-1.5 px-3 py-3">
              <div className="flex min-w-0 items-start gap-2">
                <span className="mt-1 shrink-0 text-sm font-bold leading-none text-[#E31B4F]">
                  ‹
                </span>
                <p className="min-w-0 flex-1 break-words text-sm font-semibold leading-5 text-[#123047] [overflow-wrap:anywhere]">
                  {formatMessage(offer.title)}
                </p>
                <span className="mt-1 shrink-0 text-sm font-bold leading-none text-[#E31B4F]">
                  ›
                </span>
              </div>
              {offer.description ? (
                <p className="line-clamp-2 text-xs leading-5 text-gray-500">
                  {formatMessage(offer.description)}
                </p>
              ) : null}
            </div>
            <div className="divide-y divide-gray-100 border-t border-gray-100">
              <a
                href={offer.details || "https://www.ebl.com.bd/whats-new"}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-1.5 px-3 py-2.5 text-sm font-semibold text-[#005B96] transition hover:bg-[#FFF8D8]"
              >
                <span>Offer Details</span>
                <ExternalLinkIcon className="h-3.5 w-3.5" />
              </a>
            </div>
          </div>
        ))}
      </div>
      <button
        type="button"
        onClick={onBack}
        className="w-full rounded-xl border border-[#005B96]/20 bg-white px-3 py-2.5 text-sm font-semibold text-[#005B96] shadow-sm transition hover:border-[#FFC629]/80 hover:bg-[#FFF8D8]"
      >
        Back
      </button>
    </div>
  );
}

function renderOngoingOffersCarouselContent(
  text: string,
  activeIndex: number,
  onPrevious: (totalOffers: number) => void,
  onNext: (totalOffers: number) => void,
  onSelect: (offerIndex: number) => void,
  onBack: () => void,
) {
  const offers = parseOngoingOffersContent(text);

  if (!offers.length) {
    return renderOngoingOffersContent(text, onBack);
  }

  const offerIndex = Math.min(Math.max(activeIndex, 0), offers.length - 1);
  const offer = offers[offerIndex];
  const hasMultipleOffers = offers.length > 1;

  const arrowButtonClass =
    "flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-[#005B96]/15 bg-[#F7FBFD] text-base font-bold text-[#005B96]/75 shadow-sm transition hover:border-[#FFC629] hover:bg-[#FFF4C2] hover:text-[#005B96] focus:outline-none focus:ring-2 focus:ring-[#FFC629]/45 disabled:cursor-not-allowed disabled:opacity-30";

  return (
    <div className="space-y-3">
      <div className="overflow-hidden rounded-xl border border-[#D7E5EC] bg-white text-[#123047] shadow-sm">
        <div className="bg-white">
          {offer.image ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={offer.image}
              alt={offer.title}
              className="block h-auto w-full"
              loading="lazy"
            />
          ) : (
            <div className="flex h-32 items-center justify-center bg-[#F6FAFC] px-10 text-center text-xs font-semibold text-[#005B96]">
              {formatMessage(offer.title)}
            </div>
          )}
        </div>
        <div className="space-y-1.5 px-3 py-3">
          <div className="flex min-w-0 items-center gap-2">
            {hasMultipleOffers ? (
              <button
                type="button"
                onClick={() => onPrevious(offers.length)}
                className={arrowButtonClass}
                aria-label="Previous offer"
                title="Previous offer"
              >
                {"<"}
              </button>
            ) : null}
            <p className="min-w-0 flex-1 break-words text-sm font-semibold leading-5 text-[#123047] [overflow-wrap:anywhere]">
              {formatMessage(offer.title)}
            </p>
            {hasMultipleOffers ? (
              <button
                type="button"
                onClick={() => onNext(offers.length)}
                className={arrowButtonClass}
                aria-label="Next offer"
                title="Next offer"
              >
                {">"}
              </button>
            ) : null}
          </div>
          {offer.description ? (
            <p className="line-clamp-2 text-xs leading-5 text-gray-500">
              {formatMessage(offer.description)}
            </p>
          ) : null}
          {hasMultipleOffers ? (
            <p className="text-center text-[11px] font-semibold text-gray-400">
              {offerIndex + 1} of {offers.length}
            </p>
          ) : null}
        </div>
        <div className="divide-y divide-gray-100 border-t border-gray-100">
          <a
            href={offer.details || "https://www.ebl.com.bd/whats-new"}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-1.5 px-3 py-2.5 text-sm font-semibold text-[#005B96] transition hover:bg-[#FFF8D8]"
          >
            <span>Offer Details</span>
            <ExternalLinkIcon className="h-3.5 w-3.5" />
          </a>
        </div>
      </div>
      {hasMultipleOffers ? (
        <div className="flex justify-center gap-1.5">
          {offers.map((offerItem, index) => (
            <button
              key={`${offerItem.title}-dot-${index}`}
              type="button"
              onClick={() => onSelect(index)}
              className={`h-1.5 rounded-full transition ${
                index === offerIndex
                  ? "w-5 bg-[#FFC629]"
                  : "w-1.5 bg-white/60 hover:bg-white"
              }`}
              aria-label={`Show offer ${index + 1}`}
              title={`Show offer ${index + 1}`}
            />
          ))}
        </div>
      ) : null}
      <button
        type="button"
        onClick={onBack}
        className="w-full rounded-xl border border-[#005B96]/20 bg-white px-3 py-2.5 text-sm font-semibold text-[#005B96] shadow-sm transition hover:border-[#FFC629]/80 hover:bg-[#FFF8D8]"
      >
        Back
      </button>
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
        <span
          key={`text-${nodes.length}`}
          className="block min-w-0 whitespace-pre-line break-words [overflow-wrap:anywhere]"
        >
          {formatMessage(textBlock)}
        </span>,
      );
    }

    textBuffer = [];
  };

  let index = 0;

  while (index < lines.length) {
    if (
      isSourceMetadataLine(lines[index]) &&
      index + 1 < lines.length &&
      isLastUpdatedMetadataLine(lines[index + 1])
    ) {
      flushTextBuffer();
      nodes.push(
        renderSourceMetadataBlock(
          lines[index],
          lines[index + 1],
          `metadata-${nodes.length}`,
        ),
      );
      index += 2;
      continue;
    }

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

function parseComplaintCellContent(text: string): ComplaintCellDetails {
  const blocks = text
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean);

  const details: ComplaintCellDetails = {
    title: blocks[0]?.replace(/:$/, "") || "EBL Complaint Cell",
    email: "",
    enquiry: "",
    onlineForm: "",
    source: "",
    sections: [],
  };

  let currentSection: ComplaintCellSection | null = null;

  for (const block of blocks.slice(1)) {
    if (/^email address:/i.test(block)) {
      details.email = block.replace(/^email address:\s*/i, "").trim();
      continue;
    }

    if (/^please enquire us/i.test(block)) {
      details.enquiry = block;
      continue;
    }

    if (/^online query\/complaint form:/i.test(block)) {
      details.onlineForm = block
        .replace(/^online query\/complaint form:\s*/i, "")
        .trim();
      continue;
    }

    if (/^source page:/i.test(block)) {
      details.source = block.replace(/^source page:\s*/i, "").trim();
      continue;
    }

    if (block.endsWith(":") && !block.includes("\n")) {
      currentSection = {
        title: block.replace(/:$/, ""),
        contacts: [],
      };
      details.sections.push(currentSection);
      continue;
    }

    if (!currentSection) {
      continue;
    }

    const lines = block.split(/\r?\n/).map((line) => line.trim());
    const name = lines[0]?.replace(/^\d+\.\s*/, "").trim();

    if (!name) {
      continue;
    }

    currentSection.contacts.push({
      name,
      designation:
        lines
          .find((line) => /^designation:/i.test(line))
          ?.replace(/^designation:\s*/i, "")
          .trim() ?? "",
      email:
        lines
          .find((line) => /^email:/i.test(line))
          ?.replace(/^email:\s*/i, "")
          .trim() ?? "",
      phone:
        lines
          .find((line) => /^phone no\.:/i.test(line))
          ?.replace(/^phone no\.:\s*/i, "")
          .trim() ?? "",
    });
  }

  return details;
}

function renderComplaintContact(contact: ComplaintCellContact, index: number) {
  return (
    <div key={`${contact.name}-${index}`} className="min-w-0 px-3 py-3">
      <p className="min-w-0 break-words text-sm font-semibold leading-5 text-[#004C7D] [overflow-wrap:anywhere]">
        {contact.name}
      </p>
      <dl className="mt-2 min-w-0 space-y-1.5 text-xs leading-5">
        <div className="min-w-0 break-words [overflow-wrap:anywhere]">
          <dt className="inline font-semibold text-gray-500">Designation: </dt>
          <dd className="inline text-gray-800">
            {formatMessage(contact.designation)}
          </dd>
        </div>
        <div className="min-w-0 break-words [overflow-wrap:anywhere]">
          <dt className="inline font-semibold text-gray-500">Email: </dt>
          <dd className="inline break-words text-gray-800 [overflow-wrap:anywhere]">
            {formatMessage(contact.email)}
          </dd>
        </div>
        <div className="min-w-0 break-words [overflow-wrap:anywhere]">
          <dt className="inline font-semibold text-gray-500">Phone No.: </dt>
          <dd className="inline text-gray-800">{formatMessage(contact.phone)}</dd>
        </div>
      </dl>
    </div>
  );
}

function renderComplaintCellContent(text: string) {
  const details = parseComplaintCellContent(text);
  const hasContactSections = details.sections.some(
    (section) => section.contacts.length > 0,
  );
  const footerText = details.enquiry || COMPLAINT_CELL_DEFAULT_FOOTER;
  const fallbackEmail = details.email || COMPLAINT_CELL_DEFAULT_EMAIL;
  const fallbackForm = details.onlineForm || COMPLAINT_CELL_DEFAULT_FORM;

  return (
    <div className="min-w-0 space-y-3 break-words [overflow-wrap:anywhere]">
      {hasContactSections ? (
        details.sections.map((section) => (
          <div
            key={section.title}
            className="min-w-0 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm"
          >
            <div className="min-w-0 break-words border-b border-gray-200 bg-gray-50 px-3 py-2 text-center text-xs font-semibold leading-5 text-gray-800 [overflow-wrap:anywhere]">
              {section.title}
            </div>
            <div className="divide-y divide-gray-100">
              {section.contacts.map(renderComplaintContact)}
            </div>
          </div>
        ))
      ) : (
        <div className="min-w-0 space-y-1.5 break-words text-sm leading-6 text-white [overflow-wrap:anywhere]">
          <p>
            <span className="font-semibold">Email Address: </span>
            {formatMessage(fallbackEmail)}
          </p>
          <p>
            <span className="font-semibold">
              Online query/complaint form:{" "}
            </span>
            {formatMessage(fallbackForm)}
          </p>
        </div>
      )}
      <div className="min-w-0 rounded-xl border border-[#F0C84B] bg-[#FFF8D8] px-3 py-2.5 shadow-sm">
        <p className="min-w-0 break-words text-xs font-semibold leading-5 text-[#4B3A00] [overflow-wrap:anywhere]">
          {formatMessage(footerText)}
        </p>
      </div>
    </div>
  );
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

function isHumanSupportMessage(message: Message) {
  return (
    message.role === "bot" &&
    Boolean(message.source) &&
    HUMAN_SUPPORT_MESSAGE_SOURCES.has(message.source ?? "")
  );
}

function isHumanSupportEndedMessage(message: Message) {
  const normalizedText = message.text.trim().toLowerCase();

  return (
    isHumanSupportMessage(message) &&
    normalizedText.startsWith("live chat session ended")
  );
}

function shouldShowConversationFollowUp(
  message: Message,
  messageIndex: number,
  latestBotMessageIndex: number,
) {
  return shouldShowFeedback(message) && messageIndex === latestBotMessageIndex;
}

function buildProductFollowUpQuestion(menuText: string) {
  const firstLine =
    menuText
      .split(/\r?\n/)
      .map((line) => line.trim())
      .find(Boolean) ?? "";

  if (!firstLine) {
    return "Want to know another product or service?";
  }

  const normalizedLine = firstLine.replace(/\?+$/, "");

  if (normalizedLine.toLowerCase().startsWith("which ")) {
    const subject = normalizedLine
      .replace(/^which\s+/i, "")
      .replace(/\s+do you want(?: to know)?$/i, "")
      .replace(/\s+product\/account type\b/i, " product")
      .replace(/\s+charge do you want for .+$/i, " charge for this product")
      .trim();

    if (subject) {
      return `Want to know another ${subject}?`;
    }
  }

  if (normalizedLine.toLowerCase().includes("deposit rate category")) {
    return "Want to know another deposit rate product?";
  }

  if (normalizedLine.toLowerCase().includes("lending rate category")) {
    return "Want to know another lending rate product?";
  }

  return "Want to know another product or service?";
}

function replaceLatestBotMessage(messages: Message[], botMessage: Message) {
  const nextMessages = [...messages];

  for (let index = nextMessages.length - 1; index >= 0; index -= 1) {
    if (nextMessages[index].role === "bot") {
      nextMessages[index] = botMessage;
      return nextMessages;
    }
  }

  return [...nextMessages, botMessage];
}

function hasAnyAction(actions: string[] | undefined, expectedActions: string[]) {
  if (!actions?.length) {
    return false;
  }

  const actionSet = new Set(actions.map((action) => action.toLowerCase()));

  return expectedActions.some((action) => actionSet.has(action.toLowerCase()));
}

function normalizeQuickAction(action: string) {
  return action.trim().replace(/\s+/g, " ").toLowerCase();
}

function isMainMenuQuickAction(action: string) {
  return MAIN_MENU_QUICK_ACTIONS.some(
    (mainAction) => mainAction.toLowerCase() === action.toLowerCase(),
  );
}

function isDistrictQuickAction(action: string) {
  return DISTRICT_QUICK_ACTIONS.some(
    (district) => district.toLowerCase() === action.toLowerCase(),
  );
}

function isBranchAreaQuickAction(action: string) {
  return BRANCH_AREA_QUICK_ACTIONS.some(
    (area) => area.toLowerCase() === action.toLowerCase(),
  );
}

function isLocationQuickAction(action: string) {
  return isDistrictQuickAction(action) || isBranchAreaQuickAction(action);
}

function isMainMenuQuickActionList(actions: string[] | undefined) {
  if (!actions?.length) {
    return false;
  }

  return actions.every(isMainMenuQuickAction);
}

function isDistrictQuickActionList(actions: string[] | undefined) {
  if (!actions?.length) {
    return false;
  }

  return actions.every(isLocationQuickAction);
}

function hasMenuSource(message: Message, sources: Set<string>) {
  return Boolean(message.source && sources.has(message.source));
}

function isScheduleChargeOptionText(text: string, actions?: string[]) {
  const normalizedText = text.toLowerCase();
  const isScheduleChargeRoot = hasAnyAction(actions, [
    "Retail Charges",
    "SME Charges",
    "Corporate Charges",
    "Card Charges",
  ]);

  return (
    isScheduleChargeRoot ||
    normalizedText.includes("banking charge do you want") ||
    normalizedText.includes("specific retail charge") ||
    normalizedText.includes("specific sme charge") ||
    normalizedText.includes("specific corporate charge") ||
    normalizedText.includes("specific card charge") ||
    normalizedText.includes("retail charge category do you want") ||
    normalizedText.includes("retail charge subcategory do you want") ||
    normalizedText.includes("sme charge category do you want") ||
    normalizedText.includes("sme charge subcategory do you want") ||
    normalizedText.includes("sme loan charge do you want") ||
    normalizedText.includes("sme certificate/report service do you want") ||
    normalizedText.includes("sme cheque/clearing service do you want") ||
    normalizedText.includes("corporate charge category do you want") ||
    normalizedText.includes("corporate charge subcategory do you want") ||
    normalizedText.includes("card charge type do you want") ||
    normalizedText.includes("product do you want for charges") ||
    normalizedText.includes("product/account type do you want") ||
    normalizedText.includes("charge do you want for") ||
    normalizedText.includes("charge do you want") ||
    normalizedText.includes("service do you want") ||
    normalizedText.startsWith("please specify the exact charge") ||
    normalizedText.startsWith("please specify the product/account type")
  );
}

function isInterestRateOptionText(text: string, actions?: string[]) {
  const normalizedText = text.toLowerCase();
  const isInterestRateRoot = hasAnyAction(actions, [
    "Deposit Rate",
    "Lending Rate",
  ]);

  return (
    isInterestRateRoot ||
    normalizedText.includes("interest rate do you want") ||
    normalizedText.includes("deposit rate category") ||
    normalizedText.includes("lending rate category") ||
    normalizedText.includes("deposit product rate do you want") ||
    normalizedText.includes("lending product rate do you want") ||
    normalizedText.includes("product rate do you want") ||
    normalizedText.includes("timeline do you want")
  );
}

function isCardInformationOptionText(text: string, actions?: string[]) {
  const normalizedText = text.toLowerCase();
  const isCardInformationRoot = hasAnyAction(actions, [
    "Debit Card",
    "Credit Card",
    "Prepaid Card",
    "Islamic Card",
  ]);

  return (
    isCardInformationRoot ||
    normalizedText.includes("card type do you want to know") ||
    normalizedText.includes("card options include") ||
    normalizedText.includes("please tell me the specific card name") ||
    normalizedText.includes("please tell me the specific credit card name") ||
    normalizedText.includes("please tell me the specific debit card name") ||
    normalizedText.includes("please tell me the specific prepaid card name") ||
    normalizedText.includes("please tell me the specific islamic card name")
  );
}

function isAccountOptionText(text: string, actions?: string[]) {
  const normalizedText = text.toLowerCase();
  const isAccountRoot = hasAnyAction(actions, [
    "Retail Account",
    "SME Account",
    "Islamic Account",
  ]);

  return (
    isAccountRoot ||
    normalizedText.includes("account type do you want") ||
    normalizedText.includes("account category do you want") ||
    normalizedText.includes("accounts include") ||
    normalizedText.includes("deposit options include") ||
    normalizedText.includes("please tell me the specific account name") ||
    normalizedText.includes("please tell me the specific deposit product name")
  );
}

function isLoanOptionText(text: string, actions?: string[]) {
  const normalizedText = text.toLowerCase();
  const isLoanRoot = hasAnyAction(actions, ["Retail Loans", "SME Loans"]);

  return (
    isLoanRoot ||
    normalizedText.includes("loan type do you want") ||
    normalizedText.includes("loan category do you want") ||
    normalizedText.includes("loan options include") ||
    normalizedText.includes("please tell me the specific loan name")
  );
}

function isBranchLocatorOptionText(text: string, actions?: string[]) {
  const normalizedText = text.toLowerCase();
  const hasBranchDistrictOptions = hasAnyAction(actions, [
    "Dhaka",
    "Chattogram",
    "Sylhet",
  ]);

  return (
    hasBranchDistrictOptions ||
    normalizedText.includes("district branch do you want to locate") ||
    normalizedText.includes("please tell me your area")
  );
}

function isSupportOptionText(text: string, actions?: string[]) {
  return (
    text.toLowerCase().includes("which support service do you need") &&
    hasAnyAction(actions, [HUMAN_SUPPORT_ACTION, "Complaint Cell", "Contact Us"])
  );
}

function isSupportQuickAction(action: string) {
  const normalizedAction = normalizeQuickAction(action);

  return ["human support", "complaint cell", "contact us"].includes(
    normalizedAction,
  );
}

function isCampaignOptionText(text: string, actions?: string[]) {
  return (
    text.toLowerCase().includes("which campaign would you like to view") &&
    hasAnyAction(actions, ["Ongoing Offer", "Ongoing Offers"])
  );
}

function isCampaignQuickAction(action: string) {
  return [
    "on going offer",
    "on going offers",
    "ongoing offer",
    "ongoing offers",
  ].includes(normalizeQuickAction(action));
}

function isScopedOptionMenuMessage(message: Message | null) {
  if (!message || message.role !== "bot" || !message.quickActions?.length) {
    return false;
  }

  return (
    hasMenuSource(message, SCHEDULE_CHARGE_MENU_SOURCES) ||
    hasMenuSource(message, INTEREST_RATE_MENU_SOURCES) ||
    hasMenuSource(message, CARD_INFORMATION_MENU_SOURCES) ||
    hasMenuSource(message, ACCOUNT_MENU_SOURCES) ||
    hasMenuSource(message, LOAN_MENU_SOURCES) ||
    hasMenuSource(message, BRANCH_LOCATOR_MENU_SOURCES) ||
    hasMenuSource(message, SUPPORT_MENU_SOURCES) ||
    hasMenuSource(message, CAMPAIGN_MENU_SOURCES) ||
    isScheduleChargeOptionText(message.text, message.quickActions) ||
    isInterestRateOptionText(message.text, message.quickActions) ||
    isCardInformationOptionText(message.text, message.quickActions) ||
    isAccountOptionText(message.text, message.quickActions) ||
    isLoanOptionText(message.text, message.quickActions) ||
    isBranchLocatorOptionText(message.text, message.quickActions) ||
    isSupportOptionText(message.text, message.quickActions) ||
    isCampaignOptionText(message.text, message.quickActions)
  );
}

export default function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [isWidgetClosing, setIsWidgetClosing] = useState(false);
  const [viewTransitionDirection, setViewTransitionDirection] =
    useState<ViewTransitionDirection>("forward");
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [hasStartedConversation, setHasStartedConversation] = useState(false);
  const [showEndConfirmation, setShowEndConfirmation] = useState(false);
  const [humanSupportStep, setHumanSupportStep] =
    useState<HumanSupportStep>(null);
  const [humanSupportName, setHumanSupportName] = useState("");
  const [humanSupportPhone, setHumanSupportPhone] = useState("");
  const [humanSupportFormError, setHumanSupportFormError] = useState("");
  const [liveChatSupportSessionId, setLiveChatSupportSessionId] = useState("");
  const [liveChatStatus, setLiveChatStatus] = useState("");
  const [isLiveChatAgentTyping, setIsLiveChatAgentTyping] = useState(false);

  const [messages, setMessages] = useState<Message[]>([]);
  const [offerCarouselIndexes, setOfferCarouselIndexes] = useState<
    Record<string, number>
  >({});

  const messageListRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const liveChatLastMessageIdRef = useRef(0);
  const liveChatBusyTimerRef = useRef<number | null>(null);
  const liveChatBusyNoticeSessionRef = useRef("");
  const liveChatCustomerTypingStopTimerRef = useRef<number | null>(null);
  const liveChatLastCustomerTypingSignalRef = useRef(0);
  const widgetCloseTimerRef = useRef<ReturnType<typeof setTimeout> | null>(
    null,
  );
  const canEndConversation = messages.length > 0;
  const canGoBackToIntro =
    hasStartedConversation && messages.length === 0 && !isLoading;

  useEffect(() => {
    if (!messageListRef.current) {
      return;
    }

    messageListRef.current.scrollTo({
      top: messageListRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [
    messages,
    isOpen,
    hasStartedConversation,
    isLoading,
    isLiveChatAgentTyping,
  ]);

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

  useEffect(() => {
    const restoreLiveChatTimer = window.setTimeout(() => {
      const savedSupportSessionId = localStorage.getItem(
        LIVE_CHAT_SESSION_STORAGE_KEY,
      );

      if (savedSupportSessionId) {
        setLiveChatSupportSessionId(savedSupportSessionId);
        setLiveChatStatus("waiting");
      }
    }, 0);

    return () => window.clearTimeout(restoreLiveChatTimer);
  }, []);

  useEffect(() => {
    if (!liveChatSupportSessionId) {
      return;
    }

    let isCancelled = false;

    const pollLiveChatMessages = async () => {
      try {
        const response = await fetch(
          `${LIVE_CHAT_SESSION_API_URL}/${encodeURIComponent(
            liveChatSupportSessionId,
          )}/messages?after_id=${liveChatLastMessageIdRef.current}&limit=50`,
        );

        if (!response.ok) {
          return;
        }

        const data = (await response.json()) as LiveChatMessagesApiResponse;

        if (isCancelled) {
          return;
        }

        const incomingMessages = data.messages ?? [];
        const newestMessageId = incomingMessages.reduce(
          (latestMessageId, liveChatMessage) =>
            Math.max(latestMessageId, liveChatMessage.id),
          liveChatLastMessageIdRef.current,
        );
        const botMessages: Message[] = incomingMessages
          .filter(
            (liveChatMessage) =>
              liveChatMessage.sender_type === "agent" ||
              liveChatMessage.sender_type === "system",
          )
          .map((liveChatMessage) => ({
            role: "bot",
            text: liveChatMessage.message,
            source: "live-chat-agent",
            liveChatSupportSessionId,
          }));

        if (newestMessageId > liveChatLastMessageIdRef.current) {
          liveChatLastMessageIdRef.current = newestMessageId;
        }

        if (botMessages.length > 0) {
          setMessages((currentMessages) => [
            ...currentMessages,
            ...botMessages,
          ]);
        }

        const nextStatus = data.session?.status ?? "";
        setIsLiveChatAgentTyping(
          Boolean(data.session?.agent_is_typing && nextStatus === "active"),
        );

        if (nextStatus) {
          setLiveChatStatus(nextStatus);
        }

        if (nextStatus === "ended") {
          localStorage.removeItem(LIVE_CHAT_SESSION_STORAGE_KEY);
          setLiveChatSupportSessionId("");
          setIsLiveChatAgentTyping(false);
        }
      } catch {
        // Keep polling quietly; support chat should not interrupt normal chatbot use.
      }
    };

    const initialPollTimer = window.setTimeout(() => {
      void pollLiveChatMessages();
    }, 0);
    const pollTimer = window.setInterval(() => {
      void pollLiveChatMessages();
    }, LIVE_CHAT_MESSAGE_POLL_MS);

    return () => {
      isCancelled = true;
      window.clearTimeout(initialPollTimer);
      window.clearInterval(pollTimer);
    };
  }, [liveChatSupportSessionId]);

  useEffect(() => {
    if (
      !liveChatSupportSessionId ||
      liveChatStatus !== "waiting" ||
      liveChatBusyNoticeSessionRef.current === liveChatSupportSessionId
    ) {
      if (liveChatBusyTimerRef.current) {
        window.clearTimeout(liveChatBusyTimerRef.current);
        liveChatBusyTimerRef.current = null;
      }
      return;
    }

    liveChatBusyTimerRef.current = window.setTimeout(() => {
      liveChatBusyNoticeSessionRef.current = liveChatSupportSessionId;
      liveChatBusyTimerRef.current = null;

      setMessages((currentMessages) => {
        const hasBusyNotice = currentMessages.some(
          (message) =>
            message.liveChatSupportSessionId === liveChatSupportSessionId &&
            message.text === HUMAN_SUPPORT_BUSY_MESSAGE,
        );

        if (hasBusyNotice) {
          return currentMessages;
        }

        return [
          ...currentMessages,
          {
            role: "bot",
            text: HUMAN_SUPPORT_BUSY_MESSAGE,
            source: "live-chat-agent",
            liveChatSupportSessionId,
          },
        ];
      });
    }, LIVE_CHAT_BUSY_NOTICE_MS);

    return () => {
      if (liveChatBusyTimerRef.current) {
        window.clearTimeout(liveChatBusyTimerRef.current);
        liveChatBusyTimerRef.current = null;
      }
    };
  }, [liveChatStatus, liveChatSupportSessionId]);

  useEffect(() => {
    return () => {
      if (widgetCloseTimerRef.current) {
        clearTimeout(widgetCloseTimerRef.current);
      }

      if (liveChatBusyTimerRef.current) {
        clearTimeout(liveChatBusyTimerRef.current);
      }

      if (liveChatCustomerTypingStopTimerRef.current) {
        clearTimeout(liveChatCustomerTypingStopTimerRef.current);
      }
    };
  }, []);

  const clearWidgetCloseTimer = () => {
    if (widgetCloseTimerRef.current) {
      clearTimeout(widgetCloseTimerRef.current);
      widgetCloseTimerRef.current = null;
    }
  };

  const openChatbot = () => {
    clearWidgetCloseTimer();
    setIsWidgetClosing(false);
    setIsOpen(true);
  };

  const minimizeChatbot = () => {
    if (!isOpen && !isWidgetClosing) {
      return;
    }

    clearWidgetCloseTimer();
    setShowEndConfirmation(false);
    setIsWidgetClosing(true);
    setIsOpen(false);

    widgetCloseTimerRef.current = setTimeout(() => {
      setIsWidgetClosing(false);
      widgetCloseTimerRef.current = null;
    }, WIDGET_CLOSE_ANIMATION_MS);
  };

  const getCurrentSessionId = () => {
    const savedSessionId = localStorage.getItem(SESSION_STORAGE_KEY);

    if (savedSessionId) {
      return savedSessionId;
    }

    const currentSessionId = createSessionId();
    localStorage.setItem(SESSION_STORAGE_KEY, currentSessionId);

    return currentSessionId;
  };

  const clearLiveChatCustomerTypingTimer = () => {
    if (liveChatCustomerTypingStopTimerRef.current) {
      window.clearTimeout(liveChatCustomerTypingStopTimerRef.current);
      liveChatCustomerTypingStopTimerRef.current = null;
    }
  };

  const sendLiveChatCustomerTypingStatus = async (isTyping: boolean) => {
    if (!liveChatSupportSessionId || liveChatStatus === "ended") {
      return;
    }

    try {
      await fetch(
        `${LIVE_CHAT_SESSION_API_URL}/${encodeURIComponent(
          liveChatSupportSessionId,
        )}/typing`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            sender_type: "customer",
            sender_id: getCurrentSessionId(),
            is_typing: isTyping,
          }),
        },
      );
    } catch {
      // Typing presence is temporary, so it should not interrupt the customer.
    }
  };

  const resetLiveChatCustomerTypingStatus = () => {
    clearLiveChatCustomerTypingTimer();
    liveChatLastCustomerTypingSignalRef.current = 0;
    void sendLiveChatCustomerTypingStatus(false);
  };

  const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    const nextValue = event.target.value;
    setInput(nextValue);

    if (
      !liveChatSupportSessionId ||
      liveChatStatus === "ended" ||
      humanSupportStep === "details"
    ) {
      return;
    }

    if (!nextValue.trim()) {
      resetLiveChatCustomerTypingStatus();
      return;
    }

    const now = Date.now();

    if (
      now - liveChatLastCustomerTypingSignalRef.current >
      LIVE_CHAT_TYPING_SIGNAL_MS
    ) {
      liveChatLastCustomerTypingSignalRef.current = now;
      void sendLiveChatCustomerTypingStatus(true);
    }

    clearLiveChatCustomerTypingTimer();
    liveChatCustomerTypingStopTimerRef.current = window.setTimeout(() => {
      liveChatCustomerTypingStopTimerRef.current = null;
      liveChatLastCustomerTypingSignalRef.current = 0;
      void sendLiveChatCustomerTypingStatus(false);
    }, LIVE_CHAT_TYPING_IDLE_MS);
  };

  const handleConfirmEndSession = () => {
    const newSessionId = createSessionId();
    const supportSessionToEnd = liveChatSupportSessionId;

    localStorage.setItem(SESSION_STORAGE_KEY, newSessionId);
    localStorage.removeItem(LIVE_CHAT_SESSION_STORAGE_KEY);

    if (supportSessionToEnd) {
      void fetch(
        `${LIVE_CHAT_SESSION_API_URL}/${encodeURIComponent(
          supportSessionToEnd,
        )}/end`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ ended_by: "customer" }),
        },
      );
    }

    setMessages([]);
    setInput("");
    setHasStartedConversation(false);
    setShowEndConfirmation(false);
    setHumanSupportStep(null);
    setHumanSupportName("");
    setHumanSupportPhone("");
    setHumanSupportFormError("");
    setLiveChatSupportSessionId("");
    setLiveChatStatus("");
    setIsLiveChatAgentTyping(false);
    liveChatLastMessageIdRef.current = 0;
    liveChatBusyNoticeSessionRef.current = "";
  };

  const handleStartConversation = () => {
    setViewTransitionDirection("forward");
    setHasStartedConversation(true);
    setShowEndConfirmation(false);
  };

  const handleBackToIntro = () => {
    setViewTransitionDirection("back");
    setInput("");
    setHasStartedConversation(false);
    setShowEndConfirmation(false);
    setHumanSupportStep(null);
    setHumanSupportName("");
    setHumanSupportPhone("");
    setHumanSupportFormError("");
    setIsLiveChatAgentTyping(false);
  };

  const handleShowMainMenu = () => {
    setShowEndConfirmation(false);
    setHumanSupportStep(null);
    setHumanSupportName("");
    setHumanSupportPhone("");
    setHumanSupportFormError("");
    setIsLiveChatAgentTyping(false);
    setMessages((currentMessages) => [
      ...currentMessages,
      {
        role: "bot",
        text: chatbotText.welcome,
        source: "greeting-handler",
        quickActions: MAIN_MENU_QUICK_ACTIONS,
      },
    ]);
  };

  const getPreviousProductMenu = (messageIndex: number) => {
    for (let index = messageIndex - 1; index >= 0; index -= 1) {
      const previousMessage = messages[index];

      if (
        previousMessage.role === "bot" &&
        previousMessage.quickActions?.length &&
        shouldRenderServiceActionList(previousMessage)
      ) {
        return previousMessage;
      }
    }

    return null;
  };

  const handleShowPreviousProductMenu = (productMenu: Message) => {
    setShowEndConfirmation(false);
    setMessages((currentMessages) => [
      ...currentMessages,
      {
        role: "bot",
        text: productMenu.text,
        source: productMenu.source,
        quickActions: productMenu.quickActions,
      },
    ]);
  };

  const sendMessage = async (
    message: string,
    options: SendMessageOptions = {},
  ) => {
    const userMessage = message.trim();

    if (!userMessage || isLoading) {
      return;
    }

    const currentSessionId = getCurrentSessionId();
    setHasStartedConversation(true);
    setShowEndConfirmation(false);

    const chatWithUserMessage: Message[] = options.silentUserMessage
      ? [...messages]
      : [...messages, { role: "user", text: userMessage }];

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
      const botMessage: Message = {
        role: "bot",
        text: botReply,
        source: data.source,
        quickActions,
        chatId,
      };

      await minimumResponseDelay;

      setMessages(
        options.replaceLatestBotMessage
          ? replaceLatestBotMessage(chatWithUserMessage, botMessage)
          : [...chatWithUserMessage, botMessage],
      );
    } catch {
      await minimumResponseDelay;

      const errorMessage: Message = { role: "bot", text: ERROR_MESSAGE };

      setMessages(
        options.replaceLatestBotMessage
          ? replaceLatestBotMessage(chatWithUserMessage, errorMessage)
          : [...chatWithUserMessage, errorMessage],
      );
    } finally {
      setIsLoading(false);
    }
  };

  const sendLiveChatCustomerMessage = async (message: string) => {
    const userMessage = message.trim();

    if (!userMessage || isLoading || !liveChatSupportSessionId) {
      return;
    }

    resetLiveChatCustomerTypingStatus();

    const chatWithUserMessage: Message[] = [
      ...messages,
      { role: "user", text: userMessage },
    ];

    setHasStartedConversation(true);
    setShowEndConfirmation(false);
    setMessages(chatWithUserMessage);
    setInput("");

    try {
      const response = await fetch(
        `${LIVE_CHAT_SESSION_API_URL}/${encodeURIComponent(
          liveChatSupportSessionId,
        )}/messages`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            sender_type: "customer",
            sender_id: getCurrentSessionId(),
            message: userMessage,
          }),
        },
      );

      if (!response.ok) {
        throw new Error("Live chat message request failed");
      }
    } catch {
      setMessages([
        ...chatWithUserMessage,
        {
          role: "bot",
          text: HUMAN_SUPPORT_SEND_ERROR_MESSAGE,
          source: "live-chat-agent",
        },
      ]);
    }
  };

  const requestHumanSupport = async () => {
    if (isLoading) {
      return;
    }

    const chatWithUserMessage: Message[] = [
      ...messages,
      { role: "user", text: HUMAN_SUPPORT_ACTION },
    ];

    setHasStartedConversation(true);
    setShowEndConfirmation(false);
    setHumanSupportStep("confirm");
    setHumanSupportName("");
    setHumanSupportPhone("");
    setHumanSupportFormError("");
    liveChatBusyNoticeSessionRef.current = "";
    setMessages(chatWithUserMessage);
    setInput("");
    setIsLoading(true);

    const minimumResponseDelay = wait(BOT_RESPONSE_DELAY_MS);

    await minimumResponseDelay;

    setMessages([
      ...chatWithUserMessage,
      {
        role: "bot",
        text: HUMAN_SUPPORT_CONFIRM_MESSAGE,
        source: "live-chat-agent",
        quickActions: [HUMAN_SUPPORT_CONFIRM_ACTION, HUMAN_SUPPORT_DECLINE_ACTION],
      },
    ]);
    setIsLoading(false);
  };

  const confirmHumanSupport = async () => {
    if (isLoading || humanSupportStep !== "confirm") {
      return;
    }

    const chatWithUserMessage: Message[] = [
      ...messages,
      { role: "user", text: HUMAN_SUPPORT_CONFIRM_ACTION },
    ];

    setShowEndConfirmation(false);
    setMessages(chatWithUserMessage);
    setInput("");
    setIsLoading(true);

    const minimumResponseDelay = wait(BOT_RESPONSE_DELAY_MS);
    const availability = await getLiveChatAvailability().catch(() => null);

    await minimumResponseDelay;

    if (availability?.has_available_agent === false) {
      setHumanSupportStep(null);
      setHumanSupportFormError("");
      setMessages([
        ...chatWithUserMessage,
        {
          role: "bot",
          text: availability.message || HUMAN_SUPPORT_UNAVAILABLE_MESSAGE,
          source: "live-chat-agent",
          quickActions: HUMAN_SUPPORT_FALLBACK_QUICK_ACTIONS,
        },
      ]);
      setIsLoading(false);
      return;
    }

    setHumanSupportStep("details");
    setHumanSupportFormError("");
    setMessages([
      ...chatWithUserMessage,
      {
        role: "bot",
        text: HUMAN_SUPPORT_COLLECTION_MESSAGE,
        source: "live-chat-agent",
      },
    ]);
    setIsLoading(false);
  };

  const declineHumanSupport = async () => {
    if (isLoading || humanSupportStep !== "confirm") {
      return;
    }

    const chatWithUserMessage: Message[] = [
      ...messages,
      { role: "user", text: HUMAN_SUPPORT_DECLINE_ACTION },
    ];

    setShowEndConfirmation(false);
    setHumanSupportStep(null);
    setHumanSupportName("");
    setHumanSupportPhone("");
    setHumanSupportFormError("");
    setMessages(chatWithUserMessage);
    setInput("");
    setIsLoading(true);

    const minimumResponseDelay = wait(BOT_RESPONSE_DELAY_MS);

    await minimumResponseDelay;

    setMessages([
      ...chatWithUserMessage,
      {
        role: "bot",
        text: "",
        menuOnly: true,
        source: "greeting-handler",
        quickActions: MAIN_MENU_QUICK_ACTIONS,
      },
    ]);
    setIsLoading(false);
  };

  const handleHumanSupportFormSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    if (isLoading || humanSupportStep !== "details") {
      return;
    }

    const customerName = humanSupportName.trim();
    const normalizedPhoneNumber =
      normalizeBangladeshMobileNumber(humanSupportPhone);

    if (!customerName) {
      setHumanSupportFormError(HUMAN_SUPPORT_NAME_REQUIRED_MESSAGE);
      return;
    }

    if (!normalizedPhoneNumber) {
      setHumanSupportFormError(HUMAN_SUPPORT_INVALID_PHONE_MESSAGE);
      return;
    }

    const chatWithUserMessage: Message[] = [
      ...messages,
      { role: "user", text: "Support details submitted" },
    ];
    const currentSessionId = getCurrentSessionId();

    setHasStartedConversation(true);
    setShowEndConfirmation(false);
    setHumanSupportStep(null);
    setHumanSupportFormError("");
    setMessages(chatWithUserMessage);
    setInput("");
    setIsLoading(true);

    const minimumResponseDelay = wait(BOT_RESPONSE_DELAY_MS);

    try {
      const response = await fetch(LIVE_CHAT_SESSION_API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: currentSessionId,
          customer_name: customerName,
          customer_phone: normalizedPhoneNumber,
        }),
      });

      if (!response.ok) {
        throw new Error(
          await getApiErrorMessage(response, HUMAN_SUPPORT_UNAVAILABLE_MESSAGE),
        );
      }

      const data = (await response.json()) as LiveChatApiResponse;
      const supportSessionId = data.session?.support_session_id;
      const waitingMessage: Message = {
        role: "bot",
        text: `${HUMAN_SUPPORT_TRANSFER_MESSAGE}\n\n${
          data.message ?? HUMAN_SUPPORT_WAITING_MESSAGE
        }`,
        source: "live-chat-agent",
        liveChatSupportSessionId: supportSessionId,
      };

      if (supportSessionId) {
        localStorage.setItem(
          LIVE_CHAT_SESSION_STORAGE_KEY,
          supportSessionId,
        );
        liveChatLastMessageIdRef.current = 0;
        liveChatBusyNoticeSessionRef.current = "";
        setLiveChatSupportSessionId(supportSessionId);
        setLiveChatStatus(data.session?.status ?? "waiting");
      }

      await minimumResponseDelay;

      setHumanSupportName("");
      setHumanSupportPhone("");
      setMessages([...chatWithUserMessage, waitingMessage]);
    } catch (currentError) {
      await minimumResponseDelay;

      setHumanSupportName("");
      setHumanSupportPhone("");
      const replyText =
        currentError instanceof Error && currentError.message !== "Failed to fetch"
          ? currentError.message
          : ERROR_MESSAGE;
      setMessages([
        ...chatWithUserMessage,
        {
          role: "bot",
          text: replyText,
          source: "live-chat-agent",
          quickActions: HUMAN_SUPPORT_FALLBACK_QUICK_ACTIONS,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (humanSupportStep) {
      return;
    }

    if (liveChatSupportSessionId && liveChatStatus !== "ended") {
      await sendLiveChatCustomerMessage(input);
      return;
    }

    await sendMessage(input);
  };

  const handleScopedBackNavigation = () => {
    void sendMessage(SCOPED_BACK_MESSAGE, {
      silentUserMessage: true,
      replaceLatestBotMessage: true,
    });
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

  const handleLiveChatFeedback = async (
    messageIndex: number,
    feedback: FeedbackValue,
  ) => {
    const message = messages[messageIndex];
    const supportSessionId =
      message?.liveChatSupportSessionId || liveChatSupportSessionId;

    if (message?.role !== "bot" || !supportSessionId) {
      return;
    }

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
      const response = await fetch(
        `${LIVE_CHAT_SESSION_API_URL}/${encodeURIComponent(
          supportSessionId,
        )}/feedback`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ feedback }),
        },
      );

      if (!response.ok) {
        throw new Error("Live chat feedback request failed");
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

  const handleQuickActionClick = (action: string) => {
    if (action === HUMAN_SUPPORT_ACTION) {
      void requestHumanSupport();
      return;
    }

    if (
      action === HUMAN_SUPPORT_CONFIRM_ACTION &&
      humanSupportStep === "confirm"
    ) {
      void confirmHumanSupport();
      return;
    }

    if (
      action === HUMAN_SUPPORT_DECLINE_ACTION &&
      humanSupportStep === "confirm"
    ) {
      void declineHumanSupport();
      return;
    }

    void sendMessage(action);
  };

  const renderQuickActionButton = (action: string) => {
    const isMainAction = isMainMenuQuickAction(action);
    const isDistrictAction = isDistrictQuickAction(action);
    const isWideMainAction = false;

    return (
      <button
        key={action}
        type="button"
        onClick={() => handleQuickActionClick(action)}
        disabled={isLoading}
        className={
          isMainAction
            ? `${isWideMainAction ? "col-span-2" : ""} flex min-h-11 w-full min-w-0 items-center justify-center gap-1.5 rounded-full border border-[#005B96]/40 bg-white px-2.5 py-2 text-center text-[11px] font-semibold leading-tight text-[#004C7D] shadow-sm transition duration-200 hover:-translate-y-0.5 hover:border-[#FFC629]/80 hover:bg-[#FFF8D8] hover:shadow active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0 disabled:active:scale-100`
            : isDistrictAction
              ? "group flex min-h-12 w-full min-w-0 items-center gap-2.5 rounded-xl border border-[#005B96]/20 bg-[#F3F8FC] px-3 py-2.5 text-left text-[13px] font-semibold leading-tight text-[#004C7D] shadow-sm transition duration-200 hover:-translate-y-0.5 hover:border-[#FFC629]/80 hover:bg-[#FFF8D8] hover:shadow-md active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0 disabled:active:scale-100"
            : "min-w-0 rounded-full border border-[#005B96]/15 bg-white px-3 py-2 text-sm font-medium text-[#005B96] shadow-sm transition duration-200 hover:-translate-y-0.5 hover:border-[#FFC629]/80 hover:bg-[#FFF8D8] hover:shadow active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0 disabled:active:scale-100"
        }
      >
        {isMainAction ? (
          <span className="flex h-5 w-5 shrink-0 items-center justify-center text-[#005B96]">
            <QuickActionIcon action={action} className="h-4 w-4" />
          </span>
        ) : null}
        {isDistrictAction ? (
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-white text-[#005B96] ring-1 ring-[#005B96]/15 transition group-hover:bg-[#FFC629] group-hover:text-[#123047]">
            <DistrictPinIcon />
          </span>
        ) : null}
        <span
          className={
            isMainAction
              ? "min-w-0 whitespace-nowrap"
              : isDistrictAction
              ? "min-w-0 flex-1 whitespace-nowrap"
              : "min-w-0 flex-1 break-words [overflow-wrap:anywhere]"
          }
        >
          {action}
        </span>
      </button>
    );
  };

  const shouldRenderServiceActionList = (message: Message) => {
    return isScopedOptionMenuMessage(message);
  };

  const renderServiceActionList = (
    actions: string[],
    showScopedBack = false,
    heading = "Select Services",
  ) => (
    <div className="animate-ebl-service-in mt-2 w-full max-w-[92%] overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="flex items-center justify-between gap-3 border-b border-gray-200 bg-gray-50 px-4 py-2 text-sm font-medium text-gray-600">
        <span>{heading}</span>
        {showScopedBack ? (
          <button
            type="button"
            onClick={handleScopedBackNavigation}
            disabled={isLoading}
            className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-[#005B96]/10 text-sm font-semibold leading-none text-[#005B96] transition hover:bg-[#FFF8D8] hover:text-[#123047] disabled:cursor-not-allowed disabled:opacity-60"
            aria-label="Go back to previous options"
            title="Go back"
          >
            {"<"}
          </button>
        ) : null}
      </div>
      <div className="divide-y divide-gray-200">
        {actions.map((action) => {
          const isLocationAction = isLocationQuickAction(action);
          const isSupportAction = isSupportQuickAction(action);
          const isCampaignAction = isCampaignQuickAction(action);
          const hasLeadingIcon =
            isLocationAction || isSupportAction || isCampaignAction;

          return (
            <button
              key={action}
              type="button"
              onClick={() => handleQuickActionClick(action)}
              disabled={isLoading}
              className={`flex w-full min-w-0 items-center px-4 py-3 text-sm font-medium text-[#005B96] transition duration-200 hover:bg-[#FFF8D8] active:bg-[#FFEFAF] disabled:cursor-not-allowed disabled:opacity-60 ${
                hasLeadingIcon ? "justify-start gap-3 text-left" : "justify-center text-center"
              }`}
            >
              {isLocationAction ? (
                <span className="flex h-5 w-5 shrink-0 items-center justify-center text-[#005B96]">
                  <DistrictPinIcon className="h-4 w-4" />
                </span>
              ) : null}
              {isSupportAction ? (
                <span className="flex h-5 w-5 shrink-0 items-center justify-center text-[#005B96]">
                  <QuickActionIcon action={action} className="h-4 w-4" />
                </span>
              ) : null}
              <span className="block min-w-0 break-words [overflow-wrap:anywhere]">
                {action}
              </span>
            </button>
          );
        })}
      </div>
    </div>
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
            ? "border-[#005B96] bg-[#005B96] text-white"
            : "border-[#005B96]/20 bg-white text-[#005B96] hover:bg-[#005B96]/5"
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
          <span className="text-xs font-medium text-[#005B96]">Saved</span>
        ) : null}
        {message.feedbackStatus === "error" ? (
          <span className="text-xs font-medium text-red-600">
            Could not save
          </span>
        ) : null}
      </div>
    );
  };

  const renderLiveChatEndedControls = (
    message: Message,
    messageIndex: number,
  ) => {
    if (!isHumanSupportEndedMessage(message)) {
      return null;
    }

    const isHelpfulSelected = message.feedback === "helpful";
    const isNotHelpfulSelected = message.feedback === "not_helpful";
    const isSaving = message.feedbackStatus === "saving";

    const feedbackButtonClass = (isSelected: boolean) =>
      `rounded-full border px-3 py-1.5 text-xs font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${
        isSelected
          ? "border-[#005B96] bg-[#005B96] text-white"
          : "border-[#005B96]/20 bg-white text-[#005B96] hover:bg-[#005B96]/5"
      }`;

    return (
      <div className="mt-2 flex max-w-[92%] flex-wrap items-center gap-2">
        <span className="text-xs font-medium text-gray-500">
          Was this helpful?
        </span>
        <button
          type="button"
          onClick={() => {
            void handleLiveChatFeedback(messageIndex, "helpful");
          }}
          disabled={isSaving}
          className={feedbackButtonClass(isHelpfulSelected)}
        >
          Helpful
        </button>
        <button
          type="button"
          onClick={() => {
            void handleLiveChatFeedback(messageIndex, "not_helpful");
          }}
          disabled={isSaving}
          className={feedbackButtonClass(isNotHelpfulSelected)}
        >
          Not helpful
        </button>
        {message.feedbackStatus === "saved" ? (
          <span className="text-xs font-medium text-[#005B96]">Saved</span>
        ) : null}
        {message.feedbackStatus === "error" ? (
          <span className="text-xs font-medium text-red-600">
            Could not save
          </span>
        ) : null}
        <button
          type="button"
          onClick={handleShowMainMenu}
          disabled={isLoading}
          className="rounded-full bg-[#005B96] px-3 py-1.5 text-xs font-semibold text-white shadow-sm transition duration-200 hover:-translate-y-0.5 hover:bg-[#004C7D] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0 disabled:active:scale-100"
        >
          Main menu
        </button>
      </div>
    );
  };

  const renderHumanSupportDetailsForm = (
    message: Message,
    messageIndex: number,
  ) => {
    if (
      humanSupportStep !== "details" ||
      messageIndex !== latestBotMessageIndex ||
      !isHumanSupportMessage(message)
    ) {
      return null;
    }

    return (
      <form
        onSubmit={handleHumanSupportFormSubmit}
        className="animate-ebl-service-in mt-3 w-full max-w-[92%] rounded-2xl border border-[#C8D8DD] bg-white p-3.5 shadow-sm"
      >
        <div className="space-y-3">
          <label className="block">
            <span className="mb-1.5 block text-xs font-semibold text-[#223A42]">
              Name
            </span>
            <input
              type="text"
              value={humanSupportName}
              onChange={(event) => {
                setHumanSupportName(event.target.value);
                setHumanSupportFormError("");
              }}
              disabled={isLoading}
              placeholder="Enter your full name"
              className="w-full rounded-xl border border-[#C8D8DD] bg-[#F8FBFC] px-3 py-2.5 text-sm text-[#223A42] outline-none transition duration-200 placeholder:text-slate-400 focus:border-[#005B96] focus:bg-white focus:ring-2 focus:ring-[#005B96]/10 disabled:cursor-not-allowed disabled:opacity-60"
            />
          </label>

          <label className="block">
            <span className="mb-1.5 block text-xs font-semibold text-[#223A42]">
              Mobile Number
            </span>
            <input
              type="tel"
              value={humanSupportPhone}
              onChange={(event) => {
                setHumanSupportPhone(event.target.value);
                setHumanSupportFormError("");
              }}
              disabled={isLoading}
              placeholder="017XXXXXXXX"
              className="w-full rounded-xl border border-[#C8D8DD] bg-[#F8FBFC] px-3 py-2.5 text-sm text-[#223A42] outline-none transition duration-200 placeholder:text-slate-400 focus:border-[#005B96] focus:bg-white focus:ring-2 focus:ring-[#005B96]/10 disabled:cursor-not-allowed disabled:opacity-60"
            />
          </label>

          {humanSupportFormError ? (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-xs font-medium leading-5 text-red-700">
              {humanSupportFormError}
            </p>
          ) : null}

          <button
            type="submit"
            disabled={isLoading}
            className="inline-flex w-full items-center justify-center rounded-xl bg-[#005B96] px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition duration-200 hover:-translate-y-0.5 hover:bg-[#004C7D] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0 disabled:active:scale-100"
          >
            Continue to Support
          </button>
        </div>
      </form>
    );
  };

  const renderConversationFollowUp = (
    message: Message,
    messageIndex: number,
  ) => {
    if (isLoading) {
      return null;
    }

    if (
      !shouldShowConversationFollowUp(
        message,
        messageIndex,
        latestBotMessageIndex,
      )
    ) {
      return null;
    }

    const previousProductMenu = getPreviousProductMenu(messageIndex);

    return (
      <div className="mt-2 flex max-w-[92%] flex-wrap items-center gap-2">
        <span className="text-xs font-medium text-gray-500">
          {previousProductMenu
            ? buildProductFollowUpQuestion(previousProductMenu.text)
            : "Want to know another product or service?"}
        </span>
        {previousProductMenu ? (
          <>
            <button
              type="button"
              onClick={() => handleShowPreviousProductMenu(previousProductMenu)}
              className="rounded-full bg-[#005B96] px-3 py-1.5 text-xs font-semibold text-white shadow-sm transition duration-200 hover:-translate-y-0.5 hover:bg-[#004C7D] active:scale-[0.98]"
            >
              View options
            </button>
            <button
              type="button"
              onClick={handleShowMainMenu}
              disabled={isLoading}
              className="rounded-full border border-[#005B96]/20 bg-white px-3 py-1.5 text-xs font-semibold text-[#005B96] transition duration-200 hover:-translate-y-0.5 hover:bg-[#005B96]/5 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0 disabled:active:scale-100"
            >
              Main menu
            </button>
          </>
        ) : (
          <button
            type="button"
            onClick={handleShowMainMenu}
            disabled={isLoading}
            className="rounded-full bg-[#005B96] px-3 py-1.5 text-xs font-semibold text-white shadow-sm transition duration-200 hover:-translate-y-0.5 hover:bg-[#004C7D] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0 disabled:active:scale-100"
          >
            Main menu
          </button>
        )}
      </div>
    );
  };

  const setOfferCarouselIndex = (carouselKey: string, offerIndex: number) => {
    setOfferCarouselIndexes((currentIndexes) => ({
      ...currentIndexes,
      [carouselKey]: offerIndex,
    }));
  };

  const moveOfferCarousel = (
    carouselKey: string,
    totalOffers: number,
    direction: -1 | 1,
  ) => {
    if (totalOffers <= 0) {
      return;
    }

    setOfferCarouselIndexes((currentIndexes) => {
      const currentIndex = currentIndexes[carouselKey] ?? 0;
      const nextIndex = (currentIndex + direction + totalOffers) % totalOffers;

      return {
        ...currentIndexes,
        [carouselKey]: nextIndex,
      };
    });
  };

  const renderTypingIndicator = () => (
    <div
      className="animate-ebl-message-in flex items-center gap-2"
      aria-label="Eastern Bank PLC AI Assistant is typing"
      aria-live="polite"
    >
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 border-[#005B96] bg-white">
        <RobotIcon className="h-7 w-7 text-[#005B96]" />
      </div>
      <div className="flex items-center gap-1 rounded-2xl bg-white px-3 py-3 shadow-sm">
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#FFC629]" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#FFC629] [animation-delay:120ms]" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#FFC629] [animation-delay:240ms]" />
      </div>
    </div>
  );

  const latestBotMessageIndex = messages.reduce(
    (latestIndex, message, index) =>
      message.role === "bot" ? index : latestIndex,
    -1,
  );

  const renderLiveChatAgentTypingIndicator = () => (
    <div
      className="animate-ebl-message-in"
      aria-label="EBL Support Agent is typing"
      aria-live="polite"
    >
      <p className="mb-1 ml-1 text-xs font-medium text-[#005B96]">
        Eastern Bank PLC
      </p>
      <div className="inline-flex max-w-[88%] items-center gap-2 rounded-2xl border border-[#C8D8DD] bg-[#EEF4F6] px-4 py-3 text-sm font-medium leading-6 text-[#223A42] shadow-sm">
        <span>EBL Support Agent is typing...</span>
        <span className="flex shrink-0 gap-1" aria-hidden="true">
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#005B96]" />
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#005B96] [animation-delay:120ms]" />
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#005B96] [animation-delay:240ms]" />
        </span>
      </div>
    </div>
  );
  const panelAnimationClass =
    viewTransitionDirection === "forward"
      ? "animate-ebl-panel-forward-in"
      : "animate-ebl-panel-back-in";

  return (
    <>
      <style jsx global>{`
        @keyframes ebl-widget-in {
          from {
            opacity: 0;
            transform: translateY(10px) scale(0.985);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }

        @keyframes ebl-widget-out {
          from {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
          to {
            opacity: 0;
            transform: translateY(10px) scale(0.985);
          }
        }

        @keyframes ebl-message-in {
          from {
            opacity: 0;
            transform: translateY(8px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes ebl-panel-forward-in {
          from {
            opacity: 0;
            filter: blur(1px);
            transform: translateX(14px);
          }
          to {
            opacity: 1;
            filter: blur(0);
            transform: translateX(0);
          }
        }

        @keyframes ebl-panel-back-in {
          from {
            opacity: 0;
            filter: blur(1px);
            transform: translateX(-14px);
          }
          to {
            opacity: 1;
            filter: blur(0);
            transform: translateX(0);
          }
        }

        @keyframes ebl-control-in {
          from {
            opacity: 0;
            transform: scale(0.92);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }

        @keyframes ebl-service-in {
          from {
            opacity: 0;
            transform: translateY(6px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-ebl-widget-in {
          animation: ebl-widget-in 180ms ease-out both;
        }

        .animate-ebl-widget-out {
          animation: ebl-widget-out 180ms ease-in both;
        }

        .animate-ebl-message-in {
          animation: ebl-message-in 180ms ease-out both;
        }

        .animate-ebl-panel-forward-in {
          animation: ebl-panel-forward-in 260ms cubic-bezier(0.22, 1, 0.36, 1)
            both;
        }

        .animate-ebl-panel-back-in {
          animation: ebl-panel-back-in 260ms cubic-bezier(0.22, 1, 0.36, 1)
            both;
        }

        .animate-ebl-control-in {
          animation: ebl-control-in 180ms ease-out both;
        }

        .animate-ebl-service-in {
          animation: ebl-service-in 160ms ease-out both;
        }

        @media (prefers-reduced-motion: reduce) {
          .animate-ebl-widget-in,
          .animate-ebl-widget-out,
          .animate-ebl-message-in,
          .animate-ebl-panel-forward-in,
          .animate-ebl-panel-back-in,
          .animate-ebl-control-in,
          .animate-ebl-service-in {
            animation: none;
          }
        }
      `}</style>

      <button
        type="button"
        title="Chatbot"
        onClick={() => {
          if (isOpen) {
            minimizeChatbot();
            return;
          }

          openChatbot();
        }}
        className="group fixed bottom-5 right-5 z-40 inline-flex h-14 w-14 items-center justify-center rounded-full bg-[#FFC629] p-1 text-white shadow-2xl shadow-[#005B96]/30 ring-2 ring-[#005B96]/40 transition duration-200 hover:-translate-y-0.5 hover:bg-[#F4BC20] hover:shadow-[#005B96]/40 active:scale-[0.96] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#005B96] sm:bottom-6 sm:right-6 sm:h-16 sm:w-16 sm:p-1.5"
        aria-label={isOpen ? chatbotText.close : chatbotText.open}
      >
        <span className="flex h-full w-full items-center justify-center rounded-full bg-[#005B96] p-1.5 transition group-hover:bg-[#004C7D]">
          <span className="flex h-full w-full items-center justify-center rounded-full bg-white text-[#005B96] shadow-inner transition group-hover:bg-[#FFF8D8]">
            <RobotIcon className="h-7 w-7 text-[#005B96] sm:h-8 sm:w-8" />
          </span>
        </span>
        <span className="pointer-events-none absolute bottom-full right-0 mb-3 rounded-md bg-gray-900 px-3 py-1.5 text-xs font-semibold text-white opacity-0 shadow-lg transition group-hover:opacity-100 group-focus-visible:opacity-100">
          Chatbot
        </span>
      </button>

      {isOpen || isWidgetClosing ? (
        <div
          className={`fixed inset-x-3 bottom-4 z-40 max-w-[calc(100vw-1.5rem)] sm:inset-x-auto sm:bottom-5 sm:right-5 sm:w-[360px] sm:max-w-[360px] ${
            isWidgetClosing
              ? "pointer-events-none animate-ebl-widget-out"
              : "animate-ebl-widget-in"
          }`}
          aria-hidden={isWidgetClosing}
        >
          <div
            className="relative flex flex-col overflow-hidden rounded-[1.25rem] border border-[#005B96]/10 bg-white shadow-2xl shadow-black/15 transition-[height,box-shadow] duration-300 ease-[cubic-bezier(0.22,1,0.36,1)]"
            style={{
              height: hasStartedConversation
                ? "min(520px, calc(100dvh - 2rem))"
                : "min(340px, calc(100dvh - 2rem))",
            }}
          >
            <div className="flex shrink-0 items-center justify-between gap-3 bg-[#005B96] px-4 py-3 text-white sm:px-5">
              <div className="flex min-w-0 items-center gap-2">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold sm:text-base">
                    {chatbotText.title}
                  </p>
                  <p className="mt-1 text-sm text-blue-100">
                    {chatbotText.status}
                  </p>
                </div>
              </div>

              <div className="flex shrink-0 items-center gap-2">
                {canGoBackToIntro ? (
                  <button
                    type="button"
                    onClick={handleBackToIntro}
                    className="animate-ebl-control-in inline-flex h-9 w-9 items-center justify-center rounded-full bg-white/10 text-lg font-semibold leading-none ring-1 ring-white/10 transition duration-200 hover:-translate-y-0.5 hover:bg-white/20 active:scale-[0.96]"
                    aria-label="Back to start"
                    title="Back to start"
                  >
                    {"<"}
                  </button>
                ) : null}

                <button
                  type="button"
                  onClick={minimizeChatbot}
                  className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-white/10 transition duration-200 hover:-translate-y-0.5 hover:bg-white/20 active:scale-[0.96]"
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
              <div
                key="conversation-view"
                className={`${panelAnimationClass} flex min-h-0 flex-1 flex-col bg-white px-4 py-4 sm:px-5`}
              >
                <div
                  ref={messageListRef}
                  className="min-h-0 flex-1 space-y-3 overflow-y-auto pr-1"
                >
                  {messages.map((message, index) => {
                    const shouldShowQuickActions =
                      message.role === "bot" &&
                      index === latestBotMessageIndex &&
                      message.quickActions &&
                      message.quickActions.length > 0;
                    const isCorporateTableMessage =
                      message.role === "bot" &&
                      messageHasCorporateChargeTable(message.text);
                    const isComplaintCellMessage =
                      message.role === "bot" &&
                      message.source === "complaint-cell-agent";
                    const isOngoingOffersMessage =
                      message.role === "bot" &&
                      ONGOING_OFFERS_MESSAGE_SOURCES.has(message.source ?? "");
                    const isHumanSupportBotMessage =
                      isHumanSupportMessage(message);
                    const isHumanSupportEndedBotMessage =
                      isHumanSupportEndedMessage(message);
                    const isMenuOnlyMessage =
                      message.role === "bot" && message.menuOnly;
                    const offerCarouselKey = isOngoingOffersMessage
                      ? `offer-${message.chatId ?? index}`
                      : "";
                    const activeOfferIndex = offerCarouselKey
                      ? offerCarouselIndexes[offerCarouselKey] ?? 0
                      : 0;

                    return (
                      <div
                        key={`${message.role}-${index}`}
                        className="animate-ebl-message-in"
                        style={{ animationDelay: `${Math.min(index, 4) * 18}ms` }}
                      >
                        {message.role === "bot" && !isMenuOnlyMessage ? (
                          <p className="mb-1 ml-1 text-xs font-medium text-[#005B96]">
                            Eastern Bank PLC
                          </p>
                        ) : null}
                        {!isMenuOnlyMessage ? (
                          <div
                            className={`${
                              isCorporateTableMessage ||
                              isComplaintCellMessage ||
                              isOngoingOffersMessage
                                ? "max-w-full rounded-xl px-2.5 py-2.5"
                                : "max-w-[88%] rounded-2xl px-4 py-3"
                            } min-w-0 break-words text-sm leading-6 shadow-sm [overflow-wrap:anywhere] ${
                              message.role === "bot"
                                ? isHumanSupportEndedBotMessage
                                  ? "border border-[#F0C84B] bg-[#FFF8D8] font-semibold text-[#4B3A00]"
                                  : isHumanSupportBotMessage
                                    ? "border border-[#C8D8DD] bg-[#EEF4F6] font-medium text-[#223A42]"
                                    : "bg-[#005B96] text-white"
                                : "ml-auto border border-[#B8D4E8] bg-[#EAF3FA] text-[#123047]"
                            }`}
                          >
                            {isComplaintCellMessage
                              ? renderComplaintCellContent(message.text)
                              : isOngoingOffersMessage
                                ? renderOngoingOffersCarouselContent(
                                    message.text,
                                    activeOfferIndex,
                                    (totalOffers) =>
                                      moveOfferCarousel(
                                        offerCarouselKey,
                                        totalOffers,
                                        -1,
                                      ),
                                    (totalOffers) =>
                                      moveOfferCarousel(
                                        offerCarouselKey,
                                        totalOffers,
                                        1,
                                      ),
                                    (offerIndex) =>
                                      setOfferCarouselIndex(
                                        offerCarouselKey,
                                        offerIndex,
                                      ),
                                    handleShowMainMenu,
                                  )
                                : renderMessageContent(message.text)}
                          </div>
                        ) : null}
                        {renderHumanSupportDetailsForm(message, index)}
                        {renderFeedbackControls(message, index)}
                        {renderLiveChatEndedControls(message, index)}
                        {renderConversationFollowUp(message, index)}
                        {shouldShowQuickActions ? (
                          shouldRenderServiceActionList(message) ? (
                            renderServiceActionList(
                              message.quickActions ?? [],
                              isScopedOptionMenuMessage(message),
                              message.source === "campaign-router"
                                ? "Select Campaigns"
                                : "Select Services",
                            )
                          ) : (
                            <div
                              className={
                                isMainMenuQuickActionList(
                                  message.quickActions,
                                )
                                  ? "animate-ebl-service-in mt-3 grid max-w-full grid-cols-2 gap-2"
                                  : isDistrictQuickActionList(
                                      message.quickActions,
                                    )
                                    ? "animate-ebl-service-in mt-3 grid max-w-[92%] grid-cols-1 gap-2.5"
                                  : "animate-ebl-service-in mt-2 flex max-w-[92%] flex-wrap gap-2"
                              }
                            >
                              {(message.quickActions ?? []).map(
                                renderQuickActionButton,
                              )}
                            </div>
                          )
                        ) : null}
                      </div>
                    );
                  })}

                  {isLiveChatAgentTyping
                    ? renderLiveChatAgentTypingIndicator()
                    : null}
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
                    onChange={handleInputChange}
                    placeholder={
                      humanSupportStep === "details"
                        ? "Complete the support form above..."
                        : chatbotText.placeholder
                    }
                    aria-label={chatbotText.placeholder}
                    disabled={isLoading || humanSupportStep === "details"}
                    className="min-w-0 flex-1 rounded-full border border-gray-200 bg-white px-4 py-3 text-sm text-gray-700 outline-none transition duration-200 focus:border-[#005B96] focus:ring-2 focus:ring-[#005B96]/10 disabled:cursor-not-allowed disabled:opacity-60"
                  />

                  <button
                    type="submit"
                    disabled={isLoading || humanSupportStep === "details"}
                    className="inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-[#005B96] text-white shadow-lg shadow-[#005B96]/20 transition duration-200 hover:-translate-y-0.5 hover:bg-[#004C7D] active:scale-[0.96] disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0 disabled:active:scale-100"
                    aria-label={chatbotText.send}
                  >
                    <SendIcon />
                  </button>
                </form>
              </div>
            ) : (
              <div
                key="intro-view"
                className={`${panelAnimationClass} flex min-h-0 flex-1 flex-col bg-[#F6FAFC] px-4 pb-5 pt-5 text-[#123047] sm:px-5`}
              >
                <div className="rounded-2xl border border-[#D7E5EC] bg-white px-4 py-4 shadow-sm">
                  <p className="text-2xl font-bold leading-tight text-[#005B96]">
                    {chatbotText.introTitle}
                  </p>
                  <p className="mt-3 max-w-[280px] text-sm leading-6 text-[#435867]">
                    {chatbotText.introDescription}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={handleStartConversation}
                  className="group mt-4 flex w-full items-center justify-between rounded-2xl border border-[#D7E5EC] bg-white px-4 py-4 text-left text-[#123047] shadow-sm transition duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] hover:-translate-y-0.5 hover:border-[#FFC629] hover:shadow-[0_14px_28px_rgba(0,91,150,0.14)] active:scale-[0.985]"
                >
                  <span>
                    <span className="block text-base font-semibold">
                      {chatbotText.startConversation}
                    </span>
                    <span className="mt-1.5 flex items-center gap-1.5 text-xs font-medium text-[#697B89]">
                      <ClockIcon className="h-3.5 w-3.5 shrink-0 text-[#005B96]" />
                      {chatbotText.responseTime}
                    </span>
                  </span>
                  <span
                    aria-hidden="true"
                    className="inline-flex h-11 w-11 items-center justify-center rounded-full bg-[#FFC629] text-[#123047] shadow-md shadow-[#FFC629]/30 transition duration-200 group-hover:bg-[#F4BC20]"
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
                      className="flex-1 rounded-full bg-[#005B96] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#004C7D]"
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
