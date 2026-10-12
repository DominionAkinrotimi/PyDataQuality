// Screen 5: every kind of file the user has saved.

import { useState } from "react";
import { ChevronRight, Database, Search } from "lucide-react";
import { api } from "../api";
import { Loading, Notice, Page, VerdictBadge, fmt, href, plural, useLoad, when } from "../ui";

export function Datasets() {
  const { data, error, loading } = useLoad(api.datasets, []);
  const [search, setSearch] = useState("");

  if (loading) return <Page><Loading /></Page>;
  if (error || !data) return <Page><Notice tone="crit">{error}</Notice></Page>;

  const all = data.datasets;
  const shown = all.filter((d) => d.name.toLowerCase().includes(search.trim().toLowerCase()));

  return (
    <Page>
      <p className="caps">Saved on this computer</p>
      <h1 className="text-h1">My datasets</h1>
      <p className="mt-2 max-w-2xl text-muted">
        Each one is a kind of file you check regularly. New versions are compared with what you saved as normal.
      </p>

      {all.length === 0 && (
        <div className="card mt-6 flex flex-col items-start gap-3 p-6">
          <span className="grid h-10 w-10 place-items-center rounded bg-soft2" aria-hidden><Database size={20} /></span>
          <p className="text-h3">Nothing saved yet.</p>
          <p className="max-w-xl text-muted">
            Check a file and choose “Remember this file as normal”. After that, each new version of it is compared automatically.
          </p>
          <a className="btn-primary" href={href()}>Check a file</a>
        </div>
      )}

      {all.length > 10 && (
        <label className="relative mt-5 block max-w-sm">
          <span className="sr-only">Search datasets</span>
          <Search size={16} className="pointer-events-none absolute left-3 top-[11px] text-muted" aria-hidden />
          <input className="input pl-9" placeholder="Search datasets" value={search} onChange={(e) => setSearch(e.target.value)} />
        </label>
      )}

      {all.length > 0 && (
        <ul className="mt-5 flex flex-col gap-3">
          {shown.map((dataset) => (
            <li key={dataset.key}>
              <a href={href("dataset", dataset.key)} className="card flex flex-wrap items-center gap-x-6 gap-y-2 p-4 hover:border-line2 hover:bg-soft">
                <div className="min-w-[12rem] flex-1">
                  <p className="font-mono text-h3">{dataset.name}</p>
                  <p className="text-sm2 text-muted">
                    {dataset.damaged
                      ? "The saved description is damaged. Open to delete it."
                      : `Normal learned from ${dataset.learned_from || "a file"} · ${fmt(dataset.columns ?? 0)} columns`}
                  </p>
                </div>
                <div className="text-sm2">
                  {dataset.last ? (
                    <>
                      <VerdictBadge verdict={dataset.last.verdict} headline={dataset.last.headline} />
                      <p className="mt-1 text-muted">{dataset.last.file} · {when(dataset.last.when)}</p>
                    </>
                  ) : (
                    <span className="text-muted">No later file checked yet</span>
                  )}
                </div>
                <span className="tnum font-mono text-sm2 text-muted">{plural(dataset.checks, "check")}</span>
                <ChevronRight size={18} className="text-muted" aria-hidden />
              </a>
            </li>
          ))}
          {shown.length === 0 && <li className="text-muted">No dataset matches “{search}”.</li>}
        </ul>
      )}
    </Page>
  );
}
