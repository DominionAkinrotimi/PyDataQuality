import { useRef } from "react";
import { motion, useInView, useReducedMotion } from "motion/react";
import { ArrowUpRight } from "lucide-react";
import { NumberTicker } from "@/components/magicui/number-ticker";
import { Heading, Reveal, TiltCard } from "@/components/ui";
import { cn } from "@/lib/utils";

// ------------------------------------------------------------ what it finds
type Tone = "problem" | "warning";

interface Find {
  title: string;
  /** The sentence PyDataQuality writes for this, taken from the README or the sample file. */
  says: string;
  tone: Tone;
  /** A few cells from a column; `bad` marks the ones the finding is about. */
  column: string;
  cells: { value: string; bad?: boolean; gone?: boolean }[];
}

const FINDS: Find[] = [
  {
    title: "Duplicate rows", tone: "problem", column: "row",
    says: "6 rows are exact copies of another row.",
    cells: [{ value: "1042  Ada  34" }, { value: "1043  Tunde  41", bad: true }, { value: "1043  Tunde  41", bad: true }],
  },
  {
    title: "IDs that repeat", tone: "problem", column: "order_id",
    says: "order_id should be unique, but 2 values appear more than once.",
    cells: [{ value: "7099" }, { value: "7100", bad: true }, { value: "7100", bad: true }],
  },
  {
    title: "Dates in the future", tone: "problem", column: "signup_date",
    says: "signup_date has 3 dates in the future (latest: 2031-02-12).",
    cells: [{ value: "2025-03-07" }, { value: "2031-02-12", bad: true }, { value: "2025-03-09" }],
  },
  {
    title: "A column that went missing", tone: "problem", column: "columns",
    says: "1 column is missing: discount_code. It was in orders_september.csv.",
    cells: [{ value: "order_id" }, { value: "amount" }, { value: "discount_code", bad: true, gone: true }],
  },
  {
    title: "One value spelled three ways", tone: "warning", column: "country",
    says: "country has 3 spellings of the same value: \"Nigeria\", \"nigeria \", \"NIGERIA\".",
    cells: [{ value: "Nigeria" }, { value: "nigeria ", bad: true }, { value: "NIGERIA", bad: true }],
  },
  {
    title: "Numbers stored as text", tone: "warning", column: "amount",
    says: "amount is mostly numbers, but 1 value is not: \"N/A\".",
    cells: [{ value: "54.20" }, { value: "N/A", bad: true }, { value: "119.58" }],
  },
  {
    title: "Impossible values", tone: "problem", column: "age",
    says: "age has 2 impossible values: \"999\", \"-4\". An age should be between 0 and 120.",
    cells: [{ value: "34" }, { value: "999", bad: true }, { value: "-4", bad: true }],
  },
  {
    title: "Far fewer rows than last time", tone: "warning", column: "rows",
    says: "The file has 1,200 rows. Last time it had 3,000 (60% fewer).",
    cells: [{ value: "last time  3,000" }, { value: "this time  1,200", bad: true }],
  },
];

const ALSO = ["Invalid email addresses", "Mixed date formats", "Numbers far outside the usual range", "Empty or mostly empty columns", "Values never seen before", "The same file sent twice"];

function FindCard({ find }: { find: Find }) {
  const flagged = find.tone === "problem" ? "border-crit-glow/50 bg-crit-glow/[0.12] text-[#fecaca]" : "border-warn-glow/50 bg-warn-glow/[0.12] text-[#fde68a]";
  return (
    <TiltCard className="flex flex-col p-5">
      <div aria-hidden className="mb-5 overflow-hidden rounded-lg border border-white/[0.08] bg-ink font-mono text-[12px] [transform:translateZ(28px)]">
        <p className="border-b border-white/[0.08] bg-white/[0.04] px-3 py-1.5 text-haze">{find.column}</p>
        {find.cells.map((cell, i) => (
          <p key={i} className={cn("whitespace-pre border-b border-white/[0.06] px-3 py-1.5 last:border-0", cell.bad ? cn("border-l-2", flagged) : "text-white/70", cell.gone && "line-through")}>
            {cell.value}
          </p>
        ))}
      </div>
      <h3 className="font-display text-[19px] font-semibold tracking-[-0.005em]">{find.title}</h3>
      <p className="mt-2 text-[14.5px] leading-snug text-fog">{find.says}</p>
    </TiltCard>
  );
}

