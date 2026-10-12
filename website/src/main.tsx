import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import { MotionConfig, motion, useMotionValueEvent, useScroll } from "motion/react";
import "./index.css";
import { Hero, LINKS } from "./sections/Hero";
import { CallToAction, Catches, Features, Fit, HowItWorks, PlainLanguage, Problem, Questions, Ways } from "./sections/Body";
import { cn } from "./lib/utils";

function GithubMark() {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden>
      <path d="M12 .5a11.5 11.5 0 0 0-3.64 22.41c.58.1.79-.25.79-.56v-2c-3.2.7-3.88-1.36-3.88-1.36-.53-1.33-1.28-1.69-1.28-1.69-1.05-.71.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.76 2.7 1.25 3.36.96.1-.75.4-1.25.73-1.54-2.56-.29-5.25-1.28-5.25-5.69 0-1.26.45-2.29 1.19-3.09-.12-.3-.52-1.47.11-3.06 0 0 .97-.31 3.18 1.18a11 11 0 0 1 5.78 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.06.74.8 1.19 1.83 1.19 3.09 0 4.42-2.7 5.4-5.27 5.68.41.36.78 1.06.78 2.14v3.17c0 .31.21.67.8.56A11.5 11.5 0 0 0 12 .5Z" />
    </svg>
  );
}

function Logo() {
  return (
    <a href="#top" className="flex items-center gap-2.5 font-display text-[17px] font-semibold tracking-[-0.02em]">
      <span className="grid h-8 w-8 place-items-center rounded-lg bg-ink" aria-hidden>
        <svg viewBox="0 0 32 32" width="18" height="18"><path d="M8 16.5l5 5L24 10.5" fill="none" stroke="#fff" strokeWidth="3.4" strokeLinecap="round" strokeLinejoin="round" /></svg>
      </span>
      PyDataQuality
    </a>
  );
}

function Nav() {
  const { scrollY } = useScroll();
  const [scrolled, setScrolled] = useState(false);
  useMotionValueEvent(scrollY, "change", (y) => setScrolled(y > 24));
  return (
    <motion.header
      initial={{ y: -24, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="fixed inset-x-0 top-0 z-50 px-3 pt-3"
    >
      <div
        className={cn(
          "mx-auto flex h-14 max-w-site items-center justify-between gap-4 rounded-2xl border px-4 transition-all duration-300 md:px-5",
          scrolled ? "border-line bg-white/85 shadow-[0_8px_30px_-12px_rgba(9,10,15,0.18)] backdrop-blur-md" : "border-transparent bg-transparent",
        )}
      >
        <Logo />
        <nav aria-label="Main" className="hidden items-center gap-7 text-[14.5px] text-muted md:flex">
          <a className="transition-colors hover:text-ink" href="#features">What you get</a>
          <a className="transition-colors hover:text-ink" href="#how">How it works</a>
          <a className="transition-colors hover:text-ink" href="#use">Ways to use it</a>
          <a className="transition-colors hover:text-ink" href="#faq">Questions</a>
        </nav>
        <div className="flex items-center gap-2">
          <a href={LINKS.github} className="btn-light !min-h-[40px] !px-3.5 text-[14px]" aria-label="PyDataQuality on GitHub">
            <GithubMark /> <span className="hidden sm:inline">GitHub</span>
          </a>
          <a href={LINKS.quickstart} className="btn-dark !min-h-[40px] !px-4 text-[14px]">Get started</a>
        </div>
      </div>
    </motion.header>
  );
}

function Footer() {
  return (
    <footer className="border-t border-line">
      <div className="wrap flex flex-col gap-6 py-10 md:flex-row md:items-center md:justify-between">
        <div>
          <Logo />
          <p className="mt-3 max-w-sm text-[14px] text-muted">Know whether a data file is safe to use. Free, open source, and it runs on your own computer.</p>
        </div>
        <nav aria-label="Footer" className="flex flex-wrap gap-x-7 gap-y-2 text-[14px] text-muted">
          <a className="hover:text-ink" href={LINKS.quickstart}>Quickstart</a>
          <a className="hover:text-ink" href={LINKS.guide}>User guide</a>
          <a className="hover:text-ink" href={LINKS.security}>Security</a>
          <a className="hover:text-ink" href={LINKS.pypi}>PyPI</a>
          <a className="hover:text-ink" href={LINKS.github}>GitHub</a>
        </nav>
      </div>
      <div className="wrap border-t border-line py-5 font-mono text-[12px] text-muted">MIT licence · Built by Dominion Akinrotimi</div>
    </footer>
  );
}

function App() {
  return (
    <MotionConfig reducedMotion="user">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[60] focus:rounded-lg focus:bg-ink focus:px-4 focus:py-2 focus:text-white">
        Skip to content
      </a>
      <Nav />
      <main id="main">
        <Hero />
        <Catches />
        <Problem />
        <Features />
        <PlainLanguage />
        <HowItWorks />
        <Ways />
        <Fit />
        <Questions />
        <CallToAction />
      </main>
      <Footer />
    </MotionConfig>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
