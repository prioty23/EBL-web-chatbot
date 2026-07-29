"""Backend entrypoint."""

import re
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from schemas import (
    ChatRequest,
    ChatFeedbackRequest,
    ChatResponse,
    ComplaintStatusUpdateRequest,
)

from email_sender import send_final_status_email
from complaint_email_scheduler import start_complaint_email_scheduler

from safety import contains_sensitive_data, get_safety_response

from language_support import expand_bangla_banglish_text

from groq_client import (
    generate_groq_customer_service_reply,
    update_conversation_summary,
)

from database import (
    save_chat,
    get_chat_history,
    get_website_information,
    get_website_information_by_page_names,
    get_website_information_by_page_urls,
    save_website_text,
    clear_website_information,
    get_session_summary,
    save_session_summary,
    save_complaint,
    save_chat_feedback,
    get_complaint_by_id,
    update_complaint_status,
    get_recent_user_messages,
    get_first_user_message,
    get_latest_complaint_by_session,
    search_website_information,
    save_pending_complaint,
    get_pending_complaint,
    delete_pending_complaint,
    mark_final_status_email_sent,
)

from website_scraper import get_internal_links_from_website, get_text_from_website

from topic_guard import (
    is_allowed_question,
    get_off_topic_reply,
    is_greeting_only,
    get_greeting_reply,
    is_identity_question,
    get_identity_reply,
)

from query_understanding_ai import understand_user_query_with_groq

from agent_actions import (
    get_contact_reply,
    get_online_apply_reply,
    get_branch_locator_reply,
    get_urgent_card_reply,
    get_complaint_start_reply,
)

from complaint_manager import (
    has_enough_complaint_details,
    get_issue_type,
    build_complaint_created_reply,
    extract_complaint_id,
    build_complaint_status_reply,
    build_complaint_not_found_reply,
    build_missing_complaint_id_reply,
    is_complaint_confirmation_yes,
    is_complaint_confirmation_no,
    build_complaint_confirmation_reply,
    build_complaint_cancelled_reply,
    extract_email,
    build_missing_email_reply,
)

from knowledge_router import select_knowledge_pages

from charge_database import (
    answer_card_charge_question_from_db,
    answer_exact_card_charge,
    answer_exact_corporate_charge,
    answer_exact_corporate_group_charge,
    answer_exact_retail_charge,
    answer_exact_sme_category_charge,
    answer_exact_sme_charge,
    answer_charge_question_from_db,
    card_charge_category_display_label,
    card_charge_category_label,
    card_charge_category_options,
    card_charge_name_label,
    card_charge_names,
    card_charge_product_label,
    card_charge_product_matches,
    card_charge_products,
    corporate_charge_category_label,
    corporate_charge_category_display_label,
    corporate_charge_group_categories,
    corporate_charge_group_key,
    corporate_charge_group_label,
    corporate_charge_group_options,
    corporate_charge_name_for_group_label,
    corporate_charge_name_label,
    corporate_charge_names,
    corporate_charge_names_for_group,
    corporate_charge_product_label,
    corporate_charge_product_matches,
    corporate_charge_products,
    ensure_charge_database_ready,
    import_charge_csvs,
    retail_charge_category_label,
    retail_charge_group_categories,
    retail_charge_group_key,
    retail_charge_group_label,
    retail_charge_group_options,
    retail_charge_name_label,
    retail_charge_names,
    retail_charge_product_label,
    retail_charge_product_matches,
    retail_charge_products,
    sme_charge_category_label,
    sme_charge_group_categories,
    sme_charge_group_key,
    sme_charge_group_label,
    sme_charge_group_options,
    sme_charge_name_for_category_label,
    sme_charge_name_label,
    sme_charge_names,
    sme_charge_names_for_category,
    sme_charge_product_label,
    sme_charge_product_matches,
    sme_charge_products,
)

from deposit_rate_database import (
    answer_deposit_rate_question_from_db,
    build_broad_rate_clarification,
    build_deposit_rate_menu_reply,
    deposit_rate_followup_context,
    ensure_deposit_rate_database_ready,
    import_deposit_rate_csvs,
    is_deposit_rate_question,
    query_mentions_known_deposit_rate_product,
)

from lending_rate_database import (
    answer_lending_rate_question_from_db,
    build_broad_lending_rate_clarification,
    build_lending_rate_menu_reply,
    ensure_lending_rate_database_ready,
    import_lending_rate_csvs,
    is_lending_rate_question,
)

from account_database import (
    ensure_account_types_ready,
    find_account_category,
    get_account_categories,
    get_account_names,
    import_account_types,
)

from loan_database import (
    ensure_loan_types_ready,
    find_loan_category,
    get_loan_categories,
    get_loan_names,
    import_loan_types,
)

from local_knowledge import answer_local_fee_question, search_local_knowledge

from memory_recall import (
    is_complaint_memory_question,
    is_first_memory_question,
    build_first_memory_reply,
    build_recent_memory_reply,
    build_latest_complaint_memory_reply,
)

from response_cleaner import clean_bank_contact_information


ERROR_REPLY = "Sorry, I could not process that request right now. Please try again later."
SCHEDULE_CHARGES_MENU_REPLY = (
    "Which banking charge do you want to know Retail, SME, Corporate "
    "or Card charges?"
)
INTEREST_RATE_TYPE_REPLY = (
    "Which interest rate do you want to know: Deposit rate or Lending rate?"
)
LENDING_RATE_PRODUCT_REPLY = (
    build_broad_lending_rate_clarification()
)
INTEREST_RATE_PAGE_URL = "https://www.ebl.com.bd/interest-rates"
SCHEDULE_CHARGE_CATEGORY_LABELS = {
    "retail": "Retail",
    "sme": "SME",
    "corporate": "Corporate",
    "cards": "Cards",
}
EBL_CONTEXT_LIMIT = 10000
LOCAL_KNOWLEDGE_CONTEXT_LIMIT = 7000
CHARGE_CONTEXT_LIMIT = 3600
CHARGE_LOCAL_SNIPPET_LIMIT = 2600
SESSION_SUMMARY_LIMIT = 800
LOAN_CATEGORY_QUESTION = "Do you want to know about SME or Retail loans?"
MAIN_QUICK_ACTIONS = [
    "Open an Account",
    "Loan Information",
    "Card Support",
    "Schedule of Charges",
    "Interest Rate",
    "Contact Us",
]
SCHEDULE_CHARGE_QUICK_ACTIONS = [
    "Retail Charges",
    "SME Charges",
    "Corporate Charges",
    "Card Charges",
]
INTEREST_RATE_QUICK_ACTIONS = [
    "Deposit Rate",
    "Lending Rate",
]
LOAN_SEGMENT_QUICK_ACTIONS = [
    "Retail Loans",
    "SME Loans",
]
ACCOUNT_SEGMENT_QUICK_ACTIONS = [
    "Retail Account",
    "SME Account",
    "Islamic Account",
]
CARD_CATEGORY_QUICK_ACTIONS = [
    "Debit Card",
    "Credit Card",
    "Prepaid Card",
    "Islamic Card",
]
DEPOSIT_RATE_QUICK_ACTIONS = [
    "Savings Account rate",
    "Retail FD rate",
    "DPS rate",
    "EBL Confidence rate",
    "EBL Kotipoti rate",
    "Retail EBL Super 360 Days rate",
]
DEPOSIT_RATE_CATEGORY_QUICK_ACTIONS = [
    "CASA Products",
    "Other CASA Products",
    "Business Unit: Retail",
    "Business Unit: Commercial",
    "Business Unit: Corporate",
    "Recurring Deposit",
]
LENDING_RATE_QUICK_ACTIONS = [
    "Home Loan rate",
    "Personal Loan rate",
    "SME Loan rate",
    "Credit Cards rate",
    "Food Items rate",
    "Cattle Feeds rate",
]
LENDING_RATE_CATEGORY_QUICK_ACTIONS = [
    "Agriculture, Fishing & Forestry",
    "Industry",
    "Construction",
    "Transport",
    "Trade & Commerce",
    "Other Institutional Loan",
    "Consumer Finance",
    "Miscellaneous",
]
CHARGE_PROMPT_QUICK_ACTIONS = {
    "retail": [
        "Retail account maintenance fee",
        "Retail cheque book fee",
        "Retail locker fees",
        "Retail home loan processing fee",
        "Retail cash withdrawal fee",
    ],
    "sme": [
        "SME account maintenance fee",
        "SME cheque book fee",
        "SME PIN change charge",
        "SME loan processing fee",
        "SME cash withdrawal fee",
    ],
    "corporate": [
        "Corporate account maintenance fee",
        "Corporate pay order charge",
        "Corporate RTGS charge",
        "Corporate SWIFT charge",
        "Corporate cash withdrawal fee",
    ],
    "cards": [
        "Card annual fee",
        "Card replacement fee",
        "PIN replacement fee",
        "Cash withdrawal fee",
        "Supplementary card fee",
    ],
}


LOAN_CATEGORY_SCHEDULES = {
    "retail": "Retail",
}


RETAIL_LOAN_PRODUCTS = [
    "Personal Loan",
    "Home Loan",
    "Auto Loan",
    "Two Wheeler Loan",
    "Secured loan (Cash Covered)",
    "EBL Edu Loan",
    "EBL Assure",
    "EBL Executive Loan",
    "EBL Women's Loan",
    "EBL Islamic Home Finance",
    "EBL Islamic Auto Finance",
]


SME_LOAN_PRODUCTS = [
    "EBL Utkorsho",
    "EBL Startup",
    "EBL Mukti",
    "EBL Uddipon",
    "EBL Fleet Financing",
    "EBL Krishi Loan",
    "EBL Asha",
    "EBL Cash Credit",
    "EBL Business Solution",
    "EBL E-Loan /E-Cash",
]


LOAN_PRODUCT_RULES = [
    {
        "name": "EBL Assure",
        "category": "retail",
        "page_name": "EBL Detail Page - Ebl Assure",
        "url": "https://www.ebl.com.bd/retail-loan/EBL-Assure",
        "aliases": ["ebl assure", "assure loan", "assure"],
    },
    {
        "name": "EBL Executive Loan",
        "category": "retail",
        "page_name": "EBL Detail Page - Ebl Executive Loan",
        "url": "https://www.ebl.com.bd/retail-loan/EBL-Executive-Loan",
        "aliases": ["ebl executive loan", "executive loan"],
    },
    {
        "name": "EBL Women's Loan",
        "category": "retail",
        "page_name": "EBL Detail Page - Ebl Womens Loan",
        "url": "https://www.ebl.com.bd/retail-loan/EBL-Womens-Loan",
        "aliases": [
            "ebl womens loan",
            "ebl women's loan",
            "women loan",
            "women's loan",
            "womens loan",
        ],
    },
    {
        "name": "EBL Home Loan",
        "category": "retail",
        "page_name": "EBL Detail Page - Ebl Home Loan",
        "url": "https://www.ebl.com.bd/retail-loan/EBL-Home-Loan",
        "aliases": ["ebl home loan", "home loan", "mortgage loan"],
    },
    {
        "name": "EBL Auto Loan",
        "category": "retail",
        "page_name": "EBL Detail Page - Ebl Auto Loan",
        "url": "https://www.ebl.com.bd/retail-loan/EBL-Auto-Loan",
        "aliases": ["ebl auto loan", "auto loan", "car loan"],
    },
    {
        "name": "EBL Two Wheeler Loan",
        "category": "retail",
        "page_name": "EBL Detail Page - Ebl Two Wheeler Loan",
        "url": "https://www.ebl.com.bd/retail-loan/ebl-two-wheeler-loan",
        "aliases": ["ebl two wheeler loan", "two wheeler loan", "bike loan", "motorcycle loan"],
    },
    {
        "name": "EBL Edu Loan",
        "category": "retail",
        "page_name": "EBL Detail Page - Ebl Edu Loan",
        "url": "https://www.ebl.com.bd/retail-loan/ebl-edu-loan",
        "aliases": ["ebl edu loan", "edu loan", "education loan", "student loan"],
    },
    {
        "name": "EBL Fast Cash",
        "category": "retail",
        "page_name": "EBL Detail Page - Ebl Fast Cash",
        "url": "https://www.ebl.com.bd/retail-loan/ebl-fast-cash",
        "aliases": ["ebl fast cash", "fast cash"],
    },
    {
        "name": "EBL Fast Loan",
        "category": "retail",
        "page_name": "EBL Detail Page - Ebl Fast Loan",
        "url": "https://www.ebl.com.bd/retail-loan/ebl-fast-loan",
        "aliases": ["ebl fast loan", "fast loan"],
    },
    {
        "name": "EBL Women Home Credit",
        "category": "retail",
        "page_name": "EBL Detail Page - Ebl Women Home Credit",
        "url": "https://www.ebl.com.bd/retail-loan/ebl-women-home-credit",
        "aliases": ["ebl women home credit", "women home credit"],
    },
    {
        "name": "EBL Islamic Home Finance",
        "category": "retail",
        "page_name": "EBL Islamic Home Finance Page",
        "url": "https://www.ebl.com.bd/islamic-retail-finance/home-finance/",
        "aliases": [
            "ebl islamic home finance",
            "islamic home finance",
            "islamic home loan",
            "shariah home finance",
        ],
    },
    {
        "name": "EBL Islamic Auto Finance",
        "category": "retail",
        "page_name": "EBL Islamic Auto Finance Page",
        "url": "https://www.ebl.com.bd/islamic-retail-finance/auto-finance/",
        "aliases": [
            "ebl islamic auto finance",
            "islamic auto finance",
            "islamic car finance",
            "islamic auto loan",
            "shariah auto finance",
        ],
    },
    {
        "name": "EBL Utkorsho",
        "category": "sme",
        "page_name": "EBL SME Loan Page",
        "url": "https://www.ebl.com.bd/sme/sme-loans",
        "aliases": ["ebl utkorsho", "utkorsho"],
    },
    {
        "name": "EBL Startup",
        "category": "sme",
        "page_name": "EBL SME Loan Page",
        "url": "https://www.ebl.com.bd/sme/sme-loans",
        "aliases": ["ebl startup", "startup loan", "startup"],
    },
    {
        "name": "EBL Mukti",
        "category": "sme",
        "page_name": "EBL SME Loan Page",
        "url": "https://www.ebl.com.bd/sme/sme-loans",
        "aliases": ["ebl mukti", "mukti"],
    },
    {
        "name": "EBL Uddipon",
        "category": "sme",
        "page_name": "EBL SME Loan Page",
        "url": "https://www.ebl.com.bd/sme/sme-loans",
        "aliases": ["ebl uddipon", "uddipon"],
    },
    {
        "name": "EBL Fleet Financing",
        "category": "sme",
        "page_name": "EBL SME Loan Page",
        "url": "https://www.ebl.com.bd/sme/sme-loans",
        "aliases": ["ebl fleet financing", "fleet financing", "fleet loan"],
    },
    {
        "name": "EBL Krishi Loan",
        "category": "sme",
        "page_name": "EBL SME Loan Page",
        "url": "https://www.ebl.com.bd/sme/sme-loans",
        "aliases": ["ebl krishi loan", "krishi loan", "krishi", "agri loan", "agriculture loan"],
    },
    {
        "name": "EBL Asha",
        "category": "sme",
        "page_name": "EBL SME Loan Page",
        "url": "https://www.ebl.com.bd/sme/sme-loans",
        "aliases": ["ebl asha", "asha loan", "asha"],
    },
    {
        "name": "EBL Cash Credit",
        "category": "sme",
        "page_name": "EBL SME Loan Page",
        "url": "https://www.ebl.com.bd/sme/sme-loans",
        "aliases": ["ebl cash credit", "cash credit", "cc loan"],
    },
    {
        "name": "EBL Business Solution",
        "category": "sme",
        "page_name": "EBL SME Loan Page",
        "url": "https://www.ebl.com.bd/sme/sme-loans",
        "aliases": ["ebl business solution", "business solution", "business solution loan"],
    },
    {
        "name": "EBL E-Loan /E-Cash",
        "category": "sme",
        "page_name": "EBL SME Loan Page",
        "url": "https://www.ebl.com.bd/sme/sme-loans",
        "aliases": [
            "ebl e loan e cash",
            "ebl e-loan e-cash",
            "e loan e cash",
            "e-loan e-cash",
            "e loan",
            "e-loan",
            "e cash",
            "e-cash",
            "ecash",
            "eloan",
        ],
    },
]


LOAN_SECTION_STOP_PREFIXES = [
    "eligibility",
    "mandatory documents",
    "common documents",
    "who are eligible",
    "apply now",
    "quick apply",
    "calulator",
    "calculator",
    "ebl  self  service portal",
    "ebl self service portal",
    "existing customer",
    "new customer",
]


LOAN_SECTION_SKIP_LINES = [
    "back",
    "features",
    "features:",
    "feature",
    "feature:",
    "key features",
    "key features:",
    "main features",
    "main features:",
    "primary features",
    "primary features:",
    "primary feature",
    "primary feature:",
    "special feature",
    "special feature:",
    "loan purpose",
    "loan purpose:",
    "purpose of financing",
    "purpose of financing:",
]


LOAN_FEATURE_START_HEADINGS = {
    "features",
    "feature",
    "key features",
    "main features",
    "primary features",
    "primary feature",
}


ACCOUNT_CATEGORY_QUESTION = (
    "Do you want to open a Retail account, an SME account or an Islamic account?"
)


ACCOUNT_CATEGORY_PRODUCTS = {
    "current": [
        "EBL Current Account",
        "EBL Current Plus",
        "EBL Expat LCY Account",
        "EBL Freelancer Suite",
        "EBL Mariner Account (USD)",
        "EBL Expat FCY Account",
        "EBL Citizen Account",
    ],
    "savings": [
        "EBL Power Savings",
        "EBL Classic Savings",
        "EBL Green Account",
        "EBL Max Saver",
        "EBL Premium Savings",
        "EBL 50+ Savings",
        "EBL Smart Women's Savings Account",
    ],
    "dps": [
        "EBL Women Confidence",
        "EBL Kotipoti Scheme",
        "EBL Multiplier",
        "EBL Millionaire Scheme",
        "EBL Confidence",
        "EBL Women Millionaire DPS",
    ],
    "fixed": [
        "EBL Repeat",
        "EBL FD",
        "EBL Earn First FD",
    ],
    "nrb_foreign": [
        "EBL Shonchoy",
        "EBL Paribar",
        "EBL NFCD",
        "EBL Global",
        "EBL RFCD Account",
        "EBL Expat LCY Account",
        "EBL Expat FCY Account",
        "EBL Mariner Account (USD)",
        "EBL Citizen Account",
        "EBL Freelancer Suite",
    ],
    "personal_retail": [
        "EBL High Earning Account",
        "EBL Personal Retail Account",
    ],
    "student_banking": [
        "EBL Junior Savings Account",
        "EBL Campus Account",
        "EBL Student File Services",
        "EBL Child Future Plan",
        "EBL Aspire Scheme",
        "EBL Little Star",
        "EBL Junior Saver's Islamic Account",
        "EBL Campus Islamic Account",
    ],
    "islamic_deposit": [
        "EBL Islamic Current Account",
        "EBL Islamic SND Account",
        "EBL Speed Islamic SND",
        "EBL High Performance Islamic Account",
        "EBL Power Islamic Savings Account",
        "EBL Executive Islamic Savings Account (Payroll Account)",
        "EBL Women's Islamic Savings Account",
        "EBL Campus Islamic Account",
        "EBL Junior Saver's Islamic Account",
        "EBL Islamic Term Deposit Account",
        "EBL Islamic Monthly Profit Scheme",
        "EBL Islamic DPS Account(s)",
    ],
    "sme_deposit": [
        "EBL Current Account",
        "EBL Foreign Currency Account",
        "EBL ERQ Account",
        "EBL Fixed Deposits",
        "EBL Fixed Deposit - Repeat",
        "EBL Equity Builder Account",
        "EBL Short Notice Deposit",
        "EBL Subidha",
    ],
}


ACCOUNT_CATEGORY_LABELS = {
    "current": "Current Deposit",
    "savings": "Savings Deposit",
    "dps": "DPS",
    "fixed": "Fixed Deposit",
    "nrb_foreign": "NRB/Foreign Currency",
    "personal_retail": "Personal Retail",
    "student_banking": "Student Banking",
    "islamic_deposit": "Islamic Deposit",
    "sme_deposit": "SME Deposit",
}


RETAIL_ACCOUNT_PRODUCTS = list(dict.fromkeys(
    ACCOUNT_CATEGORY_PRODUCTS["current"]
    + ACCOUNT_CATEGORY_PRODUCTS["savings"]
    + ACCOUNT_CATEGORY_PRODUCTS["dps"]
    + ACCOUNT_CATEGORY_PRODUCTS["fixed"]
    + ACCOUNT_CATEGORY_PRODUCTS["nrb_foreign"]
    + ACCOUNT_CATEGORY_PRODUCTS["personal_retail"]
    + ACCOUNT_CATEGORY_PRODUCTS["student_banking"]
    + ACCOUNT_CATEGORY_PRODUCTS["islamic_deposit"]
))


ACCOUNT_SEGMENT_PRODUCTS = {
    "retail": RETAIL_ACCOUNT_PRODUCTS,
    "sme": ACCOUNT_CATEGORY_PRODUCTS["sme_deposit"],
}


ACCOUNT_SEGMENT_LABELS = {
    "retail": "Retail Account",
    "sme": "SME Account",
}


ACCOUNT_SEGMENT_SCHEDULES = {
    "retail": "Retail",
    "sme": "SME",
}


RETAIL_BANKING_LINKS = [
    ("Retail Loan", "https://www.ebl.com.bd/retail/retail-loan"),
    ("Retail Deposit", "https://www.ebl.com.bd/retail/retail-deposit"),
    ("EBL Cards", "https://www.ebl.com.bd/retail/EBL-Cards"),
    ("EBL Skybanking", "https://www.ebl.com.bd/retail-digital/ebl-skybanking"),
    (
        "EBL Missed Call Alert Service",
        "https://www.ebl.com.bd/retail-digital/ebl-missed-call-alert-service",
    ),
    ("EBL 365 PLUS", "https://www.ebl.com.bd/retail-digital/ebl-365-plus"),
    ("EBL SKYPAY", "https://www.ebl.com.bd/retail-ecommerce/ebl-skypay"),
    ("EBL Insta Account-Branch", "https://www.ebl.com.bd/retail/ebl-insta-account"),
    ("EBL Insta Banking-Online", "https://www.ebl.com.bd/retail/ebl-insta-banking"),
    ("EBL Priority Banking", "https://www.ebl.com.bd/priority/"),
    ("EBL Power Banking", "https://www.ebl.com.bd/powerbanking"),
    ("EBL Super Saver", "https://www.ebl.com.bd/ebl-super-saver"),
    ("EBL Women Banking", "https://www.ebl.com.bd/retail/Women-Banking"),
    ("EBL Agent Banking", "https://www.ebl.com.bd/agentbanking"),
    ("EBL Payroll Banking", "https://www.ebl.com.bd/retail/EBL-Payroll-Banking"),
    ("EBL Student Banking", "https://www.ebl.com.bd/retail/EBL-Student-Banking"),
    ("EBL Bancassurance", "https://www.ebl.com.bd/retail/ebl-bancassurance"),
    ("EBL Retail Alliance", "https://www.ebl.com.bd/retail/ebl-retail-propositions"),
]


ISLAMIC_BANKING_LINKS = [
    ("EBL Islamic Banking", "https://www.ebl.com.bd/islamicbanking"),
    ("Shariah Committee", "https://www.ebl.com.bd/islamic/member_ssc"),
    ("Islamic Retail", "https://www.ebl.com.bd/islamic/islamic-retail-finance"),
    ("Islamic SME", "https://www.ebl.com.bd/islamic/islamic-sme-finance"),
    ("Islamic Corporate", "https://www.ebl.com.bd/islamic/islamic-corporate-finance"),
    ("Islamic Cards", "https://www.ebl.com.bd/islamic/islamic-cards"),
    ("Profit Distribution", "https://www.ebl.com.bd/islamic/profit-distribution"),
    ("Islamic Notice", "https://www.ebl.com.bd/islamic/notice"),
    (
        "EBL Islamic Visa Platinum Debit Card",
        "https://www.ebl.com.bd/islamic/eblcard/ebl-islamic-visa-platinum-debit-card",
    ),
    (
        "EBL Islamic Visa Prepaid Card",
        "https://www.ebl.com.bd/islamic/eblcard/ebl-islamic-visa-prepaid-card",
    ),
    (
        "EBL Islamic Priority Visa Signature Debit Card",
        "https://www.ebl.com.bd/islamic/eblcard/ebl-islamic-priority-visa-signature-debit-card",
    ),
    (
        "EBL Islamic Women's Platinum Debit Card",
        "https://www.ebl.com.bd/islamic/eblcard/islamic-women-platinum-debit-card",
    ),
]


