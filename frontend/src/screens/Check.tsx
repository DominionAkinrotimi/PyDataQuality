// Screen 1: choose a file to check.

import { useRef, useState, type DragEvent } from "react";
import { CloudUpload, FlaskConical, ShieldCheck, Table2 } from "lucide-react";
import { api, isSheetChoice, type CheckResult, type SheetChoice } from "../api";
import { Loading, Notice, Page, VerdictBadge, fmt, go, href, useLoad, when } from "../ui";

const ACCEPTED = [".csv", ".tsv", ".txt", ".xlsx", ".xlsm", ".xls", ".json", ".parquet"];

const LOOKS_FOR = [
  "Rows that are exact copies, and IDs that repeat",
  "Impossible values, such as an age of 999",
  "Dates in the future, and mixed date formats",
  "Email addresses that are not email addresses",
  "One value spelled several ways",
  "Numbers stored as text",
  "Columns that are empty or mostly empty",
];

function unsupported(file: File): string | null {
  const dot = file.name.lastIndexOf(".");
  const extension = dot >= 0 ? file.name.slice(dot).toLowerCase() : "";
  if (ACCEPTED.includes(extension)) return null;
  const kind = extension ? `a ${extension} file` : "a file with no extension";
  return `This looks like ${kind}. PyDataQuality reads CSV, Excel, JSON and Parquet files.`;
}

