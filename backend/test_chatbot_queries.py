"""Regression checks for the EBL chatbot routes.

Run from the project root:
    python backend/test_chatbot_queries.py

The checks use deterministic local query understanding instead of Groq so they
can be run before every push without network/API limits.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

import main  # noqa: E402
from database import DATABASE_NAME, create_database  # noqa: E402
from query_understanding_ai import build_fallback_understanding  # noqa: E402
from schemas import ChatRequest  # noqa: E402


@dataclass
class QueryCase:
    name: str
    messages: list[str]
    must_contain: list[str] = field(default_factory=list)
    must_not_contain: list[str] = field(default_factory=list)
    sources: set[str] = field(default_factory=set)
    quick_actions_contain: list[str] = field(default_factory=list)
    quick_actions_not_contain: list[str] = field(default_factory=list)


TEST_CASES = [
    QueryCase(
        name="Greeting shows main menu",
        messages=["hi"],
        sources={"greeting-handler"},
        must_contain=["Hello", "Eastern Bank"],
        quick_actions_contain=[
            "Open an Account",
            "Loan Information",
            "Schedule of Charges",
            "Interest Rate",
        ],
        quick_actions_not_contain=["Suggest Account", "Suggest Loan"],
    ),
    QueryCase(
        name="Identity question is answered",
        messages=["Who are you?"],
        sources={"identity-handler"},
        must_contain=["Eastern Bank PLC AI Assistant", "EBL chatbot"],
    ),
    QueryCase(
        name="Open account asks account type",
        messages=["Open an Account"],
        sources={"account-router"},
        must_contain=["Which account type"],
        quick_actions_contain=[
            "Retail Account",
            "SME Account",
            "Islamic Account",
        ],
    ),
    QueryCase(
        name="Retail account shows retail categories",
        messages=["Open an Account", "Retail Account"],
        sources={"account-router"},
        must_contain=["Which Retail account category"],
        quick_actions_contain=["Current Deposits", "Savings Deposits", "DPS"],
    ),
    QueryCase(
        name="Retail DPS stays in account flow",
        messages=["Open an Account", "Retail Account", "DPS"],
        sources={"account-router"},
        must_contain=["EBL Retail DPS accounts include"],
        must_not_contain=["interest rate"],
        quick_actions_contain=["EBL Kotipoti Scheme", "EBL Confidence"],
    ),
    QueryCase(
        name="Islamic account shows Islamic product buttons",
        messages=["Open an Account", "Islamic Account"],
        sources={"account-router"},
        must_contain=["EBL Islamic Deposit options include"],
        must_not_contain=["EBL High Performance Islamic Account features"],
        quick_actions_contain=[
            "EBL Islamic Current Account",
            "EBL Executive Islamic Savings Account (Payroll Account)",
        ],
    ),
    QueryCase(
        name="Islamic payroll product opens details",
        messages=[
            "Open an Account",
            "Islamic Account",
            "EBL Executive Islamic Savings Account (Payroll Account)",
        ],
        sources={"account-router"},
        must_contain=[
            "EBL Executive Islamic Savings Account (Payroll Account) features",
            "Higher profit rate",
        ],
        must_not_contain=["EBL Islamic Deposit options include"],
    ),
    QueryCase(
        name="Banglish papers request returns selected account documents",
        messages=["EBL Personal Retail Account", "ki ki papers lagbe"],
        sources={"account-router"},
        must_contain=[
            "EBL Personal Retail Account required documents",
            "National ID",
        ],
        must_not_contain=["Which account type"],
    ),
    QueryCase(
        name="Account information back returns main menu",
        messages=["Open an Account", "Retail Account", "Back"],
        sources={"greeting-handler"},
        must_contain=["Welcome to Eastern Bank AI Assistant"],
        quick_actions_contain=[
            "Open an Account",
            "Loan Information",
            "Card Information",
            "Schedule of Charges",
        ],
    ),
    QueryCase(
        name="Loan information asks loan type",
        messages=["Loan Information"],
        sources={"loan-router"},
        must_contain=["Which loan type"],
        quick_actions_contain=["Retail Loans", "SME Loans"],
        quick_actions_not_contain=["Suggest Loan"],
    ),
    QueryCase(
        name="Retail loan asks loan category",
        messages=["Loan Information", "Retail Loans"],
        sources={"loan-router"},
        must_contain=["Which Retail loan category"],
        quick_actions_contain=["Personal Loan", "Home Loan", "Auto Loan"],
    ),
    QueryCase(
        name="Retail Home Loan category includes Islamic Home Finance",
        messages=["Loan Information", "Retail Loans", "Home Loan"],
        sources={"loan-router"},
        must_contain=["EBL Retail Home Loan options include"],
        quick_actions_contain=["EBL Home Loan", "EBL Islamic Home Finance"],
    ),
    QueryCase(
        name="Retail Auto Loan category includes Islamic Auto Finance",
        messages=["Loan Information", "Retail Loans", "Auto Loan"],
        sources={"loan-router"},
        must_contain=["EBL Retail Auto Loan options include"],
        quick_actions_contain=["EBL Auto Loan", "EBL Islamic Auto Finance"],
    ),
    QueryCase(
        name="Islamic Home Finance opens loan details",
        messages=["EBL Islamic Home Finance"],
        sources={"loan-router"},
        must_contain=[
            "EBL Islamic Home Finance features",
            "Financing amount",
            "BDT 5,00,000 to 4,00,00,000",
        ],
        must_not_contain=["Please specify what you want to know about Islamic"],
    ),
    QueryCase(
        name="Islamic Auto Finance opens loan details",
        messages=["EBL Islamic Auto Finance"],
        sources={"loan-router"},
        must_contain=[
            "EBL Islamic Auto Finance features",
            "Brand new, reconditioned and pre-owned car",
            "Repayment tenor from 12 months to 72 months",
        ],
        must_not_contain=["Please specify what you want to know about Islamic"],
    ),
    QueryCase(
        name="Loan information back returns main menu",
        messages=["Loan Information", "Retail Loans", "Back"],
        sources={"greeting-handler"},
        must_contain=["Welcome to Eastern Bank AI Assistant"],
        quick_actions_contain=[
            "Open an Account",
            "Loan Information",
            "Card Information",
            "Schedule of Charges",
        ],
    ),
    QueryCase(
        name="Schedule of charges asks schedule type",
        messages=["Schedule of Charges"],
        sources={"schedule-charges-menu"},
        must_contain=["Which banking charge"],
        must_not_contain=["Last updated:"],
        quick_actions_contain=["Retail Charges", "SME Charges", "Corporate Charges", "Card Charges"],
    ),
    QueryCase(
        name="Retail charges show charge categories",
        messages=["Schedule of Charges", "Retail Charges"],
        sources={"retail-charge-menu"},
        must_contain=["Which Retail charge category"],
        must_not_contain=["Last updated:"],
        quick_actions_contain=["Account & Deposit Charges", "Loan Charges", "Locker Charges"],
    ),
    QueryCase(
        name="Retail home loan processing fee is precise",
        messages=["retail home loan processing fee above BDT 50 lakh"],
        sources={"charge-database"},
        must_contain=[
            "Home Loan",
            "0.30%",
            "BDT 20,000",
            "VAT",
            "Source: EBL Schedule of Charges",
            "Last updated:",
        ],
        must_not_contain=["Credit Cards lending rate", "Savings Account"],
    ),
    QueryCase(
        name="SME loan processing fee is precise",
        messages=["sme loan processing fee"],
        sources={"charge-database"},
        must_contain=["SME Loan processing fee", "BDT 15,000", "BDT 20,000"],
        must_not_contain=["Credit Cards lending rate"],
    ),
    QueryCase(
        name="Specific Subidha closing fee stays specific",
        messages=["subidha closing account fee"],
        sources={"charge-database"},
        must_contain=["Shubidha Account closing charge", "BDT 300 + VAT"],
        must_not_contain=["Savings Account", "RFCD Account"],
    ),
    QueryCase(
        name="Locker charges include locker sizes",
        messages=["locker fees"],
        sources={"charge-database"},
        must_contain=["Locker charges", "Locker - Small", "Locker - Medium", "Locker - Large"],
        must_not_contain=["Certificate fee"],
    ),
    QueryCase(
        name="Card supplementary charge stays in card charges",
        messages=["platinum credit card supplementary card charge"],
        sources={"card-charge-menu"},
        must_contain=[
            "Visa Platinum",
            "Supplementary card",
            "BDT 2,000",
            "Source: EBL Schedule of Charges",
            "Last updated:",
        ],
        must_not_contain=["Credit Cards lending rate"],
    ),
    QueryCase(
        name="Army card replacement fee works",
        messages=["card replacement fee for army card"],
        sources={"card-charge-menu"},
        must_contain=["Visa Army/Air Force/Navy Platinum", "Card replacement fee", "BDT 1,200"],
        must_not_contain=["Please specify"],
    ),
    QueryCase(
        name="Credit card menu uses official EBL card names",
        messages=["Card Information", "Credit Card"],
        sources={"card-router"},
        must_contain=["EBL Credit Card options include"],
        quick_actions_contain=[
            "EBL Diners Club International Credit Card",
            "EBL Vroom Fuel Card",
            "EBL Mastercard World Elite Biometric Metal Credit Card",
        ],
        quick_actions_not_contain=["Diners Club Credit Card"],
    ),
    QueryCase(
        name="Diners credit card shows official main features",
        messages=["EBL Diners Club International Credit Card"],
        sources={"card-router"},
        must_contain=[
            "EBL Diners Club International Credit Card main features",
            "BDT 30,000",
            "cashback",
        ],
        must_not_contain=["details:\n\nDetails link"],
    ),
    QueryCase(
        name="Vroom fuel card shows official main features",
        messages=["EBL Vroom Fuel Card"],
        sources={"card-router"},
        must_contain=[
            "EBL Vroom Fuel Card main features",
            "Fuel stations",
            "spending limit",
        ],
        must_not_contain=["details:\n\nDetails link"],
    ),
    QueryCase(
        name="World Elite biometric card shows official main features",
        messages=["EBL Mastercard World Elite Biometric Metal Credit Card"],
        sources={"card-router"},
        must_contain=[
            "EBL Mastercard World Elite Biometric Metal Credit Card main features",
            "Biometric Metal Credit Card",
            "Mastercard Concierge Service",
        ],
        must_not_contain=["details:\n\nDetails link"],
    ),
    QueryCase(
        name="Card information back returns main menu",
        messages=["Card Information", "Credit Card", "Back"],
        sources={"greeting-handler"},
        must_contain=["Welcome to Eastern Bank AI Assistant"],
        quick_actions_contain=[
            "Open an Account",
            "Card Information",
            "Schedule of Charges",
            "Interest Rate",
        ],
    ),
    QueryCase(
        name="Prepaid card menu uses official EBL prepaid names",
        messages=["Card Information", "Prepaid Card"],
        sources={"card-router"},
        must_contain=["EBL Prepaid Card options include"],
        quick_actions_contain=[
            "EBL Visa Lifestyle Prepaid Card",
            "EBL-Daraz Visa Co-brand Prepaid Card",
            "EBL-Banglalink Mastercard Co-Brand Prepaid Card",
            "EBL Mastercard Aqua Platinum Vertical Prepaid Card",
        ],
        quick_actions_not_contain=[
            "EBL Virtual Prepaid Card",
            "EBL Oil & Gas Card",
        ],
    ),
    QueryCase(
        name="Payroll prepaid card shows official main features",
        messages=["EBL Payroll Card"],
        sources={"card-router"},
        must_contain=[
            "EBL Payroll Card main features",
            "Efficient Salary Disbursement",
            "Zero balanced prepaid card",
        ],
        must_not_contain=["Three Steps of EBL Payroll Package"],
    ),
    QueryCase(
        name="Daraz prepaid card shows official main features",
        messages=["EBL-Daraz Visa Co-brand Prepaid Card"],
        sources={"card-router"},
        must_contain=[
            "EBL-Daraz Visa Co-brand Prepaid Card main features",
            "Dual Currency EMV Secured Prepaid Card",
            "Contactless Prepaid Card",
        ],
        must_not_contain=["details:\n\nDetails link"],
    ),
    QueryCase(
        name="Aqua women prepaid alias shows official main features",
        messages=["EBL MASTERCARD AQUA WOMEN"],
        sources={"card-router"},
        must_contain=[
            "EBL Mastercard Aqua Women Prepaid Card main features",
            "Exclusively for Bangladeshi Women",
            "Reduced issuance fee",
        ],
        must_not_contain=["details:\n\nDetails link"],
    ),
    QueryCase(
        name="Interest rate asks rate type",
        messages=["Interest Rate"],
        sources={"interest-rate-router"},
        must_contain=["Which interest rate"],
        must_not_contain=["Last updated:"],
        quick_actions_contain=["Deposit Rate", "Lending Rate"],
    ),
    QueryCase(
        name="Deposit rate shows deposit categories",
        messages=["Interest Rate", "Deposit Rate"],
        sources={"interest-rate-router"},
        must_contain=["Please select a deposit rate category"],
        must_not_contain=["Last updated:"],
        quick_actions_contain=["CASA Products", "Business Unit: Retail", "Recurring Deposit"],
    ),
    QueryCase(
        name="Retail EBL Super 150 Days shows table",
        messages=["retail ebl super 150 days"],
        sources={"deposit-rate-database"},
        must_contain=[
            "Retail EBL Super 150 Days interest rate",
            "Amount Band",
            "8.50%",
            "Source: EBL Interest Rate",
            "Last updated:",
        ],
        must_not_contain=["Please specify what you want to know about Retail"],
    ),
    QueryCase(
        name="Lending rate shows lending categories",
        messages=["Interest Rate", "Lending Rate"],
        sources={"interest-rate-router"},
        must_contain=["Please select a lending rate category"],
        must_not_contain=["Last updated:"],
        quick_actions_contain=["Transport", "Consumer Finance", "Trade & Commerce"],
    ),
    QueryCase(
        name="Water transport lending rate works",
        messages=["Water Transport (excluding Fishing Boats) rate"],
        sources={"lending-rate-database"},
        must_contain=[
            "Water Transport",
            "Declared Rate",
            "13.00%",
            "12.00%",
            "14.00%",
            "Source: EBL Interest Rate",
            "Last updated:",
        ],
        must_not_contain=["Please select a deposit rate category"],
    ),
    QueryCase(
        name="Complaint cell returns official complaint info",
        messages=["Complaint Cell"],
        sources={"complaint-cell-agent"},
        must_contain=["EBL Complaint Cell", "ccs.cmc@ebl-bd.com", "https://dgzip.ebl-bd.com/query/"],
        must_not_contain=["info@ebl-bd.com"],
    ),
    QueryCase(
        name="Complaint mail returns complaint email only",
        messages=["complaint mail"],
        sources={"complaint-cell-direct-agent"},
        must_contain=["Complaint Cell email", "ccs.cmc@ebl-bd.com"],
        must_not_contain=["info@ebl-bd.com"],
    ),
    QueryCase(
        name="Locate Us shows district buttons first",
        messages=["Locate Us"],
        sources={"branch-locator-agent"},
        must_contain=["Which district branch do you want to locate?"],
        quick_actions_contain=[
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
        ],
        quick_actions_not_contain=["Gulshan", "Mirpur", "Dhanmondi"],
    ),
    QueryCase(
        name="Schedule charges overrides branch district prompt",
        messages=["Locate Us", "Schedule of Charges"],
        sources={"schedule-charges-menu"},
        must_contain=["Which banking charge"],
        must_not_contain=["I could not find a matching EBL branch"],
        quick_actions_contain=["Retail Charges", "SME Charges", "Corporate Charges", "Card Charges"],
    ),
    QueryCase(
        name="Schedule charges overrides branch area prompt",
        messages=["Locate Us", "Barishal", "Schedule of Charges"],
        sources={"schedule-charges-menu"},
        must_contain=["Which banking charge"],
        must_not_contain=["I could not find a matching EBL branch"],
        quick_actions_contain=["Retail Charges", "SME Charges", "Corporate Charges", "Card Charges"],
    ),
    QueryCase(
        name="Bagerhat district selection asks for Bagerhat area",
        messages=["Locate Us", "Bagerhat"],
        sources={"branch-locator-agent"},
        must_contain=["Please tell me your area", "Mongla in Bagerhat"],
        quick_actions_not_contain=["Mongla"],
    ),
    QueryCase(
        name="Barishal district selection asks for Barishal area",
        messages=["Locate Us", "Barishal"],
        sources={"branch-locator-agent"},
        must_contain=["Please tell me your area", "Barishal Branch in Barishal"],
    ),
    QueryCase(
        name="Bogura district selection asks for Bogura area",
        messages=["Locate Us", "Bogura"],
        sources={"branch-locator-agent"},
        must_contain=["Please tell me your area", "Bogura Branch in Bogura"],
    ),
    QueryCase(
        name="Brahmanbaria district selection asks for Brahmanbaria area",
        messages=["Locate Us", "Brahmanbaria"],
        sources={"branch-locator-agent"},
        must_contain=["Please tell me your area", "Brahmanbaria Branch in Brahmanbaria"],
    ),
    QueryCase(
        name="Dhaka district selection asks for Dhaka area",
        messages=["Locate Us", "Dhaka"],
        sources={"branch-locator-agent"},
        must_contain=["Please tell me your area", "Gulshan in Dhaka"],
        quick_actions_not_contain=["Gulshan", "Mirpur", "Dhanmondi"],
    ),
    QueryCase(
        name="Chattogram district selection asks for Chattogram area",
        messages=["Locate Us", "Chattogram"],
        sources={"branch-locator-agent"},
        must_contain=["Please tell me your area", "Agrabad in Chattogram"],
        quick_actions_not_contain=["Agrabad"],
    ),
    QueryCase(
        name="Coxs Bazar district selection asks for Coxs Bazar area",
        messages=["Locate Us", "Coxs Bazar"],
        sources={"branch-locator-agent"},
        must_contain=["Please tell me your area", "Cox's Bazar Branch in Cox's Bazar"],
    ),
    QueryCase(
        name="Cumilla district selection asks for Cumilla area",
        messages=["Locate Us", "Cumilla"],
        sources={"branch-locator-agent"},
        must_contain=["Please tell me your area", "Cumilla SME-AGRI Branch in Cumilla"],
    ),
    QueryCase(
        name="Faridpur district selection asks for Faridpur area",
        messages=["Locate Us", "Faridpur"],
        sources={"branch-locator-agent"},
        must_contain=["Please tell me your area", "Faridpur Branch in Faridpur"],
    ),
    QueryCase(
        name="Feni district selection asks for Feni area",
        messages=["Locate Us", "Feni"],
        sources={"branch-locator-agent"},
        must_contain=["Please tell me your area", "Feni SME-AGRI Branch in Feni"],
    ),
    QueryCase(
        name="Gazipur district selection asks for Gazipur area",
        messages=["Locate Us", "Gazipur"],
        sources={"branch-locator-agent"},
        must_contain=["Please tell me your area", "Board Bazar in Gazipur"],
        quick_actions_not_contain=["Board Bazar"],
    ),
    QueryCase(
        name="Jashore district selection asks for Jashore area",
        messages=["Locate Us", "Jashore"],
        sources={"branch-locator-agent"},
        must_contain=["Please tell me your area", "Jashore Branch in Jashore"],
    ),
    QueryCase(
        name="Kishoreganj district selection asks for Kishoreganj area",
        messages=["Locate Us", "Kishoreganj"],
        sources={"branch-locator-agent"},
        must_contain=["Please tell me your area", "Bhairab in Kishoreganj"],
    ),
    QueryCase(
        name="Khulna district selection asks for Khulna area",
        messages=["Locate Us", "Khulna"],
        sources={"branch-locator-agent"},
        must_contain=["Please tell me your area", "Fulbarigate in Khulna"],
        quick_actions_not_contain=["Fulbarigate"],
    ),
    QueryCase(
        name="Moulvibazar district selection asks for Moulvibazar area",
        messages=["Locate Us", "Moulvibazar"],
        sources={"branch-locator-agent"},
        must_contain=["Please tell me your area", "Moulvibazar Branch in Moulvibazar"],
    ),
    QueryCase(
        name="Mymensingh district selection asks for Mymensingh area",
        messages=["Locate Us", "Mymensingh"],
        sources={"branch-locator-agent"},
        must_contain=["Please tell me your area", "Mymensingh SME-AGRI Branch in Mymensingh"],
    ),
    QueryCase(
        name="Narayanganj district selection asks for Narayanganj area",
        messages=["Locate Us", "Narayanganj"],
        sources={"branch-locator-agent"},
        must_contain=["Please tell me your area", "Sonargaon in Narayanganj"],
        quick_actions_not_contain=["Sonargaon"],
    ),
    QueryCase(
        name="Narsingdi district selection asks for Narsingdi area",
        messages=["Locate Us", "Narsingdi"],
        sources={"branch-locator-agent"},
        must_contain=["Please tell me your area", "Madhabdi in Narsingdi"],
    ),
    QueryCase(
        name="Noakhali district selection asks for Noakhali area",
        messages=["Locate Us", "Noakhali"],
        sources={"branch-locator-agent"},
        must_contain=["Please tell me your area", "Maijdee in Noakhali"],
        quick_actions_not_contain=["Maijdee"],
    ),
    QueryCase(
        name="Rajshahi district selection asks for Rajshahi area",
        messages=["Locate Us", "Rajshahi"],
        sources={"branch-locator-agent"},
        must_contain=["Please tell me your area", "Rajshahi Branch in Rajshahi"],
    ),
    QueryCase(
        name="Rangpur district selection asks for Rangpur area",
        messages=["Locate Us", "Rangpur"],
        sources={"branch-locator-agent"},
        must_contain=["Please tell me your area", "Rangpur Branch in Rangpur"],
    ),
    QueryCase(
        name="Sylhet district selection asks for Sylhet area",
        messages=["Locate Us", "Sylhet"],
        sources={"branch-locator-agent"},
        must_contain=["Please tell me your area", "Upashahar in Sylhet"],
        quick_actions_not_contain=["Upashahar"],
    ),
    QueryCase(
        name="Tangail district selection asks for Tangail area",
        messages=["Locate Us", "Tangail"],
        sources={"branch-locator-agent"},
        must_contain=["Please tell me your area", "Tangail Branch in Tangail"],
    ),
    QueryCase(
        name="Locate Us Bagerhat area flow shows Mongla branch",
        messages=["Locate Us", "Bagerhat", "Mongla"],
        sources={"branch-locator-agent"},
        must_contain=[
            "EBL Bagerhat branches matching Mongla",
            "Mongla Branch",
            "Routing No.",
            "https://www.ebl.com.bd/branches",
        ],
        must_not_contain=["Source:"],
    ),
    QueryCase(
        name="Locate Us Coxs Bazar area flow shows Coxs Bazar branch",
        messages=["Locate Us", "Coxs Bazar", "Coxs Bazar Branch"],
        sources={"branch-locator-agent"},
        must_contain=[
            "EBL Cox's Bazar branches matching Bazar",
            "Cox's Bazar Branch",
            "Routing No.",
            "https://www.ebl.com.bd/branches",
        ],
        must_not_contain=["Source:"],
    ),
    QueryCase(
        name="Locate Us Kishoreganj area flow shows Bhairab branch",
        messages=["Locate Us", "Kishoreganj", "Bhairab"],
        sources={"branch-locator-agent"},
        must_contain=[
            "EBL Kishoreganj branches matching Bhairab",
            "Bhairab SME",
            "Routing No.",
            "https://www.ebl.com.bd/branches",
        ],
        must_not_contain=["Source:"],
    ),
    QueryCase(
        name="Locate Us Narsingdi area flow shows Madhabdi branch",
        messages=["Locate Us", "Narsingdi", "Madhabdi"],
        sources={"branch-locator-agent"},
        must_contain=[
            "EBL Narsingdi branches matching Madhabdi",
            "Madhabdi SME",
            "Routing No.",
            "https://www.ebl.com.bd/branches",
        ],
        must_not_contain=["Source:"],
    ),
    QueryCase(
        name="Locate Us Dhaka area flow shows Gulshan branch",
        messages=["Locate Us", "Dhaka", "Gulshan"],
        sources={"branch-locator-agent"},
        must_contain=[
            "EBL Dhaka branches matching Gulshan",
            "Gulshan Branch",
            "Routing No.",
            "https://www.ebl.com.bd/branches",
        ],
        must_not_contain=["Source:"],
    ),
    QueryCase(
        name="Locate Us Chattogram area flow shows Agrabad branch",
        messages=["Locate Us", "Chattogram", "Agrabad"],
        sources={"branch-locator-agent"},
        must_contain=[
            "EBL Chattogram branches matching Agrabad",
            "Agrabad Branch",
            "Routing No.",
            "https://www.ebl.com.bd/branches",
        ],
        must_not_contain=["Source:"],
    ),
    QueryCase(
        name="Locate Us Gazipur area flow shows Board Bazar branch",
        messages=["Locate Us", "Gazipur", "Board Bazar"],
        sources={"branch-locator-agent"},
        must_contain=[
            "EBL Gazipur branches matching Board Bazar",
            "Board Bazar Branch",
            "Routing No.",
            "https://www.ebl.com.bd/branches",
        ],
        must_not_contain=["Source:"],
    ),
    QueryCase(
        name="Locate Us Khulna area flow shows Fulbarigate branch",
        messages=["Locate Us", "Khulna", "Fulbarigate"],
        sources={"branch-locator-agent"},
        must_contain=[
            "EBL Khulna branches matching Fulbarigate",
            "Fulbarigate Branch",
            "Routing No.",
            "https://www.ebl.com.bd/branches",
        ],
        must_not_contain=["Source:"],
    ),
    QueryCase(
        name="Locate Us Narayanganj area flow shows Sonargaon branch",
        messages=["Locate Us", "Narayanganj", "Sonargaon"],
        sources={"branch-locator-agent"},
        must_contain=[
            "EBL Narayanganj branches matching Sonargaon",
            "Sonargaon Branch",
            "Routing No.",
            "https://www.ebl.com.bd/branches",
        ],
        must_not_contain=["Source:"],
    ),
    QueryCase(
        name="Locate Us Noakhali area flow shows Maijdee branch",
        messages=["Locate Us", "Noakhali", "Maijdee"],
        sources={"branch-locator-agent"},
        must_contain=[
            "EBL Noakhali branches matching Maijdee",
            "Maijdee Branch",
            "Routing No.",
            "https://www.ebl.com.bd/branches",
        ],
        must_not_contain=["Source:"],
    ),
    QueryCase(
        name="Locate Us Sylhet area flow shows Upashahar branch",
        messages=["Locate Us", "Sylhet", "Upashahar"],
        sources={"branch-locator-agent"},
        must_contain=[
            "EBL Sylhet branches matching Upashahar",
            "Upashahar Branch",
            "Routing No.",
            "https://www.ebl.com.bd/branches",
        ],
        must_not_contain=["Source:"],
    ),
    QueryCase(
        name="Direct nearest branch query shows Gulshan branches",
        messages=["nearest branch in Gulshan"],
        sources={"branch-locator-agent"},
        must_contain=[
            "EBL Dhaka branches matching Gulshan",
            "Gulshan Branch",
            "Routing No.",
            "info@ebl-bd.com",
            "https://www.ebl.com.bd/branches",
        ],
        must_not_contain=["I could not find", "Source:"],
    ),
    QueryCase(
        name="Direct nearest branch query shows Mirpur branches",
        messages=["nearest branch in Mirpur"],
        sources={"branch-locator-agent"},
        must_contain=[
            "EBL Dhaka branches matching Mirpur",
            "Mirpur Branch",
            "Routing No.",
        ],
        must_not_contain=["Please tell me your Dhaka area"],
    ),
    QueryCase(
        name="Direct nearest branch query shows Chattogram branches",
        messages=["nearest branch in Chattogram"],
        sources={"branch-locator-agent"},
        must_contain=[
            "EBL Chattogram branches matching your area",
            "Chattogram",
            "Routing No.",
            "https://www.ebl.com.bd/branches",
        ],
        must_not_contain=["Source:"],
    ),
    QueryCase(
        name="Direct nearest branch query shows Agrabad branch",
        messages=["nearest branch in Agrabad"],
        sources={"branch-locator-agent"},
        must_contain=[
            "EBL Chattogram branches matching Agrabad",
            "Agrabad",
            "Routing No.",
        ],
        must_not_contain=["Please tell me your district or area"],
    ),
    QueryCase(
        name="Direct nearest branch query shows Gazipur branches",
        messages=["nearest branch in Gazipur"],
        sources={"branch-locator-agent"},
        must_contain=[
            "EBL Gazipur branches matching your area",
            "Gazipur",
            "Routing No.",
            "https://www.ebl.com.bd/branches",
        ],
        must_not_contain=["Source:"],
    ),
    QueryCase(
        name="Direct nearest branch query shows Board Bazar branch",
        messages=["nearest branch in Board Bazar"],
        sources={"branch-locator-agent"},
        must_contain=[
            "Board Bazar Branch",
            "Routing No.",
        ],
        must_not_contain=["Please tell me your district or area"],
    ),
    QueryCase(
        name="Direct nearest branch query shows Khulna branches",
        messages=["nearest branch in Khulna"],
        sources={"branch-locator-agent"},
        must_contain=[
            "EBL Khulna branches matching your area",
            "Khulna",
            "Routing No.",
            "https://www.ebl.com.bd/branches",
        ],
        must_not_contain=["Source:"],
    ),
    QueryCase(
        name="Direct nearest branch query shows Fulbarigate branch",
        messages=["nearest branch in Fulbarigate"],
        sources={"branch-locator-agent"},
        must_contain=[
            "EBL Khulna branches matching Fulbarigate",
            "Fulbarigate Branch",
            "Routing No.",
        ],
        must_not_contain=["Please tell me your district or area"],
    ),
    QueryCase(
        name="Direct nearest branch query shows Narayanganj branches",
        messages=["nearest branch in Narayanganj"],
        sources={"branch-locator-agent"},
        must_contain=[
            "EBL Narayanganj branches matching your area",
            "Narayanganj",
            "Routing No.",
            "https://www.ebl.com.bd/branches",
        ],
        must_not_contain=["Source:"],
    ),
    QueryCase(
        name="Direct nearest branch query shows Sonargaon branch",
        messages=["nearest branch in Sonargaon"],
        sources={"branch-locator-agent"},
        must_contain=[
            "EBL branches matching Sonargaon",
            "Sonargaon Branch",
            "Routing No.",
        ],
        must_not_contain=["Please tell me your district or area"],
    ),
    QueryCase(
        name="Direct nearest branch query shows Noakhali branches",
        messages=["nearest branch in Noakhali"],
        sources={"branch-locator-agent"},
        must_contain=[
            "EBL Noakhali branches matching your area",
            "Noakhali",
            "Routing No.",
            "https://www.ebl.com.bd/branches",
        ],
        must_not_contain=["Source:"],
    ),
    QueryCase(
        name="Direct nearest branch query shows Maijdee branch",
        messages=["nearest branch in Maijdee"],
        sources={"branch-locator-agent"},
        must_contain=[
            "EBL Noakhali branches matching Maijdee",
            "Maijdee Branch",
            "Routing No.",
        ],
        must_not_contain=["Please tell me your district or area"],
    ),
    QueryCase(
        name="Direct nearest branch query shows Sylhet branches",
        messages=["nearest branch in Sylhet"],
        sources={"branch-locator-agent"},
        must_contain=[
            "EBL Sylhet branches matching your area",
            "Sylhet",
            "Routing No.",
            "https://www.ebl.com.bd/branches",
        ],
        must_not_contain=["Source:"],
    ),
    QueryCase(
        name="Direct nearest branch query shows Upashahar branch",
        messages=["nearest branch in Upashahar"],
        sources={"branch-locator-agent"},
        must_contain=[
            "EBL Sylhet branches matching Upashahar",
            "Upashahar Branch",
            "Routing No.",
        ],
        must_not_contain=["Please tell me your district or area"],
    ),
    QueryCase(
        name="Unknown Dhaka area gives branch fallback",
        messages=["nearest branch in Tongi"],
        sources={"branch-locator-agent"},
        must_contain=[
            "I could not find a matching EBL branch in "
        ],
    ),
    QueryCase(
        name="Contact us returns general contact info",
        messages=["Contact Us"],
        sources={"contact-agent"},
        must_contain=["info@ebl-bd.com", "16230"],
    ),
]


def normalize_text(text):
    return " ".join(str(text or "").lower().split())


def prepare_environment():
    main.understand_user_query_with_groq = build_fallback_understanding
    main.safe_debug_print = lambda *args, **kwargs: None
    main.ensure_charge_database_ready()
    main.ensure_deposit_rate_database_ready()
    main.ensure_lending_rate_database_ready()
    main.ensure_branch_database_ready(auto_scrape=True)
    main.import_account_types(clear_existing=True)
    main.ensure_account_types_ready()
    main.import_loan_types(clear_existing=True)
    main.ensure_loan_types_ready()
    create_database()


def run_conversation(test_case):
    session_id = f"test-suite-{uuid.uuid4().hex}"
    response = None

    for message in test_case.messages:
        response = main.chat(ChatRequest(message=message, session_id=session_id))

    return session_id, response


def evaluate_response(test_case, response):
    errors = []
    reply = response.reply or ""
    normalized_reply = normalize_text(reply)
    quick_actions = response.quick_actions or []

    if test_case.sources and response.source not in test_case.sources:
        expected_sources = ", ".join(sorted(test_case.sources))
        errors.append(f"source expected one of [{expected_sources}], got [{response.source}]")

    for expected_text in test_case.must_contain:
        if normalize_text(expected_text) not in normalized_reply:
            errors.append(f"missing text: {expected_text}")

    for blocked_text in test_case.must_not_contain:
        if normalize_text(blocked_text) in normalized_reply:
            errors.append(f"unexpected text: {blocked_text}")

    for expected_action in test_case.quick_actions_contain:
        if expected_action not in quick_actions:
            errors.append(f"missing quick action: {expected_action}")

    for blocked_action in test_case.quick_actions_not_contain:
        if blocked_action in quick_actions:
            errors.append(f"unexpected quick action: {blocked_action}")

    return errors


def cleanup_sessions(session_ids):
    if not session_ids:
        return

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    for session_id in session_ids:
        cursor.execute("DELETE FROM chat_logs WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM session_memory WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM pending_complaints WHERE session_id = ?", (session_id,))
        main.SCOPED_NAVIGATION_STACKS.pop(session_id, None)

    connection.commit()
    connection.close()


def selected_cases(case_name):
    if not case_name:
        return TEST_CASES

    normalized_case_name = normalize_text(case_name)
    return [
        test_case
        for test_case in TEST_CASES
        if normalized_case_name in normalize_text(test_case.name)
    ]


def reply_preview(reply, max_length=220):
    compact_reply = " | ".join(str(reply or "").splitlines())

    if len(compact_reply) <= max_length:
        return compact_reply

    return compact_reply[:max_length].rstrip() + "..."


def main_entry():
    parser = argparse.ArgumentParser(description="Run EBL chatbot query regression checks.")
    parser.add_argument(
        "--case",
        help="Run only cases whose name contains this text.",
    )
    parser.add_argument(
        "--keep-sessions",
        action="store_true",
        help="Keep test chat rows in SQLite for debugging.",
    )
    args = parser.parse_args()

    cases = selected_cases(args.case)

    if not cases:
        print(f"No test cases matched: {args.case}")
        return 2

    prepare_environment()

    session_ids = []
    passed = 0
    failed = 0

    for index, test_case in enumerate(cases, start=1):
        session_id, response = run_conversation(test_case)
        session_ids.append(session_id)
        errors = evaluate_response(test_case, response)

        if errors:
            failed += 1
            print(f"FAIL {index:02d}. {test_case.name}")
            print(f"  Messages: {' -> '.join(test_case.messages)}")
            print(f"  Source: {response.source}")
            print(f"  Quick actions: {response.quick_actions}")
            print(f"  Reply: {reply_preview(response.reply)}")

            for error in errors:
                print(f"  - {error}")
        else:
            passed += 1
            print(f"PASS {index:02d}. {test_case.name} [{response.source}]")

    if not args.keep_sessions:
        cleanup_sessions(session_ids)

    print()
    print(f"Result: {passed} passed, {failed} failed, {len(cases)} total")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main_entry())