CARD_CATEGORY_QUESTION = (
    "Which EBL card type do you want to know about: Debit, Credit, Prepaid or Islamic card?"
)

CARD_APPLY_NOW_LINK = "https://www.ebl.com.bd/onlineapply"


CARD_CATEGORY_LABELS = {
    "debit": "Debit Card",
    "credit": "Credit Card",
    "prepaid": "Prepaid Card",
    "islamic": "Islamic Card",
}


CARD_CATEGORY_PRODUCTS = {
    "debit": [
        "EBL Classic Debit Card",
        "EBL Global Debit Card",
        "EBL Mastercard Platinum Debit Card",
        "EBL Mastercard World Debit Card",
        "EBL Signature Debit Card",
        "EBL Stellar Platinum Debit Card",
        "EBL UnionPay Classic Debit Card",
        "EBL Visa Business Debit Card",
        "Visa Infinite Debit Card",
        "EBL Visa Platinum Debit Card",
        "EBL Visa Signature Priority Debit Card",
        "EBL Visa Women's Platinum Debit Card",
    ],
    "credit": [
        "Diners Club Credit Card",
        "Diners Club Vroom Co Brand Credit Card",
        "EBL Banglalink Mastercard Co Brand Titanium Credit Card",
        "EBL Banglalink Mastercard Co Brand World Credit Card",
        "EBL Basis Co Branded Credit Mastercard",
        "EBL Daraz Visa Co Brand Credit Card",
        "EBL Lavender Visa Co Brand Credit",
        "EBL Pickaboo Mastercard Co Brand Titanium Credit Card",
        "EBL Pickaboo Mastercard Co Brand World Credit Card",
        "EBL ShareTrip Mastercard Co Brand Credit Card",
        "EBL Shwapno Co Branded Titanium Credit Mastercard",
        "EBL Stellar Platinum Credit Card",
        "EBL Stellar Signature Credit Card",
        "EBL Visa Air Force Platinum Credit Card",
        "EBL Visa Army Platinum Credit Card",
        "EBL Visa Classic Credit Card",
        "EBL Visa Gold Credit Card",
        "EBL Visa Navy Platinum Credit Card",
        "EBL Visa Platinum Credit Card",
        "EBL Visa Women Platinum Credit Card",
        "EBL Wander Woman Co Brand Credit Mastercard",
        "EBL World Credit Mastercard",
        "Mastercard Titanium Credit Card",
        "Meena Bazar Co Branded Visa Credit Card",
        "UnionPay Contactless Platinum Credit Card",
        "Visa Corporate Platinum Credit Card",
        "Visa Infinite Credit Card",
        "Visa Signature Acci Shield Credit Card",
        "Visa Signature Lite Credit Card",
        "Visa Women Signature Credit Card",
    ],
    "prepaid": [
        "EBL Virtual Prepaid Card",
        "EBL Banglalink Mastercard Co Brand Prepaid Card",
        "EBL Daraz Visa Co Brand Prepaid Card",
        "EBL Diners Club International Global Prepaid Card",
        "EBL Grameenphone Shopno Jabe Bari Visa Co Brand Prepaid Card",
        "EBL Mastercard Aqua Platinum Vertical Prepaid Card",
        "EBL Mastercard Aqua Women Prepaid Card",
        "EBL Mastercard Basis Co Branded Prepaid Card",
        "EBL Mastercard Medical Prepaid Card",
        "EBL Oil & Gas Card",
        "EBL Payroll Card",
        "EBL UnionPay Dragon Prepaid Card",
        "EBL Visa Lifestyle Prepaid Card",
        "EBL Wander Woman Co Brand Prepaid",
    ],
    "islamic": [
        "EBL Islamic Visa Platinum Debit Card",
        "EBL Islamic Visa Prepaid Card",
        "EBL Islamic Priority Visa Signature Debit Card",
        "EBL Islamic Women's Platinum Debit Card",
    ],
}


CARD_PRODUCT_URLS = {
    "Diners Club Credit Card": "https://www.ebl.com.bd/retail/eblcard/Diners-Club-Credit-Card",
    "Diners Club Vroom Co Brand Credit Card": "https://www.ebl.com.bd/retail/eblcard/Diners-Club-Vroom-Co-Brand-Credit-Card",
    "EBL Banglalink Mastercard Co Brand Prepaid Card": "https://www.ebl.com.bd/retail/eblcard/ebl-banglalink-mastercard-co-brand-prepaid-card",
    "EBL Banglalink Mastercard Co Brand Titanium Credit Card": "https://www.ebl.com.bd/retail/eblcard/ebl-banglalink-mastercard-co-brand-titanium-credit-card",
    "EBL Banglalink Mastercard Co Brand World Credit Card": "https://www.ebl.com.bd/retail/eblcard/ebl-banglalink-mastercard-co-brand-world-credit-card",
    "EBL Basis Co Branded Credit Mastercard": "https://www.ebl.com.bd/retail/eblcard/EBL-Basis-Co-Branded-Credit-Mastercard",
    "EBL Classic Debit Card": "https://www.ebl.com.bd/retail/eblcard/EBL-Classic-Debit-Card",
    "EBL Daraz Visa Co Brand Credit Card": "https://www.ebl.com.bd/retail/eblcard/ebl-daraz-visa-co-brand-credit-card",
    "EBL Daraz Visa Co Brand Prepaid Card": "https://www.ebl.com.bd/retail/eblcard/ebl-daraz-visa-co-brand-prepaid-card",
    "EBL Diners Club International Global Prepaid Card": "https://www.ebl.com.bd/retail/eblcard/EBL-Diners-Club-International-Global-Prepaid-Card",
    "EBL Global Debit Card": "https://www.ebl.com.bd/retail/eblcard/EBL-Global-Debit-Card",
    "EBL Grameenphone Shopno Jabe Bari Visa Co Brand Prepaid Card": "https://www.ebl.com.bd/retail/eblcard/ebl-grameenphone-shopno-jabe-bari-visa-co-brand-prepaid-card",
    "EBL Islamic Priority Visa Signature Debit Card": "https://www.ebl.com.bd/islamic/eblcard/ebl-islamic-priority-visa-signature-debit-card",
    "EBL Islamic Visa Platinum Debit Card": "https://www.ebl.com.bd/islamic/eblcard/ebl-islamic-visa-platinum-debit-card",
    "EBL Islamic Visa Prepaid Card": "https://www.ebl.com.bd/islamic/eblcard/ebl-islamic-visa-prepaid-card",
    "EBL Islamic Women's Platinum Debit Card": "https://www.ebl.com.bd/islamic/eblcard/islamic-women-platinum-debit-card",
    "EBL Lavender Visa Co Brand Credit": "https://www.ebl.com.bd/retail/eblcard/ebl-lavender-visa-co-brand-credit",
    "EBL Mastercard Aqua Platinum Vertical Prepaid Card": "https://www.ebl.com.bd/retail/eblcard/ebl-mastercard-aqua-platinum-vertical-prepaid-card",
    "EBL Mastercard Aqua Women Prepaid Card": "https://www.ebl.com.bd/retail/eblcard/ebl-mastercard-aqua-women-prepaid-card",
    "EBL Mastercard Basis Co Branded Prepaid Card": "https://www.ebl.com.bd/retail/eblcard/ebl-mastercard-basis-co-branded-prepaid-card",
    "EBL Mastercard Medical Prepaid Card": "https://www.ebl.com.bd/retail/eblcard/ebl-mastercard-medical-prepaid-card",
    "EBL Mastercard Platinum Debit Card": "https://www.ebl.com.bd/retail/eblcard/ebl-mastercard-platinum-debit-card",
    "EBL Mastercard World Debit Card": "https://www.ebl.com.bd/retail/eblcard/ebl-mastercard-world-debit-card",
    "EBL Oil & Gas Card": "https://www.ebl.com.bd/retail/eblcard/EBL-Oil---Gas-Card",
    "EBL Payroll Card": "https://www.ebl.com.bd/retail/eblcard/EBL-Payroll-Card",
    "EBL Pickaboo Mastercard Co Brand Titanium Credit Card": "https://www.ebl.com.bd/retail/eblcard/ebl-pickaboo-mastercard-co-brand-titanium-credit-card",
    "EBL Pickaboo Mastercard Co Brand World Credit Card": "https://www.ebl.com.bd/retail/eblcard/ebl-pickaboo-mastercard-co-brand-world-credit-card",
    "EBL ShareTrip Mastercard Co Brand Credit Card": "https://www.ebl.com.bd/retail/eblcard/ebl-sharetrip-mastercard-co-brand-credit-card",
    "EBL Shwapno Co Branded Titanium Credit Mastercard": "https://www.ebl.com.bd/retail/eblcard/EBL-Shwapno-Co-Branded-Titanium-Credit-Mastercard",
    "EBL Signature Debit Card": "https://www.ebl.com.bd/retail/eblcard/EBL-Signature-Debit-Card",
    "EBL Stellar Platinum Credit Card": "https://www.ebl.com.bd/retail/eblcard/ebl-stellar-platinum-credit-card",
    "EBL Stellar Platinum Debit Card": "https://www.ebl.com.bd/retail/eblcard/ebl-stellar-platinum-debit-card",
    "EBL Stellar Signature Credit Card": "https://www.ebl.com.bd/retail/eblcard/ebl-stellar-signature-credit-card",
    "EBL UnionPay Classic Debit Card": "https://www.ebl.com.bd/retail/eblcard/ebl-unionpay-classic-debit-card",
    "EBL UnionPay Dragon Prepaid Card": "https://www.ebl.com.bd/retail/eblcard/ebl-unionpay-dragon-prepaid-card",
    "EBL Visa Air Force Platinum Credit Card": "https://www.ebl.com.bd/retail/eblcard/EBL-VISA-Air-Force-Platinum-Credit-Card",
    "EBL Visa Army Platinum Credit Card": "https://www.ebl.com.bd/retail/eblcard/EBL-VISA-Army-Platinum-Credit-Card",
    "EBL Visa Business Debit Card": "https://www.ebl.com.bd/retail/eblcard/EBL-Visa-Business-Debit-Card",
    "EBL Visa Classic Credit Card": "https://www.ebl.com.bd/retail/eblcard/EBL-Visa-Classic-Credit-Card",
    "EBL Visa Gold Credit Card": "https://www.ebl.com.bd/retail/eblcard/EBL-VISA-Gold-Credit-Card",
    "EBL Visa Lifestyle Prepaid Card": "https://www.ebl.com.bd/retail/eblcard/EBL-Visa-Lifestyle-Prepaid-Card",
    "EBL Visa Navy Platinum Credit Card": "https://www.ebl.com.bd/retail/eblcard/EBL-VISA-Navy-Platinum-Credit-Card",
    "EBL Visa Platinum Credit Card": "https://www.ebl.com.bd/retail/eblcard/EBL-VISA-Platinum-Credit-Card",
    "EBL Visa Platinum Debit Card": "https://www.ebl.com.bd/retail/eblcard/EBL-Visa-Platinum-Debit-Card",
    "EBL Visa Signature Priority Debit Card": "https://www.ebl.com.bd/retail/eblcard/EBL-Visa-Signature-Priority-Debit-Card",
    "EBL Visa Women Platinum Credit Card": "https://www.ebl.com.bd/retail/eblcard/EBL-visa-women-platinum-credit-card",
    "EBL Visa Women's Platinum Debit Card": "https://www.ebl.com.bd/retail/eblcard/EBL-Visa-Womens-Platinum-Debit-Card",
    "EBL Virtual Prepaid Card": "https://ebl.com.bd/ebl-virtual-prepaid-card",
    "EBL Wander Woman Co Brand Credit Mastercard": "https://www.ebl.com.bd/retail/eblcard/ebl-wander-woman-co-brand-credit-mastercard",
    "EBL Wander Woman Co Brand Prepaid": "https://www.ebl.com.bd/retail/eblcard/ebl-wander-woman-co-brand-prepaid",
    "EBL World Credit Mastercard": "https://www.ebl.com.bd/retail/eblcard/EBL-World-Credit-Mastercard",
    "Mastercard Titanium Credit Card": "https://www.ebl.com.bd/retail/eblcard/Mastercard-Titanium-Credit-Card",
    "Meena Bazar Co Branded Visa Credit Card": "https://www.ebl.com.bd/retail/eblcard/Meena-Bazar-Co-Branded-VISA-Credit-Card",
    "UnionPay Contactless Platinum Credit Card": "https://www.ebl.com.bd/retail/eblcard/unionpay-contactless-platinum-credit-card",
    "Visa Corporate Platinum Credit Card": "https://www.ebl.com.bd/retail/eblcard/Visa-Corporate-Platinum-Credit-Card",
    "Visa Infinite Credit Card": "https://www.ebl.com.bd/retail/eblcard/visa-infinite-credit-card",
    "Visa Infinite Debit Card": "https://www.ebl.com.bd/retail/eblcard/Visa-Infinite-Debit-Card",
    "Visa Signature Acci Shield Credit Card": "https://www.ebl.com.bd/retail/eblcard/VISA-Signature-Acci-shield-Credit-Card",
    "Visa Signature Lite Credit Card": "https://www.ebl.com.bd/retail/eblcard/Visa-Signature-Lite-Credit-Card",
    "Visa Women Signature Credit Card": "https://www.ebl.com.bd/retail/eblcard/visa-women-signature-credit-card",
}


CARD_PRODUCT_RULES = []

for card_category, card_products in CARD_CATEGORY_PRODUCTS.items():
    for card_product in card_products:
        CARD_PRODUCT_RULES.append({
            "name": card_product,
            "category": card_category,
            "url": CARD_PRODUCT_URLS[card_product],
        })


ACCOUNT_PRODUCT_RULES = [
    {
        "name": "EBL Current Account",
        "category": "sme_deposit",
        "page_name": "EBL SME Deposits Page",
        "url": "https://www.ebl.com.bd/sme/sme-deposits",
        "aliases": ["sme current account", "sme current deposit", "business current account"],
    },
    {
        "name": "EBL Current Account",
        "category": "current",
        "page_name": "EBL Current Account Page",
        "url": "https://www.ebl.com.bd/retail-deposit/EBL-Current-Account",
        "aliases": ["ebl current account", "current account"],
    },
    {
        "name": "EBL Current Plus",
        "category": "current",
        "page_name": "EBL Detail Page - Ebl Current Plus",
        "url": "https://www.ebl.com.bd/retail-deposit/EBL-Current-Plus",
        "aliases": ["ebl current plus", "current plus"],
    },
    {
        "name": "EBL Power Savings",
        "category": "savings",
        "page_name": "EBL Power Savings Page",
        "url": "https://www.ebl.com.bd/retail-deposit/EBL-Power-Savings",
        "aliases": ["ebl power savings", "power savings"],
    },
    {
        "name": "EBL Classic Savings",
        "category": "savings",
        "page_name": "EBL Detail Page - Ebl Classic Savings",
        "url": "https://www.ebl.com.bd/retail-deposit/EBL-Classic-Savings",
        "aliases": ["ebl classic savings", "classic savings"],
    },
    {
        "name": "EBL Green Account",
        "category": "savings",
        "page_name": "EBL Detail Page - Ebl Green Account",
        "url": "https://www.ebl.com.bd/retail-deposit/ebl-green-account",
        "aliases": ["ebl green account", "green account"],
    },
    {
        "name": "EBL Max Saver",
        "category": "savings",
        "page_name": "EBL Max Saver Page",
        "url": "https://www.ebl.com.bd/retail-deposit/EBL-Max-Saver",
        "aliases": ["ebl max saver", "max saver"],
    },
    {
        "name": "EBL Premium Savings",
        "category": "savings",
        "page_name": "EBL Premium Savings Page",
        "url": "https://www.ebl.com.bd/retail-deposit/EBL-Premium-Savings",
        "aliases": ["ebl premium savings", "premium savings"],
    },
    {
        "name": "EBL 50+ Savings",
        "category": "savings",
        "page_name": "EBL 50+ Savings Page",
        "url": "https://www.ebl.com.bd/retail-deposit/EBL-50Plus-Savings",
        "aliases": ["ebl 50+ savings", "50+ savings", "50 plus savings", "senior savings"],
    },
    {
        "name": "EBL Smart Women's Savings Account",
        "category": "savings",
        "page_name": "EBL Detail Page - Ebl Smart Womens Savings Account",
        "url": "https://www.ebl.com.bd/retail-deposit/EBL-Smart-Womens-Savings-Account",
        "aliases": [
            "ebl smart womens savings account",
            "smart womens savings",
            "women savings account",
            "women's savings account",
            "womens savings account",
        ],
    },
    {
        "name": "EBL Women Confidence",
        "category": "dps",
        "page_name": "EBL Detail Page - Ebl Women Confidence",
        "url": "https://www.ebl.com.bd/retail-deposit/ebl-women-confidence",
        "aliases": ["ebl women confidence", "women confidence"],
    },
    {
        "name": "EBL Kotipoti Scheme",
        "category": "dps",
        "page_name": "EBL Detail Page - Ebl Kotipoti Scheme",
        "url": "https://www.ebl.com.bd/retail-deposit/EBL-Kotipoti-Scheme",
        "aliases": ["ebl kotipoti scheme", "kotipoti scheme", "kotipoti"],
    },
    {
        "name": "EBL Multiplier",
        "category": "dps",
        "page_name": "EBL Detail Page - Ebl Multiplier",
        "url": "https://www.ebl.com.bd/retail-deposit/EBL-Multiplier",
        "aliases": ["ebl multiplier", "multiplier scheme"],
    },
    {
        "name": "EBL Millionaire Scheme",
        "category": "dps",
        "page_name": "EBL Detail Page - Ebl Millionaire Scheme",
        "url": "https://www.ebl.com.bd/retail-deposit/EBL-Millionaire-Scheme",
        "aliases": ["ebl millionaire scheme", "millionaire scheme"],
    },
    {
        "name": "EBL Confidence",
        "category": "dps",
        "page_name": "EBL Detail Page - Ebl Confidence",
        "url": "https://www.ebl.com.bd/retail-deposit/EBL-Confidence",
        "aliases": ["ebl confidence", "confidence dps"],
    },
    {
        "name": "EBL Women Millionaire DPS",
        "category": "dps",
        "page_name": "EBL Detail Page - Ebl Women Millionaire DPS",
        "url": "https://www.ebl.com.bd/retail-deposit/EBL-Women-Millionaire-DPS",
        "aliases": ["ebl women millionaire dps", "women millionaire dps"],
    },
    {
        "name": "EBL Repeat",
        "category": "fixed",
        "page_name": "EBL Detail Page - Ebl Repeat",
        "url": "https://www.ebl.com.bd/retail-deposit/EBL-Repeat",
        "aliases": ["ebl repeat", "repeat fd", "repeat fixed deposit"],
    },
    {
        "name": "EBL FD",
        "category": "fixed",
        "page_name": "EBL Detail Page - Ebl Fd",
        "url": "https://www.ebl.com.bd/retail-deposit/EBL-FD",
        "aliases": ["ebl fd", "ebl fixed deposit"],
    },
    {
        "name": "EBL Earn First FD",
        "category": "fixed",
        "page_name": "EBL Detail Page - Ebl Earn First Fd",
        "url": "https://www.ebl.com.bd/retail-deposit/EBL-Earn-First-FD",
        "aliases": ["ebl earn first fd", "earn first fd", "earn first fixed deposit"],
    },
    {
        "name": "EBL Shonchoy",
        "category": "nrb_foreign",
        "page_name": "EBL Detail Page - Ebl Shonchoy",
        "url": "https://www.ebl.com.bd/retail-deposit/EBL-Shonchoy",
        "aliases": ["ebl shonchoy", "shonchoy"],
    },
    {
        "name": "EBL Paribar",
        "category": "nrb_foreign",
        "page_name": "EBL Detail Page - Ebl Paribar",
        "url": "https://www.ebl.com.bd/retail-deposit/EBL-Paribar",
        "aliases": ["ebl paribar", "paribar"],
    },
    {
        "name": "EBL NFCD",
        "category": "nrb_foreign",
        "page_name": "EBL Detail Page - Ebl Nfcd",
        "url": "https://www.ebl.com.bd/retail-deposit/EBL-NFCD",
        "aliases": ["ebl nfcd", "nfcd"],
    },
    {
        "name": "EBL Global",
        "category": "nrb_foreign",
        "page_name": "EBL Detail Page - Ebl Global",
        "url": "https://www.ebl.com.bd/retail-deposit/ebl-global",
        "aliases": ["ebl global"],
    },
    {
        "name": "EBL RFCD Account",
        "category": "nrb_foreign",
        "page_name": "EBL Detail Page - Ebl Rfcd Account",
        "url": "https://www.ebl.com.bd/retail-deposit/EBL-RFCD-Account",
        "aliases": ["ebl rfcd account", "rfcd account", "rfcd"],
    },
    {
        "name": "EBL Expat LCY Account",
        "category": "nrb_foreign",
        "page_name": "EBL Detail Page - Ebl Expat Lcy",
        "url": "https://www.ebl.com.bd/retail-deposit/ebl-expat-lcy",
        "aliases": ["ebl expat lcy account", "expat lcy account", "expat lcy"],
    },
    {
        "name": "EBL Expat FCY Account",
        "category": "nrb_foreign",
        "page_name": "EBL Detail Page - Ebl Expat Fcy",
        "url": "https://www.ebl.com.bd/retail-deposit/ebl-expat-fcy",
        "aliases": ["ebl expat fcy account", "expat fcy account", "expat fcy"],
    },
    {
        "name": "EBL Freelancer Suite",
        "category": "nrb_foreign",
        "page_name": "EBL Detail Page - Ebl Freelancer",
        "url": "https://www.ebl.com.bd/retail-deposit/ebl-freelancer",
        "aliases": ["ebl freelancer suite", "freelancer suite", "freelancer account"],
    },
    {
        "name": "EBL Mariner Account (USD)",
        "category": "nrb_foreign",
        "page_name": "EBL Detail Page - Ebl Mariner Account Usd",
        "url": "https://www.ebl.com.bd/retail-deposit/ebl-mariner-account-usd",
        "aliases": ["ebl mariner account usd", "mariner account", "mariner usd"],
    },
    {
        "name": "EBL Citizen Account",
        "category": "nrb_foreign",
        "page_name": "EBL Detail Page - Ebl Citizen",
        "url": "https://www.ebl.com.bd/retail-deposit/ebl-citizen",
        "aliases": ["ebl citizen account", "citizen account"],
    },
    {
        "name": "EBL High Earning Account",
        "category": "personal_retail",
        "page_name": "EBL Detail Page - EBL High Earning",
        "url": "https://www.ebl.com.bd/retail-deposit/ebl-high-earning-account",
        "aliases": ["ebl high earning account", "high earning account"],
    },
    {
        "name": "EBL Personal Retail Account",
        "category": "personal_retail",
        "page_name": "EBL Detail Page - Ebl Personal Retail Account",
        "url": "https://www.ebl.com.bd/retail-deposit/ebl-personal-retail-account",
        "aliases": ["ebl personal retail account", "personal retail account"],
    },
    {
        "name": "EBL Junior Savings Account",
        "category": "student_banking",
        "page_name": "EBL Junior Savings Account Page",
        "url": "https://www.ebl.com.bd/student-banking/EBL-Junior",
        "aliases": [
            "ebl junior savings account",
            "junior savings account",
            "junior savings",
            "junior account",
        ],
    },
    {
        "name": "EBL Campus Account",
        "category": "student_banking",
        "page_name": "EBL Campus Account Page",
        "url": "https://www.ebl.com.bd/student-banking/EBL-Campus-Account",
        "aliases": [
            "ebl campus account",
            "campus account",
            "student campus account",
        ],
    },
    {
        "name": "EBL Student File Services",
        "category": "student_banking",
        "page_name": "EBL Student File Services Page",
        "url": "https://www.ebl.com.bd/student-banking/EBL-Student-File-Services",
        "aliases": [
            "ebl student file services",
            "student file services",
            "student file service",
            "student file",
        ],
    },
    {
        "name": "EBL Child Future Plan",
        "category": "student_banking",
        "page_name": "EBL Child Future Plan Page",
        "url": "https://www.ebl.com.bd/student-banking/EBL-Child-Future-Plan",
        "aliases": ["ebl child future plan", "child future plan"],
    },
    {
        "name": "EBL Aspire Scheme",
        "category": "student_banking",
        "page_name": "EBL Aspire Scheme Page",
        "url": "https://www.ebl.com.bd/student-banking/EBL-Aspire-Scheme",
        "aliases": ["ebl aspire scheme", "aspire scheme", "aspire"],
    },
    {
        "name": "EBL Little Star",
        "category": "student_banking",
        "page_name": "EBL Little Star Page",
        "url": "https://www.ebl.com.bd/student-banking/ebl-little-star",
        "aliases": ["ebl little star", "little star"],
    },
    {
        "name": "EBL Islamic Current Account",
        "category": "islamic_deposit",
        "page_name": "EBL Islamic Current Account Page",
        "url": "https://www.ebl.com.bd/islamic/deposit/ebl-islamic-current-account",
        "aliases": ["ebl islamic current account", "islamic current account"],
    },
    {
        "name": "EBL Islamic SND Account",
        "category": "islamic_deposit",
        "page_name": "EBL Islamic SND Account Page",
        "url": "https://www.ebl.com.bd/islamic/deposit/ebl-islamic-snd-account",
        "aliases": ["ebl islamic snd account", "islamic snd account", "islamic special notice deposit"],
    },
    {
        "name": "EBL Speed Islamic SND",
        "category": "islamic_deposit",
        "page_name": "EBL Speed Islamic SND Page",
        "url": "https://www.ebl.com.bd/islamic/deposit/ebl-speed-islamic-snd",
        "aliases": ["ebl speed islamic snd", "speed islamic snd"],
    },
    {
        "name": "EBL High Performance Islamic Account",
        "category": "islamic_deposit",
        "page_name": "EBL High Performance Islamic Account Page",
        "url": "https://www.ebl.com.bd/islamic/deposit/ebl-high-performance-islamic-account",
        "aliases": ["ebl high performance islamic account", "high performance islamic account"],
    },
    {
        "name": "EBL Power Islamic Savings Account",
        "category": "islamic_deposit",
        "page_name": "EBL Power Islamic Savings Account Page",
        "url": "https://www.ebl.com.bd/islamic/deposit/ebl-power-islamic-savings-account",
        "aliases": ["ebl power islamic savings account", "power islamic savings", "islamic savings account"],
    },
    {
        "name": "EBL Executive Islamic Savings Account (Payroll Account)",
        "category": "islamic_deposit",
        "page_name": "EBL Executive Islamic Savings Account Page",
        "url": "https://www.ebl.com.bd/islamic/deposit/ebl-executive-islamic-savings-account-payroll-account",
        "aliases": [
            "ebl executive islamic savings account",
            "executive islamic savings",
            "islamic payroll account",
        ],
    },
    {
        "name": "EBL Women's Islamic Savings Account",
        "category": "islamic_deposit",
        "page_name": "EBL Women's Islamic Savings Account Page",
        "url": "https://www.ebl.com.bd/islamic/deposit/ebl-womens-islamic-savings-account",
        "aliases": [
            "ebl women's islamic savings account",
            "ebl womens islamic savings account",
            "women's islamic savings",
            "womens islamic savings",
        ],
    },
    {
        "name": "EBL Campus Islamic Account",
        "category": "islamic_deposit",
        "page_name": "EBL Campus Islamic Account Page",
        "url": "https://www.ebl.com.bd/islamic/deposit/ebl-campus-islamic-account",
        "aliases": ["ebl campus islamic account", "campus islamic account", "islamic student account"],
    },
    {
        "name": "EBL Junior Saver's Islamic Account",
        "category": "islamic_deposit",
        "page_name": "EBL Junior Saver's Islamic Account Page",
        "url": "https://www.ebl.com.bd/islamic/deposit/ebl-junior-savers-islamic-account",
        "aliases": [
            "ebl junior saver's islamic account",
            "ebl junior savers islamic account",
            "junior savers islamic account",
            "junior saver islamic account",
        ],
    },
    {
        "name": "EBL Islamic Term Deposit Account",
        "category": "islamic_deposit",
        "page_name": "EBL Islamic Term Deposit Account Page",
        "url": "https://www.ebl.com.bd/islamic/deposit/ebl-islamic-term-deposit-account",
        "aliases": ["ebl islamic term deposit account", "islamic term deposit", "islamic fixed deposit"],
    },
    {
        "name": "EBL Islamic Monthly Profit Scheme",
        "category": "islamic_deposit",
        "page_name": "EBL Islamic Monthly Profit Scheme Page",
        "url": "https://www.ebl.com.bd/islamic/deposit/ebl-islamic-monthly-profit-scheme",
        "aliases": ["ebl islamic monthly profit scheme", "islamic monthly profit scheme"],
    },
    {
        "name": "EBL Islamic DPS Account(s)",
        "category": "islamic_deposit",
        "page_name": "EBL Islamic DPS Account Page",
        "url": "https://www.ebl.com.bd/islamic/deposit/ebl-islamic-dps-accounts",
        "aliases": ["ebl islamic dps account", "ebl islamic dps accounts", "islamic dps"],
    },
    {
        "name": "EBL Foreign Currency Account",
        "category": "sme_deposit",
        "page_name": "EBL SME Deposits Page",
        "url": "https://www.ebl.com.bd/sme/sme-deposits",
        "aliases": ["ebl foreign currency account", "foreign currency account"],
    },
    {
        "name": "EBL ERQ Account",
        "category": "sme_deposit",
        "page_name": "EBL SME Deposits Page",
        "url": "https://www.ebl.com.bd/sme/sme-deposits",
        "aliases": ["ebl erq account", "erq account", "erq"],
    },
    {
        "name": "EBL Fixed Deposits",
        "category": "sme_deposit",
        "page_name": "EBL SME Deposits Page",
        "url": "https://www.ebl.com.bd/sme/sme-deposits",
        "aliases": ["ebl fixed deposits", "sme fixed deposits"],
    },
    {
        "name": "EBL Fixed Deposit - Repeat",
        "category": "sme_deposit",
        "page_name": "EBL SME Deposits Page",
        "url": "https://www.ebl.com.bd/sme/sme-deposits",
        "aliases": ["ebl fixed deposit repeat", "sme repeat fixed deposit"],
    },
    {
        "name": "EBL Equity Builder Account",
        "category": "sme_deposit",
        "page_name": "EBL SME Deposits Page",
        "url": "https://www.ebl.com.bd/sme/sme-deposits",
        "aliases": ["ebl equity builder account", "equity builder account", "equity builder"],
    },
    {
        "name": "EBL Short Notice Deposit",
        "category": "sme_deposit",
        "page_name": "EBL SME Deposits Page",
        "url": "https://www.ebl.com.bd/sme/sme-deposits",
        "aliases": ["ebl short notice deposit", "short notice deposit", "snd account"],
    },
    {
        "name": "EBL Subidha",
        "category": "sme_deposit",
        "page_name": "EBL SME Deposits Page",
        "url": "https://www.ebl.com.bd/sme/sme-deposits",
        "aliases": ["ebl subidha", "subidha"],
    },
]


