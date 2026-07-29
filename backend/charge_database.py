"""Structured Schedule of Charges database import and lookup."""

from pathlib import Path
import csv
import re
import sqlite3

from language_support import expand_bangla_banglish_text


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "EBL_chatbot.db"
CHARGE_DATA_DIR = BASE_DIR / "charge_data"


CHARGE_COLUMNS = [
    "schedule",
    "category",
    "product",
    "charge_name",
    "condition",
    "amount",
    "vat_note",
    "source_file",
]


RETAIL_CHARGE_MENU_GROUPS = {
    "account_deposit": {
        "label": "Account & Deposit Charges",
        "categories": (
            "Current Account",
            "Savings Account",
            "FCY Account",
            "SND Account",
            "RFCD Account",
            "NITA Account",
            "Term Deposit",
            "Monthly Deposit Scheme",
            "Agent Banking Account",
            "Other Account Services",
            "Stop Payment",
            "Cheque Book",
        ),
    },
    "loan": {
        "label": "Loan Charges",
        "categories": ("Retail Loan",),
    },
    "cheque_clearing": {
        "label": "Cheque & Clearing Charges",
        "categories": (
            "Cheque Collection",
            "Cheque Clearing",
            "FCY Cheque Collection",
        ),
    },
    "fund_remittance": {
        "label": "Fund Transfer & Remittance",
        "categories": (
            "Fund Transfer / Payment Service",
            "FCY Fund Transfer",
            "Draft / FTT Cancellation",
            "Inward Remittance FCY",
            "Remittance File",
            "Student File and Others",
            "FCY Notes Issue",
            "FCY Cash Encashment",
            "Government Securities Investment Services",
            "Standing Instruction",
            "Sweep",
            "IPO Refund",
            "Salary Disbursement",
        ),
    },
    "locker": {
        "label": "Locker Charges",
        "categories": ("Locker",),
    },
    "certificates_reports": {
        "label": "Certificates & Reports",
        "categories": (
            "Statement and Certificate",
            "Certificates/Reports",
            "Holding of Security Items",
            "Old Voucher Collection",
        ),
    },
    "digital_banking": {
        "label": "Digital Banking Charges",
        "categories": (
            "Internet Banking",
            "Phone Banking",
            "SMS Banking",
            "Skybanking",
        ),
    },
    "other_services": {
        "label": "Other Service Charges",
        "categories": (
            "Fax",
            "Postage/Mail",
        ),
    },
}


SME_CHARGE_MENU_GROUPS = {
    "account_deposit": {
        "label": "Account & Deposit Charges",
        "categories": (
            "Current Account",
            "SND / Super HPA Account",
            "FCY Account",
            "Shubidha Account",
            "EBL Protect Current Account",
            "Term Deposits",
            "Monthly Deposit Schemes",
            "Account Statement Charges",
            "Stop Payment",
            "Cheque Book",
        ),
    },
    "fund_transfer": {
        "label": "Fund Transfer & Payment Services",
        "categories": (
            "Fund Transfer / Payment Services",
            "Local Fund Transfer Fee",
            "Stop Payment Instruction",
            "Standing Instruction",
            "Sweep",
            "Salary Transfer",
            "IPO Refund",
            "FCY Fund Transfer",
            "Draft / FTT Cancellation",
            "Inward Remittance FCY",
            "Travelers Cheque / FCY Notes",
            "Travelers Cheque / FCY Encashment",
        ),
    },
    "cheque_clearing": {
        "label": "Cheque & Clearing Charges",
        "categories": (
            "Cheque Collection",
            "Cheque Clearing",
            "FCY Cheque Collection",
        ),
    },
    "certificates_reports": {
        "label": "Certificates & Reports",
        "categories": (
            "Certificates/Reports",
            "Holding of Bonds",
        ),
    },
    "digital_banking": {
        "label": "Digital Banking Charges",
        "categories": (
            "Internet Banking and Digital Platform",
            "SMS Banking",
            "Phone Banking",
        ),
    },
    "other_services": {
        "label": "Other Service Charges",
        "categories": (
            "SWIFT/Fax",
            "Postage/Mail",
            "Cost of Stationery",
            "BPID",
            "Miscellaneous",
        ),
    },
    "loan": {
        "label": "Loan Charges",
        "categories": ("SME Loan Facilities",),
    },
}


CORPORATE_CHARGE_MENU_GROUPS = {
    "account_maintenance": {
        "label": "Account Maintenance",
        "categories": ("Account Maintenance",),
    },
    "general_od_ca_snd_hpa": {
        "label": "General Charges Applicable For OD, CA, SND & HPA",
        "categories": ("General Charges Applicable For Od, Ca, Snd & Hpa",),
    },
    "certificates_reports": {
        "label": "Certificates / Reports",
        "categories": ("Certificates / Reports",),
    },
    "cash_withdrawal_intercity": {
        "label": "Cash Withdrawal (Intercity)",
        "categories": ("Cash Withdrawal (Intercity)",),
    },
    "local_funds_transfer": {
        "label": "Local Funds Transfer",
        "categories": ("Local Funds Transfer",),
    },
    "standing_instruction": {
        "label": "Standing Instruction (SI)",
        "categories": ("Standing Instruction (SI)",),
    },
    "outward_remittance_fcy": {
        "label": "Outward Remittance - FCY",
        "categories": ("Outward Remittance - FCY",),
    },
    "cheque_collection": {
        "label": "Cheque Collection",
        "categories": ("Cheque Collection",),
    },
    "digital_platform": {
        "label": "Digital Platform",
        "categories": ("Digital Platform",),
    },
    "collection_solution": {
        "label": "Collection Solution",
        "categories": ("Collection Solution",),
    },
    "lending": {
        "label": "Lending",
        "categories": ("Lending",),
    },
    "supply_chain_finance": {
        "label": "Supply Chain Finance",
        "categories": ("Supply Chain Finance",),
    },
    "miscellaneous": {
        "label": "Miscellaneous",
        "categories": ("Miscellaneous",),
    },
    "government_securities": {
        "label": "Miscellaneous (Government Securities Investment Services)",
        "categories": ("Miscellaneous (Government Securities Investment Services)",),
    },
    "special_asset": {
        "label": "Miscellaneous (Special Asset Management)",
        "categories": ("Miscellaneous (Special Asset Management)",),
    },
    "import_lc": {
        "label": "Import LC",
        "categories": ("Import LC",),
    },
    "import_miscellaneous": {
        "label": "Import Miscellaneous",
        "categories": ("Import Miscellaneous",),
    },
    "import_bills": {
        "label": "Import Bills",
        "categories": ("Import Bills",),
    },
    "export": {
        "label": "Export",
        "categories": ("Export",),
    },
    "guarantee": {
        "label": "Guarantee",
        "categories": ("Guarantee",),
    },
    "miscellaneous_trade_service": {
        "label": "Miscellaneous Cost For Trade Service",
        "categories": ("Miscellaneous Cost For Trade Service",),
    },
}


CORPORATE_CHARGE_CATEGORY_DISPLAY_LABELS = {
    "Account Maintenance": "Account Maintenance",
    "General Charges Applicable For Od, Ca, Snd & Hpa": "General Charges Applicable For OD, CA, SND & HPA",
    "Cash Withdrawal (Intercity)": "Cash Withdrawal (Intercity)",
    "Local Funds Transfer": "Local Funds Transfer",
    "Standing Instruction (SI)": "Standing Instruction",
    "Certificates / Reports": "Certificates & Reports",
    "Outward Remittance - FCY": "Outward Remittance - FCY",
    "Import LC": "Import LC",
    "Import Bills": "Import Bills",
    "Import Miscellaneous": "Import Miscellaneous",
    "Miscellaneous Cost For Trade Service": "Miscellaneous Cost For Trade Service",
}


GENERIC_QUERY_WORDS = {
    "about",
    "bank",
    "banking",
    "charge",
    "charges",
    "cost",
    "ebl",
    "eastern",
    "fee",
    "fees",
    "for",
    "how",
    "is",
    "me",
    "of",
    "only",
    "plc",
    "schedule",
    "tell",
    "the",
    "to",
    "want",
    "what",
}


SHORT_QUERY_WORDS = {
    "bb",
    "ca",
    "dd",
    "fd",
    "lg",
    "lc",
    "mt",
    "od",
    "po",
    "si",
    "tt",
}


SCHEDULE_WORDS = {
    "retail": "Retail",
    "sme": "SME",
    "corporate": "Corporate",
    "corp": "Corporate",
    "card": "Cards",
    "cards": "Cards",
}


CARD_CONTEXT_WORDS = {
    "atm",
    "card",
    "cards",
    "credit",
    "debit",
    "diners",
    "mastercard",
    "prepaid",
    "unionpay",
    "visa",
}


FEE_TRIGGER_WORDS = {
    "activation",
    "advice",
    "advance",
    "alert",
    "amendment",
    "administrative",
    "annual",
    "annually",
    "assurance",
    "atm",
    "balance",
    "book",
    "bpid",
    "certificate",
    "charge",
    "charges",
    "cheque",
    "clearing",
    "closing",
    "commission",
    "cancellation",
    "cctv",
    "documentation",
    "current",
    "deposit",
    "fee",
    "fees",
    "facility",
    "fund",
    "global",
    "guarantee",
    "import",
    "increase",
    "interest",
    "issue",
    "issuance",
    "lc",
    "local",
    "late",
    "limit",
    "lounge",
    "maintenance",
    "minimum",
    "nita",
    "noc",
    "order",
    "payment",
    "pin",
    "policy",
    "primary",
    "processing",
    "regulatory",
    "receipt",
    "remittance",
    "renewal",
    "replacement",
    "return",
    "report",
    "rtgs",
    "sales",
    "settlement",
    "solvency",
    "statement",
    "stop",
    "supplementary",
    "swift",
    "tt",
    "transfer",
    "verification",
    "voucher",
    "wallet",
    "withdrawal",
    "yearly",
}


