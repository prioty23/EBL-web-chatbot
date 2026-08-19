"use client";

import { useLanguage } from "@/components/LanguageProvider";

export default function NewsSection() {
  const { t } = useLanguage();

  return (
    <section id="news" className="section-padding bg-[#F8FAFC]">
      <div className="container-custom">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#005B96]">
              {t.news.eyebrow}
            </p>
            <h2 className="mt-3 text-3xl font-semibold text-gray-950 sm:text-4xl">
              {t.news.title}
            </h2>
            <p className="mt-4 text-base leading-7 text-gray-600 sm:text-lg sm:leading-8">
              {t.news.subtitle}
            </p>
          </div>
          <a href="#news" className="btn-secondary self-start">
            {t.news.viewAll}
          </a>
        </div>

        <div className="mt-10 grid gap-6 lg:mt-12 lg:grid-cols-3">
          {t.news.items.map((item: string[], index: number) => (
            <article
              key={item[0]}
              className="group overflow-hidden rounded-[1.75rem] border border-gray-200 bg-white shadow-sm transition duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-[#003F68]/10"
            >
              <div
                className={`relative flex h-44 items-end overflow-hidden p-6 ${
                  index === 0
                    ? "bg-[linear-gradient(135deg,#005B96,#003F68)]"
                    : index === 1
                      ? "bg-[linear-gradient(135deg,#003F68,#005B96)]"
                      : "bg-[linear-gradient(135deg,#FFC629,#D99D00)]"
                }`}
              >
                <div className="absolute -right-8 -top-8 h-36 w-36 rounded-full border-[28px] border-white/10" />
                <div className="absolute bottom-6 right-6 h-12 w-24 border-b-2 border-r-2 border-white/20" />
                <p className="relative break-words text-xs font-bold tracking-[0.24em] text-white/85 sm:text-sm sm:tracking-[0.28em]">
                  Eastern Bank PLC / {item[4]}
                </p>
              </div>
              <div className="p-6 sm:p-7">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <span className="rounded-full bg-[#005B96]/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-[#005B96]">
                    {item[1]}
                  </span>
                  <span className="text-sm text-gray-500">{item[2]}</span>
                </div>
                <h3 className="mt-5 text-xl font-semibold leading-tight text-gray-950 sm:text-2xl">
                  {item[0]}
                </h3>
                <p className="mt-4 text-sm leading-7 text-gray-600 sm:text-base">{item[5]}</p>
                <a
                  href="#news"
                  className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-gray-100 pt-5 text-sm font-semibold text-[#005B96]"
                >
                  <span>{t.news.readUpdate}</span>
                  <span className="flex items-center gap-3 text-xs font-normal text-gray-400">
                    {item[3]}
                    <span className="text-base text-[#005B96] transition group-hover:translate-x-1" aria-hidden="true">{"\u2192"}</span>
                  </span>
                </a>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
