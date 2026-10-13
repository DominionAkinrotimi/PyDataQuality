import { useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion, useScroll, useSpring, useTransform } from "motion/react";
import { Heading, Reveal, WindowFrame } from "@/components/ui";
import { cn } from "@/lib/utils";
import check960 from "@/assets/shots/check-960.webp";
import check1920 from "@/assets/shots/check-1920.webp";
import result960 from "@/assets/shots/result-960.webp";
import result1920 from "@/assets/shots/result-1920.webp";
import rows960 from "@/assets/shots/rows-960.webp";
import rows1920 from "@/assets/shots/rows-1920.webp";
import save960 from "@/assets/shots/save-960.webp";
import save1920 from "@/assets/shots/save-1920.webp";

// Screenshots of the real app (pdq ui, version 0.3) checking its built-in sample file.
const SHOTS = [
  {
    id: "check", label: "Check", small: check960, large: check1920,
    title: "Drop a file in.",
    text: "The home screen has one job. Drop in a CSV, Excel, JSON or Parquet file, or try the built-in sample first.",
    alt: "The Check screen of the PyDataQuality app: the heading \"Is this file safe to use?\" above a large area to drop a file into, and a link to try a sample file.",
  },
  {
    id: "result", label: "Result", small: result960, large: result1920,
    title: "The answer comes first.",
    text: "The verdict is the largest thing on the screen. Under it, each finding is one sentence, worst first, with the rows behind it one click away.",
    alt: "The Result screen for the sample file: a red banner reading \"Problems found\", with 3 problems, 4 warnings and 2 clean columns, followed by findings such as \"6 rows are exact copies of another row.\"",
  },
  {
    id: "rows", label: "Affected rows", small: rows960, large: rows1920,
    title: "See the rows behind a finding.",
    text: "Every finding opens the actual rows, with the reason first and the column in question marked. Download them, or copy a short message to send back.",
    alt: "The Affected rows screen: a table of the 30 rows where country is spelled \"nigeria\", each with the reason \"spelling\", and buttons to copy a message or download the rows.",
  },
  {
    id: "save", label: "Save as normal", small: save960, large: save1920,
    title: "Review what it learned.",
    text: "Before a file becomes the standard for later ones, you see what was learned, column by column, in plain words. You write no rules.",
    alt: "The Save as normal screen: a table listing each column, what it holds, such as \"numbers, no repeats\", and what will be checked next time, such as \"must stay unique\".",
  },
] as const;

type ShotId = (typeof SHOTS)[number]["id"];

export function Tour() {
  const [active, setActive] = useState<ShotId>("result");
  const shot = SHOTS.find((s) => s.id === active)!;
  const reduced = useReducedMotion();

  // The window starts tipped back and stands up as it scrolls into view.
  const frame = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: frame, offset: ["start end", "start 0.3"] });
  const progress = useSpring(scrollYProgress, { stiffness: 120, damping: 26, mass: 0.4 });
  const rotateX = useTransform(progress, [0, 1], [26, 0]);
  const scale = useTransform(progress, [0, 1], [0.9, 1]);
  const glow = useTransform(progress, [0, 1], [0.2, 1]);

  return (
    <section className="later relative overflow-hidden py-24 md:py-36" id="tour">
      <div className="wrap">
        <Heading
          eyebrow="The app"
          title="Four screens. This is all of it you need on day one."
          lede={<>These are screenshots of the real app, checking the sample file that comes with it. It opens in your browser when you run <span className="chip-dark">pdq ui</span>.</>}
          center
        />

        <Reveal delay={0.1}>
          <div role="group" aria-label="Choose a screen to look at" className="mx-auto mt-10 flex w-fit max-w-full flex-wrap justify-center gap-1 rounded-xl border border-white/10 bg-white/[0.04] p-1">
            {SHOTS.map((s, i) => (
              <button
                key={s.id}
                type="button"
                aria-pressed={active === s.id}
                onClick={() => setActive(s.id)}
                className={cn("relative min-h-[44px] cursor-pointer rounded-lg px-3.5 text-[14.5px] font-medium transition-colors duration-200 sm:px-4", active === s.id ? "text-ink" : "text-fog hover:text-white")}
              >
                {active === s.id && <motion.span layoutId="tour-pill" className="absolute inset-0 rounded-lg bg-white" transition={{ type: "spring", stiffness: 380, damping: 32 }} />}
                <span className="relative"><span className="mr-2 font-mono text-[12px] opacity-60" aria-hidden>{i + 1}</span>{s.label}</span>
              </button>
            ))}
          </div>
        </Reveal>

        <div ref={frame} className="relative mx-auto mt-10 max-w-[1040px] [perspective:1600px] md:mt-14">
          <motion.div aria-hidden style={{ opacity: glow }} className="absolute -inset-x-20 -top-16 bottom-0 bg-[radial-gradient(ellipse_50%_55%_at_50%_30%,rgba(203,213,225,0.2),transparent)]" />
          <motion.div style={reduced ? undefined : { rotateX, scale, transformOrigin: "50% 100%" }} className="relative">
            <WindowFrame>
              <div className="relative aspect-[5/6] overflow-hidden bg-paper sm:aspect-[1280/820]">
                <AnimatePresence initial={false}>
                  <motion.img
                    key={shot.id}
                    src={shot.large}
                    srcSet={`${shot.small} 960w, ${shot.large} 1920w`}
                    sizes="(min-width: 1100px) 1040px, 94vw"
                    width={1920}
                    height={1230}
                    loading="lazy"
                    decoding="async"
                    alt={shot.alt}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.35 }}
                    className="absolute left-0 top-0 h-auto w-[215%] max-w-none sm:h-full sm:w-full sm:object-cover sm:object-top"
                  />
                </AnimatePresence>
              </div>
            </WindowFrame>
          </motion.div>
        </div>

        <div className="mx-auto mt-8 max-w-[640px] text-center" aria-live="polite">
          <AnimatePresence mode="wait" initial={false}>
            <motion.div key={shot.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.22 }}>
              <h3 className="font-display text-[24px] font-semibold tracking-[-0.01em]">{shot.title}</h3>
              <p className="mt-2 text-[16.5px] leading-relaxed text-fog">{shot.text}</p>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
}
