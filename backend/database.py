import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from language_support import expand_bangla_banglish_text


BASE_DIR = Path(__file__).resolve().parent
DATABASE_NAME = str(BASE_DIR / "EBL_chatbot.db")

def add_column_if_missing(cursor, table_name, column_name, column_definition):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    existing_columns = [column[1] for column in columns]

    if column_name not in existing_columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")


def create_database():
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            complaint_id TEXT,
            user_message TEXT,
            bot_reply TEXT,
            source TEXT,
            blocked INTEGER,
            status TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS website_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_name TEXT,
            page_url TEXT,
            page_text TEXT,
            status TEXT,
            updated_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_memory (
            session_id TEXT PRIMARY KEY,
            summary TEXT,
            updated_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT UNIQUE,
            session_id TEXT,
            issue_type TEXT,
            description TEXT,
            status TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pending_complaints (
            session_id TEXT PRIMARY KEY,
            issue_type TEXT,
            description TEXT,
            created_at TEXT
        )
    """)

    add_column_if_missing(cursor, "complaints", "customer_email", "TEXT")
    add_column_if_missing(cursor, "complaints", "notification_due_at", "TEXT")
    add_column_if_missing(cursor, "complaints", "three_day_email_sent", "INTEGER DEFAULT 0")
    add_column_if_missing(cursor, "complaints", "final_status_email_sent", "INTEGER DEFAULT 0")
    add_column_if_missing(cursor, "complaints", "last_email_sent_at", "TEXT")
    add_column_if_missing(cursor, "chat_logs", "feedback", "TEXT")
    add_column_if_missing(cursor, "chat_logs", "feedback_at", "TEXT")

    connection.commit()
    connection.close()


def save_chat(
    session_id,
    user_message,
    bot_reply,
    source,
    blocked,
    status,
    complaint_id=""
):
    create_database()

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO chat_logs (
            session_id,
            complaint_id,
            user_message,
            bot_reply,
            source,
            blocked,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        complaint_id,
        user_message,
        bot_reply,
        source,
        1 if blocked else 0,
        status,
        created_at
    ))

    chat_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return chat_id


def save_chat_feedback(chat_id, session_id, feedback):
    create_database()

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    feedback_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE chat_logs
        SET feedback = ?, feedback_at = ?
        WHERE id = ?
        AND session_id = ?
        AND bot_reply IS NOT NULL
        AND bot_reply != ''
    """, (
        feedback,
        feedback_at,
        chat_id,
        session_id,
    ))

    updated_rows = cursor.rowcount

    connection.commit()
    connection.close()

    return updated_rows > 0


def get_chat_history(session_id, limit=6):
    create_database()

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT user_message, bot_reply
        FROM chat_logs
        WHERE session_id = ?
        AND blocked = 0
        ORDER BY id DESC
        LIMIT ?
    """, (session_id, limit))

    rows = cursor.fetchall()
    connection.close()

    history = []
    rows.reverse()

    for row in rows:
        user_message = row[0]
        bot_reply = row[1]

        if user_message:
            history.append({
                "role": "user",
                "content": user_message
            })

        if bot_reply:
            history.append({
                "role": "assistant",
                "content": bot_reply
            })

    return history


def save_website_text(page_name, page_url, page_text):
    create_database()

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        DELETE FROM website_info
        WHERE page_url = ?
    """, (page_url,))

    cursor.execute("""
        INSERT INTO website_info (
            page_name,
            page_url,
            page_text,
            status,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        page_name,
        page_url,
        page_text,
        "active",
        updated_at
    ))

    connection.commit()
    connection.close()


def get_website_information():
    create_database()

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT page_name, page_url, page_text
        FROM website_info
        WHERE status = 'active'
        ORDER BY id ASC
    """)

    rows = cursor.fetchall()
    connection.close()

    website_information = ""

    for row in rows:
        page_name = row[0]
        page_url = row[1]
        page_text = row[2]

        website_information += f"Page: {page_name}\n"
        website_information += f"URL: {page_url}\n"
        website_information += f"Content:\n{page_text}\n\n"

    return website_information


