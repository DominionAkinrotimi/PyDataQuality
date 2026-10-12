# UI plan

This is the plan for the PyDataQuality app: the page that opens when someone runs `pdq ui`. It lists every screen, what is on it, what it does, and the order to build them in.

## What the UI is for

One job: a person who has just received a data file finds out whether they can use it, and what to do if they cannot. Everything on screen serves that. The UI is the same engine as `pdq check`, for people who do not use a terminal.

**Who uses it.** Analysts, finance and operations staff, researchers, and anyone who is sent spreadsheets or exports by other people. Assume they know Excel and do not know Python.

**Where it runs.** On the user's own computer, in their browser, served from `127.0.0.1`. There are no accounts, no sign-in and no server to host. Files are never uploaded to the internet. This is a product decision as well as a technical one: it is the main reason to choose this over pasting a file into an online tool.

## Rules every screen follows

1. **Answer first.** The verdict is the largest thing on the result screen. Detail sits below it.
2. **Plain words.** "15 dates are in the future", never "future_dates: 15". No statistics terms unless the user asks why.
3. **Every finding leads to an action.** See the rows, download them, or say "this is fine".
4. **Never a dead end.** Every error says what happened and what to do next, in one or two sentences.
5. **Say what stays private.** The line "The file stays on this computer" appears wherever a file is chosen.
6. **One main button per screen.** Other actions are quieter.
7. **Works with a keyboard and a screen reader.** Visible focus, real buttons and links, colour never the only signal (every verdict has a word and an icon), text contrast of at least 4.5:1, readable at 400 px wide.

## Screens at a glance

There are **8 screens in the app** and **1 public page** outside it. Three exist today in a basic form.

| # | Screen | What it is for | Status |
|:--|:--|:--|:--|
| 1 | Check | Choose a file to check | Built (basic) |
| 2 | Result | The verdict and the findings | Built (basic) |
| 3 | Affected rows | See and download the rows behind a finding | To build |
| 4 | Save as normal | Review what was learned before saving it | To build |
| 5 | My datasets | Every kind of file the user has saved, with its last result | To build |
| 6 | Dataset | History, what normal looks like, and the user's rules for one dataset | To build |
| 7 | Summary to share | One page to send to whoever produced the file | Built |
| 8 | Help and privacy | How it works, what the words mean, where data goes | To build |
| 9 | Public landing page | Explains the product to someone who has never seen it | To build |

Navigation is a single top bar on screens 1 to 6 and 8: **Check · My datasets · Help**. The product name on the left returns to Check.

```
Check (1) ──choose file──> Result (2) ──a finding──> Affected rows (3)
   │                          │  ├──"remember as normal"──> Save as normal (4) ──> Dataset (6)
   │                          │  └──"summary to share"────> Summary (7, downloaded file)
My datasets (5) ──one dataset──> Dataset (6) ──a past check──> Result (2)
Help (8) is reachable from every screen.
```

---

## 1. Check

**Purpose.** Start a check. This is the home screen.

**Content**

- Heading: "Is this file safe to use?"
- One line under it: "Drop in a spreadsheet or CSV. You get a plain answer in a few seconds."
- A large drop area: "Drop a file here, or click to choose one. CSV, Excel, JSON or Parquet."
- The privacy line: "The file stays on this computer. Nothing is uploaded to the internet."
- Recent checks (up to 5): file name, verdict, when. Each opens its result.
- First-time users see an extra link: "Try it with a sample file", which checks a built-in messy file so they see a real result before using their own data.

```
┌──────────────────────────────────────────────────────────────┐
│ PyDataQuality            Check · My datasets · Help          │
├──────────────────────────────────────────────────────────────┤
│  Is this file safe to use?                                   │
│  Drop in a spreadsheet or CSV. A plain answer in seconds.    │
│  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐   │
│  │              Drop a file here                         │   │
│  │   or click to choose one. CSV, Excel, JSON, Parquet   │   │
│  └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘   │
│  The file stays on this computer. Nothing is uploaded.       │
│  Try it with a sample file                                   │
│                                                              │
│  RECENT                                                      │
│  ✖ orders_november.csv     Not safe to use     today 09:14   │
│  ✓ orders_october.csv      Looks like last time   3 Oct      │
└──────────────────────────────────────────────────────────────┘
```

