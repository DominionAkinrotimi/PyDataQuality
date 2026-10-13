// Screen 2: the verdict and the findings.

import { useState } from "react";
import { Bookmark, CircleCheck, CircleHelp, Download, Eye, FileText, RotateCcw, Terminal, Wrench } from "lucide-react";
import { api, type CheckResult, type Finding, type Level } from "../api";
import {
  Badge, CopyButton, Loading, Message, Notice, Page, VerdictIcon,
  fmt, href, levelTone, plural, sentence, useLoad, verdictTone,
} from "../ui";

const GROUPS: { level: Level; title: string; hint: string }[] = [
  { level: "problem", title: "Problems", hint: "Fix these, or get a corrected file, before relying on the data" },
  { level: "warning", title: "Warnings", hint: "Probably usable, but look at each one first" },
  { level: "note", title: "Also noted", hint: "May be fine. These never change the verdict" },
];

const SHOWN_AT_FIRST = 20;

function summary(result: CheckResult): string {
  const parts = [];
  if (result.problems) parts.push(plural(result.problems, "problem"));
  if (result.warnings) parts.push(plural(result.warnings, "warning"));
  if (!parts.length) {
    return result.has_baseline
      ? "Nothing has changed in a way that needs your attention."
      : "None of the usual problems were found in this file.";
  }
  return `${parts.join(" and ")} found in ${result.name}.`;
}

function FindingCard({
  finding, result, onIgnore, busy,
}: { finding: Finding; result: CheckResult; onIgnore: (key: string) => void; busy: boolean }) {
  const [why, setWhy] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const whyId = `why-${finding.index}`;
  return (
    <li className="card p-5">
      <div className="flex items-start justify-between gap-3">
        <p className="min-w-0 text-h3 font-medium leading-7">
          <Message text={finding.message} column={finding.column} />
        </p>
        <Badge tone={levelTone(finding.level)}>{finding.category}</Badge>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        {finding.has_rows && (
          <a className="btn-primary !min-h-[34px] !px-3 !py-1.5 text-sm2" href={href("rows", result.id, String(finding.index))}>
            <Eye size={15} aria-hidden />
            See the rows ({fmt(finding.count)})
          </a>
        )}
        {finding.why && (
          <button type="button" className="btn-outline !min-h-[34px] !px-3 !py-1.5 text-sm2" aria-expanded={why} aria-controls={whyId} onClick={() => setWhy(!why)}>
            <CircleHelp size={15} aria-hidden />
            Why?
          </button>
        )}
        {result.has_baseline && !confirm && (
          <button type="button" className="btn-ghost ml-auto !min-h-[34px] text-sm2" onClick={() => setConfirm(true)}>
            This is fine
          </button>
        )}
      </div>

      {why && (
        <div id={whyId} className="mt-3 rounded-lg border border-line bg-soft p-3.5">
          <p className="caps mb-1">How this was decided</p>
          <p>{finding.why}</p>
          {finding.examples.length > 0 && (
            <p className="mt-2 flex flex-wrap items-center gap-1.5 text-sm2 text-muted">
              Examples:
              {finding.examples.slice(0, 5).map((example, i) => (
                <span key={i} className="chip">{example === "" ? "(empty)" : example}</span>
              ))}
            </p>
          )}
        </div>
      )}

      {confirm && (
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-line bg-soft p-3.5">
          <p className="min-w-0">
            Stop reporting this for <span className="chip">{result.dataset}</span> files from now on?
            You can turn it back on under My datasets.
          </p>
          <div className="flex gap-2">
            <button type="button" className="btn-primary" disabled={busy} onClick={() => onIgnore(finding.key)}>Yes, it is fine</button>
            <button type="button" className="btn-outline" onClick={() => setConfirm(false)}>Cancel</button>
          </div>
        </div>
      )}
    </li>
  );
}

