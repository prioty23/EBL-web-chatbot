"""EBL branch database helpers for Locate Us."""

from pathlib import Path
import re
import sqlite3

from language_support import expand_bangla_banglish_text


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "EBL_chatbot.db"
BRANCH_SOURCE_URL = "https://www.ebl.com.bd/branches"
BRANCH_SUPPORTED_DISTRICTS = tuple(sorted((
    "Bagerhat",
    "Barishal",
    "Bogura",
    "Brahmanbaria",
    "Dhaka",
    "Chattogram",
    "Cox's Bazar",
    "Cumilla",
    "Faridpur",
    "Feni",
    "Gazipur",
    "Jashore",
    "Kishoreganj",
    "Khulna",
    "Moulvibazar",
    "Mymensingh",
    "Narayanganj",
    "Narsingdi",
    "Noakhali",
    "Rajshahi",
    "Rangpur",
    "Sylhet",
    "Tangail",
)))
BRANCH_DISTRICT_MENU_REPLY = "Which district branch do you want to locate?"
BRANCH_DISTRICT_QUICK_ACTIONS = list(BRANCH_SUPPORTED_DISTRICTS)
BRANCH_SUPPORTED_DISTRICT_LABEL = ", ".join(BRANCH_SUPPORTED_DISTRICTS[:-1]) + (
    f" or {BRANCH_SUPPORTED_DISTRICTS[-1]}"
)
BRANCH_AREA_PROMPT = (
    "Please tell me your district or area, for example Gulshan in Dhaka, "
    "Agrabad in Chattogram, Cox's Bazar Sadar in Cox's Bazar, "
    "Board Bazar in Gazipur, Fulbarigate in Khulna, "
    "Sonargaon in Narayanganj, Maijdee in Noakhali, or Upashahar in Sylhet."
)
BRANCH_DISTRICT_ALIASES = {
    "bagerhat": "Bagerhat",
    "bagherhat": "Bagerhat",
    "barisal": "Barishal",
    "barishal": "Barishal",
    "bogra": "Bogura",
    "bogura": "Bogura",
    "brahman baria": "Brahmanbaria",
    "brahmanbaria": "Brahmanbaria",
    "brahmonbaria": "Brahmanbaria",
    "dhaka": "Dhaka",
    "dacca": "Dhaka",
    "chattogram": "Chattogram",
    "chattagram": "Chattogram",
    "chittagong": "Chattogram",
    "ctg": "Chattogram",
    "cox bazar": "Cox's Bazar",
    "cox s bazar": "Cox's Bazar",
    "coxsbazar": "Cox's Bazar",
    "coxs bazar": "Cox's Bazar",
    "cumilla": "Cumilla",
    "comilla": "Cumilla",
    "faridpur": "Faridpur",
    "feni": "Feni",
    "gajipur": "Gazipur",
    "gazipur": "Gazipur",
    "gazipore": "Gazipur",
    "jashore": "Jashore",
    "jessore": "Jashore",
    "kishoreganj": "Kishoreganj",
    "kishorganj": "Kishoreganj",
    "khulna": "Khulna",
    "kulna": "Khulna",
    "maulvibazar": "Moulvibazar",
    "moulavi bazar": "Moulvibazar",
    "moulvibazar": "Moulvibazar",
    "mymensing": "Mymensingh",
    "mymensingh": "Mymensingh",
    "narayanganj": "Narayanganj",
    "narayangonj": "Narayanganj",
    "narayagonj": "Narayanganj",
    "nganj": "Narayanganj",
    "narsingdi": "Narsingdi",
    "narsingdhi": "Narsingdi",
    "noakhali": "Noakhali",
    "noakali": "Noakhali",
    "noakhally": "Noakhali",
    "rajshahi": "Rajshahi",
    "rangpur": "Rangpur",
    "silet": "Sylhet",
    "sylhet": "Sylhet",
    "sylhett": "Sylhet",
    "tangail": "Tangail",
}


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
    "bagerhat",
    "bagherhat",
    "barisal",
    "barishal",
    "bogra",
    "bogura",
    "brahman",
    "brahmanbaria",
    "brahmonbaria",
    "chattogram",
    "chattagram",
    "chittagong",
    "comilla",
    "cox",
    "coxs",
    "coxsbazar",
    "ctg",
    "cumilla",
    "dhaka",
    "ebl",
    "eastern",
    "faridpur",
    "feni",
    "find",
    "for",
    "gajipur",
    "gazipur",
    "gazipore",
    "give",
    "his",
    "i",
    "in",
    "is",
    "jashore",
    "jessore",
    "kishoreganj",
    "kishorganj",
    "khulna",
    "koi",
    "kothay",
    "kulna",
    "locate",
    "location",
    "maulvibazar",
    "me",
    "moulavi",
    "moulvibazar",
    "mymensing",
    "mymensingh",
    "narayanganj",
    "narayagonj",
    "narayangonj",
    "narsingdi",
    "narsingdhi",
    "near",
    "nearest",
    "nganj",
    "noakhali",
    "noakali",
    "noakhally",
    "of",
    "plc",
    "please",
    "rajshahi",
    "rangpur",
    "show",
    "silet",
    "sylhet",
    "sylhett",
    "tangail",
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


