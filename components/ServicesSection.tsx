"use client";

import { useLanguage } from "@/components/LanguageProvider";

const icons = ["\u25CE", "\u25AF", "\u2316", "\u25A3", "?", "\u2261"];
const serviceAnchors = ["#services", "#services", "#footer", "#footer", "#footer", "#footer"];

export default function ServicesSection() {
  const { t } = useLanguage();

  return (
    <section id="services" className="section-padding bg-white">
      <div className="container-custom">
        <div className="mx-auto max-w-3xl text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#005B96]">
            {t.services.eyebrow}
          </p>
          <h2 className="mt-3 text-3xl font-semibold text-gray-950 sm:text-4xl">
            {t.services.title}
          </h2>
          <p className="mt-4 text-base leading-7 text-gray-600 sm:text-lg sm:leading-8">
            {t.services.subtitle}
          </p>
        </div>

        <div className="mt-10 grid gap-4 md:mt-12 md:grid-cols-2 xl:grid-cols-3">
          {t.services.cards.map((item: string[], index: number) => (
            <article
              key={item[0]}
              className="group flex min-h-64 flex-col rounded-[1.5rem] border border-gray-200 bg-[#F8FAFC] p-5 transition duration-300 hover:border-[#FFC629] hover:bg-[#003F68] hover:shadow-xl hover:shadow-[#003F68]/15 sm:p-6"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white text-2xl font-bold text-[#005B96] shadow-sm">
                  <span aria-hidden="true">{icons[index]}</span>
                </div>
                <span className="font-mono text-xs font-bold text-gray-400 transition group-hover:text-[#FFC629]">
                  0{index + 1}
                </span>
              </div>
              <h3 className="mt-7 text-xl font-semibold text-gray-950 transition group-hover:text-white">
                {item[0]}
              </h3>
              <p className="mt-3 flex-1 text-sm leading-7 text-gray-600 transition group-hover:text-blue-50/75 sm:text-base">
                {item[1]}
              </p>
              <a
                href={serviceAnchors[index]}
                className="mt-6 inline-flex items-center justify-between gap-3 border-t border-gray-200 pt-4 text-sm font-semibold text-[#005B96] transition group-hover:border-white/15 group-hover:text-[#FFC629]"
              >
                <span className="break-words">{item[2]}</span>
                <span className="shrink-0 transition group-hover:translate-x-1" aria-hidden="true">{"\u2192"}</span>
              </a>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