export function Check() {
  const state = useLoad(api.state, []);
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [over, setOver] = useState(false);
  const [sheets, setSheets] = useState<SheetChoice | null>(null);
  const [sheet, setSheet] = useState("");

  const finish = (outcome: CheckResult | SheetChoice) => {
    if (isSheetChoice(outcome)) {
      setSheets(outcome);
      setSheet(outcome.sheets[0] ?? "");
    } else {
      go("result", outcome.id);
    }
  };

  const run = async (label: string, work: () => Promise<CheckResult | SheetChoice>) => {
    setBusy(label);
    setError(null);
    setSheets(null);
    try {
      finish(await work());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(null);
    }
  };

  const choose = (file: File | undefined) => {
    if (!file || busy) return;
    const problem = unsupported(file);
    if (problem) {
      setError(problem);
      setSheets(null);
      return;
    }
    const limit = state.data?.max_mb ?? 300;
    if (file.size > limit * 1024 * 1024) {
      setError(`This file is larger than ${limit} MB. Use the pdq check command for big files.`);
      return;
    }
    void run(`Checking ${file.name}`, () => api.check(file));
  };

  const onDrop = (event: DragEvent) => {
    event.preventDefault();
    setOver(false);
    choose(event.dataTransfer.files[0]);
  };

  return (
    <Page wide>
      <div className="grid items-start gap-8 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div className="flex min-w-0 flex-col gap-5">
          <div>
            <p className="mb-2 flex items-center gap-2 font-mono text-[12px] text-muted">
              <span className="h-2 w-2 rounded-full bg-ink" aria-hidden />
              RUNS ON THIS COMPUTER / UP TO {state.data?.max_mb ?? 300} MB
            </p>
            <h1 className="text-h1 md:text-display">Is this file safe to use?</h1>
            <p className="mt-2 max-w-2xl text-h2 font-normal text-muted">
              Drop in a spreadsheet or CSV. You get a plain answer in a few seconds.
            </p>
          </div>

          <div
            role="button"
            tabIndex={0}
            aria-label="Choose a file to check"
            aria-busy={busy !== null}
            onClick={() => !busy && input.current?.click()}
            onKeyDown={(e) => {
              if ((e.key === "Enter" || e.key === " ") && !busy) {
                e.preventDefault();
                input.current?.click();
              }
            }}
            onDragOver={(e) => {
              e.preventDefault();
              setOver(true);
            }}
            onDragLeave={() => setOver(false)}
            onDrop={onDrop}
            className={`rounded-xl border-2 border-dashed bg-white px-6 py-12 text-center transition-colors ${
              over ? "border-ink bg-soft" : "border-line2"
            } ${busy ? "cursor-progress" : "cursor-pointer hover:border-ink"}`}
          >
            <input
              ref={input}
              type="file"
              hidden
              accept={ACCEPTED.join(",")}
              onChange={(e) => {
                choose(e.target.files?.[0]);
                e.target.value = "";
              }}
            />
            {busy ? (
              <div role="status">
                <p className="text-h3">{busy}…</p>
                <div className="mx-auto mt-4 h-1 w-48 overflow-hidden rounded bg-soft2">
                  <div className="h-full w-1/2 animate-pulse rounded bg-ink" />
                </div>
              </div>
            ) : (
              <>
                <span className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-full bg-soft2" aria-hidden>
                  <CloudUpload size={26} />
                </span>
                <p className="text-h3">Drop a file here, or click to choose one.</p>
                <p className="mt-1 text-muted">CSV, Excel, JSON or Parquet.</p>
                <div className="mt-4 flex flex-wrap justify-center gap-2">
                  {[".csv", ".xlsx", ".json", ".parquet"].map((extension) => (
                    <span key={extension} className="chip">{extension}</span>
                  ))}
                </div>
              </>
            )}
          </div>

          {error && <Notice tone="crit">{error}</Notice>}

          {sheets && (
            <div className="card flex flex-col gap-3 p-4 sm:flex-row sm:items-end sm:justify-between">
              <div className="flex items-start gap-3">
                <span className="grid h-10 w-10 shrink-0 place-items-center rounded bg-soft2" aria-hidden>
                  <Table2 size={20} />
                </span>
                <div>
                  <p className="caps">{sheets.file} has {sheets.sheets.length} sheets</p>
                  <label htmlFor="sheet" className="text-base2 font-medium">Which sheet should be checked?</label>
                </div>
              </div>
              <div className="flex gap-2">
                <select id="sheet" className="input min-w-[200px] font-mono" value={sheet} onChange={(e) => setSheet(e.target.value)}>
                  {sheets.sheets.map((name) => (
                    <option key={name} value={name}>{name}</option>
                  ))}
                </select>
                <button
                  type="button"
                  className="btn-primary"
                  disabled={busy !== null}
                  onClick={() => void run(`Checking ${sheets.file}`, () => api.checkSheet(sheets.upload, sheet))}
                >
                  Check
                </button>
              </div>
            </div>
          )}

          <div className="flex items-start gap-2.5 rounded-lg bg-soft2 px-4 py-3">
            <ShieldCheck size={20} className="mt-0.5 shrink-0" aria-hidden />
            <div>
              <p className="font-medium">The file stays on this computer. Nothing is uploaded to the internet.</p>
              <p className="mt-0.5 text-sm2 text-muted">
                It is read by the PyDataQuality program running on your machine and then removed from its temporary folder.
              </p>
            </div>
          </div>

          <button
            type="button"
            disabled={busy !== null}
            onClick={() => void run("Checking the sample file", api.sample)}
            className="inline-flex items-center gap-1.5 self-start font-medium underline decoration-1 underline-offset-4 hover:text-muted disabled:opacity-50"
          >
            <FlaskConical size={17} aria-hidden />
            No file to hand? Try it with a sample messy file
          </button>
        </div>

        <aside className="flex flex-col gap-4">
          <div className="card p-5">
            <p className="caps mb-2">What it looks for</p>
            <ul className="flex flex-col gap-1.5">
              {LOOKS_FOR.map((item) => (
                <li key={item} className="flex gap-2">
                  <span className="mt-[9px] h-1 w-1 shrink-0 rounded-full bg-ink" aria-hidden />
                  {item}
                </li>
              ))}
            </ul>
            <p className="mt-3 text-sm2 text-muted">
              Once you save a file as normal, the next one is also compared with it: missing columns, new values, far fewer rows and more.
            </p>
          </div>
          <div className="card p-5">
            <p className="caps mb-2">If a file cannot be read</p>
            <p className="text-sm2 text-muted">
              You get a sentence saying why, such as the file being open in Excel or password protected. Your file is never changed.
            </p>
          </div>
        </aside>
      </div>

      <section className="mt-10" aria-labelledby="recent">
        <p className="caps">History</p>
        <h2 id="recent" className="mb-3 text-h2">Recent checks</h2>
        {state.loading && <Loading />}
        {state.error && <Notice tone="crit">{state.error}</Notice>}
        {state.data && state.data.recent.length === 0 && (
          <div className="card p-6 text-muted">
            Nothing checked yet. Results appear here so you can come back to them. Only a summary is kept, never your rows.
          </div>
        )}
        {state.data && state.data.recent.length > 0 && (
          <div className="card overflow-x-auto">
            <table className="w-full min-w-[640px] text-left">
              <thead>
                <tr className="border-b border-line bg-soft">
                  <th className="caps px-4 py-2 font-semibold">File</th>
                  <th className="caps px-4 py-2 font-semibold">Result</th>
                  <th className="caps px-4 py-2 text-right font-semibold">Problems</th>
                  <th className="caps px-4 py-2 text-right font-semibold">Warnings</th>
                  <th className="caps px-4 py-2 text-right font-semibold">Rows</th>
                  <th className="caps px-4 py-2 font-semibold">When</th>
                </tr>
              </thead>
              <tbody>
                {state.data.recent.map((entry) => (
                  <tr key={entry.id + entry.when} className="border-b border-soft2 last:border-0 hover:bg-soft">
                    <td className="px-4 py-2.5 font-mono text-sm2">
                      {entry.open ? (
                        <a className="underline underline-offset-2" href={href("result", entry.id)}>{entry.file}</a>
                      ) : (
                        entry.file
                      )}
                    </td>
                    <td className="px-4 py-2.5"><VerdictBadge verdict={entry.verdict} headline={entry.headline} /></td>
                    <td className="tnum px-4 py-2.5 text-right font-mono text-sm2">{fmt(entry.problems)}</td>
                    <td className="tnum px-4 py-2.5 text-right font-mono text-sm2">{fmt(entry.warnings)}</td>
                    <td className="tnum px-4 py-2.5 text-right font-mono text-sm2">{fmt(entry.rows)}</td>
                    <td className="px-4 py-2.5 text-sm2 text-muted">{when(entry.when)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </Page>
  );
}