TOPIC_WORDS = {
    "activation",
    "advice",
    "advance",
    "alert",
    "amendment",
    "administrative",
    "annual",
    "annually",
    "assurance",
    "atm",
    "balance",
    "book",
    "bpid",
    "cash",
    "certificate",
    "cheque",
    "clearing",
    "closing",
    "commission",
    "cancellation",
    "cctv",
    "documentation",
    "current",
    "deposit",
    "domestic",
    "draft",
    "easycredit",
    "emi",
    "export",
    "fax",
    "fcy",
    "facility",
    "fund",
    "global",
    "guarantee",
    "import",
    "increase",
    "interest",
    "international",
    "interest",
    "issue",
    "issuance",
    "lc",
    "local",
    "late",
    "limit",
    "loan",
    "lounge",
    "maintenance",
    "minimum",
    "nita",
    "noc",
    "oversea",
    "overseas",
    "overlimit",
    "offshore",
    "onshore",
    "order",
    "payment",
    "pin",
    "policy",
    "primary",
    "processing",
    "regulatory",
    "receipt",
    "remittance",
    "renewal",
    "replacement",
    "report",
    "return",
    "rfcd",
    "regular",
    "rtgs",
    "saving",
    "savings",
    "settlement",
    "sky",
    "skylounge",
    "solvency",
    "statement",
    "stop",
    "supplementary",
    "snd",
    "swift",
    "tt",
    "transfer",
    "value",
    "verification",
    "voucher",
    "wallet",
    "want2buy",
    "withdrawal",
}


CHARGE_TYPE_WORDS = {
    "activation",
    "advice",
    "advance",
    "alert",
    "amendment",
    "administrative",
    "annual",
    "assurance",
    "atm",
    "balance",
    "book",
    "bpid",
    "certificate",
    "charge",
    "charges",
    "clearing",
    "closing",
    "commission",
    "cancellation",
    "cctv",
    "deposit",
    "documentation",
    "fee",
    "fees",
    "facility",
    "fund",
    "global",
    "guarantee",
    "import",
    "increase",
    "interest",
    "issue",
    "issuance",
    "lc",
    "local",
    "late",
    "limit",
    "lounge",
    "maintenance",
    "minimum",
    "order",
    "payment",
    "pin",
    "policy",
    "primary",
    "processing",
    "regulatory",
    "receipt",
    "remittance",
    "renewal",
    "replacement",
    "return",
    "report",
    "rtgs",
    "sales",
    "settlement",
    "solvency",
    "statement",
    "stop",
    "supplementary",
    "swift",
    "tt",
    "transfer",
    "verification",
    "voucher",
    "wallet",
    "withdrawal",
    "yearly",
}


STRICT_CHARGE_NAME_WORDS = {
    "activation",
    "advice",
    "advance",
    "alert",
    "amendment",
    "administrative",
    "annual",
    "annually",
    "assurance",
    "atm",
    "balance",
    "book",
    "bpid",
    "certificate",
    "clearing",
    "closing",
    "commission",
    "cancellation",
    "cctv",
    "deposit",
    "domestic",
    "documentation",
    "facility",
    "global",
    "guarantee",
    "import",
    "increase",
    "interest",
    "issue",
    "issuance",
    "lc",
    "local",
    "late",
    "limit",
    "lounge",
    "maintenance",
    "minimum",
    "noc",
    "order",
    "oversea",
    "overseas",
    "payment",
    "pin",
    "policy",
    "primary",
    "processing",
    "regulatory",
    "receipt",
    "remittance",
    "renewal",
    "replacement",
    "return",
    "report",
    "rtgs",
    "sales",
    "settlement",
    "solvency",
    "statement",
    "stop",
    "supplementary",
    "swift",
    "tt",
    "transfer",
    "verification",
    "voucher",
    "wallet",
    "withdrawal",
    "yearly",
}


CONDITION_QUERY_WORDS = {
    "above",
    "below",
    "bdt",
    "lac",
    "lakh",
    "less",
    "more",
    "offshore",
    "onshore",
    "over",
    "than",
    "to",
    "under",
    "up",
    "upto",
}


ALIASES = {
    "activate": {"activation", "activate", "dormant"},
    "activation": {"activation", "activate", "dormant"},
    "amend": {"amendment", "amend"},
    "amendment": {"amendment", "amend"},
    "annual": {"annual", "annually", "maintenance", "yearly"},
    "annually": {"annual", "annually", "yearly"},
    "cancel": {"cancellation", "cancel"},
    "cancellation": {"cancellation", "cancel"},
    "close": {"closing", "close"},
    "closing": {"closing", "close"},
    "cheque": {"cheque", "check"},
    "check": {"cheque", "check"},
    "estatement": {"estatement", "statement"},
    "extend": {"extend", "extension", "increase"},
    "extension": {"extend", "extension", "increase"},
    "increase": {"extend", "extension", "increase"},
    "issue": {"issue", "issuance"},
    "issuance": {"issue", "issuance"},
    "maintain": {"maintenance", "maintain"},
    "maintenance": {"maintenance", "maintain"},
    "saving": {"saving", "savings"},
    "savings": {"saving", "savings"},
    "shubidha": {"shubidha", "subidha"},
    "subidha": {"shubidha", "subidha"},
    "yearly": {"annual", "annually", "yearly"},
}


CANONICAL_TOPIC_WORDS = {
    "activate": "activation",
    "activation": "activation",
    "check": "cheque",
    "cheque": "cheque",
    "close": "closing",
    "closing": "closing",
    "issue": "issuance",
    "issuance": "issuance",
    "maintain": "maintenance",
    "maintenance": "maintenance",
    "saving": "saving",
    "savings": "saving",
}


_READY = False


def row_from_sqlite(row):
    if isinstance(row, dict):
        return row

    return dict(row)


def normalize_text(text):
    text = expand_bangla_banglish_text(text)
    text = (text or "").lower().replace(",", "")
    acronym_replacements = {
        "l/c": "lc",
        "s/b/l/c": "sblc",
        "lc/lg": "lc lg",
        "d/p": "dp",
        "d/a": "da",
        "p/o": "po",
        "d/d": "dd",
        "t/t": "tt",
    }

    for original_text, replacement_text in acronym_replacements.items():
        text = text.replace(original_text, replacement_text)

    spelling_replacements = {
        "subidha": "shubidha",
    }

    for original_text, replacement_text in spelling_replacements.items():
        text = re.sub(
            rf"\b{re.escape(original_text)}\b",
            replacement_text,
            text,
        )

    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def tokenize(text):
    words = []

    for word in normalize_text(text).split():
        if len(word) <= 2 and not word.isdigit() and word not in SHORT_QUERY_WORDS:
            continue

        if word.endswith("ies") and len(word) > 4:
            word = word[:-3] + "y"
        elif word.endswith("s") and len(word) > 4:
            word = word[:-1]

        if word not in words:
            words.append(word)

    return words


def expand_words(words):
    expanded = list(words)

    if "corp" in expanded and "corporate" not in expanded:
        expanded.append("corporate")

    if "corporate" in expanded and "corp" not in expanded:
        expanded.append("corp")

    if "check" in expanded and "cheque" not in expanded:
        expanded.append("cheque")

    if "cheque" in expanded and "check" not in expanded:
        expanded.append("check")

    if "lc" in expanded and "letter" not in expanded:
        expanded.append("letter")
        expanded.append("credit")

    if "saving" in expanded and "savings" not in expanded:
        expanded.append("savings")

    if "savings" in expanded and "saving" not in expanded:
        expanded.append("saving")

    return list(dict.fromkeys(expanded))


def create_charge_table(connection):
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS charges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule TEXT NOT NULL,
            category TEXT NOT NULL,
            product TEXT NOT NULL,
            charge_name TEXT NOT NULL,
            condition TEXT,
            amount TEXT NOT NULL,
            vat_note TEXT,
            source_file TEXT NOT NULL,
            search_text TEXT NOT NULL
        )
    """)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_charges_schedule ON charges(schedule)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_charges_charge_name ON charges(charge_name)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_charges_product ON charges(product)"
    )
    connection.commit()


def build_search_text(row):
    return normalize_text(
        " ".join(
            row.get(column, "")
            for column in [
                "schedule",
                "category",
                "product",
                "charge_name",
                "condition",
                "amount",
            ]
        )
    )


def iter_charge_csv_paths():
    if not CHARGE_DATA_DIR.exists():
        return []

    return sorted(CHARGE_DATA_DIR.glob("*_charges.csv"))


def read_charge_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        missing_columns = [
            column
            for column in CHARGE_COLUMNS
            if column not in (reader.fieldnames or [])
        ]

        if missing_columns:
            raise ValueError(
                f"{path.name} is missing columns: {', '.join(missing_columns)}"
            )

        for line_number, row in enumerate(reader, start=2):
            clean_row = {
                column: (row.get(column) or "").strip()
                for column in CHARGE_COLUMNS
            }

            required_missing = [
                column
                for column in [
                    "schedule",
                    "category",
                    "product",
                    "charge_name",
                    "amount",
                    "source_file",
                ]
                if not clean_row[column]
            ]

            if required_missing:
                raise ValueError(
                    f"{path.name}:{line_number} missing required values: "
                    f"{', '.join(required_missing)}"
                )

            yield clean_row


def import_charge_csvs(clear_existing=True):
    connection = sqlite3.connect(DATABASE_PATH)
    create_charge_table(connection)
    cursor = connection.cursor()

    if clear_existing:
        cursor.execute("DELETE FROM charges")

    inserted = 0

    for path in iter_charge_csv_paths():
        for row in read_charge_csv(path):
            cursor.execute("""
                INSERT INTO charges (
                    schedule,
                    category,
                    product,
                    charge_name,
                    condition,
                    amount,
                    vat_note,
                    source_file,
                    search_text
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["schedule"],
                row["category"],
                row["product"],
                row["charge_name"],
                row["condition"],
                row["amount"],
                row["vat_note"],
                row["source_file"],
                build_search_text(row),
            ))
            inserted += 1

    connection.commit()
    connection.close()
    return inserted


