import { useRef, type ReactNode } from "react";
import { motion, useInView, useScroll, useSpring } from "motion/react";
import { ArrowUpRight } from "lucide-react";
import { Heading, Reveal, Screenshot, TiltCard } from "@/components/ui";
import clean960 from "@/assets/shots/clean-960.webp";
import clean1920 from "@/assets/shots/clean-1920.webp";
import compare960 from "@/assets/shots/compare-960.webp";
import compare1920 from "@/assets/shots/compare-1920.webp";
import { cn } from "@/lib/utils";

/**
 * The sections that say what the product does and how. Every example on this page is real output:
 * the sentences, tags, verdict names, baseline file and "why" lines come from running version 0.3
 * on its built-in sample file, or from the README.
 */

const DOT = { problem: "bg-crit-ink", warning: "bg-warn-ink", ok: "bg-ok-ink" } as const;

// ------------------------------------------------------------ what you get back
const VERDICTS: { when: string; items: [keyof typeof DOT, string][] }[] = [
  { when: "With an earlier file to compare", items: [["problem", "Not safe to use"], ["warning", "Check before use"], ["ok", "Looks like last time"]] },
  { when: "The first time", items: [["problem", "Problems found"], ["warning", "Things to check"], ["ok", "Nothing obviously wrong"]] },
];

const REASONS: [string, ReactNode][] = [
  ["Duplicates", "6 rows are exact copies of another row."],
  ["Dates", <><span className="chip mr-1.5">signup_date</span>has 3 dates in the future (latest: 2031-02-12).</>],
  ["Spelling", <><span className="chip mr-1.5">country</span>has 3 spellings of the same value: "Nigeria", "nigeria ", "NIGERIA".</>],
];

const ROWS = [["spelling", "62", "1061", "nigeria"], ["spelling", "63", "1062", "nigeria"], ["spelling", "64", "1063", "nigeria"]];

function Outcome({ step, title, text, children }: { step: string; title: string; text: string; children: ReactNode }) {
  return (
    <TiltCard className="flex flex-col p-6 md:p-7">
      <p className="font-mono text-[12px] text-haze">{step}</p>
      <h3 className="mt-3 font-display text-[23px] font-semibold leading-tight tracking-[-0.01em]">{title}</h3>
      <p className="mt-2.5 text-[15.5px] leading-relaxed text-fog">{text}</p>
      {/* A piece of the app's own white surface. */}
      <div aria-hidden className="mt-6 flex-1 rounded-xl bg-white p-4 text-ink shadow-lift [color-scheme:light]">{children}</div>
    </TiltCard>
  );
}

