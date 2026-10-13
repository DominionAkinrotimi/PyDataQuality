// Screen 9: choose what to fix, and save a corrected copy. The original file is never changed.

import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, ArrowRight, CircleCheck, Download, ListChecks, RotateCcw, Wrench } from "lucide-react";
import { api, type FixOption, type FixOutcome, type FixProposal } from "../api";
import { Badge, Loading, Message, Notice, Page, VerdictBadge, fmt, href, levelTone, plural, useLoad } from "../ui";

const LEAVE = "";

function Example({ before, after }: { before: string; after: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 font-mono text-[12px]">
      <span className="chip">{before === "" ? "(empty)" : before}</span>
      <ArrowRight size={12} className="text-muted" aria-hidden />
      <span className="chip">{after === "" ? "(empty)" : after}</span>
    </span>
  );
}

function Choice({ name, value, chosen, onChoose, title, detail, option }: {
  name: string;
  value: string;
  chosen: string;
  onChoose: (value: string) => void;
  title: string;
  detail?: string;
  option?: FixOption;
}) {
  const id = `${name}-${value || "leave"}`;
  const on = chosen === value;
  return (
    <label htmlFor={id} className={`flex cursor-pointer items-start gap-3 rounded-lg border px-4 py-3 transition-colors ${on ? "border-ink bg-soft" : "border-line bg-white hover:border-line2"}`}>
      <input id={id} type="radio" name={name} className="mt-1 h-4 w-4 shrink-0 accent-[#090a0f]" checked={on} onChange={() => onChoose(value)} />
      <span className="min-w-0">
        <span className="flex flex-wrap items-center gap-2 font-medium">
          {title}
          {option?.recommended && <Badge tone="ok">Safe to fix</Badge>}
        </span>
        {detail && <span className="mt-0.5 block text-sm2 text-muted">{detail}</span>}
        {option && option.examples.length > 0 && (
          <span className="mt-2 flex flex-wrap gap-x-4 gap-y-1.5">
            {option.examples.map(([before, after], i) => <Example key={i} before={before} after={after} />)}
          </span>
        )}
      </span>
    </label>
  );
}

function ProposalCard({ proposal, chosen, onChoose }: { proposal: FixProposal; chosen: string; onChoose: (action: string) => void }) {
  return (
    <li className="card p-5">
      <fieldset>
        <legend className="flex w-full flex-wrap items-start justify-between gap-2">
          <span className="text-h3 font-normal"><Message text={proposal.message} column={proposal.column} /></span>
          <Badge tone={levelTone(proposal.level)}>{proposal.level === "problem" ? "Problem" : proposal.level === "warning" ? "Warning" : "Note"}</Badge>
        </legend>
        <div className="mt-4 flex flex-col gap-2">
          {proposal.options.map((option) => (
            <Choice key={option.action} name={proposal.key} value={option.action} chosen={chosen} onChoose={onChoose} title={option.label} detail={option.detail} option={option} />
          ))}
          <Choice name={proposal.key} value={LEAVE} chosen={chosen} onChoose={onChoose} title="Leave it as it is" />
        </div>
      </fieldset>
    </li>
  );
}

function Outcome({ outcome, id, onAgain }: { outcome: FixOutcome; id: string; onAgain: () => void }) {
  const done = [
    outcome.removed_rows > 0 && `${plural(outcome.removed_rows, "row")} removed`,
    outcome.changed_cells > 0 && `${plural(outcome.changed_cells, "cell")} changed`,
  ].filter(Boolean).join(", ");
  const left = outcome.after.problems + outcome.after.warnings;
  return (
    <div className="flex flex-col gap-4">
      <section className="card p-6" aria-label="Corrected copy">
        <div className="flex items-start gap-4">
          <span className="grid h-12 w-12 shrink-0 place-items-center rounded-lg bg-ok-bg text-ok-ink"><CircleCheck size={24} aria-hidden /></span>
          <div className="min-w-0">
            <h1 className="text-h1">The corrected copy is ready</h1>
            <p className="mt-1 text-h3 font-normal text-slate2">{done}. {plural(outcome.rows_left, "row")} in the copy.</p>
            <p className="mt-1 text-muted">Your original file was not changed.</p>
          </div>
        </div>
        <div className="mt-5 flex flex-wrap gap-2 border-t border-line pt-5">
          <a className="btn-primary" href={api.fixedLink(id)}>
            <Download size={16} aria-hidden />
            Download {outcome.file}
          </a>
          <a className="btn-outline" href={api.changesLink(id)}>
            <ListChecks size={16} aria-hidden />
            Download the list of changes
            <span className="font-mono text-sm2 text-muted">.csv</span>
          </a>
        </div>
      </section>

      <section className="card p-6" aria-label="The corrected copy, checked again">
        <p className="caps">The corrected copy, checked again</p>
        <p className="mt-2"><VerdictBadge verdict={outcome.after.verdict} headline={outcome.after.headline} /></p>
        {left === 0 ? (
          <p className="mt-3 text-muted">Nothing is left to report.</p>
        ) : (
          <>
            <p className="mt-3 text-muted">{plural(left, "finding")} left. These were not fixed:</p>
            <ul className="mt-2 flex flex-col gap-1.5">
              {outcome.after.left.map((message) => <li key={message} className="rounded border border-line bg-soft px-3 py-2">{message}</li>)}
            </ul>
          </>
        )}
      </section>

      <div className="flex flex-wrap gap-2">
        <button type="button" className="btn-outline" onClick={onAgain}><Wrench size={16} aria-hidden />Change what is fixed</button>
        <a className="btn-outline" href={href("result", id)}><ArrowLeft size={16} aria-hidden />Back to the result</a>
        <a className="btn-outline" href={href()}><RotateCcw size={16} aria-hidden />Check another file</a>
      </div>
    </div>
  );
}