export function Finds() {
  return (
    <section className="later relative py-24 md:py-36" id="finds">
      <div className="wrap">
        <Heading
          eyebrow="What it finds"
          title="The things you would not spot by scrolling."
          lede="It works out what each column is, an ID, a date, an email, a category or a number, before judging it. Each card shows the kind of thing it catches, and the sentence it writes."
        />
        <ul className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {FINDS.map((find, i) => (
            <li key={find.title}>
              <Reveal delay={0.05 * (i % 4)} className="h-full">
                <FindCard find={find} />
              </Reveal>
            </li>
          ))}
        </ul>
        <Reveal delay={0.1}>
          <div className="mt-8 flex flex-wrap items-center gap-x-2 gap-y-2.5 text-[14.5px] text-fog">
            <span className="mr-1">It also finds:</span>
            {ALSO.map((item) => (
              <span key={item} className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1">{item}</span>
            ))}
          </div>
        </Reveal>
      </div>
    </section>
  );
}

// --------------------------------------------------------------- the problem
const STATS: { value: number; suffix: string; text: string; source: string; href: string }[] = [
  {
    value: 56, suffix: "%",
    text: "of data practitioners name poor data quality as a top problem in their work.",
    source: "dbt Labs, State of Analytics Engineering 2025",
    href: "https://www.getdbt.com/blog/state-of-analytics-engineering-2025-summary",
  },
  {
    value: 74, suffix: "%",
    text: "of data teams say business stakeholders find data issues first.",
    source: "Monte Carlo and Wakefield Research, 2023",
    href: "https://www.businesswire.com/news/home/20230502005377/en/5435996/Data-Downtime-Nearly-Doubled-Year-Over-Year-Monte-Carlo-Survey-Says",
  },
  {
    value: 15841, suffix: "",
    text: "COVID-19 cases were left out of England's daily count when a file hit a spreadsheet row limit.",
    source: "Public Health England, October 2020",
    href: "https://theconversation.com/why-you-should-never-use-excel-to-count-coronavirus-cases-147681",
  },
];

function Figure({ value, suffix }: { value: number; suffix: string }) {
  const reduced = useReducedMotion();
  const label = `${value.toLocaleString("en-US")}${suffix}`;
  return (
    <p className="font-display text-[64px] font-semibold leading-none tracking-[-0.03em] tabular-nums md:text-[84px]">
      <span className="sr-only">{label}</span>
      <span aria-hidden>
        {reduced ? value.toLocaleString("en-US") : <NumberTicker value={value} className="tracking-[-0.03em] text-white" />}
        {suffix}
      </span>
    </p>
  );
}

export function Problem() {
  const rule = useRef<HTMLDivElement>(null);
  const seen = useInView(rule, { once: true, margin: "-15%" });
  return (
    <section className="later relative overflow-hidden border-y border-white/[0.07] bg-night-1 py-24 md:py-36">
      <div aria-hidden className="grid-floor absolute inset-0 opacity-60 [mask-image:linear-gradient(to_bottom,transparent,black_30%,transparent)]" />
      <div className="wrap relative">
        <Heading
          eyebrow="The problem"
          title="Bad data is usually found late, by the wrong person."
          lede="A file looks fine when you scroll through it. The duplicate rows, the dates in 2031 and the column that quietly disappeared show up later, in a report someone else is reading."
        />
        <div ref={rule} className="relative mt-16">
          <motion.div aria-hidden className="absolute inset-x-0 top-0 h-px origin-left bg-white/25" initial={{ scaleX: 0 }} animate={{ scaleX: seen ? 1 : 0 }} transition={{ duration: 1.1, ease: [0.21, 0.6, 0.35, 1] }} />
          <div className="grid gap-12 pt-10 md:grid-cols-3 md:gap-10">
            {STATS.map((stat, i) => (
              <Reveal key={stat.source} delay={0.12 * i}>
                <Figure value={stat.value} suffix={stat.suffix} />
                <p className="mt-5 max-w-[320px] text-[17px] leading-snug text-white/85">{stat.text}</p>
                <a href={stat.href} className="link mt-4 inline-flex min-h-[32px] items-center gap-1 text-[13.5px] text-fog hover:text-white">
                  {stat.source} <ArrowUpRight size={14} aria-hidden />
                </a>
              </Reveal>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
