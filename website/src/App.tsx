import { Suspense, useState, type ReactNode } from "react";
import { MotionConfig, motion, useMotionValueEvent, useScroll } from "motion/react";
import { ShieldCheck } from "lucide-react";
import { Hero } from "./sections/Hero";
import { Finds } from "./sections/Finds";
import { Answers, Engine, FirstFile, Outcomes } from "./sections/Solution";
import { Tour } from "./sections/Tour";
import { Paper } from "./sections/Paper";
import { CallToAction, Fit, GetStarted, Questions, Ways } from "./sections/Closing";
import { LINKS } from "./lib/links";
import { cn } from "./lib/utils";
import { Wake } from "./lib/wake";

function GithubMark() {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden>
      <path d="M12 .5a11.5 11.5 0 0 0-3.64 22.41c.58.1.79-.25.79-.56v-2c-3.2.7-3.88-1.36-3.88-1.36-.53-1.33-1.28-1.69-1.28-1.69-1.05-.71.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.76 2.7 1.25 3.36.96.1-.75.4-1.25.73-1.54-2.56-.29-5.25-1.28-5.25-5.69 0-1.26.45-2.29 1.19-3.09-.12-.3-.52-1.47.11-3.06 0 0 .97-.31 3.18 1.18a11 11 0 0 1 5.78 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.06.74.8 1.19 1.83 1.19 3.09 0 4.42-2.7 5.4-5.27 5.68.41.36.78 1.06.78 2.14v3.17c0 .31.21.67.8.56A11.5 11.5 0 0 0 12 .5Z" />
    </svg>
  );
}

/** The same mark as the app, with the colours swapped for the dark page. */
function Logo() {
  return (
    <a href="#top" className="flex min-h-[44px] items-center gap-2.5 font-display text-[17px] font-semibold tracking-[-0.005em]">
      <span className="grid h-8 w-8 place-items-center rounded-lg bg-white text-ink" aria-hidden><ShieldCheck size={18} /></span>
      PyDataQuality
    </a>
  );
}

function Nav() {
  const { scrollY } = useScroll();
  const [scrolled, setScrolled] = useState(false);
  useMotionValueEvent(scrollY, "change", (y) => setScrolled(y > 24));
  return (
    <motion.header initial={{ y: -24, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ duration: 0.6, ease: "easeOut" }} className="fixed inset-x-0 top-0 z-50 px-2 pt-2 md:px-3 md:pt-3">
      <div
        className={cn(
          "mx-auto flex h-14 max-w-site items-center justify-between gap-3 rounded-2xl border px-3 transition-all duration-300 md:px-5",
          scrolled ? "border-white/10 bg-ink/90 shadow-lift backdrop-blur-xl" : "border-transparent bg-transparent",
        )}
      >
        <Logo />
        <nav aria-label="Main" className="hidden items-center gap-7 text-[14.5px] text-fog lg:flex">
          <a className="transition-colors hover:text-white" href="#answer">What you get</a>
          <a className="transition-colors hover:text-white" href="#tour">The app</a>
          <a className="transition-colors hover:text-white" href="#inside">How it works</a>
          <a className="transition-colors hover:text-white" href="#start">Install</a>
          <a className="transition-colors hover:text-white" href="#faq">Questions</a>
        </nav>
        <div className="flex items-center gap-2">
          <a href={LINKS.github} className="btn-ghost !min-h-[44px] !px-3.5 text-[14px]" aria-label="PyDataQuality on GitHub">
            <GithubMark /> <span className="hidden sm:inline">GitHub</span>
          </a>
          <a href="#start" className="btn-white !min-h-[44px] !px-4 text-[14px]">Get started</a>
        </div>
      </div>
    </motion.header>
  );
}

function Footer() {
  return (
    <footer className="later">
      <div className="wrap flex flex-col gap-6 py-12 md:flex-row md:items-center md:justify-between">
        <div>
          <Logo />
          <p className="mt-2 max-w-sm text-[14.5px] text-fog">Check a CSV or Excel file before you use it. Free, open source, and it runs on your own computer.</p>
        </div>
        <nav aria-label="Footer" className="flex flex-wrap gap-x-7 text-[14.5px] text-fog">
          {([["Quickstart", LINKS.quickstart], ["User guide", LINKS.guide], ["Security", LINKS.security], ["PyPI", LINKS.pypi], ["GitHub", LINKS.github]] as const).map(([label, href]) => (
            <a key={label} className="inline-flex min-h-[44px] items-center transition-colors hover:text-white" href={href}>{label}</a>
          ))}
        </nav>
      </div>
      <div className="wrap border-t border-white/[0.08] py-5 font-mono text-[12px] text-haze">MIT licence · Built by Dominion Akinrotimi</div>
    </footer>
  );
}

/**
 * The whole page is written into the HTML when the site is built, so it can be read without
 * JavaScript and by search engines. Each section below the first screen sits in its own Suspense
 * boundary and is woken up in turn (see lib/wake.ts) instead of all in one long block.
 */
export const STAGES = 13; // the twelve sections below, and the footer

const LATER: ReactNode[] = [
  <Outcomes />, <FirstFile />, <Finds />, <Tour />, <Paper />, <Engine />, <Answers />, <GetStarted />, <Ways />, <Fit />, <Questions />, <CallToAction />,
];

export function App() {
  return (
    <MotionConfig reducedMotion="user">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[60] focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:text-ink">
        Skip to content
      </a>
      <Nav />
      <main id="main">
        <Hero />
        {LATER.map((section, i) => <Suspense key={i} fallback={null}><Wake index={i}>{section}</Wake></Suspense>)}
      </main>
      <Suspense fallback={null}><Wake index={LATER.length}><Footer /></Wake></Suspense>
    </MotionConfig>
  );
}
