# Security

## How PyDataQuality handles your data

- It runs entirely on your computer. It makes no network requests and has no account, telemetry or update check.
- `pdq ui` serves its page on `127.0.0.1` only. It refuses requests addressed to any other host name and requires a per-session token on every request that reads or changes anything, so another website open in your browser cannot use it.
- Files dropped on the page are written to a temporary folder, read, and deleted. Only the most recent result is held in memory.
- Baseline files are read with a safe YAML loader. They hold column names, types, ranges, category values and row counts, not your rows.
- Everything taken from a data file is HTML-escaped before it is shown in the page or the shareable summary.
- “This is wrong” on a finding prepares a short report for you to send yourself, by email or on GitHub. It holds the kind of finding, the kind of column, row and column counts, and the version. It never holds a value from the file, a column name or a file name, and the app does not send it. A test fills a file with recognisable values and checks that none appear in any report.
- The project counts downloads using the totals that GitHub and PyPI publish, saved once a day to the `stats` branch. It has no information about who downloaded anything or how the app is used.

## What to be aware of

- A baseline for a category column lists that column's distinct values. If those are sensitive, keep the `.pdq` folder out of shared drives and version control.
- The shareable summary and the `--why` output include a few example values from the affected rows. Read a summary before forwarding it.
- `matches REGEX` rules run a regular expression you supply against your data. A badly written pattern can be slow. Only use baselines and rules from people you trust.
- `pdq ui` is built for one person on their own computer. Do not expose its port to a network.

## Reporting a vulnerability

Please do not open a public issue. Email contact.dominionakinrotimi@gmail.com with a description and steps to reproduce. You will get a reply within 7 days.
