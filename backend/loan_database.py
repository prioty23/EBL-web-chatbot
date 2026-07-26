"""Loan type database import helpers."""

from pathlib import Path
import csv
import re
import sqlite3

from language_support import expand_bangla_banglish_text


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "EBL_chatbot.db"
LOAN_DATA_DIR = BASE_DIR / "loan_data"


LOAN_TYPE_COLUMNS = [
    "schedule_type",
    "loan_category",
    "loan_name",
    "source_file",
]


_READY = False


LOAN_CATEGORY_ALIASES = {
    "personal loan": ["personal", "personal loan"],
    "home loan": ["home", "home loan", "home credit", "mortgage"],
    "auto loan": ["auto", "auto loan", "car", "car loan", "vehicle"],
    "two wheeler loan": [
        "two wheeler",
        "two wheeler loan",
        "bike",
        "bike loan",
        "motorcycle",
        "motorcycle loan",
    ],
    "secured loan": [
        "secured",
        "secured loan",
        "cash covered",
        "fast cash",
        "fast loan",
    ],
    "ebl edu loan": ["edu", "edu loan", "education", "education loan", "student loan"],
}


def create_loan_type_table(connection):
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loan_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule_type TEXT NOT NULL,
            loan_category TEXT NOT NULL,
            loan_name TEXT NOT NULL,
            source_file TEXT NOT NULL,
            search_text TEXT NOT NULL,
            UNIQUE(schedule_type, loan_category, loan_name)
        )
    """)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_loan_types_schedule "
        "ON loan_types(schedule_type)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_loan_types_category "
        "ON loan_types(loan_category)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_loan_types_name "
        "ON loan_types(loan_name)"
    )
    connection.commit()


def build_loan_search_text(row):
    return " ".join(
        row.get(column, "")
        for column in [
            "schedule_type",
            "loan_category",
            "loan_name",
        ]
    ).lower()


def normalize_loan_type_text(text):
    text = expand_bangla_banglish_text(text)
    text = text.lower()
    text = text.replace("&", " and ")
    return " ".join(re.findall(r"[a-z0-9+]+", text))


def get_connection():
    return sqlite3.connect(DATABASE_PATH)


def iter_loan_type_csv_paths():
    if not LOAN_DATA_DIR.exists():
        return []

    return sorted(LOAN_DATA_DIR.glob("*.csv"))


def read_loan_type_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        missing_columns = [
            column
            for column in LOAN_TYPE_COLUMNS
            if column not in (reader.fieldnames or [])
        ]

        if missing_columns:
            raise ValueError(
                f"{path.name} is missing columns: {', '.join(missing_columns)}"
            )

        for line_number, row in enumerate(reader, start=2):
            clean_row = {
                column: (row.get(column) or "").strip()
                for column in LOAN_TYPE_COLUMNS
            }
            required_missing = [
                column for column in LOAN_TYPE_COLUMNS if not clean_row[column]
            ]

            if required_missing:
                raise ValueError(
                    f"{path.name}:{line_number} missing required values: "
                    f"{', '.join(required_missing)}"
                )

            yield clean_row


def import_loan_types(clear_existing=True):
    connection = get_connection()
    create_loan_type_table(connection)
    cursor = connection.cursor()

    if clear_existing:
        cursor.execute("DELETE FROM loan_types")

    inserted = 0

    for path in iter_loan_type_csv_paths():
        for row in read_loan_type_csv(path):
            cursor.execute("""
                INSERT INTO loan_types (
                    schedule_type,
                    loan_category,
                    loan_name,
                    source_file,
                    search_text
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                row["schedule_type"],
                row["loan_category"],
                row["loan_name"],
                row["source_file"],
                build_loan_search_text(row),
            ))
            inserted += 1

    connection.commit()
    connection.close()
    return inserted


def ensure_loan_types_ready(force_import=False):
    global _READY

    if _READY and not force_import:
        return

    connection = get_connection()
    create_loan_type_table(connection)
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM loan_types")
    row_count = cursor.fetchone()[0]
    connection.close()

    if force_import or row_count == 0:
        import_loan_types(clear_existing=True)

    _READY = True


def get_loan_categories(schedule_type):
    ensure_loan_types_ready()

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT loan_category
        FROM loan_types
        WHERE lower(schedule_type) = lower(?)
        GROUP BY loan_category
        ORDER BY MIN(id)
    """, (schedule_type,))
    categories = [row[0] for row in cursor.fetchall()]
    connection.close()

    return categories


def get_loan_names(schedule_type, loan_category):
    ensure_loan_types_ready()

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT loan_name
        FROM loan_types
        WHERE lower(schedule_type) = lower(?)
          AND lower(loan_category) = lower(?)
        ORDER BY id
    """, (schedule_type, loan_category))
    loan_names = [row[0] for row in cursor.fetchall()]
    connection.close()

    return loan_names


def find_loan_category(schedule_type, message):
    categories = get_loan_categories(schedule_type)
    normalized_message = normalize_loan_type_text(message)

    if not normalized_message:
        return ""

    for category in categories:
        normalized_category = normalize_loan_type_text(category)

        if (
            normalized_category == normalized_message
            or normalized_category in normalized_message
        ):
            return category

    for alias_group, aliases in LOAN_CATEGORY_ALIASES.items():
        for alias in aliases:
            normalized_alias = normalize_loan_type_text(alias)

            if (
                normalized_alias == normalized_message
                or normalized_alias in normalized_message
            ):
                for category in categories:
                    normalized_category = normalize_loan_type_text(category)

                    if (
                        normalize_loan_type_text(alias_group)
                        in normalized_category
                    ):
                        return category

    return ""