export function Outcomes() {
  return (
    <section className="later relative py-24 md:py-36" id="answer">
      <div className="wrap">
        <Heading
          eyebrow="What you get back"
          title="An answer, the reasons, and the rows."
          lede="Not a report to study. One line, a short list, and the rows."
        />
        <div className="mt-14 grid grid-cols-[minmax(0,1fr)] gap-4 lg:grid-cols-3">
          <Reveal className="h-full">
            <Outcome step="1" title="A verdict" text="Can you use the file? One line tells you.">
              {VERDICTS.map((group) => (
                <div key={group.when} className="mb-3 last:mb-0">
                  <p className="mb-1.5 font-mono text-[11px] uppercase tracking-[0.08em] text-muted">{group.when}</p>
                  {group.items.map(([tone, label]) => (
                    <p key={label} className="flex items-center gap-2.5 py-[3px] text-[14.5px] font-medium">
                      <span className={cn("h-2 w-2 shrink-0 rounded-full", DOT[tone])} />{label}
                    </p>
                  ))}
                </div>
              ))}
            </Outcome>
          </Reveal>
          <Reveal delay={0.08} className="h-full">
            <Outcome step="2" title="The reasons" text="What is wrong, where, and how many rows. Worst first.">
              {REASONS.map(([tag, sentence]) => (
                <div key={tag} className="border-b border-line py-2.5 first:pt-0 last:border-0 last:pb-0">
                  <p className="text-[13.5px] leading-snug">{sentence}</p>
                  <p className="mt-1 font-mono text-[10.5px] uppercase tracking-[0.08em] text-muted">{tag}</p>
                </div>
              ))}
            </Outcome>
          </Reveal>
          <Reveal delay={0.16} className="h-full">
            <Outcome step="3" title="The rows to send back" text="Download the affected rows, with a message ready to send.">
              <div className="overflow-hidden rounded-md border border-line font-mono text-[11px]">
                <div className="grid grid-cols-[1.2fr_0.6fr_1fr_1fr] bg-soft2 text-muted">
                  {["reason", "row", "customer_id", "country"].map((head) => <span key={head} className="truncate px-2 py-1.5">{head}</span>)}
                </div>
                {ROWS.map((row) => (
                  <div key={row[1]} className="grid grid-cols-[1.2fr_0.6fr_1fr_1fr] border-t border-line">
                    {row.map((cell, i) => <span key={i} className={cn("truncate px-2 py-1.5", i === 0 || i === 3 ? "text-crit-ink" : "text-slate2")}>{cell}</span>)}
                  </div>
                ))}
              </div>
              <p className="mt-3 rounded-md bg-soft2 p-2.5 text-[12.5px] leading-snug text-slate2">
                In sample_customers.csv: signup_date has 3 dates in the future (latest: 2031-02-12). The rows are attached.
              </p>
            </Outcome>
          </Reveal>
        </div>
      </div>
    </section>
  );
}

// ------------------------------------------------------- one file is enough
// Screenshots of the real app. The files are small example files made for these pictures.
const CASES = [
  {
    label: "The first time",
    title: "Checked on its own.",
    text: "Duplicates, impossible values, broken dates, mixed spellings.",
    small: clean960, large: clean1920,
    alt: "PyDataQuality result for survey_responses.csv, a file checked for the first time: a green banner reading \"Nothing obviously wrong\", with 0 problems, 0 warnings and 6 clean columns.",
  },
  {
    label: "If it comes again (optional)",
    title: "Compared with the last one.",
    text: "Save a good file once. The next one is checked against it.",
    small: compare960, large: compare1920,
    alt: "PyDataQuality result for orders_september.csv compared with orders_august.csv: a red banner reading \"Not safe to use\", with 3 problems and 1 warning, including 9 dates in the future and a missing column.",
  },
];