export function Result({ id }: { id: string }) {
  const { data: result, error, loading, setData } = useLoad(() => api.result(id), [id]);
  const [showAll, setShowAll] = useState(false);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  if (loading) return <Page><Loading label="Loading the result" /></Page>;
  if (error || !result) {
    return (
      <Page>
        <Notice tone="crit">{error ?? "That result is not available."}</Notice>
        <a className="btn-primary mt-4" href={href()}>Check a file</a>
      </Page>
    );
  }

  const ignore = async (key: string) => {
    setBusy(true);
    setActionError(null);
    try {
      setData(await api.ignore(result.id, key));
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const tone = verdictTone(result.verdict);
  const bar = { crit: "bg-crit-ink", warn: "bg-warn-ink", ok: "bg-ok-ink", info: "bg-info-ink", plain: "bg-ink" }[tone];
  const tile = { crit: "bg-crit-bg text-crit-ink", warn: "bg-warn-bg text-warn-ink", ok: "bg-ok-bg text-ok-ink", info: "", plain: "" }[tone];
  const visible = showAll ? result.findings : result.findings.slice(0, SHOWN_AT_FIRST);
  const saveLabel = result.has_baseline ? "These changes are fine. Make this the new normal" : "Remember this file as normal";

  return (
    <Page wide>
      <p className="mb-4 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm2 text-muted">
        <span className="chip">{result.name}</span>
        <span className="tnum font-mono">{plural(result.rows, "row")}</span>·
        <span className="tnum font-mono">{plural(result.columns, "column")}</span>·
        {result.compared_with ? (
          <span>Compared with <span className="chip">{result.compared_with}</span></span>
        ) : (
          <span>No earlier file to compare with, so this only covers what is wrong in any file</span>
        )}
        <span className="ml-auto font-mono">checked in {result.seconds}s</span>
      </p>

      {result.sample && (
        <div className="mb-4">
          <Notice>This is the built-in sample file. <a className="underline" href={href()}>Check one of your own</a> when you are ready.</Notice>
        </div>
      )}

      <section className="card relative overflow-hidden" aria-label="Verdict">
        <span className={`absolute inset-y-0 left-0 w-1.5 ${bar}`} aria-hidden />
        <div className="flex flex-col gap-5 p-6 pl-8 md:flex-row md:items-center md:justify-between">
          <div className="flex items-start gap-4">
            <span className={`grid h-14 w-14 shrink-0 place-items-center rounded-lg ${tile}`}>
              <VerdictIcon verdict={result.verdict} size={28} />
            </span>
            <div>
              <h1 className="text-h1">{sentence(result.headline)}</h1>
              <p className="mt-1 text-h3 font-normal text-slate2">{summary(result)}</p>
            </div>
          </div>
          <dl className="grid grid-cols-3 divide-x divide-line rounded-lg bg-soft2 text-center">
            {[
              ["Problems", result.problems, result.problems ? "text-crit-ink" : ""],
              ["Warnings", result.warnings, result.warnings ? "text-warn-ink" : ""],
              ["Clean columns", result.clean_columns.length, ""],
            ].map(([label, value, colour]) => (
              <div key={label as string} className="px-5 py-3">
                <dd className={`tnum font-mono text-stat ${colour}`}>{fmt(value as number)}</dd>
                <dt className="caps mt-1">{label}</dt>
              </div>
            ))}
          </dl>
        </div>
      </section>

      {actionError && <div className="mt-4"><Notice tone="crit">{actionError}</Notice></div>}

      <div className="mt-6 grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="flex min-w-0 flex-col gap-8">
          {result.findings.length === 0 && (
            <div className="card flex items-start gap-3 p-6">
              <CircleCheck size={22} className="mt-0.5 shrink-0 text-ok-ink" aria-hidden />
              <div>
                <p className="text-h3">Every column was looked at and nothing was flagged.</p>
                {!result.has_baseline && !result.sample && (
                  <p className="mt-1 text-muted">
                    If this file is good, remember it as normal. The next version will then be compared with it.
                  </p>
                )}
              </div>
            </div>
          )}

          {GROUPS.map(({ level, title, hint }) => {
            const group = visible.filter((f) => f.level === level);
            const total = result.findings.filter((f) => f.level === level).length;
            if (!total) return null;
            return (
              <section key={level} aria-labelledby={`group-${level}`}>
                <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
                  <h2 id={`group-${level}`} className="flex items-center gap-2 text-h2">
                    {title}
                    <Badge tone={levelTone(level)}>{total}</Badge>
                  </h2>
                  <p className="text-sm2 text-muted">{hint}</p>
                </div>
                <ol className="flex flex-col gap-3">
                  {group.map((finding) => (
                    <FindingCard key={finding.key + finding.index} finding={finding} result={result} onIgnore={ignore} busy={busy} />
                  ))}
                </ol>
              </section>
            );
          })}

          {result.findings.length > SHOWN_AT_FIRST && !showAll && (
            <button type="button" className="btn-outline self-start" onClick={() => setShowAll(true)}>
              Show all {result.findings.length} findings
            </button>
          )}

          {result.clean_columns.length > 0 && result.findings.length > 0 && (
            <section aria-labelledby="clean">
              <h2 id="clean" className="mb-3 flex items-center gap-2 text-h2">
                <CircleCheck size={20} aria-hidden />
                {result.has_baseline ? "Unchanged columns" : "No issues in"}
              </h2>
              <div className="card flex flex-wrap gap-2 p-5">
                {result.clean_columns.map((column) => (
                  <span key={column} className="chip">{column}</span>
                ))}
              </div>
            </section>
          )}

          {result.hidden > 0 && (
            <p className="text-sm2 text-muted">
              {plural(result.hidden, "finding")} hidden because you marked {result.hidden === 1 ? "it" : "them"} as fine.{" "}
              <a className="underline" href={href("dataset", result.dataset)}>Review</a>
            </p>
          )}
        </div>

        <aside className="flex flex-col gap-4 lg:sticky lg:top-20">
          <div className="card p-5">
            <p className="caps">What next</p>
            {!result.sample && (
              <>
                <a className="btn-primary mt-3 w-full text-center" href={href("save", result.id)}>
                  <Bookmark size={16} aria-hidden />
                  {saveLabel}
                </a>
                <p className="mt-2 text-sm2 text-muted">
                  You will see what was learned before anything is saved.
                </p>
              </>
            )}
            <div className="mt-4 flex flex-col gap-2 border-t border-line pt-4">
              {result.problems + result.warnings > 0 && (
                <a className="btn-outline justify-start" href={href("fix", result.id)}>
                  <Wrench size={16} aria-hidden />
                  Fix this file
                  <span className="ml-auto text-sm2 text-muted">makes a copy</span>
                </a>
              )}
              {result.affected_rows > 0 && (
                <a className="btn-outline justify-start" href={api.rowsLink(result.id, "all")}>
                  <Download size={16} aria-hidden />
                  Download the affected rows
                  <span className="ml-auto font-mono text-sm2 text-muted">.csv</span>
                </a>
              )}
              <a className="btn-outline justify-start" href={api.reportLink(result.id)}>
                <FileText size={16} aria-hidden />
                Download a summary to share
                <span className="ml-auto font-mono text-sm2 text-muted">.html</span>
              </a>
              <a className="btn-outline justify-start" href={href()}>
                <RotateCcw size={16} aria-hidden />
                Check another file
              </a>
            </div>
          </div>

          {!result.sample && !result.has_baseline && (
            <div className="card p-5">
              <p className="caps flex items-center gap-1.5"><Terminal size={13} aria-hidden /> Same check from a terminal</p>
              <pre className="mt-2 overflow-x-auto rounded border border-line bg-soft p-2.5 font-mono text-[12px]">pdq check {result.name}</pre>
              <div className="mt-2"><CopyButton text={`pdq check ${result.name}`} /></div>
            </div>
          )}
        </aside>
      </div>
    </Page>
  );
}
