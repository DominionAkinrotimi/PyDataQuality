import { Component, Suspense, lazy, useEffect, useRef, useState, type ReactNode } from "react";
import { AnimatePresence, motion, useInView, useReducedMotion, type Variants } from "motion/react";
import { ArrowDown, MonitorCheck } from "lucide-react";
import { CopyCommand } from "@/components/ui";
import { HeroPoster } from "@/components/HeroPoster";
import { SAMPLE_VERDICT } from "@/lib/sheet";
import type { ScenePhase } from "@/three/HeroScene";

// The 3D code is a separate file, fetched only when it will actually be shown.
const HeroScene = lazy(() => import("@/three/HeroScene"));

/** True when this device should get the moving scene rather than the still picture. */
function canRun3d(): boolean {
  const nav = navigator as Navigator & { deviceMemory?: number; connection?: { saveData?: boolean } };
  if (nav.connection?.saveData) return false;
  if (nav.hardwareConcurrency !== undefined && nav.hardwareConcurrency < 4) return false;
  if (nav.deviceMemory !== undefined && nav.deviceMemory < 4) return false;
  // Phones keep the still picture: the scene would cost them battery and a slower first load.
  if (window.matchMedia("(max-width: 767px), (pointer: coarse) and (max-width: 1023px)").matches) return false;
  return "WebGL2RenderingContext" in window;
}

/** If the scene cannot start (no WebGL after all), the still picture simply stays. */
class SceneBoundary extends Component<{ onError: () => void; children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch() { this.props.onError(); }
  render() { return this.state.failed ? null : this.props.children; }
}

function useScene() {
  const reduced = useReducedMotion();
  const [wanted, setWanted] = useState(false);
  useEffect(() => {
    if (reduced || !canRun3d()) { setWanted(false); return; }
    // Wait until the page has loaded and the browser is idle, so the first screen is never held up.
    let idle = 0;
    let timer = 0;
    const start = () => {
      if (typeof window.requestIdleCallback === "function") idle = window.requestIdleCallback(() => setWanted(true), { timeout: 2500 });
      else timer = window.setTimeout(() => setWanted(true), 400);
    };
    if (document.readyState === "complete") start();
    else window.addEventListener("load", start, { once: true });
    return () => {
      window.removeEventListener("load", start);
      if (idle) window.cancelIdleCallback(idle);
      if (timer) clearTimeout(timer);
    };
  }, [reduced]);
  return wanted;
}

function usePageVisible() {
  const [visible, setVisible] = useState(true);
  useEffect(() => {
    const onChange = () => setVisible(document.visibilityState === "visible");
    document.addEventListener("visibilitychange", onChange);
    return () => document.removeEventListener("visibilitychange", onChange);
  }, []);
  return visible;
}

function Stage() {
  const stage = useRef<HTMLDivElement>(null);
  const wanted = useScene();
  const onScreen = useInView(stage, { margin: "80px" });
  const pageVisible = usePageVisible();
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);
  const [phase, setPhase] = useState<ScenePhase>("verdict");
  useEffect(() => { if (!wanted) { setReady(false); setPhase("verdict"); } }, [wanted]);

  return (
    <div ref={stage} className="relative mx-auto aspect-[5/4] w-full max-w-[720px] lg:aspect-auto lg:h-full lg:max-w-none">
      <p className="sr-only">
        Illustration: a sheet of spreadsheet cells is scanned from top to bottom. The cells with something wrong, such as a row
        that is a copy of the one above, two impossible ages and two dates in the future, lift out of the sheet and turn red or
        amber. The rest turn green. The verdict for the file reads: {SAMPLE_VERDICT.headline}, {SAMPLE_VERDICT.summary} in {SAMPLE_VERDICT.file}.
      </p>
      <div aria-hidden className="absolute inset-0 lg:-inset-x-10 lg:-inset-y-6">
        <div className="absolute left-1/2 top-1/2 h-[70%] w-[70%] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(closest-side,rgba(255,255,255,0.07),transparent)]" />
        <div className="absolute inset-0 transition-opacity duration-700" style={{ opacity: ready ? 0 : 1 }}>
          <HeroPoster />
        </div>
        {wanted && !failed && (
          <div className="absolute inset-0 transition-opacity duration-700" style={{ opacity: ready ? 1 : 0 }}>
            <SceneBoundary onError={() => { setFailed(true); setReady(false); setPhase("verdict"); }}>
              <Suspense fallback={null}>
                <HeroScene
                  active={onScreen && pageVisible}
                  onReady={() => setReady(true)}
                  onPhase={setPhase}
                  onUnsupported={() => { setFailed(true); setReady(false); setPhase("verdict"); }}
                />
              </Suspense>
            </SceneBoundary>
          </div>
        )}

        {/* The verdict. The file name stays put; the panel under it changes as the scan runs. */}
        <div className="absolute bottom-[3%] left-[2%] w-[min(330px,86%)] lg:bottom-[8%] lg:left-[4%]">
          <div className="rounded-2xl bg-white p-1.5 text-ink shadow-sheet">
            <div className="flex items-center justify-between gap-3 px-2.5 pb-1.5 pt-1 font-mono text-[11px] text-muted">
              <span className="truncate">{SAMPLE_VERDICT.file}</span>
              <span className="shrink-0">{SAMPLE_VERDICT.size}</span>
            </div>
            <div className="relative h-[70px] overflow-hidden rounded-[10px] bg-soft2">
              <AnimatePresence initial={false}>
                {phase === "verdict" ? (
                  <motion.div key="verdict" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.3 }} className="absolute inset-0 flex flex-col justify-center px-3.5">
                    <span className="flex items-center gap-2.5 font-display text-[18px] font-semibold leading-tight">
                      <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-crit-ink" />
                      {SAMPLE_VERDICT.headline}
                    </span>
                    <span className="mt-1 truncate text-[12.5px] text-slate2">{SAMPLE_VERDICT.summary}</span>
                  </motion.div>
                ) : (
                  <motion.div key="checking" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.3 }} className="absolute inset-0 flex flex-col justify-center px-3.5">
                    <span className="font-display text-[18px] font-semibold leading-tight">Checking</span>
                    <span className="mt-3 block h-[3px] overflow-hidden rounded-full bg-line2">
                      <motion.span className="block h-full w-1/3 rounded-full bg-ink" animate={{ x: ["-100%", "300%"] }} transition={{ duration: 1.3, repeat: Infinity, ease: "easeInOut" }} />
                    </span>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