def canonical_branch_district(district):
    cleaned_district = clean_branch_field(district)
    normalized_district = normalize_branch_text(cleaned_district)

    return BRANCH_DISTRICT_ALIASES.get(
        normalized_district,
        cleaned_district,
    )


def branch_districts_from_query(query):
    normalized_query = normalize_branch_text(query)
    query_tokens = set(normalized_query.split())
    districts = []

    for alias, district in BRANCH_DISTRICT_ALIASES.items():
        alias_tokens = alias.split()
        alias_found = (
            alias in query_tokens
            if len(alias_tokens) == 1
            else f" {alias} " in f" {normalized_query} "
        )

        if alias_found and district not in districts:
            districts.append(district)

    return districts


def branch_district_from_query(query):
    districts = branch_districts_from_query(query)

    return districts[0] if districts else ""


def branch_area_prompt(district):
    district = canonical_branch_district(district)
    example_area = {
        "Bagerhat": "Mongla",
        "Barishal": "Barishal Branch",
        "Bogura": "Bogura Branch",
        "Brahmanbaria": "Brahmanbaria Branch",
        "Dhaka": "Gulshan",
        "Chattogram": "Agrabad",
        "Cox's Bazar": "Cox's Bazar Branch",
        "Cumilla": "Cumilla SME-AGRI Branch",
        "Faridpur": "Faridpur Branch",
        "Feni": "Feni SME-AGRI Branch",
        "Gazipur": "Board Bazar",
        "Jashore": "Jashore Branch",
        "Kishoreganj": "Bhairab",
        "Khulna": "Fulbarigate",
        "Moulvibazar": "Moulvibazar Branch",
        "Mymensingh": "Mymensingh SME-AGRI Branch",
        "Narayanganj": "Sonargaon",
        "Narsingdi": "Madhabdi",
        "Noakhali": "Maijdee",
        "Rajshahi": "Rajshahi Branch",
        "Rangpur": "Rangpur Branch",
        "Sylhet": "Upashahar",
        "Tangail": "Tangail Branch",
    }.get(district, "Gulshan")

    return f"Please tell me your area, for example {example_area} in {district}."


def is_branch_area_prompt(reply):
    if reply == BRANCH_AREA_PROMPT:
        return True

    return (
        reply.startswith("Please tell me your area, for example ")
        and any(district in reply for district in BRANCH_SUPPORTED_DISTRICTS)
    )


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
    district = canonical_branch_district(district)

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM branches WHERE lower(district) = lower(?)",
        (district,),
    )

    for branch in branches:
        clean_branch = {
            "district": canonical_branch_district(branch.get("district", district)),
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


def branch_count(district):
    create_branch_table()
    district = canonical_branch_district(district)

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM branches WHERE lower(district) = lower(?)",
        (district,),
    )
    count = cursor.fetchone()[0]
    connection.close()
    return count


