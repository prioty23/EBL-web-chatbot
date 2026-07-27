"""Structured deposit interest rate database import and lookup."""

from pathlib import Path
import csv
import re
import sqlite3

from language_support import expand_bangla_banglish_text


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "EBL_chatbot.db"
DEPOSIT_RATE_DATA_DIR = BASE_DIR / "deposit_rate_data"


DEPOSIT_RATE_COLUMNS = [
    "business_unit",
    "category",
    "product",
    "condition",
    "rate",
    "note",
    "source_file",
]


GENERIC_RATE_WORDS = {
    "about",
    "account",
    "accounts",
    "bank",
    "banking",
    "bdt",
    "deposit",
    "deposits",
    "ebl",
    "eastern",
    "for",
    "give",
    "how",
    "interest",
    "is",
    "me",
    "of",
    "plc",
    "product",
    "rate",
    "rates",
    "show",
    "tell",
    "the",
    "to",
    "want",
    "what",
}


DEPOSIT_RATE_CONTEXT_WORDS = {
    "alo",
    "aspire",
    "casa",
    "classic",
    "confidence",
    "current",
    "deposit",
    "deposits",
    "diamond",
    "dps",
    "earn",
    "equity",
    "fd",
    "fdr",
    "fixed",
    "future",
    "hpa",
    "insta",
    "kotipoti",
    "max",
    "millionaire",
    "multiplier",
    "payroll",
    "premium",
    "recurring",
    "repeat",
    "salary",
    "saving",
    "savings",
    "scheme",
    "shubidha",
    "snd",
    "super",
    "term",
    "women",
    "womens",
}


BLOCKED_RATE_CONTEXT_WORDS = {
    "card",
    "cards",
    "credit",
    "debit",
    "exchange",
    "forex",
    "loan",
    "loans",
    "usd",
}


BUSINESS_UNIT_WORDS = {
    "retail": ["Retail"],
    "sme": ["SME", "Commercial"],
    "commercial": ["Commercial"],
    "corporate": ["Corporate"],
    "corp": ["Corporate"],
}


CATEGORY_WORDS = {
    "casa": "CASA Products",
    "current": "CASA Products",
    "hpa": "Other CASA / SND / HPA",
    "saving": "CASA Products",
    "savings": "CASA Products",
    "snd": "Other CASA / SND / HPA",
    "fd": "Term Deposit",
    "fdr": "Term Deposit",
    "fixed": "Term Deposit",
    "term": "Term Deposit",
    "dps": "Recurring Deposit",
    "recurring": "Recurring Deposit",
    "scheme": "Recurring Deposit",
    "closed": "Closed Products",
}


SHORT_WORDS = {"fd", "rd", "cr"}


_READY = False


def normalize_text(text):
    text = expand_bangla_banglish_text(text)
    text = (text or "").lower()
    replacements = {
        "&": " and ",
        "+": " plus ",
        "50+": "50 plus",
        "≤": " up to ",
        "–": "-",
        "—": "-",
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "f/d": "fd",
        "fdr": "fd",
        "fixed deposits": "fixed deposit",
        "crore": "cr",
        "months": "month",
        "years": "year",
        "days": "day",
        "subidha": "shubidha",
    }

    for original_text, replacement_text in replacements.items():
        text = text.replace(original_text, replacement_text)

    return re.sub(r"[^a-z0-9.]+", " ", text).strip()


def tokenize(text):
    words = []

    for word in normalize_text(text).split():
        if len(word) <= 2 and not word.isdigit() and word not in SHORT_WORDS:
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

    def add(word):
        if word not in expanded:
            expanded.append(word)

    if "fd" in expanded:
        add("fixed")
        add("deposit")

    if "fixed" in expanded and "deposit" in expanded:
        add("fd")

    if "fdr" in expanded:
        add("fd")

    if "dps" in expanded:
        add("recurring")
        add("deposit")

    if "recurring" in expanded:
        add("dps")

    if "saving" in expanded:
        add("savings")

    if "savings" in expanded:
        add("saving")

    if "women" in expanded:
        add("womens")

    if "womens" in expanded:
        add("women")

    if "corporate" in expanded:
        add("corp")

    if "cr" in expanded:
        add("crore")

    return expanded


