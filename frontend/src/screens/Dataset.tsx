// Screen 6: one dataset. History, what normal looks like, rules and ignored findings.

import { useState } from "react";
import { ArrowLeft, Trash2 } from "lucide-react";
import { api } from "../api";
import { Loading, Notice, Page, VerdictBadge, fmt, go, href, plural, useLoad, verdictTone, when } from "../ui";
import { ColumnTable } from "./Save";

type Tab = "history" | "normal" | "rules";
const TABS: { id: Tab; label: string }[] = [
  { id: "history", label: "History" },
  { id: "normal", label: "What normal looks like" },
  { id: "rules", label: "Rules and ignored findings" },
];

const DOT = { crit: "bg-crit-ink", warn: "bg-warn-ink", ok: "bg-ok-ink", info: "bg-info-ink", plain: "bg-ink" };

export function Dataset({ datasetKey }: { datasetKey: string }) {
  const { data, error, loading, setData } = useLoad(() => api.dataset(datasetKey), [datasetKey]);
  const [tab, setTab] = useState<Tab>("history");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);

  const remove = async () => {
    try {
      await api.deleteDataset(datasetKey);
      go("datasets");
    } catch (e) {
      setFailure((e as Error).message);
    }
  };

  if (loading) return <Page><Loading /></Page>;
  if (error || !data) {
    return (
      <Page>
        <a className="mb-4 inline-flex items-center gap-1.5 font-medium hover:underline" href={href("datasets")}>
          <ArrowLeft size={17} aria-hidden /> My datasets
        </a>
        <Notice tone="crit">{error ?? "That dataset is not available."}</Notice>
        {!confirmDelete ? (
          <button type="button" className="btn-outline mt-4" onClick={() => setConfirmDelete(true)}>
            <Trash2 size={16} aria-hidden /> Delete this dataset
          </button>
        ) : (
          <div className="mt-4 flex gap-2">
            <button type="button" className="btn-primary" onClick={remove}>Yes, delete it</button>
            <button type="button" className="btn-outline" onClick={() => setConfirmDelete(false)}>Cancel</button>
          </div>
        )}
      </Page>
    );
  }

  const restore = async (key: string) => {
    try {
      setData(await api.unignore(data.key, key));
    } catch (e) {
      setFailure((e as Error).message);
    }
  };

  const strip = data.history.slice(0, 12).reverse();

  return (
    <Page>
      <a className="mb-4 inline-flex items-center gap-1.5 font-medium hover:underline" href={href("datasets")}>
        <ArrowLeft size={17} aria-hidden /> My datasets
      </a>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="font-mono text-h1">{data.name}</h1>
          <p className="mt-1 text-muted">
            Normal was learned from <span className="chip">{data.learned_from || "a file"}</span>
            {data.learned_on && ` on ${data.learned_on}`} ({plural(data.rows, "row")}).
          </p>
        </div>
        <a className="btn-primary" href={href()}>Check a new file</a>
      </div>

      {failure && <div className="mt-4"><Notice tone="crit">{failure}</Notice></div>}

      <div role="tablist" aria-label="Dataset sections" className="mt-6 inline-flex flex-wrap gap-1 rounded bg-soft2 p-[3px]">
        {TABS.map(({ id, label }) => (
          <button
            key={id}
            role="tab"
            type="button"
            aria-selected={tab === id}
            onClick={() => setTab(id)}
            className={`rounded-[4px] border px-3 py-1.5 text-sm2 font-medium ${
              tab === id ? "border-line bg-white text-ink" : "border-transparent text-muted hover:text-ink"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="mt-5" role="tabpanel">
        {tab === "history" && (
          <>
            {data.history.length === 0 ? (
              <div className="card p-6 text-muted">
                No file has been checked against this yet. Check the next version of the file and it will appear here.
              </div>
            ) : (
              <>
                <div className="mb-4 flex items-center gap-3">
                  <span className="caps">Last {strip.length}</span>
                  <ol className="flex gap-1" aria-label="Recent verdicts, oldest first">
                    {strip.map((entry, i) => (
                      <li key={i} title={`${entry.file}: ${entry.headline.toLowerCase()}`}>
                        <span className={`block h-5 w-2.5 rounded-sm ${DOT[verdictTone(entry.verdict)]}`} />
                        <span className="sr-only">{entry.file}: {entry.headline.toLowerCase()}</span>
                      </li>
                    ))}
                  </ol>
                </div>
                <div className="card overflow-x-auto">
                  <table className="w-full min-w-[560px] text-left">
                    <thead>
                      <tr className="border-b border-line bg-soft">
                        <th className="caps px-4 py-2 font-semibold">When</th>
                        <th className="caps px-4 py-2 font-semibold">File</th>
                        <th className="caps px-4 py-2 font-semibold">Result</th>
                        <th className="caps px-4 py-2 text-right font-semibold">Problems</th>
                        <th className="caps px-4 py-2 text-right font-semibold">Warnings</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.history.map((entry, i) => (
                        <tr key={i} className="border-b border-soft2 last:border-0">
                          <td className="px-4 py-2.5 text-sm2 text-muted">{when(entry.when)}</td>
                          <td className="px-4 py-2.5 font-mono text-sm2">{entry.file}</td>
                          <td className="px-4 py-2.5"><VerdictBadge verdict={entry.verdict} headline={entry.headline} /></td>
                          <td className="tnum px-4 py-2.5 text-right font-mono text-sm2">{fmt(entry.problems)}</td>
                          <td className="tnum px-4 py-2.5 text-right font-mono text-sm2">{fmt(entry.warnings)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
            <p className="mt-3 text-sm2 text-muted">Only these summaries are kept. Past files and their rows are not stored.</p>
          </>
        )}

        {tab === "normal" && (
          <>
            <ColumnTable columns={data.columns} />
            <p className="mt-3 text-sm2 text-muted">
              To update this, check a newer file and choose “Make this the new normal”. The saved description is a small
              text file you can also open and edit: <span className="break-all font-mono">{data.path}</span>
            </p>
          </>
        )}

        {tab === "rules" && (
          <div className="flex flex-col gap-6">
            <section>
              <h2 className="mb-2 text-h3">Your rules</h2>
              {data.rules.length === 0 ? (
                <div className="card p-5 text-muted">
                  No rules of your own yet. To add one, open the file below in a text editor and add lines like these:
                  <pre className="mt-3 overflow-x-auto rounded border border-line bg-soft p-3 font-mono text-[12px] text-ink">{`rules:
  price: [greater than 0]
  order_id: [unique, not empty]
  status: [one of paid, pending, refunded]`}</pre>
                  <p className="mt-2 break-all font-mono text-sm2">{data.path}</p>
                </div>
              ) : (
                <ul className="card divide-y divide-soft2">
                  {data.rules.map((rule, i) => (
                    <li key={i} className="px-4 py-3">
                      <span className="chip">{rule.column}</span> must be: {rule.rule}
                    </li>
                  ))}
                </ul>
              )}
            </section>
            <section>
              <h2 className="mb-2 text-h3">Findings you marked as fine</h2>
              {data.ignored.length === 0 ? (
                <div className="card p-5 text-muted">None. Use “This is fine” on a result to stop a finding being reported.</div>
              ) : (
                <ul className="card divide-y divide-soft2">
                  {data.ignored.map((key) => {
                    const [code, ...rest] = key.split(":");
                    return (
                      <li key={key} className="flex flex-wrap items-center justify-between gap-2 px-4 py-3">
                        <span>
                          {code.replace(/_/g, " ")} in <span className="chip">{rest.join(":")}</span>
                        </span>
                        <button type="button" className="btn-outline" onClick={() => restore(key)}>Start flagging this again</button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </section>
          </div>
        )}
      </div>

      <div className="mt-10 border-t border-line pt-5">
        {!confirmDelete ? (
          <button type="button" className="btn-ghost" onClick={() => setConfirmDelete(true)}>
            <Trash2 size={16} aria-hidden /> Delete this dataset
          </button>
        ) : (
          <div className="flex flex-wrap items-center gap-3 rounded-lg border border-line bg-white p-4">
            <p className="min-w-0 flex-1">
              Delete <span className="chip">{data.name}</span> and its history? Your data files are not touched.
            </p>
            <button type="button" className="btn-primary" onClick={remove}>Yes, delete it</button>
            <button type="button" className="btn-outline" onClick={() => setConfirmDelete(false)}>Cancel</button>
          </div>
        )}
      </div>
    </Page>
  );
}
