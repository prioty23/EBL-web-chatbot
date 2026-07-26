"""Structured lending interest rate database import and lookup."""

from pathlib import Path
import csv
import re
import sqlite3

from language_support import expand_bangla_banglish_text


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "EBL_chatbot.db"
LENDING_RATE_DATA_DIR = BASE_DIR / "lending_rate_data"


LENDING_RATE_COLUMNS = [
    "section",
    "category",
    "subcategory",
    "economic_purpose",
    "declared_rate",
    "lowest_rate",
    "highest_rate",
    "pdf_page",
    "source_file",
]


SHORT_WORDS = {
    "cc",
    "epz",
    "ir",
    "od",
    "pc",
    "pf",
    "tr",
}


GENERIC_LENDING_WORDS = {
    "about",
    "and",
    "bank",
    "banking",
    "can",
    "customer",
    "customers",
    "ebl",
    "eastern",
    "finance",
    "financing",
    "for",
    "give",
    "how",
    "i",
    "interest",
    "know",
    "lending",
    "loan",
    "loans",
    "may",
    "me",
    "my",
    "of",
    "or",
    "other",
    "others",
    "please",
    "plc",
    "rate",
    "rates",
    "show",
    "tell",
    "the",
    "to",
    "want",
    "what",
    "you",
}


LENDING_CONTEXT_WORDS = {
    "advance",
    "agriculture",
    "agricultural",
    "auto",
    "automobile",
    "car",
    "card",
    "commercial",
    "construction",
    "consumer",
    "credit",
    "education",
    "educational",
    "export",
    "flat",
    "home",
    "housing",
    "import",
    "industry",
    "lease",
    "lending",
    "loan",
    "loans",
    "mortgage",
    "personal",
    "professional",
    "rmg",
    "salary",
    "sme",
    "trade",
    "transport",
    "vehicle",
    "working",
}


_READY = False


def normalize_text(text):
    text = expand_bangla_banglish_text(text)
    text = (text or "").lower()
    replacements = {
        "&": " and ",
        "/": " ",
        "-": " ",
        "rmg": "ready made garments rmg",
        "ready-made": "ready made",
        "motorcycle": "motor cycle motorcycle",
        "automobiles": "automobile",
        "machineries": "machinery",
    }

    for original_text, replacement_text in replacements.items():
        text = text.replace(original_text, replacement_text)

    return re.sub(r"[^a-z0-9]+", " ", text).strip()


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

    if "home" in expanded or "mortgage" in expanded:
        add("flat")
        add("purchase")
        add("housing")

    if "auto" in expanded or "car" in expanded or "vehicle" in expanded:
        add("transport")
        add("motor")

    if "bike" in expanded or "motorcycle" in expanded:
        add("transport")
        add("motor")

    if "sme" in expanded:
        add("small")
        add("medium")

    if "student" in expanded or "edu" in expanded:
        add("educational")
        add("expenses")

    if "working" in expanded:
        add("capital")

    if "lc" in expanded:
        add("import")

    return expanded


