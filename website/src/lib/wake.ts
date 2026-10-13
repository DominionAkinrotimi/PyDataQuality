/**
 * The built page arrives as finished HTML. React then has to "wake up" each section so its buttons
 * and animations work. Doing that for the whole page at once blocks a slow phone, so the sections
 * below the first screen are woken one at a time while the browser is idle. Any touch, key press
 * or scroll wakes whatever is left. Until a section is woken its text and pictures are still there.
 */
interface Gate { open: boolean; promise: Promise<void>; release: () => void }

const gates: Gate[] = [];
let gated = false;

function gate(index: number): Gate {
  if (!gates[index]) {
    let release = () => {};
    const promise = new Promise<void>((resolve) => { release = resolve; });
    const entry: Gate = { open: false, promise, release: () => { entry.open = true; release(); } };
    gates[index] = entry;
  }
  return gates[index];
}

/** Called once, just before the prerendered page is woken. */
export function wakeInStages(total: number) {
  gated = true;
  for (let i = 0; i < total; i++) gate(i);
  const all = () => gates.forEach((entry) => entry.release());
  (["pointerdown", "keydown", "wheel", "touchstart", "scroll"] as const).forEach((name) =>
    window.addEventListener(name, all, { once: true, passive: true, capture: true }),
  );
  let next = 0;
  const step = () => {
    if (next >= gates.length) return;
    gates[next++].release();
    if (typeof window.requestIdleCallback === "function") window.requestIdleCallback(step, { timeout: 800 });
    else window.setTimeout(step, 150);
  };
  window.setTimeout(step, 300);
}

/** Holds its children as plain HTML until its turn comes. Must sit inside a Suspense boundary. */
export function Wake({ index, children }: { index: number; children: React.ReactNode }) {
  if (gated && !gate(index).open) throw gate(index).promise;
  return children;
}
