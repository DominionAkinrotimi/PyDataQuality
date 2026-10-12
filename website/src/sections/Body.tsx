import { useState, type ReactNode } from "react";
import { AnimatePresence, motion } from "motion/react";
import {
  ArrowRight, ArrowUpRight, CalendarX2, Copy as CopyIcon, FileWarning, History, Lock, MessageSquareText,
  Minus, Plus, Rows3, ScanSearch, SpellCheck, TextCursorInput, Type,
} from "lucide-react";
import { BlurFade } from "@/components/magicui/blur-fade";
import { BorderBeam } from "@/components/magicui/border-beam";
import { DotPattern } from "@/components/magicui/dot-pattern";
import { Marquee } from "@/components/magicui/marquee";
import { NumberTicker } from "@/components/magicui/number-ticker";
import { AnimatedSpan, Terminal, TypingAnimation } from "@/components/magicui/terminal";
import { cn } from "@/lib/utils";
import { CopyCommand, LINKS } from "./Hero";

function Reveal({ children, delay = 0, className }: { children: ReactNode; delay?: number; className?: string }) {
  return (
    <BlurFade inView delay={delay} className={className}>
      {children}
    </BlurFade>
  );
}

function Heading({ eyebrow, title, lede, center = false }: { eyebrow: string; title: ReactNode; lede?: ReactNode; center?: boolean }) {
  return (
    <Reveal className={cn("max-w-[720px]", center && "mx-auto text-center")}>
      <p className="eyebrow mb-4">{eyebrow}</p>
      <h2 className="h2">{title}</h2>
      {lede && <p className="lede mt-5">{lede}</p>}
    </Reveal>
  );
}

// ------------------------------------------------------------ what it finds
const CATCHES: [typeof Rows3, string][] = [
  [Rows3, "Duplicate rows"],
  [ScanSearch, "IDs that repeat"],
  [CalendarX2, "Dates in the future"],
  [FileWarning, "A column that went missing"],
  [SpellCheck, "One value spelled three ways"],
  [Type, "Numbers stored as text"],
  [TextCursorInput, "Invalid email addresses"],
  [History, "Far fewer rows than last time"],
  [CalendarX2, "Mixed date formats"],
  [ScanSearch, "Impossible ages and negative prices"],
  [FileWarning, "The same file sent twice"],
  [Rows3, "Values never seen before"],
];

export function Catches() {
  return (
    <section className="border-y border-line bg-soft py-6" aria-label="Examples of what PyDataQuality finds">
      <Marquee pauseOnHover className="[--duration:46s] [--gap:0.75rem]">
        {CATCHES.map(([Icon, label]) => (
          <span key={label} className="inline-flex items-center gap-2 rounded-full border border-line bg-white px-4 py-2 text-[14px] text-slate2">
            <Icon size={15} aria-hidden />
            {label}
          </span>
        ))}
      </Marquee>
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
    text: "of data teams say business stakeholders find data issues before they do.",
    source: "Monte Carlo and Wakefield Research, 2023",
    href: "https://www.businesswire.com/news/home/20230502005377/en/5435996/Data-Downtime-Nearly-Doubled-Year-Over-Year-Monte-Carlo-Survey-Says",
  },
  {
    value: 15841, suffix: "",
    text: "COVID-19 cases went missing from England's daily count when a file hit a spreadsheet row limit.",
    source: "Public Health England incident, October 2020",
    href: "https://theconversation.com/why-you-should-never-use-excel-to-count-coronavirus-cases-147681",
  },
];

