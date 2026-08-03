import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


COMPLAINT_CELL_URL = "https://www.ebl.com.bd/regulatory/complaintcell"
DEFAULT_COMPLAINT_CELL_EMAIL = "ccs.cmc@ebl-bd.com"
DEFAULT_QUERY_COMPLAINT_LINK = "https://dgzip.ebl-bd.com/query/"
DEFAULT_COMPLAINT_CELL_FOOTER = (
    "Please enquire us from 10am to 5pm, SUN-THU, (Except Holidays) "
    "Or For 24 hours Contact Center: please call 16230 (from any mobile), "
    "+8809677716230 (from any local & overseas number)"
)
REQUEST_TIMEOUT_SECONDS = 15
CACHE_TTL_SECONDS = 30 * 60

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

_CACHE = {
    "fetched_at": 0.0,
    "reply": "",
}


def clean_text(value):
    return " ".join((value or "").replace("\xa0", " ").split())


def decode_cloudflare_email(encoded_email):
    if not encoded_email:
        return ""

    try:
        key = int(encoded_email[:2], 16)
        decoded_chars = []

        for index in range(2, len(encoded_email), 2):
            decoded_chars.append(chr(int(encoded_email[index:index + 2], 16) ^ key))

        return "".join(decoded_chars)
    except (TypeError, ValueError):
        return ""


def decode_protected_emails(soup):
    for email_span in soup.select(".__cf_email__"):
        decoded_email = decode_cloudflare_email(email_span.get("data-cfemail", ""))

        if decoded_email:
            email_span.string = decoded_email

    for email_link in soup.find_all("a", href=True):
        href = email_link.get("href", "")

        if "/cdn-cgi/l/email-protection#" not in href:
            continue

        decoded_email = decode_cloudflare_email(href.rsplit("#", 1)[-1])

        if decoded_email:
            email_link.clear()
            email_link.append(decoded_email)


def extract_general_email(soup):
    email_pattern = re.compile(r"[\w.\-+]+@[\w.\-]+\.\w+")

    for paragraph in soup.find_all(["p", "strong"]):
        text = clean_text(paragraph.get_text(" ", strip=True))

        if "Email Address" not in text:
            continue

        match = email_pattern.search(text)

        if match:
            return match.group(0)

    return ""


def extract_query_complaint_link(soup):
    for link in soup.find_all("a", href=True):
        link_text = clean_text(link.get_text(" ", strip=True)).lower()

        if "query/complaint" not in link_text and "complaint management" not in link_text:
            continue

        return urljoin(COMPLAINT_CELL_URL, link["href"])

    return ""


def extract_enquiry_details(soup):
    for paragraph in soup.find_all("p"):
        text = clean_text(paragraph.get_text(" ", strip=True))

        if "Please enquire us" in text:
            return text

    return ""


def parse_contact_sections(soup):
    sections = []
    current_section = ""

    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = [
                clean_text(cell.get_text(" ", strip=True))
                for cell in row.find_all(["th", "td"])
            ]
            cells = [cell for cell in cells if cell]

            if not cells:
                continue

            if len(cells) == 1:
                current_section = cells[0]
                continue

            if len(cells) < 4:
                continue

            lower_cells = [cell.lower() for cell in cells[:4]]

            if lower_cells == ["name", "designation", "email", "phone no."]:
                continue

            name, designation, email, phone = cells[:4]

            if not name or not designation:
                continue

            sections.append({
                "section": current_section,
                "name": name,
                "designation": designation,
                "email": email,
                "phone": phone,
            })

    return sections


def split_enquiry_details(enquiry_text):
    enquiry_time = ""
    contact_center = ""

    if not enquiry_text:
        return enquiry_time, contact_center

    time_match = re.search(
        r"from\s+(.+?)\s+Or\s+For\s+24 hours",
        enquiry_text,
        flags=re.IGNORECASE,
    )

    if time_match:
        enquiry_time = clean_text(time_match.group(1).rstrip(","))

    contact_match = re.search(
        r"For\s+24 hours Contact Center:\s*(.+)",
        enquiry_text,
        flags=re.IGNORECASE,
    )

    if contact_match:
        contact_center = clean_text(contact_match.group(1))

    return enquiry_time, contact_center


def build_complaint_cell_fallback_reply():
    return "\n\n".join([
        "EBL Complaint Cell:",
        f"Email Address: {DEFAULT_COMPLAINT_CELL_EMAIL}",
        f"Online query/complaint form: {DEFAULT_QUERY_COMPLAINT_LINK}",
        DEFAULT_COMPLAINT_CELL_FOOTER,
    ])


def build_intro_details(general_email, enquiry_text, query_complaint_link):
    detail_lines = []
    general_email = general_email or DEFAULT_COMPLAINT_CELL_EMAIL
    enquiry_text = enquiry_text or DEFAULT_COMPLAINT_CELL_FOOTER
    query_complaint_link = query_complaint_link or DEFAULT_QUERY_COMPLAINT_LINK

    if general_email:
        detail_lines.append(f"Email Address: {general_email}")

    if enquiry_text:
        detail_lines.append(enquiry_text)

    if query_complaint_link:
        detail_lines.append(f"Online query/complaint form: {query_complaint_link}")

    detail_lines.append(f"Source page: {COMPLAINT_CELL_URL}")

    return "\n\n".join(detail_lines)


def build_contact_blocks(contacts, limit=None):
    contact_blocks = []
    visible_contacts = contacts[:limit] if limit else contacts

    for index, contact in enumerate(visible_contacts, start=1):
        contact_blocks.append(
            "\n".join([
                f"{index}. {contact['name']}",
                f"Designation: {contact['designation']}",
                f"Email: {contact['email']}",
                f"Phone No.: {contact['phone']}",
            ])
        )

    return "\n\n".join(contact_blocks)


def build_simple_contact_summary(contacts):
    central_members = [
        contact
        for contact in contacts
        if contact["section"] == "Members of Central Customer Service & Complaint Management Cell"
    ]

    if not central_members:
        return ""

    return build_contact_blocks(central_members, limit=2)


def fetch_complaint_cell_reply():
    response = requests.get(
        COMPLAINT_CELL_URL,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    decode_protected_emails(soup)

    general_email = extract_general_email(soup)
    query_complaint_link = extract_query_complaint_link(soup)
    enquiry_text = extract_enquiry_details(soup)
    contacts = parse_contact_sections(soup)

    reply_parts = [
        "EBL Complaint Cell:",
        build_intro_details(general_email, enquiry_text, query_complaint_link),
    ]

    section_names = []

    for contact in contacts:
        section = contact["section"]

        if section and section not in section_names:
            section_names.append(section)

    for section_name in section_names:
        section_contacts = [
            contact
            for contact in contacts
            if contact["section"] == section_name
        ]

        if not section_contacts:
            continue

        reply_parts.extend([
            f"{section_name}:",
            build_contact_blocks(section_contacts),
        ])

    return "\n\n".join(reply_parts)


def build_complaint_cell_reply():
    now = time.time()

    if _CACHE["reply"] and now - _CACHE["fetched_at"] < CACHE_TTL_SECONDS:
        return _CACHE["reply"]

    try:
        reply = fetch_complaint_cell_reply()
    except Exception:
        reply = build_complaint_cell_fallback_reply()

    _CACHE["reply"] = reply
    _CACHE["fetched_at"] = now

    return reply
