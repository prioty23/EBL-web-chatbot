"use client";

import { useLanguage } from "@/components/LanguageProvider";
import { useState } from "react";

const slideLinks = [
  ["#needs", "#needs"],
  ["#needs", "#footer"],
  ["#needs", "#footer"],
  ["#needs", "#footer"],
];

const actionIcons = ["\u2197", "\u25A3", "\u25CE"];

export default function Hero() {
  const [activeSlide, setActiveSlide] = useState(0);
  const { t } = useLanguage();
  const slide = t.hero.slides[activeSlide];

  const goToPrevious = () => {
    setActiveSlide((current) => (current === 0 ? t.hero.slides.length - 1 : current - 1));
  };

  const goToNext = () => {
    setActiveSlide((current) => (current === t.hero.slides.length - 1 ? 0 : current + 1));
  };

  return (
    <section className="relative overflow-hidden bg-[linear-gradient(135deg,rgba(0,91,150,0.13)_0%,rgba(234,244,251,0.9)_38%,#f8fafc_100%)]">
      <div className="pointer-events-none absolute -right-28 top-14 h-80 w-80 rounded-full border-[52px] border-[#005B96]/5" />
      <div className="pointer-events-none absolute -left-20 bottom-24 h-48 w-48 rounded-full bg-[#FFC629]/20 blur-3xl" />

      <div className="container-custom relative grid gap-10 py-12 sm:gap-12 sm:py-16 lg:grid-cols-[1.05fr_0.95fr] lg:items-center lg:py-24">
        <div className="max-w-2xl">
          <p className="mb-5 inline-flex max-w-full items-center gap-2 rounded-full border border-[#005B96]/10 bg-white/70 px-4 py-2 text-xs font-semibold text-[#005B96] shadow-sm backdrop-blur sm:text-sm">
            <span className="h-2 w-2 shrink-0 rounded-full bg-[#FFC629]" />
            <span className="min-w-0 break-words">{slide.badge}</span>
          </p>
          <h1 className="text-3xl font-semibold tracking-tight text-gray-950 sm:text-5xl lg:text-6xl">
            {slide.title}
          </h1>
          <p className="mt-5 max-w-xl text-base leading-7 text-gray-600 sm:mt-6 sm:text-lg sm:leading-8">
            {slide.description}
          </p>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:gap-4">
            <a href={slideLinks[activeSlide][0]} className="btn-primary w-full sm:w-auto">
              {slide.primaryLabel}
            </a>
            <a href={slideLinks[activeSlide][1]} className="btn-secondary w-full sm:w-auto">
              {slide.secondaryLabel}
            </a>
          </div>

          <div className="mt-10 flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
            <div className="flex flex-wrap items-center gap-2">
              {t.hero.slides.map((item: { title: string }, index: number) => (
                <button
                  key={item.title}
                  type="button"
                  onClick={() => setActiveSlide(index)}
                  aria-label={`${t.hero.goToSlide} ${index + 1}`}
                  className={`h-3 rounded-full transition ${
                    activeSlide === index
                      ? "w-10 bg-[#005B96]"
                      : "w-3 bg-[#005B96]/25 hover:bg-[#005B96]/45"
                  }`}
                />
              ))}
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={goToPrevious}
                className="rounded-full border border-[#005B96]/20 px-4 py-2 text-sm font-semibold text-[#005B96] transition hover:bg-white"
              >
                {t.hero.previous}
              </button>
              <button
                type="button"
                onClick={goToNext}
                className="rounded-full border border-[#005B96]/20 px-4 py-2 text-sm font-semibold text-[#005B96] transition hover:bg-white"
              >
                {t.hero.next}
              </button>
            </div>
          </div>
        </div>

        <div className="relative rounded-[2rem] border border-white/80 bg-white/85 p-4 shadow-2xl shadow-[#005B96]/15 backdrop-blur sm:p-6">
          <div className="absolute right-3 top-3 rounded-full bg-[#FFC629] px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.18em] text-[#123047] shadow-lg sm:-right-3 sm:-top-3 sm:px-4 sm:py-2 sm:text-xs">
            {t.hero.live}
          </div>

          <div className="rounded-[1.75rem] bg-[#003F68] p-5 text-white sm:p-8">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                <p className="text-xs font-medium uppercase tracking-[0.2em] text-[#FFC629] sm:text-sm sm:tracking-[0.24em]">
                  {t.hero.account}
                </p>
                <p className="mt-4 text-sm text-blue-50/70">{t.hero.balance}</p>
                <p className="mt-2 break-words text-3xl font-semibold tracking-tight sm:text-4xl">
                  $24,850.00
                </p>
              </div>
              <div className="w-fit rounded-full bg-white/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[#FFC629]">
                {t.hero.active}
              </div>
            </div>

            <div className="mt-10 flex flex-col gap-5 border-t border-white/10 pt-6 sm:flex-row sm:items-end sm:justify-between">
              <div className="min-w-0">
                <p className="text-xs uppercase tracking-[0.18em] text-[#FFC629]">
                  {t.hero.thisMonth}
                </p>
                <p className="mt-2 text-lg font-semibold">+$2,410.50</p>
              </div>
              <div className="flex h-14 items-end justify-end gap-1.5 self-end sm:self-auto" aria-hidden="true">
                {[38, 55, 42, 72, 60, 88, 76, 100].map((height, index) => (
                  <span
                    key={`${height}-${index}`}
                    className="w-2 rounded-full bg-[#FFC629]/85"
                    style={{ height: `${height}%` }}
                  />
                ))}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-3 p-3 pb-0 pt-5 min-[420px]:grid-cols-3 sm:gap-4">
            {actionIcons.map((icon, index) => {
              const label = t.hero.actions[index];

              return (
                <div key={label} className="rounded-2xl bg-[#F8FAFC] p-3 text-center">
                  <p className="text-xl" aria-hidden="true">{icon}</p>
                  <p className="mt-1 text-xs font-semibold text-[#003F68]">{label}</p>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="container-custom relative pb-8 lg:pb-10">
        <div className="grid overflow-hidden rounded-[1.75rem] border border-[#005B96]/10 bg-white shadow-xl shadow-[#005B96]/8 sm:grid-cols-2 lg:grid-cols-4">
          {t.hero.stats.map((stat: string[], index: number) => (
            <div
              key={stat[1]}
              className={`px-6 py-5 ${
                index > 0 ? "border-t border-[#005B96]/10 sm:border-l lg:border-t-0" : ""
              } ${index === 2 ? "sm:border-l-0 lg:border-l" : ""}`}
            >
              <div className="flex flex-wrap items-baseline gap-2">
                <p className="text-2xl font-bold tracking-tight text-[#005B96]">
                  {stat[0]}
                </p>
                <p className="break-words font-semibold text-[#003F68]">{stat[1]}</p>
              </div>
              <p className="mt-1 text-sm text-gray-500">{stat[2]}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