**Actions.** Drop or choose a file (goes to Result). Open a recent check. Try the sample.

**States**

| State | What the user sees |
|:--|:--|
| Checking | The drop area shows "Checking orders.csv…" with a progress line. Choosing another file is disabled until it finishes. |
| Wrong file type | "This looks like a PDF. PyDataQuality reads CSV, Excel, JSON and Parquet files." |
| Cannot be read | "Could not read orders.xlsx. It may be open in Excel, password protected or damaged. Close it and try again." |
| Too large | "This file is larger than 300 MB. Use the `pdq check` command for big files." with a link to Help. |
| Excel file with several sheets | A small chooser: "This workbook has 3 sheets. Which one?" (today the first sheet is used silently) |
| App closed | "The check could not run. Is the pdq window still open?" |

**Uses.** `load_file`, `check`. Recent checks need the history store described under screen 6.

---

## 2. Result

**Purpose.** Tell the user whether the file can be used, and why.

**Content**

- **Verdict banner**, one of six, with an icon and a count:

  | | With an earlier file to compare | First time |
  |:--|:--|:--|
  | Problems | ✖ Not safe to use | ✖ Problems found |
  | Warnings only | ! Check before use | ! Things to check |
  | Nothing found | ✓ Looks like last time | ✓ Nothing obviously wrong |

- **Context line:** "orders_november.csv: 1,200 rows, 8 columns. Compared with orders_september.csv." On a first check it says: "No earlier file to compare with, so this only covers what is wrong in any file."
- **Findings**, grouped as Problems, Warnings and Also noted. Each is one sentence with the column, the count and an example value.
- Each finding has two small links: **See the rows** (screen 3) and **Why?** (opens a short explanation in place).
- Each finding has a quiet menu: **This is fine** (ignore it for this dataset from now on).
- **Unchanged / No issues in:** the columns with nothing to report, so the user knows they were looked at.
- **Action bar**, in this order:
  1. First check, or changes are acceptable: **Remember this file as normal** (main button, goes to screen 4)
  2. **Download the affected rows**
  3. **Download a summary to share** (screen 7)
  4. **Check another file**

```
┌──────────────────────────────────────────────────────────────┐
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ ✖ Not safe to use                3 problems, 2 warnings  │ │
│ └──────────────────────────────────────────────────────────┘ │
│ orders_november.csv: 1,200 rows, 8 columns.                  │
│ Compared with orders_september.csv.                          │
│                                                              │
│ PROBLEMS                                                     │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ 1 column is missing: discount_code. It was in            │ │
│ │ orders_september.csv.                          Why?   ⋯  │ │
│ ├──────────────────────────────────────────────────────────┤ │
│ │ order_date has 15 dates in the future                    │ │
│ │ (latest: 2031-01-01).            See the rows · Why?  ⋯  │ │
│ └──────────────────────────────────────────────────────────┘ │
│ WARNINGS                                                     │
│ │ country has 1 value never seen before: "Togo" (10 rows). │ │
│                                                              │
│ UNCHANGED  customer_id, email, amount                        │
│                                                              │
│ [ These changes are fine. Make this the new normal ]         │
│   Download the affected rows · Summary to share · New check  │
└──────────────────────────────────────────────────────────────┘
```

**States**

| State | What the user sees |
|:--|:--|
| Nothing found | Green banner, the list of columns checked, and the suggestion to remember the file as normal if it is a first check. No empty "0 findings" tables. |
| No affected rows | "Download the affected rows" is hidden (for example when the only finding is a missing column). |
| More than 20 findings | The first 20 are shown, worst first, with "Show all 34". |
| A rule could not be understood | Shown as a problem, with a link to the rules tab so it can be fixed. |

**Uses.** `CheckResult` (`verdict`, `headline`, `findings`, `clean_columns`). The ignore action writes to the `ignore` list in the baseline.

---

## 3. Affected rows