def dhaka_branch_count():
    return branch_count("Dhaka")


def supported_branch_counts():
    return {
        district: branch_count(district)
        for district in BRANCH_SUPPORTED_DISTRICTS
    }


def ensure_branch_database_ready(auto_scrape=False):
    create_branch_table()
    missing_districts = [
        district
        for district in BRANCH_SUPPORTED_DISTRICTS
        if branch_count(district) == 0
    ]

    if not missing_districts or not auto_scrape:
        return

    try:
        from branch_scraper import refresh_supported_branches

        refresh_supported_branches(districts=missing_districts)
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


def get_first_branches(district, limit=5):
    create_branch_table()
    district = canonical_branch_district(district)

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id, district, branch_name, address, routing_no, phone_email,
               area_keywords, source_url, updated_at, search_text
        FROM branches
        WHERE lower(district) = lower(?)
        ORDER BY lower(branch_name), id
        LIMIT ?
    """, (district, limit))
    branches = [row_to_branch(row) for row in cursor.fetchall()]
    connection.close()
    return branches


def get_first_dhaka_branches(limit=5):
    return get_first_branches("Dhaka", limit=limit)


def search_branches(query, limit=3):
    ensure_branch_database_ready(auto_scrape=True)
    query_terms = extract_branch_query_terms(query)
    requested_districts = branch_districts_from_query(query)

    if not query_terms and requested_districts:
        return get_first_branches(requested_districts[0], limit=limit)

    if not query_terms:
        return []

    normalized_query = normalize_branch_text(" ".join(query_terms))
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id, district, branch_name, address, routing_no, phone_email,
               area_keywords, source_url, updated_at, search_text
        FROM branches
    """)
    branches = [row_to_branch(row) for row in cursor.fetchall()]
    connection.close()

    scored_branches = []

    for branch in branches:
        if requested_districts and branch["district"] not in requested_districts:
            continue

        score = score_branch(branch, query_terms, normalized_query)

        if score > 0:
            scored_branches.append((score, branch))

    scored_branches.sort(
        key=lambda item: (-item[0], item[1]["branch_name"].lower())
    )

    return [branch for _, branch in scored_branches[:limit]]


def search_dhaka_branches(query, limit=3):
    return search_branches(f"Dhaka {query}", limit=limit)


def branch_table_cell(value):
    return " ".join(str(value or "N/A").split()).replace("|", "/")


def format_branch_reply(branches, area_query):
    if not branches:
        requested_districts = branch_districts_from_query(area_query)
        district_hint = (
            requested_districts[0]
            if requested_districts
            else BRANCH_SUPPORTED_DISTRICT_LABEL
        )

        return (
            f"I could not find a matching EBL branch in {district_hint} for that area. "
            "Please try another nearby area or district."
        )

    area_terms = extract_branch_query_terms(area_query)
    area_label = " ".join(area_terms).title() if area_terms else "your area"
    branch_districts = sorted({branch["district"] for branch in branches})

    if len(branch_districts) == 1:
        lines = [f"EBL {branch_districts[0]} branches matching {area_label}:"]
    else:
        lines = [f"EBL branches matching {area_label}:"]

    lines.extend([
        "",
        "| Branch | Address | Routing No. | Phone & Email |",
        "| --- | --- | --- | --- |",
    ])

    for branch in branches:
        lines.append(
            f"| {branch_table_cell(branch['branch_name'])} | "
            f"{branch_table_cell(branch['address'])} | "
            f"{branch_table_cell(branch['routing_no'])} | "
            f"{branch_table_cell(branch['phone_email'])} |"
        )

    lines.extend([
        "",
        BRANCH_SOURCE_URL,
    ])

    return "\n".join(lines)


def build_branch_locator_reply(query):
    ensure_branch_database_ready(auto_scrape=True)
    branches = search_branches(query)
    return format_branch_reply(branches, query)


def build_dhaka_branch_reply(query):
    return build_branch_locator_reply(f"Dhaka {query}")
