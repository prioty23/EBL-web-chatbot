"""EBL branch database helpers for Locate Us."""

from pathlib import Path
import re
import sqlite3

from language_support import expand_bangla_banglish_text


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "EBL_chatbot.db"
BRANCH_SOURCE_URL = "https://www.ebl.com.bd/branches"
BRANCH_AREA_PROMPT = (
    "Please tell me your Dhaka area, for example Gulshan, Mirpur, "
    "Dhanmondi, Motijheel, or Uttara."
)


BRANCH_QUERY_STOP_WORDS = {
    "a",
    "about",
    "address",
    "am",
    "ami",
    "an",
    "and",
    "area",
    "bank",
    "branch",
    "branches",
    "brance",
    "dhaka",
    "ebl",
    "eastern",
    "find",
    "for",
    "give",
    "his",
    "i",
    "in",
    "is",
    "koi",
    "kothay",
    "locate",
    "location",
    "me",
    "near",
    "nearest",
    "of",
    "plc",
    "please",
    "show",
    "the",
    "to",
    "us",
    "want",
    "where",
}


GENERIC_BRANCH_KEYWORDS = {
    "address",
    "avenue",
    "bank",
    "branch",
    "building",
    "c",
    "center",
    "centre",
    "complex",
    "floor",
    "holding",
    "house",
    "level",
    "limited",
    "ltd",
    "main",
    "no",
    "plaza",
    "plot",
    "road",
    "shop",
    "shopping",
    "tower",
}


def create_branch_table():
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS branches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            district TEXT NOT NULL,
            branch_name TEXT NOT NULL,
            address TEXT NOT NULL,
            routing_no TEXT,
            phone_email TEXT,
            area_keywords TEXT,
            source_url TEXT,
            updated_at TEXT,
            search_text TEXT NOT NULL
        )
    """)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_branches_district "
        "ON branches(district)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_branches_name "
        "ON branches(branch_name)"
    )

    existing_columns = [
        column[1]
        for column in cursor.execute("PRAGMA table_info(branches)").fetchall()
    ]

    for column_name, column_type in [
        ("source_url", "TEXT"),
        ("updated_at", "TEXT"),
        ("search_text", "TEXT"),
    ]:
        if column_name not in existing_columns:
            cursor.execute(
                f"ALTER TABLE branches ADD COLUMN {column_name} {column_type}"
            )

    connection.commit()
    connection.close()


def normalize_branch_text(text):
    text = expand_bangla_banglish_text(text or "")
    text = text.lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def branch_tokens(text):
    tokens = []

    for token in normalize_branch_text(text).split():
        if len(token) <= 1:
            continue

        if token not in tokens:
            tokens.append(token)

    return tokens


def clean_branch_field(value):
    return " ".join((value or "").replace("\xa0", " ").split())


def build_area_keywords(branch):
    base_text = " ".join([
        branch.get("branch_name", ""),
        branch.get("address", ""),
        branch.get("district", ""),
    ])
    keywords = []

    for token in branch_tokens(base_text):
        if token in GENERIC_BRANCH_KEYWORDS:
            continue

        if token.isdigit():
            continue

        keywords.append(token)

    return " ".join(keywords)


def build_branch_search_text(branch):
    return normalize_branch_text(
        " ".join([
            branch.get("district", ""),
            branch.get("branch_name", ""),
            branch.get("address", ""),
            branch.get("routing_no", ""),
            branch.get("phone_email", ""),
            branch.get("area_keywords", ""),
        ])
    )


def save_branches(branches, district="Dhaka", source_url=BRANCH_SOURCE_URL):
    create_branch_table()

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM branches WHERE lower(district) = lower(?)",
        (district,),
    )

    for branch in branches:
        clean_branch = {
            "district": clean_branch_field(branch.get("district", district)),
            "branch_name": clean_branch_field(branch.get("branch_name", "")),
            "address": clean_branch_field(branch.get("address", "")),
            "routing_no": clean_branch_field(branch.get("routing_no", "")),
            "phone_email": clean_branch_field(branch.get("phone_email", "")),
            "area_keywords": clean_branch_field(branch.get("area_keywords", "")),
            "updated_at": clean_branch_field(branch.get("updated_at", "")),
        }

        if not clean_branch["area_keywords"]:
            clean_branch["area_keywords"] = build_area_keywords(clean_branch)

        clean_branch["search_text"] = build_branch_search_text(clean_branch)

        if not clean_branch["branch_name"] or not clean_branch["address"]:
            continue

        cursor.execute("""
            INSERT INTO branches (
                district,
                branch_name,
                address,
                routing_no,
                phone_email,
                area_keywords,
                source_url,
                updated_at,
                search_text
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            clean_branch["district"],
            clean_branch["branch_name"],
            clean_branch["address"],
            clean_branch["routing_no"],
            clean_branch["phone_email"],
            clean_branch["area_keywords"],
            source_url,
            clean_branch["updated_at"],
            clean_branch["search_text"],
        ))

    connection.commit()
    connection.close()


