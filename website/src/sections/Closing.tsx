import { useRef, useState } from "react";
import { AnimatePresence, motion, useInView } from "motion/react";
import { ArrowRight, Check, Minus, Plus } from "lucide-react";
import { BorderBeam } from "@/components/magicui/border-beam";
import { CopyCommand, Heading, Reveal, TiltCard } from "@/components/ui";
import { LINKS } from "@/lib/links";
import { cn } from "@/lib/utils";

// ------------------------------------------------------------- ways to use it
const WAYS = [
  {
    id: "browser", label: "In your browser", command: "pdq ui",
    who: "For people who would rather not use a terminal.",
    points: ["Drag and drop a file", "See the rows behind any finding", "Review what was learned before saving", "A history of every kind of file you check"],
    code: `$ pdq ui\n\nAn app opens in your browser.\nDrop a file on it to check it.\nIt is served from your own computer\nand loads nothing from the internet.`,
  },
  {
    id: "terminal", label: "In a terminal", command: "pdq check file.csv",
    who: "For quick checks and scheduled jobs.",
    points: ["One command, nothing to configure", "Exit codes 0, 1 and 2 for automation", "Machine-readable output with --json", "Your own rules in plain sentences"],
    code: `$ pdq check orders.csv --rule "price: greater than 0"\n$ pdq accept orders.csv\n$ pdq rows orders.csv\n$ pdq report orders.csv`,
  },
  {
    id: "python", label: "In Python", command: "pdq.check(df)",
    who: "For notebooks and scripts.",
    points: ["Works on a file path or a DataFrame", "Shows the same summary in a notebook", "Affected rows come back as a DataFrame", "The same findings as the app"],
    code: `import pydataquality as pdq\n\nresult = pdq.check("orders.csv")\nresult.verdict        # 'problems'\nresult.bad_rows()     # DataFrame, with a reason column`,
  },
] as const;