def get_website_information_by_page_names(page_names):
    create_database()

    if not page_names:
        return get_website_information()

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    placeholders = ",".join(["?"] * len(page_names))

    cursor.execute(f"""
        SELECT page_name, page_url, page_text
        FROM website_info
        WHERE status = 'active'
        AND page_name IN ({placeholders})
        ORDER BY id ASC
    """, page_names)

    rows = cursor.fetchall()
    connection.close()

    website_information = ""

    for row in rows:
        page_name = row[0]
        page_url = row[1]
        page_text = row[2]

        website_information += f"Page: {page_name}\n"
        website_information += f"URL: {page_url}\n"
        website_information += f"Content:\n{page_text}\n\n"

    return website_information


def get_website_information_by_page_urls(page_urls):
    create_database()

    if not page_urls:
        return get_website_information()

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    placeholders = ",".join(["?"] * len(page_urls))

    cursor.execute(f"""
        SELECT page_name, page_url, page_text
        FROM website_info
        WHERE status = 'active'
        AND page_url IN ({placeholders})
        ORDER BY id ASC
    """, page_urls)

    rows = cursor.fetchall()
    connection.close()

    website_information = ""

    for row in rows:
        page_name = row[0]
        page_url = row[1]
        page_text = row[2]

        website_information += f"Page: {page_name}\n"
        website_information += f"URL: {page_url}\n"
        website_information += f"Content:\n{page_text}\n\n"

    return website_information


def clear_website_information():
    create_database()

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("DELETE FROM website_info")

    connection.commit()
    connection.close()


def get_session_summary(session_id):
    create_database()

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT summary
        FROM session_memory
        WHERE session_id = ?
    """, (session_id,))

    row = cursor.fetchone()
    connection.close()

    if row:
        return row[0]

    return ""


def save_session_summary(session_id, summary):
    create_database()

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT OR REPLACE INTO session_memory (
            session_id,
            summary,
            updated_at
        )
        VALUES (?, ?, ?)
    """, (
        session_id,
        summary,
        updated_at
    ))

    connection.commit()
    connection.close()


def generate_complaint_id(cursor):
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"CMP-{today}-"

    cursor.execute("""
        SELECT COUNT(*)
        FROM complaints
        WHERE complaint_id LIKE ?
    """, (prefix + "%",))

    count = cursor.fetchone()[0]
    next_number = count + 1

    return f"{prefix}{next_number:04d}"


def save_complaint(session_id, issue_type, description, customer_email=""):
    create_database()

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    complaint_id = generate_complaint_id(cursor)
    created_datetime = datetime.now()
    created_at = created_datetime.strftime("%Y-%m-%d %H:%M:%S")
    updated_at = created_at
    notification_due_at = add_working_days(created_datetime, 3).strftime("%Y-%m-%d %H:%M:%S")
    status = "Pending"

    cursor.execute("""
        INSERT INTO complaints (
            complaint_id,
            session_id,
            issue_type,
            description,
            status,
            created_at,
            updated_at,
            customer_email,
            notification_due_at,
            three_day_email_sent,
            final_status_email_sent,
            last_email_sent_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        complaint_id,
        session_id,
        issue_type,
        description,
        status,
        created_at,
        updated_at,
        customer_email,
        notification_due_at,
        0,
        0,
        ""
    ))

    connection.commit()
    connection.close()

    return {
        "complaint_id": complaint_id,
        "session_id": session_id,
        "issue_type": issue_type,
        "description": description,
        "status": status,
        "created_at": created_at,
        "updated_at": updated_at,
        "customer_email": customer_email,
        "notification_due_at": notification_due_at,
        "three_day_email_sent": 0,
        "final_status_email_sent": 0,
        "last_email_sent_at": "",
    }


def get_complaint_by_id(complaint_id):
    create_database()

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT complaint_id, session_id, issue_type, description, status,
               created_at, updated_at, customer_email, notification_due_at,
               three_day_email_sent, final_status_email_sent, last_email_sent_at
        FROM complaints
        WHERE complaint_id = ?
    """, (complaint_id,))

    row = cursor.fetchone()
    connection.close()

    if not row:
        return None

    return {
        "complaint_id": row[0],
        "session_id": row[1],
        "issue_type": row[2],
        "description": row[3],
        "status": row[4],
        "created_at": row[5],
        "updated_at": row[6],
        "customer_email": row[7],
        "notification_due_at": row[8],
        "three_day_email_sent": row[9],
        "final_status_email_sent": row[10],
        "last_email_sent_at": row[11],
    }