def create_deposit_rate_table(connection):
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deposit_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_unit TEXT NOT NULL,
            category TEXT NOT NULL,
            product TEXT NOT NULL,
            condition TEXT NOT NULL,
            rate TEXT NOT NULL,
            note TEXT,
            source_file TEXT NOT NULL,
            search_text TEXT NOT NULL
        )
    """)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_deposit_rates_unit "
        "ON deposit_rates(business_unit)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_deposit_rates_category "
        "ON deposit_rates(category)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_deposit_rates_product "
        "ON deposit_rates(product)"
    )
    connection.commit()


def build_search_text(row):
    return normalize_text(
        " ".join(
            row.get(column, "")
            for column in [
                "business_unit",
                "category",
                "product",
                "condition",
                "rate",
                "note",
            ]
        )
    )


def iter_deposit_rate_csv_paths():
    if not DEPOSIT_RATE_DATA_DIR.exists():
        return []

    return sorted(DEPOSIT_RATE_DATA_DIR.glob("*.csv"))


def read_deposit_rate_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        missing_columns = [
            column
            for column in DEPOSIT_RATE_COLUMNS
            if column not in (reader.fieldnames or [])
        ]

        if missing_columns:
            raise ValueError(
                f"{path.name} is missing columns: {', '.join(missing_columns)}"
            )

        for line_number, row in enumerate(reader, start=2):
            clean_row = {
                column: (row.get(column) or "").strip()
                for column in DEPOSIT_RATE_COLUMNS
            }

            required_missing = [
                column
                for column in [
                    "business_unit",
                    "category",
                    "product",
                    "condition",
                    "rate",
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


def import_deposit_rate_csvs(clear_existing=True):
    connection = sqlite3.connect(DATABASE_PATH)
    create_deposit_rate_table(connection)
    cursor = connection.cursor()

    if clear_existing:
        cursor.execute("DELETE FROM deposit_rates")

    inserted = 0

    for path in iter_deposit_rate_csv_paths():
        for row in read_deposit_rate_csv(path):
            cursor.execute("""
                INSERT INTO deposit_rates (
                    business_unit,
                    category,
                    product,
                    condition,
                    rate,
                    note,
                    source_file,
                    search_text
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["business_unit"],
                row["category"],
                row["product"],
                row["condition"],
                row["rate"],
                row["note"],
                row["source_file"],
                build_search_text(row),
            ))
            inserted += 1

    connection.commit()
    connection.close()
    return inserted


def ensure_deposit_rate_database_ready(force_import=False):
    global _READY

    if _READY and not force_import:
        return

    connection = sqlite3.connect(DATABASE_PATH)
    create_deposit_rate_table(connection)
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM deposit_rates")
    row_count = cursor.fetchone()[0]
    connection.close()

    if force_import or row_count == 0:
        import_deposit_rate_csvs(clear_existing=True)

    _READY = True


def row_field_words(row, *field_names):
    return set(
        tokenize(
            " ".join(row[field_name] or "" for field_name in field_names)
        )
    )


def requested_business_units(words):
    units = []
    word_set = set(words)
    primary_unit_words = {
        "retail": "Retail",
        "commercial": "Commercial",
        "corporate": "Corporate",
    }

    def add_units(business_units):
        for business_unit in business_units:
            if business_unit not in units:
                units.append(business_unit)

    for word in words:
        business_unit = primary_unit_words.get(word)

        if business_unit:
            return [business_unit]

    if "sme" in word_set:
        add_units(["SME", "Commercial"])

    if "corp" in word_set:
        add_units(["Corporate"])

    for word in words:
        add_units(BUSINESS_UNIT_WORDS.get(word, []))

    return units


def query_has_rate_terms(words):
    return bool({"interest", "rate", "rates", "profit"} & set(words))


def query_has_deposit_rate_context(words):
    return bool(set(words) & DEPOSIT_RATE_CONTEXT_WORDS)


def is_deposit_rate_question(query):
    words = expand_words(tokenize(query))

    if not query_has_rate_terms(words):
        return False

    if set(words) & BLOCKED_RATE_CONTEXT_WORDS:
        return False

    return query_has_deposit_rate_context(words)


def detect_requested_category(words):
    for word in words:
        category = CATEGORY_WORDS.get(word)

        if category:
            return category

    return ""


def row_product_phrase_in_query(row, query):
    query_text = f" {normalize_text(query)} "
    product_phrase = normalize_text(row["product"])

    if product_phrase and f" {product_phrase} " in query_text:
        return True

    query_words = set(expand_words(tokenize(query)))
    product_words = set(expand_words(tokenize(row["product"])))

    if product_words and product_words <= query_words:
        return True

    product_parts = re.split(r"\s*/\s*|\s+-\s+", row["product"])

    for product_part in product_parts:
        phrase = normalize_text(product_part)

        if phrase and len(phrase) > 3 and f" {phrase} " in query_text:
            return True

    return False


def product_phrase_in_query(product, query):
    query_text = f" {normalize_text(query)} "
    product_phrase = normalize_text(product)

    if not product_phrase:
        return False

    query_words = set(expand_words(tokenize(query)))
    product_words = set(expand_words(tokenize(product)))

    if product_words and product_words <= query_words:
        return True

    if len(product_phrase.split()) == 1 and "ebl" not in tokenize(query):
        return False

    if f" {product_phrase} " in query_text:
        return True

    product_parts = re.split(r"\s*/\s*|\s+-\s+", product)

    for product_part in product_parts:
        phrase = normalize_text(product_part)

        if len(phrase.split()) < 2 and "ebl" not in tokenize(query):
            continue

        if phrase and len(phrase) > 3 and f" {phrase} " in query_text:
            return True

    return False


