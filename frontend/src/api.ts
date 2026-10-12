// Everything the page asks of the local Python process.

export type Level = "problem" | "warning" | "note";
export type Verdict = "ok" | "warnings" | "problems";

export interface Finding {
  index: number;
  level: Level;
  code: string;
  category: string;
  column: string;
  message: string;
  count: number;
  examples: string[];
  why: string;
  key: string;
  has_rows: boolean;
}

export interface CheckResult {
  id: string;
  name: string;
  dataset: string;
  verdict: Verdict;
  headline: string;
  rows: number;
  columns: number;
  compared_with: string | null;
  has_baseline: boolean;
  problems: number;
  warnings: number;
  notes: number;
  affected_rows: number;
  clean_columns: string[];
  findings: Finding[];
  hidden: number;
  seconds: number;
  sample: boolean;
}

export interface SheetChoice {
  needs_sheet: true;
  upload: string;
  sheets: string[];
  file: string;
}

export interface HistoryEntry {
  id: string;
  when: string;
  dataset: string;
  file: string;
  verdict: Verdict;
  headline: string;
  problems: number;
  warnings: number;
  rows: number;
  compared_with: string | null;
  open?: boolean;
}

export interface AppState {
  version: string;
  home: string;
  recent: HistoryEntry[];
  datasets: number;
  max_mb: number;
}

export interface RowsPage {
  title: string;
  file: string;
  total: number;
  shown: number;
  file_rows: number;
  columns: string[];
  highlight: string | null;
  rows: { row: string; reason: string; cells: string[] }[];
  findings: { index: number; message: string; count: number }[];
}

export interface ColumnNote {
  name: string;
  holds: string;
  checks: string[];
  checked: boolean;
}

export interface Preview {
  name: string;
  file: string;
  replaces: boolean;
  rows: number;
  problems: number;
  warnings: number;
  columns: ColumnNote[];
}

export interface DatasetSummary {
  key: string;
  name: string;
  damaged: boolean;
  learned_from?: string;
  learned_on?: string;
  rows?: number;
  columns?: number;
  checks: number;
  last: HistoryEntry | null;
}

export interface DatasetDetail {
  key: string;
  name: string;
  learned_from: string;
  learned_on: string;
  rows: number;
  path: string;
  columns: ColumnNote[];
  rules: { column: string; rule: string }[];
  ignored: string[];
  history: HistoryEntry[];
}

const token = document.querySelector<HTMLMetaElement>('meta[name="pdq-token"]')?.content ?? "";

const STOPPED = "PyDataQuality has stopped. Run pdq ui again in your terminal, then reload this page.";

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      ...init,
      headers: { "X-PDQ-Token": token, ...(init?.headers ?? {}) },
    });
  } catch {
    throw new Error(STOPPED);
  }
  let data: unknown = null;
  try {
    data = await response.json();
  } catch {
    /* handled below */
  }
  if (!response.ok) {
    const message = (data as { error?: string } | null)?.error;
    throw new Error(message || "The request failed. Try again.");
  }
  return data as T;
}

const post = <T>(path: string, body: unknown = {}) =>
  call<T>(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

const q = (params: Record<string, string>) => new URLSearchParams(params).toString();

export const api = {
  state: () => call<AppState>("/api/state"),
  check: (file: File) =>
    call<CheckResult | SheetChoice>(`/api/check?${q({ name: file.name })}`, { method: "POST", body: file }),
  checkSheet: (upload: string, sheet: string) => post<CheckResult>("/api/check-sheet", { upload, sheet }),
  sample: () => post<CheckResult>("/api/sample"),
  result: (id: string) => call<CheckResult>(`/api/result?${q({ id })}`),
  rows: (id: string, finding: string) => call<RowsPage>(`/api/rows?${q({ id, finding })}`),
  preview: (id: string) => call<Preview>(`/api/preview?${q({ id })}`),
  accept: (id: string, name: string, skip: string[]) =>
    post<{ dataset: string; message: string }>("/api/accept", { id, name, skip }),
  ignore: (id: string, key: string) => post<CheckResult>("/api/ignore", { id, key }),
  datasets: () => call<{ datasets: DatasetSummary[] }>("/api/datasets"),
  dataset: (key: string) => call<DatasetDetail>(`/api/dataset?${q({ key })}`),
  unignore: (dataset: string, key: string) => post<DatasetDetail>("/api/unignore", { dataset, key }),
  deleteDataset: (dataset: string) => post<{ deleted: string }>("/api/delete-dataset", { dataset }),
  forgetEverything: () => post<{ removed: number }>("/api/forget-everything"),
  // Downloads are plain links, so the token travels in the address.
  rowsLink: (id: string, finding: string) => `/download/rows?${q({ id, finding, t: token })}`,
  reportLink: (id: string) => `/download/report?${q({ id, t: token })}`,
};

export function isSheetChoice(value: CheckResult | SheetChoice): value is SheetChoice {
  return (value as SheetChoice).needs_sheet === true;
}
