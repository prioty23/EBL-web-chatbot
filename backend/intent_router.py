from complaint_manager import looks_like_customer_issue
from language_support import expand_bangla_banglish_text


def contains_any(message, keywords):
    message = expand_bangla_banglish_text(message).lower()

    for keyword in keywords:
        if keyword in message:
            return True

    return False


def detect_intent(message):
    message = expand_bangla_banglish_text(message).lower().strip()

    # Online application link
    if contains_any(message, [
        "apply online",
        "online apply",
        "online application",
        "application link",
        "apply link",
        "apply now",
        "online form",
        "apply card online",
        "apply loan online",
        "apply account online",
    ]):
        return "online_apply"

    # Complaint status check
    if contains_any(message, [
        "complaint status",
        "status of complaint",
        "track complaint",
        "check complaint",
        "complaint id",
        "my complaint",
        "cmp-"
    ]):
        return "complaint_status"

    # Memory recall
    if contains_any(message, [
        "what did i ask earlier",
        "what did i ask before",
        "previous question",
        "earlier question",
        "last question",
        "last time",
        "first text",
        "first message",
        "first question",
        "oldest message",
        "oldest question",
        "what did i ask first",
        "what did i first ask",
        "remember what i asked",
        "what was my previous",
        "what was my first text",
        "what was my first message",
        "what was my first question",
        "show my recent questions",
        "what complaint did i create",
        "previous complaint",
        "last complaint",
        "complaint i created before",
        "what issue did i submit"
    ]):
        return "memory_question"

    # Contact information
    if contains_any(message, [
        "email",
        "mail",
        "hotline",
        "phone",
        "number",
        "contact",
        "customer support",
        "customer service",
        "call center",
        "helpline"
    ]):
        return "contact_information"

    # Urgent card or security issue
    if contains_any(message, [
        "lost card",
        "card lost",
        "stolen card",
        "card stolen",
        "block card",
        "freeze card",
        "unauthorized transaction",
        "fraud transaction",
        "fraud",
        "hacked",
        "account hacked",
        "suspicious transaction",
        "transaction not mine"
    ]):
        return "urgent_card_issue"

    # Customer issue / complaint creation
    if looks_like_customer_issue(message):
        return "complaint_create"

    # Complaint creation
    if contains_any(message, [
        "complaint",
        "complain",
        "issue",
        "problem",
        "charged twice",
        "double charge",
        "deducted",
        "failed transaction",
        "transaction failed",
        "refund",
        "atm cash did not come",
        "cash not received",
        "payment failed",
        "card problem",
        "deposit not added",
        "cash deposit not added",
        "not added to my account",
        "deposit not credited",
        "cash deposit not credited",
        "not credited to my account",
        "deposit missing",
        "cash deposit missing",
        "money not added",
        "money not credited",
        "not showing in my account"
    ]):
        return "complaint_create"

    # Fees, charges, and schedule-of-charges questions
    if contains_any(message, [
        "fee",
        "fees",
        "charge",
        "charges",
        "schedule of charges",
        "vat",
        "maintenance fee",
        "annual fee",
        "minimum balance",
        "closing charge",
        "account closing",
    ]):
        return "charge_information"

    # Islamic banking
    if contains_any(message, [
        "islamic banking",
        "islamic account",
        "islamic accounts",
        "islamic deposit",
        "islamic deposits",
        "islamic finance",
        "islamic loan",
        "islamic card",
        "islamic cards",
        "shariah",
        "sharia",
        "mudarabah",
        "wadiah",
        "profit distribution",
    ]):
        return "islamic_banking"

    # Student banking
    if contains_any(message, [
        "student banking",
        "student account",
        "junior savings",
        "junior account",
        "campus account",
        "student file",
        "child future plan",
        "aspire scheme",
        "little star",
    ]):
        return "student_banking"

    # Retail banking menu/services
    if contains_any(message, [
        "retail banking",
        "retail services",
        "retail products",
        "retail account options",
        "retail accounts",
        "insta account",
        "insta banking",
        "priority banking",
        "power banking",
        "super saver",
        "women banking",
        "agent banking",
        "payroll banking",
        "bancassurance",
        "retail alliance",
        "skypay",
        "missed call alert",
        "365 plus",
    ]):
        return "retail_banking"

    # Account information
    if contains_any(message, [
        "how can i open an account",
        "how to open an account",
        "open an account",
        "open account",
        "account opening",
        "create account",
        "new account",
        "bank account",
        "savings account",
        "current account",
        "documents required",
        "what documents",
        "nid",
        "passport",
        "nominee",
        "kyc"
    ]):
        return "account_information"

    # Card information
    if contains_any(message, [
        "card",
        "credit card",
        "debit card",
        "prepaid card",
        "dual currency",
        "dual currency card",
        "dollar endorsement",
        "foreign currency endorsement",
        "passport endorsement",
        "endorsement",
        "visa",
        "mastercard",
        "card service"
    ]):
        return "card_information"

    # Loan information
    if contains_any(message, [
        "loan",
        "loans",
        "oan",
        "oans",
        "loam",
        "lone",
        "personal loan",
        "home loan",
        "auto loan",
        "car loan",
        "sme loan",
        "retail loan"
    ]):
        return "loan_information"

    # Deposit information
    if contains_any(message, [
        "deposit",
        "fixed deposit",
        "fdr",
        "dps",
        "savings scheme",
        "term deposit"
    ]):
        return "deposit_information"

    # Digital banking
    if contains_any(message, [
        "digital banking",
        "internet banking",
        "mobile banking",
        "skybanking",
        "app",
        "online banking"
    ]):
        return "digital_banking"

    # Branch / ATM locator
    if contains_any(message, [
        "branch",
        "atm",
        "locator",
        "location",
        "near me",
        "where is",
        "nearest branch",
        "nearest atm"
    ]):
        return "branch_locator"

    return "off_topic"