def update_complaint_status(complaint_id, new_status):
    create_database()

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE complaints
        SET status = ?, updated_at = ?
        WHERE complaint_id = ?
    """, (
        new_status,
        updated_at,
        complaint_id,
    ))

    updated_rows = cursor.rowcount

    connection.commit()
    connection.close()

    if updated_rows == 0:
        return None

    return get_complaint_by_id(complaint_id)
def get_recent_user_messages(session_id, limit=5):
    create_database()

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT user_message, created_at
        FROM chat_logs
        WHERE session_id = ?
        AND blocked = 0
        AND user_message IS NOT NULL
        AND user_message != ''
        AND source != 'memory-recall-agent'
        ORDER BY id DESC
        LIMIT ?
    """, (session_id, limit))

    rows = cursor.fetchall()
    connection.close()

    messages = []
    rows.reverse()

    for row in rows:
        messages.append({
            "message": row[0],
            "created_at": row[1]
        })

    return messages


def get_first_user_message(session_id):
    create_database()

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT user_message, created_at
        FROM chat_logs
        WHERE session_id = ?
        AND blocked = 0
        AND user_message IS NOT NULL
        AND user_message != ''
        AND source != 'memory-recall-agent'
        ORDER BY id ASC
        LIMIT 1
    """, (session_id,))

    row = cursor.fetchone()
    connection.close()

    if not row:
        return None

    return {
        "message": row[0],
        "created_at": row[1],
    }


def get_latest_complaint_by_session(session_id):
    create_database()

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT complaint_id, issue_type, description, status, created_at, updated_at
        FROM complaints
        WHERE session_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (session_id,))

    row = cursor.fetchone()
    connection.close()

    if not row:
        return None

    return {
        "complaint_id": row[0],
        "issue_type": row[1],
        "description": row[2],
        "status": row[3],
        "created_at": row[4],
        "updated_at": row[5]
    }


GENERIC_QUERY_WORDS = [
    "about",
    "and",
    "are",
    "available",
    "benefit",
    "benefits",
    "card",
    "cards",
    "credit",
    "detail",
    "details",
    "debit",
    "does",
    "ebl",
    "feature",
    "features",
    "information",
    "for",
    "from",
    "have",
    "loan",
    "loans",
    "mastercard",
    "offer",
    "offers",
    "tell",
    "the",
    "visa",
    "what",
    "with",
    "which",
    "you",
    "your",
]


def build_relevant_website_snippet(page_text, query_words, prefer_documents, max_characters=4000):
    if not page_text:
        return ""

    lower_text = page_text.lower()
    best_position = -1

    if prefer_documents:
        document_phrases = [
            "required documents for account opening",
            "documents required to open account",
            "required documents",
            "account opening form",
            "applicants",
            "nominees",
        ]

        for phrase in document_phrases:
            position = lower_text.find(phrase)
            if position >= 0:
                best_position = position
                break

    if best_position < 0 and "feature" in query_words:
        for phrase in ["key features", "features"]:
            position = lower_text.find(phrase)
            if position >= 0:
                best_position = position
                break

    if best_position < 0 and "loan" in query_words:
        for phrase in ["personal loan", "home loan", "auto loan", "ebl assure"]:
            position = lower_text.find(phrase)
            if position >= 0:
                best_position = position
                break

    if best_position < 0 and "card" in query_words:
        card_phrases = []

        if "debit" in query_words:
            card_phrases.append("debit cards")

        if "prepaid" in query_words:
            card_phrases.append("prepaid cards")

        if "islamic" in query_words:
            card_phrases.append("islamic cards")

        if "credit" in query_words:
            card_phrases.append("credit cards")

        card_phrases.extend([
            "credit cards",
            "debit cards",
            "prepaid cards",
            "islamic cards",
        ])

        for phrase in card_phrases:
            position = lower_text.find(phrase)
            if position >= 0:
                best_position = position
                break

    if best_position < 0:
        for word in query_words:
            position = lower_text.find(word)
            if position >= 0:
                best_position = position
                break

    if best_position < 0:
        return page_text[:max_characters]

    start = max(0, best_position - 350)
    end = min(len(page_text), start + max_characters)

    if end == len(page_text):
        start = max(0, end - max_characters)

    return page_text[start:end].strip()


def search_website_information(query, limit=5):
    create_database()

    if not query:
        return ""

    query = expand_bangla_banglish_text(query)

    cleaned_query = (
        query.lower()
        .replace("?", " ")
        .replace(",", " ")
        .replace(".", " ")
        .replace(":", " ")
        .replace(";", " ")
        .replace("/", " ")
        .replace("-", " ")
    )

    query_words = normalize_query_words(cleaned_query)
    user_query_words = list(query_words)
    user_important_words = [
        word
        for word in user_query_words
        if word not in GENERIC_QUERY_WORDS
    ]

    extra_keywords = []
    prefer_documents = contains_any_query_word(cleaned_query, [
        "document",
        "documents",
        "required",
        "requirement",
        "requirements",
        "need",
        "needed",
    ])

    if "account" in cleaned_query or "open" in cleaned_query:
        extra_keywords.extend([
            "account",
            "deposit",
            "savings",
            "current",
            "onlineapply",
            "apply",
            "required",
            "documents",
            "account opening form",
            "applicants",
            "nominees",
        ])

    if "saving" in cleaned_query or "savings" in cleaned_query:
        extra_keywords.extend([
            "savings",
            "saving",
            "savings account",
            "retail deposit",
            "power savings",
            "premium savings",
            "50+ savings",
            "max saver",
        ])

    if "card" in cleaned_query:
        extra_keywords.extend([
            "card",
            "credit",
            "debit",
            "visa",
            "mastercard",
        ])

    if "loan" in cleaned_query:
        extra_keywords.extend([
            "loan",
            "retail",
            "sme",
            "home",
            "auto",
            "personal",
        ])

    if "skybanking" in cleaned_query or "digital" in cleaned_query or "app" in cleaned_query:
        extra_keywords.extend([
            "skybanking",
            "digital",
            "internet",
            "online",
            "mobile",
        ])

    if "islamic" in cleaned_query or "shariah" in cleaned_query or "sharia" in cleaned_query:
        extra_keywords.extend([
            "islamic",
            "shariah",
            "sharia",
            "mudarabah",
            "wadiah",
            "profit",
            "distribution",
            "deposit",
            "finance",
            "financing",
            "cards",
        ])

    if "charge" in cleaned_query or "fee" in cleaned_query:
        extra_keywords.extend([
            "charge",
            "charges",
            "fee",
            "fees",
            "schedule",
        ])

    if "rate" in cleaned_query or "interest" in cleaned_query:
        extra_keywords.extend([
            "rate",
            "rates",
            "interest",
        ])

    query_words.extend(extra_keywords)
    query_words = list(dict.fromkeys(query_words))

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT page_name, page_url, page_text
        FROM website_info
        WHERE status = 'active'
    """)

    rows = cursor.fetchall()
    connection.close()

    scored_pages = []

    for row in rows:
        page_name = row[0]
        page_url = row[1]
        page_text = row[2] or ""

        page_identity = f"{page_name} {page_url}".lower()
        searchable_text = f"{page_name} {page_url} {page_text}".lower()

        score = 0
        important_words = user_important_words
        identity_hits = 0

        for word in query_words:
            if word in searchable_text:
                word_count = searchable_text.count(word)

                if word in GENERIC_QUERY_WORDS:
                    score += min(word_count, 5)
                else:
                    score += word_count * 10

            if word in page_identity:
                if word in GENERIC_QUERY_WORDS:
                    score += 25
                else:
                    score += 250

        for word in important_words:
            if word in page_identity:
                identity_hits += 1
                score += 350

        if important_words and identity_hits == len(important_words):
            score += 1200

        if important_words and identity_hits == 0:
            score -= 250

        if prefer_documents:
            for phrase in [
                "required documents for account opening",
                "documents required to open account",
                "completed and signed account opening form",
                "recent passport",
                "copy of national id",
                "copy of recent utility bill",
                "nominees",
            ]:
                if phrase in searchable_text:
                    score += searchable_text.count(phrase) * 8

            if "required documents for account opening" in searchable_text:
                score += 120

            if "completed and signed account opening form" in searchable_text:
                score += 80

        if "saving" in cleaned_query or "savings" in cleaned_query:
            if "saving" in page_identity or "deposit" in page_identity:
                score += 150
            else:
                score -= 150

        if "loan" in cleaned_query or "loans" in cleaned_query:
            if "loan" in page_identity:
                score += 300
            elif "card" in page_identity:
                score -= 400

            if not important_words and page_name in [
                "EBL Retail Loan Page",
                "EBL SME Loan Page",
            ]:
                score += 800

        if "card" in cleaned_query or "cards" in cleaned_query:
            if "card" in page_identity or "eblcard" in page_identity:
                score += 300
            elif "loan" in page_identity:
                score -= 400

            if not important_words and page_name == "EBL Cards Page":
                score += 800

        if score > 0:
            scored_pages.append({
                "score": score,
                "page_name": page_name,
                "page_url": page_url,
                "page_text": page_text,
            })

    scored_pages.sort(key=lambda item: item["score"], reverse=True)

    selected_pages = scored_pages[:limit]

    website_information = ""

    for item in selected_pages:
        snippet = build_relevant_website_snippet(
            item["page_text"],
            user_important_words + user_query_words + query_words,
            prefer_documents,
        )

        website_information += f"Page: {item['page_name']}\n"
        website_information += f"URL: {item['page_url']}\n"
        website_information += f"Content:\n{snippet}\n\n"

    return website_information.strip()


