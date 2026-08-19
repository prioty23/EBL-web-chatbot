"use client";

import { useLanguage } from "@/components/LanguageProvider";

const icons = ["\u25EB", "\u25B0", "\u2302", "\u2197", "\u25CE", "%"];

export default function NeedsSection() {
  const { t } = useLanguage();

  return (
    <section id="needs" className="section-padding bg-white">
      <div className="container-custom">
        <div className="mx-auto max-w-3xl text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#005B96]">
            {t.needs.eyebrow}
          </p>
          <h2 className="mt-3 text-3xl font-semibold text-gray-950 sm:text-4xl">
            {t.needs.title}
          </h2>
          <p className="mt-4 text-base leading-7 text-gray-600 sm:text-lg sm:leading-8">
            {t.needs.subtitle}
          </p>
        </div>

        <div className="mt-10 grid gap-5 md:mt-12 md:grid-cols-2 xl:grid-cols-3">
          {t.needs.cards.map((item: string[], index: number) => (
            <article
              key={item[0]}
              className="group relative overflow-hidden rounded-[1.75rem] border border-gray-100 bg-white p-6 shadow-sm transition duration-300 hover:-translate-y-1 hover:border-[#005B96]/20 hover:shadow-xl hover:shadow-[#005B96]/8 sm:p-7"
            >
              <span className="absolute right-6 top-5 text-5xl font-bold text-[#005B96]/[0.04]">
                0{index + 1}
              </span>
              <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-[#005B96] text-2xl font-bold text-white shadow-lg shadow-[#005B96]/20 transition group-hover:bg-[#004C7D]">
                <span aria-hidden="true">{icons[index]}</span>
              </div>
              <p className="mt-6 text-xs font-bold uppercase tracking-[0.18em] text-[#B58200]">
                {item[1]}
              </p>
              <h3 className="mt-2 text-xl font-semibold text-gray-950">
                {item[0]}
              </h3>
              <p className="mt-3 text-sm leading-7 text-gray-600 sm:text-base">{item[2]}</p>
              <a
                href="#footer"
                className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-[#005B96]"
              >
                {item[3]}
                <span className="transition group-hover:translate-x-1" aria-hidden="true">{"\u2192"}</span>
              </a>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