def query_mentions_known_deposit_rate_product(query):
    words = set(expand_words(tokenize(query)))

    if not words or words & BLOCKED_RATE_CONTEXT_WORDS:
        return False

    return any(
        product_phrase_in_query(product, query)
        for product in get_all_products()
    )


def row_matches_requested_unit(row, units):
    if not units:
        return True

    row_unit = row["business_unit"]

    return row_unit in units or row_unit == "General"


def score_rate_row(row, words, query):
    units = requested_business_units(words)

    if not row_matches_requested_unit(row, units):
        return 0

    requested_category = detect_requested_category(words)

    if requested_category and row["category"] != requested_category:
        if requested_category == "Term Deposit" and row["category"] == "Time Frame Products":
            pass
        else:
            return 0

    score = 0
    row_words = row_field_words(
        row,
        "business_unit",
        "category",
        "product",
        "condition",
    )
    product_words = row_field_words(row, "product")
    category_words = row_field_words(row, "category")
    condition_words = row_field_words(row, "condition")

    if units:
        if row["business_unit"] == units[0]:
            score += 300
        elif row["business_unit"] in units:
            score += 220
        elif row["business_unit"] == "General":
            score += 40

    if row_product_phrase_in_query(row, query):
        score += 400

    for word in words:
        if word in GENERIC_RATE_WORDS:
            continue

        if word in product_words:
            score += 90
        elif word in condition_words:
            score += 55
        elif word in category_words:
            score += 45
        elif word in row_words:
            score += 20

    phrase_text = normalize_text(
        f"{row['business_unit']} {row['category']} {row['product']} "
        f"{row['condition']}"
    )

    for size in [4, 3, 2]:
        for index in range(0, len(words) - size + 1):
            phrase = " ".join(words[index:index + size])

            if phrase and phrase in phrase_text:
                score += size * 30

    if "dps" in words and row["category"] == "Recurring Deposit":
        score += 150

    if "fd" in words and row["category"] in {"Term Deposit", "Time Frame Products"}:
        score += 130

    if {"saving", "savings"} & set(words) and "saving" in row_words:
        score += 120

    if "snd" in words and "snd" in row_words:
        score += 150

    if "hpa" in words and "hpa" in row_words:
        score += 150

    return score


def specific_product_query_words(words):
    ignored_words = (
        GENERIC_RATE_WORDS
        | set(BUSINESS_UNIT_WORDS)
        | set(CATEGORY_WORDS)
        | {
            "all",
            "amount",
            "balance",
            "band",
            "day",
            "less",
            "lakh",
            "lac",
            "million",
            "month",
            "more",
            "than",
            "tenure",
            "up",
            "year",
        }
    )

    return [
        word
        for word in words
        if word not in ignored_words and not re.fullmatch(r"\d+(\.\d+)?", word)
    ]


