// Shared pieces used by every screen.

import { useCallback, useEffect, useState, type ReactNode } from "react";
import { CircleCheck, CircleX, Copy, Check, TriangleAlert, Info } from "lucide-react";
import type { Level, Verdict } from "./api";

export const fmt = (n: number) => n.toLocaleString("en-US");
export const plural = (n: number, one: string, many = one + "s") => `${fmt(n)} ${n === 1 ? one : many}`;

export function when(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  const today = new Date();
  const time = date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  if (date.toDateString() === today.toDateString()) return `today ${time}`;
  return date.toLocaleDateString([], { day: "numeric", month: "short", year: "numeric" });
}

// ---------------------------------------------------------------- routing
export function useRoute(): string[] {
  const read = () => window.location.hash.replace(/^#\/?/, "").split("/").filter(Boolean).map(decodeURIComponent);
  const [parts, setParts] = useState<string[]>(read);
  useEffect(() => {
    const onChange = () => {
      setParts(read());
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return parts;
}

export const go = (...parts: string[]) => {
  window.location.hash = "/" + parts.map(encodeURIComponent).join("/");
};
export const href = (...parts: string[]) => "#/" + parts.map(encodeURIComponent).join("/");

// ------------------------------------------------------------ data loading
export function useLoad<T>(load: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const run = useCallback(() => {
    setLoading(true);
    setError(null);
    load()
      .then(setData)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  useEffect(run, [run]);
  return { data, error, loading, reload: run, setData };
}

// -------------------------------------------------------------- components
const TONES = {
  crit: "bg-crit-bg border-crit-line text-crit-ink",
  warn: "bg-warn-bg border-warn-line text-warn-ink",
  ok: "bg-ok-bg border-ok-line text-ok-ink",
  info: "bg-info-bg border-info-line text-info-ink",
  plain: "bg-soft2 border-line text-slate2",
} as const;
export type Tone = keyof typeof TONES;

export const levelTone = (level: Level): Tone => (level === "problem" ? "crit" : level === "warning" ? "warn" : "plain");
export const verdictTone = (verdict: Verdict): Tone => (verdict === "problems" ? "crit" : verdict === "warnings" ? "warn" : "ok");

export function Badge({ tone = "plain", children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span className={`inline-flex items-center gap-1 whitespace-nowrap rounded-[4px] border px-2 py-0.5 text-[11px] font-semibold tracking-[0.04em] ${TONES[tone]}`}>
      {children}
    </span>
  );
}

export function VerdictIcon({ verdict, size = 16 }: { verdict: Verdict; size?: number }) {
  if (verdict === "problems") return <CircleX size={size} aria-hidden />;
  if (verdict === "warnings") return <TriangleAlert size={size} aria-hidden />;
  return <CircleCheck size={size} aria-hidden />;
}

/** Verdict as an icon plus words. Colour is never the only signal. */
export function VerdictBadge({ verdict, headline }: { verdict: Verdict; headline: string }) {
  return (
    <Badge tone={verdictTone(verdict)}>
      <VerdictIcon verdict={verdict} size={13} />
      {sentence(headline)}
    </Badge>
  );
}

export const sentence = (text: string) => text.charAt(0) + text.slice(1).toLowerCase();

export function Notice({ tone = "info", children }: { tone?: Tone; children: ReactNode }) {
  const Icon = tone === "crit" ? CircleX : tone === "warn" ? TriangleAlert : tone === "ok" ? CircleCheck : Info;
  return (
    <div role={tone === "crit" ? "alert" : "status"} className={`flex items-start gap-2.5 rounded-lg border px-4 py-3 ${TONES[tone]}`}>
      <Icon size={18} className="mt-0.5 shrink-0" aria-hidden />
      <div className="min-w-0 text-base2 text-ink">{children}</div>
    </div>
  );
}

export function Loading({ label = "Loading" }: { label?: string }) {
  return (
    <p className="flex items-center gap-2 py-10 text-muted" role="status">
      <span className="h-2 w-2 animate-pulse rounded-full bg-ink" aria-hidden />
      {label}…
    </p>
  );
}

export function Page({ children, wide = false }: { children: ReactNode; wide?: boolean }) {
  return <div className={`mx-auto w-full px-4 py-8 md:px-8 ${wide ? "max-w-[1280px]" : "max-w-[960px]"}`}>{children}</div>;
}

export function CopyButton({ text, label = "Copy" }: { text: string; label?: string }) {
  const [state, setState] = useState<"idle" | "done" | "failed">("idle");
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setState("done");
    } catch {
      setState("failed");
    }
    window.setTimeout(() => setState("idle"), 2000);
  };
  return (
    <button type="button" className="btn-outline" onClick={copy}>
      {state === "done" ? <Check size={16} aria-hidden /> : <Copy size={16} aria-hidden />}
      {state === "done" ? "Copied" : state === "failed" ? "Select and copy by hand" : label}
    </button>
  );
}

/** Marks the column name inside a finding sentence so it reads as data. */
export function Message({ text, column }: { text: string; column: string }) {
  const at = column && column !== "(whole file)" ? text.indexOf(column) : -1;
  if (at < 0) return <>{text}</>;
  return (
    <>
      {text.slice(0, at)}
      <span className="chip mx-0.5 align-baseline">{column}</span>
      {text.slice(at + column.length)}
    </>
  );
}
