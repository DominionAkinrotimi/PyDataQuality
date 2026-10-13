import { useRef, type ReactNode } from "react";
import { motion, useInView, useReducedMotion, useScroll, useSpring } from "motion/react";
import { ArrowUpRight } from "lucide-react";
import { NumberTicker } from "@/components/magicui/number-ticker";
import { Heading, Reveal, TiltCard } from "@/components/ui";
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
          lede="You do not get a report to study. You get one line saying whether the file can be used, a short list of what is wrong in sentences, and the exact rows behind each one."
        />
        <div className="mt-14 grid grid-cols-[minmax(0,1fr)] gap-4 lg:grid-cols-3">
          <Reveal className="h-full">
            <Outcome step="1" title="A verdict" text="One of six, and the worst finding decides which. On a first check it never says “safe”, because it has nothing to compare the file with yet.">
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
            <Outcome step="2" title="The reasons, in sentences" text="Each finding names the column, how many rows are affected and an example value. Problems come first, then warnings, largest first.">
              {REASONS.map(([tag, sentence]) => (
                <div key={tag} className="border-b border-line py-2.5 first:pt-0 last:border-0 last:pb-0">
                  <p className="text-[13.5px] leading-snug">{sentence}</p>
                  <p className="mt-1 font-mono text-[10.5px] uppercase tracking-[0.08em] text-muted">{tag}</p>
                </div>
              ))}
            </Outcome>
          </Reveal>
          <Reveal delay={0.16} className="h-full">
            <Outcome step="3" title="The rows to send back" text="Every finding opens the rows behind it, with the reason in the first column. Download them, or copy a short message for whoever produced the file.">
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

// ------------------------------------------------- what happens to a file
const STAGES: { title: string; text: ReactNode }[] = [
  {
    title: "It reads the file where it is.",
    text: <>CSV, TSV, Excel, JSON and Parquet. For a CSV it works out the separator and the text encoding itself. Nothing is sent anywhere: in the app, the file is copied to a temporary folder on your computer, read, and deleted.</>,
  },
  {
    title: "It works out what each column holds.",
    text: <>From the values and the column name it decides whether a column is an ID, an email, a date, a number, a number stored as text, a yes/no, a category or free text. This is what lets it judge a file it has never seen: once a column is known to hold email addresses, the few values that are not stand out.</>,
  },
  {
    title: "It runs only the checks that fit.",
    text: <>An ID column is checked for repeats, not for unusual numbers. A future date in <span className="chip-dark">signup_date</span> is a problem, while one in <span className="chip-dark">due_date</span> is expected. The check for extreme numbers is strict on purpose, so ordinary uneven data such as incomes or order amounts is left alone.</>,
  },
  {
    title: "It compares with the file you approved.",
    text: <>It finds the earlier file by name, ignoring dates, month names and words like “final” or “copy”, or failing that by matching columns. Then it looks for columns that went missing, appeared or changed type, fewer than half or more than double the rows, an ID that now repeats, category values never seen before, numbers outside the earlier range or whose typical value has shifted, a column that is much emptier, and the very same file sent again.</>,
  },
  {
    title: "It writes the answer.",
    text: <>Each finding becomes one sentence with a count and an example. The worst finding sets the verdict. The same result is shown in the app, printed by the command and returned to Python.</>,
  },
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
    values: [Ghana, Kenya, NIGERIA, Nigeria, South Africa, nigeria]
  monthly_spend:
    kind: number
    min: 15.28
    max: 480000.0
    median: 68.475`;

const PRIVACY = [
  "The app answers only on 127.0.0.1, your own computer, and refuses requests addressed to any other name.",
  "Each session has its own key, so another website open in your browser cannot use the app.",
  "It makes no network requests. There is no account, no tracking and no update check.",
  "A file you drop in is deleted from the temporary folder once it has been read.",
];

const WHY: [string, string][] = [
  ["country has 3 spellings of the same value.", "Values are compared after removing extra spaces and ignoring capital letters."],
  ["signup_date has 3 dates in the future.", "Compared with today's date on this computer."],
  ["signup_date mixes 2 date formats.", "Mixed formats are often read wrongly, for example 03/04 as March or April."],
];

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
          eyebrow="What it does with your file"
          title="From a dropped file to an answer, in five steps."
          lede="No AI and no guessing. The checks are ordinary rules that run on your computer, and you can ask how any finding was decided."
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
                <p className="px-5 py-4 text-[14.5px] leading-relaxed text-fog">
                  Saving a file as normal writes a small text file like this: column names, what each holds, ranges, category values and the row count. It does not hold your rows. This one was saved from the sample file, mistakes included, which is why the app shows you what it learned before you save. You can open the file, read it and add your own rules.
                </p>
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
            <Reveal delay={0.12}>
              <Panel label="Ask why">
                <ul className="px-5 py-2">
                  {WHY.map(([finding, why]) => (
                    <li key={finding} className="border-b border-white/[0.07] py-3 last:border-0">
                      <p className="text-[14.5px] text-white/90">{finding}</p>
                      <p className="mt-1 text-[14px] leading-snug text-fog"><span className="mr-1.5 font-mono text-[11px] uppercase tracking-[0.08em] text-haze">Why</span>{why}</p>
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
    detail: "Drop the file in, or run one command. There is nothing to set up and no rules to write, so it is quick enough to do every time a file arrives.",
  },
  {
    value: 74, suffix: "%",
    text: "of data teams say business stakeholders find data issues first.",
    source: "Monte Carlo and Wakefield Research, 2023",
    href: "https://www.businesswire.com/news/home/20230502005377/en/5435996/Data-Downtime-Nearly-Doubled-Year-Over-Year-Monte-Carlo-Survey-Says",
    answer: "You see it first.",
    detail: "The verdict comes before you build anything on the file, with the affected rows and a short message ready for whoever produced it.",
  },
  {
    value: 15841, suffix: "",
    text: "COVID-19 cases were left out of England's daily count when a file hit a spreadsheet row limit.",
    source: "Public Health England, October 2020",
    href: "https://theconversation.com/why-you-should-never-use-excel-to-count-coronavirus-cases-147681",
    answer: "It remembers the last file.",
    detail: "Once you save a file as normal, the next one is compared with it. Fewer than half the rows, or a column that has gone missing, is flagged before you use the file.",
  },
];

function Figure({ value, suffix }: { value: number; suffix: string }) {
  const reduced = useReducedMotion();
  const label = `${value.toLocaleString("en-US")}${suffix}`;
  return (
    <p className="font-display text-[52px] font-semibold leading-none tracking-[-0.03em] tabular-nums md:text-[64px]">
      <span className="sr-only">{label}</span>
      <span aria-hidden>
        {reduced ? value.toLocaleString("en-US") : <NumberTicker value={value} className="tracking-[-0.03em] text-white" />}
        {suffix}
      </span>
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
          eyebrow="Why it is worth a minute"
          title="Find it before your reader does."
          lede="A file looks fine when you scroll through it. The trouble shows up later, in a report someone else is reading. Here is what is known about that, and what PyDataQuality does about each part."
        />
        <ul className="mt-12">
          {STATS.map((stat, i) => <Answer key={stat.source} stat={stat} index={i} />)}
        </ul>
      </div>
    </section>
  );
}