def filter_rows_by_product_words(rows, words):
    if len(rows) <= 1:
        return rows

    specific_words = specific_product_query_words(words)

    if not specific_words:
        return rows

    product_matches = []

    for row in rows:
        product_words = row_field_words(row, "product")
        matched_words = [
            word
            for word in specific_words
            if word in product_words
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


def filter_rows_by_exact_product(rows, query):
    if len(rows) <= 1:
        return rows

    exact_rows = [
        row
        for row in rows
        if row_product_phrase_in_query(row, query)
    ]

    return exact_rows or rows


def filter_rows_by_short_product_context(rows, words):
    if len(rows) <= 1:
        return rows

    filtered_rows = rows

    for word in ["snd", "hpa"]:
        if word not in words:
            continue

        product_matches = [
            row
            for row in filtered_rows
            if word in row_field_words(row, "product")
        ]

        if product_matches:
            filtered_rows = product_matches

    if "bank" in words:
        bank_product_matches = [
            row
            for row in filtered_rows
            if "bank" in row_field_words(row, "product")
        ]

        if bank_product_matches:
            filtered_rows = bank_product_matches

    return filtered_rows


def duration_words(words):
    duration_units = {"day", "month", "year"}
    durations = []

    for index, word in enumerate(words[:-1]):
        if re.fullmatch(r"\d+(\.\d+)?", word) and words[index + 1] in duration_units:
            durations.append((word, words[index + 1]))

    return durations


def filter_rows_by_duration(rows, words):
    if len(rows) <= 1:
        return rows

    requested_durations = duration_words(words)

    if not requested_durations:
        return rows

    duration_matches = []

    for row in rows:
        row_words = tokenize(f"{row['product']} {row['condition']}")
        matched_count = 0

        for amount, unit in requested_durations:
            if amount in row_words and unit in row_words:
                matched_count += 1

        if matched_count:
            duration_matches.append((matched_count, row))

    if not duration_matches:
        return rows

    top_count = max(count for count, _ in duration_matches)

    return [
        row
        for count, row in duration_matches
        if count == top_count
    ]


def get_candidate_rows(query, limit=120):
    words = expand_words(tokenize(query))

    if not words or not is_deposit_rate_question(query):
        return []

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    create_deposit_rate_table(connection)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM deposit_rates")
    rows = [dict(row) for row in cursor.fetchall()]
    connection.close()

    scored_rows = [
        (score_rate_row(row, words, query), row)
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
        if score >= max(120, top_score * 0.70)
    ]

    selected_rows = filter_rows_by_exact_product(selected_rows, query)
    selected_rows = filter_rows_by_short_product_context(selected_rows, words)
    selected_rows = filter_rows_by_product_words(selected_rows, words)
    selected_rows = filter_rows_by_duration(selected_rows, words)

    return selected_rows[:limit]


def get_all_products():
    ensure_deposit_rate_database_ready()
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT product
        FROM deposit_rates
        GROUP BY product
        ORDER BY MIN(id)
    """)
    products = [row[0] for row in cursor.fetchall()]
    connection.close()
    return products


def unique_in_order(items):
    unique_items = []

    for item in items:
        if item and item not in unique_items:
            unique_items.append(item)

    return unique_items


def join_readable(items):
    items = [item for item in items if item]

    if len(items) <= 1:
        return "".join(items)

    if len(items) == 2:
        return f"{items[0]} and {items[1]}"

    return f"{', '.join(items[:-1])}, and {items[-1]}"


def is_broad_deposit_rate_question(query):
    words = expand_words(tokenize(query))
    specific_words = specific_product_query_words(words)

    return is_deposit_rate_question(query) and not specific_words


def build_broad_rate_clarification():
    return (
        "Please specify the deposit product or category: savings/CASA, "
        "SND/HPA, Retail FD, Commercial FD, Corporate FD, recurring deposit/DPS, "
        "or closed products."
    )


DEPOSIT_RATE_MENU_FILTERS = {
    "casa products": {
        "label": "CASA Products",
        "where": "category = ?",
        "params": ("CASA Products",),
    },
    "other casa products": {
        "label": "Other CASA Products",
        "where": "category = ?",
        "params": ("Other CASA / SND / HPA",),
    },
    "business unit retail": {
        "label": "Business Unit: Retail",
        "where": "business_unit = ? AND category IN (?, ?)",
        "params": ("Retail", "Term Deposit", "Time Frame Products"),
    },
    "business unit commercial": {
        "label": "Business Unit: Commercial",
        "where": "business_unit = ? AND category IN (?, ?)",
        "params": ("Commercial", "Term Deposit", "Time Frame Products"),
    },
    "business unit corporate": {
        "label": "Business Unit: Corporate",
        "where": "business_unit = ? AND category IN (?, ?)",
        "params": ("Corporate", "Term Deposit", "Time Frame Products"),
    },
    "recurring deposit": {
        "label": "Recurring Deposit",
        "where": "category = ?",
        "params": ("Recurring Deposit",),
    },
}


def get_deposit_rate_menu_option(query):
    normalized_query = normalize_text(query)

    if not normalized_query:
        return ""

    if {"rate", "rates", "interest"} & set(tokenize(query)):
        return ""

    aliases = {
        "casa": "casa products",
        "casa product": "casa products",
        "casa products": "casa products",
        "savings casa": "casa products",
        "savings casa products": "casa products",
        "other casa": "other casa products",
        "other casa product": "other casa products",
        "other casa products": "other casa products",
        "snd hpa": "other casa products",
        "business unit retail": "business unit retail",
        "retail business unit": "business unit retail",
        "retail deposit": "business unit retail",
        "business unit commercial": "business unit commercial",
        "commercial business unit": "business unit commercial",
        "commercial deposit": "business unit commercial",
        "business unit corporate": "business unit corporate",
        "corporate business unit": "business unit corporate",
        "corporate deposit": "business unit corporate",
        "recurring": "recurring deposit",
        "recurring deposit": "recurring deposit",
        "dps": "recurring deposit",
    }

    if normalized_query in aliases:
        return aliases[normalized_query]

    for alias, menu_key in aliases.items():
        if f" {alias} " in f" {normalized_query} ":
            return menu_key

    return ""


def get_products_for_deposit_rate_menu_option(menu_key):
    ensure_deposit_rate_database_ready()
    menu_filter = DEPOSIT_RATE_MENU_FILTERS.get(menu_key)

    if not menu_filter:
        return []

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    cursor.execute(f"""
        SELECT product
        FROM deposit_rates
        WHERE {menu_filter["where"]}
        GROUP BY product
        ORDER BY MIN(id)
    """, menu_filter["params"])
    products = [row[0] for row in cursor.fetchall()]
    connection.close()

    return products


DEPOSIT_MENU_ENTRY_LABELS = {
    "business unit retail": [
        "FD",
        "Extra Value FD",
        "EBL Super FD",
        "EBL Super FD Repeat",
        "EBL Super Repeat",
        "EBL Century",
    ],
    "business unit commercial": [
        "FD",
        "Extra Value FD",
        "EBL Super",
        "EBL Super Repeat",
        "EBL Century",
    ],
    "business unit corporate": [
        "FD",
        "Extra Value FD",
        "EBL ALO",
        "EBL High Value",
        "EBL Diamond Corp",
        "EBL Diamond Commercial",
        "EBL Repeat",
        "EBL Repeat Corp",
        "EBL Repeat Commercial",
        "EBL 50",
        "EBL Earn First",
        "EBL Earn First - SME",
    ],
}


DEPOSIT_PRODUCT_FAMILY_RULES = [
    {"key": "ebl_earn_first_sme", "label": "EBL Earn First - SME", "exact_products": ("EBL Earn First - SME",), "fallback_to_all_units": True, "fallback_units": ("Corporate",)},
    {"key": "ebl_diamond_commercial", "label": "EBL Diamond Commercial", "exact_products": ("EBL Diamond Commercial",), "fallback_to_all_units": True, "fallback_units": ("Corporate",)},
    {"key": "ebl_repeat_commercial", "label": "EBL Repeat Commercial", "exact_products": ("EBL Repeat Commercial",), "fallback_to_all_units": True, "fallback_units": ("Corporate",)},
    {"key": "ebl_diamond_corp", "label": "EBL Diamond Corp", "exact_products": ("EBL Diamond Corp",), "fallback_to_all_units": True},
    {"key": "ebl_repeat_corp", "label": "EBL Repeat Corp", "exact_products": ("EBL Repeat Corp",), "fallback_to_all_units": True},
    {"key": "extra_value_fd", "label": "Extra Value FD", "exact_products": ("Extra Value FD 1 Month", "Extra Value FD 3 Month", "Extra Value FD 3 Months", "Extra Value FD 6 Month", "Extra Value FD 6 Months", "Extra Value FD 1 Year")},
    {"key": "ebl_super_fd_repeat", "label": "EBL Super FD Repeat", "exact_products": ("EBL Super FD Repeat 189 Days", "EBL Super FD Repeat 369 Days")},
    {
        "key": "ebl_super_repeat",
        "label": "EBL Super Repeat",
        "exact_products": ("EBL Super 120 Days", "EBL Super Repeat 150 Days", "EBL Super Repeat 360 Days", "EBL Super 399 Days"),
        "exact_products_by_unit": {
            "Retail": ("EBL Super 120 Days", "EBL Super Repeat 150 Days", "EBL Super Repeat 360 Days", "EBL Super 399 Days"),
            "Commercial": ("EBL Super Repeat 150 Days", "EBL Super Repeat 360 Days"),
        },
    },
    {"key": "ebl_century", "label": "EBL Century", "exact_products": ("EBL Super Century", "EBL Super Double Century", "EBL Super Double Century Repeat")},
    {"key": "ebl_super_century", "label": "EBL Super Century", "exact_products": ("EBL Super Century", "EBL Super Double Century", "EBL Super Double Century Repeat")},
    {"key": "ebl_super_fd", "label": "EBL Super FD", "exact_products": ("EBL Super FD 99 Days", "EBL Super FD 189 Days", "EBL Super FD 369 Days", "EBL Super FD 3 Month", "EBL Super FD 6 Month")},
    {"key": "ebl_high_value", "label": "EBL High Value", "exact_products": ("EBL High Value",), "fallback_to_all_units": True, "fallback_units": ("Corporate",)},
    {"key": "ebl_earn_first", "label": "EBL Earn First", "exact_products": ("EBL Earn First",), "fallback_to_all_units": True, "fallback_units": ("Corporate",)},
    {"key": "ebl_repeat", "label": "EBL Repeat", "exact_products": ("EBL Repeat",), "fallback_to_all_units": True, "fallback_units": ("Corporate",)},
    {
        "key": "ebl_super",
        "label": "EBL Super",
        "exact_products_by_unit": {
            "Commercial": ("EBL Super 120 Days", "EBL Super 150 Days", "EBL Super 360 Days", "EBL Super 399 Days"),
        },
    },
    {"key": "ebl_alo", "label": "EBL ALO", "exact_products": ("EBL ALO",), "fallback_to_all_units": True, "fallback_units": ("Corporate",)},
    {"key": "ebl_50", "label": "EBL 50", "exact_products": ("EBL 50",), "fallback_to_all_units": True, "fallback_units": ("Corporate",)},
    {"key": "fd", "label": "FD", "exact_products": ("FD 1 Month", "FD 3 Month", "FD 3 Months", "FD 6 Month", "FD 6 Months", "FD 1 Year", "FD 2 Year", "FD 2 Years", "FD 3 Year", "FD 3 Years")},
]


DEPOSIT_PRODUCT_FAMILY_BY_KEY = {
    rule["key"]: rule
    for rule in DEPOSIT_PRODUCT_FAMILY_RULES
}


def normalize_family_phrase(text):
    return re.sub(r"[^a-z0-9.]+", " ", (text or "").lower()).strip()


def deposit_product_family(product):
    product_text = normalize_text(product)

    for rule in DEPOSIT_PRODUCT_FAMILY_RULES:
        if product_matches_deposit_family_rule(product_text, rule):
            return rule

    return None


def product_matches_deposit_family_rule(product_text, rule, business_unit=None):
    exact_products_by_unit = rule.get("exact_products_by_unit", {})
    exact_products = exact_products_by_unit.get(
        business_unit,
        rule.get("exact_products", ()),
    )

    if exact_products:
        exact_product_texts = {
            normalize_text(product)
            for product in exact_products
        }

        return product_text in exact_product_texts

    if rule["key"] == "extra_value_fd":
        return product_text.startswith("extra value fd")

    if rule["key"] == "ebl_super_repeat":
        return product_text.startswith("ebl super") and "repeat" in product_text

    if rule["key"] == "ebl_super_century":
        return (
            product_text.startswith("ebl super")
            and "century" in product_text
            and "repeat" not in product_text
        )

    if rule["key"] == "ebl_super_fd":
        return (
            product_text.startswith("ebl super fd")
            and "repeat" not in product_text
        )

    if rule["key"] == "ebl_super":
        return (
            product_text.startswith("ebl super")
            and "century" not in product_text
            and "repeat" not in product_text
            and not product_text.startswith("ebl super fd")
        )

    if rule["key"] == "fd":
        return product_text.startswith("fd ")

    return False


def get_deposit_rate_menu_entries(menu_key):
    fixed_entries = DEPOSIT_MENU_ENTRY_LABELS.get(menu_key)

    if fixed_entries:
        menu_filter = DEPOSIT_RATE_MENU_FILTERS.get(menu_key, {})
        menu_label = menu_filter.get("label", "")
        business_units = (
            [menu_filter["params"][0]]
            if menu_label.startswith("Business Unit:") and menu_filter.get("params")
            else []
        )
        entries = []

        for entry in fixed_entries:
            family = get_deposit_family_rule_for_query(entry)

            if business_units and family:
                if not get_rows_for_deposit_family(family["key"], business_units):
                    continue

            entries.append(entry)

        return entries

    products = get_products_for_deposit_rate_menu_option(menu_key)
    menu_filter = DEPOSIT_RATE_MENU_FILTERS.get(menu_key, {})
    menu_label = menu_filter.get("label", "")
    should_group_term_products = menu_label.startswith("Business Unit:")
    entries = []

    for product in products:
        family = deposit_product_family(product) if should_group_term_products else None
        label = family["label"] if family else product

        if label not in entries:
            entries.append(label)

    return entries


def get_deposit_family_rule_for_query(query):
    normalized_query = normalize_text(query)
    plain_query = normalize_family_phrase(query)

    if not normalized_query and not plain_query:
        return None

    for rule in DEPOSIT_PRODUCT_FAMILY_RULES:
        if (
            rule["key"] == "ebl_super"
            and (
                "century" in plain_query
                or "repeat" in plain_query
                or "ebl super fd" in plain_query
            )
        ):
            continue

        family_phrases = [
            rule["label"].lower(),
            *(rule.get("aliases", ())),
        ]

        for phrase in family_phrases:
            phrase_text = normalize_family_phrase(phrase)

            if phrase_text and (
                f" {phrase_text} " in f" {plain_query} "
                or f" {phrase_text} " in f" {normalized_query} "
            ):
                return rule

    return None


def deposit_rate_followup_context(rate_context, user_message):
    if not rate_context:
        return ""

    if get_deposit_family_rule_for_query(user_message):
        context_words = expand_words(tokenize(rate_context))
        business_units = requested_business_units(context_words)

        if business_units:
            return " ".join(business_units)

        return ""

    return rate_context


def get_rows_for_deposit_family(family_key, business_units=None):
    ensure_deposit_rate_database_ready()
    rule = DEPOSIT_PRODUCT_FAMILY_BY_KEY.get(family_key)

    if not rule:
        return []

    business_units = business_units or []
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    def fetch_rows(units):
        if units:
            placeholders = ", ".join("?" for _ in units)
            cursor.execute(f"""
                SELECT *
                FROM deposit_rates
                WHERE category IN ('Term Deposit', 'Time Frame Products')
                AND business_unit IN ({placeholders})
                ORDER BY id
            """, units)
        else:
            cursor.execute("""
                SELECT *
                FROM deposit_rates
                WHERE category IN ('Term Deposit', 'Time Frame Products')
                ORDER BY id
            """)

        return [
            dict(row)
            for row in cursor.fetchall()
            if product_matches_deposit_family_rule(
                normalize_text(row["product"]),
                rule,
                row["business_unit"],
            )
        ]

    rows = fetch_rows(business_units)

    if (
        not rows
        and business_units
        and rule.get("fallback_to_all_units")
        and business_units[0] in rule.get("fallback_units", ())
    ):
        rows = fetch_rows([])

        for row in rows:
            row["business_unit"] = business_units[0]

    connection.close()

    exact_products = rule.get("exact_products", ())
    exact_products_by_unit = rule.get("exact_products_by_unit", {})

    if business_units:
        exact_products = exact_products_by_unit.get(business_units[0], exact_products)

    if exact_products:
        product_order = {
            normalize_text(product): index
            for index, product in enumerate(exact_products)
        }

        rows.sort(
            key=lambda row: (
                product_order.get(normalize_text(row["product"]), len(product_order)),
                row["id"],
            )
        )

    return rows


def get_products_for_deposit_family(family_key, business_units=None):
    rows = get_rows_for_deposit_family(family_key, business_units)
    return unique_in_order(row["product"] for row in rows)


def family_label_count_in_query(rule, query):
    family_label = normalize_family_phrase(rule["label"])
    query_text = f" {normalize_family_phrase(query)} "

    if not family_label:
        return 0

    pattern = rf"(?=\s{re.escape(family_label)}\s)"

    return len(re.findall(pattern, query_text))


def matching_specific_family_products(query, products):
    return [
        product
        for product in products
        if product_phrase_in_query(product, query)
    ]


def build_deposit_product_family_reply(query):
    words = expand_words(tokenize(query))
    family = get_deposit_family_rule_for_query(query)

    if not family:
        return ""

    business_units = requested_business_units(words)
    rows = get_rows_for_deposit_family(family["key"], business_units)

    if query_has_specific_timeline(query):
        rows = filter_rows_by_duration(rows, words)

    products = unique_in_order(row["product"] for row in rows)

    if not rows:
        if business_units:
            return (
                f"I could not find {family['label']} under "
                f"{business_units[0]} deposit rates."
            )

        return ""

    matched_products = matching_specific_family_products(query, products)
    family_label_text = normalize_text(family["label"])

    if matched_products:
        is_family_label_match = (
            len(matched_products) == 1
            and normalize_text(matched_products[0]) == family_label_text
        )

        if not is_family_label_match or family_label_count_in_query(family, query) > 1:
            return ""

    if len(products) == 1:
        if should_show_timeline_selection(query, rows):
            row_business_units = unique_in_order(
                row["business_unit"]
                for row in rows
                if row["business_unit"] and row["business_unit"] != "General"
            )

            if (
                business_units
                and family.get("fallback_to_all_units")
                and row_business_units
                and not set(row_business_units) & set(business_units)
            ):
                return build_timeline_selection_reply_with_subject(
                    rows,
                    family["label"],
                )

            return build_timeline_selection_reply(rows)

        if len(rows) == 1:
            return format_single_row_answer(rows[0])

        return format_multi_row_answer(rows)

    subject_parts = []

    if len(business_units) == 1:
        subject_parts.append(business_units[0])

    subject_parts.append(family["label"])
    subject = " ".join(subject_parts)
    product_lines = "\n".join(
        f"- {product} rate"
        for product in products
    )

    return f"Which {subject} timeline do you want?\n\n{product_lines}"


def build_deposit_rate_menu_reply(query):
    menu_key = get_deposit_rate_menu_option(query)

    if not menu_key:
        return ""

    label = DEPOSIT_RATE_MENU_FILTERS[menu_key]["label"]
    products = get_deposit_rate_menu_entries(menu_key)

    if not products:
        return ""

    product_lines = "\n".join(
        f"- {product} rate"
        for product in products
    )

    return f"Which {label} deposit product rate do you want?\n\n{product_lines}"


def build_product_clarification(rows):
    products = unique_in_order(row["product"] for row in rows)

    if not products:
        return build_broad_rate_clarification()

    examples = ", ".join(products[:8])

    if len(products) > 8:
        examples = f"{examples}, ..."

    return f"Please specify the deposit product or tenure, for example: {examples}."


def deposit_category_quick_action_type(query):
    words = set(expand_words(tokenize(query)))

    if not query_has_rate_terms(words):
        return ""

    if "dps" in words or "recurring" in words:
        return "dps"

    if "fd" in words or "fixed" in words or "fdr" in words:
        return "retail_fd"

    if words & {"saving", "savings", "casa"}:
        return "savings"

    return ""


def get_products_for_deposit_category(category_type):
    ensure_deposit_rate_database_ready()

    filters = {
        "savings": ("Retail", "CASA Products"),
        "retail_fd": ("Retail", "Term Deposit"),
        "dps": ("Retail", "Recurring Deposit"),
    }
    selected_filter = filters.get(category_type)

    if not selected_filter:
        return []

    business_unit, category = selected_filter
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT product
        FROM deposit_rates
        WHERE business_unit = ?
        AND category = ?
        GROUP BY product
        ORDER BY MIN(id)
    """, (business_unit, category))
    products = [row[0] for row in cursor.fetchall()]
    connection.close()

    return products


