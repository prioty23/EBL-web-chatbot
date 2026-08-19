"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";

const navItems = [
  {
    label: "About EBL",
    href: "https://www.ebl.com.bd/about",
    links: [
      { label: "EBL At A Glance", href: "https://www.ebl.com.bd/about/ebl-at-a-glance" },
      { label: "Board of Directors", href: "https://www.ebl.com.bd/about/board-of-directors" },
      { label: "Management Committee", href: "https://www.ebl.com.bd/about/management-committee" },
      { label: "Awards", href: "https://www.ebl.com.bd/about/awards" },
    ],
  },
  {
    label: "Retail & SME",
    href: "https://www.ebl.com.bd/retail/retail-deposit",
    links: [
      { label: "Retail Deposit", href: "https://www.ebl.com.bd/retail/retail-deposit" },
      { label: "Retail Loan", href: "https://www.ebl.com.bd/retail/retail-loan" },
      { label: "EBL Cards", href: "https://www.ebl.com.bd/retail/EBL-Cards" },
      { label: "SME Deposits", href: "https://www.ebl.com.bd/sme/sme-deposits" },
      { label: "SME Loans", href: "https://www.ebl.com.bd/sme/sme-loans" },
    ],
  },
  {
    label: "Corporate",
    href: "https://www.ebl.com.bd/corporate",
    links: [
      { label: "Corporate Banking", href: "https://www.ebl.com.bd/corporate/banking/Corporate-Banking-Division" },
      { label: "Trade Services", href: "https://www.ebl.com.bd/corporate/trade-services" },
      { label: "Cash Management", href: "https://www.ebl.com.bd/corporate/cash-management" },
    ],
  },
  {
    label: "Islamic Banking",
    href: "https://www.ebl.com.bd/islamicbanking",
    links: [],
  },
  {
    label: "Treasury, FIs & OBU",
    href: "https://www.ebl.com.bd/treasury",
    links: [
      { label: "Treasury", href: "https://www.ebl.com.bd/treasury" },
      { label: "Financial Institutions", href: "https://www.ebl.com.bd/fi" },
      { label: "Offshore Banking Unit", href: "https://www.ebl.com.bd/obu" },
    ],
  },
  {
    label: "Investor Relations",
    href: "https://www.ebl.com.bd/investor-relations",
    links: [
      { label: "Financial Reports", href: "https://www.ebl.com.bd/financial-reports" },
      { label: "Price Sensitive Information", href: "https://www.ebl.com.bd/price-sensitive-information" },
      { label: "Disclosures", href: "https://www.ebl.com.bd/disclosures" },
    ],
  },
  {
    label: "Career",
    href: "https://www.ebl.com.bd/career",
    links: [],
  },
];

function ChevronDownIcon() {
  return (
    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" aria-hidden="true">
      <path d="m6 9 6 6 6-6" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="m20 20-4.2-4.2M18 10.5a7.5 7.5 0 1 1-15 0 7.5 7.5 0 0 1 15 0Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeWidth="2.5"
      />
    </svg>
  );
}

function InternationalDeskLogo() {
  return (
    <svg className="h-9 w-[132px] shrink-0" viewBox="0 0 160 44" aria-hidden="true">
      <defs>
        <clipPath id="international-desk-globe">
          <circle cx="22" cy="22" r="20" />
        </clipPath>
      </defs>
      <circle cx="22" cy="22" r="20" fill="#FFC629" />
      <g clipPath="url(#international-desk-globe)" fill="#FFFFFF">
        <path d="M16 3.5c4.6 1.4 6.7 4.5 5.8 8.2-.6 2.5-2.7 3.6-4.7 4.8-1.7 1-3.3 2-3.7 4.1-.5 2.8 1.4 4.7 4.8 4.9 2.4.1 3.7 1.1 3.8 3.1.1 1.9-1.2 3.8-3.3 4.7-2.3 1-4.5.3-6.7-2-3.1-3.2-4.7-8.6-4-13.7C8.9 10.8 11.7 5.9 16 3.5Z" />
        <path d="M27.4 4.4c6.5 1.9 11.2 7.9 12 14.8l-5.3-1.7-3.7 2.6-4.8-1.5-1.7-5.3 3.6-2.6-.1-6.3Z" />
        <path d="M35.5 25.4c-1.1 6.2-5.8 11.5-12 13.3l.8-5.5 3.8-2.1 1.1-4.6 6.3-1.1Z" />
        <path d="M3.2 25.2c3.1-.8 5.5-.3 7.1 1.6l1.4 4.6-2.4 3.2c-3-2.2-5.2-5.5-6.1-9.4Z" />
      </g>
      <text x="50" y="17" fill="#4C4C4F" fontFamily="Arial, Helvetica, sans-serif" fontSize="15" fontWeight="700">
        International
      </text>
      <text x="49" y="39" fill="#4C4C4F" fontFamily="Arial, Helvetica, sans-serif" fontSize="32" fontWeight="900">
        desk
      </text>
    </svg>
  );
}

