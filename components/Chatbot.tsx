"use client";

import { translations } from "@/data/translations";
import { useEffect, useRef, useState } from "react";
import type { FormEvent, ReactNode } from "react";

type Message = {
  role: "bot" | "user";
  text: string;
  source?: string;
  quickActions?: string[];
  chatId?: number;
  feedback?: FeedbackValue;
  feedbackStatus?: FeedbackStatus;
};

type ChatApiResponse = {
  reply?: string;
  source?: string;
  quick_actions?: string[];
  chat_id?: number;
};

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

const chatbotText = translations.en.chatbot;
const CHATBOT_API_URL = "http://127.0.0.1:8000/chat";
const CHATBOT_FEEDBACK_API_URL = "http://127.0.0.1:8000/chat/feedback";
const ERROR_MESSAGE =
  "Sorry, I could not connect to the chatbot server. Please try again later.";
const MAIN_MENU_QUICK_ACTIONS = [
  "Open an Account",
  "Loan Information",
  "Card Information",
  "Complaint Cell",
  "Schedule of Charges",
  "Interest Rate",
  "Contact Us",
  "Locate Us",
];
const SCOPED_BACK_MESSAGE = "Back";
const COMPLAINT_CELL_DEFAULT_EMAIL = "ccs.cmc@ebl-bd.com";
const COMPLAINT_CELL_DEFAULT_FORM = "https://dgzip.ebl-bd.com/query/";
const COMPLAINT_CELL_DEFAULT_FOOTER =
  "Please enquire us from 10am to 5pm, SUN-THU, (Except Holidays) Or For 24 hours Contact Center: please call 16230 (from any mobile), +8809677716230 (from any local & overseas number)";

const SESSION_STORAGE_KEY = "eastern_ai_session_id";
const BOT_RESPONSE_DELAY_MS = 1400;
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
          className="break-all font-semibold underline underline-offset-2"
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