**Purpose.** Show the actual rows behind a finding so the user can judge it and act on it.

**Content**

- Heading: the finding's sentence.
- A table of the affected rows, with the column in question highlighted and a **Reason** column first.
- A filter: **All findings** or one finding at a time.
- The first 200 rows are shown, with the total stated: "Showing 200 of 1,656 rows. Download to see all."
- **Download these rows** (CSV, with the reason column), and **Copy as a message** which puts a short ready-to-send note on the clipboard: "15 rows in orders_november.csv have an order_date in the future. The rows are attached."

**States.** No rows for this finding (structural findings such as a missing column): the screen says so and offers the other findings. Very wide tables scroll sideways inside their own box; the page itself never does.

**Uses.** `CheckResult.bad_rows()`, which already carries `_pdq_reason`.

---

## 4. Save as normal

**Purpose.** Let the user see what the tool learned before it becomes the standard later files are judged against. This is where trust is built, and where a wrong assumption gets corrected in one step.

**Content**

- Heading: "This is what a normal orders file looks like"
- A name for the dataset, pre-filled from the file name ("orders"), editable. Help text: "Later files with a similar name are compared with this one."
- One row per column, in plain words:

  | Column | What it holds | What will be checked next time |
  |:--|:--|:--|
  | order_id | numbers, no repeats | must stay unique |
  | status | text, 3 values: paid, pending, refunded | new values are flagged |
  | amount | numbers, 9.46 to 304.87 | values far outside this range are flagged |
  | discount_code | text, 71% empty | flagged if it becomes much emptier |

- Each row has a switch: **Check this column** (on by default). Turning it off stops comparisons for that column.
- If the file being saved has findings, a notice at the top: "This file has 2 warnings. Saving it means they count as normal from now on."
- Main button: **Save**. Secondary: **Cancel**.

**After saving.** Goes to the Dataset screen (6) with a confirmation: "Saved. The next orders file will be compared with this one."

**States.** A dataset with this name already exists: "You already have a dataset called orders. Replace what normal looks like, or save as a new dataset?" The user's own rules and ignored findings are always kept when replacing.

**Uses.** `baseline.learn`, `baseline.save`. Today accepting is a single click with no review; this screen replaces that.

---

## 5. My datasets

**Purpose.** One place to see every kind of file the user checks regularly and how the last one did.

**Content**

- A list, most recently checked first. Each row: dataset name, last file checked, last verdict (icon and words), when, and how many checks so far.
- A search box once there are more than 10.
- Each row opens the Dataset screen.

**States.** Empty: "Nothing saved yet. Check a file and choose 'Remember this file as normal'. After that, each new version of it is compared automatically." with a button to Check.

**Uses.** The baseline files in `~/.pydataquality/baselines`, plus the history store.

---

## 6. Dataset

**Purpose.** Everything about one dataset. Three tabs.

**Tab: History**

- A timeline of past checks: date, file name, verdict, number of problems and warnings. Each opens its result (screen 2).
- A simple strip of the last 12 verdicts as coloured marks with labels, so a run of bad files is visible at a glance.
- Only summaries are stored. Past files and their rows are not kept, and the screen says so.

**Tab: What normal looks like**

- The same table as screen 4, read-only, with "Learned from orders_september.csv on 7 Oct 2026".
- **Update from a new file** (goes to Check, then screen 4).
- **Open the baseline file** for people who want to edit the YAML directly.

**Tab: Your rules**

- Existing rules as sentences: "price must be greater than 0", each with a remove button.
- **Add a rule** builds one from three choices, so nothing has to be typed from memory:

  ```
  [ column ▾ ]  [ must be greater than ▾ ]  [ 0        ]   [ Add ]
     price         must be unique
     order_id      must not be empty
     status        must be one of…
                   must be between… and…
                   must be on or after…
                   must be an email address
  ```

- **Findings you chose to ignore**, each with "Start flagging this again".

**Dataset actions.** Rename. Delete (asks once: "Delete orders and its history? Your data files are not touched.").

