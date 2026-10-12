# PyDataQuality

**Know whether a data file is safe to use, and what changed since the last one. One command, nothing to configure.**

Someone sends you a spreadsheet or a CSV. Before you build a report on it, you want to know two things: is anything wrong with it, and is it like the one they sent last time? PyDataQuality answers both in plain language, on your own computer.

```
$ pdq check orders_november.csv

✖ NOT SAFE TO USE   3 problems, 5 warnings
  orders_november.csv: 1,200 rows, 8 columns. Compared with orders_september.csv.

PROBLEMS
  1  1 column is missing: discount_code. It was in orders_september.csv.
  2  order_id had no repeats last time. Now 1 value appears more than once, e.g. "7100".
  3  order_date has 15 dates in the future (latest: 2031-01-01).

WARNINGS
  4  The file has 1,200 rows. Last time it had 3,000 (60% fewer).
  5  amount values have shifted. The typical value was 54.725, now it is 119.58.
  6  country has 1 value never seen before: "Togo" (10 rows).
  7  status has 1 value never seen before: "chargeback" (10 rows).
  8  1 new column not seen before: channel.

UNCHANGED  customer_id, email

Next:  pdq rows orders_november.csv     save the affected rows with reasons
       pdq accept orders_november.csv   this is fine, make it the new normal
```

Your data never leaves your machine. There is no account and no server.

## Install

```bash
pip install pydataquality
```

Python 3.8 or newer. Reads CSV, TSV, Excel, JSON and Parquet (Parquet needs `pip install pyarrow`).

## How it works

### 1. Check a file

```bash
pdq check customers.csv
```

The first time, there is nothing to compare with, so PyDataQuality looks for what is wrong in any file and what is wrong for the kind of column it is looking at:

| It finds | Example message |
|:--|:--|
| Exact duplicate rows | `150 rows are exact copies of another row.` |
| IDs that repeat | `order_id should be unique, but 2 values appear more than once.` |
| Impossible values | `age has 21 impossible values: "999", "-5". An age should be between 0 and 120.` |
| Dates in the future | `signup_date has 15 dates in the future (latest: 2031-01-01).` |
| Mixed or broken dates | `visit_date mixes 2 date formats. Most look like 2024-01-31, but 3 rows look like "05/01/2026".` |
| Invalid emails | `email has 31 values that are not email addresses, e.g. "not-an-email".` |
| One value spelled several ways | `country has 3 spellings of the same value: "Nigeria", "NIGERIA", "nigeria ".` |
| Numbers stored as text | `amount is mostly numbers, but 1 value is not: "N/A".` |
| Wildly out-of-range numbers | `y has 2 values wildly outside the usual range (most rows are between 4.72 and 6.54): "58.9", "31.8".` |
| Empty or mostly empty columns | `deck is empty in 688 rows (77%).` |

It works out what each column is (an identifier, a date, an email, a category, a number) before judging it, so it does not, for example, run outlier detection on ID numbers. It is deliberately quiet: a clean file gets `NOTHING OBVIOUSLY WRONG`.

Without an earlier file it never says "safe", because it cannot know what normal looks like yet.

### 2. Tell it what normal looks like

```bash
pdq accept customers.csv
```

This saves a small, readable file (`.pdq/customers.yml`, next to your data) describing the columns, their types, allowed values, ranges and how often they are empty. You write no rules.

### 3. Check the next one

```bash
pdq check customers_november.csv
```

The baseline is found automatically: dates, month names and words like "final" or "copy" in the file name are ignored, so `customers_november.csv` is compared with what was learned from `customers_october.csv`. Now it also reports:

- columns that disappeared, appeared or changed type
- far fewer or far more rows than last time
- a column that used to be unique and now repeats
- category values never seen before
- numbers outside the range seen before, or whose distribution has shifted
- a column that is suddenly much emptier
- the very same file sent again

When a difference is fine, run `pdq accept` on the new file to make it the new normal.

### 4. Act on it

```bash
pdq rows customers_november.csv
```

Saves the affected rows to `customers_november_problem_rows.csv` with a `_pdq_reason` column saying why each row is there. Send that back to whoever produced the file.

### Prefer not to use a terminal?

```bash
pdq ui
```

A page opens in your browser. Drop a file on it and you get the same verdict, with buttons to download the affected rows, download a summary, or remember the file as normal. The page is served from your own computer and only answers to it. Close the terminal window to stop it.

To send someone the result:

```bash
pdq report customers_november.csv
```

This writes a single HTML file you can email. In a notebook, `pdq.check(df)` displays the same summary.

## Your own rules

Open the baseline file and add a `rules` section. Rules are written the way you would say them:

```yaml
rules:
  price: [greater than 0]
  order_id: [unique, not empty]
  status: [one of paid, pending, refunded]
  ship_date: [on or after order_date]
  email: [is email]
```

