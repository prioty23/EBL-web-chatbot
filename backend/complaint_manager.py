import re

from language_support import expand_bangla_banglish_text


DIRECT_COMPLAINT_TERMS = [
    "complaint",
    "complain",
    "issue",
    "problem",
]

COMPLAINT_STATUS_TERMS = [
    "complaint status",
    "status of complaint",
    "track complaint",
    "check complaint",
    "complaint id",
    "my complaint status",
    "cmp-",
]

COMPLAINT_CELL_TERMS = [
    "complaint cell",
    "complaintcell",
    "complaint management cell",
    "complaint mail",
    "complaint email",
    "complain mail",
    "complain email",
    "complaint form",
    "complaint link",
    "complaint page",
    "query complaint",
]

COMPLAINT_CREATE_TERMS = [
    "create complaint",
    "submit complaint",
    "file complaint",
    "lodge complaint",
    "raise complaint",
    "make complaint",
    "want to complain",
    "need to complain",
    "complain about",
    "complaint about",
    "report issue",
]

ISSUE_INDICATORS = [
    "failed",
    "failure",
    "deducted",
    "charged",
    "blocked",
    "locked",
    "stuck",
    "pending",
    "declined",
    "rejected",
    "missing",
    "lost",
    "stolen",
    "unauthorized",
    "fraud",
    "wrong",
    "error",
    "refund",
    "dispute",
    "delayed",
    "delay",
    "misbehaved",
    "rude",
    "bad service",
    "not received",
    "did not receive",
    "cannot",
    "can't",
    "unable",
    "not working",
    "does not work",
    "not added",
    "not credited",
    "not showing",
    "not posted",
    "not cleared",
    "not transferred",
    "not updated",
    "not activated",
    "not opened",
    "not delivered",
    "still pending",
    "double charge",
    "charged twice",
]

BANKING_CONTEXT_TERMS = [
    "account",
    "card",
    "atm",
    "cash",
    "deposit",
    "deposited",
    "transaction",
    "transfer",
    "payment",
    "app",
    "skybanking",
    "online banking",
    "internet banking",
    "mobile banking",
    "cheque",
    "check",
    "branch",
    "loan",
    "emi",
    "remittance",
    "fee",
    "charge",
    "balance",
    "login",
    "password",
    "otp",
    "pin",
    "debit",
    "credit",
    "refund",
    "statement",
    "salary",
    "dps",
    "fdr",
    "customer service",
    "hotline",
    "ebl",
    "bank",
    "banking",
    "money",
]


def contains_any(message, keywords):
    message = expand_bangla_banglish_text(message).lower()
    return any(keyword in message for keyword in keywords)


def has_issue_indicator(message):
    message = expand_bangla_banglish_text(message).lower()
    return contains_any(message, ISSUE_INDICATORS)


def has_banking_context(message):
    message = expand_bangla_banglish_text(message).lower()
    return contains_any(message, BANKING_CONTEXT_TERMS)


def looks_like_customer_issue(message):
    message = expand_bangla_banglish_text(message).lower().strip()

    return (
        contains_any(message, DIRECT_COMPLAINT_TERMS)
        or (has_issue_indicator(message) and has_banking_context(message))
    )


def is_customer_complaint_request(message):
    message = expand_bangla_banglish_text(message).lower().strip()

    if contains_any(message, COMPLAINT_STATUS_TERMS):
        return False

    if contains_any(message, COMPLAINT_CELL_TERMS):
        return False

    if has_specific_complaint_details(message):
        return True

    if contains_any(message, COMPLAINT_CREATE_TERMS):
        return True

    return contains_any(message, DIRECT_COMPLAINT_TERMS) and has_banking_context(
        message
    )


def has_specific_complaint_details(message):
    message = expand_bangla_banglish_text(message).lower().strip()

    return has_issue_indicator(message) and has_banking_context(message)


def is_deposit_not_credited_issue(message):
    message = expand_bangla_banglish_text(message).lower()

    deposit_words = [
        "deposit",
        "deposited",
        "cash",
        "money",
    ]
    missing_credit_phrases = [
        "not added",
        "not credited",
        "not showing",
        "not posted",
        "missing",
        "still now",
    ]

    return (
        any(word in message for word in deposit_words)
        and any(phrase in message for phrase in missing_credit_phrases)
    )


def has_enough_complaint_details(message):
    message = expand_bangla_banglish_text(message).lower().strip()

    if len(message.split()) < 2:
        return False

    return has_specific_complaint_details(message)