def contains_any_query_word(text, words):
    for word in words:
        if word in text:
            return True

    return False


def normalize_query_words(cleaned_query):
    words = []

    for word in cleaned_query.split():
        word = word.strip()

        if len(word) <= 2:
            continue

        if word.endswith("ies") and len(word) > 4:
            word = word[:-3] + "y"
        elif word.endswith("s") and len(word) > 4:
            word = word[:-1]

        if word not in words:
            words.append(word)

    return words

def save_pending_complaint(session_id, issue_type, description):
    create_database()

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT OR REPLACE INTO pending_complaints (
            session_id,
            issue_type,
            description,
            created_at
        )
        VALUES (?, ?, ?, ?)
    """, (
        session_id,
        issue_type,
        description,
        created_at
    ))

    connection.commit()
    connection.close()


def get_pending_complaint(session_id):
    create_database()

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT issue_type, description, created_at
        FROM pending_complaints
        WHERE session_id = ?
    """, (session_id,))

    row = cursor.fetchone()
    connection.close()

    if not row:
        return None

    return {
        "issue_type": row[0],
        "description": row[1],
        "created_at": row[2],
    }


def delete_pending_complaint(session_id):
    create_database()

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM pending_complaints
        WHERE session_id = ?
    """, (session_id,))

    connection.commit()
    connection.close()

def add_working_days(start_datetime, working_days):
    current_date = start_datetime
    added_days = 0

    while added_days < working_days:
        current_date = current_date + timedelta(days=1)

        if current_date.weekday() not in [4, 5]: # Monday=0 to Sunday=6, so 4=Friday, 5=Saturday
            added_days += 1

    return current_date

def get_due_three_day_complaints():
    create_database()

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        SELECT complaint_id, session_id, issue_type, description, status,
               created_at, updated_at, customer_email, notification_due_at,
               three_day_email_sent, final_status_email_sent, last_email_sent_at
        FROM complaints
        WHERE customer_email IS NOT NULL
        AND customer_email != ''
        AND notification_due_at IS NOT NULL
        AND notification_due_at != ''
        AND notification_due_at <= ?
        AND three_day_email_sent = 0
        AND status NOT IN ('Resolved', 'Rejected')
    """, (now,))

    rows = cursor.fetchall()
    connection.close()

    complaints = []

    for row in rows:
        complaints.append({
            "complaint_id": row[0],
            "session_id": row[1],
            "issue_type": row[2],
            "description": row[3],
            "status": row[4],
            "created_at": row[5],
            "updated_at": row[6],
            "customer_email": row[7],
            "notification_due_at": row[8],
            "three_day_email_sent": row[9],
            "final_status_email_sent": row[10],
            "last_email_sent_at": row[11],
        })

    return complaints


def mark_three_day_email_sent(complaint_id):
    create_database()

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    sent_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE complaints
        SET three_day_email_sent = 1,
            last_email_sent_at = ?
        WHERE complaint_id = ?
    """, (
        sent_at,
        complaint_id
    ))

    connection.commit()
    connection.close()


def mark_final_status_email_sent(complaint_id):
    create_database()

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    sent_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE complaints
        SET final_status_email_sent = 1,
            last_email_sent_at = ?
        WHERE complaint_id = ?
    """, (
        sent_at,
        complaint_id
    ))

    connection.commit()
    connection.close()