ACCOUNT_SECTION_STOP_PREFIXES = [
    "eligibility",
    "eligibility criteria",
    "identification document",
    "the below maturity value table",
    "product name",
    "maturity amount",
    "required documents",
    "documents required",
    "account opening documents",
    "mandatory documents",
    "relevant charges",
    "calculator",
    "fees",
    "apply now",
    "quick apply",
    "click here",
    "ebl  self  service portal",
    "ebl self service portal",
    "existing customer",
    "new customer",
    "read more",
]


ACCOUNT_SECTION_SKIP_LINES = [
    "back",
    "features",
    "features:",
    "key features",
    "key features:",
    "key features include",
    "key features include:",
    "best for you if you:",
    "best for you if you are looking for a",
    "best for you if you are looking for a:",
    "best for you if you have",
    "best for you if you have:",
    "here",
]

def limit_text(text, max_characters):
    if not text:
        return ""

    if len(text) <= max_characters:
        return text

    return text[:max_characters]


def combine_context_sections(*sections):
    return "\n\n".join(
        section.strip()
        for section in sections
        if section and section.strip()
    )


def is_document_question(message):
    message = message.lower()

    account_words = [
        "account",
        "savings",
        "saving",
        "current",
        "open",
        "opening",
    ]

    return has_document_word(message) and contains_any_word(message, account_words)


def contains_any_word(message, words):
    message = expand_bangla_banglish_text(message).lower()

    for word in words:
        if word in message:
            return True

    return False


def normalize_menu_text(message):
    message = expand_bangla_banglish_text(message)
    cleaned_text = "".join(
        character.lower() if character.isalnum() else " "
        for character in message
    )

    return " ".join(cleaned_text.split())


def normalize_literal_menu_text(message):
    cleaned_text = "".join(
        character.lower() if character.isalnum() else " "
        for character in message
    )

    return " ".join(cleaned_text.split())


def literal_card_charge_menu_category(message):
    normalized_message = normalize_literal_menu_text(message)
    menu_aliases = {
        "card charge": "cards",
        "card charges": "cards",
        "cards charge": "cards",
        "cards charges": "cards",
        "credit card charge": "credit",
        "credit card charges": "credit",
        "credit cards charge": "credit",
        "credit cards charges": "credit",
        "debit card charge": "debit",
        "debit card charges": "debit",
        "debit cards charge": "debit",
        "debit cards charges": "debit",
        "prepaid card charge": "prepaid",
        "prepaid card charges": "prepaid",
        "prepaid cards charge": "prepaid",
        "prepaid cards charges": "prepaid",
    }

    return menu_aliases.get(normalized_message, "")


def literal_schedule_charge_menu_category(message):
    normalized_message = normalize_literal_menu_text(message)
    menu_aliases = {
        "retail charge": "retail",
        "retail charges": "retail",
        "retail banking charge": "retail",
        "retail banking charges": "retail",
        "sme charge": "sme",
        "sme charges": "sme",
        "sme banking charge": "sme",
        "sme banking charges": "sme",
        "corp charge": "corporate",
        "corp charges": "corporate",
        "corporate charge": "corporate",
        "corporate charges": "corporate",
        "corporate banking charge": "corporate",
        "corporate banking charges": "corporate",
        "card charge": "cards",
        "card charges": "cards",
        "cards charge": "cards",
        "cards charges": "cards",
    }

    return menu_aliases.get(normalized_message, "")


def is_schedule_charges_menu_request(message):
    normalized_message = normalize_menu_text(message)

    return (
        normalized_message in {
        "schedule of charges",
        "charges schedule",
        "schedule charges",
        "banking charges",
        "banking charge",
    }
        or "schedule of charges" in normalized_message
    )


def get_schedule_charge_category(message):
    normalized_message = normalize_menu_text(message)
    normalized_words = set(normalized_message.split())
    specific_charge_words = {
        "activation",
        "annual",
        "atm",
        "bpid",
        "book",
        "cash",
        "certificate",
        "cheque",
        "closing",
        "collection",
        "courier",
        "digital",
        "draft",
        "eblconnect",
        "export",
        "fcy",
        "fee",
        "fees",
        "guarantee",
        "import",
        "instruction",
        "lc",
        "lending",
        "loan",
        "maintenance",
        "npsb",
        "order",
        "pay",
        "payment",
        "pin",
        "postage",
        "processing",
        "rate",
        "remittance",
        "replacement",
        "report",
        "rtgs",
        "solvency",
        "standing",
        "statement",
        "supplementary",
        "swift",
        "token",
        "tt",
        "transfer",
        "withdrawal",
    }
    category_aliases = {
        "retail": {
            "retail",
            "retail charge",
            "retail charges",
            "retail banking charge",
            "retail banking charges",
        },
        "sme": {
            "sme",
            "sme charge",
            "sme charges",
            "sme banking charge",
            "sme banking charges",
        },
        "corporate": {
            "corp",
            "corp charge",
            "corp charges",
            "corporate",
            "corporate charge",
            "corporate charges",
            "corporate banking charge",
            "corporate banking charges",
        },
        "cards": {
            "card",
            "card charge",
            "card charges",
            "cards",
            "cards charge",
            "cards charges",
            "credit card charge",
            "credit card charges",
            "credit cards charge",
            "credit cards charges",
            "debit card charge",
            "debit card charges",
            "debit cards charge",
            "debit cards charges",
            "prepaid card charge",
            "prepaid card charges",
            "prepaid cards charge",
            "prepaid cards charges",
        },
    }

    for category, aliases in category_aliases.items():
        if normalized_message in aliases:
            return category

    if not normalized_words & {"charge", "charges", "fee", "fees", "schedule"}:
        return ""

    if normalized_words & specific_charge_words:
        return ""

    if "retail" in normalized_words:
        return "retail"

    if "sme" in normalized_words:
        return "sme"

    if normalized_words & {"corporate", "corp"}:
        return "corporate"

    if normalized_words & {"card", "cards"}:
        return "cards"

    return ""


def build_schedule_charge_category_reply(category):
    category_label = SCHEDULE_CHARGE_CATEGORY_LABELS.get(category, "Banking")

    return (
        f"Which specific {category_label} charge do you want to know? "
        "Please type the charge name, for example account maintenance fee, "
        "cheque book fee, credit report fee, annual fee, or cash withdrawal fee."
    )


def build_retail_charge_group_reply():
    action_lines = "\n".join(
        f"- {option}"
        for option in retail_charge_group_options()
    )

    return f"Which Retail charge category do you want to know?\n\n{action_lines}"


def build_retail_charge_subcategory_reply(group_key):
    group_label = retail_charge_group_label(group_key)
    categories = retail_charge_group_categories(group_key)

    if not group_label or not categories:
        return ""

    if len(categories) == 1:
        return build_retail_charge_product_reply(categories[0])

    action_lines = "\n".join(f"- {category}" for category in categories)

    return (
        f"Which Retail charge subcategory do you want under {group_label}?\n\n"
        f"{action_lines}"
    )


def build_retail_charge_product_reply(category):
    category_label = retail_charge_category_label(category)
    products = retail_charge_products(category_label)

    if not category_label or not products:
        return ""

    if len(products) == 1:
        return build_retail_charge_name_reply(category_label, products[0])

    action_lines = "\n".join(f"- {product}" for product in products)

    return (
        f"Which Retail {category_label} product/account type do you want?\n\n"
        f"{action_lines}"
    )


def build_retail_charge_name_reply(category, product):
    category_label = retail_charge_category_label(category)
    product_label = retail_charge_product_label(category_label, product)
    charge_names = retail_charge_names(category_label, product_label)

    if not category_label or not product_label or not charge_names:
        return ""

    if len(charge_names) == 1:
        return answer_exact_retail_charge(
            category_label,
            product_label,
            charge_names[0],
        )

    action_lines = "\n".join(f"- {charge_name}" for charge_name in charge_names)

    return (
        f"Which Retail {category_label} charge do you want for {product_label}?\n\n"
        f"{action_lines}"
    )


def retail_charge_context_from_reply(reply):
    if reply.startswith("Which Retail charge category"):
        return {"stage": "group"}

    subcategory_match = re.match(
        r"Which Retail charge subcategory do you want under (.+?)\?",
        reply,
    )

    if subcategory_match:
        return {
            "stage": "subcategory",
            "group": subcategory_match.group(1).strip(),
        }

    product_match = re.match(
        r"Which Retail (.+?) product/account type do you want\?",
        reply,
    )

    if product_match:
        return {
            "stage": "product",
            "category": product_match.group(1).strip(),
        }

    charge_match = re.match(
        r"Which Retail (.+?) charge do you want for (.+?)\?",
        reply,
    )

    if charge_match:
        return {
            "stage": "charge",
            "category": charge_match.group(1).strip(),
            "product": charge_match.group(2).strip(),
        }

    return {}


def last_retail_charge_context(session_id):
    reply = last_assistant_reply(session_id)
    return retail_charge_context_from_reply(reply)


def has_recent_retail_charge_context(session_id):
    history = get_chat_history(session_id, limit=8)

    for message in reversed(history):
        if message["role"] != "assistant":
            continue

        context = retail_charge_context_from_reply(message["content"])

        if context:
            return True

    return False


def build_retail_charge_recovery_reply(session_id, user_message):
    if not has_recent_retail_charge_context(session_id):
        return ""

    group_key = retail_charge_group_key(user_message)

    if group_key:
        return build_retail_charge_subcategory_reply(group_key)

    category = retail_charge_category_label(user_message)

    if category:
        return build_retail_charge_product_reply(category)

    product_matches = retail_charge_product_matches(user_message)

    if len(product_matches) == 1:
        category, product = product_matches[0]
        return build_retail_charge_name_reply(category, product)

    return ""


def build_retail_charge_flow_reply(session_id, user_message):
    context = last_retail_charge_context(session_id)

    if not context:
        return ""

    if context["stage"] == "group":
        group_key = retail_charge_group_key(user_message)

        if group_key:
            return build_retail_charge_subcategory_reply(group_key)

        return ""

    if context["stage"] == "subcategory":
        category = retail_charge_category_label(user_message)

        if category:
            return build_retail_charge_product_reply(category)

        return ""

    if context["stage"] == "product":
        category = context["category"]
        product = retail_charge_product_label(category, user_message)

        if product:
            return build_retail_charge_name_reply(category, product)

        return ""

    if context["stage"] == "charge":
        category = context["category"]
        product = context["product"]
        charge_name = retail_charge_name_label(category, product, user_message)

        if not charge_name:
            alternate_product = retail_charge_product_label(category, user_message)

            if alternate_product:
                return build_retail_charge_name_reply(category, alternate_product)

            return ""

        return answer_exact_retail_charge(category, product, charge_name)

    return ""


def build_sme_charge_group_reply():
    action_lines = "\n".join(
        f"- {option}"
        for option in sme_charge_group_options()
    )

    return f"Which SME charge category do you want to know?\n\n{action_lines}"


def build_sme_charge_subcategory_reply(group_key):
    group_label = sme_charge_group_label(group_key)
    categories = sme_charge_group_categories(group_key)

    if not group_label or not categories:
        return ""

    if group_key == "certificates_reports":
        return build_sme_certificates_reports_reply()

    if group_key == "cheque_clearing":
        return build_sme_cheque_clearing_reply()

    if len(categories) == 1:
        return build_sme_charge_product_reply(categories[0])

    action_lines = "\n".join(f"- {category}" for category in categories)

    return (
        f"Which SME charge subcategory do you want under {group_label}?\n\n"
        f"{action_lines}"
    )


def build_sme_charge_product_reply(category):
    category_label = sme_charge_category_label(category)

    if category_label == "SME Loan Facilities":
        return build_sme_loan_charge_reply()

    products = sme_charge_products(category_label)

    if not category_label or not products:
        return ""

    if len(products) == 1:
        return build_sme_charge_name_reply(category_label, products[0])

    action_lines = "\n".join(f"- {product}" for product in products)

    return (
        f"Which SME {category_label} product/account type do you want?\n\n"
        f"{action_lines}"
    )


def build_sme_charge_name_reply(category, product):
    category_label = sme_charge_category_label(category)
    product_label = sme_charge_product_label(category_label, product)
    charge_names = sme_charge_names(category_label, product_label)

    if not category_label or not product_label or not charge_names:
        return ""

    if len(charge_names) == 1:
        return answer_exact_sme_charge(
            category_label,
            product_label,
            charge_names[0],
        )

    action_lines = "\n".join(f"- {charge_name}" for charge_name in charge_names)

    return (
        f"Which SME {category_label} charge do you want for {product_label}?\n\n"
        f"{action_lines}"
    )


def build_sme_loan_charge_reply():
    charge_names = sme_charge_names_for_category("SME Loan Facilities")

    if not charge_names:
        return ""

    action_lines = "\n".join(f"- {charge_name}" for charge_name in charge_names)

    return f"Which SME loan charge do you want to know?\n\n{action_lines}"


def build_sme_certificates_reports_reply():
    services = sme_charge_products("Certificates/Reports")

    if "Holding of Bonds" not in services:
        services.append("Holding of Bonds")

    action_lines = "\n".join(f"- {service}" for service in services)

    return f"Which SME certificate/report service do you want?\n\n{action_lines}"


def build_sme_cheque_clearing_reply():
    services = []

    for category in [
        "Cheque Collection",
        "Cheque Clearing",
        "FCY Cheque Collection",
    ]:
        services.extend(sme_charge_products(category))

    action_lines = "\n".join(f"- {service}" for service in services)

    return f"Which SME cheque/clearing service do you want?\n\n{action_lines}"


def sme_charge_context_from_reply(reply):
    if reply.startswith("Which SME charge category"):
        return {"stage": "group"}

    if reply.startswith("Which SME loan charge"):
        return {"stage": "loan_charge"}

    if reply.startswith("Which SME certificate/report service"):
        return {"stage": "certificates_reports_service"}

    if reply.startswith("Which SME cheque/clearing service"):
        return {"stage": "cheque_clearing_service"}

    subcategory_match = re.match(
        r"Which SME charge subcategory do you want under (.+?)\?",
        reply,
    )

    if subcategory_match:
        return {
            "stage": "subcategory",
            "group": subcategory_match.group(1).strip(),
        }

    product_match = re.match(
        r"Which SME (.+?) product/account type do you want\?",
        reply,
    )

    if product_match:
        return {
            "stage": "product",
            "category": product_match.group(1).strip(),
        }

    charge_match = re.match(
        r"Which SME (.+?) charge do you want for (.+?)\?",
        reply,
    )

    if charge_match:
        return {
            "stage": "charge",
            "category": charge_match.group(1).strip(),
            "product": charge_match.group(2).strip(),
        }

    return {}


def last_sme_charge_context(session_id):
    reply = last_assistant_reply(session_id)
    return sme_charge_context_from_reply(reply)


def has_recent_sme_charge_context(session_id):
    history = get_chat_history(session_id, limit=8)

    for message in reversed(history):
        if message["role"] != "assistant":
            continue

        context = sme_charge_context_from_reply(message["content"])

        if context:
            return True

    return False


def build_sme_charge_recovery_reply(session_id, user_message):
    if not has_recent_sme_charge_context(session_id):
        return ""

    group_key = sme_charge_group_key(user_message)

    if group_key:
        return build_sme_charge_subcategory_reply(group_key)

    category = sme_charge_category_label(user_message)

    if category:
        return build_sme_charge_product_reply(category)

    product_matches = sme_charge_product_matches(user_message)

    if len(product_matches) == 1:
        category, product = product_matches[0]
        return build_sme_charge_name_reply(category, product)

    return ""


def build_sme_charge_flow_reply(session_id, user_message):
    context = last_sme_charge_context(session_id)

    if not context:
        return ""

    if context["stage"] == "cheque_clearing_service":
        for category in [
            "Cheque Collection",
            "Cheque Clearing",
            "FCY Cheque Collection",
        ]:
            product = sme_charge_product_label(category, user_message)

            if product:
                return build_sme_charge_name_reply(category, product)

        return ""

    if context["stage"] == "certificates_reports_service":
        normalized_message = normalize_menu_text(user_message)

        if normalized_message in {"holding of bonds", "bonds"}:
            return build_sme_charge_name_reply("Holding of Bonds", "Bonds")

        product = sme_charge_product_label("Certificates/Reports", user_message)

        if product:
            return build_sme_charge_name_reply("Certificates/Reports", product)

        return ""

    if context["stage"] == "loan_charge":
        charge_name = sme_charge_name_for_category_label(
            "SME Loan Facilities",
            user_message,
        )

        if charge_name:
            return answer_exact_sme_category_charge(
                "SME Loan Facilities",
                charge_name,
            )

        return ""

    if context["stage"] == "group":
        group_key = sme_charge_group_key(user_message)

        if group_key:
            return build_sme_charge_subcategory_reply(group_key)

        return ""

    if context["stage"] == "subcategory":
        category = sme_charge_category_label(user_message)

        if category:
            return build_sme_charge_product_reply(category)

        return ""

    if context["stage"] == "product":
        category = context["category"]
        product = sme_charge_product_label(category, user_message)

        if product:
            return build_sme_charge_name_reply(category, product)

        return ""

    if context["stage"] == "charge":
        category = context["category"]
        product = context["product"]
        charge_name = sme_charge_name_label(category, product, user_message)

        if not charge_name:
            alternate_product = sme_charge_product_label(category, user_message)

            if alternate_product:
                return build_sme_charge_name_reply(category, alternate_product)

            return ""

        return answer_exact_sme_charge(category, product, charge_name)

    return ""


def build_corporate_charge_group_reply():
    action_lines = "\n".join(
        f"- {option}"
        for option in corporate_charge_group_options()
    )

    return f"Which Corporate charge category do you want to know?\n\n{action_lines}"


def build_corporate_group_service_reply(group_key):
    group_label = corporate_charge_group_label(group_key)
    charge_names = corporate_charge_names_for_group(group_key)

    if not group_label or not charge_names:
        return ""

    action_lines = "\n".join(f"- {charge_name}" for charge_name in charge_names)

    return f"Which Corporate {group_label} charge do you want?\n\n{action_lines}"


def build_corporate_charge_subcategory_reply(group_key):
    group_label = corporate_charge_group_label(group_key)
    categories = corporate_charge_group_categories(group_key)

    if not group_label or not categories:
        return ""

    return build_corporate_group_service_reply(group_key)


def build_corporate_charge_product_reply(category):
    category_label = corporate_charge_category_label(category)
    products = corporate_charge_products(category_label)

    if not category_label or not products:
        return ""

    if len(products) == 1:
        return build_corporate_charge_name_reply(category_label, products[0])

    action_lines = "\n".join(f"- {product}" for product in products)

    return (
        f"Which Corporate {corporate_charge_category_display_label(category_label)} "
        f"service do you want?\n\n{action_lines}"
    )