export function FirstFile() {
  return (
    <section className="later relative overflow-hidden border-y border-white/[0.07] bg-night-1 py-24 md:py-36" id="first">
      <div className="wrap">
        <Heading
          eyebrow="One file is enough"
          title="No earlier version needed."
          lede="Most files arrive once. It checks a file on its own. Comparing with an earlier one is a bonus, not a requirement."
        />
        <div className="mt-14 grid grid-cols-[minmax(0,1fr)] gap-12 lg:grid-cols-2 lg:gap-8">
          {CASES.map((item, i) => (
            <Reveal key={item.label} delay={0.1 * i}>
              <figure>
                <Screenshot small={item.small} large={item.large} alt={item.alt} sizes="(min-width: 1024px) 560px, 92vw" />
                <figcaption className="mt-6">
                  <p className="eyebrow">{item.label}</p>
                  <p className="mt-2 font-display text-[24px] font-semibold leading-tight tracking-[-0.01em]">{item.title}</p>
                  <p className="mt-1.5 text-[16px] text-fog">{item.text}</p>
                </figcaption>
              </figure>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

// ------------------------------------------------- what happens to a file
const STAGES: { title: string; text: ReactNode }[] = [
  { title: "Reads the file", text: <>CSV, Excel, JSON or Parquet, on your computer.</> },
  { title: "Works out each column", text: <>ID, date, email, number, category or text.</> },
  { title: "Runs the checks that fit", text: <>A future <span className="chip-dark">signup_date</span> is a problem. A future <span className="chip-dark">due_date</span> is not.</> },
  { title: "Compares, if you saved an earlier file", text: <>Missing columns, new values, far fewer rows, shifted numbers.</> },
  { title: "Writes the answer", text: <>One sentence per finding. The worst one sets the verdict.</> },
];

// The baseline saved from the sample file, with some lines left out. The values are as saved,
// including the sample's mistakes, which is why the app warns before a file with problems is saved.
const BASELINE = `# PyDataQuality baseline: what a normal file looks like.
name: customers
learned_from: customers.csv
rows: 486
columns:
  customer_id: {kind: id, type: numbers, unique: true}
  email: {kind: email, type: text, unique: true}
  country:
    kind: category
    values: [Ghana, Kenya, NIGERIA, Nigeria, South Africa, nigeria]`;

const PRIVACY = ["Served from 127.0.0.1, your own computer.", "No network requests, no account, no tracking.", "Your file is deleted once it has been read."];

function Panel({ label, children, className }: { label: string; children: ReactNode; className?: string }) {
  return (
    <div className={cn("card overflow-hidden", className)}>
      <p className="border-b border-white/[0.08] px-5 py-3 font-mono text-[11.5px] uppercase tracking-[0.12em] text-haze">{label}</p>
      {children}
    </div>
  );
}

export function Engine() {
  const track = useRef<HTMLOListElement>(null);
  const { scrollYProgress } = useScroll({ target: track, offset: ["start 0.8", "end 0.55"] });
  const drawn = useSpring(scrollYProgress, { stiffness: 90, damping: 24 });
  return (
    <section className="later relative border-y border-white/[0.07] bg-night-1 py-24 md:py-36" id="inside">
      <div className="wrap">
        <Heading
          eyebrow="How it works"
          title="No AI. Five plain steps."
          lede="Fixed rules, run on your computer. Ask “Why?” on any finding to see how it was decided."
        />
        <div className="mt-14 grid grid-cols-[minmax(0,1fr)] gap-12 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)] lg:gap-14">
          <ol ref={track} className="relative">
            <span aria-hidden className="absolute bottom-2 left-[15px] top-2 w-px bg-white/10" />
            <motion.span aria-hidden style={{ scaleY: drawn }} className="absolute bottom-2 left-[15px] top-2 w-px origin-top bg-white" />
            {STAGES.map((stage, i) => (
              <li key={stage.title} className="relative pb-10 pl-14 last:pb-0">
                <span aria-hidden className="absolute left-0 top-0 grid h-[31px] w-[31px] place-items-center rounded-full border border-white/20 bg-night-1 font-mono text-[12px] text-white">{i + 1}</span>
                <Reveal delay={0.04 * i}>
                  <h3 className="font-display text-[22px] font-semibold leading-tight tracking-[-0.01em]">{stage.title}</h3>
                  <p className="mt-2.5 text-[16px] leading-relaxed text-fog">{stage.text}</p>
                </Reveal>
              </li>
            ))}
          </ol>

          <div className="flex flex-col gap-4 lg:sticky lg:top-24 lg:self-start">
            <Reveal>
              <Panel label="What it remembers">
                <pre tabIndex={0} aria-label="A saved baseline file, shortened" className="overflow-x-auto bg-ink px-5 py-4 font-mono text-[12.5px] leading-relaxed text-white/80">{BASELINE}</pre>
                <p className="px-5 py-4 text-[14.5px] leading-relaxed text-fog">A small text file you can read and edit. It describes your columns. It does not hold your rows.</p>
              </Panel>
            </Reveal>
            <Reveal delay={0.06}>
              <Panel label="Where your file goes">
                <ul className="flex flex-col gap-3 px-5 py-4">
                  {PRIVACY.map((line) => (
                    <li key={line} className="flex items-start gap-3 text-[14.5px] leading-relaxed text-white/85">
                      <span aria-hidden className="mt-[9px] h-1.5 w-1.5 shrink-0 rounded-full bg-ok-glow" />{line}
                    </li>
                  ))}
                </ul>
              </Panel>
            </Reveal>
          </div>
        </div>
      </div>
    </section>
  );
}

// ------------------------------------------------ the problem, and the answer
const STATS: { value: number; suffix: string; text: string; source: string; href: string; answer: string; detail: string }[] = [
  {
    value: 56, suffix: "%",
    text: "of data practitioners name poor data quality as a top problem in their work.",
    source: "dbt Labs, State of Analytics Engineering 2025",
    href: "https://www.getdbt.com/blog/state-of-analytics-engineering-2025-summary",
    answer: "Checking becomes one step.",
    detail: "Drop the file in. Nothing to set up, no rules to write.",
  },
  {
    value: 74, suffix: "%",
    text: "of data teams say business stakeholders find data issues first.",
    source: "Monte Carlo and Wakefield Research, 2023",
    href: "https://www.businesswire.com/news/home/20230502005377/en/5435996/Data-Downtime-Nearly-Doubled-Year-Over-Year-Monte-Carlo-Survey-Says",
    answer: "You see it first.",
    detail: "The verdict comes before you build anything on the file.",
  },
  {
    value: 15841, suffix: "",
    text: "COVID-19 cases were left out of England's daily count when a file hit a spreadsheet row limit.",
    source: "Public Health England, October 2020",
    href: "https://theconversation.com/why-you-should-never-use-excel-to-count-coronavirus-cases-147681",
    answer: "It can remember the last file.",
    detail: "Save a good file once. Far fewer rows next time, or a missing column, gets flagged.",
  },
];

function Figure({ value, suffix }: { value: number; suffix: string }) {
  return (
    <p className="font-display text-[52px] font-semibold leading-none tracking-[-0.03em] tabular-nums md:text-[64px]">
      {value.toLocaleString("en-US")}{suffix}
    </p>
  );
}

function Answer({ stat, index }: { stat: (typeof STATS)[number]; index: number }) {
  const ref = useRef<HTMLLIElement>(null);
  const seen = useInView(ref, { once: true, margin: "-15%" });
  return (
    <li ref={ref} className="relative grid gap-x-12 gap-y-6 py-10 md:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] md:py-12">
      <motion.span aria-hidden className="absolute inset-x-0 top-0 h-px origin-left bg-white/20" initial={{ scaleX: 0 }} animate={{ scaleX: seen ? 1 : 0 }} transition={{ duration: 0.9, delay: 0.05 * index, ease: [0.21, 0.6, 0.35, 1] }} />
      <div>
        <Figure value={stat.value} suffix={stat.suffix} />
        <p className="mt-4 max-w-[380px] text-[16px] leading-snug text-fog">{stat.text}</p>
        <a href={stat.href} className="link mt-3 inline-flex min-h-[32px] items-center gap-1 text-[13.5px] text-fog hover:text-white">
          {stat.source} <ArrowUpRight size={14} aria-hidden />
        </a>
      </div>
      <Reveal delay={0.1}>
        <p className="eyebrow mb-3">With PyDataQuality</p>
        <h3 className="font-display text-[28px] font-semibold leading-tight tracking-[-0.015em] md:text-[34px]">{stat.answer}</h3>
        <p className="mt-3 max-w-[520px] text-[17px] leading-relaxed text-white/85">{stat.detail}</p>
      </Reveal>
    </li>
  );
}

export function Answers() {
  return (
    <section className="later relative overflow-hidden py-24 md:py-36" id="why">
      <div aria-hidden className="grid-floor absolute inset-0 opacity-60 [mask-image:linear-gradient(to_bottom,transparent,black_30%,transparent)]" />
      <div className="wrap relative">
        <Heading
          eyebrow="Why it matters"
          title="Find it before your reader does."
          lede="Bad files are usually caught late, by someone else."
        />
        <ul className="mt-12">
          {STATS.map((stat, i) => <Answer key={stat.source} stat={stat} index={i} />)}
        </ul>
      </div>
    </section>
  );
}