export function Ways() {
  const [active, setActive] = useState<(typeof WAYS)[number]["id"]>("browser");
  const way = WAYS.find((w) => w.id === active)!;
  return (
    <section className="later py-24 md:py-36" id="use">
      <div className="wrap">
        <Heading eyebrow="Three ways to use it" title="Use it the way you already work." lede="The same checks and the same answer, whichever you choose." center />
        <Reveal delay={0.1}>
          <div role="group" aria-label="Ways to use PyDataQuality" className="mx-auto mt-10 flex w-fit max-w-full flex-wrap justify-center gap-1 rounded-xl border border-white/10 bg-white/[0.04] p-1">
            {WAYS.map((w) => (
              <button
                key={w.id}
                type="button"
                aria-pressed={active === w.id}
                onClick={() => setActive(w.id)}
                className={cn("relative min-h-[44px] cursor-pointer rounded-lg px-4 text-[14.5px] font-medium transition-colors duration-200", active === w.id ? "text-ink" : "text-fog hover:text-white")}
              >
                {active === w.id && <motion.span layoutId="way-pill" className="absolute inset-0 rounded-lg bg-white" transition={{ type: "spring", stiffness: 380, damping: 32 }} />}
                <span className="relative">{w.label}</span>
              </button>
            ))}
          </div>
          <div className="card mx-auto mt-6 max-w-[980px] overflow-hidden shadow-lift" aria-live="polite">
            <AnimatePresence mode="wait" initial={false}>
              <motion.div key={way.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.22 }} className="grid md:grid-cols-2">
                <div className="p-7 md:p-10">
                  <span className="chip-dark !text-[13px]">{way.command}</span>
                  <p className="mt-5 font-display text-[26px] font-semibold leading-tight tracking-[-0.01em]">{way.who}</p>
                  <ul className="mt-6 flex flex-col gap-3">
                    {way.points.map((point) => (
                      <li key={point} className="flex items-start gap-3 text-[16px] text-white/85">
                        <Check size={17} className="mt-1 shrink-0 text-white/50" aria-hidden />
                        {point}
                      </li>
                    ))}
                  </ul>
                </div>
                <pre tabIndex={0} aria-label={`Example: ${way.label}`} className="overflow-x-auto border-t border-white/[0.09] bg-ink p-7 font-mono text-[13px] leading-relaxed text-white/80 md:border-l md:border-t-0 md:p-10">{way.code}</pre>
              </motion.div>
            </AnimatePresence>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

// -------------------------------------------------------------- fit and FAQ
const FITS = ["Analysts with a monthly export", "Finance and operations staff with supplier or bank files", "Researchers with survey downloads", "Anyone who knows Excel and is sent files by other people"];
const NOT = [
  "It does not fix or edit your file. It tells you what is wrong and where.",
  "It does not use AI. The checks are fixed rules, so the same file gives the same answer.",
  "It does not run on a server or watch a database. It checks a file when you ask.",
  "It reads files that fit in your computer's memory, not larger ones.",
  "On a first check it never says “safe”, only “nothing obviously wrong”.",
];

export function Fit() {
  return (
    <section className="later border-t border-white/[0.07] bg-night-1 py-24 md:py-36" id="fit">
      <div className="wrap grid gap-4 md:grid-cols-2">
        <Reveal className="h-full">
          <TiltCard className="bg-night-2 p-8 md:p-10">
            <p className="eyebrow mb-4">Who it is for</p>
            <h2 className="font-display text-[28px] font-semibold leading-tight tracking-[-0.01em] md:text-[32px]">People who are sent files and have to trust them.</h2>
            <ul className="mt-7 flex flex-col gap-3.5">
              {FITS.map((item) => (
                <li key={item} className="flex items-start gap-3 text-[16.5px] text-white/85"><Plus size={18} className="mt-1 shrink-0 text-ok-glow" aria-hidden />{item}</li>
              ))}
            </ul>
          </TiltCard>
        </Reveal>
        <Reveal delay={0.08} className="h-full">
          <TiltCard className="bg-night-2 p-8 md:p-10">
            <p className="eyebrow mb-4">What it is not</p>
            <h2 className="font-display text-[28px] font-semibold leading-tight tracking-[-0.01em] md:text-[32px]">A small tool with one job. Here are its limits.</h2>
            <ul className="mt-7 flex flex-col gap-3.5">
              {NOT.map((item) => (
                <li key={item} className="flex items-start gap-3 text-[16.5px] text-white/85"><Minus size={18} className="mt-1 shrink-0 text-haze" aria-hidden />{item}</li>
              ))}
            </ul>
          </TiltCard>
        </Reveal>
      </div>
    </section>
  );
}

const FAQ: [string, string][] = [
  ["Does my file leave my computer?", "No. The app is a small program running on your own machine. It makes no requests to the internet, has no account and collects nothing. A file you drop in is read and then deleted from a temporary folder."],
  ["Do I need to know Python?", "No. Python has to be on your computer so you can install PyDataQuality, and that is all. After that you run pdq ui and use the page in your browser."],
  ["How does it know what is wrong without being told?", "Two ways. Some things are wrong in any file: duplicate rows, repeated IDs, a date column with two formats. Others are wrong for the kind of column: once it recognises an age, a date or an email, it knows a negative age or a date in 2031 is suspect. After you save a file as normal, it also compares each new file with that one."],
  ["What if it flags something that is fine?", "Mark the finding as fine and it stops being reported for that kind of file. If the whole file is the new normal, save it as normal. It is tuned to stay quiet: a clean file says “nothing obviously wrong”."],
  ["Will it fix the file for me?", "No. It never changes your file. It shows you the rows that are affected, with the reason for each, so you can correct them or send them back to whoever produced the file."],
  ["What kinds of file does it read?", "CSV, TSV, Excel, JSON and Parquet. For an Excel workbook with several sheets, it asks which one."],
  ["Is it really free?", "Yes. It is open source under the MIT licence. There is no paid version."],
];

export function Questions() {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <section className="later py-24 md:py-36" id="faq">
      <div className="wrap grid gap-12 lg:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)]">
        <Heading
          eyebrow="Questions"
          title="Before you trust it with a file."
          lede={<>More detail in the <a className="link text-white" href={LINKS.guide}>user guide</a> and the <a className="link text-white" href={LINKS.security}>security notes</a>.</>}
        />
        <Reveal delay={0.1}>
          <ul className="border-t border-white/10">
            {FAQ.map(([question, answer], i) => {
              const isOpen = open === i;
              return (
                <li key={question} className="border-b border-white/10">
                  <h3>
                    <button
                      type="button"
                      aria-expanded={isOpen}
                      aria-controls={`faq-${i}`}
                      onClick={() => setOpen(isOpen ? null : i)}
                      className="flex min-h-[68px] w-full cursor-pointer items-center justify-between gap-4 py-4 text-left font-display text-[19px] font-medium tracking-[-0.01em] transition-colors hover:text-white/80"
                    >
                      {question}
                      <motion.span animate={{ rotate: isOpen ? 45 : 0 }} transition={{ duration: 0.2 }} className="grid h-8 w-8 shrink-0 place-items-center rounded-full border border-white/15" aria-hidden>
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
                        <p className="max-w-[640px] pb-6 text-[16.5px] leading-relaxed text-fog">{answer}</p>
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
  const panel = useRef<HTMLDivElement>(null);
  const seen = useInView(panel, { margin: "100px" });
  return (
    <section className="later px-2 pb-6 md:px-4">
      <Reveal>
        <div ref={panel} className="grain relative mx-auto max-w-[1400px] overflow-hidden rounded-[24px] border border-white/10 bg-night-2 px-6 py-20 text-center md:rounded-[36px] md:px-12 md:py-32">
          <div aria-hidden className="grid-floor absolute inset-0 [mask-image:radial-gradient(ellipse_at_center,black,transparent_70%)]" />
          <div aria-hidden className="absolute inset-x-0 top-0 h-2/3 bg-[radial-gradient(ellipse_50%_100%_at_50%_0%,rgba(203,213,225,0.14),transparent)]" />
          {seen && <BorderBeam size={360} duration={12} colorFrom="#ffffff" colorTo="#64748b" borderWidth={1.5} />}
          <div className="relative mx-auto max-w-[680px]">
            <h2 className="font-display text-[40px] font-semibold leading-[1.0] tracking-[-0.015em] md:text-[68px]">Check the file you trust least.</h2>
            <p className="mx-auto mt-6 max-w-[480px] text-[17.5px] text-fog">Install it, run <span className="chip-dark !text-[14px]">pdq ui</span> and drop the file in.</p>
            <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
              <CopyCommand command="pip install pydataquality" />
              <a href={LINKS.quickstart} className="btn-white min-h-[48px]">
                Read the quickstart <ArrowRight size={16} aria-hidden />
              </a>
            </div>
            <p className="mt-7 font-mono text-[12.5px] text-haze">Reads CSV, Excel, JSON and Parquet · MIT licence</p>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
