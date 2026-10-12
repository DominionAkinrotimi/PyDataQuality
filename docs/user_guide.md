# User guide

PyDataQuality answers two questions about a data file: is anything wrong with it, and is it like the last one? This guide covers everyday use. For a first run, start with the [quickstart](quickstart.md).

## Choose how to use it

| You are | Use | Start with |
|:--|:--|:--|
| Sent spreadsheets and would rather not open a terminal | The browser page | `pdq ui` |
| Comfortable with a terminal | The command | `pdq check file.csv` |
| Working in Python or a notebook | The library | `pdq.check(df)` |
| Running a scheduled job or pipeline | The command's exit code | `pdq check file.csv \|\| exit 1` |

All four give the same findings.

## Reading a result

Every result starts with a verdict.

| Verdict | Means |
|:--|:--|
| `NOT SAFE TO USE` / `PROBLEMS FOUND` | At least one problem. Fix it or get a corrected file before relying on the data. |
| `CHECK BEFORE USE` / `THINGS TO CHECK` | Only warnings. Probably usable, but look at each one first. |
| `LOOKS LIKE LAST TIME` / `NOTHING OBVIOUSLY WRONG` | Nothing found. |

The first wording in each row appears when there is an earlier file to compare with. The second appears on a first check, when the tool can only look for things that are wrong in any file. It never says "safe" without something to compare against.

Findings come in three levels:

- **Problems** are almost certainly errors: a missing column, repeated IDs, impossible values.
- **Warnings** are worth a look: unusual spellings, invalid emails, a big change in row count.
- **Also noted** are facts that may be fine: a column that is 8% empty, a few large values. They never change the verdict.

To see how any finding was decided, add `--why`.

## Working with baselines

A baseline is what PyDataQuality remembers about a file you approved.

- **Create or replace one:** `pdq accept orders.csv`
- **Where it is kept:** in a `.pdq` folder next to your data, as `orders.yml`. From the browser page, in `.pydataquality/baselines` in your home folder.
- **How the next file finds it:** by name. Dates, month names, numbers and words like "final" or "copy" are ignored, so `orders_november_2026.csv` matches the baseline from `orders_october_2026.csv`. If the name does not match, the saved baseline with the most similar columns is used.
- **If the wrong one is picked:** name it yourself with `pdq accept orders.csv --as orders` and `pdq check file.csv --baseline orders`.
- **To check without comparing:** `pdq check file.csv --no-baseline`
- **To start again:** delete the `.yml` file.

The baseline is a short text file. You can open it, read it and edit it.

## Your own rules

Add a `rules` section to the baseline file:

```yaml
rules:
  price: [greater than 0]
  order_id: [unique, not empty]
  status: [one of paid, pending, refunded]
  ship_date: [on or after order_date]
```

| Rule | Meaning |
|:--|:--|
| `unique` | no value appears twice |
| `not empty` | no missing values |
| `greater than N`, `at least N`, `less than N`, `at most N` | numeric limits |
| `between A and B` | inclusive range |
| `one of a, b, c` | allowed values, ignoring capital letters |
| `is email`, `is date` | format checks |
| `on or after X`, `on or before X`, `after X`, `before X` | X is a date, another column, or `today` |
| `not in the future` | dates up to now |
| `matches REGEX` | a full regular-expression match |

Rows that break a rule are reported as problems. If a rule is mistyped, you are told. It is never skipped silently.

To try a rule once without editing anything:

```bash
pdq check orders.csv --rule "price: greater than 0"
```

## Silencing a finding

If a finding is correct but you have decided it is fine, find its key with `--why` (for example `spelling:country`) and add it to the baseline:

```yaml
ignore:
  - spelling:country
```

The result then says how many findings were hidden, so nothing disappears without trace. Your `rules` and `ignore` sections are kept when you run `pdq accept` again.

## Looking at one thing

```bash
pdq check orders.csv --column price          # one column
pdq check orders.csv --only duplicates       # one kind of finding
```

## In a scheduled job or pipeline

`pdq check` exits with:

| Code | Meaning |
|:--|:--|
| 0 | nothing found |
| 1 | warnings only |
| 2 | problems |
| 3 | the file or its baseline could not be read |

```bash
# Stop on problems, continue on warnings
pdq check incoming/orders.csv
if [ $? -ge 2 ]; then exit 1; fi
```

For machine-readable output use `--json`.

## In Python

```python
import pydataquality as pdq

result = pdq.check(df, baseline="baselines/orders.yml",
                   rules={"price": ["greater than 0"]})

if not result:                       # a result is true only when nothing was found
    print(result.headline)
    for finding in result.problems:
        print(finding.column, finding.message)
    result.bad_rows().to_csv("to_fix.csv", index=False)
```

See the [API reference](api.md).

## Privacy and safety

- Everything runs on your computer. PyDataQuality makes no network requests and has no account or telemetry.
- `pdq ui` serves its page on `127.0.0.1`, which only your own computer can reach. It refuses requests from other sites open in your browser.
- Files dropped on the page are read and then deleted from a temporary folder. Only a small baseline file is kept, and only if you ask.
- The summary from `pdq report` contains the findings and example values, not your rows. Read it before forwarding if the examples could be sensitive.

## Troubleshooting

**"Could not read file.xlsx"**
The file may be open in Excel, password protected or damaged. Close it and try again. For `.xls` files from old versions of Excel, save as `.xlsx` first.

**"Reading Parquet files needs one more package"**
Run `pip install pyarrow`.

**The columns look wrong, or everything is in one column**
The file probably has title rows above the header. Remove them, or save the sheet as CSV with the header on the first line. Separators `,` `;` tab and `|` are detected automatically.

**Only the first sheet of my workbook was checked**
That is the current behaviour. Save the sheet you need as its own file.

**It compared with the wrong earlier file**
Use `--baseline NAME`, or `--no-baseline` to skip the comparison. See "Working with baselines" above.

**"The baseline file could not be read"**
The `.yml` file was damaged, usually by a hand edit. Fix the edit, or delete the file and run `pdq accept` again.

**It flagged something that is fine**
Run `pdq accept` if the whole file is the new normal, or add the finding to the `ignore` list. If it is a false alarm on data that is plainly correct, please [report it](https://github.com/DominionAkinrotimi/PyDataQuality/issues) with a small example.

**The file is very large**
Files are read into memory, so a file close to the size of your computer's memory will fail or be very slow. For files of several gigabytes, check a sample: `pdq.check(pdq.sample_large_dataset("big.csv", n_samples=100000))`.

**`pdq` is not recognised**
Use `python -m pydataquality.pdq_cli check file.csv`, or make sure Python's scripts folder is on your PATH.

## The profiling interface

The original interface for a detailed statistical profile of one DataFrame is still included: `analyze_dataframe`, `generate_report`, `create_visual_report`, `compare_drift`, and the `pydataquality` command. It is documented in the [API reference](api.md).
