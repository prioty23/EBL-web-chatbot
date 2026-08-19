"use client";

import { useLanguage } from "@/components/LanguageProvider";

const footerAnchors = {
  banking: ["#needs", "#needs", "#needs", "#needs", "#footer"],
  company: ["#footer", "#footer", "#footer", "#footer", "#footer"],
  support: ["#footer", "#footer", "#footer", "#footer", "#footer"],
  legal: ["#footer", "#footer", "#footer"],
};

const EBL_HOTLINE = "16230";
const EBL_EMAIL = "info@ebl-bd.com";

export default function Footer() {
  const { t } = useLanguage();

  return (
    <footer id="footer" className="bg-[#005B96] text-white">
      <div className="container-custom py-16 lg:py-20">
        <div className="rounded-[2rem] border border-white/10 bg-white/5 p-6 shadow-2xl shadow-black/10 sm:p-8 lg:p-10">
          <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#FFC629]">
                {t.footer.newsletter}
              </p>
              <h2 className="mt-3 text-2xl font-semibold tracking-tight sm:text-3xl">
                {t.footer.newsletterTitle}
              </h2>
              <p className="mt-4 max-w-2xl text-sm leading-7 text-blue-50/80 sm:text-base sm:leading-8">
                {t.footer.newsletterText}
              </p>
            </div>

            <form className="flex flex-col gap-4 sm:flex-row">
              <input
                type="email"
                placeholder={t.footer.emailPlaceholder}
                aria-label={t.footer.emailPlaceholder}
                className="h-12 w-full min-w-0 rounded-full border border-white/15 bg-white/10 px-5 text-white placeholder:text-blue-50/50 outline-none transition focus:border-[#FFC629] focus:ring-2 focus:ring-[#FFC629]/20"
              />
              <button
                type="submit"
                className="inline-flex h-12 w-full items-center justify-center rounded-full bg-[#FFC629] px-6 text-sm font-semibold text-[#123047] transition hover:bg-[#F2B800] sm:w-auto"
              >
                {t.footer.subscribe}
              </button>
            </form>
          </div>
        </div>

        <div className="mt-14 grid gap-10 md:grid-cols-2 xl:grid-cols-4">
          <div>
            <p className="text-2xl font-semibold tracking-tight text-white">Eastern Bank PLC</p>
            <p className="mt-4 text-sm leading-7 text-blue-50/75 sm:text-base sm:leading-8">
              {t.footer.description}
            </p>
            <div className="mt-6 space-y-2 text-sm text-blue-50/80">
              <p>
                <span className="text-[#FFC629]">{t.footer.hotline}:</span>{" "}
                {EBL_HOTLINE}
              </p>
              <p className="break-all">
                <span className="text-[#FFC629]">Email:</span> {EBL_EMAIL}
              </p>
            </div>
          </div>

          {[
            [t.footer.bankingTitle, t.footer.bankingLinks, footerAnchors.banking],
            [t.footer.companyTitle, t.footer.companyLinks, footerAnchors.company],
            [t.footer.supportTitle, t.footer.supportLinks, footerAnchors.support],
          ].map(([title, links, anchors]) => (
            <div key={title as string}>
              <h3 className="text-lg font-semibold text-white">{title as string}</h3>
              <div className="mt-5 space-y-3 text-sm text-blue-50/75">
                {(links as string[]).map((item, index) => (
                  <a
                    key={item}
                    href={(anchors as string[])[index]}
                    className="block break-words transition hover:text-[#FFC629]"
                  >
                    {item}
                  </a>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-14 flex flex-col gap-4 border-t border-white/10 pt-6 text-sm text-blue-50/70 md:flex-row md:items-center md:justify-between">
          <p className="break-words">{t.footer.copyright}</p>
          <div className="flex flex-wrap gap-4 sm:gap-5">
            {t.footer.legalLinks.map((item: string, index: number) => (
              <a key={item} href={footerAnchors.legal[index]} className="transition hover:text-[#FFC629]">
                {item}
              </a>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}