def build_deposit_category_selection_reply(query):
    if query_mentions_known_deposit_rate_product(query):
        return ""

    category_type = deposit_category_quick_action_type(query)

    if not category_type:
        return ""

    label_by_type = {
        "savings": "Savings/CASA",
        "retail_fd": "Retail FD",
        "dps": "DPS/recurring deposit",
    }
    products = get_products_for_deposit_category(category_type)

    if not products:
        return ""

    product_lines = "\n".join(
        f"- {product} rate"
        for product in products
    )

    return (
        f"Which {label_by_type[category_type]} product rate do you want?\n\n"
        f"{product_lines}"
    )


def product_group_key(row):
    return normalize_text(row["product"])


def condition_heading_for_category(category):
    if category in {"Recurring Deposit", "Time Frame Products"}:
        return "Tenure"

    if category == "Term Deposit":
        return "Amount Band"

    if category in {"CASA Products", "Other CASA / SND / HPA"}:
        return "Balance / Band"

    return "Condition"


TIMELINE_CATEGORIES = {"Recurring Deposit", "Time Frame Products"}


def is_timeline_rate_row(row):
    return row["category"] in TIMELINE_CATEGORIES


def query_has_specific_timeline(query):
    words = expand_words(tokenize(query))

    return bool(duration_words(words))