export function Problem() {
  return (
    <section className="py-24 md:py-32">
      <div className="wrap">
        <Heading
          eyebrow="The problem"
          title="Bad data is usually found late, by the wrong person."
          lede="A file looks fine when you scroll through it. The duplicate rows, the dates in 2031 and the column that quietly disappeared show up later, in a report someone else is reading."
        />
        <div className="mt-14 grid gap-px overflow-hidden rounded-2xl border border-line bg-line md:grid-cols-3">
          {STATS.map((stat, i) => (
            <Reveal key={stat.source} delay={0.08 * i} className="h-full">
              <div className="flex h-full flex-col bg-white p-7">
                <p className="font-display text-[56px] font-semibold leading-none tracking-[-0.04em] tabular-nums">
                  <NumberTicker value={stat.value} className="text-ink" />
                  {stat.suffix}
                </p>
                <p className="mt-4 flex-1 text-[16px] leading-relaxed text-slate2">{stat.text}</p>
                <a href={stat.href} className="mt-5 inline-flex items-center gap-1 text-[13px] text-muted underline decoration-line2 underline-offset-4 hover:text-ink">
                  {stat.source} <ArrowUpRight size={13} aria-hidden />
                </a>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

// ----------------------------------------------------------------- features
function Card({ className, children, delay = 0 }: { className?: string; children: ReactNode; delay?: number }) {
  return (
    <Reveal delay={delay} className={className}>
      <motion.div whileHover={{ y: -3 }} transition={{ type: "spring", stiffness: 300, damping: 24 }} className="panel flex h-full flex-col overflow-hidden p-7">
        {children}
      </motion.div>
    </Reveal>
  );
}

function CardText({ icon: Icon, title, text }: { icon: typeof Rows3; title: string; text: string }) {
  return (
    <>
      <span className="mb-4 grid h-10 w-10 place-items-center rounded-lg bg-ink text-white" aria-hidden><Icon size={19} /></span>
      <h3 className="font-display text-[22px] font-semibold tracking-[-0.02em]">{title}</h3>
      <p className="mt-2 text-[15.5px] leading-relaxed text-muted">{text}</p>
    </>
  );
}

export function Features() {
  return (
    <section className="bg-canvas py-24 md:py-32" id="features">
      <div className="wrap">
        <Heading
          eyebrow="What you get"
          title="A second pair of eyes that never gets tired of spreadsheets."
          lede="Built for people who are sent data by other people and have to trust it. You do not need to know what the rules should be."
        />
        <div className="mt-14 grid gap-4 md:grid-cols-6">
          <Card className="md:col-span-4">
            <CardText icon={ScanSearch} title="Finds what the eye misses" text="It works out what each column is, an ID, a date, an email, a category, before judging it. That is why it can say an age of 999 is impossible without being told." />
            <ul className="mt-6 grid gap-2 sm:grid-cols-2" aria-hidden>
              {[
                ["age", 'has 2 impossible values: "999", "-4".'],
                ["email", "has 4 values that are not email addresses."],
                ["signup_date", "mixes 2 date formats."],
                ["country", "has 3 spellings of the same value."],
              ].map(([column, text]) => (
                <li key={column} className="rounded-lg border border-line bg-soft px-3 py-2.5 text-[13.5px] leading-snug">
                  <span className="chip mr-1">{column}</span>{text}
                </li>
              ))}
            </ul>
          </Card>

          <Card className="md:col-span-2" delay={0.08}>
            <CardText icon={Lock} title="Stays on your computer" text="No upload, no account, no tracking. The app talks only to your own machine." />
            <div className="mt-6 flex flex-1 items-end" aria-hidden>
              <div className="w-full rounded-lg border border-line bg-soft p-3 font-mono text-[12px] text-muted">
                <p className="flex justify-between"><span>address</span><span className="text-ink">127.0.0.1</span></p>
                <p className="mt-1 flex justify-between"><span>sent to the internet</span><span className="text-ok-ink">0 bytes</span></p>
              </div>
            </div>
          </Card>

          <Card className="md:col-span-3" delay={0.05}>
            <CardText icon={History} title="Remembers last month's file" text="Tell it once that a file is good. It learns the columns, values and ranges, and compares every later version. You never write a rule." />
            <div className="mt-6 grid grid-cols-[1fr_auto_1fr] items-center gap-3 font-mono text-[12px]" aria-hidden>
              <div className="rounded-lg border border-line bg-soft p-3">
                <p className="text-muted">october</p>
                <p className="mt-1">8 columns</p><p>3,000 rows</p><p>3 countries</p>
              </div>
              <ArrowRight size={16} className="text-muted" />
              <div className="rounded-lg border border-crit-line bg-crit-bg p-3">
                <p className="text-crit-ink">november</p>
                <p className="mt-1"><span className="text-crit-ink">7</span> columns</p>
                <p><span className="text-crit-ink">1,200</span> rows</p>
                <p><span className="text-crit-ink">4</span> countries</p>
              </div>
            </div>
          </Card>

          <Card className="md:col-span-3" delay={0.12}>
            <CardText icon={Rows3} title="Hands you the rows to fix" text="Every finding opens the actual rows behind it, with the reason for each. Download them and send them back to whoever made the file." />
            <div className="mt-6 overflow-hidden rounded-lg border border-line font-mono text-[11.5px]" aria-hidden>
              <div className="grid grid-cols-[1.3fr_0.6fr_1fr_1fr] border-b border-line bg-soft text-muted">
                {["reason", "row", "order_id", "order_date"].map((h) => <span key={h} className="px-2.5 py-1.5">{h}</span>)}
              </div>
              {[["future date", "413", "7102", "2031-01-01"], ["future date", "456", "7145", "2031-01-01"], ["not unique", "902", "7102", "2026-11-03"]].map((row, i) => (
                <div key={i} className="grid grid-cols-[1.3fr_0.6fr_1fr_1fr] border-b border-soft2 last:border-0">
                  <span className="px-2.5 py-1.5 text-crit-ink">{row[0]}</span>
                  {row.slice(1).map((c, j) => <span key={j} className="px-2.5 py-1.5 text-slate2">{c}</span>)}
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
}

// ------------------------------------------------------------ plain language
const TRANSLATIONS: { wrong: string; jargon: string; plain: ReactNode }[] = [
  { wrong: "Dates in the future", jargon: "future_dates: 15", plain: <><span className="chip mr-1">order_date</span>has 15 dates in the future (latest: 2031-01-01).</> },
  { wrong: "Repeated IDs", jargon: "is_unique: False", plain: <><span className="chip mr-1">order_id</span>should be unique, but 2 values appear more than once.</> },
  { wrong: "A column went missing", jargon: "KeyError: 'vat_rate'", plain: <>1 column is missing: <span className="chip mx-1">vat_rate</span>. It was in last month's file.</> },
  { wrong: "Odd values", jargon: "outliers outside [-8.00, 96.00]", plain: <><span className="chip mr-1">age</span>has 2 impossible values: "999", "-5". An age should be between 0 and 120.</> },
];

export function PlainLanguage() {
  return (
    <section className="py-24 md:py-32">
      <div className="wrap">
        <Heading
          eyebrow="Plain language"
          title="Sentences you can act on, or forward."
          lede="Each finding names the column, the count and an example. No statistics unless you ask why."
        />
        <div className="mt-14 flex flex-col gap-3">
          {TRANSLATIONS.map((row, i) => (
            <Reveal key={row.wrong} delay={0.06 * i}>
              <div className="grid items-center gap-x-6 gap-y-2 rounded-2xl border border-line p-5 md:grid-cols-[180px_minmax(0,1fr)_auto_minmax(0,1.4fr)]">
                <p className="eyebrow !tracking-[0.08em]">{row.wrong}</p>
                <p className="font-mono text-[13px] text-muted line-through decoration-line2">{row.jargon}</p>
                <ArrowRight size={16} className="hidden text-muted md:block" aria-hidden />
                <p className="flex items-start gap-2 text-[16px] leading-snug">
                  <MessageSquareText size={18} className="mt-0.5 shrink-0" aria-hidden />
                  <span>{row.plain}</span>
                </p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

// -------------------------------------------------------------- how it works
const STEPS: [string, string][] = [
  ["Check", "Drop a file on the page, or run one command. You get a verdict and a short list, worst first."],
  ["Remember", "When a file is good, save it as normal. You see exactly what was learned before anything is saved."],
  ["Check the next one", "Next month's file is compared automatically: missing columns, new values, fewer rows, shifted numbers."],
  ["Act", "Download the affected rows with the reason for each, or a one-page summary to send back."],
];

export function HowItWorks() {
  return (
    <section className="dark-zone relative overflow-hidden bg-ink py-24 text-white md:py-32" id="how">
      <DotPattern width={24} height={24} cr={1} className="text-white/[0.09] [mask-image:linear-gradient(to_bottom,black,transparent_85%)]" />
      <div className="wrap relative grid items-start gap-14 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)]">
        <div>
          <Reveal>
            <p className="eyebrow mb-4 !text-white/50">How it works</p>
            <h2 className="h2">Four steps. The first takes under a minute.</h2>
          </Reveal>
          <ol className="mt-10 flex flex-col">
            {STEPS.map(([title, text], i) => (
              <Reveal key={title} delay={0.08 * i}>
                <li className="grid grid-cols-[44px_minmax(0,1fr)] gap-x-4 border-t border-white/10 py-6">
                  <span className="font-mono text-[13px] text-white/40">0{i + 1}</span>
                  <div>
                    <h3 className="font-display text-[21px] font-semibold tracking-[-0.02em]">{title}</h3>
                    <p className="mt-1.5 text-[15.5px] leading-relaxed text-white/65">{text}</p>
                  </div>
                </li>
              </Reveal>
            ))}
          </ol>
        </div>

        <Reveal delay={0.15} className="lg:sticky lg:top-28">
          <Terminal className="max-h-none w-full max-w-none border-white/15 bg-[#0f1117] text-[12.5px] text-white/90 [&_code]:gap-y-1.5">
            <TypingAnimation className="text-white">$ pdq check orders_november.csv</TypingAnimation>
            <AnimatedSpan className="text-[#f87171]">✖ NOT SAFE TO USE   2 problems, 2 warnings</AnimatedSpan>
            <AnimatedSpan className="text-white/45">  1,200 rows, 7 columns. Compared with orders_october.csv.</AnimatedSpan>
            <AnimatedSpan className="pt-2 text-[#f87171]">PROBLEMS</AnimatedSpan>
            <AnimatedSpan> 1  1 column is missing: discount_code.</AnimatedSpan>
            <AnimatedSpan> 2  order_date has 15 dates in the future.</AnimatedSpan>
            <AnimatedSpan className="pt-2 text-[#fbbf24]">WARNINGS</AnimatedSpan>
            <AnimatedSpan> 3  The file has 1,200 rows. Last time 3,000.</AnimatedSpan>
            <AnimatedSpan> 4  country has 1 value never seen before: "Togo".</AnimatedSpan>
            <AnimatedSpan className="pt-2 text-[#4ade80]">UNCHANGED  customer_id, email, amount</AnimatedSpan>
            <TypingAnimation className="pt-2 text-white">$ pdq rows orders_november.csv</TypingAnimation>
            <AnimatedSpan className="text-white/45">Saved 25 rows to orders_november_problem_rows.csv</AnimatedSpan>
          </Terminal>
          <p className="mt-3 font-mono text-[12px] text-white/40">Exit codes 0, 1 and 2 make it usable in scheduled jobs.</p>
        </Reveal>
      </div>
    </section>
  );
}

// ------------------------------------------------------------- ways to use it
const WAYS = [
  {
    id: "browser", label: "In your browser", command: "pdq ui",
    who: "For people who would rather not use a terminal.",
    points: ["Drag and drop a file", "See the rows behind any finding", "Review what was learned before saving", "A history of every dataset you check"],
    code: `$ pdq ui\nPyDataQuality is running at http://127.0.0.1:8765/\nDrop a file on the page to check it.\nFiles stay on this computer.`,
  },
  {
    id: "terminal", label: "In a terminal", command: "pdq check file.csv",
    who: "For quick checks, scheduled jobs and pipelines.",
    points: ["One command, no configuration", "Exit codes 0, 1, 2 for automation", "JSON output with --json", "Your own rules in plain sentences"],
    code: `$ pdq check orders.csv --rule "price: greater than 0"\n$ pdq accept orders.csv\n$ pdq rows orders.csv\n$ pdq report orders.csv`,
  },
  {
    id: "python", label: "In Python", command: "pdq.check(df)",
    who: "For notebooks and scripts.",
    points: ["Works on a file path or a DataFrame", "Results display as a summary in notebooks", "Affected rows come back as a DataFrame", "The same findings as the app"],
    code: `import pydataquality as pdq\n\nresult = pdq.check("orders.csv")\nresult.verdict        # 'problems'\nresult.bad_rows()     # DataFrame, with a reason column`,
  },
] as const;

export function Ways() {
  const [active, setActive] = useState<(typeof WAYS)[number]["id"]>("browser");
  const way = WAYS.find((w) => w.id === active)!;
  return (
    <section className="py-24 md:py-32" id="use">
      <div className="wrap">
        <Heading eyebrow="Three ways in" title="Use it the way you already work." lede="The same checks and the same answer, whichever you choose." center />
        <Reveal delay={0.1}>
          <div role="tablist" aria-label="Ways to use PyDataQuality" className="mx-auto mt-10 flex w-fit max-w-full flex-wrap justify-center gap-1 rounded-xl border border-line bg-soft p-1">
            {WAYS.map((w) => (
              <button
                key={w.id}
                role="tab"
                type="button"
                id={`tab-${w.id}`}
                aria-selected={active === w.id}
                aria-controls="way-panel"
                onClick={() => setActive(w.id)}
                className={cn("relative min-h-[40px] rounded-lg px-4 text-[14.5px] font-medium transition-colors", active === w.id ? "text-white" : "text-muted hover:text-ink")}
              >
                {active === w.id && (
                  <motion.span layoutId="way-pill" className="absolute inset-0 rounded-lg bg-ink" transition={{ type: "spring", stiffness: 380, damping: 30 }} />
                )}
                <span className="relative">{w.label}</span>
              </button>
            ))}
          </div>
          <div id="way-panel" role="tabpanel" aria-labelledby={`tab-${way.id}`} className="panel mx-auto mt-6 max-w-[940px] overflow-hidden">
            <AnimatePresence mode="wait">
              <motion.div
                key={way.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.22 }}
                className="grid md:grid-cols-2"
              >
                <div className="p-7 md:p-9">
                  <span className="chip !text-[13px]">{way.command}</span>
                  <p className="mt-4 font-display text-[24px] font-semibold leading-tight tracking-[-0.02em]">{way.who}</p>
                  <ul className="mt-5 flex flex-col gap-2.5">
                    {way.points.map((point) => (
                      <li key={point} className="flex items-start gap-2.5 text-[15.5px] text-slate2">
                        <span className="mt-[9px] h-1.5 w-1.5 shrink-0 rounded-full bg-ink" aria-hidden />
                        {point}
                      </li>
                    ))}
                  </ul>
                </div>
                <pre className="overflow-x-auto border-t border-line bg-soft p-7 font-mono text-[13px] leading-relaxed text-slate2 md:border-l md:border-t-0 md:p-9">{way.code}</pre>
              </motion.div>
            </AnimatePresence>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

// -------------------------------------------------------------- fit and FAQ
const FITS = ["Analysts with a monthly export", "Finance and operations teams with supplier or bank files", "Researchers with survey downloads", "Data scientists with this week's extract"];
const NOT = ["It checks files that fit in your computer's memory", "It does not monitor a data warehouse", "It does not fix or edit your data", "On a first check it never says “safe”, only “nothing obviously wrong”"];

const FAQ: [string, string][] = [
  ["Does my data leave my computer?", "No. The app is a small program running on your own machine. It makes no requests to the internet, has no account and collects nothing. A file you drop in is read and then deleted from a temporary folder."],
  ["Do I need to know Python?", "No. Install it once, run pdq ui, and use the page in your browser. Python is only needed to install it."],
  ["How does it know what is wrong without being told?", "Two ways. Some things are wrong in any file: duplicate rows, repeated IDs, a date column with two formats. Others are wrong for the kind of column: once it recognises an age, a date or an email, it knows a negative age or a date in 2031 is suspect. After you save a file as normal, it also compares each new file with that."],
  ["What if it flags something that is fine?", "Mark the finding as fine and it stops being reported for that dataset. If the whole file is the new normal, save it as normal. It is tuned to stay quiet: a clean file says “nothing obviously wrong”."],
  ["What file types does it read?", "CSV, TSV, Excel (it asks which sheet), JSON and Parquet."],
  ["Is it really free?", "Yes. It is open source under the MIT licence. There is no paid tier."],
];

export function Fit() {
  return (
    <section className="bg-canvas py-24 md:py-32">
      <div className="wrap grid gap-4 md:grid-cols-2">
        <Reveal>
          <div className="panel h-full p-8">
            <p className="eyebrow mb-3">Who it is for</p>
            <h3 className="font-display text-[26px] font-semibold tracking-[-0.02em]">People who are sent files and have to trust them.</h3>
            <ul className="mt-6 flex flex-col gap-3">
              {FITS.map((item) => (
                <li key={item} className="flex items-start gap-3 text-[16px] text-slate2"><Plus size={18} className="mt-0.5 shrink-0 text-ok-ink" aria-hidden />{item}</li>
              ))}
            </ul>
          </div>
        </Reveal>
        <Reveal delay={0.08}>
          <div className="panel h-full p-8">
            <p className="eyebrow mb-3">What it is not</p>
            <h3 className="font-display text-[26px] font-semibold tracking-[-0.02em]">A small tool with one job. Here are its limits.</h3>
            <ul className="mt-6 flex flex-col gap-3">
              {NOT.map((item) => (
                <li key={item} className="flex items-start gap-3 text-[16px] text-slate2"><Minus size={18} className="mt-0.5 shrink-0 text-muted" aria-hidden />{item}</li>
              ))}
            </ul>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

export function Questions() {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <section className="py-24 md:py-32" id="faq">
      <div className="wrap grid gap-12 lg:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)]">
        <Heading eyebrow="Questions" title="Before you trust it with a file." lede={<>More detail in the <a className="underline underline-offset-4" href={LINKS.guide}>user guide</a> and the <a className="underline underline-offset-4" href={LINKS.security}>security notes</a>.</>} />
        <Reveal delay={0.1}>
          <ul className="border-t border-line">
            {FAQ.map(([question, answer], i) => {
              const isOpen = open === i;
              return (
                <li key={question} className="border-b border-line">
                  <h3>
                    <button
                      type="button"
                      aria-expanded={isOpen}
                      aria-controls={`faq-${i}`}
                      onClick={() => setOpen(isOpen ? null : i)}
                      className="flex min-h-[64px] w-full items-center justify-between gap-4 py-4 text-left font-display text-[19px] font-medium tracking-[-0.01em]"
                    >
                      {question}
                      <motion.span animate={{ rotate: isOpen ? 45 : 0 }} transition={{ duration: 0.2 }} className="grid h-8 w-8 shrink-0 place-items-center rounded-full border border-line" aria-hidden>
                        <Plus size={16} />
                      </motion.span>
                    </button>
                  </h3>
                  <AnimatePresence initial={false}>
                    {isOpen && (
                      <motion.div
                        id={`faq-${i}`}
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.28, ease: [0.21, 0.6, 0.35, 1] }}
                        className="overflow-hidden"
                      >
                        <p className="max-w-[640px] pb-6 text-[16px] leading-relaxed text-muted">{answer}</p>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </li>
              );
            })}
          </ul>
        </Reveal>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------- CTA
export function CallToAction() {
  return (
    <section className="pb-24 md:pb-32">
      <div className="wrap">
        <Reveal>
          <div className="dark-zone relative overflow-hidden rounded-3xl bg-ink px-6 py-16 text-center text-white md:px-12 md:py-24">
            <DotPattern width={22} height={22} cr={1} className="text-white/[0.1] [mask-image:radial-gradient(ellipse_at_center,black,transparent_70%)]" />
            <BorderBeam size={320} duration={11} colorFrom="#ffffff" colorTo="#6b7280" borderWidth={1.5} />
            <div className="relative mx-auto max-w-[640px]">
              <h2 className="font-display text-[38px] font-semibold leading-[1.05] tracking-[-0.035em] md:text-[56px]">Check your first file in a minute.</h2>
              <p className="mt-5 text-[17px] text-white/65">Install it, run <span className="font-mono text-white">pdq ui</span>, and drop in the file you trust least.</p>
              <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
                <CopyCommand command="pip install pydataquality" dark />
                <a href={LINKS.quickstart} className="btn bg-white text-ink hover:bg-soft2">
                  Read the quickstart <ArrowRight size={16} aria-hidden />
                </a>
              </div>
              <p className="mt-6 flex items-center justify-center gap-1.5 font-mono text-[12px] text-white/40">
                <CopyIcon size={12} aria-hidden /> Python 3.8+ · reads CSV, Excel, JSON and Parquet · MIT licence
              </p>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
