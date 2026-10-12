# Quickstart

Five minutes from install to a checked file.

## 1. Install

```bash
pip install pydataquality
```

You need Python 3.8 or newer. CSV, Excel and JSON work straight away. For Parquet files also run `pip install pyarrow`.

## 2. Check a file

Pick whichever suits you. All three run the same checks.

**In the browser, no commands after this one**

```bash
pdq ui
```

A page opens. Drop your file on it.

**In the terminal**

```bash
pdq check customers.csv
```

**In Python or a notebook**

```python
import pydataquality as pdq

result = pdq.check("customers.csv")   # or pdq.check(df)
print(result)
```

You get a verdict and a short list, worst first:

```
✖ PROBLEMS FOUND   3 problems, 2 warnings
  customers.csv: 5,150 rows, 7 columns. No earlier file to compare with.

PROBLEMS
  1  150 rows are exact copies of another row.
  2  age has 21 impossible values: "999", "-5". An age should be between 0 and 120.
  3  signup_date has 15 dates in the future (latest: 2031-01-01).

WARNINGS
  4  country has 3 spellings of the same value: "Nigeria", "NIGERIA", "nigeria ".
  5  email has 31 values that are not email addresses, e.g. "not-an-email".
```

A file with nothing wrong says `NOTHING OBVIOUSLY WRONG`.

## 3. Get the rows to fix

```bash
pdq rows customers.csv
```

This saves `customers_problem_rows.csv`. Its last column, `_pdq_reason`, says why each row is listed. In the browser, use **Download the affected rows**.

## 4. Remember what normal looks like

When a file is good, tell PyDataQuality:

```bash
pdq accept customers.csv
```

It saves a small description of the file: its columns, types, allowed values and ranges. You do not write any rules.

## 5. Check the next one

Next week or next month, when a new version arrives:

```bash
pdq check customers_november.csv
```

It is compared with the one you accepted. You are told about missing or new columns, far fewer or more rows, values never seen before, numbers outside the usual range, and more. If nothing changed, you see `LOOKS LIKE LAST TIME`.

If a change is fine, run `pdq accept` on the new file to make it the new normal.

## 6. Send the result to someone

```bash
pdq report customers_november.csv
```

This writes one HTML file you can email to whoever produced the data.

## Next steps

- [User guide](user_guide.md): your own rules, silencing a finding, using it in a scheduled job, troubleshooting
- [API reference](api.md): everything available from Python
- [UI plan](ui-plan.md): what the browser app does today and what is planned