def create_lending_rate_table(connection):
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lending_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section TEXT NOT NULL,
            category TEXT,
            subcategory TEXT,
            economic_purpose TEXT NOT NULL,
            declared_rate TEXT NOT NULL,
            lowest_rate TEXT NOT NULL,
            highest_rate TEXT NOT NULL,
            pdf_page TEXT,
            source_file TEXT NOT NULL,
            search_text TEXT NOT NULL
        )
    """)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_lending_rates_section "
        "ON lending_rates(section)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_lending_rates_category "
        "ON lending_rates(category)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_lending_rates_purpose "
        "ON lending_rates(economic_purpose)"
    )
    connection.commit()


def build_search_text(row):
    return normalize_text(
        " ".join(
            row.get(column, "")
            for column in [
                "section",
                "category",
                "subcategory",
                "economic_purpose",
                "declared_rate",
                "lowest_rate",
                "highest_rate",
            ]
        )
    )


def iter_lending_rate_csv_paths():
    if not LENDING_RATE_DATA_DIR.exists():
        return []

    return sorted(LENDING_RATE_DATA_DIR.glob("*.csv"))


def read_lending_rate_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        missing_columns = [
            column
            for column in LENDING_RATE_COLUMNS
            if column not in (reader.fieldnames or [])
        ]

        if missing_columns:
            raise ValueError(
                f"{path.name} is missing columns: {', '.join(missing_columns)}"
            )

        for line_number, row in enumerate(reader, start=2):
            clean_row = {
                column: (row.get(column) or "").strip()
                for column in LENDING_RATE_COLUMNS
            }
            required_missing = [
                column
                for column in [
                    "section",
                    "economic_purpose",
                    "declared_rate",
                    "lowest_rate",
                    "highest_rate",
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


def import_lending_rate_csvs(clear_existing=True):
    connection = sqlite3.connect(DATABASE_PATH)
    create_lending_rate_table(connection)
    cursor = connection.cursor()

    if clear_existing:
        cursor.execute("DELETE FROM lending_rates")

    inserted = 0

    for path in iter_lending_rate_csv_paths():
        for row in read_lending_rate_csv(path):
            cursor.execute("""
                INSERT INTO lending_rates (
                    section,
                    category,
                    subcategory,
                    economic_purpose,
                    declared_rate,
                    lowest_rate,
                    highest_rate,
                    pdf_page,
                    source_file,
                    search_text
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["section"],
                row["category"],
                row["subcategory"],
                row["economic_purpose"],
                row["declared_rate"],
                row["lowest_rate"],
                row["highest_rate"],
                row["pdf_page"],
                row["source_file"],
                build_search_text(row),
            ))
            inserted += 1

    connection.commit()
    connection.close()
    return inserted


def ensure_lending_rate_database_ready(force_import=False):
    global _READY

    if _READY and not force_import:
        return

    connection = sqlite3.connect(DATABASE_PATH)
    create_lending_rate_table(connection)
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM lending_rates")
    row_count = cursor.fetchone()[0]
    connection.close()

    if force_import or row_count == 0:
        import_lending_rate_csvs(clear_existing=True)

    _READY = True


def row_field_words(row, *field_names):
    return set(
        tokenize(
            " ".join(row[field_name] or "" for field_name in field_names)
        )
    )


def has_rate_terms(words):
    return bool({"interest", "rate", "rates", "lending"} & set(words))


def has_lending_context(words):
    return bool(set(words) & LENDING_CONTEXT_WORDS)


def is_lending_rate_question(query):
    words = expand_words(tokenize(query))

    if not words:
        return False

    if not has_rate_terms(words):
        return False

    return has_lending_context(words)


def query_has_any_phrase(query_text, phrases):
    return any(f" {normalize_text(phrase)} " in query_text for phrase in phrases)


def row_field_text(row, *field_names):
    return normalize_text(
        " ".join(row[field_name] or "" for field_name in field_names)
    )


def get_all_lending_rate_rows():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    create_lending_rate_table(connection)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM lending_rates")
    rows = [dict(row) for row in cursor.fetchall()]
    connection.close()
    return rows


def important_query_words(query):
    return [
        word
        for word in tokenize(query)
        if word not in GENERIC_LENDING_WORDS
    ]


def row_has_excepted_query_word(row, query_words):
    if "except" in query_words or "excluding" in query_words:
        return False

    purpose_text = row_field_text(row, "economic_purpose")

    return any(
        f"except {word}" in purpose_text
        for word in query_words
    )