def should_show_timeline_selection(query, rows):
    if len(rows) <= 1:
        return False

    product_keys = unique_in_order(product_group_key(row) for row in rows)

    if len(product_keys) != 1:
        return False

    if not all(is_timeline_rate_row(row) for row in rows):
        return False

    if query_has_specific_timeline(query):
        return False

    timelines = unique_in_order(row["condition"] for row in rows)

    return len(timelines) > 1


def build_timeline_selection_reply(rows):
    subject = subject_for_rows(rows)
    timeline_lines = "\n".join(
        f"- {subject} {condition} rate"
        for condition in unique_in_order(row["condition"] for row in rows)
    )

    return f"Which {subject} timeline do you want?\n\n{timeline_lines}"


def build_timeline_selection_reply_with_subject(rows, subject):
    timeline_lines = "\n".join(
        f"- {subject} {condition} rate"
        for condition in unique_in_order(row["condition"] for row in rows)
    )

    return f"Which {subject} timeline do you want?\n\n{timeline_lines}"


def subject_for_rows(rows):
    row = rows[0]
    product = row["product"].strip()
    business_unit = row["business_unit"].strip()
    business_units = unique_in_order(
        item["business_unit"].strip()
        for item in rows
        if item["business_unit"].strip() and item["business_unit"].strip() != "General"
    )

    if len(business_units) > 1:
        return product

    if business_unit and business_unit != "General":
        product_words = set(tokenize(product))
        unit_words = set(tokenize(business_unit))

        if not product_words & unit_words:
            return f"{business_unit} {product}"

    return product