def build_corporate_charge_name_reply(category, product):
    category_label = corporate_charge_category_label(category)
    product_label = corporate_charge_product_label(category_label, product)
    charge_names = corporate_charge_names(category_label, product_label)

    if not category_label or not product_label or not charge_names:
        return ""

    if len(charge_names) == 1:
        return answer_exact_corporate_charge(
            category_label,
            product_label,
            charge_names[0],
        )

    action_lines = "\n".join(f"- {charge_name}" for charge_name in charge_names)
    category_display = corporate_charge_category_display_label(category_label)
    generic_product_labels = {
        "Export Trade Service",
        "Guarantee",
        "Import Trade Service",
        "Supply Chain Finance",
        "Trade Service",
    }

    if product_label in generic_product_labels:
        return (
            f"Which Corporate {category_display} charge do you want?\n\n"
            f"{action_lines}"
        )

    return (
        f"Which Corporate {category_display} charge do you want for {product_label}?\n\n"
        f"{action_lines}"
    )


def corporate_charge_context_from_reply(reply):
    if reply.startswith("Which Corporate charge category"):
        return {"stage": "group"}

    group_charge_match = re.match(
        r"Which Corporate (.+?) charge do you want\?",
        reply,
    )

    if group_charge_match:
        group_key = corporate_charge_group_key(group_charge_match.group(1).strip())

        if group_key:
            return {
                "stage": "group_charge",
                "group_key": group_key,
            }

    subcategory_match = re.match(
        r"Which Corporate charge subcategory do you want under (.+?)\?",
        reply,
    )

    if subcategory_match:
        return {
            "stage": "subcategory",
            "group": subcategory_match.group(1).strip(),
        }

    product_match = re.match(
        r"Which Corporate (.+?) product/account type do you want\?",
        reply,
    )

    if not product_match:
        product_match = re.match(
            r"Which Corporate (.+?) service do you want\?",
            reply,
        )

    if product_match:
        return {
            "stage": "product",
            "category": product_match.group(1).strip(),
        }

    charge_match = re.match(
        r"Which Corporate (.+?) charge do you want for (.+?)\?",
        reply,
    )

    if not charge_match:
        no_product_charge_match = re.match(
            r"Which Corporate (.+?) charge do you want\?",
            reply,
        )

        if no_product_charge_match:
            category = no_product_charge_match.group(1).strip()
            products = corporate_charge_products(category)

            if len(products) == 1:
                return {
                    "stage": "charge",
                    "category": category,
                    "product": products[0],
                }

    if charge_match:
        return {
            "stage": "charge",
            "category": charge_match.group(1).strip(),
            "product": charge_match.group(2).strip(),
        }

    return {}


def last_corporate_charge_context(session_id):
    reply = last_assistant_reply(session_id)
    return corporate_charge_context_from_reply(reply)


def has_recent_corporate_charge_context(session_id):
    history = get_chat_history(session_id, limit=8)

    for message in reversed(history):
        if message["role"] != "assistant":
            continue

        context = corporate_charge_context_from_reply(message["content"])

        if context:
            return True

    return False


def build_corporate_charge_recovery_reply(session_id, user_message):
    if not has_recent_corporate_charge_context(session_id):
        return ""

    group_key = corporate_charge_group_key(user_message)

    if group_key:
        return build_corporate_charge_subcategory_reply(group_key)

    category = corporate_charge_category_label(user_message)

    if category:
        group_key = corporate_charge_group_key(
            corporate_charge_category_display_label(category)
        )

        if group_key:
            return build_corporate_charge_subcategory_reply(group_key)

        return build_corporate_charge_product_reply(category)

    product_matches = corporate_charge_product_matches(user_message)

    if len(product_matches) == 1:
        category, product = product_matches[0]
        return build_corporate_charge_name_reply(category, product)

    return ""


def build_corporate_charge_flow_reply(session_id, user_message):
    context = last_corporate_charge_context(session_id)

    if not context:
        return ""

    if context["stage"] == "group":
        group_key = corporate_charge_group_key(user_message)

        if group_key:
            return build_corporate_charge_subcategory_reply(group_key)

        return ""

    if context["stage"] == "group_charge":
        group_key = context["group_key"]
        charge_name = corporate_charge_name_for_group_label(group_key, user_message)

        if charge_name:
            return answer_exact_corporate_group_charge(group_key, charge_name)

        return ""

    if context["stage"] == "subcategory":
        category = corporate_charge_category_label(user_message)

        if category:
            group_key = corporate_charge_group_key(
                corporate_charge_category_display_label(category)
            )

            if group_key:
                return build_corporate_charge_subcategory_reply(group_key)

            return build_corporate_charge_product_reply(category)

        return ""

    if context["stage"] == "product":
        category = context["category"]
        product = corporate_charge_product_label(category, user_message)

        if product:
            return build_corporate_charge_name_reply(category, product)

        return ""

    if context["stage"] == "charge":
        category = context["category"]
        product = context["product"]
        charge_name = corporate_charge_name_label(category, product, user_message)

        if not charge_name:
            alternate_product = corporate_charge_product_label(category, user_message)

            if alternate_product:
                return build_corporate_charge_name_reply(category, alternate_product)

            return ""

        return answer_exact_corporate_charge(category, product, charge_name)

    return ""


def build_card_charge_type_reply():
    action_lines = "\n".join(
        f"- {option}"
        for option in card_charge_category_options()
    )

    return f"Which Card charge type do you want to know?\n\n{action_lines}"


def build_card_charge_product_reply(category):
    category_label = card_charge_category_label(category)
    products = card_charge_products(category_label)

    if not category_label or not products:
        return ""

    display_label = card_charge_category_display_label(category_label)
    action_lines = "\n".join(f"- {product}" for product in products)

    return (
        f"Which {display_label} product do you want for charges?\n\n"
        f"{action_lines}"
    )


def build_card_charge_name_reply(category, product):
    category_label = card_charge_category_label(category)
    product_label = card_charge_product_label(category_label, product)
    charge_names = card_charge_names(category_label, product_label)

    if not category_label or not product_label or not charge_names:
        return ""

    if len(charge_names) == 1:
        return answer_exact_card_charge(
            category_label,
            product_label,
            charge_names[0],
        )

    display_label = card_charge_category_display_label(category_label)
    action_lines = "\n".join(f"- {charge_name}" for charge_name in charge_names)

    return (
        f"Which {display_label} charge do you want for {product_label}?\n\n"
        f"{action_lines}"
    )


def card_charge_context_from_reply(reply):
    if reply.startswith("Which Card charge type"):
        return {"stage": "type"}

    product_match = re.match(
        r"Which (.+?) product do you want for charges\?",
        reply,
    )

    if product_match:
        return {
            "stage": "product",
            "category": product_match.group(1).strip(),
        }

    charge_match = re.match(
        r"Which (.+?) charge do you want for (.+?)\?",
        reply,
    )

    if charge_match:
        return {
            "stage": "charge",
            "category": charge_match.group(1).strip(),
            "product": charge_match.group(2).strip(),
        }

    return {}


def last_card_charge_context(session_id):
    reply = last_assistant_reply(session_id)
    return card_charge_context_from_reply(reply)


def recent_card_charge_context(session_id):
    history = get_chat_history(session_id, limit=8)

    for message in reversed(history):
        if message["role"] != "assistant":
            continue

        context = card_charge_context_from_reply(message["content"])

        if context:
            return context

    return {}


def has_recent_card_charge_context(session_id):
    return bool(recent_card_charge_context(session_id))


def build_card_charge_recovery_reply(session_id, user_message):
    context = recent_card_charge_context(session_id)

    if not context:
        return ""

    if context["stage"] == "charge":
        category = context["category"]
        product = context["product"]
        charge_name = card_charge_name_label(category, product, user_message)

        if charge_name:
            return answer_exact_card_charge(category, product, charge_name)

    category = card_charge_category_label(user_message)

    if category:
        return build_card_charge_product_reply(category)

    product_matches = card_charge_product_matches(user_message)

    if len(product_matches) == 1:
        category, product = product_matches[0]
        return build_card_charge_name_reply(category, product)

    return ""


def build_card_charge_flow_reply(session_id, user_message):
    context = last_card_charge_context(session_id)

    if not context:
        return ""

    if context["stage"] == "type":
        category = card_charge_category_label(user_message)

        if category:
            return build_card_charge_product_reply(category)

        return ""

    if context["stage"] == "product":
        category = context["category"]
        product = card_charge_product_label(category, user_message)

        if product:
            return build_card_charge_name_reply(category, product)

        return ""

    if context["stage"] == "charge":
        category = context["category"]
        product = context["product"]
        charge_name = card_charge_name_label(category, product, user_message)

        if not charge_name:
            alternate_product = card_charge_product_label(category, user_message)

            if alternate_product:
                return build_card_charge_name_reply(category, alternate_product)

            return ""

        return answer_exact_card_charge(category, product, charge_name)

    return ""


def last_reply_was_schedule_charges_menu(session_id):
    history = get_chat_history(session_id, limit=1)

    return any(
        message["role"] == "assistant"
        and message["content"] == SCHEDULE_CHARGES_MENU_REPLY
        for message in history
    )


def is_bare_schedule_charge_category(message):
    normalized_message = normalize_menu_text(message)
    words = set(normalized_message.split())

    if normalized_message in {
        "retail",
        "sme",
        "corp",
        "corporate",
        "card",
        "cards",
    }:
        return True

    if words & {"account", "accounts", "loan", "loans", "charge", "charges", "fee", "fees", "support"}:
        return False

    return bool(
        words & {"retail", "sme", "corp", "corporate", "card", "cards"}
    )


def last_assistant_reply(session_id, limit=6):
    history = get_chat_history(session_id, limit=limit)

    for message in reversed(history):
        if message["role"] == "assistant":
            return message["content"]

    return ""


def last_user_message(session_id, limit=6):
    history = get_chat_history(session_id, limit=limit)

    for message in reversed(history):
        if message["role"] == "user":
            return message["content"]

    return ""


def last_reply_was_schedule_charge_prompt(session_id):
    reply = last_assistant_reply(session_id)

    return (
        reply == SCHEDULE_CHARGES_MENU_REPLY
        or reply.startswith("Which specific Retail charge")
        or reply.startswith("Which specific SME charge")
        or reply.startswith("Which specific Corporate charge")
        or reply.startswith("Which specific Cards charge")
    )


def schedule_from_charge_prompt(reply):
    if reply.startswith("Which specific Retail charge"):
        return "retail"

    if reply.startswith("Which specific SME charge"):
        return "sme"

    if reply.startswith("Which specific Corporate charge"):
        return "corporate"

    if reply.startswith("Which specific Cards charge"):
        return "cards"

    return ""


def last_reply_was_charge_clarification_prompt(session_id):
    reply = last_assistant_reply(session_id).lower()

    return (
        reply.startswith("please specify the product/account type:")
        or reply.startswith("please specify the exact charge:")
    )


def is_charge_condition_follow_up(message):
    normalized_message = normalize_menu_text(message)

    return any(
        phrase in f" {normalized_message} "
        for phrase in [
            " above ",
            " below ",
            " under ",
            " over ",
            " up to ",
            " upto ",
            " more than ",
            " less than ",
            " within country ",
            " outside country ",
            " onshore ",
            " offshore ",
            " same day ",
            " next day ",
        ]
    ) or any(word.isdigit() for word in normalized_message.split())


def is_charge_product_follow_up(message):
    words = normalized_word_set(message)

    return bool(
        words
        & {
            "account",
            "accounts",
            "bank",
            "card",
            "cards",
            "corp",
            "corporate",
            "customer",
            "customers",
            "ebl",
            "other",
            "retail",
            "sme",
        }
    )


def is_primary_navigation_message(message):
    normalized_message = normalize_menu_text(message)

    if is_fee_or_charge_question(message):
        return False

    return normalized_message in {
        "open an account",
        "loan information",
        "card support",
        "interest rate",
        "interest rates",
        "retail loan",
        "retail loans",
        "sme loan",
        "sme loans",
        "retail account",
        "sme account",
        "islamic account",
        "debit card",
        "credit card",
        "prepaid card",
        "islamic card",
    }


def last_reply_looks_like_charge_answer(session_id):
    reply = last_assistant_reply(session_id).lower()

    return (
        " charges:" in reply
        or " fee:" in reply
        or " fee for " in reply
        or " charge for " in reply
        or " + vat" in reply
        or "vat included" in reply
    )


def build_contextual_charge_query(session_id, user_message):
    if is_primary_navigation_message(user_message):
        return ""

    if is_specific_card_product_information_request(user_message):
        return ""

    previous_user_message = last_user_message(session_id)
    previous_assistant_reply = last_assistant_reply(session_id)

    if (
        previous_user_message
        and not is_fee_or_charge_question(user_message)
        and (
            is_fee_or_charge_question(previous_user_message)
            or last_reply_looks_like_charge_answer(session_id)
        )
        and is_charge_condition_follow_up(user_message)
    ):
        return f"{previous_user_message} {user_message}"

    if last_reply_was_charge_clarification_prompt(session_id):
        if previous_user_message:
            return f"{previous_user_message} {user_message}"

        return user_message

    if (
        last_reply_looks_like_charge_answer(session_id)
        and not is_fee_or_charge_question(user_message)
        and is_charge_product_follow_up(user_message)
    ):
        return user_message

    if last_reply_was_schedule_charge_prompt(session_id):
        schedule_context = schedule_from_charge_prompt(previous_assistant_reply)

        if schedule_context:
            return f"{schedule_context} {user_message}"

        return user_message

    return ""


def get_bare_banking_segment(message):
    normalized_message = normalize_menu_text(message)

    if normalized_message in ["retail", "sme", "islamic"]:
        return normalized_message

    words = set(normalized_message.split())

    if words & {
        "account",
        "accounts",
        "business",
        "card",
        "cards",
        "charge",
        "charges",
        "deposit",
        "deposits",
        "dps",
        "fd",
        "fdr",
        "fee",
        "fees",
        "fixed",
        "loan",
        "loans",
        "rate",
        "rates",
        "recurring",
        "saving",
        "savings",
        "unit",
    }:
        return ""

    if "retail" in words:
        return "retail"

    if "sme" in words:
        return "sme"

    if "islamic" in words:
        return "islamic"

    return ""


def build_bare_banking_segment_reply(session_id, user_message):
    segment = get_bare_banking_segment(user_message)

    if not segment:
        return ""

    history = get_chat_history(session_id, limit=4)

    if last_assistant_asked_for_account_category(history):
        if segment in ACCOUNT_SEGMENT_SCHEDULES:
            return build_account_schedule_category_reply(segment)

        if segment == "islamic":
            return build_account_category_reply("islamic_deposit")

    if last_assistant_asked_for_loan_category(history):
        if segment in ["retail", "sme"]:
            return build_loan_category_reply(segment)

        return (
            "For Islamic banking, please tell me whether you want Islamic account, "
            "Islamic finance or Islamic card information."
        )

    segment_label = {
        "retail": "Retail",
        "sme": "SME",
        "islamic": "Islamic",
    }.get(segment, "that")

    return (
        f"Please specify what you want to know about {segment_label}: "
        "account, loan, card or schedule of charges."
    )


def normalized_word_set(message):
    return set(normalize_menu_text(message).split())


def is_interest_rate_phrase(message):
    normalized_message = normalize_menu_text(message)

    return (
        "interest rate" in normalized_message
        or "interest rates" in normalized_message
    )


def has_rate_word(message):
    return bool(normalized_word_set(message) & {"rate", "rates"})


def has_card_rate_context(message):
    words = normalized_word_set(message)

    return bool(
        words
        & {
            "card",
            "cards",
            "credit",
            "debit",
            "prepaid",
            "visa",
            "mastercard",
            "diners",
            "unionpay",
        }
    )


def has_lending_rate_context(message):
    words = normalized_word_set(message)

    return bool(
        words
        & {
            "lending",
            "loan",
            "loans",
            "finance",
            "financing",
            "mortgage",
            "home",
            "auto",
            "personal",
            "car",
            "vehicle",
            "wheeler",
        }
    )


def has_specific_deposit_rate_context(message):
    words = {
        word for word in normalized_word_set(message)
        if word.isascii()
    }
    generic_words = {
        "about",
        "bank",
        "banking",
        "can",
        "ebl",
        "eastern",
        "give",
        "how",
        "i",
        "interest",
        "know",
        "koto",
        "may",
        "me",
        "much",
        "my",
        "of",
        "please",
        "plc",
        "rate",
        "rates",
        "show",
        "tell",
        "the",
        "want",
        "what",
        "you",
    }
    deposit_type_words = {
        "deposit",
        "deposits",
        "savings",
        "saving",
        "casa",
    }

    return bool(words - generic_words - deposit_type_words)


def has_specific_lending_rate_context(message):
    words = {
        word for word in normalized_word_set(message)
        if word.isascii()
    }
    generic_words = {
        "about",
        "bank",
        "banking",
        "can",
        "ebl",
        "eastern",
        "give",
        "how",
        "i",
        "interest",
        "know",
        "koto",
        "may",
        "me",
        "much",
        "my",
        "of",
        "please",
        "plc",
        "rate",
        "rates",
        "show",
        "tell",
        "the",
        "want",
        "what",
        "you",
    }
    lending_type_words = {
        "lending",
        "loan",
        "loans",
        "finance",
        "financing",
    }

    return bool(words - generic_words - lending_type_words)


def get_interest_rate_type_choice(message):
    words = normalized_word_set(message)

    if words & {
        "deposit",
        "deposits",
        "savings",
        "saving",
        "casa",
        "snd",
        "hpa",
        "fd",
        "fdr",
        "fixed",
        "dps",
        "recurring",
    }:
        return "deposit"

    if words & {
        "lending",
        "loan",
        "loans",
        "finance",
        "financing",
        "mortgage",
        "home",
        "auto",
        "personal",
        "car",
        "vehicle",
        "wheeler",
    }:
        return "lending"

    return ""


def is_broad_interest_rate_question(message):
    if not is_interest_rate_phrase(message):
        return False

    if has_card_rate_context(message):
        return False

    if is_deposit_rate_question(message) or has_lending_rate_context(message):
        return False

    return True


def last_reply_was_interest_rate_type_prompt(session_id):
    return last_assistant_reply(session_id) == INTEREST_RATE_TYPE_REPLY


def last_reply_was_deposit_rate_product_prompt(session_id):
    last_reply = last_assistant_reply(session_id)

    return (
        last_reply.startswith(
        "Please specify the deposit product or category"
    )
        or "deposit product rate do you want?" in last_reply
        or "timeline do you want?" in last_reply
        or "Savings/CASA product rate" in last_reply
        or "Retail FD product rate" in last_reply
        or "DPS/recurring deposit product rate" in last_reply
    )


def strip_deposit_timeline_from_subject(subject):
    return re.sub(
        r"\s+\d+(?:\.\d+)?\s+(?:day|days|month|months|year|years)$",
        "",
        subject.strip(),
        flags=re.IGNORECASE,
    ).strip()


def deposit_rate_context_from_reply(reply):
    timeline_match = re.search(r"Which (.+?) timeline do you want\?", reply)

    if timeline_match:
        return timeline_match.group(1).strip()

    if "Business Unit: Retail" in reply:
        return "Retail"

    if "Business Unit: Commercial" in reply:
        return "Commercial"

    if "Business Unit: Corporate" in reply:
        return "Corporate"

    if "Savings/CASA product rate" in reply:
        return "Retail"

    if "Retail FD product rate" in reply:
        return "Retail"

    if "DPS/recurring deposit product rate" in reply:
        return "Retail"

    answer_match = re.search(
        r"^(Retail|Commercial|Corporate)\s+(.+?)\s+interest rate:",
        reply,
        flags=re.IGNORECASE,
    )

    if answer_match:
        business_unit = answer_match.group(1).title()
        subject = strip_deposit_timeline_from_subject(answer_match.group(2))

        return f"{business_unit} {subject}".strip()

    return ""


def deposit_rate_prompt_context(session_id):
    history = get_chat_history(session_id, limit=12)

    for message in reversed(history):
        if message["role"] != "assistant":
            continue

        context = deposit_rate_context_from_reply(message["content"])

        if context:
            return context

    return ""


def build_contextual_deposit_rate_reply(session_id, user_message):
    if has_card_rate_context(user_message) or has_lending_rate_context(user_message):
        return ""

    if is_broad_interest_rate_question(user_message):
        return ""

    if not (
        looks_like_deposit_rate_product_name(user_message)
        or (
            (is_deposit_rate_question(user_message) or has_rate_word(user_message))
            and has_specific_deposit_rate_context(user_message)
        )
    ):
        return ""

    rate_context = deposit_rate_followup_context(
        deposit_rate_prompt_context(session_id),
        user_message,
    )

    if not rate_context:
        return ""

    rate_query = f"{rate_context} {user_message}".strip()

    return answer_deposit_rate_question_from_db(
        f"{rate_query} deposit interest rate"
    )


def last_reply_was_lending_rate_product_prompt(session_id):
    last_reply = last_assistant_reply(session_id)

    return (
        last_reply == LENDING_RATE_PRODUCT_REPLY
        or "lending product rate do you want?" in last_reply
    )


def build_lending_rate_reply(user_message):
    normalized_message = normalize_menu_text(user_message)

    if normalized_message in {
        "lending",
        "lending rate",
        "lending rates",
        "loan",
        "loan rate",
        "loan rates",
        "loan interest rate",
        "loan interest rates",
    }:
        return LENDING_RATE_PRODUCT_REPLY

    return (
        answer_lending_rate_question_from_db(
            f"{user_message} lending interest rate"
        )
        or LENDING_RATE_PRODUCT_REPLY
    )


def build_interest_rate_flow_reply(session_id, user_message):
    if last_reply_was_interest_rate_type_prompt(session_id):
        selected_rate_type = get_interest_rate_type_choice(user_message)
        normalized_message = normalize_menu_text(user_message)

        if selected_rate_type == "deposit":
            menu_reply = build_deposit_rate_menu_reply(user_message)

            if menu_reply:
                return menu_reply

            if normalized_message not in {
                "deposit",
                "deposits",
                "deposit rate",
                "deposit rates",
                "deposit interest rate",
                "deposit interest rates",
            }:
                structured_deposit_reply = answer_deposit_rate_question_from_db(
                    f"{user_message} deposit interest rate"
                )

                if structured_deposit_reply:
                    return structured_deposit_reply

            return build_broad_rate_clarification()

        if selected_rate_type == "lending":
            if normalized_message not in {
                "lending",
                "lending rate",
                "lending rates",
                "loan",
                "loan rate",
                "loan rates",
                "loan interest rate",
                "loan interest rates",
            }:
                return build_lending_rate_reply(user_message)

            return LENDING_RATE_PRODUCT_REPLY

        direct_deposit_reply = answer_deposit_rate_question_from_db(
            f"{user_message} deposit interest rate"
        )

        if direct_deposit_reply:
            return direct_deposit_reply

        direct_lending_reply = answer_lending_rate_question_from_db(
            f"{user_message} lending interest rate"
        )

        if direct_lending_reply and direct_lending_reply != LENDING_RATE_PRODUCT_REPLY:
            return direct_lending_reply

        return INTEREST_RATE_TYPE_REPLY

    if last_reply_was_deposit_rate_product_prompt(session_id):
        if is_broad_interest_rate_question(user_message):
            return INTEREST_RATE_TYPE_REPLY

        if get_interest_rate_type_choice(user_message) == "lending":
            return LENDING_RATE_PRODUCT_REPLY

        menu_reply = build_deposit_rate_menu_reply(user_message)

        if menu_reply:
            return menu_reply

        rate_context = deposit_rate_followup_context(
            deposit_rate_prompt_context(session_id),
            user_message,
        )
        rate_query = f"{rate_context} {user_message}".strip()

        return (
            answer_deposit_rate_question_from_db(
                f"{rate_query} deposit interest rate"
            )
            or build_broad_rate_clarification()
        )

    if last_reply_was_lending_rate_product_prompt(session_id):
        normalized_message = normalize_menu_text(user_message)

        if get_interest_rate_type_choice(user_message) == "deposit" and normalized_message in {
            "deposit",
            "deposits",
            "deposit rate",
            "deposit rates",
            "deposit interest rate",
            "deposit interest rates",
        }:
            return build_broad_rate_clarification()

        menu_reply = build_lending_rate_menu_reply(user_message)

        if menu_reply:
            return menu_reply

        return build_lending_rate_reply(user_message)

    if is_broad_interest_rate_question(user_message):
        return INTEREST_RATE_TYPE_REPLY

    contextual_deposit_reply = build_contextual_deposit_rate_reply(
        session_id,
        user_message,
    )

    if contextual_deposit_reply:
        return contextual_deposit_reply

    selected_rate_type = get_interest_rate_type_choice(user_message)
    normalized_message = normalize_menu_text(user_message)

    if selected_rate_type == "deposit" and normalized_message in {
        "deposit",
        "deposits",
        "deposit rate",
        "deposit rates",
        "deposit interest rate",
        "deposit interest rates",
    }:
        return build_broad_rate_clarification()

    deposit_menu_reply = build_deposit_rate_menu_reply(user_message)

    if deposit_menu_reply:
        return deposit_menu_reply

    if (
        selected_rate_type == "deposit"
        and (is_interest_rate_phrase(user_message) or has_rate_word(user_message))
        and not has_specific_deposit_rate_context(user_message)
    ):
        return build_broad_rate_clarification()

    if selected_rate_type == "lending" and normalized_message in {
        "lending",
        "lending rate",
        "lending rates",
        "loan interest rate",
        "loan interest rates",
    }:
        return LENDING_RATE_PRODUCT_REPLY

    lending_menu_reply = build_lending_rate_menu_reply(user_message)

    if lending_menu_reply:
        return lending_menu_reply

    if (
        selected_rate_type == "lending"
        and (is_interest_rate_phrase(user_message) or has_rate_word(user_message))
    ):
        if has_specific_lending_rate_context(user_message):
            return build_lending_rate_reply(user_message)

        return LENDING_RATE_PRODUCT_REPLY

    return ""


