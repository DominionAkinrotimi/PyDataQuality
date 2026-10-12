// Screen 3: the rows behind a finding.

import { useMemo, useState } from "react";
import { ArrowLeft, Download, Search } from "lucide-react";
import { api } from "../api";
import { CopyButton, Loading, Notice, Page, fmt, go, href, plural, useLoad } from "../ui";

export function Rows({ id, finding }: { id: string; finding: string }) {
  const { data, error, loading } = useLoad(() => api.rows(id, finding), [id, finding]);
  const [search, setSearch] = useState("");

  const visible = useMemo(() => {
    if (!data) return [];
    const needle = search.trim().toLowerCase();
    if (!needle) return data.rows;
    return data.rows.filter(
      (row) => row.reason.toLowerCase().includes(needle) || row.cells.some((cell) => cell.toLowerCase().includes(needle)),
    );
  }, [data, search]);

  if (loading) return <Page wide><Loading label="Loading the rows" /></Page>;
  if (error || !data) {
    return (
      <Page>
        <Notice tone="crit">{error ?? "Those rows are not available."}</Notice>
        <a className="btn-primary mt-4" href={href()}>Check a file</a>
      </Page>
    );
  }

  const highlight = data.highlight ? data.columns.indexOf(data.highlight) : -1;
  const message =
    finding === "all"
      ? `${plural(data.total, "row")} in ${data.file} need attention. The rows are attached, with the reason for each in the first column.`
      : `In ${data.file}: ${data.title} The ${data.total === 1 ? "row is" : "rows are"} attached.`;

  return (
    <Page wide>
      <a className="mb-4 inline-flex items-center gap-1.5 font-medium hover:underline" href={href("result", id)}>
        <ArrowLeft size={17} aria-hidden />
        Back to the result for {data.file}
      </a>

      <h1 className="max-w-4xl text-h1">{data.title}</h1>
      <p className="mt-2 text-muted">
        {data.total === 0
          ? "This finding is about the file as a whole, so there are no individual rows to show."
          : data.shown < data.total
            ? `Showing the first ${fmt(data.shown)} of ${fmt(data.total)} affected rows. Download to see all of them.`
            : `${plural(data.total, "affected row")} out of ${fmt(data.file_rows)} in the file.`}
      </p>

      <div className="card mt-5 flex flex-col gap-3 p-3 lg:flex-row lg:items-center">
        <label className="flex min-w-0 items-center gap-2">
          <span className="caps shrink-0">Showing</span>
          <select
            className="input min-w-0 max-w-[26rem]"
            value={finding}
            onChange={(e) => go("rows", id, e.target.value)}
          >
            <option value="all">All affected rows</option>
            {data.findings.map((f) => (
              <option key={f.index} value={String(f.index)}>
                {f.message.length > 70 ? f.message.slice(0, 67) + "…" : f.message} ({fmt(f.count)})
              </option>
            ))}
          </select>
        </label>
        <label className="relative min-w-[200px] flex-1">
          <span className="sr-only">Search the rows shown</span>
          <Search size={16} className="pointer-events-none absolute left-3 top-[11px] text-muted" aria-hidden />
          <input className="input pl-9" placeholder="Search the rows shown" value={search} onChange={(e) => setSearch(e.target.value)} />
        </label>
        <div className="flex flex-wrap gap-2">
          {data.total > 0 && (
            <>
              <CopyButton text={message} label="Copy as a message" />
              <a className="btn-primary" href={api.rowsLink(id, finding)}>
                <Download size={16} aria-hidden />
                Download these rows
              </a>
            </>
          )}
        </div>
      </div>

      {data.total > 0 && (
        <div className="card mt-4 overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-line bg-soft">
                <th className="caps whitespace-nowrap px-4 py-2 font-semibold">Reason</th>
                <th className="caps whitespace-nowrap px-4 py-2 text-right font-semibold">Row</th>
                {data.columns.map((column, i) => (
                  <th key={column} className={`caps whitespace-nowrap px-4 py-2 font-semibold normal-case ${i === highlight ? "bg-crit-bg text-crit-ink" : ""}`}>
                    <span className="font-mono tracking-normal">{column}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visible.map((row) => (
                <tr key={row.row} className="border-b border-soft2 last:border-0 hover:bg-soft">
                  <td className="whitespace-nowrap px-4 py-2 text-sm2">
                    <span className="rounded-[4px] border border-crit-line bg-crit-bg px-2 py-0.5 text-crit-ink">{row.reason}</span>
                  </td>
                  <td className="tnum px-4 py-2 text-right font-mono text-sm2 text-muted">{row.row}</td>
                  {row.cells.map((cell, i) => (
                    <td
                      key={i}
                      className={`max-w-[22rem] truncate whitespace-nowrap px-4 py-2 font-mono text-sm2 ${
                        i === highlight ? "bg-crit-bg font-semibold text-crit-ink" : ""
                      }`}
                      title={cell}
                    >
                      {cell === "" ? <span className="text-muted">(empty)</span> : cell}
                    </td>
                  ))}
                </tr>
              ))}
              {visible.length === 0 && (
                <tr>
                  <td colSpan={data.columns.length + 2} className="px-4 py-6 text-muted">
                    No rows shown here match “{search}”.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
      {data.total > 0 && (
        <p className="mt-3 text-sm2 text-muted">
          “Row” is the row number in the file as a spreadsheet shows it, counting the header as row 1.
        </p>
      )}
    </Page>
  );
}