def ensure_charge_database_ready(force_import=False):
    global _READY

    if _READY and not force_import:
        return

    connection = sqlite3.connect(DATABASE_PATH)
    create_charge_table(connection)
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM charges")
    row_count = cursor.fetchone()[0]
    connection.close()

    if force_import or row_count == 0:
        import_charge_csvs(clear_existing=True)

    _READY = True


def unique_in_order(items):
    unique_items = []

    for item in items:
        if item and item not in unique_items:
            unique_items.append(item)

    return unique_items


def retail_charge_group_options():
    return [
        group["label"]
        for group in RETAIL_CHARGE_MENU_GROUPS.values()
    ]


def retail_charge_group_key(label):
    normalized_label = normalize_text(label)

    if not normalized_label:
        return ""

    aliases = {
        "account charge": "account_deposit",
        "account charges": "account_deposit",
        "account deposit charge": "account_deposit",
        "account deposit charges": "account_deposit",
        "deposit charge": "account_deposit",
        "deposit charges": "account_deposit",
        "loan charge": "loan",
        "loan charges": "loan",
        "cheque charge": "cheque_clearing",
        "cheque charges": "cheque_clearing",
        "cheque clearing charge": "cheque_clearing",
        "cheque clearing charges": "cheque_clearing",
        "clearing charge": "cheque_clearing",
        "clearing charges": "cheque_clearing",
        "fund transfer": "fund_remittance",
        "fund transfer remittance": "fund_remittance",
        "fund transfer remittance charge": "fund_remittance",
        "fund transfer remittance charges": "fund_remittance",
        "remittance": "fund_remittance",
        "remittance charge": "fund_remittance",
        "remittance charges": "fund_remittance",
        "locker": "locker",
        "locker charge": "locker",
        "locker charges": "locker",
        "certificate": "certificates_reports",
        "certificate report": "certificates_reports",
        "certificate reports": "certificates_reports",
        "certificates reports": "certificates_reports",
        "certificates reports charge": "certificates_reports",
        "certificates reports charges": "certificates_reports",
        "report": "certificates_reports",
        "reports": "certificates_reports",
        "digital": "digital_banking",
        "digital banking": "digital_banking",
        "digital banking charge": "digital_banking",
        "digital banking charges": "digital_banking",
        "other service": "other_services",
        "other service charge": "other_services",
        "other service charges": "other_services",
    }

    if normalized_label in aliases:
        return aliases[normalized_label]

    for key, group in RETAIL_CHARGE_MENU_GROUPS.items():
        if normalized_label == normalize_text(group["label"]):
            return key

    return ""


def retail_charge_group_label(group_key):
    group = RETAIL_CHARGE_MENU_GROUPS.get(group_key, {})

    return group.get("label", "")


def retail_charge_group_categories(group_key):
    group = RETAIL_CHARGE_MENU_GROUPS.get(group_key)

    if not group:
        return []

    ensure_charge_database_ready()
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    placeholders = ", ".join("?" for _item in group["categories"])
    cursor.execute(f"""
        SELECT category, MIN(id)
        FROM charges
        WHERE schedule = ?
        AND category IN ({placeholders})
        GROUP BY category
        ORDER BY MIN(id)
    """, ("Retail", *group["categories"]))
    available_categories = [row[0] for row in cursor.fetchall()]
    connection.close()

    return [
        category
        for category in group["categories"]
        if category in available_categories
    ]


def retail_charge_category_exists(category):
    normalized_category = normalize_text(category)

    return any(
        normalized_category == normalize_text(known_category)
        for group in RETAIL_CHARGE_MENU_GROUPS.values()
        for known_category in group["categories"]
    )


def retail_charge_category_label(category):
    normalized_category = normalize_text(category)

    for group in RETAIL_CHARGE_MENU_GROUPS.values():
        for known_category in group["categories"]:
            if normalized_category == normalize_text(known_category):
                return known_category

    return ""


def retail_charge_products(category):
    category = retail_charge_category_label(category)

    if not category:
        return []

    ensure_charge_database_ready()
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT product, MIN(id)
        FROM charges
        WHERE schedule = ?
        AND category = ?
        GROUP BY product
        ORDER BY MIN(id)
    """, ("Retail", category))
    products = [row[0] for row in cursor.fetchall()]
    connection.close()

    return products


def retail_charge_product_label(category, product):
    normalized_product = normalize_text(product)

    for existing_product in retail_charge_products(category):
        if normalized_product == normalize_text(existing_product):
            return existing_product

    return ""


def retail_charge_product_matches(product):
    normalized_product = normalize_text(product)

    if not normalized_product:
        return []

    matches = []

    for group in RETAIL_CHARGE_MENU_GROUPS.values():
        for category in group["categories"]:
            for existing_product in retail_charge_products(category):
                if normalized_product == normalize_text(existing_product):
                    matches.append((category, existing_product))

    return matches


def retail_charge_names(category, product):
    category = retail_charge_category_label(category)
    product = retail_charge_product_label(category, product)

    if not category or not product:
        return []

    ensure_charge_database_ready()
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT charge_name, MIN(id)
        FROM charges
        WHERE schedule = ?
        AND category = ?
        AND product = ?
        GROUP BY charge_name
        ORDER BY MIN(id)
    """, ("Retail", category, product))
    charge_names = [row[0] for row in cursor.fetchall()]
    connection.close()

    return charge_names


def retail_charge_name_label(category, product, charge_name):
    normalized_charge_name = normalize_text(charge_name)

    for existing_charge_name in retail_charge_names(category, product):
        if normalized_charge_name == normalize_text(existing_charge_name):
            return existing_charge_name

    return ""


def answer_exact_retail_charge(category, product, charge_name):
    category = retail_charge_category_label(category)
    product = retail_charge_product_label(category, product)
    charge_name = retail_charge_name_label(category, product, charge_name)

    if not category or not product or not charge_name:
        return ""

    ensure_charge_database_ready()
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("""
        SELECT *
        FROM charges
        WHERE schedule = ?
        AND category = ?
        AND product = ?
        AND charge_name = ?
        ORDER BY id
    """, ("Retail", category, product, charge_name))
    rows = [dict(row) for row in cursor.fetchall()]
    connection.close()

    if not rows:
        return ""

    if len(rows) == 1:
        return format_single_row_answer(rows[0])

    return format_multi_row_answer(rows)


def sme_charge_group_options():
    return [
        group["label"]
        for group in SME_CHARGE_MENU_GROUPS.values()
    ]


def sme_charge_group_key(label):
    normalized_label = normalize_text(label)

    if not normalized_label:
        return ""

    aliases = {
        "account charge": "account_deposit",
        "account charges": "account_deposit",
        "account deposit charge": "account_deposit",
        "account deposit charges": "account_deposit",
        "deposit charge": "account_deposit",
        "deposit charges": "account_deposit",
        "fund transfer": "fund_transfer",
        "fund transfer charge": "fund_transfer",
        "fund transfer charges": "fund_transfer",
        "fund transfer payment": "fund_transfer",
        "fund transfer payment service": "fund_transfer",
        "fund transfer payment services": "fund_transfer",
        "payment service": "fund_transfer",
        "payment services": "fund_transfer",
        "remittance": "fund_transfer",
        "remittance charge": "fund_transfer",
        "remittance charges": "fund_transfer",
        "cheque charge": "cheque_clearing",
        "cheque charges": "cheque_clearing",
        "cheque clearing charge": "cheque_clearing",
        "cheque clearing charges": "cheque_clearing",
        "clearing charge": "cheque_clearing",
        "clearing charges": "cheque_clearing",
        "certificate": "certificates_reports",
        "certificate report": "certificates_reports",
        "certificate reports": "certificates_reports",
        "certificates reports": "certificates_reports",
        "report": "certificates_reports",
        "reports": "certificates_reports",
        "digital": "digital_banking",
        "digital banking": "digital_banking",
        "digital banking charge": "digital_banking",
        "digital banking charges": "digital_banking",
        "other service": "other_services",
        "other service charge": "other_services",
        "other service charges": "other_services",
        "loan charge": "loan",
        "loan charges": "loan",
        "sme loan": "loan",
        "sme loan charge": "loan",
        "sme loan charges": "loan",
    }

    if normalized_label in aliases:
        return aliases[normalized_label]

    for key, group in SME_CHARGE_MENU_GROUPS.items():
        if normalized_label == normalize_text(group["label"]):
            return key

    return ""


def sme_charge_group_label(group_key):
    group = SME_CHARGE_MENU_GROUPS.get(group_key, {})

    return group.get("label", "")


def sme_charge_group_categories(group_key):
    group = SME_CHARGE_MENU_GROUPS.get(group_key)

    if not group:
        return []

    ensure_charge_database_ready()
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    placeholders = ", ".join("?" for _item in group["categories"])
    cursor.execute(f"""
        SELECT category, MIN(id)
        FROM charges
        WHERE schedule = ?
        AND category IN ({placeholders})
        GROUP BY category
        ORDER BY MIN(id)
    """, ("SME", *group["categories"]))
    available_categories = [row[0] for row in cursor.fetchall()]
    connection.close()

    return [
        category
        for category in group["categories"]
        if category in available_categories
    ]


def sme_charge_category_label(category):
    normalized_category = normalize_text(category)

    for group in SME_CHARGE_MENU_GROUPS.values():
        for known_category in group["categories"]:
            if normalized_category == normalize_text(known_category):
                return known_category

    return ""