def get_issue_type(message):
    message = expand_bangla_banglish_text(message).lower()

    if is_deposit_not_credited_issue(message):
        return "Deposit Not Credited Issue"

    if (
        "fraud" in message
        or "unauthorized" in message
        or "hacked" in message
        or "suspicious" in message
        or "transaction not mine" in message
    ):
        return "Security / Unauthorized Transaction Issue"

    if "card" in message:
        return "Card Issue"

    if "atm" in message:
        return "ATM Issue"

    if "cash" in message and contains_any(message, ["withdraw", "withdrawal", "atm"]):
        return "ATM Issue"

    if contains_any(message, ["app", "skybanking", "online banking", "internet banking", "mobile banking", "login"]):
        return "Digital Banking Issue"

    if "cheque" in message or "check" in message:
        return "Cheque Issue"

    if "remittance" in message:
        return "Remittance Issue"

    if "loan" in message or "emi" in message:
        return "Loan Issue"

    if contains_any(message, ["transaction", "payment", "transfer", "deducted", "charged", "refund"]):
        return "Transaction Issue"

    if "deposit" in message or "deposited" in message:
        return "Deposit Issue"

    if "account" in message:
        return "Account Issue"

    if "branch" in message or "customer service" in message or "hotline" in message:
        return "Service Issue"

    if "fee" in message or "charge" in message:
        return "Fee / Charge Issue"

    return "General Complaint"


def build_complaint_created_reply(complaint):
    return (
        "Your complaint has been created successfully.\n\n"
        f"Complaint ID: {complaint['complaint_id']}\n"
        f"Issue Type: {complaint['issue_type']}\n"
        f"Status: {complaint['status']}\n"
        f"Created At: {complaint['created_at']}\n\n"
        "Please save your complaint ID for future status checking. "
        "Do not share OTP, PIN, password, CVV or full card number."
    )


def extract_complaint_id(message):
    match = re.search(r"CMP-\d{8}-\d{4}", message.upper())

    if match:
        return match.group(0)

    return None


def build_complaint_status_reply(complaint):
    return (
        "Complaint status found.\n\n"
        f"Complaint ID: {complaint['complaint_id']}\n"
        f"Issue Type: {complaint['issue_type']}\n"
        f"Status: {complaint['status']}\n"
        f"Created At: {complaint['created_at']}\n"
        f"Last Updated: {complaint['updated_at']}"
    )


def build_complaint_not_found_reply(complaint_id):
    return (
        f"I could not find any complaint with this ID: {complaint_id}\n\n"
        "Please check the complaint ID and try again."
    )


def build_missing_complaint_id_reply():
    return (
        "Please provide your complaint ID to check the status.\n\n"
        "Example: CMP-20260628-0001"
    )


def is_complaint_confirmation_yes(message):
    message = expand_bangla_banglish_text(message).lower().strip()

    yes_exact_words = [
        "yes",
        "ok",
        "okay",
        "sure",
        "create",
        "submit",
        "do it",
    ]

    yes_phrases = [
        "yes create",
        "yes please",
        "create complaint",
        "submit complaint",
        "ok create",
        "okay create",
        "please create",
        "create it",
        "please submit",
    ]

    if message in yes_exact_words:
        return True

    for phrase in yes_phrases:
        if phrase in message:
            return True

    return False


def is_complaint_confirmation_no(message):
    message = expand_bangla_banglish_text(message).lower().strip()

    no_exact_words = [
        "no",
        "cancel",
        "stop",
        "later",
    ]

    no_phrases = [
        "not now",
        "do not create",
        "don't create",
        "dont create",
        "no need",
        "cancel it",
        "stop it",
        "create later",
    ]

    if message in no_exact_words:
        return True

    for phrase in no_phrases:
        if phrase in message:
            return True

    return False


def build_complaint_confirmation_reply(issue_type):
    return (
        "I can create a complaint record for this issue.\n\n"
        "Do you want me to create the complaint record now?\n"
        "Please reply with Yes to create or No to cancel.\n\n"
        "For your safety, do not share OTP, PIN, password, CVV or full card number."
    )


def build_complaint_cancelled_reply():
    return (
        "Okay, I will not create a complaint record now.\n\n"
        "If you want to create it later, please describe the issue again and confirm that you want to create a complaint."
    )


def extract_email(message):
    match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        message
    )

    if match:
        return match.group(0)

    return ""


def build_missing_email_reply():
    return (
        "Please provide your email address so I can create the complaint record "
        "and send future status updates.\n\n"
        "Example: my email is customer@example.com\n\n"
        "For your safety, do not share OTP, PIN, password, CVV or full card number."
    )