def rows_matching_exact_lending_purpose(rows, query):
    query_words = important_query_words(query)

    if not query_words:
        return []

    query_word_set = set(query_words)

    if "rmg" in query_word_set and not (query_word_set & {"export", "import"}):
        rmg_rows = [
            row
            for row in rows
            if (
                "rmg" in row_field_words(row, "economic_purpose")
                or {"ready", "garment"} <= row_field_words(row, "economic_purpose")
            )
        ]

        if rmg_rows:
            return rmg_rows

    scored_rows = []

    for row in rows:
        if row_has_excepted_query_word(row, query_words):
            continue

        product_words = row_field_words(row, "subcategory", "economic_purpose")

        if not product_words:
            continue

        overlap = query_word_set & product_words

        if not overlap:
            continue

        query_coverage = len(overlap) / len(query_word_set)
        product_coverage = len(overlap) / len(product_words)

        if query_coverage < 1 and product_coverage < 1:
            continue

        if max(query_coverage, product_coverage) < 0.50:
            continue

        score = int(query_coverage * 100) + int(product_coverage * 100)
        scored_rows.append((score, row))

    if not scored_rows:
        return []

    top_score = max(score for score, _row in scored_rows)
    return [
        row
        for score, row in scored_rows
        if score == top_score
    ]


def rows_where_field_contains(rows, field_names, phrase):
    phrase = normalize_text(phrase)
    return [
        row
        for row in rows
        if phrase in row_field_text(row, *field_names)
    ]


def rows_where_category_heading_contains(rows, phrase):
    phrase = normalize_text(phrase)
    matched_rows = []

    for row in rows:
        category_text = row_field_text(row, "category")

        if phrase not in category_text:
            continue

        if "excluding" in category_text:
            continue

        matched_rows.append(row)

    return matched_rows


def narrow_rows_by_extra_words(rows, query, anchor_words):
    words = [
        word
        for word in expand_words(tokenize(query))
        if word not in GENERIC_LENDING_WORDS and word not in anchor_words
    ]

    if not words:
        return rows

    scored_rows = []

    for row in rows:
        purpose_text = row_field_text(row, "subcategory", "economic_purpose")
        purpose_words = row_field_words(row, "subcategory", "economic_purpose")
        score = sum(
            1
            for word in words
            if word in purpose_words and f"except {word}" not in purpose_text
        )

        if score:
            scored_rows.append((score, row))

    if not scored_rows:
        return rows

    top_score = max(score for score, _row in scored_rows)
    return [
        row
        for score, row in scored_rows
        if score == top_score
    ]