def sme_charge_products(category):
    category = sme_charge_category_label(category)

    if not category:
        return []

    ensure_charge_database_ready()
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT product, MIN(id)
        FROM charges
        WHERE schedule = ?
        AND category = ?
        GROUP BY product
        ORDER BY MIN(id)
    """, ("SME", category))
    products = [row[0] for row in cursor.fetchall()]
    connection.close()

    return products


def sme_charge_product_label(category, product):
    normalized_product = normalize_text(product)

    for existing_product in sme_charge_products(category):
        if normalized_product == normalize_text(existing_product):
            return existing_product

    return ""


def sme_charge_product_matches(product):
    normalized_product = normalize_text(product)

    if not normalized_product:
        return []

    matches = []

    for group in SME_CHARGE_MENU_GROUPS.values():
        for category in group["categories"]:
            for existing_product in sme_charge_products(category):
                if normalized_product == normalize_text(existing_product):
                    matches.append((category, existing_product))

    return matches


def sme_charge_names(category, product):
    category = sme_charge_category_label(category)
    product = sme_charge_product_label(category, product)

    if not category or not product:
        return []

    ensure_charge_database_ready()
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT charge_name, MIN(id)
        FROM charges
        WHERE schedule = ?
        AND category = ?
        AND product = ?
        GROUP BY charge_name
        ORDER BY MIN(id)
    """, ("SME", category, product))
    charge_names = [row[0] for row in cursor.fetchall()]
    connection.close()

    return charge_names


def sme_charge_names_for_category(category):
    category = sme_charge_category_label(category)

    if not category:
        return []

    ensure_charge_database_ready()
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT charge_name, MIN(id)
        FROM charges
        WHERE schedule = ?
        AND category = ?
        GROUP BY charge_name
        ORDER BY MIN(id)
    """, ("SME", category))
    charge_names = [row[0] for row in cursor.fetchall()]
    connection.close()

    return charge_names


def sme_charge_name_label(category, product, charge_name):
    normalized_charge_name = normalize_text(charge_name)

    for existing_charge_name in sme_charge_names(category, product):
        if normalized_charge_name == normalize_text(existing_charge_name):
            return existing_charge_name

    return ""


def sme_charge_name_for_category_label(category, charge_name):
    normalized_charge_name = normalize_text(charge_name)

    for existing_charge_name in sme_charge_names_for_category(category):
        if normalized_charge_name == normalize_text(existing_charge_name):
            return existing_charge_name

    return ""


def answer_exact_sme_charge(category, product, charge_name):
    category = sme_charge_category_label(category)
    product = sme_charge_product_label(category, product)
    charge_name = sme_charge_name_label(category, product, charge_name)

    if not category or not product or not charge_name:
        return ""

    ensure_charge_database_ready()
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("""
        SELECT *
        FROM charges
        WHERE schedule = ?
        AND category = ?
        AND product = ?
        AND charge_name = ?
        ORDER BY id
    """, ("SME", category, product, charge_name))
    rows = [dict(row) for row in cursor.fetchall()]
    connection.close()

    if not rows:
        return ""

    if len(rows) == 1:
        return format_single_row_answer(rows[0])

    return format_multi_row_answer(rows)


def answer_exact_sme_category_charge(category, charge_name):
    category = sme_charge_category_label(category)
    charge_name = sme_charge_name_for_category_label(category, charge_name)

    if not category or not charge_name:
        return ""

    ensure_charge_database_ready()
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("""
        SELECT *
        FROM charges
        WHERE schedule = ?
        AND category = ?
        AND charge_name = ?
        ORDER BY id
    """, ("SME", category, charge_name))
    rows = [dict(row) for row in cursor.fetchall()]
    connection.close()

    if not rows:
        return ""

    if len(rows) == 1:
        return format_single_row_answer(rows[0])

    return format_multi_row_answer(rows)


def corporate_charge_group_options():
    return [
        group["label"]
        for group in CORPORATE_CHARGE_MENU_GROUPS.values()
    ]


def corporate_charge_group_key(label):
    normalized_label = normalize_text(label)

    if not normalized_label:
        return ""

    aliases = {
        "account": "account_maintenance",
        "account charge": "account_maintenance",
        "account charges": "account_maintenance",
        "account maintenance": "account_maintenance",
        "account maintenance charge": "account_maintenance",
        "account maintenance charges": "account_maintenance",
        "account statement": "account_maintenance",
        "general charges applicable for od ca snd hpa": "general_od_ca_snd_hpa",
        "general charges applicable for od ca snd and hpa": "general_od_ca_snd_hpa",
        "od ca snd hpa": "general_od_ca_snd_hpa",
        "stop payment": "general_od_ca_snd_hpa",
        "cheque book": "general_od_ca_snd_hpa",
        "cash": "cash_withdrawal_intercity",
        "cash withdrawal": "cash_withdrawal_intercity",
        "cash withdrawal intercity": "cash_withdrawal_intercity",
        "cash withdrawal charge": "cash_withdrawal_intercity",
        "cash withdrawal charges": "cash_withdrawal_intercity",
        "fund transfer": "local_funds_transfer",
        "fund transfer charge": "local_funds_transfer",
        "fund transfer charges": "local_funds_transfer",
        "local fund transfer": "local_funds_transfer",
        "local funds transfer": "local_funds_transfer",
        "local payment": "local_funds_transfer",
        "local payment charge": "local_funds_transfer",
        "local payment charges": "local_funds_transfer",
        "payment": "local_funds_transfer",
        "payment charge": "local_funds_transfer",
        "payment charges": "local_funds_transfer",
        "pay order": "local_funds_transfer",
        "rtgs": "local_funds_transfer",
        "standing instruction": "standing_instruction",
        "standing instruction charge": "standing_instruction",
        "standing instruction charges": "standing_instruction",
        "si": "standing_instruction",
        "cheque": "cheque_collection",
        "cheque charge": "cheque_collection",
        "cheque charges": "cheque_collection",
        "cheque collection": "cheque_collection",
        "cheque collection charge": "cheque_collection",
        "cheque collection charges": "cheque_collection",
        "clearing": "cheque_collection",
        "clearing charge": "cheque_collection",
        "clearing charges": "cheque_collection",
        "collection": "cheque_collection",
        "collection charge": "cheque_collection",
        "collection charges": "cheque_collection",
        "certificate": "certificates_reports",
        "certificate report": "certificates_reports",
        "certificate reports": "certificates_reports",
        "certificates reports": "certificates_reports",
        "report": "certificates_reports",
        "reports": "certificates_reports",
        "digital": "digital_platform",
        "digital platform": "digital_platform",
        "digital platform charge": "digital_platform",
        "digital platform charges": "digital_platform",
        "eblconnect": "digital_platform",
        "internet banking": "digital_platform",
        "collection solution": "collection_solution",
        "outward remittance": "outward_remittance_fcy",
        "outward remittance charge": "outward_remittance_fcy",
        "outward remittance charges": "outward_remittance_fcy",
        "outward remittance fcy": "outward_remittance_fcy",
        "fcy": "outward_remittance_fcy",
        "tt": "outward_remittance_fcy",
        "draft": "outward_remittance_fcy",
        "loan": "lending",
        "loan charge": "lending",
        "loan charges": "lending",
        "lending": "lending",
        "lending charge": "lending",
        "lending charges": "lending",
        "supply chain": "supply_chain_finance",
        "supply chain finance": "supply_chain_finance",
        "trade": "miscellaneous_trade_service",
        "trade service": "miscellaneous_trade_service",
        "trade service charge": "miscellaneous_trade_service",
        "trade service charges": "miscellaneous_trade_service",
        "import": "import_lc",
        "import charge": "import_lc",
        "import charges": "import_lc",
        "import lc": "import_lc",
        "import miscellaneous": "import_miscellaneous",
        "import other": "import_miscellaneous",
        "import other charges": "import_miscellaneous",
        "import bill": "import_bills",
        "import bills": "import_bills",
        "export": "export",
        "export charge": "export",
        "export charges": "export",
        "guarantee": "guarantee",
        "guarantee charge": "guarantee",
        "guarantee charges": "guarantee",
        "government securities": "government_securities",
        "government securities charge": "government_securities",
        "government securities charges": "government_securities",
        "bpid": "government_securities",
        "special asset": "special_asset",
        "special asset management": "special_asset",
        "special asset management charge": "special_asset",
        "special asset management charges": "special_asset",
        "sam": "special_asset",
        "misc": "miscellaneous",
        "miscellaneous": "miscellaneous",
        "miscellaneous charge": "miscellaneous",
        "miscellaneous charges": "miscellaneous",
        "miscellaneous cost for trade service": "miscellaneous_trade_service",
        "swift": "miscellaneous_trade_service",
        "courier": "miscellaneous",
        "postage": "miscellaneous",
    }

    if normalized_label in aliases:
        return aliases[normalized_label]

    for key, group in CORPORATE_CHARGE_MENU_GROUPS.items():
        if normalized_label == normalize_text(group["label"]):
            return key

    return ""


def corporate_charge_group_label(group_key):
    group = CORPORATE_CHARGE_MENU_GROUPS.get(group_key, {})

    return group.get("label", "")


def corporate_charge_category_display_label(category):
    category = corporate_charge_category_label(category) or category

    return CORPORATE_CHARGE_CATEGORY_DISPLAY_LABELS.get(category, category)


def corporate_charge_group_categories(group_key):
    group = CORPORATE_CHARGE_MENU_GROUPS.get(group_key)

    if not group:
        return []

    ensure_charge_database_ready()
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    placeholders = ", ".join("?" for _item in group["categories"])
    cursor.execute(f"""
        SELECT category, MIN(id)
        FROM charges
        WHERE schedule = ?
        AND category IN ({placeholders})
        GROUP BY category
        ORDER BY MIN(id)
    """, ("Corporate", *group["categories"]))
    available_categories = [row[0] for row in cursor.fetchall()]
    connection.close()

    return [
        category
        for category in group["categories"]
        if category in available_categories
    ]


def corporate_charge_category_label(category):
    normalized_category = normalize_text(category)

    for known_category, display_label in CORPORATE_CHARGE_CATEGORY_DISPLAY_LABELS.items():
        if normalized_category == normalize_text(display_label):
            return known_category

    for group in CORPORATE_CHARGE_MENU_GROUPS.values():
        for known_category in group["categories"]:
            if normalized_category == normalize_text(known_category):
                return known_category

    return ""


def corporate_charge_products(category):
    category = corporate_charge_category_label(category)

    if not category:
        return []

    ensure_charge_database_ready()
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT product, MIN(id)
        FROM charges
        WHERE schedule = ?
        AND category = ?
        GROUP BY product
        ORDER BY MIN(id)
    """, ("Corporate", category))
    products = [row[0] for row in cursor.fetchall()]
    connection.close()

    return products


