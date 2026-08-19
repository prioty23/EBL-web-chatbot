"use client";

import { useLanguage } from "@/components/LanguageProvider";

export default function ProductFinder() {
  const { t } = useLanguage();
  const selectGroups = [
    ["customer-type", t.finder.labels[0], t.finder.placeholders[0], t.finder.customerTypes],
    ["interest", t.finder.labels[1], t.finder.placeholders[1], t.finder.interests],
    ["priority", t.finder.labels[2], t.finder.placeholders[2], t.finder.priorities],
  ];

  return (
    <section id="product-finder" className="section-padding bg-[#F8FAFC]">
      <div className="container-custom">
        <div className="relative overflow-hidden rounded-[2.5rem] bg-[#003F68] p-5 shadow-2xl shadow-[#003F68]/20 sm:p-8 lg:p-12">
          <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full border-[48px] border-white/5" />
          <div className="pointer-events-none absolute bottom-0 left-1/3 h-48 w-48 rounded-full bg-[#FFC629]/20 blur-3xl" />

          <div className="relative grid gap-10 lg:grid-cols-[0.8fr_1.2fr] lg:items-center">
            <div className="flex flex-col justify-between text-white">
              <div>
                <p className="inline-flex max-w-full items-center gap-2 rounded-full bg-white/10 px-4 py-2 text-[11px] font-bold uppercase tracking-[0.2em] text-[#FFC629] sm:text-xs">
                  <span className="h-2 w-2 shrink-0 rounded-full bg-[#FFC629]" />
                  <span className="min-w-0 break-words">{t.finder.badge}</span>
                </p>
                <h2 className="mt-6 text-3xl font-semibold leading-tight sm:text-4xl">
                  {t.finder.title}
                </h2>
                <p className="mt-5 max-w-xl text-sm leading-7 text-blue-50/75 sm:text-base sm:leading-8">
                  {t.finder.subtitle}
                </p>
              </div>

              <div className="mt-8 grid gap-3 sm:grid-cols-3">
                {t.finder.steps.map((step: string, index: number) => (
                  <div key={step} className="border-t border-white/20 pt-3">
                    <span className="text-xs font-bold text-[#FFC629]">0{index + 1}</span>
                    <p className="mt-1 text-xs text-blue-50/75 sm:text-sm">{step}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-[1.75rem] bg-white p-5 shadow-2xl shadow-black/15 sm:p-8">
              <div className="mb-6 flex flex-col gap-3 border-b border-gray-100 pb-5 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <p className="text-sm font-bold text-[#005B96]">{t.finder.formTitle}</p>
                  <p className="mt-1 text-sm text-gray-500">{t.finder.duration}</p>
                </div>
                <span className="w-fit rounded-full bg-[#005B96]/10 px-3 py-1 text-xs font-bold text-[#005B96]">
                  {t.finder.questionCount}
                </span>
              </div>

              <div className="space-y-5">
                {selectGroups.map(([id, label, placeholder, options]) => (
                  <div key={id as string}>
                    <label
                      htmlFor={id as string}
                      className="mb-2 block text-sm font-semibold text-gray-700"
                    >
                      {label as string}
                    </label>
                    <select
                      id={id as string}
                      defaultValue=""
                      className="w-full min-w-0 rounded-xl border border-gray-200 bg-[#F8FAFC] px-4 py-3.5 text-sm text-gray-700 outline-none transition focus:border-[#005B96] focus:bg-white focus:ring-2 focus:ring-[#005B96]/10 sm:text-base"
                    >
                      <option value="" disabled>{placeholder as string}</option>
                      {(options as string[]).map((item) => (
                        <option key={item} value={item}>{item}</option>
                      ))}
                    </select>
                  </div>
                ))}

                <button type="button" className="btn-primary w-full justify-center gap-2 text-center">
                  <span className="break-words">{t.finder.button}</span>
                  <span aria-hidden="true">{"\u2192"}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
