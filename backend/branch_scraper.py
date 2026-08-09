"""Scrape EBL branch information from the official website."""

from datetime import datetime

import requests
from bs4 import BeautifulSoup

from branch_database import (
    BRANCH_SOURCE_URL,
    BRANCH_SUPPORTED_DISTRICTS,
    canonical_branch_district,
    save_branches,
)


HEADERS = {
    "User-Agent": "Mozilla/5.0",
}


def clean_text(value):
    return " ".join((value or "").replace("\xa0", " ").split())


def decode_cloudflare_email(encoded_email):
    try:
        key = int(encoded_email[:2], 16)
        characters = [
            chr(int(encoded_email[index:index + 2], 16) ^ key)
            for index in range(2, len(encoded_email), 2)
        ]
        return "".join(characters)
    except (TypeError, ValueError):
        return ""


def decode_protected_emails(soup):
    for anchor in soup.select("a.__cf_email__[data-cfemail]"):
        decoded_email = decode_cloudflare_email(anchor.get("data-cfemail"))

        if decoded_email:
            anchor.string = decoded_email


def table_header_texts(table):
    headers = []

    for header in table.select("th"):
        headers.append(clean_text(header.get_text(" ", strip=True)).lower())

    return headers


def looks_like_branch_table(table):
    header_text = " ".join(table_header_texts(table))

    return (
        "district" in header_text
        and "branch name" in header_text
        and "address" in header_text
        and "routing" in header_text
    )


def extract_table_rows(table):
    rows = table.select("tbody tr")

    if not rows:
        rows = table.select("tr")

    return rows


def normalize_filter_districts(districts):
    if not districts:
        return set(BRANCH_SUPPORTED_DISTRICTS)

    return {
        canonical_branch_district(district)
        for district in districts
        if district
    }


def extract_branch_from_row(row, updated_at, target_districts=None):
    columns = [
        clean_text(column.get_text(" ", strip=True))
        for column in row.select("td")
    ]

    if len(columns) < 6:
        return None

    district = canonical_branch_district(columns[1])
    branch_name = columns[2]
    address = columns[3]
    routing_no = columns[4]
    phone_email = columns[5]

    if target_districts and district not in target_districts:
        return None

    if not branch_name or branch_name == "-":
        return None

    return {
        "district": district,
        "branch_name": branch_name,
        "address": address,
        "routing_no": routing_no,
        "phone_email": phone_email,
        "area_keywords": f"{branch_name} {address}",
        "updated_at": updated_at,
    }


def scrape_branches(url=BRANCH_SOURCE_URL, districts=None):
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    decode_protected_emails(soup)
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    target_districts = normalize_filter_districts(districts)
    branches = []

    for table in soup.find_all("table"):
        if not looks_like_branch_table(table):
            continue

        for row in extract_table_rows(table):
            branch = extract_branch_from_row(row, updated_at, target_districts)

            if branch:
                branches.append(branch)

    return branches


def refresh_supported_branches(url=BRANCH_SOURCE_URL, districts=None):
    target_districts = normalize_filter_districts(districts)
    branches = scrape_branches(url, target_districts)

    for district in target_districts:
        district_branches = [
            branch
            for branch in branches
            if canonical_branch_district(branch.get("district")) == district
        ]
        save_branches(district_branches, district=district, source_url=url)

    return branches


def scrape_dhaka_branches(url=BRANCH_SOURCE_URL):
    return scrape_branches(url, districts=("Dhaka",))


def refresh_dhaka_branches(url=BRANCH_SOURCE_URL):
    return refresh_supported_branches(url, districts=("Dhaka",))


if __name__ == "__main__":
    scraped_branches = refresh_supported_branches()
    district_labels = ", ".join(BRANCH_SUPPORTED_DISTRICTS)
    print(f"Saved {len(scraped_branches)} {district_labels} branches from {BRANCH_SOURCE_URL}")