def corporate_charge_product_label(category, product):
    normalized_product = normalize_text(product)

    for existing_product in corporate_charge_products(category):
        if normalized_product == normalize_text(existing_product):
            return existing_product

    return ""


def corporate_charge_product_matches(product):
    normalized_product = normalize_text(product)

    if not normalized_product:
        return []

    matches = []

    for group in CORPORATE_CHARGE_MENU_GROUPS.values():
        for category in group["categories"]:
            for existing_product in corporate_charge_products(category):
                if normalized_product == normalize_text(existing_product):
                    matches.append((category, existing_product))

    return matches


def corporate_charge_names_for_group(group_key):
    categories = corporate_charge_group_categories(group_key)

    if not categories:
        return []

    ensure_charge_database_ready()
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    placeholders = ", ".join("?" for _item in categories)
    cursor.execute(f"""
        SELECT charge_name, MIN(id)
        FROM charges
        WHERE schedule = ?
        AND category IN ({placeholders})
        GROUP BY charge_name
        ORDER BY MIN(id)
    """, ("Corporate", *categories))
    charge_names = [row[0] for row in cursor.fetchall()]
    connection.close()

    return charge_names


def corporate_charge_name_for_group_label(group_key, charge_name):
    normalized_charge_name = normalize_text(charge_name)

    for existing_charge_name in corporate_charge_names_for_group(group_key):
        if normalized_charge_name == normalize_text(existing_charge_name):
            return existing_charge_name

    return ""