def looks_like_deposit_rate_product_name(message):
    words = normalized_word_set(message)

    if has_card_rate_context(message) or has_lending_rate_context(message):
        return False

    has_numeric_tenure = any(word.isdigit() for word in words) and bool(
        words & {"day", "days", "month", "months", "year", "years"}
    )

    has_rate_sheet_product_hint = (
        "century" in words
        or "alo" in words
        or "diamond" in words
        or ("high" in words and "value" in words)
        or ("extra" in words and "value" in words and bool(words & {"fd", "fdr"}))
    )

    if query_mentions_known_deposit_rate_product(message):
        return True

    if not has_numeric_tenure and not has_rate_sheet_product_hint:
        return False

    return bool(words & {"ebl", "fd", "fdr", "fixed", "term", "super"})


def last_reply_is_account_product_selection_prompt(history):
    for item in reversed(history or []):
        if item.get("role") != "assistant":
            continue

        content = item.get("content", "").lower()

        return (
            "which retail account category" in content
            or "which sme account category" in content
            or "which islamic account category" in content
            or "please tell me the specific account name" in content
            or (
                "please tell me the specific" in content
                and "product name" in content
                and "features and link" in content
            )
        )

    return False


def build_deposit_rate_product_name_reply(user_message, history=None):
    if last_reply_is_account_product_selection_prompt(history):
        return ""

    if not looks_like_deposit_rate_product_name(user_message):
        return ""

    return answer_deposit_rate_question_from_db(
        f"{user_message} deposit interest rate"
    )


def is_fee_or_charge_question(message):
    message = message.lower()

    charge_words = [
        "fee",
        "fees",
        "charge",
        "charges",
        "commission",
        "remittance",
        "inward",
        "schedule of charges",
        "vat",
        "maintenance fee",
        "annual fee",
        "minimum balance",
        "closing charge",
        "account closing",
    ]

    fee_service_phrases = [
        "atm receipt",
        "cash advance",
        "cash withdrawal",
        "cash withdrawal/advance",
        "cash withdrawal / advance",
        "cib report",
        "fund transfer",
        "guarantee amendment",
        "guarantee issuance",
        "lc opening",
        "lc processing",
        "pay order",
        "rtgs",
        "solvency certificate",
        "standing instruction",
        "swift",
        "inward remittance",
    ]

    return contains_any_word(message, charge_words + fee_service_phrases)


def build_charge_not_found_reply():
    return (
        "I could not find an exact match in the EBL Schedule of Charges. "
        "Please mention the schedule type, product/account type, and charge name "
        "for example Retail locker lost key replacement fee, SME inward remittance "
        "for other bank customer, or Cards replacement fee."
    )


def has_document_word(message, include_need=True):
    message = message.lower()

    document_words = [
        "document",
        "documents",
        "required",
        "requirement",
        "requirements",
    ]

    if include_need:
        document_words.extend(["need", "needed"])

    return contains_any_word(message, document_words)


def is_broad_account_opening_question(message):
    message = message.lower()

    broad_phrases = [
        "how can i open an account",
        "how to open an account",
        "open an account",
        "open account",
        "account opening",
        "account options",
        "account types",
        "available accounts",
        "create account",
        "new account",
        "what accounts are available",
        "which accounts are available",
    ]

    return any(phrase in message for phrase in broad_phrases)


def clean_document_line(line):
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2022": "-",
        "\ufffd": "'",
        "��": "",
        "\xb7": "",
        "\xa0": " ",
        "ofPartnership": "of Partnership",
    }

    cleaned_line = line.strip()

    for old_value, new_value in replacements.items():
        cleaned_line = cleaned_line.replace(old_value, new_value)

    return cleaned_line.strip()


def is_required_document_heading(line):
    lower_line = line.lower().rstrip(":")

    return (
        lower_line == "required documents for account opening"
        or lower_line == "documents required to open account"
        or lower_line.startswith("required documents to open")
        or lower_line.startswith("documents required to open")
        or lower_line == "identification document"
    )


def should_skip_document_line(line):
    lower_line = line.lower().strip()

    return (
        not line
        or line in ["|", "+", "-", "�"]
        or lower_line == "click here"
        or lower_line == "for required documents,"
        or lower_line == "for required documents"
    )


def should_stop_document_collection(line):
    lower_line = line.lower().strip()

    stop_prefixes = [
        "page:",
        "url:",
        "quick apply",
        "apply now",
        "apply for",
        "preferred branch",
        "ebl  self  service portal",
        "ebl self service portal",
        "existing customer",
        "new customer",
        "special benefits",
        "account opening form",
        "profit sharing ratio",
        "for more information",
        "for more details",
        "calculator",
        "relevant charges",
        "all fees are as per",
    ]

    return any(lower_line.startswith(prefix) for prefix in stop_prefixes)


def is_document_group_heading(line):
    lower_line = line.lower().rstrip(":")

    group_headings = [
        "partnership",
        "additional requirement for registered partnership",
        "limited liability/public/private company",
        "association/club/charity/trust/society etc.",
        "notes",
        "eligibility & requirements",
        "identification document",
    ]

    return lower_line in group_headings


def extract_required_document_lines(website_info):
    if not website_info:
        return []

    lines = [
        clean_document_line(line)
        for line in website_info.splitlines()
    ]

    start_index = -1

    for index, line in enumerate(lines):
        if is_required_document_heading(line):
            start_index = index
            break

    if start_index < 0:
        return []

    document_lines = []

    for line in lines[start_index + 1:]:
        if should_skip_document_line(line):
            continue

        if should_stop_document_collection(line):
            break

        if line in ["':", "' :"] and document_lines:
            document_lines[-1] = f"{document_lines[-1]}'" + ":"
            continue

        if (line.startswith("':") or line.startswith("' :")) and document_lines:
            suffix = line[1:].strip()
            document_lines[-1] = f"{document_lines[-1]}'{suffix}"
            continue

        document_lines.append(line)

        if line.lower().startswith("during account opening"):
            break

    return document_lines


def format_document_reply(title, document_lines):
    reply = f"{title}\n\n"
    inside_group = False

    for line in document_lines:
        lower_line = line.lower()

        if is_document_group_heading(line):
            reply += f"\n{line.rstrip(':')}:\n"
            inside_group = False
            continue

        if (
            lower_line.startswith("applicants")
            or lower_line.startswith("nominees")
        ):
            reply += f"- {line}\n"
            inside_group = True
            continue

        if (
            lower_line.startswith("completed")
            or lower_line.startswith("during account opening")
        ):
            reply += f"- {line}\n"
            inside_group = False
            continue

        if inside_group:
            reply += f"  - {line}\n"
        else:
            reply += f"- {line}\n"

    return reply.strip()


def build_required_documents_reply(user_message, website_info, product_name="", force=False):
    if not force and not is_document_question(user_message):
        return ""

    document_lines = extract_required_document_lines(website_info)

    if not document_lines:
        return ""

    if product_name:
        title = f"{product_name} required documents from the EBL website:"
    else:
        title = "The EBL website lists these required documents:"

    return format_document_reply(title, document_lines)


def normalize_loan_lookup_text(text):
    text = expand_bangla_banglish_text(text)
    text = text.lower()

    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "-": " ",
        "_": " ",
        "/": " ",
        "(": " ",
        ")": " ",
        ".": " ",
        ",": " ",
        "?": " ",
        "!": " ",
        ":": " ",
        "'": "",
    }

    for old_value, new_value in replacements.items():
        text = text.replace(old_value, new_value)

    return " ".join(text.split())


def contains_loan_lookup_phrase(message, phrase):
    normalized_message = normalize_loan_lookup_text(message)
    normalized_phrase = normalize_loan_lookup_text(phrase)

    return f" {normalized_phrase} " in f" {normalized_message} "


def detect_specific_loan_product(message):
    for product in LOAN_PRODUCT_RULES:
        for alias in product["aliases"]:
            if contains_loan_lookup_phrase(message, alias):
                return product

    return None


def detect_loan_category(message):
    normalized_message = normalize_loan_lookup_text(message)
    words = normalized_message.split()

    if "sme" in words:
        return "sme"

    if "retail" in words:
        return "retail"

    return ""


def last_assistant_asked_for_loan_category(history):
    for item in reversed(history):
        if item.get("role") != "assistant":
            continue

        content = item.get("content", "").lower()

        return "sme or retail loans" in content

    return False


def detect_loan_schedule_from_category_prompt(history):
    for item in reversed(history):
        if item.get("role") != "assistant":
            continue

        content = item.get("content", "").lower()

        if "which retail loan category" in content:
            return "Retail"

        return ""

    return ""


def is_loan_category_follow_up(message, history):
    return bool(
        detect_loan_category(message)
        and last_assistant_asked_for_loan_category(history)
    )


def build_retail_loan_category_prompt():
    categories = get_loan_categories("Retail")

    if not categories:
        return ""

    category_lines = "\n".join(f"- {category}" for category in categories)

    return (
        "Which Retail loan category do you want to know?\n\n"
        f"{category_lines}"
    )


def build_retail_loan_names_for_category_reply(category):
    loan_names = get_loan_names("Retail", category)

    if not loan_names:
        return ""

    loan_lines = "\n".join(f"- {loan_name}" for loan_name in loan_names)

    return (
        f"EBL Retail {category} options include:\n\n"
        f"{loan_lines}\n\n"
        "Please tell me the specific loan name if you want details or eligibility."
    )


def build_loan_category_reply(category):
    if category == "retail":
        category_prompt = build_retail_loan_category_prompt()

        if category_prompt:
            return category_prompt

        product_lines = "\n".join(f"- {product}" for product in RETAIL_LOAN_PRODUCTS)

        return (
            "EBL Retail Loan options include:\n\n"
            f"{product_lines}\n\n"
            "Please tell me the specific Retail loan name if you want its features and link."
        )

    if category == "sme":
        product_lines = "\n".join(f"- {product}" for product in SME_LOAN_PRODUCTS)

        return (
            "EBL SME Loan options include:\n\n"
            f"{product_lines}\n\n"
            "Please tell me the specific SME loan name if you want its features and link."
        )

    return ""


def build_retail_loan_subcategory_reply(user_message):
    if contains_loan_lookup_phrase(user_message, "personal loan"):
        return (
            "EBL Personal Loan options include:\n\n"
            "- EBL Assure\n"
            "- EBL Executive Loan\n"
            "- EBL Women's Loan\n\n"
            "Please tell me the specific Personal Loan product name if you want its features and link."
        )

    if (
        contains_loan_lookup_phrase(user_message, "secured loan")
        or contains_loan_lookup_phrase(user_message, "cash covered")
    ):
        return (
            "EBL Secured loan (Cash Covered) options include:\n\n"
            "- EBL Fast Cash\n"
            "- EBL Fast Loan\n\n"
            "Please tell me the specific Secured loan product name if you want its features and link."
        )

    return ""


def get_content_from_website_information(website_information):
    marker = "Content:\n"

    if marker not in website_information:
        return website_information

    return website_information.split(marker, 1)[1].strip()


def find_case_insensitive(text, pattern, start=0):
    return text.lower().find(pattern.lower(), start)


def slice_retail_loan_section(page_text, product_name):
    marker = f"BACK\n{product_name}\n"
    start = find_case_insensitive(page_text, marker)

    if start >= 0:
        section = page_text[start + len("BACK\n"):]
    else:
        title_marker = f"\n{product_name}\n"
        start = page_text.lower().rfind(title_marker.lower())

        if start < 0:
            start = find_case_insensitive(page_text, product_name)

        if start < 0:
            return page_text

        section = page_text[start:].strip()

    end_positions = []

    for stop_text in [
        "\nQuick Apply",
        "\nCalulator",
        "\nCalculator",
        "\nEBL  Self  Service Portal",
        "\nEBL Self Service Portal",
    ]:
        position = find_case_insensitive(section, stop_text)

        if position >= 0:
            end_positions.append(position)

    if end_positions:
        section = section[:min(end_positions)]

    return section.strip()


def slice_sme_loan_section(page_text, product_name):
    start = find_case_insensitive(page_text, product_name)

    if start < 0:
        return page_text

    boundary_products = SME_LOAN_PRODUCTS
    end_positions = []

    for boundary_product in boundary_products:
        if boundary_product == product_name:
            continue

        position = find_case_insensitive(page_text, boundary_product, start + len(product_name))

        if position >= 0:
            end_positions.append(position)

    end = min(end_positions) if end_positions else len(page_text)

    return page_text[start:end].strip()


def clean_loan_line(line):
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2022": "-",
        "\ufffd": "",
    }

    cleaned_line = line.strip()

    for old_value, new_value in replacements.items():
        cleaned_line = cleaned_line.replace(old_value, new_value)

    return " ".join(cleaned_line.split())


def should_stop_loan_feature_collection(line, stop_before_eligibility=True):
    lower_line = line.lower()

    for prefix in LOAN_SECTION_STOP_PREFIXES:
        if not stop_before_eligibility and prefix in [
            "eligibility",
            "who are eligible",
        ]:
            continue

        if lower_line.startswith(prefix):
            return True

    return False


def should_skip_loan_feature_line(line, product_name):
    lower_line = line.lower()

    if not line or line in ["|", "+", "-"]:
        return True

    if lower_line == product_name.lower():
        return True

    if lower_line.startswith("[") and lower_line.endswith("]"):
        return True

    return lower_line in LOAN_SECTION_SKIP_LINES


def normalize_loan_heading(line):
    return line.lower().strip().rstrip(":")


def find_loan_feature_start_index(lines):
    for index, line in enumerate(lines):
        if normalize_loan_heading(line) in LOAN_FEATURE_START_HEADINGS:
            return index

    return -1


def is_loan_field_label(line):
    return line.rstrip().endswith(":")


def should_merge_loan_continuation(current_line, next_line):
    lower_current = current_line.lower().strip()
    lower_next = next_line.lower().strip()

    return (
        current_line.endswith("/")
        or lower_current in ["minimum"]
        or lower_next.startswith(("per ", "of ", "for ", "from "))
    )


def build_loan_feature_bullets(
    section_text,
    product_name,
    max_bullets=30,
    stop_before_eligibility=True,
):
    raw_lines = section_text.splitlines()
    lines = [clean_loan_line(line) for line in raw_lines]
    lines = [line for line in lines if line]

    if stop_before_eligibility:
        feature_start_index = find_loan_feature_start_index(lines)

        if feature_start_index >= 0:
            lines = lines[feature_start_index + 1:]

    bullets = []
    index = 0

    while index < len(lines):
        line = lines[index]

        if should_stop_loan_feature_collection(line, stop_before_eligibility):
            break

        if should_skip_loan_feature_line(line, product_name):
            index += 1
            continue

        next_line = lines[index + 1] if index + 1 < len(lines) else ""

        if is_loan_field_label(line):
            values = []
            index += 1

            while index < len(lines):
                value_line = lines[index]

                if should_stop_loan_feature_collection(
                    value_line,
                    stop_before_eligibility,
                ):
                    break

                if should_skip_loan_feature_line(value_line, product_name):
                    index += 1
                    continue

                if is_loan_field_label(value_line):
                    break

                values.append(value_line)
                index += 1

                following_line = lines[index] if index < len(lines) else ""

                if (
                    not following_line
                    or is_loan_field_label(following_line)
                    or should_stop_loan_feature_collection(
                        following_line,
                        stop_before_eligibility,
                    )
                    or should_skip_loan_feature_line(following_line, product_name)
                ):
                    break

                if not should_merge_loan_continuation(values[-1], following_line):
                    break

            if values:
                bullets.append(f"{line.rstrip(':').strip()}: {' '.join(values)}")

            continue

        bullet_line = line
        index += 1

        while index < len(lines):
            following_line = lines[index]

            if (
                is_loan_field_label(following_line)
                or should_stop_loan_feature_collection(
                    following_line,
                    stop_before_eligibility,
                )
                or should_skip_loan_feature_line(following_line, product_name)
                or not should_merge_loan_continuation(bullet_line, following_line)
            ):
                break

            bullet_line = f"{bullet_line} {following_line}"
            index += 1

        bullets.append(bullet_line)

        if len(bullets) >= max_bullets:
            break

    return bullets


def get_loan_product_page_text(product):
    website_information = get_website_information_by_page_names([product["page_name"]])
    page_text = get_content_from_website_information(website_information)

    if page_text:
        return page_text

    try:
        page_text = get_text_from_website(product["url"])

        if page_text:
            save_website_text(
                page_name=product["page_name"],
                page_url=product["url"],
                page_text=page_text,
            )

    except Exception:
        return ""

    return page_text


def build_specific_loan_reply(product):
    page_text = get_loan_product_page_text(product)

    if product["category"] == "sme":
        section_text = slice_sme_loan_section(page_text, product["name"])
    else:
        section_text = slice_retail_loan_section(page_text, product["name"])

    bullets = build_loan_feature_bullets(
        section_text,
        product["name"],
        stop_before_eligibility=product["category"] != "sme",
    )

    if not bullets:
        return (
            f"{product['name']} details:\n\n"
            f"Link: {product['url']}"
        )

    bullet_text = "\n".join(f"- {bullet}" for bullet in bullets)

    return (
        f"{product['name']} features:\n\n"
        f"{bullet_text}\n\n"
        f"Link: {product['url']}"
    )


def build_loan_router_reply(user_message, intent, history):
    schedule_context = detect_loan_schedule_from_category_prompt(history)

    if schedule_context == "Retail":
        selected_category = find_loan_category("Retail", user_message)

        if selected_category:
            return build_retail_loan_names_for_category_reply(selected_category)

    category = detect_loan_category(user_message)

    if category == "retail":
        selected_category = find_loan_category("Retail", user_message)

        if selected_category:
            return build_retail_loan_names_for_category_reply(selected_category)

    product = detect_specific_loan_product(user_message)

    if product:
        return build_specific_loan_reply(product)

    retail_subcategory_reply = build_retail_loan_subcategory_reply(user_message)

    if retail_subcategory_reply:
        return retail_subcategory_reply

    if intent == "loan_information":
        if category:
            return build_loan_category_reply(category)

        return LOAN_CATEGORY_QUESTION

    if is_loan_category_follow_up(user_message, history):
        return build_loan_category_reply(category)

    return ""


def detect_account_segment(message):
    normalized_message = normalize_loan_lookup_text(message)
    words = normalized_message.split()

    if "sme" in words or "business" in words or "institutional" in words:
        return "sme"

    if "retail" in words:
        return "retail"

    if "personal" in words and ("account" in words or "deposit" in words):
        return "retail"

    return ""


def detect_account_category(message):
    normalized_message = normalize_loan_lookup_text(message)
    words = normalized_message.split()

    if (
        "islamic" in words
        or "shariah" in words
        or "sharia" in words
        or "mudarabah" in words
        or "wadiah" in words
    ):
        return "islamic_deposit"

    if "sme" in words or "business" in words or "institutional" in words:
        return "sme_deposit"

    if (
        "student" in words
        or "campus" in words
        or "junior" in words
        or "child" in words
        or "aspire" in words
        or "little" in words
    ):
        return "student_banking"

    if "personal" in words and "retail" in words:
        return "personal_retail"

    if (
        "nrb" in words
        or "foreign" in words
        or "currency" in words
        or "fcy" in words
        or "usd" in words
        or "rfcd" in words
        or "nfcd" in words
        or "expat" in words
        or "mariner" in words
        or "freelancer" in words
    ):
        return "nrb_foreign"

    if "dps" in words or "scheme" in words or "recurring" in words:
        return "dps"

    if "fixed" in words or "fd" in words or "fdr" in words or "term" in words:
        return "fixed"

    if "saving" in words or "savings" in words:
        return "savings"

    if "current" in words:
        return "current"

    return ""


def detect_specific_account_product(message):
    category = detect_account_category(message)

    for product in ACCOUNT_PRODUCT_RULES:
        for alias in product["aliases"]:
            if alias.lower().startswith("ebl ") and contains_loan_lookup_phrase(message, alias):
                return product

    for product in ACCOUNT_PRODUCT_RULES:
        if category and product["category"] != category:
            continue

        for alias in product["aliases"]:
            if contains_loan_lookup_phrase(message, alias):
                return product

    return None


def last_assistant_asked_for_account_category(history):
    for item in reversed(history):
        if item.get("role") != "assistant":
            continue

        content = item.get("content", "").lower()

        return (
            "retail account or an sme account" in content
            or "retail account or sme account" in content
            or "retail account, an sme account or an islamic account" in content
            or "do you want to open a retail account" in content
            or "which account type do you want to open" in content
        )

    return False


def detect_account_schedule_from_category_prompt(history):
    for item in reversed(history):
        if item.get("role") != "assistant":
            continue

        content = item.get("content", "").lower()

        if "which retail account category" in content:
            return "Retail"

        if "which sme account category" in content:
            return "SME"

        return ""

    return ""


def is_account_category_follow_up(message, history):
    return bool(
        (detect_account_segment(message) or detect_account_category(message))
        and last_assistant_asked_for_account_category(history)
    )


def is_account_feature_follow_up(message):
    normalized_message = normalize_loan_lookup_text(message)

    return normalized_message in [
        "feature",
        "features",
        "benefit",
        "benefits",
        "show features",
        "show benefits",
        "tell me features",
        "tell me benefits",
        "tell me more",
        "details",
        "more details",
    ]


def detect_account_product_from_history(history):
    for item in reversed(history):
        if item.get("role") != "assistant":
            continue

        content = item.get("content", "").lower()

        for product in ACCOUNT_PRODUCT_RULES:
            if product["name"].lower() in content:
                return product

    return None


def build_link_list_reply(title, links):
    link_lines = "\n".join(
        f"- {label}: {url}"
        for label, url in links
    )

    return f"{title}\n\n{link_lines}"


def build_retail_banking_overview_reply():
    return build_link_list_reply(
        "EBL Retail Banking options include:",
        RETAIL_BANKING_LINKS,
    )


def build_islamic_banking_overview_reply():
    return build_link_list_reply(
        "EBL Islamic Banking information and product links:",
        ISLAMIC_BANKING_LINKS,
    )


def build_account_segment_reply(segment):
    products = ACCOUNT_SEGMENT_PRODUCTS.get(segment, [])

    if not products:
        return ""

    product_lines = "\n".join(f"- {product}" for product in products)
    segment_label = ACCOUNT_SEGMENT_LABELS.get(segment, "Account")

    return (
        f"EBL {segment_label} products include:\n\n"
        f"{product_lines}\n\n"
        "Please tell me the specific account product name if you want its features and link."
    )


def build_account_schedule_category_reply(segment):
    schedule = ACCOUNT_SEGMENT_SCHEDULES.get(segment, "")

    if not schedule:
        return ""

    categories = get_account_categories(schedule)

    if not categories:
        return ""

    category_lines = "\n".join(f"- {category}" for category in categories)

    return (
        f"Which {schedule} account category do you want to know or open?\n\n"
        f"{category_lines}"
    )


def build_account_names_for_category_reply(schedule, category):
    account_names = get_account_names(schedule, category)

    if not account_names:
        return ""

    account_lines = "\n".join(f"- {account_name}" for account_name in account_names)

    return (
        f"EBL {schedule} {category} accounts include:\n\n"
        f"{account_lines}\n\n"
        "Please tell me the specific account name if you want details or opening information."
    )


def build_account_category_reply(category):
    products = ACCOUNT_CATEGORY_PRODUCTS.get(category, [])

    if not products:
        return ""

    product_lines = "\n".join(f"- {product}" for product in products)
    category_label = ACCOUNT_CATEGORY_LABELS.get(category, "Account")

    return (
        f"EBL {category_label} options include:\n\n"
        f"{product_lines}\n\n"
        f"Please tell me the specific {category_label} product name if you want its features and link."
    )


