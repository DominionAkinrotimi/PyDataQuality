import { useEffect, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { ArrowRight, Check, CircleCheck, CircleX, Copy, FileSpreadsheet, ShieldCheck } from "lucide-react";
import { BorderBeam } from "@/components/magicui/border-beam";
import { DotPattern } from "@/components/magicui/dot-pattern";
import { cn } from "@/lib/utils";

export const LINKS = {
  github: "https://github.com/DominionAkinrotimi/PyDataQuality",
  quickstart: "https://github.com/DominionAkinrotimi/PyDataQuality/blob/main/docs/quickstart.md",
  guide: "https://github.com/DominionAkinrotimi/PyDataQuality/blob/main/docs/user_guide.md",
  security: "https://github.com/DominionAkinrotimi/PyDataQuality/blob/main/SECURITY.md",
  pypi: "https://pypi.org/project/pydataquality/",
};

export function CopyCommand({ command, dark = false }: { command: string; dark?: boolean }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(command);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      /* the command is selectable text, so copying by hand still works */
    }
  };
  return (
    <button
      type="button"
      onClick={copy}
      aria-label={`Copy the command: ${command}`}
      className={cn(
        "group inline-flex min-h-[44px] items-center gap-3 rounded-lg border px-4 font-mono text-[14px] transition-colors",
        dark ? "border-white/15 bg-white/5 text-white hover:bg-white/10" : "border-line bg-white text-ink hover:border-line2 hover:bg-soft",
      )}
    >
      <span className={dark ? "text-white/40" : "text-muted"} aria-hidden>$</span>
      <span className="select-all">{command}</span>
      <span className={cn("ml-1 grid h-6 w-6 place-items-center rounded", dark ? "text-white/60" : "text-muted")} aria-hidden>
        {copied ? <Check size={15} /> : <Copy size={15} />}
      </span>
      <span className="sr-only" role="status">{copied ? "Copied" : ""}</span>
    </button>
  );
}

// ---------------------------------------------------------------- the demo
type Phase = "drop" | "scan" | "verdict";

interface Scenario {
  file: string;
  context: string;
  rows: string[][];
  bad: number[];
  tone: "crit" | "ok";
  headline: string;
  summary: string;
  findings: { level: "problem" | "warning" | "ok"; text: string; column?: string }[];
}

const HEADERS = ["order_id", "order_date", "country", "amount"];

const SCENARIOS: Scenario[] = [
  {
    file: "orders_november.csv",
    context: "1,200 rows · compared with orders_october.csv",
    rows: [
      ["7101", "2026-11-02", "Nigeria", "54.20"],
      ["7102", "2031-01-01", "Ghana", "61.75"],
      ["7103", "2026-11-02", "Kenya", "48.10"],
      ["7104", "2026-11-03", "Nigeria", "72.00"],
      ["7102", "2026-11-03", "Togo", "39.95"],
      ["7106", "2026-11-04", "Ghana", "58.30"],
    ],
    bad: [1, 4],
    tone: "crit",
    headline: "Not safe to use",
    summary: "2 problems and 1 warning",
    findings: [
      { level: "problem", column: "order_date", text: "has 15 dates in the future (latest: 2031-01-01)." },
      { level: "problem", column: "order_id", text: "had no repeats last time. Now 4 values appear more than once." },
      { level: "warning", column: "country", text: 'has 1 value never seen before: "Togo" (10 rows).' },
    ],
  },
  {
    file: "orders_december.csv",
    context: "3,104 rows · compared with orders_october.csv",
    rows: [
      ["8101", "2026-12-01", "Nigeria", "51.40"],
      ["8102", "2026-12-01", "Ghana", "66.10"],
      ["8103", "2026-12-02", "Kenya", "47.85"],
      ["8104", "2026-12-02", "Nigeria", "70.25"],
      ["8105", "2026-12-03", "Kenya", "42.60"],
      ["8106", "2026-12-03", "Ghana", "59.90"],
    ],
    bad: [],
    tone: "ok",
    headline: "Looks like last time",
    summary: "Nothing needs your attention",
    findings: [
      { level: "ok", text: "All 8 columns are present, with the same types as before." },
      { level: "ok", text: "3,104 rows, within the usual range." },
      { level: "ok", text: "No new values, no repeated IDs, no dates in the future." },
    ],
  },
];

const DURATION: Record<Phase, number> = { drop: 1300, scan: 2100, verdict: 4600 };
const NEXT: Record<Phase, Phase> = { drop: "scan", scan: "verdict", verdict: "drop" };