| Rule | Meaning |
|:--|:--|
| `unique` | no value appears twice |
| `not empty` | no missing values |
| `greater than N`, `at least N`, `less than N`, `at most N` | numeric limits |
| `between A and B` | inclusive range |
| `one of a, b, c` | allowed values (capital letters ignored) |
| `is email`, `is date` | format checks |
| `on or after X`, `on or before X`, `after X`, `before X` | X is a date, another column, or `today` |
| `not in the future` | dates up to now |
| `matches REGEX` | full regular-expression match |

A rule that cannot be understood is reported as a problem. It is never skipped silently.

Try a rule without editing anything:

```bash
pdq check orders.csv --rule "price: greater than 0"
```

To silence a finding you have decided is fine, add its key (shown by `--why`) to an `ignore` list in the baseline:

```yaml
ignore:
  - spelling:country
```

Your `rules` and `ignore` sections are kept when you run `pdq accept` again.

## Command reference

```
pdq check FILE      check a file ("pdq FILE" does the same)
    --why               explain how each finding was decided
    --column NAME       only show findings for this column
    --only KIND         only show one kind of finding, e.g. duplicates
    --rule "COL: RULE"  add a check for this run
    --baseline PATH     compare with a specific baseline
    --no-baseline       do not compare with any earlier file
    --json              machine-readable output
pdq accept FILE     remember this file as normal
    --as NAME           dataset name, if the file name is not a good guide
pdq rows FILE       save the affected rows, with reasons
    -o PATH             where to save
pdq report FILE     write a one-page HTML summary to share
    -o PATH             where to save
pdq ui              open the drag-and-drop page in your browser
    --port N            use a specific port
    --no-browser        print the address without opening it
```

### In a pipeline or scheduled job

`pdq check` exits with `0` when nothing was found, `1` for warnings, `2` for problems and `3` if the file could not be read:

```bash
pdq check incoming/orders.csv || exit 1
```

## In Python

```python
import pydataquality as pdq

result = pdq.check("orders_november.csv")   # or pdq.check(df)

result.verdict        # 'ok', 'warnings' or 'problems'
result.headline       # 'NOT SAFE TO USE'
print(result)         # the same text as the command line

for finding in result.problems:
    print(finding.column, finding.message, finding.count)

bad = result.bad_rows()                     # DataFrame with a _pdq_reason column
html = result.to_html()                     # the shareable summary page
pdq.accept("orders_november.csv")           # make it the new normal

# With a DataFrame, say where the baseline lives
pdq.accept(df, path="baselines/orders.yml")
result = pdq.check(new_df, baseline="baselines/orders.yml",
                   rules={"price": ["greater than 0"]})
```

## What it is not

PyDataQuality checks files and DataFrames that fit in memory. It is not a warehouse monitoring platform, and it does not replace a full validation framework. If you need a managed suite of expectations across a data platform, look at Great Expectations, Soda or Pandera. If you want an exhaustive statistical profile, look at ydata-profiling (now fg-data-profiling). Use PyDataQuality when you have a file and need a quick, trustworthy answer.

## Profiling API

The original profiling interface is still included for a detailed look at a single DataFrame.

```python
analyzer = pdq.analyze_dataframe(df, name="My Dataset")

analyzer.issues                                   # QualityIssue objects with severity
analyzer.get_problematic_rows("age", "outliers")  # the rows behind an issue
pdq.generate_report(analyzer, output_path="quality_report.html")
pdq.create_visual_report(analyzer, save_path="charts/")

# Compare two datasets (Population Stability Index and KS test)
drift = pdq.compare_drift(pdq.analyze_dataframe(train_df), pdq.analyze_dataframe(new_df))

# A prompt to paste into an AI assistant. Raw values from columns that look
# like personal data are left out unless you pass include_values=True.
from pydataquality import QualityReportGenerator
prompt = QualityReportGenerator(analyzer).generate_ai_remediation_prompt()
```

```bash
pydataquality data.csv --report html --visualize
pydataquality data.csv --rules rules.yaml --fail-on critical
```

See the [quickstart](docs/quickstart.md), [API reference](docs/api.md) and [examples](examples/).

## Research paper

The profiling kernel and drift statistics are described in a preprint:

> **PyDataQuality: An Actionable, Lightweight Data Profiling and Distribution Drift Detection Framework for Production Machine Learning Pipelines**. Dominion Akinrotimi, 2026.

[Read the paper (PDF)](https://github.com/DominionAkinrotimi/PyDataQuality/blob/main/paperwriting/final%20paper%20in%20pdf/PyDataQuality.pdf) · [Technical study guide](STUDY_GUIDE.md)

## Contributing

```bash
git clone https://github.com/DominionAkinrotimi/pydataquality.git
cd pydataquality
pip install -e ".[dev]"
pytest
```

Bug reports are most useful with a small file that shows the problem, especially a false alarm on data that is actually fine.

## License

MIT. See [LICENSE](LICENSE).