def rows_matching_specific_lending_targets(rows, query):
    query_text = f" {normalize_text(query)} "
    query_words = set(expand_words(tokenize(query)))

    product_rules = [
        (
            {"home", "mortgage"},
            ["home loan", "mortgage", "flat purchase"],
            "economic_purpose",
            "flat purchase",
        ),
        (
            {"renovation", "repair", "extension"},
            ["house renovation", "home renovation", "house repair"],
            "economic_purpose",
            "house renovation",
        ),
        (
            {"auto", "car", "vehicle", "motorcycle", "bike"},
            [
                "auto loan",
                "car loan",
                "vehicle loan",
                "motorcycle loan",
                "bike loan",
                "transport loan",
            ],
            "economic_purpose",
            "transport loan",
        ),
        (
            {"card"},
            ["credit card", "card interest"],
            "economic_purpose",
            "credit cards",
        ),
        (
            {"dps"},
            ["dps"],
            "economic_purpose",
            "personal loan against dps",
        ),
        (
            {"fdr", "fd", "fixed"},
            ["fdr", "fixed deposit"],
            "economic_purpose",
            "personal loan against fdr",
        ),
        (
            {"salary"},
            ["salary"],
            "economic_purpose",
            "loan against salary",
        ),
        (
            {"pf"},
            ["provident fund"],
            "economic_purpose",
            "loan against pf",
        ),
        (
            {"education", "educational", "student", "edu"},
            ["education", "educational", "student"],
            "economic_purpose",
            "educational expenses",
        ),
        (
            {"doctor", "professional"},
            ["doctor", "professional"],
            "economic_purpose",
            "doctors loan professional loans",
        ),
        (
            {"consumer", "goods"},
            ["consumer goods"],
            "economic_purpose",
            "consumer goods",
        ),
        (
            {"travel", "travelling", "holiday"},
            ["travel", "travelling", "holiday"],
            "economic_purpose",
            "travelling holiday loan",
        ),
        (
            {"treatment", "medical"},
            ["treatment", "medical"],
            "economic_purpose",
            "treatment expenses",
        ),
        (
            {"marriage"},
            ["marriage"],
            "economic_purpose",
            "marriage expenses",
        ),
        (
            {"land"},
            ["land purchase"],
            "economic_purpose",
            "land purchase",
        ),
        (
            {"personal"},
            ["personal loan"],
            "economic_purpose",
            "other personal loans",
        ),
        (
            {"sme"},
            ["sme loan", "small and medium"],
            "economic_purpose",
            "small and medium industries",
        ),
    ]

    for word_set, phrases, field_name, target in product_rules:
        if query_words & word_set or query_has_any_phrase(query_text, phrases):
            matched_rows = rows_where_field_contains(rows, [field_name], target)

            if matched_rows:
                return matched_rows

    category_rules = [
        (
            {"export", "pc", "ecc"},
            ["export financing"],
            "category",
            "export financing",
            {"export", "financing", "pc", "ecc"},
        ),
        (
            {"import", "lim", "ltr", "tr", "lc"},
            ["import financing"],
            "category",
            "import financing",
            {"import", "financing", "lim", "ltr", "tr", "lc"},
        ),
        (
            {"working", "capital"},
            ["working capital"],
            "category",
            "working capital financing",
            {"working", "capital", "financing"},
        ),
        (
            {"term"},
            ["term loan"],
            "category",
            "term loan",
            {"term", "loan"},
        ),
        (
            {"wholesale"},
            ["wholesale trade", "retail trade"],
            "category",
            "wholesale and retail trade",
            {"wholesale", "retail", "trade"},
        ),
        (
            {"procurement", "government"},
            ["government procurement", "procurement by government"],
            "category",
            "procurement by government",
            {"procurement", "government"},
        ),
        (
            {"lease", "leasing"},
            ["lease financing", "leasing"],
            "category",
            "lease financing",
            {"lease", "leasing", "financing"},
        ),
        (
            {"agriculture", "agricultural"},
            ["agriculture"],
            "category",
            "agriculture",
            {"agriculture", "agricultural"},
        ),
        (
            {"fishing"},
            ["fishing"],
            "category",
            "fishing",
            {"fishing"},
        ),
        (
            {"forestry", "logging"},
            ["forestry", "logging"],
            "category",
            "forestry and logging",
            {"forestry", "logging"},
        ),
        (
            {"financial", "nbfi", "insurance", "ngo", "merchant", "cooperative"},
            ["financial corporation", "nbfi", "insurance", "merchant bank"],
            "section",
            "other institutional loan",
            {"financial", "corporation", "institutional", "loan"},
        ),
        (
            {"construction"},
            ["construction"],
            "section",
            "construction",
            {"construction"},
        ),
        (
            {"industry", "industrial"},
            ["industry"],
            "section",
            "industry",
            {"industry", "industrial"},
        ),
        (
            {"transport"},
            ["transport"],
            "section",
            "transport",
            {"transport"},
        ),
        (
            {"trade", "commerce"},
            ["trade and commerce", "trade", "commerce"],
            "section",
            "trade and commerce",
            {"trade", "commerce"},
        ),
        (
            {"consumer"},
            ["consumer finance"],
            "section",
            "consumer finance",
            {"consumer", "finance"},
        ),
        (
            {"miscellaneous", "poverty", "welfare", "development"},
            ["miscellaneous", "poverty alleviation"],
            "section",
            "miscellaneous",
            {"miscellaneous"},
        ),
    ]

    for word_set, phrases, field_name, target, anchor_words in category_rules:
        if query_words & word_set or query_has_any_phrase(query_text, phrases):
            if field_name == "category" and target in {
                "export financing",
                "import financing",
            }:
                matched_rows = rows_where_category_heading_contains(rows, target)
            else:
                matched_rows = rows_where_field_contains(rows, [field_name], target)

            if matched_rows:
                return narrow_rows_by_extra_words(
                    matched_rows,
                    query,
                    anchor_words,
                )

    return []