export function Fix({ id }: { id: string }) {
  const { data, error, loading } = useLoad(() => api.fixes(id), [id]);
  const [choices, setChoices] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);
  const [outcome, setOutcome] = useState<FixOutcome | null>(null);

  useEffect(() => {
    if (!data) return;
    const start: Record<string, string> = {};
    for (const proposal of data.fixable) start[proposal.key] = proposal.options.find((o) => o.recommended)?.action ?? LEAVE;
    setChoices(start);
  }, [data]);

  const totals = useMemo(() => {
    let rows = 0;
    let cells = 0;
    for (const proposal of data?.fixable ?? []) {
      const option = proposal.options.find((o) => o.action === choices[proposal.key]);
      if (option) { rows += option.rows; cells += option.cells; }
    }
    return { rows, cells, any: Object.values(choices).some((action) => action !== LEAVE) };
  }, [choices, data]);

  if (loading) return <Page><Loading label="Working out what can be fixed" /></Page>;
  if (error || !data) {
    return (
      <Page>
        <Notice tone="crit">{error ?? "That result is not available."}</Notice>
        <a className="btn-primary mt-4" href={href()}>Check a file</a>
      </Page>
    );
  }

  if (outcome) return <Page><Outcome outcome={outcome} id={id} onAgain={() => setOutcome(null)} /></Page>;

  const apply = async () => {
    setBusy(true);
    setFailure(null);
    try {
      const chosen = Object.fromEntries(Object.entries(choices).filter(([, action]) => action !== LEAVE));
      setOutcome(await api.fix(id, chosen));
      window.scrollTo(0, 0);
    } catch (e) {
      setFailure((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Page>
      <a className="mb-4 inline-flex items-center gap-1.5 font-medium hover:underline" href={href("result", id)}>
        <ArrowLeft size={17} aria-hidden />
        Back to the result
      </a>
      <h1 className="text-h1">Fix this file</h1>
      <p className="mt-2 max-w-2xl text-muted">
        Choose what to fix in <span className="chip">{data.file}</span>. You get a corrected copy and a list of every change.
        Your original file is not changed.
      </p>

      <div className="mt-6 flex flex-col gap-6">
        {data.fixable.length === 0 ? (
          <Notice>Nothing in this file can be fixed from here.</Notice>
        ) : (
          <ol className="flex flex-col gap-3">
            {data.fixable.map((proposal) => (
              <ProposalCard key={proposal.key} proposal={proposal} chosen={choices[proposal.key] ?? LEAVE} onChoose={(action) => setChoices({ ...choices, [proposal.key]: action })} />
            ))}
          </ol>
        )}

        {data.not_fixable.length > 0 && (
          <section aria-labelledby="not-fixable">
            <h2 id="not-fixable" className="mb-3 text-h2">Cannot be fixed here</h2>
            <ul className="card divide-y divide-soft2">
              {data.not_fixable.map((proposal) => (
                <li key={proposal.key} className="px-5 py-4">
                  <p><Message text={proposal.message} column={proposal.column} /></p>
                  <p className="mt-1 text-sm2 text-muted">{proposal.reason}</p>
                </li>
              ))}
            </ul>
          </section>
        )}

        {failure && <Notice tone="crit">{failure}</Notice>}

        {data.fixable.length > 0 && (
          <div className="card sticky bottom-4 flex flex-wrap items-center justify-between gap-3 p-4 shadow-[0_8px_30px_-12px_rgba(9,10,15,0.25)]">
            <p className="text-muted" role="status">
              {totals.any
                ? <>The copy will have <span className="font-medium text-ink">{plural(totals.rows, "row")} removed</span> and <span className="font-medium text-ink">{plural(totals.cells, "cell")} changed</span>, out of {fmt(data.rows)} rows.</>
                : "Nothing is chosen yet."}
            </p>
            <button type="button" className="btn-primary" disabled={busy || !totals.any} onClick={apply}>
              <Wrench size={16} aria-hidden />
              {busy ? "Fixing…" : "Make a corrected copy"}
            </button>
          </div>
        )}
      </div>
    </Page>
  );
}