def format_rate_table(rows):
    rows = sorted(rows, key=lambda row: row["id"])
    heading = condition_heading_for_category(rows[0]["category"])
    business_units = unique_in_order(
        row["business_unit"]
        for row in rows
        if row["business_unit"] and row["business_unit"] != "General"
    )
    show_business_unit = len(business_units) > 1

    if show_business_unit:
        lines = [
            f"| Business Unit | {heading} | Interest Rate |",
            "| --- | --- | --- |",
        ]
    else:
        lines = [
            f"| {heading} | Interest Rate |",
            "| --- | --- |",
        ]

    for row in rows:
        if show_business_unit:
            lines.append(
                f"| {row['business_unit']} | {row['condition']} | {row['rate']} |"
            )
        else:
            lines.append(f"| {row['condition']} | {row['rate']} |")

    return "\n".join(lines)


def format_single_row_answer(row):
    subject = subject_for_rows([row])
    note = row["note"].strip()
    answer = f"{subject} interest rate:\n{format_rate_table([row])}"

    if note:
        answer = f"{answer}\nNote: {note}"

    return answer


def format_multi_row_answer(rows):
    rows = sorted(rows, key=lambda row: row["id"])
    products = unique_in_order(row["product"] for row in rows)
    product_keys = unique_in_order(product_group_key(row) for row in rows)

    if len(product_keys) > 1:
        return build_product_clarification(rows)

    subject = subject_for_rows(rows)
    notes = unique_in_order(row["note"].strip() for row in rows if row["note"].strip())

    answer = f"{subject} interest rate:\n{format_rate_table(rows)}"

    if notes:
        answer = f"{answer}\nNote: {'; '.join(notes)}"

    return answer


def answer_deposit_rate_question_from_db(query):
    ensure_deposit_rate_database_ready()

    if not is_deposit_rate_question(query):
        return ""

    product_family_reply = build_deposit_product_family_reply(query)

    if product_family_reply:
        return product_family_reply

    category_selection_reply = build_deposit_category_selection_reply(query)

    if category_selection_reply:
        return category_selection_reply

    rows = get_candidate_rows(query)

    if not rows:
        if is_broad_deposit_rate_question(query):
            return build_broad_rate_clarification()

        return ""

    if len(rows) == 1:
        return format_single_row_answer(rows[0])

    if should_show_timeline_selection(query, rows):
        return build_timeline_selection_reply(rows)

    return format_multi_row_answer(rows)
