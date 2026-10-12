import { StrictMode, type ReactNode } from "react";
import { createRoot } from "react-dom/client";
import { ShieldCheck } from "lucide-react";
import "./index.css";
import { api } from "./api";
import { href, useLoad, useRoute } from "./ui";
import { Check } from "./screens/Check";
import { Result } from "./screens/Result";
import { Rows } from "./screens/Rows";
import { Save } from "./screens/Save";
import { Datasets } from "./screens/Datasets";
import { Dataset } from "./screens/Dataset";
import { Help } from "./screens/Help";

function NavLink({ to, active, children }: { to: string; active: boolean; children: ReactNode }) {
  return (
    <a
      href={to}
      aria-current={active ? "page" : undefined}
      className={`rounded px-3 py-1.5 text-base2 transition-colors ${
        active ? "bg-soft2 font-medium text-ink" : "text-muted hover:text-ink"
      }`}
    >
      {children}
    </a>
  );
}

function Shell({ section, children }: { section: string; children: ReactNode }) {
  const state = useLoad(api.state, []);
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-20 border-b border-line bg-white">
        <div className="mx-auto flex h-14 max-w-[1280px] items-center justify-between gap-4 px-4 md:px-8">
          <a href={href()} className="flex items-center gap-2 text-h3 text-ink">
            <span className="grid h-7 w-7 place-items-center rounded bg-ink text-white" aria-hidden>
              <ShieldCheck size={16} />
            </span>
            PyDataQuality
          </a>
          <nav className="flex items-center gap-1" aria-label="Main">
            <NavLink to={href()} active={section === "check"}>Check</NavLink>
            <NavLink to={href("datasets")} active={section === "datasets"}>My datasets</NavLink>
            <NavLink to={href("help")} active={section === "help"}>Help</NavLink>
          </nav>
        </div>
      </header>
      <main className="flex-1">{children}</main>
      <footer className="border-t border-line bg-white">
        <div className="mx-auto flex max-w-[1280px] flex-wrap items-center justify-between gap-2 px-4 py-3 text-sm2 text-muted md:px-8">
          <span>
            <span className="font-mono text-ink">PyDataQuality {state.data ? `v${state.data.version}` : ""}</span>
            {" · "}Runs on this computer. Nothing is uploaded.
          </span>
          <a className="underline underline-offset-2 hover:text-ink" href={href("help")}>
            Where your data goes
          </a>
        </div>
      </footer>
    </div>
  );
}

function App() {
  const [screen, a, b] = useRoute();
  switch (screen) {
    case "result":
      return <Shell section="check"><Result id={a ?? ""} /></Shell>;
    case "rows":
      return <Shell section="check"><Rows id={a ?? ""} finding={b ?? "all"} /></Shell>;
    case "save":
      return <Shell section="check"><Save id={a ?? ""} /></Shell>;
    case "datasets":
      return <Shell section="datasets"><Datasets /></Shell>;
    case "dataset":
      return <Shell section="datasets"><Dataset datasetKey={a ?? ""} /></Shell>;
    case "help":
      return <Shell section="help"><Help /></Shell>;
    default:
      return <Shell section="check"><Check /></Shell>;
  }
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