def corporate_charge_names(category, product):
    category = corporate_charge_category_label(category)
    product = corporate_charge_product_label(category, product)

    if not category or not product:
        return []

    ensure_charge_database_ready()
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT charge_name, MIN(id)
        FROM charges
        WHERE schedule = ?
        AND category = ?
        AND product = ?
        GROUP BY charge_name
        ORDER BY MIN(id)
    """, ("Corporate", category, product))
    charge_names = [row[0] for row in cursor.fetchall()]
    connection.close()

    return charge_names


def corporate_charge_name_label(category, product, charge_name):
    normalized_charge_name = normalize_text(charge_name)

    for existing_charge_name in corporate_charge_names(category, product):
        if normalized_charge_name == normalize_text(existing_charge_name):
            return existing_charge_name

    return ""


def answer_exact_corporate_charge(category, product, charge_name):
    category = corporate_charge_category_label(category)
    product = corporate_charge_product_label(category, product)
    charge_name = corporate_charge_name_label(category, product, charge_name)

    if not category or not product or not charge_name:
        return ""

    ensure_charge_database_ready()
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("""
        SELECT *
        FROM charges
        WHERE schedule = ?
        AND category = ?
        AND product = ?
        AND charge_name = ?
        ORDER BY id
    """, ("Corporate", category, product, charge_name))
    rows = [dict(row) for row in cursor.fetchall()]
    connection.close()

    if not rows:
        return ""

    return format_corporate_table_answer(rows)


def answer_exact_corporate_group_charge(group_key, charge_name):
    categories = corporate_charge_group_categories(group_key)
    charge_name = corporate_charge_name_for_group_label(group_key, charge_name)

    if not categories or not charge_name:
        return ""

    ensure_charge_database_ready()
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    placeholders = ", ".join("?" for _item in categories)
    cursor.execute(f"""
        SELECT *
        FROM charges
        WHERE schedule = ?
        AND category IN ({placeholders})
        AND charge_name = ?
        ORDER BY id
    """, ("Corporate", *categories, charge_name))
    rows = [dict(row) for row in cursor.fetchall()]
    connection.close()

    if not rows:
        return ""

    return format_corporate_table_answer(rows)


def detect_requested_schedule(words):
    word_set = set(words)
    strong_card_words = CARD_CONTEXT_WORDS - {"atm"}

    if word_set & strong_card_words:
        return "Cards"

    for word in words:
        if word in SCHEDULE_WORDS:
            return SCHEDULE_WORDS[word]

    if word_set & CARD_CONTEXT_WORDS:
        return "Cards"

    return ""


def schedule_words_ignored_for_product(words):
    ignored_words = set(SCHEDULE_WORDS)

    if set(words) & CARD_CONTEXT_WORDS:
        ignored_words -= {"corp", "corporate"}

    return ignored_words


def word_matches(word, row_words):
    aliases = ALIASES.get(word, {word})
    return any(alias in row_words for alias in aliases)


def has_charge_trigger(words):
    return bool(set(words) & FEE_TRIGGER_WORDS)


def row_field_words(row, *field_names):
    return set(
        tokenize(
            " ".join(row[field_name] or "" for field_name in field_names)
        )
    )


def required_topic_words(words):
    topic_words = []

    for word in words:
        if word not in TOPIC_WORDS or word in {"charge", "fee", "fees"}:
            continue

        canonical_word = CANONICAL_TOPIC_WORDS.get(word, word)

        if canonical_word not in topic_words:
            topic_words.append(canonical_word)

    return topic_words


def row_matches_required_topics(row, words):
    topics = required_topic_words(words)

    if not topics:
        return True

    row_words = row_field_words(
        row,
        "category",
        "product",
        "charge_name",
        "condition",
    )

    matched = [
        word
        for word in topics
        if word_matches(word, row_words)
    ]

    if len(topics) <= 2:
        return len(matched) == len(topics)

    return len(matched) >= max(2, len(topics) - 1)


def score_charge_row(row, words, requested_schedule):
    row_words = row_field_words(
        row,
        "schedule",
        "category",
        "product",
        "charge_name",
        "condition",
        "amount",
    )

    if requested_schedule and row["schedule"].lower() != requested_schedule.lower():
        return -1000

    if not row_matches_required_topics(row, words):
        return 0

    score = 0

    if requested_schedule:
        score += 500

    product_words = row_field_words(row, "product")
    category_words = row_field_words(row, "category")
    charge_words = row_field_words(row, "charge_name")
    condition_words = row_field_words(row, "condition")

    for word in words:
        if word in GENERIC_QUERY_WORDS:
            continue

        if word_matches(word, charge_words):
            score += 90
        elif word_matches(word, product_words):
            score += 80
        elif word_matches(word, category_words):
            score += 45
        elif word_matches(word, condition_words):
            score += 35
        elif word_matches(word, row_words):
            score += 15

    if has_charge_trigger(words):
        product_or_category_match = any(
            word not in GENERIC_QUERY_WORDS
            and word not in CHARGE_TYPE_WORDS
            and (
                word_matches(word, product_words)
                or word_matches(word, category_words)
            )
            for word in words
        )

        if product_or_category_match:
            score += 50

    phrase_text = normalize_text(
        f"{row['product']} {row['charge_name']} {row['condition']}"
    )
    query_text = " ".join(words)

    for size in [4, 3, 2]:
        for index in range(0, len(words) - size + 1):
            phrase = " ".join(words[index:index + size])

            if phrase in phrase_text and phrase not in GENERIC_QUERY_WORDS:
                score += size * 25

    if " ".join(words[:3]) and " ".join(words[:3]) in phrase_text:
        score += 50

    if "account" in words and "account" in row_words:
        score += 30

    if "loan" in words and "loan" in row_words:
        score += 30

    if "card" in words and "card" not in row_words:
        score -= 120

    if "credit" in words and "credit" not in row_words:
        score -= 80

    if "debit" in words and "debit" not in row_words:
        score -= 80

    return score


def get_candidate_rows(query, limit=80, allow_product_only=False):
    words = expand_words(tokenize(query))

    if not words:
        return []

    if not has_charge_trigger(words) and not allow_product_only:
        return []

    requested_schedule = detect_requested_schedule(words)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    create_charge_table(connection)
    cursor = connection.cursor()

    if requested_schedule:
        cursor.execute(
            "SELECT * FROM charges WHERE lower(schedule) = lower(?)",
            (requested_schedule,),
        )
    else:
        cursor.execute("SELECT * FROM charges")

    rows = [dict(row) for row in cursor.fetchall()]
    connection.close()

    scored_rows = [
        (score_charge_row(row, words, requested_schedule), row)
        for row in rows
    ]
    scored_rows = [
        (score, row)
        for score, row in scored_rows
        if score >= 120
    ]
    scored_rows.sort(key=lambda item: item[0], reverse=True)

    if not scored_rows:
        return []

    top_score = scored_rows[0][0]

    selected_rows = [
        row
        for score, row in scored_rows
        if score >= max(120, top_score * 0.72)
    ]

    selected_rows = filter_rows_by_exact_charge_name_phrase(selected_rows, query)
    selected_rows = filter_rows_by_charge_name_words(selected_rows, words)
    selected_rows = filter_rows_by_exact_product_phrase(selected_rows, query)
    selected_rows = filter_rows_by_specific_product_words(selected_rows, words)
    selected_rows = filter_rows_by_default_card_product(selected_rows, words)
    selected_rows = filter_rows_by_card_context(selected_rows, words)
    selected_rows = filter_rows_by_query_condition(selected_rows, query)
    return selected_rows[:limit]


def specific_product_query_words(words):
    ignored_words = (
        GENERIC_QUERY_WORDS
        | CHARGE_TYPE_WORDS
        | CONDITION_QUERY_WORDS
        | schedule_words_ignored_for_product(words)
        | {"account", "accounts", "bank", "banking", "card", "cards", "loan", "loans"}
    )

    return [
        word
        for word in words
        if word not in ignored_words and not word.isdigit()
    ]


def filter_rows_by_specific_product_words(rows, words):
    if len(rows) <= 1:
        return rows

    specific_words = specific_product_query_words(words)

    if not specific_words:
        return rows

    product_matches = []

    for row in rows:
        product_words = row_field_words(row, "category", "product")
        matched_words = [
            word
            for word in specific_words
            if word_matches(word, product_words)
        ]

        if matched_words:
            product_matches.append((len(matched_words), row))

    if not product_matches:
        return rows

    top_count = max(count for count, _ in product_matches)
    return [
        row
        for count, row in product_matches
        if count == top_count
    ]


def filter_rows_by_exact_product_phrase(rows, query):
    if len(rows) <= 1:
        return rows

    query_text = f" {normalize_text(query)} "

    if rows_share_single_category(rows):
        category_phrase = normalize_text(rows[0]["category"])
        query_words = set(expand_words(tokenize(query)))
        strict_charge_words = {
            word
            for word in query_words
            if word in STRICT_CHARGE_NAME_WORDS
            and word not in {"charge", "charges", "fee", "fees"}
        }

        if (
            category_phrase
            and f" {category_phrase} " in query_text
            and query_words & {"charge", "charges", "fee", "fees", "cost"}
            and not strict_charge_words
        ):
            return rows

    whole_product_matches = []

    for row in rows:
        product_phrase = normalize_text(row["product"])

        if (
            product_phrase
            and " fee " not in f" {product_phrase} "
            and " charge " not in f" {product_phrase} "
            and f" {product_phrase} " in query_text
        ):
            whole_product_matches.append((len(product_phrase.split()), row))

    if whole_product_matches:
        top_score = max(score for score, _row in whole_product_matches)
        return [
            row
            for score, row in whole_product_matches
            if score == top_score
        ]

    if rows_share_single_category(rows):
        category_phrase = normalize_text(rows[0]["category"])

        if category_phrase and f" {category_phrase} " in query_text:
            return rows

    exact_row_matches = [
        (product_phrase_match_score(row, query), row)
        for row in rows
    ]
    exact_row_matches = [
        (score, row)
        for score, row in exact_row_matches
        if score > 0
    ]

    if not exact_row_matches:
        return rows

    top_score = max(score for score, _row in exact_row_matches)
    return [
        row
        for score, row in exact_row_matches
        if score == top_score
    ]


def normalized_charge_name_phrases(row):
    raw_charge_name = row["charge_name"] or ""
    parts = [raw_charge_name]
    parts.extend(
        re.split(
            r"\s*/\s*|\s+-\s+|\s+\bor\b\s+|\s+\band\b\s+",
            raw_charge_name,
        )
    )

    phrases = []

    for part in parts:
        phrase = normalize_text(part)

        if phrase and phrase not in phrases:
            phrases.append(phrase)

        words = phrase.split()

        if len(words) > 2:
            suffix_phrase = " ".join(words[1:])

            if suffix_phrase and suffix_phrase not in phrases:
                phrases.append(suffix_phrase)

    return phrases


def charge_name_phrase_match_score(row, query):
    query_text = f" {normalize_text(query)} "
    best_score = 0

    for charge_name in normalized_charge_name_phrases(row):
        if f" {charge_name} " in query_text:
            best_score = max(best_score, len(charge_name.split()))

    return best_score


def filter_rows_by_exact_charge_name_phrase(rows, query):
    if len(rows) <= 1:
        return rows

    exact_row_matches = [
        (charge_name_phrase_match_score(row, query), row)
        for row in rows
    ]
    exact_row_matches = [
        (score, row)
        for score, row in exact_row_matches
        if score > 0
    ]

    if not exact_row_matches:
        return rows

    top_score = max(score for score, _row in exact_row_matches)
    return [
        row
        for score, row in exact_row_matches
        if score == top_score
    ]


def filter_rows_by_charge_name_words(rows, words):
    if len(rows) <= 1:
        return rows

    strict_words = [
        word
        for word in words
        if word in STRICT_CHARGE_NAME_WORDS and word not in {"charge", "fee", "fees"}
    ]

    if not strict_words:
        return rows

    charge_matches = []

    for row in rows:
        charge_words = row_field_words(row, "charge_name")
        matched_words = [
            word
            for word in strict_words
            if word_matches(word, charge_words)
        ]

        if matched_words:
            charge_matches.append((len(matched_words), row))

    if not charge_matches:
        return rows

    top_count = max(count for count, _ in charge_matches)
    top_rows = [
        row
        for count, row in charge_matches
        if count == top_count
    ]

    if len(top_rows) <= 1:
        return top_rows

    row_lengths = [
        (len(row_field_words(row, "charge_name")), row)
        for row in top_rows
    ]
    row_lengths.sort(key=lambda item: item[0])

    distinct_lengths = sorted({length for length, _ in row_lengths})

    if len(distinct_lengths) > 1 and distinct_lengths[0] + 2 < distinct_lengths[1]:
        return [
            row
            for length, row in row_lengths
            if length == distinct_lengths[0]
        ]

    return top_rows


def filter_rows_by_default_card_product(rows, words):
    if len(rows) <= 1:
        return rows

    word_set = set(words)

    if not {"card", "credit"} <= word_set:
        return rows

    if "platinum" not in word_set:
        return rows

    card_product_rules = [
        ({"corporate", "platinum"}, "visa corporate platinum"),
        ({"women", "platinum"}, "visa women platinum"),
        ({"unionpay", "platinum"}, "unionpay platinum"),
        ({"army", "platinum"}, "visa army air force navy platinum"),
        ({"air", "force", "platinum"}, "visa army air force navy platinum"),
        ({"navy", "platinum"}, "visa army air force navy platinum"),
    ]

    for required_words, product_name in card_product_rules:
        if required_words <= word_set:
            matched_rows = [
                row
                for row in rows
                if normalize_text(row["product"]) == product_name
            ]

            if matched_rows:
                return matched_rows

    specific_modifiers = {
        "air",
        "army",
        "corporate",
        "force",
        "navy",
        "unionpay",
        "women",
    }

    if word_set & specific_modifiers:
        return rows

    visa_platinum_rows = [
        row
        for row in rows
        if normalize_text(row["product"]) == "visa platinum"
    ]

    return visa_platinum_rows or rows


def filter_rows_by_card_context(rows, words):
    if len(rows) <= 1:
        return rows

    if not all(row["schedule"].lower() == "cards" for row in rows):
        return rows

    if "replacement" in words and "pin" not in words:
        card_replacement_rows = [
            row
            for row in rows
            if "card replacement" in normalize_text(row["charge_name"])
        ]

        if card_replacement_rows:
            return card_replacement_rows

    if "supplementary" in words:
        supplementary_rows = [
            row
            for row in rows
            if "supplementary" in normalize_text(row["charge_name"])
            or "supplementary" in normalize_text(row["condition"])
        ]

        if supplementary_rows:
            return supplementary_rows

    annual_words = {"annual", "annually", "renewal", "issuance", "yearly"}

    if annual_words & set(words):
        primary_rows = [
            row
            for row in rows
            if "primary card" in normalize_text(row["condition"])
        ]

        if primary_rows:
            return primary_rows

    return rows


def query_condition_direction(query):
    text = f" {normalize_text(query)} "

    if any(phrase in text for phrase in [" above ", " over ", " more than "]):
        return "above"

    if any(
        phrase in text
        for phrase in [
            " up to ",
            " upto ",
            " below ",
            " under ",
            " less than ",
            " not more than ",
        ]
    ):
        return "up_to"

    return ""


def query_location_condition(query):
    text = f" {normalize_text(query)} "

    if " offshore " in text:
        return "offshore"

    if " onshore " in text:
        return "onshore"

    if " outside country " in text or " abroad " in text:
        return "outside"

    if " within country " in text or " inside country " in text:
        return "within"

    return ""


def query_day_condition(query):
    text = f" {normalize_text(query)} "

    if " same day " in text:
        return "same day"

    if " next day " in text:
        return "next day"

    return ""


def query_atm_condition(query):
    text = f" {normalize_text(query)} "

    if (
        " non ebl atm " in text
        or " non ebl " in text
        or " other atm " in text
        or " another atm " in text
    ):
        return "other atm"

    if " ebl atm " in text:
        return "ebl atm"

    return ""


def query_has_specific_condition(query):
    text = normalize_text(query)
    words = set(text.split())

    if query_condition_direction(query):
        return True

    if query_location_condition(query):
        return True

    if query_day_condition(query):
        return True

    if query_atm_condition(query):
        return True

    if any(word.isdigit() for word in words):
        return True

    return bool(words & {"free", "premium", "regular"})


def filter_rows_by_query_condition(rows, query):
    if len(rows) <= 1:
        return rows

    direction = query_condition_direction(query)
    location = query_location_condition(query)
    day = query_day_condition(query)
    atm = query_atm_condition(query)
    filtered_rows = rows

    if direction:
        query_numbers = {
            word
            for word in tokenize(query)
            if word.isdigit()
        }
        exact_number_matches = []

        for row in filtered_rows:
            condition_text = f" {normalize_text(row['condition'])} "

            for number in query_numbers:
                if direction == "above" and any(
                    phrase in condition_text
                    for phrase in [
                        f" above bdt {number} ",
                        f" above {number} ",
                        f" more than bdt {number} ",
                        f" more than {number} ",
                        f" bdt {number} and above ",
                        f" {number} and above ",
                    ]
                ):
                    exact_number_matches.append(row)

                if direction == "up_to" and any(
                    phrase in condition_text
                    for phrase in [
                        f" up to bdt {number} ",
                        f" up to {number} ",
                        f" below bdt {number} ",
                        f" below {number} ",
                    ]
                ):
                    exact_number_matches.append(row)

        if exact_number_matches:
            filtered_rows = list(dict.fromkeys(
                row["id"]
                for row in exact_number_matches
            ))
            id_map = {
                row["id"]: row
                for row in exact_number_matches
            }
            filtered_rows = [id_map[row_id] for row_id in filtered_rows]

        direction_matches = []

        for row in filtered_rows:
            condition_text = f" {normalize_text(row['condition'])} "

            if direction == "above" and (
                " above " in condition_text or " more than " in condition_text
            ):
                direction_matches.append(row)

            if direction == "up_to" and any(
                phrase in condition_text
                for phrase in [" up to ", " below ", " less than "]
            ):
                direction_matches.append(row)

        if direction_matches:
            filtered_rows = direction_matches

    if location:
        location_matches = []

        for row in filtered_rows:
            condition_text = f" {normalize_text(row['condition'])} "

            if location == "outside" and " outside " in condition_text:
                location_matches.append(row)

            if location == "within" and (
                " within " in condition_text or " inside " in condition_text
            ):
                location_matches.append(row)

            if location in {"onshore", "offshore"} and f" {location} " in condition_text:
                location_matches.append(row)

        if location_matches:
            filtered_rows = location_matches

    if day:
        day_matches = [
            row
            for row in filtered_rows
            if day in normalize_text(row["condition"])
        ]

        if day_matches:
            filtered_rows = day_matches

    if atm:
        atm_matches = [
            row
            for row in filtered_rows
            if atm in normalize_text(row["condition"])
            or atm in normalize_text(row["charge_name"])
        ]

        if atm_matches:
            filtered_rows = atm_matches

    query_numbers = {
        word
        for word in tokenize(query)
        if word.isdigit()
    }

    if query_numbers and not direction:
        number_matches = [
            row
            for row in filtered_rows
            if query_numbers & set(tokenize(row["condition"]))
        ]

        if number_matches:
            filtered_rows = number_matches

    return filtered_rows


def normalize_amount(amount, vat_note):
    amount = (amount or "").strip()
    vat_note = (vat_note or "").strip()
    lower_amount = amount.lower()
    lower_vat = vat_note.lower()

    if not amount:
        return ""

    if lower_amount in {"free", "nil", "n/a", "not applicable"}:
        return amount

    if "vat included" in lower_vat and "vat" in lower_amount:
        return amount

    if "vat included" in lower_vat:
        return f"{amount} (VAT included)"

    if "vat applicable" in lower_vat and "vat" not in lower_amount:
        return f"{amount} + VAT"

    return amount


def get_related_rows(row, same_product=True):
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    if same_product:
        cursor.execute("""
            SELECT *
            FROM charges
            WHERE schedule = ?
            AND category = ?
            AND product = ?
            AND charge_name = ?
            ORDER BY id ASC
        """, (
            row["schedule"],
            row["category"],
            row["product"],
            row["charge_name"],
        ))
    else:
        cursor.execute("""
            SELECT *
            FROM charges
            WHERE schedule = ?
            AND category = ?
            AND charge_name = ?
            ORDER BY id ASC
        """, (
            row["schedule"],
            row["category"],
            row["charge_name"],
        ))

    rows = [dict(sqlite_row) for sqlite_row in cursor.fetchall()]
    connection.close()
    return rows


def normalized_payable_value(row):
    return normalize_amount(row["amount"], row["vat_note"]).lower()


def all_rows_have_same_payable_value(rows):
    values = {
        normalized_payable_value(row)
        for row in rows
    }

    return len(values) == 1


def normalized_product_phrases(row):
    raw_product = row["product"] or ""
    parts = [raw_product]
    parts.extend(
        re.split(
            r"\s*/\s*|\s+-\s+|\s+\bor\b\s+|\s+\band\b\s+",
            raw_product,
        )
    )

    phrases = []
    removable_suffixes = [
        " account",
        " accounts",
        " card",
        " cards",
        " loan",
        " loans",
    ]

    for part in parts:
        phrase = normalize_text(part)

        if phrase and phrase not in phrases:
            phrases.append(phrase)

        for suffix in removable_suffixes:
            if phrase.endswith(suffix):
                short_phrase = phrase[: -len(suffix)].strip()

                if short_phrase and short_phrase not in phrases:
                    phrases.append(short_phrase)

    return phrases


def product_phrase_match_score(row, query):
    query_text = f" {normalize_text(query)} "
    best_score = 0

    for phrase in normalized_product_phrases(row):
        if " fee " in f" {phrase} " or " charge " in f" {phrase} ":
            continue

        if f" {phrase} " in query_text:
            best_score = max(best_score, len(phrase.split()))

    return best_score


def row_product_phrase_in_query(row, query):
    return product_phrase_match_score(row, query) > 0


def query_mentions_product(row, query):
    query_words = set(expand_words(tokenize(query)))
    category_words = row_field_words(row, "category")
    charge_words = row_field_words(row, "charge_name")
    product_words = row_field_words(row, "product")
    specific_product_words = (
        product_words
        - category_words
        - charge_words
        - {"account", "loan", "fee", "charge"}
    )

    return any(
        word_matches(word, specific_product_words)
        for word in query_words
    )


def prefer_generic_row(rows, query):
    if len(rows) <= 1:
        return rows

    if rows_have_same_charge_name(rows) and all_rows_have_same_payable_value(rows):
        return rows

    query_text = f" {normalize_text(query)} "

    if rows_share_single_category(rows):
        category_phrase = normalize_text(rows[0]["category"])

        if category_phrase and f" {category_phrase} " in query_text:
            return rows

    exact_product_rows = [
        row
        for row in rows
        if row_product_phrase_in_query(row, query)
    ]

    if exact_product_rows:
        return exact_product_rows

    if any(query_mentions_product(row, query) for row in rows):
        return rows

    generic_rows = [
        row
        for row in rows
        if row["product"].lower() == row["category"].lower()
        or row["product"].lower() in {
            "all retail loans",
            "all retail loans and overdraft",
            "all accounts",
        }
    ]

    return generic_rows or rows


def expand_related_rows_for_answer(rows, query):
    rows = prefer_generic_row(rows, query)

    if len(rows) != 1:
        return rows

    row = rows[0]

    if row_product_phrase_in_query(row, query) or query_mentions_product(row, query):
        return rows

    if query_has_specific_condition(query):
        return rows

    same_product_rows = get_related_rows(row, same_product=True)

    if len(same_product_rows) > 1 and len(same_product_rows) <= 5:
        return same_product_rows

    same_category_rows = get_related_rows(row, same_product=False)

    if (
        len(same_category_rows) > 1
        and all_rows_have_same_payable_value(same_category_rows)
    ):
        return same_category_rows

    return rows


def cleanup_subject(subject):
    subject = re.sub(r"\bAccount account\b", "Account", subject, flags=re.I)
    subject = re.sub(r"\bLoan loan\b", "Loan", subject, flags=re.I)
    subject = re.sub(r"\bfee fee\b", "fee", subject, flags=re.I)
    subject = re.sub(r"\bcharge charge\b", "charge", subject, flags=re.I)
    return " ".join(subject.split())


def build_subject(row):
    product = row["product"].strip()
    charge_name = row["charge_name"].strip()

    generic_products = {
        "Any account",
        "Cash Withdrawal (Intercity)",
        "Cheque / instruction",
        "Cheque Book",
        "Export Trade Service",
        "Fax",
        "Guarantee",
        "Import Trade Service",
        "Supply Chain Finance",
        "Trade Service",
    }

    if not product or product in generic_products:
        return cleanup_subject(charge_name)

    if charge_name.lower().startswith(product.lower()):
        return cleanup_subject(charge_name)

    return cleanup_subject(f"{product} {charge_name}")


def build_group_subject(rows):
    if not rows:
        return ""

    row = rows[0]
    category = row["category"].strip()
    charge_name = row["charge_name"].strip()

    if len(rows) > 1 and all_rows_have_same_payable_value(rows):
        return cleanup_subject(f"{category} {charge_name}")

    return build_subject(row)


def should_show_condition(condition):
    condition = (condition or "").strip().lower()
    hidden_conditions = {
        "any currency",
        "if customer forgets or requests a new one",
    }
    return bool(condition) and condition not in hidden_conditions


def display_condition(row):
    condition = (row["condition"] or "").strip()
    category = (row["category"] or "").strip().lower()

    if not condition:
        return ""

    parts = []

    for part in condition.split(";"):
        clean_part = part.strip()

        if clean_part.lower() == category:
            continue

        if normalize_text(clean_part) in normalize_text(row["charge_name"]):
            continue

        parts.append(clean_part)

    return "; ".join(parts)


def format_single_row_answer(row):
    subject = build_subject(row)
    amount = normalize_amount(row["amount"], row["vat_note"])
    condition = display_condition(row)

    if amount.lower() in {"n/a", "not applicable"}:
        if should_show_condition(condition):
            return f"{subject} for {condition} is not applicable."

        return f"{subject} is not applicable."

    if (
        normalize_text(row["charge_name"]) == "interest rate"
        and normalize_text(condition) == "annual"
    ):
        return f"{row['product']} annual interest rate is {amount}."

    if should_show_condition(condition):
        return f"{subject} for {condition} is {amount}."

    return f"{subject} is {amount}."


def rows_have_same_subject(rows):
    if not rows:
        return False

    first_subject = build_subject(rows[0]).lower()
    return all(build_subject(row).lower() == first_subject for row in rows)


def rows_have_same_charge_name(rows):
    if not rows:
        return False

    first_charge_name = rows[0]["charge_name"].strip().lower()
    return all(row["charge_name"].strip().lower() == first_charge_name for row in rows)


def rows_have_multiple_schedules(rows):
    schedules = {
        row["schedule"].strip().lower()
        for row in rows
        if row["schedule"].strip()
    }

    return len(schedules) > 1


def join_readable(items):
    items = [item for item in items if item]

    if len(items) <= 1:
        return "".join(items)

    if len(items) == 2:
        return f"{items[0]} and {items[1]}"

    return f"{', '.join(items[:-1])}, and {items[-1]}"


def format_bullet_answer(heading, bullets):
    clean_bullets = [
        bullet.strip().rstrip(".")
        for bullet in bullets
        if bullet and bullet.strip()
    ]

    if not clean_bullets:
        return heading

    return f"{heading}:\n" + "\n".join(
        f"- {bullet}"
        for bullet in clean_bullets
    )


def rows_are_corporate(rows):
    return bool(rows) and all(
        row["schedule"].strip().lower() == "corporate"
        for row in rows
    )


def markdown_table_cell(value):
    return " ".join((value or "").split()).replace("|", "/")


def corporate_banking_side(row):
    condition = normalize_text(row["condition"])

    if "offshore banking" in condition:
        return "offshore"

    return "onshore"


def corporate_condition_detail(row):
    condition = (row["condition"] or "").strip()

    if not condition:
        return ""

    detail_parts = []

    for part in condition.split(";"):
        clean_part = part.strip()
        normalized_part = normalize_text(clean_part)

        if normalized_part in {"onshore banking", "offshore banking"}:
            continue

        if normalized_part == normalize_text(row["category"]):
            continue

        if normalized_part in normalize_text(row["charge_name"]):
            continue

        detail_parts.append(clean_part)

    return "; ".join(detail_parts)


def corporate_table_particular(row, same_charge_name):
    charge_name = cleanup_subject(row["charge_name"])
    detail = corporate_condition_detail(row)

    if same_charge_name and detail:
        return detail

    if same_charge_name:
        return charge_name

    if detail:
        return f"{charge_name} - {detail}"

    return charge_name


def corporate_table_heading(rows):
    if rows_have_same_charge_name(rows):
        return cleanup_subject(rows[0]["charge_name"])

    if rows_share_single_category(rows):
        return corporate_charge_category_display_label(rows[0]["category"])

    return "Corporate charges"


def corporate_side_slab_summary(rows, side):
    parts = []

    for row in rows:
        if corporate_banking_side(row) != side:
            continue

        detail = corporate_condition_detail(row)
        amount = normalize_amount(row["amount"], row["vat_note"])

        if detail and amount:
            parts.append(f"{detail}: {amount}")
        elif amount:
            parts.append(amount)

    if not parts:
        return "N/A"

    prefix = "Equivalent Currency "
    return f"{prefix}{'; '.join(parts)}"


def should_collapse_corporate_side_slabs(rows):
    if not rows_have_same_charge_name(rows):
        return False

    if not rows_share_single_category(rows):
        return False

    return rows[0]["category"].strip().lower() == "outward remittance - fcy"


def format_corporate_side_slab_table(rows):
    heading = corporate_table_heading(rows)
    particular = cleanup_subject(rows[0]["charge_name"])
    onshore = corporate_side_slab_summary(rows, "onshore")
    offshore = corporate_side_slab_summary(rows, "offshore")

    return "\n".join([
        f"{heading}:",
        "",
        "| Particulars | Onshore Banking Charges | Offshore Banking Charges |",
        "| --- | --- | --- |",
        (
            "| "
            f"{markdown_table_cell(particular)} | "
            f"{markdown_table_cell(onshore)} | "
            f"{markdown_table_cell(offshore)} |"
        ),
    ])


def format_corporate_table_answer(rows):
    if not rows:
        return ""

    rows = sorted(rows, key=lambda row: row["id"])

    if should_collapse_corporate_side_slabs(rows):
        return format_corporate_side_slab_table(rows)

    same_charge_name = rows_have_same_charge_name(rows)
    table_rows = {}

    for row in rows:
        particular = corporate_table_particular(row, same_charge_name)
        side = corporate_banking_side(row)
        amount = normalize_amount(row["amount"], row["vat_note"])

        if particular not in table_rows:
            table_rows[particular] = {
                "onshore": "",
                "offshore": "",
            }

        existing_amount = table_rows[particular][side]
        table_rows[particular][side] = (
            f"{existing_amount} / {amount}" if existing_amount else amount
        )

    heading = corporate_table_heading(rows)
    lines = [
        f"{heading}:",
        "",
        "| Particulars | Onshore Banking Charges | Offshore Banking Charges |",
        "| --- | --- | --- |",
    ]

    for particular, charges in table_rows.items():
        lines.append(
            "| "
            f"{markdown_table_cell(particular)} | "
            f"{markdown_table_cell(charges['onshore'] or 'N/A')} | "
            f"{markdown_table_cell(charges['offshore'] or 'N/A')} |"
        )

    return "\n".join(lines)


def format_product_charge_summary(rows):
    if not rows:
        return ""

    rows = sorted(rows, key=lambda row: row["id"])
    product = rows[0]["product"]
    category = rows[0]["category"]
    bullets = []
    include_schedule = rows_have_multiple_schedules(rows)
    include_product = rows_have_multiple_products(rows)
    heading = category if include_product and rows_share_single_category(rows) else product

    for row in rows:
        amount = normalize_amount(row["amount"], row["vat_note"])
        condition = display_condition(row)
        charge_name = row["charge_name"].strip()
        label_parts = []

        if include_schedule:
            label_parts.append(row["schedule"].strip())

        if include_product:
            label_parts.append(row["product"].strip())

        label_parts.append(charge_name)

        if should_show_condition(condition):
            label_parts.append(condition)

        bullets.append(f"{' - '.join(label_parts)}: {amount}")

    if category.lower() == "locker":
        bullets.append(
            "Note: Premium locker location is subject to bank authority approval"
        )

    return format_bullet_answer(f"{heading} charges", bullets)


def rows_share_single_product(rows):
    if not rows:
        return False

    first_product = rows[0]["product"].lower()
    return all(row["product"].lower() == first_product for row in rows)


def rows_have_multiple_products(rows):
    products = {
        row["product"].strip().lower()
        for row in rows
        if row["product"].strip()
    }

    return len(products) > 1


def rows_share_single_category(rows):
    if not rows:
        return False

    first_category = rows[0]["category"].lower()
    return all(row["category"].lower() == first_category for row in rows)


def query_asks_product_charge_summary(query, rows):
    if not rows or not (
        rows_share_single_product(rows)
        or rows_share_single_category(rows)
    ):
        return False

    words = set(expand_words(tokenize(query)))

    if not (words & {"charge", "charges", "fee", "fees", "cost"}):
        return False

    if len({row["charge_name"].strip().lower() for row in rows}) <= 1:
        return False

    product_words = row_field_words(rows[0], "product")
    category_words = row_field_words(rows[0], "category")
    product_query_words = [
        word
        for word in words
        if word not in GENERIC_QUERY_WORDS
        and word not in CHARGE_TYPE_WORDS
        and (
            word_matches(word, product_words)
            or word_matches(word, category_words)
        )
    ]

    return bool(product_query_words)


def format_multi_row_answer(rows):
    rows = sorted(rows, key=lambda row: row["id"])

    if (
        len(rows) <= 6
        and rows_have_same_charge_name(rows)
        and all_rows_have_same_payable_value(rows)
    ):
        charge_name = cleanup_subject(rows[0]["charge_name"])
        amount = normalize_amount(rows[0]["amount"], rows[0]["vat_note"])
        products = []

        for row in rows:
            product = row["product"].strip()

            if product and product not in products:
                products.append(product)

        if len(products) > 1:
            return format_bullet_answer(
                charge_name,
                [
                    f"{product}: {amount}"
                    for product in products
                ],
            )

        return f"{charge_name} is {amount}."

    if rows_have_same_subject(rows) and len(rows) <= 12:
        subject = build_group_subject(rows)
        bullets = []
        include_schedule = rows_have_multiple_schedules(rows)

        for row in rows:
            condition = display_condition(row)
            amount = normalize_amount(row["amount"], row["vat_note"])
            label_parts = []

            if include_schedule:
                label_parts.append(row["schedule"].strip())

            if should_show_condition(condition):
                label_parts.append(condition)

            if label_parts:
                bullets.append(f"{' - '.join(label_parts)}: {amount}")
            else:
                bullets.append(amount)

        return format_bullet_answer(subject, bullets)

    if rows_have_same_charge_name(rows) and len(rows) <= 35:
        charge_name = cleanup_subject(rows[0]["charge_name"])
        bullets = []

        for row in rows:
            product = row["product"].strip()
            condition = display_condition(row)
            amount = normalize_amount(row["amount"], row["vat_note"])
            label = product

            if condition and condition not in {
                "Credit Cards",
                "Debit Cards",
                "Prepaid Cards",
            }:
                label = f"{label} - {condition}" if label else condition

            if amount.lower() in {"n/a", "not applicable"}:
                bullets.append(f"{label}: not applicable")
            else:
                bullets.append(f"{label}: {amount}")

        return format_bullet_answer(charge_name, bullets)

    if all_rows_have_same_payable_value(rows):
        subject = build_group_subject(rows)
        amount = normalize_amount(rows[0]["amount"], rows[0]["vat_note"])
        return f"{subject} is {amount}."

    products = []

    for row in rows:
        product = row["product"]

        if product not in products:
            products.append(product)

    if 1 < len(products) <= 6:
        return (
            "Please specify the product/account type:\n"
            + "\n".join(f"- {product}" for product in products)
        )

    charge_names = []

    for row in rows:
        charge_name = row["charge_name"]

        if charge_name not in charge_names:
            charge_names.append(charge_name)

    if 1 < len(charge_names) <= 6:
        return (
            "Please specify the exact charge:\n"
            + "\n".join(f"- {charge_name}" for charge_name in charge_names)
        )

    return format_single_row_answer(rows[0])


def answer_charge_question_from_db(query, allow_product_only=False):
    ensure_charge_database_ready()
    rows = get_candidate_rows(query, allow_product_only=allow_product_only)

    if not rows:
        return ""

    rows = expand_related_rows_for_answer(rows, query)

    if rows_are_corporate(rows):
        return format_corporate_table_answer(rows)

    if (
        allow_product_only
        and not has_charge_trigger(expand_words(tokenize(query)))
        and len(rows) > 1
    ):
        if rows_share_single_product(rows):
            return format_product_charge_summary(rows)

    if len(rows) > 1 and query_asks_product_charge_summary(query, rows):
        return format_product_charge_summary(rows)

    if len(rows) == 1:
        return format_single_row_answer(rows[0])

    return format_multi_row_answer(rows)
