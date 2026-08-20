import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


WHATS_NEW_URL = "https://www.ebl.com.bd/whats-new"
REQUEST_TIMEOUT_SECONDS = 15
CACHE_TTL_SECONDS = 30 * 60

SKIP_IMAGE_KEYWORDS = (
    "logo",
    "favicon",
    "user-loging",
    "branch-icon",
    "exchangerate",
    "call_center",
    "menu-left-icon",
)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
}

FALLBACK_OFFERS = [
    {
        "title": "GoZayaan Domestic Campaign Aug-Sep 2026",
        "description": "View the latest EBL campaign details from the official What's New page.",
        "image_url": "",
        "details_url": WHATS_NEW_URL,
    },
    {
        "title": "Up to 65% Discount On Domestic Hotel Bookings",
        "description": "View the latest EBL campaign details from the official What's New page.",
        "image_url": "",
        "details_url": WHATS_NEW_URL,
    },
    {
        "title": "Up to 10% Discount Domestic & International",
        "description": "View the latest EBL campaign details from the official What's New page.",
        "image_url": "",
        "details_url": WHATS_NEW_URL,
    },
    {
        "title": "Bangla QR-Foodpanda Campaign",
        "description": "View the latest EBL campaign details from the official What's New page.",
        "image_url": "",
        "details_url": WHATS_NEW_URL,
    },
    {
        "title": "EBL Uddipon",
        "description": "View the latest EBL campaign details from the official What's New page.",
        "image_url": "",
        "details_url": WHATS_NEW_URL,
    },
]

_CACHE = {
    "fetched_at": 0.0,
    "reply": "",
}


def clean_text(value):
    return " ".join((value or "").replace("\xa0", " ").split())


def clean_offer_title(value):
    title = clean_text(value)

    for suffix in [
        "Whats New Main Banner",
        "What's New Main Banner",
        "Whats-new Main Banner",
        "Whats New Banner",
    ]:
        if title.lower().endswith(suffix.lower()):
            title = title[: -len(suffix)].strip()

    return title.strip(" -|")


def title_from_url(value):
    path = (value or "").split("?", 1)[0].rstrip("/")
    slug = path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    title = " ".join(part for part in slug.replace("_", "-").split("-") if part)

    return clean_text(title).title()


def closest_offer_link(image):
    for parent in image.parents:
        if parent.name == "a" and parent.get("href"):
            return urljoin(WHATS_NEW_URL, parent["href"])

        parent_classes = parent.get("class", []) if parent else []

        if parent.name in {"body", "html"} or "offersowl-carousel-1col" in parent_classes:
            break

    return WHATS_NEW_URL


def image_source(image):
    for attribute in ["data-src", "data-lazy-src", "src"]:
        value = image.get(attribute)

        if value:
            return urljoin(WHATS_NEW_URL, value)

    srcset = image.get("srcset") or image.get("data-srcset")

    if srcset:
        first_source = srcset.split(",", 1)[0].strip().split(" ", 1)[0]

        if first_source:
            return urljoin(WHATS_NEW_URL, first_source)

    return ""


def offer_description(title):
    if "discount" in title.lower():
        return "Explore the latest EBL discount campaign and offer details."

    if "campaign" in title.lower():
        return "Explore the latest EBL campaign details and eligibility."

    return "Explore the latest EBL offer details from the official What's New page."


def parse_offers(html):
    soup = BeautifulSoup(html, "html.parser")
    offers = []
    seen_titles = set()

    for image in soup.find_all("img"):
        alt_text = clean_text(image.get("alt", ""))
        source = image_source(image)
        source_lower = source.lower()
        haystack = f"{alt_text} {source}".lower()

        if not source or any(keyword in source_lower for keyword in SKIP_IMAGE_KEYWORDS):
            continue

        is_whats_new_asset = "assets/whatsnew" in source_lower
        has_offer_keyword = any(
            keyword in haystack
            for keyword in [
                "whats new",
                "campaign",
                "offer",
                "discount",
                "cashback",
                "hotel",
                "shopping",
                "foodpanda",
                "bkash",
            ]
        )

        if not is_whats_new_asset and not has_offer_keyword:
            continue

        details_url = closest_offer_link(image)
        title = (
            clean_offer_title(alt_text)
            or title_from_url(details_url)
            or title_from_url(source)
        )

        if not title or title.lower() in seen_titles:
            continue

        seen_titles.add(title.lower())
        offers.append({
            "title": title,
            "description": offer_description(title),
            "image_url": source,
            "details_url": details_url,
        })

    return offers


def fetch_ongoing_offers():
    response = requests.get(
        WHATS_NEW_URL,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    return parse_offers(response.text)


def build_offers_reply(offers):
    if not offers:
        offers = FALLBACK_OFFERS

    blocks = ["EBL Ongoing Offers:"]

    for offer in offers:
        blocks.append("\n".join([
            "Offer:",
            f"Title: {offer.get('title', '').strip()}",
            f"Description: {offer.get('description', '').strip()}",
            f"Image: {offer.get('image_url', '').strip()}",
            f"Details: {offer.get('details_url', WHATS_NEW_URL).strip()}",
        ]))

    return "\n\n".join(blocks)


def build_ongoing_offers_reply():
    now = time.time()

    if _CACHE["reply"] and now - _CACHE["fetched_at"] < CACHE_TTL_SECONDS:
        return _CACHE["reply"]

    try:
        offers = fetch_ongoing_offers()
    except Exception:
        offers = FALLBACK_OFFERS

    reply = build_offers_reply(offers)

    _CACHE["reply"] = reply
    _CACHE["fetched_at"] = now

    return reply
