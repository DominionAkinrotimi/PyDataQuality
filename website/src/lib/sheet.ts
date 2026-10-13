/**
 * The sheet shown in the hero, shared by the 3D scene and its static poster so both draw the same
 * file. It mirrors the built-in sample (sample_customers.csv): seven columns, and the kinds of
 * finding the app reports for it.
 */
export const COLS = 7;
export const ROWS = 12; // the first row is the header

export type Flag = "problem" | "warning";

/** Relative column widths: customer_id, full_name, age, email, country, signup_date, monthly_spend. */
const COL_WIDTHS = [0.8, 1.25, 0.55, 1.6, 0.9, 1.05, 0.95];

const FLAGGED: Record<string, Flag> = {
  // age: two impossible values
  "3,2": "problem",
  "8,2": "problem",
  // signup_date: dates in the future
  "5,5": "problem",
  "10,5": "problem",
  // country: one value spelled three ways
  "2,4": "warning",
  "6,4": "warning",
  // email: not an email address
  "9,3": "warning",
  // monthly_spend: far outside the usual range
  "4,6": "warning",
};
// one row that is an exact copy of the row above it
for (let c = 0; c < COLS; c++) FLAGGED[`7,${c}`] = "problem";

/** Deterministic 0..1 value per cell, used for the length of the "text" drawn in it. */
function cellSeed(row: number, col: number): number {
  const x = Math.sin(row * 127.1 + col * 311.7) * 43758.5453;
  return x - Math.floor(x);
}

export interface Cell { row: number; col: number; x: number; y: number; w: number; h: number; flag?: Flag; fill: number }

/** Cell rectangles in a unit space: x across 0..1, y down 0..1. */
export function layoutCells(): Cell[] {
  const total = COL_WIDTHS.reduce((a, b) => a + b, 0);
  const cells: Cell[] = [];
  for (let row = 0; row < ROWS; row++) {
    let x = 0;
    for (let col = 0; col < COLS; col++) {
      const w = COL_WIDTHS[col] / total;
      // the copied row repeats the text lengths of the row above it
      const seedRow = row === 7 ? 6 : row;
      cells.push({ row, col, x, y: row / ROWS, w, h: 1 / ROWS, flag: row === 0 ? undefined : FLAGGED[`${row},${col}`], fill: 0.35 + cellSeed(seedRow, col) * 0.5 });
      x += w;
    }
  }
  return cells;
}

/** The verdict the app gives the sample file. Shown beside the sheet once the scan has passed. */
export const SAMPLE_VERDICT = {
  file: "sample_customers.csv",
  headline: "Problems found",
  summary: "3 problems and 4 warnings",
};
