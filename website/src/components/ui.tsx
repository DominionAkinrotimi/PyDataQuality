import { useRef, useState, type PointerEvent, type ReactNode } from "react";
import { motion, useMotionTemplate, useMotionValue, useReducedMotion, useSpring } from "motion/react";
import { Check, Copy } from "lucide-react";
import { BlurFade } from "@/components/magicui/blur-fade";
import { cn } from "@/lib/utils";

export function Reveal({ children, delay = 0, className }: { children: ReactNode; delay?: number; className?: string }) {
  return (
    <BlurFade inView delay={delay} className={className}>
      {children}
    </BlurFade>
  );
}

export function Heading({ eyebrow, title, lede, center = false }: { eyebrow: string; title: ReactNode; lede?: ReactNode; center?: boolean }) {
  return (
    <Reveal className={cn("max-w-[760px]", center && "mx-auto text-center")}>
      <p className="eyebrow mb-4">{eyebrow}</p>
      <h2 className="h2">{title}</h2>
      {lede && <p className="lede mt-5">{lede}</p>}
    </Reveal>
  );
}

export function CopyCommand({ command, className }: { command: string; className?: string }) {
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
        "group inline-flex min-h-[48px] max-w-full cursor-pointer items-center gap-3 rounded-lg border border-white/15 bg-white/[0.05] pl-4 pr-2 font-mono text-[14px] text-white transition-colors duration-200 hover:border-white/30 hover:bg-white/10",
        className,
      )}
    >
      <span className="text-haze" aria-hidden>$</span>
      <span className="select-all truncate">{command}</span>
      <span className="ml-1 grid h-8 w-8 shrink-0 place-items-center rounded-md bg-white/10 text-white/80 transition-colors group-hover:bg-white group-hover:text-ink" aria-hidden>
        {copied ? <Check size={15} /> : <Copy size={15} />}
      </span>
      <span className="sr-only" role="status">{copied ? "Copied" : ""}</span>
    </button>
  );
}

/**
 * A card that tilts toward the pointer, with a soft light that follows it. Written for this site
 * after Aceternity UI's "3D Card Effect". Still under reduced motion and on touch screens.
 */
export function TiltCard({ children, className }: { children: ReactNode; className?: string }) {
  const reduced = useReducedMotion();
  const ref = useRef<HTMLDivElement>(null);
  const rx = useSpring(0, { stiffness: 220, damping: 22 });
  const ry = useSpring(0, { stiffness: 220, damping: 22 });
  const gx = useMotionValue(50);
  const gy = useMotionValue(0);
  const light = useMotionTemplate`radial-gradient(420px circle at ${gx}% ${gy}%, rgba(255,255,255,0.09), transparent 62%)`;

  const onMove = (event: PointerEvent<HTMLDivElement>) => {
    if (reduced || event.pointerType !== "mouse" || !ref.current) return;
    const box = ref.current.getBoundingClientRect();
    const px = (event.clientX - box.left) / box.width;
    const py = (event.clientY - box.top) / box.height;
    ry.set((px - 0.5) * 9);
    rx.set((0.5 - py) * 9);
    gx.set(px * 100);
    gy.set(py * 100);
  };
  const onLeave = () => { rx.set(0); ry.set(0); };

  return (
    <div className="h-full [perspective:1100px]">
      <motion.div
        ref={ref}
        onPointerMove={onMove}
        onPointerLeave={onLeave}
        style={{ rotateX: rx, rotateY: ry, transformStyle: "preserve-3d" }}
        className={cn("card group relative h-full overflow-hidden", className)}
      >
        <motion.div aria-hidden className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100" style={{ background: light }} />
        <div className="relative h-full">{children}</div>
      </motion.div>
    </div>
  );
}

/** A plain browser window around a screenshot of the app. The address is the one the app really uses. */
export function WindowFrame({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn("overflow-hidden rounded-xl border border-white/15 bg-white shadow-sheet md:rounded-2xl", className)}>
      <div className="flex h-9 items-center gap-3 border-b border-line bg-soft2 px-3 md:h-10 md:px-4" aria-hidden>
        <span className="flex gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-line2" />
          <span className="h-2.5 w-2.5 rounded-full bg-line2" />
          <span className="h-2.5 w-2.5 rounded-full bg-line2" />
        </span>
        <span className="mx-auto flex h-6 w-full max-w-[340px] items-center justify-center rounded-md border border-line bg-white font-mono text-[11px] text-muted">
          127.0.0.1:8765
        </span>
        <span className="w-[42px]" />
      </div>
      {children}
    </div>
  );
}