**Uses.** `baseline.load`/`save`, the `rules` and `ignore` sections, `baseline.rule_mask` to validate a rule before saving it. Needs a history store: one small JSON file per dataset holding the date, file name, verdict and counts of each check.

---

## 7. Summary to share

**Purpose.** One page the user sends to whoever produced the file. It is how the result leaves the app, and how other people first see the product.

**Content.** File name, date, verdict, the findings in the same words, and the footer "Checked with PyDataQuality. The check ran on the recipient's computer." It contains no row data, so it is safe to forward.

**Form.** A single self-contained HTML file with no outside links, so it opens anywhere and can be emailed. Available from the Result screen and from `pdq report`.

**To add.** An optional note field before downloading ("Hi Tunde, three things to fix before I can use this"), shown at the top of the page.

**Uses.** `webui.report_html`, `CheckResult.to_html()`.

---

## 8. Help and privacy

**Purpose.** Answer the questions people have before they trust a tool with their data.

**Content**

- **How it works**, in four steps with one line each: check, remember, check the next one, act.
- **What the verdicts mean**, the six from screen 2.
- **What it looks for**, the list from the README in the same words.
- **Where your data goes:** nowhere. The page runs on this computer. Files are read and then deleted from a temporary folder. What is saved: one small baseline file per dataset and a summary of each check, in a folder shown on the page, with a button to delete everything.
- **When it gets something wrong:** how to ignore a finding, how to add a rule, how to report a false alarm.
- **Using it from the command line or Python**, with links.

Static content. No search needed at this size.

---

## 9. Public landing page

Outside the app, hosted on GitHub Pages. One page whose job is to make the product's use clear in ten seconds to someone who has never heard of it.

- Headline: "Know whether a data file is safe to use."
- A 20-second recording of dropping a file on the page and getting a verdict.
- Three boxes: "Finds what the eye misses", "Remembers last month's file", "Stays on your computer".
- The install line, and "No terminal? Run `pdq ui`."
- Who it is for, and what it is not.
- Links to the docs and GitHub.

---

## Reliability and safety requirements for the UI

These apply to every screen and are part of "done".

- The server listens on `127.0.0.1` only, refuses requests addressed to any other host name, and requires a per-session token on every request that reads or changes anything. *(done)*
- Everything taken from a file (column names, values, file names) is escaped before it is shown. *(done; keep a test for each new screen)*
- Uploaded files go to a temporary folder and are deleted after reading. *(done)*
- A failed check never leaves the page stuck. The drop area resets and the error is shown in words. *(partly done; needs the specific messages in screen 1)*
- A damaged baseline file produces a plain message naming the file, never a stack trace. *(done for the command line; needs a screen message)*
- Nothing is fetched from the internet: no fonts, scripts or analytics. *(done)*
- History stores summaries only, never rows.
- Closing the terminal stops the app. The page then says the app has stopped and how to start it again.

## Build order

| Step | Screens | Why this order |
|:--|:--|:--|
| 1 | Finish 1 and 2: error messages, "Why?" and "This is fine" on findings, sample file, sheet chooser | The first minute decides whether anyone stays |
| 2 | 3 Affected rows | The most asked-for next step after a verdict |
| 3 | 4 Save as normal | Makes the baseline understandable, which the comparison depends on |
| 4 | 8 Help and privacy, 9 landing page | Needed before telling people about it |
| 5 | 5 My datasets, 6 Dataset (History, then Normal, then Rules) | Rewards repeat use; needs the history store |
| 6 | Note field on 7 | Small, improves sharing |

Steps 1 to 4 make a version worth showing to the people who answered the questionnaire. Step 5 is what turns a one-off check into a habit.

## Not in this plan

Accounts and sign-in, a hosted version, team sharing of baselines, scheduled or watched folders, charts and dashboards, editing or fixing data inside the app, and connecting to databases. Each could come later. None is needed to find out whether people use the product.

## How we will know the UI works

- A new user gets from opening the page to a verdict on their own file in under one minute, without help.
- In a five-person test, every person can say in their own words what the verdict means and what they would do next.
- At least 3 in 10 users who check one file check a second within 14 days.
- Fewer than one finding per clean file that the user marks "This is fine".
