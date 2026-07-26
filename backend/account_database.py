"""Account type database import helpers."""

from pathlib import Path
import csv
import re
import sqlite3

from language_support import expand_bangla_banglish_text


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "EBL_chatbot.db"
ACCOUNT_DATA_DIR = BASE_DIR / "account_data"


ACCOUNT_TYPE_COLUMNS = [
    "schedule_type",
    "account_category",
    "account_name",
    "source_file",
]


_READY = False


ACCOUNT_CATEGORY_ALIASES = {
    "current": ["current", "current deposit", "current deposits"],
    "savings": ["saving", "savings", "savings deposit", "savings deposits"],
    "high earning": ["high earning", "high earning account"],
    "fixed": ["fixed", "fixed deposit", "fixed deposits", "fd", "fdr"],
    "dps": ["dps", "deposit pension", "scheme"],
    "nrb": ["nrb", "non resident", "shonchoy", "paribar", "nfcd"],
    "foreign currency": [
        "foreign",
        "foreign currency",
        "fcy",
        "rfcd",
        "freelancer",
        "mariner",
        "expat fcy",
        "citizen",
    ],
    "personal retail": ["personal retail", "personal retail account"],
    "short notice": ["short notice", "short notice deposit", "snd", "subidha"],
    "recurring": ["recurring", "recurring deposit", "equity builder"],
}


def create_account_type_table(connection):
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule_type TEXT NOT NULL,
            account_category TEXT NOT NULL,
            account_name TEXT NOT NULL,
            source_file TEXT NOT NULL,
            search_text TEXT NOT NULL,
            UNIQUE(schedule_type, account_category, account_name)
        )
    """)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_account_types_schedule "
        "ON account_types(schedule_type)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_account_types_category "
        "ON account_types(account_category)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_account_types_name "
        "ON account_types(account_name)"
    )
    connection.commit()


def build_account_search_text(row):
    return " ".join(
        row.get(column, "")
        for column in [
            "schedule_type",
            "account_category",
            "account_name",
        ]
    ).lower()


def normalize_account_text(text):
    text = expand_bangla_banglish_text(text)
    text = text.lower()
    text = text.replace("&", " and ")
    return " ".join(re.findall(r"[a-z0-9+]+", text))


def get_connection():
    return sqlite3.connect(DATABASE_PATH)


def iter_account_type_csv_paths():
    if not ACCOUNT_DATA_DIR.exists():
        return []

    return sorted(ACCOUNT_DATA_DIR.glob("*.csv"))


def read_account_type_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        missing_columns = [
            column
            for column in ACCOUNT_TYPE_COLUMNS
            if column not in (reader.fieldnames or [])
        ]

        if missing_columns:
            raise ValueError(
                f"{path.name} is missing columns: {', '.join(missing_columns)}"
            )

        for line_number, row in enumerate(reader, start=2):
            clean_row = {
                column: (row.get(column) or "").strip()
                for column in ACCOUNT_TYPE_COLUMNS
            }
            required_missing = [
                column for column in ACCOUNT_TYPE_COLUMNS if not clean_row[column]
            ]

            if required_missing:
                raise ValueError(
                    f"{path.name}:{line_number} missing required values: "
                    f"{', '.join(required_missing)}"
                )

            yield clean_row


def import_account_types(clear_existing=True):
    connection = get_connection()
    create_account_type_table(connection)
    cursor = connection.cursor()

    if clear_existing:
        cursor.execute("DELETE FROM account_types")

    inserted = 0

    for path in iter_account_type_csv_paths():
        for row in read_account_type_csv(path):
            cursor.execute("""
                INSERT INTO account_types (
                    schedule_type,
                    account_category,
                    account_name,
                    source_file,
                    search_text
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                row["schedule_type"],
                row["account_category"],
                row["account_name"],
                row["source_file"],
                build_account_search_text(row),
            ))
            inserted += 1

    connection.commit()
    connection.close()
    return inserted


def ensure_account_types_ready(force_import=False):
    global _READY

    if _READY and not force_import:
        return

    connection = get_connection()
    create_account_type_table(connection)
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM account_types")
    row_count = cursor.fetchone()[0]
    connection.close()

    if force_import or row_count == 0:
        import_account_types(clear_existing=True)

    _READY = True


def get_account_categories(schedule_type):
    ensure_account_types_ready()

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT account_category
        FROM account_types
        WHERE lower(schedule_type) = lower(?)
        GROUP BY account_category
        ORDER BY MIN(id)
    """, (schedule_type,))
    categories = [row[0] for row in cursor.fetchall()]
    connection.close()

    return categories


def get_account_names(schedule_type, account_category):
    ensure_account_types_ready()

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT account_name
        FROM account_types
        WHERE lower(schedule_type) = lower(?)
          AND lower(account_category) = lower(?)
        ORDER BY id
    """, (schedule_type, account_category))
    account_names = [row[0] for row in cursor.fetchall()]
    connection.close()

    return account_names


def find_account_category(schedule_type, message):
    categories = get_account_categories(schedule_type)
    normalized_message = normalize_account_text(message)

    if not normalized_message:
        return ""

    for category in categories:
        normalized_category = normalize_account_text(category)

        if (
            normalized_category == normalized_message
            or normalized_category in normalized_message
        ):
            return category

    for alias_group, aliases in ACCOUNT_CATEGORY_ALIASES.items():
        for alias in aliases:
            normalized_alias = normalize_account_text(alias)

            if (
                normalized_alias == normalized_message
                or normalized_alias in normalized_message
            ):
                for category in categories:
                    normalized_category = normalize_account_text(category)

                    if (
                        normalize_account_text(alias_group) in normalized_category
                    ):
                        return category

    return ""