def slice_retail_account_section(page_text, product_name):
    marker = f"BACK\n{product_name}\n"
    start = find_case_insensitive(page_text, marker)

    if start >= 0:
        section = page_text[start + len("BACK\n"):]
    else:
        title_marker = f"\n{product_name}\n"
        content_start = find_case_insensitive(page_text, "\nSearch\n")

        if content_start >= 0:
            start = find_case_insensitive(
                page_text,
                title_marker,
                content_start,
            )
        else:
            start = -1

        if start < 0:
            start = page_text.lower().rfind(title_marker.lower())

        if start < 0:
            start = find_case_insensitive(page_text, product_name)

        if start < 0:
            return page_text

        section = page_text[start:].strip()

    return trim_account_section_end(section)


def slice_sme_account_section(page_text, product_name):
    start = find_case_insensitive(page_text, product_name)

    if start < 0:
        return page_text

    boundary_products = ACCOUNT_CATEGORY_PRODUCTS["sme_deposit"]
    end_positions = []

    for boundary_product in boundary_products:
        if boundary_product == product_name:
            continue

        position = find_case_insensitive(page_text, boundary_product, start + len(product_name))

        if position >= 0:
            end_positions.append(position)

    end = min(end_positions) if end_positions else len(page_text)

    return page_text[start:end].strip()


def trim_account_section_end(section_text):
    end_positions = []

    for stop_text in [
        "\nRequired Documents",
        "\nDocuments Required",
        "\nAccount Opening Documents",
        "\nFees",
        "\nQuick Apply",
        "\nApply now",
        "\nEBL  Self  Service Portal",
        "\nEBL Self Service Portal",
    ]:
        position = find_case_insensitive(section_text, stop_text)

        if position >= 0:
            end_positions.append(position)

    if end_positions:
        return section_text[:min(end_positions)].strip()

    return section_text.strip()


def should_stop_account_feature_collection(line):
    lower_line = line.lower()

    for prefix in ACCOUNT_SECTION_STOP_PREFIXES:
        if lower_line.startswith(prefix):
            return True

    return False


def should_skip_account_feature_line(line, product_name):
    lower_line = line.lower()

    if not line or line in ["|", "+", "-"]:
        return True

    if lower_line == product_name.lower():
        return True

    return lower_line in ACCOUNT_SECTION_SKIP_LINES


def build_account_feature_bullets(section_text, product_name, max_bullets=15):
    raw_lines = section_text.splitlines()
    lines = [clean_loan_line(line) for line in raw_lines]
    lines = [line for line in lines if line]

    feature_headings = [
        "features",
        "key features",
        "key features include",
        "features and benefits",
        "benefits and features",
    ]

    for index, line in enumerate(lines):
        normalized_line = line.lower().rstrip(":")

        if normalized_line in feature_headings:
            lines = lines[index + 1:]
            break

    bullets = []
    index = 0

    while index < len(lines):
        line = lines[index]
        line = line.replace(" : Please see", "").replace(": Please see", "")

        if should_stop_account_feature_collection(line):
            break

        if should_skip_account_feature_line(line, product_name):
            index += 1
            continue

        next_line = lines[index + 1] if index + 1 < len(lines) else ""

        if line.endswith(":") and next_line and not should_stop_account_feature_collection(next_line):
            bullets.append(f"{line.rstrip(':')}: {next_line}")
            index += 2
        else:
            bullets.append(line)
            index += 1

        if len(bullets) >= max_bullets:
            break

    return bullets


def normalize_account_detail_lines(section_text):
    return [
        clean_loan_line(line)
        for line in section_text.splitlines()
        if clean_loan_line(line)
    ]


def is_numeric_table_value(value):
    cleaned_value = value.replace(",", "").replace(".", "").strip()

    return cleaned_value.isdigit()


def format_detail_table(headers, rows):
    if not headers or not rows:
        return ""

    column_count = max([len(headers)] + [len(row) for row in rows])
    padded_headers = headers + [""] * (column_count - len(headers))
    padded_rows = [
        row + [""] * (column_count - len(row))
        for row in rows
    ]
    safe_headers = [header.replace("|", "/") for header in padded_headers]
    safe_rows = [
        [cell.replace("|", "/") for cell in row]
        for row in padded_rows
    ]

    header_line = "| " + " | ".join(safe_headers) + " |"
    separator_line = "| " + " | ".join("---" for _ in safe_headers) + " |"
    row_lines = [
        "| " + " | ".join(row) + " |"
        for row in safe_rows
    ]

    return "\n".join([header_line, separator_line] + row_lines)


def collect_numeric_rows(lines, start_index, width, max_rows=20):
    rows = []
    index = start_index

    while index + width <= len(lines) and len(rows) < max_rows:
        row = lines[index:index + width]

        if not all(is_numeric_table_value(cell) for cell in row):
            break

        rows.append(row)
        index += width

    return rows


def remove_duplicate_detail_bullets(bullets, detail_lines):
    detail_texts = {
        " ".join(line.lower().split())
        for line in detail_lines
        if line
    }

    filtered_bullets = []

    for bullet in bullets:
        normalized_bullet = " ".join(bullet.lower().split())

        if normalized_bullet in detail_texts:
            continue

        if "minimum opening amount" in normalized_bullet and "tenure" in normalized_bullet:
            continue

        filtered_bullets.append(bullet)

    return filtered_bullets


def extract_fixed_deposit_amount_and_tenure(section_text):
    amount_lines = []
    tenure_lines = []
    seen_amount_lines = set()
    seen_tenure_lines = set()

    for line in normalize_account_detail_lines(section_text):
        split_match = re.search(r"\s+and\s+tenure\s+is\s+", line, flags=re.IGNORECASE)

        if split_match and "minimum opening amount" in line.lower():
            amount_line = line[:split_match.start()].strip()
            tenure_line = f"Tenure is {line[split_match.end():].strip()}"
            normalized_amount = " ".join(amount_line.lower().split())
            normalized_tenure = " ".join(tenure_line.lower().split())

            if normalized_amount not in seen_amount_lines:
                amount_lines.append(amount_line)
                seen_amount_lines.add(normalized_amount)

            if normalized_tenure not in seen_tenure_lines:
                tenure_lines.append(tenure_line)
                seen_tenure_lines.add(normalized_tenure)

            continue

        lower_line = line.lower()

        if lower_line.startswith("minimum opening amount"):
            normalized_line = " ".join(lower_line.split())

            if normalized_line not in seen_amount_lines:
                amount_lines.append(line)
                seen_amount_lines.add(normalized_line)

        elif lower_line.startswith("tenure is"):
            normalized_line = " ".join(lower_line.split())

            if normalized_line not in seen_tenure_lines:
                tenure_lines.append(line)
                seen_tenure_lines.add(normalized_line)

    return amount_lines, tenure_lines


def build_fixed_deposit_reply(product, section_text):
    amount_lines, tenure_lines = extract_fixed_deposit_amount_and_tenure(section_text)
    features = build_account_feature_bullets(section_text, product["name"], max_bullets=8)
    features = remove_duplicate_detail_bullets(
        features,
        amount_lines + tenure_lines,
    )

    reply_parts = [f"{product['name']} details:"]

    if amount_lines:
        reply_parts.append(
            "FD Amount:\n" + "\n".join(f"- {line}" for line in amount_lines)
        )

    if tenure_lines:
        reply_parts.append(
            "Tenure:\n" + "\n".join(f"- {line}" for line in tenure_lines)
        )

    if features:
        reply_parts.append(
            "Key Features:\n" + "\n".join(f"- {feature}" for feature in features)
        )

    reply_parts.append(f"Link: {product['url']}")

    return "\n\n".join(reply_parts)


def build_confidence_dps_table(product_name, lines):
    try:
        installment_index = lines.index("Installment")
        maturity_amount_index = lines.index("Maturity Amount", installment_index)
    except ValueError:
        return ""

    years = []
    index = maturity_amount_index + 1

    while index + 1 < len(lines) and lines[index].lower() == "maturity after":
        years.append(lines[index + 1])
        index += 2

    if not years:
        return ""

    rows = collect_numeric_rows(lines, index, len(years) + 1)

    if not rows:
        return ""

    headers = ["Product Name", product_name] + [""] * (len(years) - 1)
    table_rows = [
        ["Installment"] + [f"Maturity after {year}" for year in years],
    ] + rows

    return format_detail_table(headers, table_rows)


def build_kotipoti_dps_table(lines):
    try:
        initial_index = lines.index("Initial Amount")
        maturity_index = lines.index("Maturity Amount", initial_index)
        year_index = lines.index("Year", maturity_index)
        installment_index = lines.index("Installment", year_index)
    except ValueError:
        return ""

    initial_amounts = lines[initial_index + 1:maturity_index]
    data_start = installment_index + 1
    first_row_width = len(initial_amounts) + 2

    if data_start + first_row_width > len(lines):
        return ""

    first_row = lines[data_start:data_start + first_row_width]

    if not all(is_numeric_table_value(cell) for cell in first_row):
        return ""

    maturity_amount = first_row[-1]
    rows = [first_row]
    index = data_start + first_row_width
    later_row_width = len(initial_amounts) + 1

    while index + later_row_width <= len(lines):
        row = lines[index:index + later_row_width]

        if not all(is_numeric_table_value(cell) for cell in row):
            break

        rows.append(row + [maturity_amount])
        index += later_row_width

    if not initial_amounts or not rows:
        return ""

    headers = ["Product Name", "EBL Kotipoti"] + [""] * (len(initial_amounts) - 1)
    table_rows = [
        ["Initial Amount"] + initial_amounts,
        ["Maturity Amount", maturity_amount] + [""] * (len(initial_amounts) - 1),
        ["Year"] + [
            f"Installment ({amount})"
            for amount in initial_amounts
        ],
    ]
    table_rows.extend(row[:-1] for row in rows)

    return format_detail_table(headers, table_rows)


def build_multiplier_dps_table(lines):
    try:
        initial_index = lines.index("Initial Amount")
        tenure_index = lines.index("Tenure in Year", initial_index)
        maturity_index = lines.index("Maturity Amount", tenure_index)
        monthly_index = lines.index("Monthly Installment", maturity_index)
    except ValueError:
        return ""

    initial_amount = lines[initial_index + 1] if initial_index + 1 < len(lines) else ""
    tenures = lines[tenure_index + 1:maturity_index]
    maturity_amounts = lines[maturity_index + 1:monthly_index]
    monthly_installments = []

    for line in lines[monthly_index + 1:]:
        if not is_numeric_table_value(line):
            break

        monthly_installments.append(line)

    row_count = min(len(tenures), len(maturity_amounts), len(monthly_installments))

    if not initial_amount or row_count == 0:
        return ""

    headers = ["Product Name", "EBL Multiplier"] + [""] * (row_count - 1)
    table_rows = [
        ["Initial Amount", initial_amount] + [""] * (row_count - 1),
        ["Tenure in Year"] + tenures[:row_count],
        ["Maturity Amount"] + maturity_amounts[:row_count],
        ["Monthly Installment"] + monthly_installments[:row_count],
    ]

    return format_detail_table(headers, table_rows)


def build_millionaire_dps_table(lines):
    try:
        year_index = lines.index("Year")
        initial_index = lines.index("Initial Amount", year_index)
        maturity_index = lines.index("Maturity Amount", initial_index)
    except ValueError:
        return ""

    initial_amounts = []
    index = maturity_index + 1

    while index < len(lines):
        cleaned_value = lines[index].replace(",", "").strip()

        if cleaned_value.isdigit() and int(cleaned_value) <= 30 and initial_amounts:
            break

        initial_amounts.append(lines[index])
        index += 1

    first_row_width = len(initial_amounts) + 2

    if index + first_row_width > len(lines):
        return ""

    first_row = lines[index:index + first_row_width]

    if not all(is_numeric_table_value(cell) for cell in first_row):
        return ""

    maturity_amount = first_row[-1]
    rows = [first_row]
    index += first_row_width
    later_row_width = len(initial_amounts) + 1

    while index + later_row_width <= len(lines):
        row = lines[index:index + later_row_width]

        if not all(is_numeric_table_value(cell) for cell in row):
            break

        rows.append(row + [maturity_amount])
        index += later_row_width

    if not initial_amounts or not rows:
        return ""

    headers = ["Product Name", "EBL Millionaire"] + [""] * (len(initial_amounts) - 1)
    table_rows = [
        ["Initial Amount"] + initial_amounts,
        ["Maturity Amount", maturity_amount] + [""] * (len(initial_amounts) - 1),
        ["Year"] + [
            f"Installment ({amount})"
            for amount in initial_amounts
        ],
    ]
    table_rows.extend(row[:-1] for row in rows)

    return format_detail_table(headers, table_rows)


def build_dps_installment_table(product_name, section_text):
    lines = normalize_account_detail_lines(section_text)
    product_name_lower = product_name.lower()

    if product_name_lower in ["ebl confidence", "ebl women confidence"]:
        return build_confidence_dps_table(product_name, lines)

    if product_name_lower == "ebl kotipoti scheme":
        return build_kotipoti_dps_table(lines)

    if product_name_lower == "ebl multiplier":
        return build_multiplier_dps_table(lines)

    if product_name_lower == "ebl millionaire scheme":
        return build_millionaire_dps_table(lines)

    return ""


def build_dps_reply(product, section_text):
    features = build_account_feature_bullets(section_text, product["name"], max_bullets=6)
    table = build_dps_installment_table(product["name"], section_text)

    reply_parts = [f"{product['name']} details:"]

    if features:
        reply_parts.append(
            "Key Features:\n" + "\n".join(f"- {feature}" for feature in features)
        )

    if table:
        reply_parts.append(f"Installment Amount Table:\n{table}")
    else:
        reply_parts.append(
            "Installment Amount Table: Not available in the extracted EBL website text for this product."
        )

    reply_parts.append(f"Link: {product['url']}")

    return "\n\n".join(reply_parts)


def get_account_product_page_text(product):
    website_information = get_website_information_by_page_names([product["page_name"]])
    page_text = get_content_from_website_information(website_information)

    if page_text:
        return page_text

    try:
        page_text = get_text_from_website(product["url"])

        if page_text:
            save_website_text(
                page_name=product["page_name"],
                page_url=product["url"],
                page_text=page_text,
            )

    except Exception:
        return ""

    return page_text


def build_specific_account_reply(product):
    page_text = get_account_product_page_text(product)

    if product["category"] == "sme_deposit":
        section_text = slice_sme_account_section(page_text, product["name"])
    else:
        section_text = slice_retail_account_section(page_text, product["name"])

    if product["category"] == "fixed":
        return build_fixed_deposit_reply(product, section_text)

    if product["category"] == "dps":
        return build_dps_reply(product, section_text)

    bullets = build_account_feature_bullets(section_text, product["name"])

    if not bullets:
        return (
            f"{product['name']} details:\n\n"
            f"Link: {product['url']}"
        )

    bullet_text = "\n".join(f"- {bullet}" for bullet in bullets)

    return (
        f"{product['name']} features:\n\n"
        f"{bullet_text}\n\n"
        f"Link: {product['url']}"
    )


def build_specific_account_documents_reply(product, user_message):
    page_text = get_account_product_page_text(product)

    if not page_text:
        return ""

    return build_required_documents_reply(
        user_message=user_message,
        website_info=page_text,
        product_name=product["name"],
        force=True,
    )


def build_account_router_reply(user_message, intent, history, search_query=""):
    schedule_context = detect_account_schedule_from_category_prompt(history)

    if schedule_context:
        selected_category = find_account_category(schedule_context, user_message)

        if selected_category:
            return build_account_names_for_category_reply(
                schedule_context,
                selected_category,
            )

    product = detect_specific_account_product(user_message)

    if product:
        if is_document_question(user_message) or is_document_question(search_query):
            return build_specific_account_documents_reply(product, user_message)

        return build_specific_account_reply(product)

    if (
        is_document_question(user_message)
        or is_document_question(search_query)
        or has_document_word(user_message, include_need=False)
        or has_document_word(search_query, include_need=False)
    ):
        product = detect_account_product_from_history(history)

        if product:
            document_reply = build_specific_account_documents_reply(product, user_message)

            if document_reply:
                return document_reply

    if is_account_feature_follow_up(user_message):
        product = detect_account_product_from_history(history)

        if product:
            return build_specific_account_reply(product)

    segment = detect_account_segment(user_message)
    category = detect_account_category(user_message)
    is_broad_account_question = (
        is_broad_account_opening_question(user_message)
        or is_broad_account_opening_question(search_query)
    )
    account_context_words = [
        "account",
        "accounts",
        "deposit",
        "deposits",
        "dps",
        "fd",
        "fdr",
        "saving",
        "savings",
    ]
    has_account_context = contains_any_word(
        normalize_loan_lookup_text(user_message),
        account_context_words,
    )

    if (
        intent in ["account_information", "deposit_information", "student_banking"]
        or is_broad_account_question
        or has_account_context
    ):
        if segment:
            schedule = ACCOUNT_SEGMENT_SCHEDULES.get(segment, "")
            selected_category = (
                find_account_category(schedule, user_message)
                if schedule
                else ""
            )

            if selected_category:
                return build_account_names_for_category_reply(
                    schedule,
                    selected_category,
                )

            category_reply = build_account_schedule_category_reply(segment)

            if category_reply:
                return category_reply

            return build_account_segment_reply(segment)

        if category:
            return build_account_category_reply(category)

        if is_broad_account_question:
            return ACCOUNT_CATEGORY_QUESTION

    if is_account_category_follow_up(user_message, history):
        if segment:
            category_reply = build_account_schedule_category_reply(segment)

            if category_reply:
                return category_reply

            return build_account_segment_reply(segment)

        return build_account_category_reply(category)

    return ""


def detect_card_category(message):
    normalized_message = normalize_loan_lookup_text(message)
    words = normalized_message.split()

    if "islamic" in words or "shariah" in words or "sharia" in words:
        return "islamic"

    if "credit" in words:
        return "credit"

    if "debit" in words:
        return "debit"

    if "prepaid" in words or ("pre" in words and "paid" in words):
        return "prepaid"

    return ""


def build_card_aliases(product_name):
    aliases = [
        product_name,
        product_name.replace("EBL ", "", 1),
    ]

    if "Women's" in product_name:
        aliases.append(product_name.replace("Women's", "Womens"))

    if "UnionPay" in product_name:
        aliases.append(product_name.replace("UnionPay", "Unionpay"))

    if "Mastercard" in product_name:
        aliases.append(product_name.replace("Mastercard", "MasterCard"))

    return list(dict.fromkeys(aliases))


def detect_specific_card_product(message):
    category = detect_card_category(message)

    for product in CARD_PRODUCT_RULES:
        if category and product["category"] != category:
            continue

        for alias in build_card_aliases(product["name"]):
            if contains_loan_lookup_phrase(message, alias):
                return product

    if category:
        return None

    for product in CARD_PRODUCT_RULES:
        for alias in build_card_aliases(product["name"]):
            if contains_loan_lookup_phrase(message, alias):
                return product

    return None


def last_assistant_asked_for_card_category(history):
    for item in reversed(history):
        if item.get("role") != "assistant":
            continue

        content = item.get("content", "").lower()

        return "debit, credit, prepaid or islamic card" in content

    return False


def is_card_category_follow_up(message, history):
    return bool(
        detect_card_category(message)
        and last_assistant_asked_for_card_category(history)
    )


def build_card_category_reply(category):
    products = CARD_CATEGORY_PRODUCTS.get(category, [])

    if not products:
        return ""

    product_lines = "\n".join(f"- {product}" for product in products)
    category_label = CARD_CATEGORY_LABELS.get(category, "Card")

    reply = (
        f"EBL {category_label} options include:\n\n"
        f"{product_lines}\n\n"
        f"Please tell me the specific {category_label} name if you want its features and link."
    )

    if category == "credit":
        reply += "\nFor credit cards, I can also share the Apply Now link for the selected card."

    return reply


def get_card_product_page_text(product):
    website_information = get_website_information_by_page_urls([product["url"]])
    page_text = get_content_from_website_information(website_information)

    if page_text:
        return page_text

    website_information = search_website_information(product["name"], limit=1)
    page_text = get_content_from_website_information(website_information)

    if page_text:
        return page_text

    try:
        page_text = get_text_from_website(product["url"])

        if page_text:
            save_website_text(
                page_name=f"EBL Detail Page - {product['name']}",
                page_url=product["url"],
                page_text=page_text,
            )

    except Exception:
        return ""

    return page_text


def slice_card_section(page_text, product_name):
    marker = f"BACK\n{product_name}\n"
    start = find_case_insensitive(page_text, marker)

    if start >= 0:
        section = page_text[start + len("BACK\n"):]
    else:
        title_marker = f"\n{product_name}\n"
        start = find_case_insensitive(page_text, title_marker)

        if start < 0:
            start = find_case_insensitive(page_text, product_name)

        if start < 0:
            back_marker = "\nback\n"
            start = page_text.lower().rfind(back_marker)

            if start < 0:
                return page_text

            section = page_text[start + len(back_marker):].strip()
        else:
            section = page_text[start:].strip()


    end_positions = []

    for stop_text in [
        "\n100 Gulshan Avenue",
        "\nEBL Query/Complaint",
        "\nBank Note Security Features",
        "\nContact Us",
        "\nApply Now",
    ]:
        position = find_case_insensitive(section, stop_text)

        if position >= 0:
            end_positions.append(position)

    if end_positions:
        section = section[:min(end_positions)]

    return section.strip()


def should_stop_card_feature_collection(line):
    lower_line = line.lower()

    stop_prefixes = [
        "100 gulshan avenue",
        "dhaka-",
        "bangladesh",
        "ebl query/complaint",
        "bank note security features",
        "contact us",
    ]

    return any(lower_line.startswith(prefix) for prefix in stop_prefixes)


def should_skip_card_feature_line(line, product_name):
    lower_line = line.lower()

    if not line or line in ["|", "+", "-"]:
        return True

    if lower_line == product_name.lower():
        return True

    return lower_line in [
        "back",
        "apply now",
        "read more",
        "details",
        "features",
        "features:",
        "key features",
        "key features:",
        "exclusive offers",
        "value added benefits",
    ]


def summarize_card_feature_line(line):
    line = clean_loan_line(line)

    if not line:
        return ""

    if ":" in line:
        line = line.split(":", 1)[0].strip()

    if " please visit" in line.lower():
        return ""

    if line.lower().startswith("for airport"):
        return ""

    return line.strip(" -")


def summarize_card_feature_detail(feature_line, detail_line):
    feature_text = normalize_loan_lookup_text(feature_line)
    detail_line = clean_loan_line(detail_line).lstrip(": ")

    if "zero issuance" in feature_text:
        return "Zero issuance fee for eligible cardholders."

    if "zero renewal" in feature_text:
        return "Renewal fee can be waived when the required yearly transactions are completed."

    if "contactless" in feature_text:
        return "Tap-to-pay contactless transactions are supported."

    if "revolving" in feature_text:
        return "Flexible revolving credit facility is available."

    if "onetime" in feature_text or "lifetime free" in feature_text:
        return "Annual fee benefit applies when the required yearly transactions are completed."

    if "global currency" in feature_text:
        return "Local and foreign currency usage is supported as per card terms."

    if "skylounge" in feature_text or ("sky" in feature_text and "lounge" in feature_text):
        return "Complimentary EBL SKYLOUNGE access as per card benefits."

    if "global lounge" in feature_text or "vip airport lounge" in feature_text:
        return "Global lounge access is available as per schedule of charges."

    if "priority pass" in feature_text:
        return "Priority Pass lounge access is available; charges may apply."

    if "meet" in feature_text and "greet" in feature_text:
        return "Airport Meet & Greet fast-track service is available with advance booking."

    if "risk assurance" in feature_text or "insurance" in feature_text:
        return "Risk assurance coverage applies as per card terms."

    if "interest free" in feature_text:
        return "Up to 45 days interest-free period on eligible transactions."

    if "cash advance" in feature_text:
        return "Cash advance facility is available through eligible channels."

    if "auto debit" in feature_text:
        return "Automatic payment from an EBL account can be set up."

    if "discount" in feature_text:
        return "Discounts are available at selected EBL partner merchants."

    if "installment" in feature_text or "emi" in feature_text:
        return "Eligible transactions can be converted into installment plans."

    if "zip" in feature_text and "easycredit" in feature_text:
        return "ZIP and EasyCredit installment facilities are available."

    if "zip" in feature_text:
        return "Interest-free installment plans are available at partner merchant outlets."

    if "easycredit" in feature_text:
        return "Eligible card limit can be used for transfer or pay order through EMI."

    if "supplementary" in feature_text:
        return "Supplementary card facility is available as per card terms."

    if "payment" in feature_text:
        return "Flexible payment options are available through EBL channels."

    if "contact center" in feature_text or "contact centre" in feature_text:
        return "24-hour card support is available through EBL Contact Center."

    if not detail_line:
        return ""

    lower_detail = detail_line.lower()

    if lower_detail.startswith(("http", "www.")):
        return ""

    if lower_detail.startswith(("for airport", "please visit")):
        return ""

    if should_stop_card_feature_collection(detail_line):
        return ""

    first_sentence = re.split(r"(?<=[.!?])\s+", detail_line, maxsplit=1)[0].strip()
    first_sentence = first_sentence.rstrip(".")

    if len(first_sentence) > 130:
        words = first_sentence.split()
        trimmed_words = []

        for word in words:
            candidate = " ".join(trimmed_words + [word])

            if len(candidate) > 120:
                break

            trimmed_words.append(word)

        first_sentence = " ".join(trimmed_words).rstrip(",;:")

    if not first_sentence:
        return ""

    return f"{first_sentence}."