export default function Header() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 bg-white shadow-sm">
      <div className="flex w-full items-center justify-between gap-3 px-4 py-4 sm:px-6 lg:px-7">
        <Link
          href="/"
          onClick={() => setMenuOpen(false)}
          className="flex shrink-0 items-center transition hover:opacity-95"
          aria-label="Eastern Bank PLC home"
        >
          <span className="flex h-10 w-[52px] items-center justify-center rounded-l-lg border border-r-0 border-gray-200 bg-white py-1 shadow-sm sm:h-11 sm:w-[56px]">
            <Image
              src="/ebl-header-mark.png"
              alt=""
              width={54}
              height={40}
              className="h-full w-full object-contain"
            />
          </span>
          <span className="flex h-10 items-center rounded-r-lg bg-[#FFC629] px-3 font-serif text-[17px] font-semibold leading-none text-[#005B96] shadow-sm sm:h-11 sm:px-4 sm:text-[21px]">
            Eastern Bank PLC.
          </span>
        </Link>

        <nav className="hidden min-w-0 flex-1 flex-nowrap items-center justify-center gap-0.5 xl:flex 2xl:gap-1">
          {navItems.map((item, index) => (
            <div key={item.label} className="group relative shrink-0">
              <a
                href={item.href}
                className="inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2 py-2 text-[13px] font-medium text-gray-700 transition hover:bg-[#005B96]/5 hover:text-[#005B96] 2xl:px-3 2xl:text-sm"
              >
                {item.label}
                {item.links.length > 0 ? <ChevronDownIcon /> : null}
              </a>
              {item.links.length > 0 ? (
                <div
                  className={`invisible absolute top-full z-20 mt-3 max-h-[70vh] w-72 overflow-y-auto rounded-[1.5rem] border border-gray-100 bg-white p-3 opacity-0 shadow-xl shadow-black/8 transition duration-200 group-hover:visible group-hover:opacity-100 ${
                    index >= navItems.length - 2 ? "right-0" : "left-0"
                  }`}
                >
                  {item.links.map((link) => (
                    <a
                      key={link.label}
                      href={link.href}
                      className="block rounded-xl px-4 py-3 text-sm text-gray-600 transition hover:bg-[#005B96]/5 hover:text-[#005B96]"
                    >
                      {link.label}
                    </a>
                  ))}
                </div>
              ) : null}
            </div>
          ))}
        </nav>

        <div className="flex shrink-0 items-center gap-2 sm:gap-3">
          <a
            href="https://www.ebl.com.bd/search"
            aria-label="Search Eastern Bank PLC"
            className="hidden text-[#005B96] transition hover:text-[#004C7D] xl:inline-flex"
          >
            <SearchIcon />
          </a>
          <span className="hidden h-9 w-px bg-gray-300 xl:block" />
          <a
            href="https://www.ebl.com.bd/home/internationaldesk"
            aria-label="International Desk"
            className="hidden h-11 items-center rounded-sm border border-gray-100 bg-white px-2 shadow-sm transition duration-200 hover:-translate-y-0.5 hover:shadow-md xl:inline-flex"
          >
            <InternationalDeskLogo />
          </a>
          <button
            type="button"
            aria-label={menuOpen ? "Close menu" : "Open menu"}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((open) => !open)}
            className="inline-flex h-11 w-11 items-center justify-center rounded-full border border-[#005B96]/20 text-[#005B96] transition hover:bg-[#005B96]/5 xl:hidden"
          >
            <span className="sr-only">Toggle navigation</span>
            <div className="flex flex-col gap-1.5">
              <span className={`block h-0.5 w-5 bg-current transition ${menuOpen ? "translate-y-2 rotate-45" : ""}`} />
              <span className={`block h-0.5 w-5 bg-current transition ${menuOpen ? "opacity-0" : ""}`} />
              <span className={`block h-0.5 w-5 bg-current transition ${menuOpen ? "-translate-y-2 -rotate-45" : ""}`} />
            </div>
          </button>
        </div>
      </div>

      {menuOpen ? (
        <div className="border-t border-black/5 bg-white xl:hidden">
          <div className="container-custom space-y-3 py-4">
            {navItems.map((item) => (
              <div key={item.label} className="rounded-2xl border border-gray-100 bg-gray-50/60 px-4 py-3">
                <a
                  href={item.href}
                  onClick={() => setMenuOpen(false)}
                  className="block text-sm font-semibold text-gray-800"
                >
                  {item.label}
                </a>
                {item.links.length > 0 ? <div className="mt-3 space-y-2 pl-4">
                  {item.links.map((link) => (
                    <a
                      key={link.label}
                      href={link.href}
                      onClick={() => setMenuOpen(false)}
                      className="block text-sm text-gray-600 transition hover:text-[#005B96]"
                    >
                      {link.label}
                    </a>
                  ))}
                </div> : null}
              </div>
            ))}
            <a
              href="https://www.ebl.com.bd/search"
              onClick={() => setMenuOpen(false)}
              className="btn-primary mt-3 w-full justify-center gap-2"
            >
              <SearchIcon />
              Search
            </a>
            <a
              href="https://www.ebl.com.bd/home/internationaldesk"
              onClick={() => setMenuOpen(false)}
              className="flex min-h-12 w-full items-center justify-center gap-2 rounded-full border border-gray-200 bg-white px-4 text-sm font-bold text-gray-700 shadow-sm transition hover:border-[#FFC629] hover:bg-[#FFF8DC]"
            >
              <InternationalDeskLogo />
            </a>
          </div>
        </div>
      ) : null}
    </header>
  );
}
