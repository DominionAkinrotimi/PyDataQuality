import { useRef, useState } from "react";
import { AnimatePresence, motion, useInView } from "motion/react";
import { Check, Download, Minus, Plus } from "lucide-react";
import { BorderBeam } from "@/components/magicui/border-beam";
import { CopyCommand, Heading, Reveal, TiltCard } from "@/components/ui";
import { LINKS } from "@/lib/links";
import { cn } from "@/lib/utils";

// ------------------------------------------------------------- ways to use it
const WAYS = [
  {
    id: "browser", label: "In your browser", command: "pdq ui",
    who: "No terminal needed.",
    points: ["Drag and drop a file", "See the rows behind any finding", "Review what was learned before saving", "A history of every kind of file you check"],
    code: `$ pdq ui\n\nAn app opens in your browser.\nDrop a file on it to check it.\nIt is served from your own computer\nand loads nothing from the internet.`,
  },
  {
    id: "terminal", label: "In a terminal", command: "pdq check file.csv",
    who: "Quick checks and scheduled jobs.",
    points: ["One command, nothing to configure", "Exit codes 0, 1 and 2 for automation", "Machine-readable output with --json", "Your own rules in plain sentences"],
    code: `$ pdq check orders_september.csv\n\n✖ NOT SAFE TO USE   3 problems, 1 warning\n\nPROBLEMS\n  1  order_date has 9 dates in the future (latest: 2031-01-09).\n  2  order_id had no repeats last time. Now 1 value appears more than once, e.g. "8252".\n  3  1 column is missing: discount_code. It was in orders_august.csv.\n\nWARNINGS\n  4  country has 1 value never seen before: "Togo" (6 rows).`,
  },
  {
    id: "python", label: "In Python", command: "pdq.check(df)",
    who: "Notebooks and scripts.",
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
const FITS = ["Anyone handed a spreadsheet they have to trust", "Analysts with an export to report on", "Finance and operations staff with supplier or bank files", "Researchers with survey downloads"];
const NOT = [
  "It does not fix or edit your file.",
  "It does not use AI.",
  "It does not run on a server.",
  "It does not read files larger than memory.",
  "It cannot tell that a believable value is wrong.",
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
            <h2 className="font-display text-[28px] font-semibold leading-tight tracking-[-0.01em] md:text-[32px]">One job. Clear limits.</h2>
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

export const FAQ: [string, string][] = [
  ["I only have one file. Is that enough?", "Yes. It checks a single file on its own. Comparing with an earlier file is optional."],
  ["Does my file leave my computer?", "No. It makes no requests to the internet, has no account and collects nothing."],
  ["Do I need to know Python?", "No. Download the app for Windows or Mac and double-click it. It needs no Python and no terminal."],
  ["How does it know what is wrong?", "It works out what each column holds, then checks it. After you save a file as normal, it also compares each new file with that one."],
  ["What if it flags something that is fine?", "Mark it as fine and it stops being reported for that kind of file."],
  ["What does it save?", "A small text file describing your columns, only when you save a file as normal. Not your rows."],
  ["Is it free?", "Yes. Open source, MIT licence, no paid version."],
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

// ------------------------------------------------------------- get started
const SETUP: { title: string; text: string }[] = [
  { title: "Download", text: "One file, about 26 MB. No Python, no terminal." },
  { title: "Run it", text: "It installs for you only. No administrator password." },
  { title: "Drop a file in", text: "PyDataQuality opens in your browser. Your file stays on your computer." },
];

export function GetStarted() {
  return (
    <section className="later py-24 md:py-36" id="start">
      <div className="wrap">
        <Heading eyebrow="Get started" title="Download it. Double-click. Done." lede="Free, for Windows and Mac." />
        <Reveal delay={0.05}>
          <div className="mt-10 flex flex-wrap items-center gap-3">
            <a href={LINKS.windows} className="btn-white min-h-[52px] !px-6 text-[16px]">
              <Download size={18} aria-hidden /> Download for Windows
            </a>
            <a href={LINKS.mac} className="btn-ghost min-h-[52px] !px-6 text-[16px]">
              <Download size={18} aria-hidden /> Download for Mac
            </a>
          </div>
          <p className="mt-4 text-[14px] text-fog">Windows 10 or 11. Mac with Apple Silicon (M1 or newer). <a className="link text-white" href={LINKS.releases}>All downloads</a>.</p>
        </Reveal>
        <ol className="mt-12 grid grid-cols-[minmax(0,1fr)] gap-4 lg:grid-cols-3">
          {SETUP.map((step, i) => (
            <li key={step.title}>
              <Reveal delay={0.08 * i} className="h-full">
                <div className="card flex h-full flex-col p-6 md:p-7">
                  <p className="font-mono text-[12px] text-haze" aria-hidden>{i + 1}</p>
                  <h3 className="mt-3 font-display text-[22px] font-semibold leading-tight tracking-[-0.01em]">{step.title}</h3>
                  <p className="mt-2 text-[15.5px] leading-relaxed text-fog">{step.text}</p>
                </div>
              </Reveal>
            </li>
          ))}
        </ol>
        <Reveal delay={0.1}>
          <div className="mt-4 grid grid-cols-[minmax(0,1fr)] gap-4 lg:grid-cols-2">
            <div className="card p-6 md:p-7">
              <h3 className="font-display text-[19px] font-semibold tracking-[-0.005em]">Your computer will ask if you are sure</h3>
              <p className="mt-2 text-[15.5px] leading-relaxed text-fog">
                The app is new and not yet signed. On Windows, choose <span className="text-white">More info</span>, then <span className="text-white">Run anyway</span>.
                On a Mac, confirm it in <span className="text-white">System Settings, Privacy &amp; Security</span>.
              </p>
            </div>
            <div className="card p-6 md:p-7">
              <h3 className="font-display text-[19px] font-semibold tracking-[-0.005em]">Already use Python?</h3>
              <p className="mt-2 text-[15.5px] leading-relaxed text-fog">Install it with pip, then run <span className="chip-dark">pdq ui</span>.</p>
              <CopyCommand command="pip install pydataquality" className="mt-4" />
            </div>
          </div>
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
        <div ref={panel} className="relative mx-auto max-w-[1400px] overflow-hidden rounded-[24px] border border-white/10 bg-night-2 px-6 py-20 text-center md:rounded-[36px] md:px-12 md:py-32">
          <div aria-hidden className="grid-floor absolute inset-0 [mask-image:radial-gradient(ellipse_at_center,black,transparent_70%)]" />
          <div aria-hidden className="absolute inset-x-0 top-0 h-2/3 bg-[radial-gradient(ellipse_50%_100%_at_50%_0%,rgba(203,213,225,0.14),transparent)]" />
          {seen && <BorderBeam size={360} duration={12} colorFrom="#ffffff" colorTo="#64748b" borderWidth={1.5} />}
          <div className="relative mx-auto max-w-[680px]">
            <h2 className="font-display text-[40px] font-semibold leading-[1.0] tracking-[-0.015em] md:text-[68px]">Check the file you trust least.</h2>
            <p className="mx-auto mt-6 max-w-[480px] text-[17.5px] text-fog">Download it, open it and drop the file in.</p>
            <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
              <a href={LINKS.windows} className="btn-white min-h-[52px] !px-6 text-[16px]">
                <Download size={18} aria-hidden /> Download for Windows
              </a>
              <a href={LINKS.mac} className="btn-ghost min-h-[52px] !px-6 text-[16px]">
                <Download size={18} aria-hidden /> Download for Mac
              </a>
            </div>
            <p className="mt-7 font-mono text-[12.5px] text-haze">Free · Reads CSV, Excel and JSON · MIT licence</p>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