def is_card_feature_detail_sentence(line):
    lower_line = f" {line.lower()} "

    if line.endswith((".", "!", "?", "।")):
        return True

    detail_phrases = [
        " any ",
        " are ",
        " can ",
        " comes ",
        " eligible ",
        " entitled ",
        " gives ",
        " has ",
        " have ",
        " need ",
        " needs ",
        " offers ",
        " paid ",
        " there ",
        " where ",
        " whenever ",
        " will ",
        " you ",
        " your ",
    ]

    return len(line.split()) > 8 and any(phrase in lower_line for phrase in detail_phrases)


def is_main_card_feature_line(line):
    if not line:
        return False

    lower_line = line.lower()

    if lower_line.startswith(("http", "www.")):
        return False

    if len(line) > 95:
        return False

    if is_card_feature_detail_sentence(line):
        return False

    feature_keywords = {
        "access",
        "airport",
        "assurance",
        "auto",
        "bonus",
        "cashback",
        "cash",
        "complimentary",
        "currency",
        "discount",
        "easycredit",
        "emi",
        "fee",
        "free",
        "global",
        "insurance",
        "issuance",
        "lounge",
        "meet",
        "offer",
        "pass",
        "points",
        "program",
        "renewal",
        "reward",
        "revolving",
        "risk",
        "sky",
        "skylounge",
        "supplementary",
        "zip",
        "zero",
    }

    line_words = set(normalize_loan_lookup_text(line).split())

    if line_words & feature_keywords:
        return True

    return len(line.split()) <= 6 and line[:1].isupper()


def build_card_feature_bullets(section_text, product_name, max_bullets=6):
    raw_lines = section_text.splitlines()
    lines = [clean_loan_line(line) for line in raw_lines]
    lines = [line for line in lines if line]

    bullets = []
    seen_bullets = set()
    index = 0

    while index < len(lines):
        line = lines[index]

        if should_stop_card_feature_collection(line):
            break

        if should_skip_card_feature_line(line, product_name):
            index += 1
            continue

        feature_line = summarize_card_feature_line(line)

        if not is_main_card_feature_line(feature_line):
            index += 1
            continue

        normalized_feature = normalize_loan_lookup_text(feature_line)

        if normalized_feature in seen_bullets:
            index += 1
            continue

        detail_line = ""
        next_index = index + 1

        while next_index < len(lines):
            candidate_line = lines[next_index]

            if should_stop_card_feature_collection(candidate_line):
                break

            if should_skip_card_feature_line(candidate_line, product_name):
                next_index += 1
                continue

            candidate_feature = summarize_card_feature_line(candidate_line)

            if is_main_card_feature_line(candidate_feature):
                break

            detail_line = candidate_line
            break

        feature_detail = summarize_card_feature_detail(feature_line, detail_line)
        bullet = (
            f"{feature_line}: {feature_detail}"
            if feature_detail
            else feature_line
        )

        seen_bullets.add(normalized_feature)
        bullets.append(bullet)

        if len(bullets) >= max_bullets:
            break

        index += 1

    return bullets


def build_specific_card_reply(product):
    page_text = get_card_product_page_text(product)
    section_text = slice_card_section(page_text, product["name"])
    bullets = build_card_feature_bullets(section_text, product["name"])

    if bullets:
        bullet_text = "\n".join(f"- {bullet}" for bullet in bullets)
        reply = (
            f"{product['name']} features:\n\n"
            f"{bullet_text}\n\n"
            f"Details link: {product['url']}"
        )
    else:
        reply = (
            f"{product['name']} details:\n\n"
            f"Details link: {product['url']}"
        )

    if product["category"] == "credit":
        reply += f"\nApply now: {CARD_APPLY_NOW_LINK}"

    return reply


def build_card_router_reply(user_message, intent, history):
    product = detect_specific_card_product(user_message)

    if product:
        return build_specific_card_reply(product)

    category = detect_card_category(user_message)

    if intent == "card_information":
        if category:
            return build_card_category_reply(category)

        return CARD_CATEGORY_QUESTION

    if is_card_category_follow_up(user_message, history):
        return build_card_category_reply(category)

    return ""


def is_specific_card_product_information_request(message):
    return bool(
        detect_specific_card_product(message)
        and not is_fee_or_charge_question(message)
        and not has_rate_word(message)
    )


DISCOVERY_SOURCES = [
    {
        "page_url": "https://www.ebl.com.bd/retail/EBL-Cards",
        "allowed_paths": [
            "/retail/eblcard/",
            "/islamic/eblcard/",
            "/ebl-virtual-prepaid-card",
        ],
    },
    {
        "page_url": "https://www.ebl.com.bd/retail/retail-loan",
        "allowed_paths": [
            "/retail-loan/",
        ],
    },
    {
        "page_url": "https://www.ebl.com.bd/sme/sme-loans",
        "allowed_paths": [
            "/sme-loan/",
            "/sme/sme-loan/",
        ],
    },
    {
        "page_url": "https://www.ebl.com.bd/retail/retail-deposit",
        "allowed_paths": [
            "/retail-deposit/",
        ],
    },
    {
        "page_url": "https://www.ebl.com.bd/retail/EBL-Student-Banking",
        "allowed_paths": [
            "/student-banking/",
            "/islamic/deposit/",
        ],
    },
    {
        "page_url": "https://www.ebl.com.bd/islamicbanking",
        "allowed_paths": [
            "/islamic/",
            "/islamicbanking",
            "/islamic-retail-finance/",
        ],
    },
    {
        "page_url": "https://www.ebl.com.bd/retail/ebl-insta-banking",
        "allowed_paths": [
            "/retail/",
            "/retail-digital/",
            "/retail-ecommerce/",
            "/priority/",
            "/powerbanking",
            "/ebl-super-saver",
            "/agentbanking",
        ],
    },
]

MAX_DISCOVERED_PAGES = 180


def is_allowed_discovered_url(url, allowed_paths):
    parsed_url = urlparse(url)
    path = parsed_url.path.lower()

    if not parsed_url.netloc.endswith("ebl.com.bd"):
        return False

    for allowed_path in allowed_paths:
        if path.startswith(allowed_path.lower()):
            return True

    return False


def build_discovered_page_name(link):
    link_text = link.get("text", "").strip()

    if link_text and link_text.lower() not in ["readmore", "read more", "apply now"]:
        return f"EBL Detail Page - {link_text}"

    path = urlparse(link["url"]).path.strip("/")
    slug = path.split("/")[-1]
    title = slug.replace("-", " ").replace("_", " ").strip()

    if not title:
        title = "Product Detail"

    return f"EBL Detail Page - {title.title()}"


def discover_website_pages():
    discovered_pages = []
    seen_urls = set(page["page_url"] for page in WEBSITE_PAGES)

    for source in DISCOVERY_SOURCES:
        links = get_internal_links_from_website(source["page_url"])

        for link in links:
            page_url = link["url"]

            if page_url in seen_urls:
                continue

            if not is_allowed_discovered_url(page_url, source["allowed_paths"]):
                continue

            seen_urls.add(page_url)
            discovered_pages.append({
                "page_name": build_discovered_page_name(link),
                "page_url": page_url,
            })

            if len(discovered_pages) >= MAX_DISCOVERED_PAGES:
                return discovered_pages

    return discovered_pages


WEBSITE_PAGES = [
    {
        "page_name": "EBL Home Page",
        "page_url": "https://www.ebl.com.bd/",
    },
    {
        "page_name": "EBL Cards Page",
        "page_url": "https://www.ebl.com.bd/retail/EBL-Cards",
    },
    {
        "page_name": "EBL Retail Loan Page",
        "page_url": "https://www.ebl.com.bd/retail/retail-loan",
    },
    {
        "page_name": "EBL SME Loan Page",
        "page_url": "https://www.ebl.com.bd/sme/sme-loans",
    },
    {
        "page_name": "EBL Retail Deposits Page",
        "page_url": "https://www.ebl.com.bd/retail/retail-deposit",
    },
    {
        "page_name": "EBL Power Savings Page",
        "page_url": "https://www.ebl.com.bd/retail-deposit/EBL-Power-Savings",
    },
    {
        "page_name": "EBL Premium Savings Page",
        "page_url": "https://www.ebl.com.bd/retail-deposit/EBL-Premium-Savings",
    },
    {
        "page_name": "EBL 50+ Savings Page",
        "page_url": "https://www.ebl.com.bd/retail-deposit/EBL-50Plus-Savings",
    },
    {
        "page_name": "EBL Max Saver Page",
        "page_url": "https://www.ebl.com.bd/retail-deposit/EBL-Max-Saver",
    },
    {
        "page_name": "EBL Current Account Page",
        "page_url": "https://www.ebl.com.bd/retail-deposit/EBL-Current-Account",
    },
    {
        "page_name": "EBL SME Deposits Page",
        "page_url": "https://www.ebl.com.bd/sme/sme-deposits",
    },
    {
        "page_name": "EBL Digital Banking Page",
        "page_url": "https://www.ebl.com.bd/retail-digital/ebl-skybanking",
    },
    {
        "page_name": "EBL Missed Call Alert Service Page",
        "page_url": "https://www.ebl.com.bd/retail-digital/ebl-missed-call-alert-service",
    },
    {
        "page_name": "EBL 365 PLUS Page",
        "page_url": "https://www.ebl.com.bd/retail-digital/ebl-365-plus",
    },
    {
        "page_name": "EBL SKYPAY Page",
        "page_url": "https://www.ebl.com.bd/retail-ecommerce/ebl-skypay",
    },
    {
        "page_name": "EBL Insta Account Branch Page",
        "page_url": "https://www.ebl.com.bd/retail/ebl-insta-account",
    },
    {
        "page_name": "EBL Insta Banking Online Page",
        "page_url": "https://www.ebl.com.bd/retail/ebl-insta-banking",
    },
    {
        "page_name": "EBL Priority Banking Page",
        "page_url": "https://www.ebl.com.bd/priority/",
    },
    {
        "page_name": "EBL Power Banking Page",
        "page_url": "https://www.ebl.com.bd/powerbanking",
    },
    {
        "page_name": "EBL Super Saver Page",
        "page_url": "https://www.ebl.com.bd/ebl-super-saver",
    },
    {
        "page_name": "EBL Women Banking Page",
        "page_url": "https://www.ebl.com.bd/retail/Women-Banking",
    },
    {
        "page_name": "EBL Agent Banking Page",
        "page_url": "https://www.ebl.com.bd/agentbanking",
    },
    {
        "page_name": "EBL Payroll Banking Page",
        "page_url": "https://www.ebl.com.bd/retail/EBL-Payroll-Banking",
    },
    {
        "page_name": "EBL Student Banking Page",
        "page_url": "https://www.ebl.com.bd/retail/EBL-Student-Banking",
    },
    {
        "page_name": "EBL Junior Savings Account Page",
        "page_url": "https://www.ebl.com.bd/student-banking/EBL-Junior",
    },
    {
        "page_name": "EBL Campus Account Page",
        "page_url": "https://www.ebl.com.bd/student-banking/EBL-Campus-Account",
    },
    {
        "page_name": "EBL Student File Services Page",
        "page_url": "https://www.ebl.com.bd/student-banking/EBL-Student-File-Services",
    },
    {
        "page_name": "EBL Child Future Plan Page",
        "page_url": "https://www.ebl.com.bd/student-banking/EBL-Child-Future-Plan",
    },
    {
        "page_name": "EBL Aspire Scheme Page",
        "page_url": "https://www.ebl.com.bd/student-banking/EBL-Aspire-Scheme",
    },
    {
        "page_name": "EBL Little Star Page",
        "page_url": "https://www.ebl.com.bd/student-banking/ebl-little-star",
    },
    {
        "page_name": "EBL Bancassurance Page",
        "page_url": "https://www.ebl.com.bd/retail/ebl-bancassurance",
    },
    {
        "page_name": "EBL Retail Alliance Page",
        "page_url": "https://www.ebl.com.bd/retail/ebl-retail-propositions",
    },
    {
        "page_name": "EBL Islamic Banking Page",
        "page_url": "https://www.ebl.com.bd/islamicbanking",
    },
    {
        "page_name": "EBL Shariah Committee Page",
        "page_url": "https://www.ebl.com.bd/islamic/member_ssc",
    },
    {
        "page_name": "EBL Islamic Retail Finance Page",
        "page_url": "https://www.ebl.com.bd/islamic/islamic-retail-finance",
    },
    {
        "page_name": "EBL Islamic SME Finance Page",
        "page_url": "https://www.ebl.com.bd/islamic/islamic-sme-finance",
    },
    {
        "page_name": "EBL Islamic Corporate Finance Page",
        "page_url": "https://www.ebl.com.bd/islamic/islamic-corporate-finance",
    },
    {
        "page_name": "EBL Islamic Cards Page",
        "page_url": "https://www.ebl.com.bd/islamic/islamic-cards",
    },
    {
        "page_name": "EBL Islamic Profit Distribution Page",
        "page_url": "https://www.ebl.com.bd/islamic/profit-distribution",
    },
    {
        "page_name": "EBL Islamic Notice Page",
        "page_url": "https://www.ebl.com.bd/islamic/notice",
    },
    {
        "page_name": "EBL Islamic Home Finance Page",
        "page_url": "https://www.ebl.com.bd/islamic-retail-finance/home-finance/",
    },
    {
        "page_name": "EBL Islamic Auto Finance Page",
        "page_url": "https://www.ebl.com.bd/islamic-retail-finance/auto-finance/",
    },
    {
        "page_name": "EBL Islamic Current Account Page",
        "page_url": "https://www.ebl.com.bd/islamic/deposit/ebl-islamic-current-account",
    },
    {
        "page_name": "EBL Islamic SND Account Page",
        "page_url": "https://www.ebl.com.bd/islamic/deposit/ebl-islamic-snd-account",
    },
    {
        "page_name": "EBL Speed Islamic SND Page",
        "page_url": "https://www.ebl.com.bd/islamic/deposit/ebl-speed-islamic-snd",
    },
    {
        "page_name": "EBL High Performance Islamic Account Page",
        "page_url": "https://www.ebl.com.bd/islamic/deposit/ebl-high-performance-islamic-account",
    },
    {
        "page_name": "EBL Power Islamic Savings Account Page",
        "page_url": "https://www.ebl.com.bd/islamic/deposit/ebl-power-islamic-savings-account",
    },
    {
        "page_name": "EBL Executive Islamic Savings Account Page",
        "page_url": "https://www.ebl.com.bd/islamic/deposit/ebl-executive-islamic-savings-account-payroll-account",
    },
    {
        "page_name": "EBL Women's Islamic Savings Account Page",
        "page_url": "https://www.ebl.com.bd/islamic/deposit/ebl-womens-islamic-savings-account",
    },
    {
        "page_name": "EBL Campus Islamic Account Page",
        "page_url": "https://www.ebl.com.bd/islamic/deposit/ebl-campus-islamic-account",
    },
    {
        "page_name": "EBL Junior Saver's Islamic Account Page",
        "page_url": "https://www.ebl.com.bd/islamic/deposit/ebl-junior-savers-islamic-account",
    },
    {
        "page_name": "EBL Islamic Term Deposit Account Page",
        "page_url": "https://www.ebl.com.bd/islamic/deposit/ebl-islamic-term-deposit-account",
    },
    {
        "page_name": "EBL Islamic Monthly Profit Scheme Page",
        "page_url": "https://www.ebl.com.bd/islamic/deposit/ebl-islamic-monthly-profit-scheme",
    },
    {
        "page_name": "EBL Islamic DPS Account Page",
        "page_url": "https://www.ebl.com.bd/islamic/deposit/ebl-islamic-dps-accounts",
    },
    {
        "page_name": "EBL Islamic Visa Platinum Debit Card Page",
        "page_url": "https://www.ebl.com.bd/islamic/eblcard/ebl-islamic-visa-platinum-debit-card",
    },
    {
        "page_name": "EBL Islamic Visa Prepaid Card Page",
        "page_url": "https://www.ebl.com.bd/islamic/eblcard/ebl-islamic-visa-prepaid-card",
    },
    {
        "page_name": "EBL Islamic Priority Visa Signature Debit Card Page",
        "page_url": "https://www.ebl.com.bd/islamic/eblcard/ebl-islamic-priority-visa-signature-debit-card",
    },
    {
        "page_name": "EBL Islamic Women's Platinum Debit Card Page",
        "page_url": "https://www.ebl.com.bd/islamic/eblcard/islamic-women-platinum-debit-card",
    },
    {
        "page_name": "EBL Contact Page",
        "page_url": "https://www.ebl.com.bd/contact",
    },
    {
        "page_name": "EBL Locator Page",
        "page_url": "https://www.ebl.com.bd/branches",
    },
    {
        "page_name": "EBL Online Apply Page",
        "page_url": "https://www.ebl.com.bd/onlineapply",
    },
    {
        "page_name": "EBL Forms and Downloads Page",
        "page_url": "https://www.ebl.com.bd/forms-downloads",
    },
    {
        "page_name": "EBL Interest Rates Page",
        "page_url": "https://www.ebl.com.bd/interest-rates",
    },
    {
        "page_name": "EBL Schedule of Charges Page",
        "page_url": "https://www.ebl.com.bd/schedule-of-charges",
    },
    {
        "page_name": "EBL Foreign Exchange Rate Page",
        "page_url": "https://www.ebl.com.bd/foreign-exchange-rate",
    },
    {
        "page_name": "EBL Complaint Cell Page",
        "page_url": "https://www.ebl.com.bd/complaint-cell",
    },
]


def unique_quick_actions(actions, limit=60):
    unique_actions = []

    for action in actions:
        clean_action = " ".join((action or "").strip().split())

        if clean_action and clean_action not in unique_actions:
            unique_actions.append(clean_action)

        if len(unique_actions) >= limit:
            break

    return unique_actions


def extract_bullet_quick_actions(reply, limit=8):
    actions = []

    for line in reply.splitlines():
        clean_line = line.strip()

        if not clean_line.startswith("- "):
            continue

        action = clean_line[2:].strip()

        if not action or ":" in action or "http" in action.lower():
            continue

        actions.append(action)

    return unique_quick_actions(actions, limit=limit)


def build_quick_actions(reply, source):
    if not reply:
        return []

    if source in {"greeting-handler", "identity-handler"}:
        return MAIN_QUICK_ACTIONS

    if reply == SCHEDULE_CHARGES_MENU_REPLY:
        return SCHEDULE_CHARGE_QUICK_ACTIONS

    if (
        source == "retail-charge-menu"
        and reply.startswith("Which Retail ")
    ):
        return extract_bullet_quick_actions(reply, limit=60)

    if (
        source == "sme-charge-menu"
        and reply.startswith("Which SME ")
    ):
        return extract_bullet_quick_actions(reply, limit=60)

    if (
        source == "corporate-charge-menu"
        and reply.startswith("Which Corporate ")
    ):
        return extract_bullet_quick_actions(reply, limit=60)

    if (
        source == "card-charge-menu"
        and (
            reply.startswith("Which Card ")
            or reply.startswith("Which Credit Card ")
            or reply.startswith("Which Debit Card ")
            or reply.startswith("Which Prepaid Card ")
        )
    ):
        return extract_bullet_quick_actions(reply, limit=60)

    if reply == INTEREST_RATE_TYPE_REPLY:
        return INTEREST_RATE_QUICK_ACTIONS

    if reply == LOAN_CATEGORY_QUESTION:
        return LOAN_SEGMENT_QUICK_ACTIONS

    if reply == ACCOUNT_CATEGORY_QUESTION:
        return ACCOUNT_SEGMENT_QUICK_ACTIONS

    if reply == CARD_CATEGORY_QUESTION:
        return CARD_CATEGORY_QUICK_ACTIONS

    if reply == LENDING_RATE_PRODUCT_REPLY:
        return LENDING_RATE_CATEGORY_QUICK_ACTIONS

    if reply.startswith("Which specific Retail charge"):
        return CHARGE_PROMPT_QUICK_ACTIONS["retail"]

    if reply.startswith("Which specific SME charge"):
        return CHARGE_PROMPT_QUICK_ACTIONS["sme"]

    if reply.startswith("Which specific Corporate charge"):
        return CHARGE_PROMPT_QUICK_ACTIONS["corporate"]

    if reply.startswith("Which specific Cards charge"):
        return CHARGE_PROMPT_QUICK_ACTIONS["cards"]

    if reply.startswith("Please specify the exact charge:"):
        if "\n-" in reply:
            return extract_bullet_quick_actions(reply, limit=12)

        return extract_bullet_quick_actions(
            "- " + reply.split(":", 1)[1].replace(", ", "\n- ").rstrip("."),
            limit=6,
        )

    if reply.startswith("Please specify the product/account type:"):
        if "\n-" in reply:
            return extract_bullet_quick_actions(reply, limit=12)

        return extract_bullet_quick_actions(
            "- " + reply.split(":", 1)[1].replace(", ", "\n- ").rstrip("."),
            limit=6,
        )

    if reply.startswith("Please specify the deposit product"):
        return DEPOSIT_RATE_CATEGORY_QUICK_ACTIONS

    if (
        "deposit product rate do you want?" in reply
        and source in {"deposit-rate-database", "interest-rate-router"}
    ):
        return extract_bullet_quick_actions(reply, limit=60)

    if (
        "timeline do you want?" in reply
        and source in {"deposit-rate-database", "interest-rate-router"}
    ):
        return extract_bullet_quick_actions(reply, limit=60)

    if (
        "lending product rate do you want?" in reply
        and source in {"lending-rate-database", "interest-rate-router"}
    ):
        return extract_bullet_quick_actions(reply, limit=60)

    if reply.startswith("Which Retail loan category"):
        return unique_quick_actions(get_loan_categories("Retail"), limit=8)

    if reply.startswith("Which Retail account category"):
        return unique_quick_actions(get_account_categories("Retail"), limit=8)

    if reply.startswith("Which SME account category"):
        return unique_quick_actions(get_account_categories("SME"), limit=8)

    if (
        source in {"account-router", "loan-router", "card-router"}
        and (
            "options include:" in reply
            or "accounts include:" in reply
            or "Please tell me the specific" in reply
        )
    ):
        return extract_bullet_quick_actions(reply, limit=30)

    return []


def strip_quick_action_bullets(reply, quick_actions):
    if not quick_actions:
        return reply

    quick_action_set = set(quick_actions)
    kept_lines = []

    for line in reply.splitlines():
        clean_line = line.strip()

        if clean_line.startswith("- ") and clean_line[2:].strip() in quick_action_set:
            continue

        kept_lines.append(line)

    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept_lines)).strip()


def display_reply_for_quick_actions(reply, quick_actions):
    if not quick_actions:
        return reply

    if reply == SCHEDULE_CHARGES_MENU_REPLY:
        return "Which banking charge do you want to know?"

    if reply.startswith("Which Retail charge category"):
        return "Which Retail charge category do you want to know?"

    if reply.startswith("Which Retail charge subcategory"):
        return reply.splitlines()[0]

    if (
        reply.startswith("Which Retail ")
        and (
            " product/account type do you want?" in reply
            or " charge do you want for " in reply
        )
    ):
        return reply.splitlines()[0]

    if reply.startswith("Which SME charge category"):
        return "Which SME charge category do you want to know?"

    if reply.startswith("Which SME charge subcategory"):
        return reply.splitlines()[0]

    if (
        reply.startswith("Which SME ")
        and (
            " product/account type do you want?" in reply
            or " charge do you want for " in reply
        )
    ):
        return reply.splitlines()[0]

    if reply.startswith("Which Corporate charge category"):
        return "Which Corporate charge category do you want to know?"

    if reply.startswith("Which Corporate charge subcategory"):
        return reply.splitlines()[0]

    if (
        reply.startswith("Which Corporate ")
        and (
            " product/account type do you want?" in reply
            or " service do you want?" in reply
            or " charge do you want for " in reply
            or " charge do you want?" in reply
        )
    ):
        return reply.splitlines()[0]

    if (
        reply.startswith("Which Card ")
        or reply.startswith("Which Credit Card ")
        or reply.startswith("Which Debit Card ")
        or reply.startswith("Which Prepaid Card ")
    ):
        return reply.splitlines()[0]

    if reply == INTEREST_RATE_TYPE_REPLY:
        return "Which interest rate do you want to know?"

    if reply == LOAN_CATEGORY_QUESTION:
        return "Which loan type do you want to know?"

    if reply == ACCOUNT_CATEGORY_QUESTION:
        return "Which account type do you want to open or know about?"

    if reply == CARD_CATEGORY_QUESTION:
        return "Which EBL card type do you want to know about?"

    if reply == LENDING_RATE_PRODUCT_REPLY:
        return "Please select a lending rate category."

    if reply.startswith("Which specific Retail charge"):
        return "Which specific Retail charge do you want to know?"

    if reply.startswith("Which specific SME charge"):
        return "Which specific SME charge do you want to know?"

    if reply.startswith("Which specific Corporate charge"):
        return "Which specific Corporate charge do you want to know?"

    if reply.startswith("Which specific Cards charge"):
        return "Which specific Card charge do you want to know?"

    if reply.startswith("Please specify the exact charge:"):
        return "Please specify the exact charge."

    if reply.startswith("Please specify the product/account type:"):
        return "Please specify the product/account type."

    if reply.startswith("Please specify the deposit product"):
        return "Please select a deposit rate category."

    return strip_quick_action_bullets(reply, quick_actions)


