// Screen 4: review what was learned before it becomes "normal".

import { useEffect, useState } from "react";
import { ArrowLeft, Bookmark } from "lucide-react";
import { api, type ColumnNote } from "../api";
import { Loading, Notice, Page, fmt, go, href, plural, useLoad } from "../ui";

export function ColumnTable({ columns, skipped, onToggle }: {
  columns: ColumnNote[];
  skipped?: Set<string>;
  onToggle?: (name: string) => void;
}) {
  return (
    <div className="card overflow-x-auto">
      <table className="w-full min-w-[640px] text-left">
        <thead>
          <tr className="border-b border-line bg-soft">
            <th className="caps px-4 py-2 font-semibold">Column</th>
            <th className="caps px-4 py-2 font-semibold">What it holds</th>
            <th className="caps px-4 py-2 font-semibold">What is checked next time</th>
            {onToggle && <th className="caps px-4 py-2 text-right font-semibold">Check it</th>}
          </tr>
        </thead>
        <tbody>
          {columns.map((column) => {
            const off = skipped ? skipped.has(column.name) : !column.checked;
            return (
              <tr key={column.name} className={`border-b border-soft2 align-top last:border-0 ${off ? "opacity-55" : ""}`}>
                <td className="px-4 py-3"><span className="chip">{column.name}</span></td>
                <td className="px-4 py-3">{column.holds}</td>
                <td className="px-4 py-3 text-muted">
                  {off ? "Not compared" : (
                    <ul className="flex flex-col gap-0.5">
                      {column.checks.map((line) => <li key={line}>{line}</li>)}
                    </ul>
                  )}
                </td>
                {onToggle && (
                  <td className="px-4 py-3 text-right">
                    <input
                      type="checkbox"
                      className="h-4 w-4 accent-[#090a0f]"
                      checked={!off}
                      onChange={() => onToggle(column.name)}
                      aria-label={`Check the ${column.name} column in later files`}
                    />
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function Save({ id }: { id: string }) {
  const { data, error, loading } = useLoad(() => api.preview(id), [id]);
  const [name, setName] = useState("");
  const [skipped, setSkipped] = useState<Set<string>>(new Set());
  const [saving, setSaving] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);

  useEffect(() => {
    if (data) {
      setName(data.name);
      setSkipped(new Set(data.columns.filter((c) => !c.checked).map((c) => c.name)));
    }
  }, [data]);

  if (loading) return <Page><Loading label="Working out what normal looks like" /></Page>;
  if (error || !data) {
    return (
      <Page>
        <Notice tone="crit">{error ?? "That result is not available."}</Notice>
        <a className="btn-primary mt-4" href={href()}>Check a file</a>
      </Page>
    );
  }

  const toggle = (column: string) => {
    const next = new Set(skipped);
    if (next.has(column)) next.delete(column);
    else next.add(column);
    setSkipped(next);
  };

  const save = async () => {
    setSaving(true);
    setFailure(null);
    try {
      const saved = await api.accept(id, name, [...skipped]);
      go("dataset", saved.dataset);
    } catch (e) {
      setFailure((e as Error).message);
      setSaving(false);
    }
  };

  const findings = data.problems + data.warnings;
  return (
    <Page>
      <a className="mb-4 inline-flex items-center gap-1.5 font-medium hover:underline" href={href("result", id)}>
        <ArrowLeft size={17} aria-hidden />
        Back to the result
      </a>
      <h1 className="text-h1">This is what a normal {name ? `${name} file` : "file"} looks like</h1>
      <p className="mt-2 max-w-2xl text-muted">
        Learned from <span className="chip">{data.file}</span> ({plural(data.rows, "row")}). Later files are judged
        against this. You did not have to write any rules.
      </p>

      <div className="mt-5 flex flex-col gap-4">
        {findings > 0 && (
          <Notice tone="warn">
            This file has {[data.problems && plural(data.problems, "problem"), data.warnings && plural(data.warnings, "warning")].filter(Boolean).join(" and ")}.
            Saving it means {findings === 1 ? "that counts" : "they count"} as normal from now on.
          </Notice>
        )}
        {data.replaces && (
          <Notice>
            This replaces what normal looks like for this dataset. Your own rules and the findings you marked as fine are kept.
          </Notice>
        )}

        <div className="card p-5">
          <label htmlFor="dataset-name" className="font-medium">Name for this kind of file</label>
          <input id="dataset-name" className="input mt-2 max-w-sm font-mono" value={name} maxLength={60} onChange={(e) => setName(e.target.value)} />
          <p className="mt-2 text-sm2 text-muted">
            Later files with a similar name or the same columns are compared with this one automatically.
          </p>
        </div>

        <ColumnTable columns={data.columns} skipped={skipped} onToggle={toggle} />
        <p className="text-sm2 text-muted">
          {fmt(data.columns.length - skipped.size)} of {fmt(data.columns.length)} columns will be compared.
          Untick a column that is expected to change every time.
        </p>

        {failure && <Notice tone="crit">{failure}</Notice>}

        <div className="flex flex-wrap gap-2">
          <button type="button" className="btn-primary" disabled={saving || !name.trim()} onClick={save}>
            <Bookmark size={16} aria-hidden />
            {saving ? "Saving…" : "Save as normal"}
          </button>
          <a className="btn-outline" href={href("result", id)}>Cancel</a>
        </div>
      </div>
    </Page>
  );
}