def score_lending_rate_row(row, words):
    row_words = row_field_words(
        row,
        "section",
        "category",
        "subcategory",
        "economic_purpose",
    )
    purpose_words = row_field_words(row, "economic_purpose")
    category_words = row_field_words(row, "category", "subcategory")
    section_words = row_field_words(row, "section")

    score = 0

    for word in words:
        if word in GENERIC_LENDING_WORDS:
            continue

        if word in purpose_words:
            score += 95
        elif word in category_words:
            score += 65
        elif word in section_words:
            score += 50
        elif word in row_words:
            score += 25

    phrase_text = normalize_text(
        f"{row['section']} {row['category']} {row['subcategory']} "
        f"{row['economic_purpose']}"
    )

    for size in [4, 3, 2]:
        for index in range(0, len(words) - size + 1):
            phrase = " ".join(words[index:index + size])

            if phrase and phrase in phrase_text:
                score += size * 35

    return score


def get_candidate_rows(query, limit=40):
    words = expand_words(tokenize(query))

    if not words:
        return []

    rows = get_all_lending_rate_rows()

    exact_rows = (
        rows_matching_exact_lending_purpose(rows, query)
        if has_rate_terms(words)
        else []
    )

    if exact_rows:
        return exact_rows[:limit]

    if not is_lending_rate_question(query):
        return []

    alias_rows = rows_matching_specific_lending_targets(rows, query)

    if alias_rows:
        return alias_rows[:limit]

    scored_rows = [
        (score_lending_rate_row(row, words), row)
        for row in rows
    ]
    scored_rows = [
        (score, row)
        for score, row in scored_rows
        if score >= 100
    ]
    scored_rows.sort(key=lambda item: item[0], reverse=True)

    if not scored_rows:
        return []

    top_score = scored_rows[0][0]
    selected_rows = [
        row
        for score, row in scored_rows
        if score >= max(100, top_score * 0.70)
    ]

    return selected_rows[:limit]


def unique_in_order(items):
    unique_items = []

    for item in items:
        if item and item not in unique_items:
            unique_items.append(item)

    return unique_items


def build_broad_lending_rate_clarification():
    return (
        "Which lending product rate do you want to know? Please type the product, "
        "for example Home Loan, Personal Loan, Auto Loan, SME Loan, Agriculture, "
        "Import Financing, Export Financing, or Credit Card."
    )


def format_lending_rate_table(rows):
    rows = sorted(rows, key=lambda row: row["id"])
    lines = [
        "| Economic Purpose | Declared Rate | Lowest Rate | Highest Rate |",
        "| --- | --- | --- | --- |",
    ]

    for row in rows:
        lines.append(
            f"| {row['economic_purpose']} | {row['declared_rate']} | "
            f"{row['lowest_rate']} | {row['highest_rate']} |"
        )

    return "\n".join(lines)


def format_single_row_answer(row):
    return (
        f"{row['economic_purpose']} lending rate:\n"
        f"{format_lending_rate_table([row])}"
    )


def format_multi_row_answer(rows):
    return f"Lending rate:\n{format_lending_rate_table(rows)}"


def answer_lending_rate_question_from_db(query):
    ensure_lending_rate_database_ready()

    rows = get_candidate_rows(query)

    if not rows:
        if not is_lending_rate_question(query):
            return ""

        return build_broad_lending_rate_clarification()

    if len(rows) == 1:
        return format_single_row_answer(rows[0])

    return format_multi_row_answer(rows)
