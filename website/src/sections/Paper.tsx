import { useRef, type ReactNode } from "react";
import { motion, useInView, useScroll, useSpring } from "motion/react";
import { ArrowRight, MessageSquareText } from "lucide-react";
import { Heading, Reveal } from "@/components/ui";

/**
 * The light part of the page. It uses the app's own surfaces, white paper, hairlines and ink, so
 * the step from the site into the app is a small one.
 */

// ------------------------------------------------------------ plain language
const TRANSLATIONS: { wrong: string; jargon: string; plain: ReactNode }[] = [
  { wrong: "Dates in the future", jargon: "future_dates: 15", plain: <><span className="chip mr-1.5">order_date</span>has 15 dates in the future (latest: 2031-01-01).</> },
  { wrong: "Repeated IDs", jargon: "is_unique: False", plain: <><span className="chip mr-1.5">order_id</span>should be unique, but 2 values appear more than once.</> },
  { wrong: "A column went missing", jargon: "KeyError: 'discount_code'", plain: <>1 column is missing: <span className="chip mx-1">discount_code</span>. It was in orders_september.csv.</> },
  { wrong: "Impossible values", jargon: "outliers outside [-8.00, 96.00]", plain: <><span className="chip mr-1.5">age</span>has 2 impossible values: "999", "-4". An age should be between 0 and 120.</> },
];

function Translation({ row, index }: { row: (typeof TRANSLATIONS)[number]; index: number }) {
  const ref = useRef<HTMLLIElement>(null);
  const seen = useInView(ref, { once: true, margin: "-12%" });
  const delay = index * 0.12;
  return (
    <li ref={ref} className="grid items-center gap-x-6 gap-y-3 border-t border-line py-6 md:grid-cols-[170px_minmax(0,0.9fr)_auto_minmax(0,1.5fr)]">
      <p className="eyebrow !tracking-[0.08em]">{row.wrong}</p>
      <p className="relative w-fit font-mono text-[13.5px] text-muted">
        <span className="sr-only">What a tool usually prints: </span>
        {row.jargon}
        <motion.span aria-hidden className="absolute inset-x-0 top-1/2 h-px origin-left bg-crit-ink" initial={{ scaleX: 0 }} animate={{ scaleX: seen ? 1 : 0 }} transition={{ duration: 0.45, delay: delay + 0.15 }} />
      </p>
      <ArrowRight size={16} className="hidden text-muted md:block" aria-hidden />
      <motion.p
        className="flex items-start gap-2.5 text-[17px] leading-snug text-ink"
        initial={{ opacity: 0, x: -10 }}
        animate={seen ? { opacity: 1, x: 0 } : { opacity: 0, x: -10 }}
        transition={{ duration: 0.5, delay: delay + 0.45 }}
      >
        <MessageSquareText size={18} className="mt-0.5 shrink-0" aria-hidden />
        <span><span className="sr-only">What PyDataQuality writes: </span>{row.plain}</span>
      </motion.p>
    </li>
  );
}

function PlainLanguage() {
  return (
    <div className="wrap py-20 md:py-28" id="plain">
      <Heading
        eyebrow="Plain language"
        title="Sentences you can act on, or forward."
        lede="No jargon. No statistics unless you ask."
      />
      <ul className="mt-12 border-b border-line">
        {TRANSLATIONS.map((row, i) => <Translation key={row.wrong} row={row} index={i} />)}
      </ul>
    </div>
  );
}

// -------------------------------------------------------------- how it works
const STEPS: { title: string; text: string; command: string }[] = [
  { title: "Check", command: "pdq check orders.csv", text: "Drop a file in. Get a verdict." },
  { title: "Remember", command: "pdq accept orders.csv", text: "Save a good file as normal." },
  { title: "Check the next one", command: "pdq check orders_november.csv", text: "It is compared automatically." },
  { title: "Act", command: "pdq rows orders_november.csv", text: "Send the bad rows back." },
];

function HowItWorks() {
  const track = useRef<HTMLOListElement>(null);
  const { scrollYProgress } = useScroll({ target: track, offset: ["start 0.85", "end 0.6"] });
  const drawn = useSpring(scrollYProgress, { stiffness: 90, damping: 24 });
  return (
    <div className="wrap pb-20 md:pb-28" id="how">
      <Heading eyebrow="What you do" title="Four steps. You write no rules." lede="A button in the app, or a command." />
      <ol ref={track} className="relative mt-14 grid gap-10 md:grid-cols-4 md:gap-6">
        {/* The line fills as you scroll: down the side on a phone, across the top on a wide screen. */}
        <span aria-hidden className="absolute bottom-0 left-[15px] top-0 w-px bg-line md:bottom-auto md:left-0 md:right-0 md:top-[15px] md:h-px md:w-auto" />
        <motion.span aria-hidden style={{ scaleY: drawn }} className="absolute bottom-0 left-[15px] top-0 w-px origin-top bg-ink md:hidden" />
        <motion.span aria-hidden style={{ scaleX: drawn }} className="absolute left-0 right-0 top-[15px] hidden h-px origin-left bg-ink md:block" />
        {STEPS.map((step, i) => (
          <li key={step.title} className="relative pl-12 md:pl-0 md:pt-12">
            <span className="absolute left-0 top-0 grid h-[31px] w-[31px] place-items-center rounded-full border border-ink bg-ink font-mono text-[12px] text-white" aria-hidden>{i + 1}</span>
            <Reveal delay={0.08 * i}>
              <h3 className="font-display text-[22px] font-semibold tracking-[-0.005em]">{step.title}</h3>
              <p className="mt-2 text-[15.5px] leading-relaxed text-muted">{step.text}</p>
              <p className="mt-4 overflow-x-auto rounded-lg border border-line bg-white px-3 py-2.5 font-mono text-[12.5px] text-slate2">
                <span className="text-muted" aria-hidden>$ </span>{step.command}
              </p>
            </Reveal>
          </li>
        ))}
      </ol>
    </div>
  );
}

export function Paper() {
  return (
    <section className="later paper-zone relative px-2 md:px-4" aria-label="Plain language, and the four steps">
      <div className="mx-auto max-w-[1400px] overflow-hidden rounded-[24px] bg-paper text-ink shadow-sheet md:rounded-[36px] [color-scheme:light]">
        <PlainLanguage />
        <HowItWorks />
      </div>
    </section>
  );
}
