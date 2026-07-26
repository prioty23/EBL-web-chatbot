from language_support import expand_bangla_banglish_text


BANKING_KEYWORDS = [
    "account", "savings", "current", "deposit", "fixed deposit",
    "loan", "card", "credit card", "debit card", "prepaid card",
    "transaction", "payment", "refund", "charge", "deducted",
    "atm", "branch", "bank", "banking",
    "mobile banking", "internet banking", "digital banking",
    "support", "hotline", "customer service", "contact",
    "email", "mail", "phone", "number", "call center", "helpline",
    "complaint", "issue", "problem",
    "statement", "balance", "kyc", "documents",
    "nominee", "nid", "passport", "tin",
    "customer support",
    "islamic", "shariah", "sharia", "mudarabah", "wadiah",
    "profit distribution",
    "feature", "features", "benefit", "benefits",
    "student banking", "student account", "campus account",
    "junior savings", "student file", "child future",
    "aspire scheme", "little star",
]

CONTACT_WORDS = [
    "contact", "email", "mail", "phone", "number",
    "hotline", "call center", "helpline", "customer support",
]


FOLLOW_UP_WORDS = [
    "what documents", "documents required", "tell me more",
    "explain that", "what about", "which one",
    "how much", "how long", "why", "feature", "features",
    "benefit", "benefits",
    "that", "this", "it", "those", "them"
]


GREETING_WORDS = [
    "hi", "hello", "hey", "good morning", "good afternoon",
    "good evening", "assalamualaikum", "salam"
]


IDENTITY_QUESTION_PHRASES = [
    "who are you",
    "who r u",
    "what are you",
    "what is your name",
    "what's your name",
    "your name",
    "who am i talking to",
    "who is this",
    "are you a bot",
    "are you chatbot",
    "are you a chatbot",
    "are you human",
    "tell me about yourself",
    "what can you do",
]


def normalize_simple_message(message):
    message = expand_bangla_banglish_text(message)

    return " ".join(
        message.lower()
        .replace("?", " ")
        .replace("!", " ")
        .replace(".", " ")
        .replace(",", " ")
        .strip()
        .split()
    )


def normalize_raw_simple_message(message):
    return " ".join(
        (message or "")
        .lower()
        .replace("?", " ")
        .replace("!", " ")
        .replace(".", " ")
        .replace(",", " ")
        .strip()
        .split()
    )


def is_greeting_only(message):
    raw_message = normalize_raw_simple_message(message)
    expanded_message = normalize_simple_message(message)

    if raw_message in GREETING_WORDS or expanded_message in GREETING_WORDS:
        return True

    greeting_terms = set(GREETING_WORDS + [
        "greeting",
        "salam",
        "আসসালামু",
        "আলাইকুম",
        "সালাম",
        "হ্যালো",
        "হাই",
    ])
    words = set(expanded_message.split())

    if words and words <= greeting_terms:
        return True

    for greeting in GREETING_WORDS:
        if raw_message == greeting:
            return True

    return False


def is_identity_question(message):
    message = normalize_simple_message(message)

    for phrase in IDENTITY_QUESTION_PHRASES:
        if phrase in message:
            return True

    return False


def get_greeting_reply():
    return (
        "Hello! Welcome to Eastern Bank AI Assistant. How may I assist you today?"
    )


def get_identity_reply():
    return (
        "I am Eastern Bank PLC AI Assistant, the EBL chatbot. "
        "I can help with EBL accounts, loans, cards, schedule of charges, "
        "branch/contact information, and complaint guidance."
    )


def is_contact_question(message):
    message = expand_bangla_banglish_text(message).lower()

    for word in CONTACT_WORDS:
        if word in message:
            return True

    return False


def is_banking_related(message):
    message = expand_bangla_banglish_text(message).lower()

    for keyword in BANKING_KEYWORDS:
        if keyword in message:
            return True

    return False


def is_follow_up(message):
    message = expand_bangla_banglish_text(message).lower()

    for word in FOLLOW_UP_WORDS:
        if word in message:
            return True

    return False


def is_allowed_question(message, has_previous_history):
    if is_greeting_only(message):
        return True

    if is_identity_question(message):
        return True

    if is_contact_question(message):
        return True

    if is_banking_related(message):
        return True

    if has_previous_history and is_follow_up(message):
        return True

    return False


def get_off_topic_reply():
    return (
        "This question is not related to banking or the current conversation. "
        "I can help with accounts, cards, loans, deposits, digital banking, "
        "transactions, complaints, or customer support."
    )