function Demo() {
  const reduce = useReducedMotion();
  const [index, setIndex] = useState(0);
  const [phase, setPhase] = useState<Phase>(reduce ? "verdict" : "drop");
  const scenario = SCENARIOS[index];

  useEffect(() => {
    if (reduce) return;
    const timer = window.setTimeout(() => {
      if (phase === "verdict") setIndex((i) => (i + 1) % SCENARIOS.length);
      setPhase(NEXT[phase]);
    }, DURATION[phase]);
    return () => window.clearTimeout(timer);
  }, [phase, reduce]);

  const scanned = phase !== "drop";
  const done = phase === "verdict";
  const crit = scenario.tone === "crit";

  return (
    <div
      className="relative mx-auto w-full max-w-[940px] overflow-hidden rounded-2xl border border-line bg-white shadow-[0_1px_2px_rgba(9,10,15,0.04),0_24px_60px_-20px_rgba(9,10,15,0.18)]"
      role="img"
      aria-label="Animated example. A file called orders_november.csv is checked and found not safe to use, with two problems and one warning. The next file, orders_december.csv, looks like last time."
    >
      <BorderBeam size={220} duration={9} colorFrom="#090a0f" colorTo="#9ca3af" borderWidth={1.5} />

      <div className="flex items-center gap-2 border-b border-line bg-soft px-4 py-2.5" aria-hidden>
        <span className="h-2.5 w-2.5 rounded-full bg-line2" />
        <span className="h-2.5 w-2.5 rounded-full bg-line2" />
        <span className="h-2.5 w-2.5 rounded-full bg-line2" />
        <span className="ml-3 font-mono text-[12px] text-muted">127.0.0.1 · pdq ui</span>
        <span className="ml-auto hidden items-center gap-1.5 font-mono text-[11px] text-muted sm:flex">
          <ShieldCheck size={13} /> nothing leaves this computer
        </span>
      </div>

      <div className="grid gap-0 md:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)]" aria-hidden>
        {/* The file */}
        <div className="border-b border-line p-5 md:border-b-0 md:border-r">
          <AnimatePresence mode="wait">
            <motion.div
              key={scenario.file}
              initial={{ opacity: 0, y: -14, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 8 }}
              transition={{ type: "spring", stiffness: 260, damping: 22 }}
              className="mb-3 inline-flex max-w-full items-center gap-2 rounded-lg border border-line bg-soft px-3 py-2"
            >
              <FileSpreadsheet size={16} className="shrink-0" />
              <span className="truncate font-mono text-[13px]">{scenario.file}</span>
            </motion.div>
          </AnimatePresence>
          <p className="mb-3 font-mono text-[11px] text-muted">{scenario.context}</p>

          <div className="relative overflow-hidden rounded-lg border border-line">
            <div className="grid grid-cols-4 border-b border-line bg-soft">
              {HEADERS.map((h) => (
                <span key={h} className="truncate px-2.5 py-1.5 font-mono text-[10.5px] font-medium text-muted">{h}</span>
              ))}
            </div>
            {scenario.rows.map((row, r) => {
              const flagged = scanned && scenario.bad.includes(r);
              return (
                <motion.div
                  key={scenario.file + r}
                  className="grid grid-cols-4 border-b border-soft2 last:border-0"
                  animate={{ backgroundColor: flagged ? "#fef2f2" : "#ffffff" }}
                  transition={{ delay: flagged && phase === "scan" ? 0.3 + r * 0.28 : 0, duration: 0.25 }}
                >
                  {row.map((cell, c) => (
                    <span key={c} className={cn("truncate px-2.5 py-[7px] font-mono text-[11.5px]", flagged ? "text-crit-ink" : "text-slate2")}>
                      {cell}
                    </span>
                  ))}
                </motion.div>
              );
            })}
            {phase === "scan" && (
              <motion.div
                className="pointer-events-none absolute inset-x-0 h-10 bg-gradient-to-b from-transparent via-ink/[0.07] to-transparent"
                initial={{ top: "0%" }}
                animate={{ top: "100%" }}
                transition={{ duration: 1.9, ease: "linear" }}
              >
                <div className="absolute inset-x-0 bottom-0 h-px bg-ink/60" />
              </motion.div>
            )}
          </div>
        </div>

        {/* The answer */}
        <div className="min-h-[300px] p-5">
          <AnimatePresence mode="wait">
            {!done ? (
              <motion.div
                key="waiting"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex h-full min-h-[260px] flex-col items-center justify-center gap-3 text-muted"
              >
                <span className="font-mono text-[12px]">{phase === "drop" ? "file received" : "checking every column…"}</span>
                <span className="h-1 w-40 overflow-hidden rounded bg-soft2">
                  <motion.span
                    className="block h-full rounded bg-ink"
                    initial={{ width: "4%" }}
                    animate={{ width: phase === "scan" ? "100%" : "12%" }}
                    transition={{ duration: phase === "scan" ? 1.9 : 0.6, ease: "easeInOut" }}
                  />
                </span>
              </motion.div>
            ) : (
              <motion.div key={"verdict" + scenario.file} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <motion.div
                  initial={{ opacity: 0, y: 10, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  transition={{ type: "spring", stiffness: 240, damping: 20 }}
                  className={cn(
                    "mb-3 flex items-center gap-3 rounded-xl border px-4 py-3.5",
                    crit ? "border-crit-line bg-crit-bg" : "border-ok-line bg-ok-bg",
                  )}
                >
                  {crit ? <CircleX size={26} className="shrink-0 text-crit-ink" /> : <CircleCheck size={26} className="shrink-0 text-ok-ink" />}
                  <div>
                    <p className={cn("font-display text-[22px] font-semibold leading-tight tracking-[-0.02em]", crit ? "text-crit-ink" : "text-ok-ink")}>
                      {scenario.headline}
                    </p>
                    <p className="text-[13px] text-slate2">{scenario.summary}</p>
                  </div>
                </motion.div>
                <ul className="flex flex-col gap-2">
                  {scenario.findings.map((finding, i) => (
                    <motion.li
                      key={i}
                      initial={{ opacity: 0, x: 12 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.25 + i * 0.16, duration: 0.35, ease: "easeOut" }}
                      className="flex items-start gap-2.5 rounded-lg border border-line px-3 py-2.5 text-[13.5px] leading-snug"
                    >
                      <span
                        className={cn(
                          "mt-[5px] h-2 w-2 shrink-0 rounded-full",
                          finding.level === "problem" ? "bg-crit-ink" : finding.level === "warning" ? "bg-warn-ink" : "bg-ok-ink",
                        )}
                      />
                      <span>
                        {finding.column && <span className="chip mr-1">{finding.column}</span>}
                        {finding.text}
                      </span>
                    </motion.li>
                  ))}
                </ul>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

// -------------------------------------------------------------------- hero
const rise = {
  hidden: { opacity: 0, y: 18, filter: "blur(6px)" },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
    transition: { delay: 0.08 * i, duration: 0.6, ease: [0.21, 0.6, 0.35, 1] as [number, number, number, number] },
  }),
};

export function Hero() {
  return (
    <section className="relative overflow-hidden pb-16 pt-28 md:pb-24 md:pt-36" id="top">
      <DotPattern
        width={22}
        height={22}
        cr={1}
        className="text-ink/20 [mask-image:radial-gradient(ellipse_60%_55%_at_50%_30%,black,transparent)]"
      />
      <div className="wrap relative">
        <motion.div initial="hidden" animate="show" className="mx-auto flex max-w-[860px] flex-col items-center text-center">
          <motion.a
            variants={rise}
            custom={0}
            href={LINKS.github}
            className="mb-6 inline-flex items-center gap-2 rounded-full border border-line bg-white px-3.5 py-1.5 text-[13px] text-slate2 transition-colors hover:border-line2"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-ok-ink" aria-hidden />
            Free and open source · runs on your own computer
            <ArrowRight size={14} aria-hidden />
          </motion.a>

          <motion.h1
            variants={rise}
            custom={1}
            className="font-display text-[44px] font-semibold leading-[1.02] tracking-[-0.04em] sm:text-[60px] md:text-[76px]"
          >
            Know whether a data file is <span className="relative whitespace-nowrap">safe to use
              <motion.span
                aria-hidden
                className="absolute -bottom-1 left-0 h-[5px] w-full origin-left rounded bg-ink md:-bottom-2 md:h-[7px]"
                initial={{ scaleX: 0 }}
                animate={{ scaleX: 1 }}
                transition={{ delay: 0.75, duration: 0.7, ease: [0.21, 0.6, 0.35, 1] }}
              />
            </span>.
          </motion.h1>

          <motion.p variants={rise} custom={2} className="lede mt-7 max-w-[620px]">
            Someone sends you a spreadsheet or a CSV. Drop it in and get a plain answer in seconds:
            what is wrong with it, and what changed since the last one.
          </motion.p>

          <motion.div variants={rise} custom={3} className="mt-9 flex flex-wrap items-center justify-center gap-3">
            <CopyCommand command="pip install pydataquality" />
            <a href="#how" className="btn-dark">
              See how it works <ArrowRight size={16} aria-hidden />
            </a>
          </motion.div>

          <motion.p variants={rise} custom={4} className="mt-5 font-mono text-[12px] text-muted">
            Then run <span className="text-ink">pdq ui</span> · Python 3.8+ · Windows, macOS, Linux
          </motion.p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.55, duration: 0.8, ease: [0.21, 0.6, 0.35, 1] }}
          className="mt-14 md:mt-20"
        >
          <Demo />
        </motion.div>
      </div>
    </section>
  );
}