const sequence: Variants = { hidden: {}, show: { transition: { staggerChildren: 0.09, delayChildren: 0.05 } } };
const rise: Variants = {
  hidden: { opacity: 0, y: 18, filter: "blur(6px)" },
  show: { opacity: 1, y: 0, filter: "blur(0px)", transition: { duration: 0.7, ease: [0.21, 0.6, 0.35, 1] } },
};

// The headline is the largest thing on the first screen, so it is painted at once and only slides.
const headline: Variants = { hidden: { y: 18 }, show: { y: 0, transition: { duration: 0.7, ease: [0.21, 0.6, 0.35, 1] } } };

export function Hero() {
  return (
    <section id="top" className="relative overflow-hidden">
      <div aria-hidden className="grid-floor absolute inset-0 [mask-image:radial-gradient(ellipse_70%_60%_at_65%_40%,black,transparent)]" />
      <div aria-hidden className="absolute inset-x-0 top-0 h-[520px] bg-[radial-gradient(ellipse_60%_100%_at_70%_0%,rgba(148,163,184,0.16),transparent)]" />

      <div className="wrap relative grid items-center gap-2 pb-10 pt-28 lg:min-h-[100svh] lg:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)] lg:gap-4 lg:pb-20 lg:pt-24">
        <motion.div variants={sequence} initial="hidden" animate="show" className="relative z-10 max-w-[600px]">
          <motion.p variants={rise} className="eyebrow mb-6 flex items-center gap-2.5">
            <span className="h-px w-8 bg-white/30" aria-hidden />
            Free and open source
          </motion.p>
          <motion.h1 variants={headline} className="font-display text-[44px] font-semibold leading-[0.98] tracking-[-0.015em] sm:text-[60px] lg:text-[76px]">
            Know whether a data file is safe to use.
          </motion.h1>
          <motion.p variants={rise} className="lede mt-7 max-w-[520px]">
            Drop in a spreadsheet or CSV. Get a plain answer in seconds, and the rows that are wrong.
          </motion.p>
          <motion.div variants={rise} className="mt-9 flex flex-wrap items-center gap-3">
            <CopyCommand command="pip install pydataquality" />
            <a href="#how" className="btn-ghost min-h-[48px] border-transparent bg-transparent">
              See how it works <ArrowDown size={16} aria-hidden />
            </a>
          </motion.div>
          <motion.p variants={rise} className="mt-7 flex items-center gap-2.5 text-[14px] text-fog">
            <MonitorCheck size={17} className="shrink-0 text-white/70" aria-hidden />
            Works on a single file. Runs on your computer. Nothing is uploaded.
          </motion.p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1.1, delay: 0.25, ease: [0.21, 0.6, 0.35, 1] }}
          className="relative lg:h-[min(640px,72vh)]"
        >
          <Stage />
        </motion.div>
      </div>
    </section>
  );
}