def dhaka_branch_count():
    create_branch_table()

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM branches WHERE lower(district) = 'dhaka'"
    )
    count = cursor.fetchone()[0]
    connection.close()
    return count


def ensure_branch_database_ready(auto_scrape=False):
    create_branch_table()

    if dhaka_branch_count() > 0 or not auto_scrape:
        return

    try:
        from branch_scraper import refresh_dhaka_branches

        refresh_dhaka_branches()
    except Exception:
        return


def extract_branch_query_terms(query):
    tokens = []

    for token in branch_tokens(query):
        if token in BRANCH_QUERY_STOP_WORDS:
            continue

        if token not in tokens:
            tokens.append(token)

    return tokens


def row_to_branch(row):
    return {
        "id": row[0],
        "district": row[1],
        "branch_name": row[2],
        "address": row[3],
        "routing_no": row[4],
        "phone_email": row[5],
        "area_keywords": row[6],
        "source_url": row[7],
        "updated_at": row[8],
        "search_text": row[9],
    }


def score_branch(branch, query_terms, normalized_query):
    search_text = branch["search_text"] or ""
    branch_name = normalize_branch_text(branch["branch_name"])
    address = normalize_branch_text(branch["address"])
    keywords = normalize_branch_text(branch["area_keywords"])
    score = 0

    if normalized_query and normalized_query in search_text:
        score += 40

    for term in query_terms:
        if term in branch_name:
            score += 35

        if term in keywords:
            score += 30

        if term in address:
            score += 20

        if f" {term} " in f" {search_text} ":
            score += 10

    return score


def get_first_dhaka_branches(limit=5):
    create_branch_table()

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id, district, branch_name, address, routing_no, phone_email,
               area_keywords, source_url, updated_at, search_text
        FROM branches
        WHERE lower(district) = 'dhaka'
        ORDER BY id
        LIMIT ?
    """, (limit,))
    branches = [row_to_branch(row) for row in cursor.fetchall()]
    connection.close()
    return branches


def search_dhaka_branches(query, limit=3):
    ensure_branch_database_ready(auto_scrape=True)
    query_terms = extract_branch_query_terms(query)

    if not query_terms:
        return []

    normalized_query = normalize_branch_text(" ".join(query_terms))
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id, district, branch_name, address, routing_no, phone_email,
               area_keywords, source_url, updated_at, search_text
        FROM branches
        WHERE lower(district) = 'dhaka'
    """)
    branches = [row_to_branch(row) for row in cursor.fetchall()]
    connection.close()

    scored_branches = []

    for branch in branches:
        score = score_branch(branch, query_terms, normalized_query)

        if score > 0:
            scored_branches.append((score, branch))

    scored_branches.sort(
        key=lambda item: (-item[0], item[1]["branch_name"].lower())
    )

    return [branch for _, branch in scored_branches[:limit]]


def format_branch_reply(branches, area_query):
    if not branches:
        return (
            "I could not find a matching EBL branch in Dhaka for that area. "
            "Please try another nearby area such as Gulshan, Mirpur, "
            "Dhanmondi, Motijheel, Uttara or Banani."
        )

    area_terms = extract_branch_query_terms(area_query)
    area_label = " ".join(area_terms).title() if area_terms else "your area"
    lines = [f"EBL Dhaka branches matching {area_label}:"]

    for index, branch in enumerate(branches, start=1):
        lines.extend([
            "",
            f"{index}. {branch['branch_name']}",
            f"Address: {branch['address']}",
        ])

        if branch["routing_no"]:
            lines.append(f"Routing No.: {branch['routing_no']}")

        if branch["phone_email"]:
            lines.append(f"Phone & Email: {branch['phone_email']}")

    lines.extend([
        "",
        BRANCH_SOURCE_URL,
    ])

    return "\n".join(lines)


def build_dhaka_branch_reply(query):
    ensure_branch_database_ready(auto_scrape=True)
    branches = search_dhaka_branches(query)
    return format_branch_reply(branches, query)