function renderCorporateChargeCellContent(cellContent: string) {
  const parts = cellContent
    .split(";")
    .map((part) => part.trim())
    .filter(Boolean);

  if (parts.length <= 1) {
    return formatMessage(cellContent);
  }

  return (
    <span className="block space-y-1">
      {parts.map((part, index) => (
        <span key={`${part}-${index}`} className="block">
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

function renderTableCells(
  cells: string[],
  isHeader: boolean,
  rowKey: string,
  isCorporateCharge: boolean,
) {
  const renderedCells: ReactNode[] = [];

  for (let index = 0; index < cells.length; index += 1) {
    if (cells[index] === "" && index > 0) {
      continue;
    }

    let colSpan = 1;

    while (index + colSpan < cells.length && cells[index + colSpan] === "") {
      colSpan += 1;
    }

    const sharedClassName = isCorporateCharge
      ? `border border-emerald-100 px-3 py-2.5 text-left whitespace-normal break-normal [overflow-wrap:normal] [word-break:normal] ${
          isHeader || index === 0 ? "align-middle" : "align-top"
        }`
      : "border border-gray-200 px-3 py-2 align-top text-left whitespace-nowrap";
    const cellKey = `${rowKey}-${index}`;
    const cellContent = cells[index] || "\u00A0";

    if (isHeader) {
      renderedCells.push(
        <th
          key={cellKey}
          colSpan={colSpan > 1 ? colSpan : undefined}
          className={
            isCorporateCharge
              ? `${sharedClassName} bg-emerald-50 font-semibold text-[#064E3B]`
              : `${sharedClassName} bg-gray-50 font-semibold text-gray-900`
          }
        >
          {formatMessage(cellContent)}
        </th>,
      );
    } else {
      renderedCells.push(
        <td
          key={cellKey}
          colSpan={colSpan > 1 ? colSpan : undefined}
          className={
            isCorporateCharge
              ? `${sharedClassName} bg-white text-gray-700 ${
                  index === 0 ? "font-medium" : ""
                }`
              : `${sharedClassName} text-gray-700`
          }
        >
          {isCorporateCharge
            ? renderCorporateChargeCellContent(cellContent)
            : formatMessage(cellContent)}
        </td>,
      );
    }
  }

  return renderedCells;
}

function renderMarkdownTable(headers: string[], rows: string[][], key: string) {
  const isCorporateCharge = isCorporateChargeTable(headers);

  return (
    <div
      key={key}
      className={
        isCorporateCharge
          ? "my-2 max-w-full overflow-x-auto rounded-lg border border-emerald-100 bg-white text-gray-800 shadow-sm"
          : "my-2 max-w-full overflow-x-auto rounded-lg border border-gray-200 bg-white text-gray-800 shadow-sm"
      }
    >
      <table
        className={
          isCorporateCharge
            ? "min-w-[680px] table-fixed border-collapse text-xs leading-5"
            : "min-w-full border-collapse text-xs leading-5"
        }
      >
        {isCorporateCharge ? (
          <colgroup>
            <col style={{ width: "30%" }} />
            <col style={{ width: "35%" }} />
            <col style={{ width: "35%" }} />
          </colgroup>
        ) : null}
        <thead>
          <tr>
            {renderTableCells(headers, true, `${key}-header`, isCorporateCharge)}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={`${key}-row-${rowIndex}`}>
              {renderTableCells(
                row,
                false,
                `${key}-row-${rowIndex}`,
                isCorporateCharge,
              )}
            </tr>
          ))}
        </tbody>
      </table>
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
    <div key={`${contact.name}-${index}`} className="px-3 py-3">
      <p className="text-sm font-semibold leading-5 text-[#005B43]">
        {contact.name}
      </p>
      <dl className="mt-2 space-y-1.5 text-xs leading-5">
        <div>
          <dt className="inline font-semibold text-gray-500">Designation: </dt>
          <dd className="inline text-gray-800">
            {formatMessage(contact.designation)}
          </dd>
        </div>
        <div>
          <dt className="inline font-semibold text-gray-500">Email: </dt>
          <dd className="inline break-all text-gray-800">
            {formatMessage(contact.email)}
          </dd>
        </div>
        <div>
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
    <div className="space-y-3">
      {hasContactSections ? (
        details.sections.map((section) => (
          <div
            key={section.title}
            className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm"
          >
            <div className="border-b border-gray-200 bg-gray-50 px-3 py-2 text-center text-xs font-semibold leading-5 text-gray-800">
              {section.title}
            </div>
            <div className="divide-y divide-gray-100">
              {section.contacts.map(renderComplaintContact)}
            </div>
          </div>
        ))
      ) : (
        <div className="space-y-1.5 text-sm leading-6 text-white">
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
      <div className="rounded-xl border border-[#F0C84B] bg-[#FFF8D8] px-3 py-2.5 shadow-sm">
        <p className="text-xs font-semibold leading-5 text-[#4B3A00]">
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

function isMainMenuQuickAction(action: string) {
  return MAIN_MENU_QUICK_ACTIONS.some(
    (mainAction) => mainAction.toLowerCase() === action.toLowerCase(),
  );
}

function isMainMenuQuickActionList(actions: string[] | undefined) {
  if (!actions?.length) {
    return false;
  }

  return actions.every(isMainMenuQuickAction);
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

function isScopedOptionMenuMessage(message: Message | null) {
  if (!message || message.role !== "bot" || !message.quickActions?.length) {
    return false;
  }

  return (
    hasMenuSource(message, SCHEDULE_CHARGE_MENU_SOURCES) ||
    hasMenuSource(message, INTEREST_RATE_MENU_SOURCES) ||
    isScheduleChargeOptionText(message.text, message.quickActions) ||
    isInterestRateOptionText(message.text, message.quickActions)
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

  const handleShowMainMenu = () => {
    setShowEndConfirmation(false);
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

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
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

  const renderQuickActionButton = (action: string) => {
    const isMainAction = isMainMenuQuickAction(action);

    return (
      <button
        key={action}
        type="button"
        onClick={() => {
          void sendMessage(action);
        }}
        disabled={isLoading}
        className={
          isMainAction
            ? "flex min-h-11 w-full items-center gap-2 rounded-full border border-[#006A4E]/70 bg-white px-3 py-2 text-left text-[11px] font-semibold leading-tight text-[#005B43] shadow-sm transition hover:bg-[#006A4E]/5 hover:shadow disabled:cursor-not-allowed disabled:opacity-60"
            : "rounded-full border border-[#006A4E]/15 bg-white px-3 py-2 text-sm font-medium text-[#006A4E] shadow-sm transition hover:bg-[#006A4E]/5 disabled:cursor-not-allowed disabled:opacity-60"
        }
      >
        {isMainAction ? (
          <span className="flex h-6 w-6 shrink-0 items-center justify-center text-[#006A4E]">
            <QuickActionIcon action={action} />
          </span>
        ) : null}
        <span className="min-w-0 flex-1">{action}</span>
      </button>
    );
  };

  const shouldRenderServiceActionList = (message: Message) => {
    return isScopedOptionMenuMessage(message);
  };

  const renderServiceActionList = (
    actions: string[],
    showScopedBack = false,
  ) => (
    <div className="mt-2 w-full max-w-[92%] overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="flex items-center justify-between gap-3 border-b border-gray-200 bg-gray-50 px-4 py-2 text-sm font-medium text-gray-600">
        <span>Select Services</span>
        {showScopedBack ? (
          <button
            type="button"
            onClick={handleScopedBackNavigation}
            disabled={isLoading}
            className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-[#006A4E]/10 text-sm font-semibold leading-none text-[#006A4E] transition hover:bg-[#006A4E]/15 disabled:cursor-not-allowed disabled:opacity-60"
            aria-label="Go back to previous options"
            title="Go back"
          >
            {"<"}
          </button>
        ) : null}
      </div>
      <div className="divide-y divide-gray-200">
        {actions.map((action) => (
          <button
            key={action}
            type="button"
            onClick={() => {
              void sendMessage(action);
            }}
            disabled={isLoading}
            className="block w-full px-4 py-3 text-center text-sm font-medium text-[#006A4E] transition hover:bg-[#006A4E]/5 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {action}
          </button>
        ))}
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
              className="rounded-full bg-[#006A4E] px-3 py-1.5 text-xs font-semibold text-white shadow-sm transition hover:bg-[#00543E]"
            >
              View options
            </button>
            <button
              type="button"
              onClick={handleShowMainMenu}
              disabled={isLoading}
              className="rounded-full border border-[#006A4E]/20 bg-white px-3 py-1.5 text-xs font-semibold text-[#006A4E] transition hover:bg-[#006A4E]/5 disabled:cursor-not-allowed disabled:opacity-60"
            >
              Main menu
            </button>
          </>
        ) : (
          <button
            type="button"
            onClick={handleShowMainMenu}
            disabled={isLoading}
            className="rounded-full bg-[#006A4E] px-3 py-1.5 text-xs font-semibold text-white shadow-sm transition hover:bg-[#00543E] disabled:cursor-not-allowed disabled:opacity-60"
          >
            Main menu
          </button>
        )}
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

  const latestBotMessageIndex = messages.reduce(
    (latestIndex, message, index) =>
      message.role === "bot" ? index : latestIndex,
    -1,
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

                    return (
                      <div key={`${message.role}-${index}`}>
                        {message.role === "bot" ? (
                          <p className="mb-1 ml-1 text-xs font-medium text-[#006A4E]">
                            Eastern Bank PLC
                          </p>
                        ) : null}
                        <div
                          className={`${
                            isCorporateTableMessage || isComplaintCellMessage
                              ? "max-w-full rounded-xl px-2.5 py-2.5"
                              : "max-w-[88%] rounded-2xl px-4 py-3"
                          } text-sm leading-6 shadow-sm ${
                            message.role === "bot"
                              ? "bg-[#006A4E] text-white"
                              : "ml-auto bg-gray-100 text-gray-700"
                          }`}
                        >
                          {isComplaintCellMessage
                            ? renderComplaintCellContent(message.text)
                            : renderMessageContent(message.text)}
                        </div>
                        {renderFeedbackControls(message, index)}
                        {renderConversationFollowUp(message, index)}
                        {shouldShowQuickActions ? (
                          shouldRenderServiceActionList(message) ? (
                            renderServiceActionList(
                              message.quickActions ?? [],
                              isScopedOptionMenuMessage(message),
                            )
                          ) : (
                            <div
                              className={
                                isMainMenuQuickActionList(
                                  message.quickActions,
                                )
                                  ? "mt-3 grid max-w-[92%] grid-cols-2 gap-2.5"
                                  : "mt-2 flex max-w-[92%] flex-wrap gap-2"
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
