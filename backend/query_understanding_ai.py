import json
import os

from dotenv import load_dotenv
from groq import Groq

from intent_router import detect_intent
from language_support import (
    expand_bangla_banglish_text,
    has_bangla_script,
)


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

ALLOWED_INTENTS = [
    "greeting",
    "account_information",
    "card_information",
    "loan_information",
    "deposit_information",
    "digital_banking",
    "branch_locator",
    "charge_information",
    "contact_information",
    "online_apply",
    "complaint_create",
    "complaint_status",
    "memory_question",
    "off_topic",
    "general_information",
]

SYSTEM_PROMPT = """
You are only a query understanding engine for Eastern Bank PLC chatbot.
Your job is to classify the user message and rewrite it into a clean English search query for searching EBL website database.
Do not answer the customer.
Do not use general banking knowledge.
Return only valid JSON.
No markdown.
No explanation.

Allowed intent values:
- greeting
- account_information
- card_information
- loan_information
- deposit_information
- digital_banking
- branch_locator
- charge_information
- contact_information
- online_apply
- complaint_create
- complaint_status
- memory_question
- off_topic
- general_information

The JSON must contain exactly these keys:
intent
search_query
language

Language should be a short label such as english, banglish, bangla, broken_english, or unknown.
The search_query should be clean English terms useful for searching Eastern Bank PLC website content.
For case-specific questions, the search_query must preserve both:
- the EBL product/service the customer is asking about
- the exact information type requested, such as process, required documents, requirements, eligibility, fees, limits, features, application, activation, or recommendation
Example: "How can I do dollar endorsement?" -> "EBL dollar endorsement process"
Example: "What documents are required for dollar endorsement?" -> "EBL dollar endorsement required documents"
Example: "I am a student, which card will be perfect for me?" -> "EBL student card recommendation suitable card"
Example follow-up after a product was discussed: keep the requested detail words clearly, such as "required documents" or "process".

Intent guidance:
- Understand Banglish, Bangla-style English, broken English, spelling mistakes, and short customer messages semantically.
- Banglish examples:
  "charge koto", "account khulte chai", "card hariye geche",
  "platinum card er supplementary charge", "deposit rate koto".
- Bangla examples:
  "সঞ্চয়ী হিসাবের ফি কত", "কার্ড হারিয়ে গেছে", "লোন রেট কত",
  "শাখা কোথায়", "অনলাইন আবেদন লিংক".
- Use account_information for broad account opening and account document requirement questions, even when the customer does not use formal English or does not write the word "open".
- Do not classify broad account opening questions as online_apply.
- Use online_apply only when the customer explicitly asks for an online application link, application form, apply link, or apply online page.
- Use complaint_create when the customer reports a banking problem, failed transaction, double charge, duplicate deduction, money deducted, refund issue, card problem, ATM problem, app problem, or service issue.
- Use card_information for broad card help or card product questions.
- Use charge_information when the customer asks about fees, charges, VAT, minimum balance, annual fee, maintenance fee, closing charge, or schedule of charges.
- Use memory_question when the customer asks what they asked before, their previous/last/recent question, or their first text/message/question in this chat session.
"""


def build_fallback_understanding(message):
    fallback_intent = detect_intent(message)
    expanded_message = expand_bangla_banglish_text(message)
    language = "bangla" if has_bangla_script(message) else "unknown"

    if language == "unknown" and expanded_message != message:
        language = "banglish"

    return {
        "intent": fallback_intent,
        "search_query": expanded_message,
        "language": language,
    }


def parse_groq_json(content):
    if not content:
        raise ValueError("Groq returned an empty response")

    parsed = json.loads(content.strip())

    if not isinstance(parsed, dict):
        raise ValueError("Groq response JSON is not an object")

    intent = str(parsed.get("intent", "")).strip()
    search_query = str(parsed.get("search_query", "")).strip()
    language = str(parsed.get("language", "")).strip() or "unknown"

    if intent not in ALLOWED_INTENTS:
        raise ValueError("Groq returned an unsupported intent")

    if not search_query:
        raise ValueError("Groq returned an empty search query")

    return {
        "intent": intent,
        "search_query": search_query,
        "language": language,
    }


def normalize_understood_query(message, understood_query):
    fallback_intent = detect_intent(message)

    guardrail_fallback_intents = [
        "complaint_create",
        "complaint_status",
        "urgent_card_issue",
        "contact_information",
        "branch_locator",
        "charge_information",
        "card_information",
        "memory_question",
    ]

    if fallback_intent in guardrail_fallback_intents:
        understood_query = dict(understood_query)
        understood_query["intent"] = fallback_intent
        understood_query["search_query"] = message
        return understood_query

    if fallback_intent == "account_information" and understood_query.get("intent") == "online_apply":
        understood_query = dict(understood_query)
        understood_query["intent"] = "account_information"
        understood_query["search_query"] = (
            "EBL account opening requirements account types savings current deposit online application"
        )
        return understood_query

    return understood_query


def understand_user_query_with_groq(message):
    if not GROQ_API_KEY:
        return build_fallback_understanding(message)

    try:
        client = Groq(api_key=GROQ_API_KEY)

        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": message,
                },
            ],
            temperature=0,
            max_completion_tokens=250,
        )

        content = chat_completion.choices[0].message.content
        understood_query = parse_groq_json(content)
        return normalize_understood_query(message, understood_query)

    except Exception as error:
        print("QUERY UNDERSTANDING ERROR:", repr(error))
        return build_fallback_understanding(message)
