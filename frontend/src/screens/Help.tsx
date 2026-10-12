// Screen 8: how it works and where data goes.

import { useState, type ReactNode } from "react";
import { api, type Verdict } from "../api";
import { Notice, Page, VerdictBadge, href, useLoad } from "../ui";

const STEPS: [string, string][] = [
  ["Check", "Drop in a file. You get a verdict and a short list of what is wrong, worst first."],
  ["Remember", "When a file is good, save it as normal. PyDataQuality learns its columns, values and ranges. You write no rules."],
  ["Check the next one", "The next version is compared with it automatically, so you also see what changed."],
  ["Act", "Download the affected rows with the reason for each, or a one-page summary to send back."],
];

const VERDICTS: [Verdict, string, string, string][] = [
  ["problems", "NOT SAFE TO USE", "PROBLEMS FOUND", "At least one problem. Fix it or get a corrected file before relying on the data."],
  ["warnings", "CHECK BEFORE USE", "THINGS TO CHECK", "Only warnings. Probably usable, but look at each one first."],
  ["ok", "LOOKS LIKE LAST TIME", "NOTHING OBVIOUSLY WRONG", "Nothing was found."],
];

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="card p-6">
      <h2 className="mb-3 text-h2">{title}</h2>
      <div className="flex flex-col gap-3">{children}</div>
    </section>
  );
}

export function Help() {
  const state = useLoad(api.state, []);
  const [confirm, setConfirm] = useState(false);
  const [outcome, setOutcome] = useState<string | null>(null);

  const forget = async () => {
    try {
      const done = await api.forgetEverything();
      setOutcome(`Deleted ${done.removed} saved dataset${done.removed === 1 ? "" : "s"} and the check history.`);
      state.reload();
    } catch (e) {
      setOutcome((e as Error).message);
    }
    setConfirm(false);
  };

  return (
    <Page>
      <p className="caps">Help and privacy</p>
      <h1 className="text-h1">How it works</h1>

      <div className="mt-6 flex flex-col gap-5">
        <Section title="Four steps">
          <ol className="grid gap-3 sm:grid-cols-2">
            {STEPS.map(([name, text], i) => (
              <li key={name} className="rounded-lg border border-line bg-soft p-4">
                <p className="caps">Step {i + 1}</p>
                <p className="text-h3">{name}</p>
                <p className="mt-1 text-muted">{text}</p>
              </li>
            ))}
          </ol>
        </Section>

        <Section title="What the verdicts mean">
          <ul className="flex flex-col gap-3">
            {VERDICTS.map(([verdict, withBaseline, first, meaning]) => (
              <li key={verdict} className="flex flex-col gap-1.5">
                <span className="flex flex-wrap gap-2">
                  <VerdictBadge verdict={verdict} headline={withBaseline} />
                  <VerdictBadge verdict={verdict} headline={first} />
                </span>
                <span className="text-muted">{meaning}</span>
              </li>
            ))}
          </ul>
          <p className="text-muted">
            The first wording appears when there is an earlier file to compare with. The second appears on a first check.
            Without something to compare against, the app never says a file is safe.
          </p>
          <p className="text-muted">
            Findings come as problems, warnings, and things that are “also noted”. Notes may be perfectly fine and never
            change the verdict.
          </p>
        </Section>

        <Section title="Where your data goes">
          <p><strong>Nowhere.</strong> This page is served by a program running on your own computer. It makes no requests to the internet, and there is no account.</p>
          <ul className="flex list-disc flex-col gap-1.5 pl-5 text-muted">
            <li>A file you drop in is read and then deleted from a temporary folder.</li>
            <li>The last few results are held in memory until you close the pdq window.</li>
            <li>If you save a file as normal, a small description is kept: column names, types, ranges, the distinct values of category columns, and row counts. Not your rows.</li>
            <li>A one-line summary of each check is kept for the history lists.</li>
            <li>The summary you can download contains findings and a few example values. Read it before forwarding.</li>
          </ul>
          {state.data && (
            <p className="text-muted">
              Everything saved is in this folder: <span className="break-all font-mono text-ink">{state.data.home}</span>
            </p>
          )}
          {outcome && <Notice tone="ok">{outcome}</Notice>}
          {!confirm ? (
            <button type="button" className="btn-outline self-start" onClick={() => setConfirm(true)}>Delete everything saved</button>
          ) : (
            <div className="flex flex-wrap items-center gap-3 rounded-lg border border-line bg-soft p-4">
              <p className="min-w-0 flex-1">Delete every saved dataset and the check history? Your data files are not touched.</p>
              <button type="button" className="btn-primary" onClick={forget}>Yes, delete everything</button>
              <button type="button" className="btn-outline" onClick={() => setConfirm(false)}>Cancel</button>
            </div>
          )}
        </Section>

        <Section title="When it gets something wrong">
          <ul className="flex list-disc flex-col gap-1.5 pl-5 text-muted">
            <li>If the whole file is fine, save it as the new normal.</li>
            <li>If one finding is fine, use “This is fine” on it. It stops being reported for that dataset, and you can turn it back on under <a className="underline" href={href("datasets")}>My datasets</a>.</li>
            <li>If the columns look wrong, the file probably has title rows above the header. Remove them and try again.</li>
            <li>If a file cannot be read, it may be open in Excel, password protected or damaged.</li>
          </ul>
        </Section>

        <Section title="From a terminal or Python">
          <p className="text-muted">The same checks are available without this page.</p>
          <pre className="overflow-x-auto rounded border border-line bg-soft p-3 font-mono text-[12px]">{`pdq check orders.csv        # verdict and findings
pdq accept orders.csv       # remember it as normal
pdq rows orders.csv         # save the affected rows
pdq report orders.csv       # one-page summary to share

import pydataquality as pdq
result = pdq.check("orders.csv")`}</pre>
        </Section>
      </div>
    </Page>
  );
}