def build_response(reply, source, blocked=False, quick_actions=None, chat_id=None):
    return ChatResponse(
        reply=reply,
        source=source,
        blocked=blocked,
        quick_actions=quick_actions or [],
        chat_id=chat_id,
    )


def save_and_build_response(
    session_id,
    user_message,
    reply,
    source,
    status,
    blocked=False,
    quick_actions=None,
):
    response_quick_actions = []

    if not blocked:
        response_quick_actions = unique_quick_actions(
            quick_actions
            if quick_actions is not None
            else build_quick_actions(reply, source),
        )

    chat_id = save_chat(
        session_id=session_id,
        user_message=user_message,
        bot_reply=reply,
        source=source,
        blocked=blocked,
        status=status,
    )

    display_reply = display_reply_for_quick_actions(reply, response_quick_actions)

    return build_response(
        display_reply,
        source,
        blocked,
        response_quick_actions,
        chat_id,
    )


def update_summary_safely(session_id, session_summary, user_message, reply):
    try:
        new_summary = update_conversation_summary(
            session_summary,
            user_message,
            reply,
        )

        save_session_summary(session_id, new_summary)

    except Exception:
        pass


def safe_debug_print(label, value):
    message = f"{label} {value!r}"
    print(message.encode("ascii", "backslashreplace").decode("ascii"))


app = FastAPI(
    title="Eastern Bank AI Chatbot API",
    description="FastAPI backend for Eastern Bank AI chatbot",
    version="1.0.0",
)

@app.on_event("startup")
def startup_event():
    import_charge_csvs(clear_existing=True)
    ensure_charge_database_ready()
    import_deposit_rate_csvs(clear_existing=True)
    ensure_deposit_rate_database_ready()
    import_lending_rate_csvs(clear_existing=True)
    ensure_lending_rate_database_ready()
    import_account_types(clear_existing=True)
    ensure_account_types_ready()
    import_loan_types(clear_existing=True)
    ensure_loan_types_ready()
    start_complaint_email_scheduler()
    

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Eastern AI Chatbot API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "eastern-bank-plc-chatbot-backend"
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    user_message = request.message.strip()
    session_id = request.session_id or "default-session"

    if contains_sensitive_data(user_message):
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=get_safety_response(),
            source="safety-filter",
            status="blocked",
            blocked=True,
        )

    if is_identity_question(user_message):
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=get_identity_reply(),
            source="identity-handler",
            status="answered",
        )

    if is_greeting_only(user_message):
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=get_greeting_reply(),
            source="greeting-handler",
            status="greeting",
        )

    if is_schedule_charges_menu_request(user_message):
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=SCHEDULE_CHARGES_MENU_REPLY,
            source="schedule-charges-menu",
            status="answered",
        )

    early_card_charge_flow_reply = build_card_charge_flow_reply(
        session_id,
        user_message,
    )

    if early_card_charge_flow_reply:
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=early_card_charge_flow_reply,
            source="card-charge-menu",
            status="answered",
        )

    literal_card_category = literal_card_charge_menu_category(user_message)

    if literal_card_category:
        reply = (
            build_card_charge_type_reply()
            if literal_card_category == "cards"
            else build_card_charge_product_reply(literal_card_category)
        )

        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=reply,
            source="card-charge-menu",
            status="answered",
        )

    literal_schedule_category = literal_schedule_charge_menu_category(user_message)

    if literal_schedule_category:
        if literal_schedule_category == "retail":
            reply = build_retail_charge_group_reply()
            source = "retail-charge-menu"
        elif literal_schedule_category == "sme":
            reply = build_sme_charge_group_reply()
            source = "sme-charge-menu"
        elif literal_schedule_category == "corporate":
            reply = build_corporate_charge_group_reply()
            source = "corporate-charge-menu"
        else:
            reply = build_card_charge_type_reply()
            source = "card-charge-menu"

        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=reply,
            source=source,
            status="answered",
        )

    schedule_charge_category = get_schedule_charge_category(user_message)

    if schedule_charge_category and (
        not is_bare_schedule_charge_category(user_message)
        or last_reply_was_schedule_charges_menu(session_id)
    ):
        if schedule_charge_category == "retail":
            return save_and_build_response(
                session_id=session_id,
                user_message=user_message,
                reply=build_retail_charge_group_reply(),
                source="retail-charge-menu",
                status="answered",
            )

        if schedule_charge_category == "sme":
            return save_and_build_response(
                session_id=session_id,
                user_message=user_message,
                reply=build_sme_charge_group_reply(),
                source="sme-charge-menu",
                status="answered",
            )

        if schedule_charge_category == "corporate":
            return save_and_build_response(
                session_id=session_id,
                user_message=user_message,
                reply=build_corporate_charge_group_reply(),
                source="corporate-charge-menu",
                status="answered",
            )

        if schedule_charge_category == "cards":
            card_category = card_charge_category_label(user_message)
            reply = (
                build_card_charge_product_reply(card_category)
                if card_category
                else build_card_charge_type_reply()
            )

            return save_and_build_response(
                session_id=session_id,
                user_message=user_message,
                reply=reply,
                source="card-charge-menu",
                status="answered",
            )

        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=build_schedule_charge_category_reply(schedule_charge_category),
            source="schedule-charges-category-menu",
            status="answered",
        )

    retail_charge_flow_reply = build_retail_charge_flow_reply(
        session_id,
        user_message,
    )

    if retail_charge_flow_reply:
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=retail_charge_flow_reply,
            source="retail-charge-menu",
            status="answered",
        )

    retail_charge_recovery_reply = build_retail_charge_recovery_reply(
        session_id,
        user_message,
    )

    if retail_charge_recovery_reply:
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=retail_charge_recovery_reply,
            source="retail-charge-menu",
            status="answered",
        )

    sme_charge_flow_reply = build_sme_charge_flow_reply(
        session_id,
        user_message,
    )

    if sme_charge_flow_reply:
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=sme_charge_flow_reply,
            source="sme-charge-menu",
            status="answered",
        )

    sme_charge_recovery_reply = build_sme_charge_recovery_reply(
        session_id,
        user_message,
    )

    if sme_charge_recovery_reply:
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=sme_charge_recovery_reply,
            source="sme-charge-menu",
            status="answered",
        )

    corporate_charge_flow_reply = build_corporate_charge_flow_reply(
        session_id,
        user_message,
    )

    if corporate_charge_flow_reply:
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=corporate_charge_flow_reply,
            source="corporate-charge-menu",
            status="answered",
        )

    corporate_charge_recovery_reply = build_corporate_charge_recovery_reply(
        session_id,
        user_message,
    )

    if corporate_charge_recovery_reply:
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=corporate_charge_recovery_reply,
            source="corporate-charge-menu",
            status="answered",
        )

    card_charge_flow_reply = build_card_charge_flow_reply(
        session_id,
        user_message,
    )

    if card_charge_flow_reply:
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=card_charge_flow_reply,
            source="card-charge-menu",
            status="answered",
        )

    card_charge_recovery_reply = build_card_charge_recovery_reply(
        session_id,
        user_message,
    )

    if card_charge_recovery_reply:
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=card_charge_recovery_reply,
            source="card-charge-menu",
            status="answered",
        )

    direct_card_charge_reply = answer_card_charge_question_from_db(user_message)

    if direct_card_charge_reply:
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=direct_card_charge_reply,
            source="card-charge-menu",
            status="answered",
        )

    bare_segment_reply = build_bare_banking_segment_reply(session_id, user_message)

    if bare_segment_reply:
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=bare_segment_reply,
            source="bare-segment-router",
            status="answered",
        )

    interest_rate_flow_reply = build_interest_rate_flow_reply(
        session_id,
        user_message,
    )

    if interest_rate_flow_reply:
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=interest_rate_flow_reply,
            source="interest-rate-router",
            status="answered",
        )

    structured_deposit_rate_reply = answer_deposit_rate_question_from_db(
        user_message
    )

    if structured_deposit_rate_reply:
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=structured_deposit_rate_reply,
            source="deposit-rate-database",
            status="answered",
        )

    deposit_product_history = get_chat_history(session_id, limit=4)
    deposit_rate_product_name_reply = build_deposit_rate_product_name_reply(
        user_message,
        deposit_product_history,
    )

    if deposit_rate_product_name_reply:
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=deposit_rate_product_name_reply,
            source="deposit-rate-database",
            status="answered",
        )

    if is_specific_card_product_information_request(user_message):
        specific_card_product = detect_specific_card_product(user_message)

        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=build_specific_card_reply(specific_card_product),
            source="card-router",
            status="answered",
        )

    contextual_charge_query = build_contextual_charge_query(session_id, user_message)

    if contextual_charge_query:
        structured_fee_reply = answer_charge_question_from_db(
            contextual_charge_query,
            allow_product_only=True,
        )

        if structured_fee_reply:
            return save_and_build_response(
                session_id=session_id,
                user_message=user_message,
                reply=structured_fee_reply,
                source="charge-database",
                status="answered",
            )

    if is_fee_or_charge_question(user_message):
        structured_fee_reply = answer_charge_question_from_db(
            user_message,
            allow_product_only=True,
        )

        if structured_fee_reply:
            return save_and_build_response(
                session_id=session_id,
                user_message=user_message,
                reply=structured_fee_reply,
                source="charge-database",
                status="answered",
            )

        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=build_charge_not_found_reply(),
            source="charge-database",
            status="not_found",
        )

    structured_lending_rate_reply = answer_lending_rate_question_from_db(
        user_message
    )

    if structured_lending_rate_reply:
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=structured_lending_rate_reply,
            source="lending-rate-database",
            status="answered",
        )

    understood_query = understand_user_query_with_groq(user_message)
    safe_debug_print("UNDERSTOOD QUERY:", understood_query)

    intent = understood_query["intent"]
    search_query = understood_query["search_query"]
    is_deposit_rate_query = (
        is_deposit_rate_question(user_message)
        or is_deposit_rate_question(search_query)
    )
    is_lending_rate_query = (
        is_lending_rate_question(user_message)
        or is_lending_rate_question(search_query)
    )
    is_charge_query = (
        intent == "charge_information"
        or is_fee_or_charge_question(user_message)
        or is_fee_or_charge_question(search_query)
        or is_deposit_rate_query
        or is_lending_rate_query
    )

    if intent == "greeting" or is_greeting_only(user_message):
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=get_greeting_reply(),
            source="greeting-handler",
            status="greeting",
        )

    pending_complaint = get_pending_complaint(session_id)

    if pending_complaint:
        if is_complaint_confirmation_no(user_message):
            delete_pending_complaint(session_id)

            return save_and_build_response(
                session_id=session_id,
                user_message=user_message,
                reply=build_complaint_cancelled_reply(),
                source="complaint-agent",
                status="complaint_cancelled",
            )

        customer_email = extract_email(user_message)

        if is_complaint_confirmation_yes(user_message) or customer_email:
            if not customer_email:
                return save_and_build_response(
                    session_id=session_id,
                    user_message=user_message,
                    reply=build_missing_email_reply(),
                    source="complaint-agent",
                    status="collecting_customer_email",
                )

            complaint = save_complaint(
                session_id=session_id,
                issue_type=pending_complaint["issue_type"],
                description=pending_complaint["description"],
                customer_email=customer_email,
            )

            delete_pending_complaint(session_id)

            complaint_reply = build_complaint_created_reply(complaint)

            return save_and_build_response(
                session_id=session_id,
                user_message=user_message,
                reply=complaint_reply,
                source="complaint-agent",
                status="complaint_created",
            )

        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=(
                "Please confirm whether you want me to create the complaint record.\n\n"
                "Reply with Yes and your email address to create it or No to cancel."
            ),
            source="complaint-agent",
            status="waiting_complaint_confirmation",
        )

    if intent == "contact_information":
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=get_contact_reply(user_message),
            source="contact-agent",
            status="answered",
        )

    if intent == "online_apply":
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=get_online_apply_reply(user_message),
            source="online-apply-agent",
            status="answered",
        )

    if intent == "branch_locator" and not is_charge_query:
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=get_branch_locator_reply(),
            source="branch-locator-agent",
            status="answered",
        )

    if intent == "urgent_card_issue":
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=get_urgent_card_reply(),
            source="urgent-escalation-agent",
            status="urgent",
        )

    if intent == "complaint_create":
        if not has_enough_complaint_details(user_message):
            return save_and_build_response(
                session_id=session_id,
                user_message=user_message,
                reply=get_complaint_start_reply(),
                source="complaint-agent",
                status="collecting_complaint_details",
            )

        issue_type = get_issue_type(user_message)

        save_pending_complaint(
            session_id=session_id,
            issue_type=issue_type,
            description=user_message,
        )

        confirmation_reply = build_complaint_confirmation_reply(issue_type)

        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=confirmation_reply,
            source="complaint-agent",
            status="waiting_complaint_confirmation",
        )

    if intent == "complaint_status":
        complaint_id = extract_complaint_id(user_message)

        if not complaint_id:
            return save_and_build_response(
                session_id=session_id,
                user_message=user_message,
                reply=build_missing_complaint_id_reply(),
                source="complaint-status-agent",
                status="missing_complaint_id",
            )

        complaint = get_complaint_by_id(complaint_id)

        if not complaint:
            return save_and_build_response(
                session_id=session_id,
                user_message=user_message,
                reply=build_complaint_not_found_reply(complaint_id),
                source="complaint-status-agent",
                status="complaint_not_found",
            )

        status_reply = build_complaint_status_reply(complaint)

        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=status_reply,
            source="complaint-status-agent",
            status="complaint_status_found",
        )

    if intent == "memory_question":
        if is_complaint_memory_question(user_message):
            latest_complaint = get_latest_complaint_by_session(session_id)
            memory_reply = build_latest_complaint_memory_reply(latest_complaint)
        elif is_first_memory_question(user_message):
            first_message = get_first_user_message(session_id)
            memory_reply = build_first_memory_reply(first_message)
        else:
            recent_messages = get_recent_user_messages(session_id, limit=5)
            memory_reply = build_recent_memory_reply(recent_messages)

        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=memory_reply,
            source="memory-recall-agent",
            status="memory_recalled",
        )

    history_limit = 2 if is_charge_query else 4
    history = get_chat_history(session_id, limit=history_limit)
    has_previous_history = len(history) > 0

    card_router_reply = ""

    if not is_charge_query:
        card_router_reply = build_card_router_reply(user_message, intent, history)

    if card_router_reply:
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=card_router_reply,
            source="card-router",
            status="answered",
        )

    loan_router_reply = ""

    if not is_charge_query:
        loan_router_reply = build_loan_router_reply(user_message, intent, history)

    if loan_router_reply:
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=loan_router_reply,
            source="loan-router",
            status="answered",
        )

    account_router_reply = ""

    if not is_charge_query:
        account_router_reply = build_account_router_reply(
            user_message,
            intent,
            history,
            search_query,
        )

    if account_router_reply:
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=account_router_reply,
            source="account-router",
            status="answered",
        )

    if intent == "retail_banking":
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=build_retail_banking_overview_reply(),
            source="retail-banking-router",
            status="answered",
        )

    if intent == "islamic_banking":
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=build_islamic_banking_overview_reply(),
            source="islamic-banking-router",
            status="answered",
        )

    if intent == "off_topic" and not is_allowed_question(user_message, has_previous_history):
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=get_off_topic_reply(),
            source="topic-guard",
            status="off_topic",
        )

    is_broad_account_retrieval = (
        intent == "account_information"
        and (
            is_broad_account_opening_question(user_message)
            or is_broad_account_opening_question(search_query)
        )
    )

    local_knowledge_search_limit = 1 if is_charge_query else 3
    local_knowledge_snippet_limit = (
        CHARGE_LOCAL_SNIPPET_LIMIT
        if is_charge_query
        else 2800
    )
    local_knowledge_context_limit = (
        CHARGE_CONTEXT_LIMIT
        if is_charge_query
        else LOCAL_KNOWLEDGE_CONTEXT_LIMIT
    )

    local_knowledge_info = limit_text(
        search_local_knowledge(
            f"{user_message}\n{search_query}",
            limit=local_knowledge_search_limit,
            max_snippet_characters=local_knowledge_snippet_limit,
        ),
        local_knowledge_context_limit,
    )

    if is_charge_query:
        structured_deposit_rate_reply = answer_deposit_rate_question_from_db(
            f"{user_message}\n{search_query}"
        )

        if structured_deposit_rate_reply:
            return save_and_build_response(
                session_id=session_id,
                user_message=user_message,
                reply=structured_deposit_rate_reply,
                source="deposit-rate-database",
                status="answered",
            )

        structured_lending_rate_reply = answer_lending_rate_question_from_db(
            f"{user_message}\n{search_query}"
        )

        if structured_lending_rate_reply:
            return save_and_build_response(
                session_id=session_id,
                user_message=user_message,
                reply=structured_lending_rate_reply,
                source="lending-rate-database",
                status="answered",
            )

        structured_fee_reply = answer_charge_question_from_db(
            f"{user_message}\n{search_query}",
            allow_product_only=True,
        )

        if structured_fee_reply:
            return save_and_build_response(
                session_id=session_id,
                user_message=user_message,
                reply=structured_fee_reply,
                source="charge-database",
                status="answered",
            )

        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=build_charge_not_found_reply(),
            source="charge-database",
            status="not_found",
        )

    use_website_context = not (is_charge_query and local_knowledge_info)
    website_page_context_limit = (
        CHARGE_CONTEXT_LIMIT
        if is_charge_query
        else EBL_CONTEXT_LIMIT
    )

    if not use_website_context:
        website_page_info = ""

    elif is_broad_account_retrieval:
        selected_pages = [
            "EBL Online Apply Page",
            "EBL Retail Deposits Page",
            "EBL SME Deposits Page",
            "EBL Verified Contact Information",
        ]

        website_page_info = limit_text(
            get_website_information_by_page_names(selected_pages),
            website_page_context_limit,
        )

    else:
        website_page_info = limit_text(
            search_website_information(search_query, limit=5),
            website_page_context_limit,
        )

    if use_website_context and not website_page_info:
        selected_pages = select_knowledge_pages(intent)

        website_page_info = limit_text(
            get_website_information_by_page_names(selected_pages),
            website_page_context_limit,
        )

    if use_website_context and not website_page_info:
        website_page_info = limit_text(
            get_website_information(),
            website_page_context_limit,
        )

    final_context_limit = CHARGE_CONTEXT_LIMIT if is_charge_query else EBL_CONTEXT_LIMIT

    website_info = limit_text(
        combine_context_sections(
            local_knowledge_info,
            website_page_info,
        ),
        final_context_limit,
    )

    session_summary = limit_text(
        get_session_summary(session_id),
        SESSION_SUMMARY_LIMIT,
    )

    required_documents_reply = ""

    if not (
        is_broad_account_retrieval
    ):
        required_documents_reply = build_required_documents_reply(
            user_message,
            website_info,
        )

    if required_documents_reply:
        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=required_documents_reply,
            source="website-retrieval",
            status="answered",
        )

    try:
        reply = generate_groq_customer_service_reply(
            user_message,
            history,
            website_info,
            session_summary,
        )

    except Exception as error:
        print("GROQ ERROR:", repr(error))

        return save_and_build_response(
            session_id=session_id,
            user_message=user_message,
            reply=f"System error: {type(error).__name__}: {error}",
            source="system-error",
            status="error",
        )

    reply = clean_bank_contact_information(reply)

    response = save_and_build_response(
        session_id=session_id,
        user_message=user_message,
        reply=reply,
        source="groq-llm",
        status="answered",
    )

    update_summary_safely(
        session_id=session_id,
        session_summary=session_summary,
        user_message=user_message,
        reply=reply,
    )

    return response


def normalize_chat_feedback(feedback):
    normalized_feedback = normalize_menu_text(feedback).replace(" ", "_")
    feedback_aliases = {
        "helpful": "helpful",
        "not_helpful": "not_helpful",
        "nothelpful": "not_helpful",
    }

    return feedback_aliases.get(normalized_feedback, "")


@app.post("/chat/feedback")
def submit_chat_feedback(request: ChatFeedbackRequest):
    feedback = normalize_chat_feedback(request.feedback)

    if not feedback:
        raise HTTPException(
            status_code=400,
            detail="Feedback must be helpful or not_helpful.",
        )

    session_id = request.session_id or "default-session"
    feedback_saved = save_chat_feedback(
        chat_id=request.chat_id,
        session_id=session_id,
        feedback=feedback,
    )

    if not feedback_saved:
        raise HTTPException(
            status_code=404,
            detail="Chat response not found for this session.",
        )

    return {
        "message": "Feedback saved",
        "feedback": feedback,
    }


@app.post("/refresh-website-info")
def refresh_website_info():
    clear_website_information()

    saved_pages = []
    failed_pages = []

    for page in WEBSITE_PAGES:
        try:
            page_text = get_text_from_website(page["page_url"])

            save_website_text(
                page_name=page["page_name"],
                page_url=page["page_url"],
                page_text=page_text,
            )

            saved_pages.append({
                "page_name": page["page_name"],
                "page_url": page["page_url"],
                "characters_saved": len(page_text),
            })

        except Exception as error:
            failed_pages.append({
                "page_name": page["page_name"],
                "page_url": page["page_url"],
                "error": str(error),
            })

    try:
        discovered_pages = discover_website_pages()
    except Exception as error:
        discovered_pages = []
        failed_pages.append({
            "page_name": "EBL Detail Page Discovery",
            "page_url": "multiple EBL source pages",
            "error": str(error),
        })

    for page in discovered_pages:
        try:
            page_text = get_text_from_website(page["page_url"])

            save_website_text(
                page_name=page["page_name"],
                page_url=page["page_url"],
                page_text=page_text,
            )

            saved_pages.append({
                "page_name": page["page_name"],
                "page_url": page["page_url"],
                "characters_saved": len(page_text),
                "discovered": True,
            })

        except Exception as error:
            failed_pages.append({
                "page_name": page["page_name"],
                "page_url": page["page_url"],
                "error": str(error),
            })

    verified_contact_text = """
Eastern Bank PLC official contact information:

General email: info@ebl-bd.com
Hotline: 16230
From overseas: +8809677716230
General contact number: +8809666777325
Official online application link: https://www.ebl.com.bd/onlineapply

Source: Eastern Bank PLC official contact page.
"""

    save_website_text(
        page_name="EBL Verified Contact Information",
        page_url="https://www.ebl.com.bd/contact",
        page_text=verified_contact_text,
    )

    saved_pages.append({
        "page_name": "EBL Verified Contact Information",
        "page_url": "https://www.ebl.com.bd/contact",
        "characters_saved": len(verified_contact_text),
    })

    return {
        "message": "Website information refresh completed",
        "saved_pages": saved_pages,
        "failed_pages": failed_pages,
    }


@app.patch("/admin/complaints/{complaint_id}/status")
def admin_update_complaint_status(
    complaint_id: str,
    request: ComplaintStatusUpdateRequest,
):
    allowed_statuses = [
        "Pending",
        "In Progress",
        "Resolved",
        "Rejected",
    ]

    requested_status = request.status.strip()
    normalized_status = None

    for status in allowed_statuses:
        if requested_status.lower() == status.lower():
            normalized_status = status
            break

    if not normalized_status:
        raise HTTPException(
            status_code=400,
            detail="Invalid status. Allowed statuses are: Pending, In Progress, Resolved, Rejected.",
        )

    updated_complaint = update_complaint_status(
        complaint_id=complaint_id.upper(),
        new_status=normalized_status,
    )

    if not updated_complaint:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found.",
        )

    email_sent = False

    if normalized_status in ["Resolved", "Rejected"]:
        if updated_complaint.get("customer_email") and not updated_complaint.get("final_status_email_sent"):
            try:
                email_sent = send_final_status_email(
                    updated_complaint["customer_email"],
                    updated_complaint,
                )

                if email_sent:
                    mark_final_status_email_sent(updated_complaint["complaint_id"])

            except Exception as error:
                print("FINAL STATUS EMAIL ERROR:", repr(error))

    return {
        "message": "Complaint status updated successfully",
        "email_sent": email_sent,
        "complaint": updated_complaint,
    }
