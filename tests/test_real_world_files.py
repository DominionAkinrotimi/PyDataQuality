"""
Files as people actually receive them: a title block above the table, "--" for
an empty amount, a pair of columns where each row fills in only one, long
reference numbers and free-text descriptions.

The statement here is made up. It copies the layout of a real wallet statement
that produced false alarms in version 0.3.0, with none of its contents.
"""

import numpy as np
import pandas as pd
import pytest

import pydataquality as pdq
from pydataquality import semantic as sem
from pydataquality.checker import find_header_row
from pydataquality.standalone import either_or_columns

HEADINGS = ["Trans. Date", "Value Date", "Description", "Debit(N)", "Credit(N)", "Balance After(N)", "Channel", "Transaction Reference"]


def statement_rows(n=400, seed=3):
    """A made-up statement as rows of cells, title block included."""
    rng = np.random.default_rng(seed)
    people = ["ADA OBI", "Tunde Bello", "KEMI ADE", "living faith church", "Musa Sani"]
    notes = ["Offering", "offering", "bread", "Bread", "cash", "payment"]
    rows = [
        ["Wallet Account Statement", None, None, None, "Date Printed", "14 Jan 2026 08:57:40", None, None],
        ["Account Name", "EXAMPLE PERSON", "Account Number", "1234567890", "Address", "1 Example Street, Lagos", None, None],
        ["Account Type", "Wallet Account", "Period", "06 Jan 2020-13 Jan 2026", None, None, None, None],
        ["Opening Balance", "N0.00", "Total Debit", "N4,418,815.14", "Debit Count", 1621, None, None],
        ["Closing Balance", "N0.00", "Total Credit", "N4,418,815.14", "Credit Count", 1369, None, None],
        [None] * 8,
        HEADINGS,
    ]
    day = pd.Timestamp("2023-08-04 12:00:00")
    for i in range(n):
        day += pd.Timedelta(minutes=int(rng.integers(30, 3000)))
        amount = f"{rng.uniform(100, 30000):,.2f}"
        paid_in = bool(rng.random() < 0.45)
        description = f"Transfer {'from' if paid_in else 'to'} {rng.choice(people)} | Example Bank | 90{rng.integers(10**7, 10**8)} | {rng.choice(notes)}"
        reference = f"09FG{rng.integers(10**11, 10**12)}XQ" if i % 70 == 0 else str(rng.integers(10**17, 10**18))
        rows.append([
            day.strftime("%d %b %Y %H:%M:%S"), day.strftime("%d %b %Y"), description,
            "--" if paid_in else amount, amount if paid_in else "--", f"{rng.uniform(0, 90000):,.2f}", "Mobile", reference,
        ])
    return rows


@pytest.fixture
def statement_xlsx(tmp_path):
    path = tmp_path / "wallet_statement.xlsx"
    pd.DataFrame(statement_rows()).to_excel(path, index=False, header=False)
    return str(path)


@pytest.fixture
def statement_csv(tmp_path):
    path = tmp_path / "wallet_statement.csv"
    pd.DataFrame(statement_rows()).to_csv(path, index=False, header=False)
    return str(path)


# ------------------------------------------------------------ finding the table
def test_title_block_is_skipped_in_excel(statement_xlsx):
    df = pdq.load_file(statement_xlsx)
    assert list(df.columns) == HEADINGS
    assert df.attrs["header_row"] == 7
    assert len(df) == 400
    # rows are numbered as the spreadsheet numbers them: headings on row 7, data from row 8
    assert df.index[0] + 2 == 8


def test_title_block_is_skipped_in_csv(statement_csv):
    df = pdq.load_file(statement_csv)
    assert list(df.columns) == HEADINGS
    assert df.attrs["header_row"] == 7


def test_ordinary_file_is_read_exactly_as_before(tmp_path):
    path = tmp_path / "plain.csv"
    pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"], "amount": [1.5, 2.5, 3.5]}).to_csv(path, index=False)
    df = pdq.load_file(str(path))
    assert list(df.columns) == ["id", "name", "amount"]
    assert "header_row" not in df.attrs
    assert list(df.index) == [0, 1, 2]


def test_header_row_rules():
    table = [["id", "name", "amount"], [1, "a", 2.5], [2, "b", 3.5]]
    assert find_header_row(table) == 0
    assert find_header_row([["Report for March", None, None], [None, None, None]] + table) == 2
    # no headings anywhere: leave the first row alone and let the check say so
    assert find_header_row([["Totals", None, None], [1, "a", 2.5], [2, "b", 3.5]]) == 0
    # an all-text table gives no way to tell a heading from a row, so nothing is skipped
    assert find_header_row([["Title", None, None], ["city", "country", "team"], ["Lagos", "Nigeria", "A"]]) == 0
    # a first row that is already as wide as the table is always kept
    assert find_header_row([["2021", "2022", "2023"], [1, 2, 3], [4, 5, 6]]) == 0
    assert find_header_row([]) == 0


# ------------------------------------------------------------ what gets reported
def test_statement_is_quiet(statement_xlsx):
    result = pdq.check(statement_xlsx, baseline=False)
    assert result.problems == []
    assert result.warnings == []
    codes = {f.code for f in result.findings}
    assert codes == {"table_start"}
    start = [f for f in result.findings if f.code == "table_start"][0]
    assert "starts on row 7" in start.message
    for finding in result.findings:
        assert "Unnamed" not in finding.message


def test_statement_columns_are_understood(statement_xlsx):
    result = pdq.check(statement_xlsx, baseline=False)
    kinds = {str(k): v for k, v in result.kinds.items()}
    assert kinds["Trans. Date"] == sem.DATE
    assert kinds["Debit(N)"] == sem.NUMBER_AS_TEXT
    assert kinds["Credit(N)"] == sem.NUMBER_AS_TEXT
    assert kinds["Balance After(N)"] == sem.NUMBER_AS_TEXT
    # a long reference number is a label, not a quantity
    assert kinds["Transaction Reference"] in (sem.TEXT, sem.ID)
    assert kinds["Description"] in (sem.TEXT, sem.CATEGORY)


def test_dashes_count_as_empty_only_in_number_and_date_columns():
    df = pd.DataFrame({
        "debit": ["1,200.00", "--", "50.00", "-", "75.10", "N/A"] * 20,
        "posted": ["2024-01-31", "--", "2024-02-01", "2024-02-02", "n/a", "2024-02-03"] * 20,
        "grade": ["A", "-", "B", "--", "A", "B"] * 20,
    })
    cleaned = sem.blank_placeholders(df)
    assert cleaned["debit"].isna().sum() == 60
    assert cleaned["posted"].isna().sum() == 40
    assert cleaned["grade"].isna().sum() == 0  # here a dash may be a real value
    assert df["debit"].isna().sum() == 0  # the caller's table is not changed


def test_a_real_stray_word_in_a_number_column_is_still_reported():
    df = pd.DataFrame({"amount": ["10.50", "20.00", "--", "pending", "31.25", "18.00"] * 20})
    result = pdq.check(df, baseline=False)
    finding = [f for f in result.findings if f.code == "not_a_number"]
    assert finding and '"pending"' in finding[0].message and "--" not in finding[0].message


def test_either_or_columns_are_not_reported_as_empty():
    rng = np.random.default_rng(1)
    paid_in = rng.random(300) < 0.6
    df = pd.DataFrame({
        "ref": np.arange(300),
        "debit": np.where(paid_in, np.nan, 10.0),
        "credit": np.where(paid_in, 10.0, np.nan),
        "note": np.where(rng.random(300) < 0.6, None, "x"),
    })
    assert either_or_columns(df) == {"debit", "credit"}
    result = pdq.check(df, baseline=False)
    reported = {f.column for f in result.findings if f.code == "missing"}
    assert "debit" not in reported and "credit" not in reported
    assert "note" in reported  # an unpaired half-empty column is still reported


# ------------------------------------------------------------ spelling
def test_spelling_is_not_checked_in_free_text():
    df = pd.DataFrame({
        "order": np.arange(200),
        "description": [f"Transfer to SOMEONE {i % 40} | Example Bank | 1234567890 | {'Offering' if i % 2 else 'offering'}" for i in range(200)],
    })
    result = pdq.check(df, baseline=False)
    assert not [f for f in result.findings if f.code == "spelling"]


def test_spelling_message_shows_every_spelling_in_full():
    long_a, long_b = "Customer Support And Billing", "customer support and billing"
    df = pd.DataFrame({"team": [long_a] * 120 + [long_b] * 12 + ["Sales"] * 100})
    result = pdq.check(df, baseline=False)
    finding = [f for f in result.findings if f.code == "spelling"][0]
    assert f'"{long_a}"' in finding.message and f'"{long_b}"' in finding.message


# ------------------------------------------------------------ no headings at all
def test_file_without_headings_stops_with_one_clear_problem(tmp_path):
    path = tmp_path / "no_headings.csv"
    rows = [["Totals for the year", "", "", ""]] + [[f"name{i}", f"city{i % 5}", f"team{i % 3}", f"note{i}"] for i in range(50)]
    pd.DataFrame(rows).to_csv(path, index=False, header=False)
    result = pdq.check(str(path), baseline=False)
    assert [f.code for f in result.findings] == ["no_header"]
    assert result.verdict == "problems"
    assert "could not be found" in result.findings[0].message
    assert "Unnamed" not in result.findings[0].message


def test_one_missing_heading_is_still_only_a_warning():
    df = pd.DataFrame({"id": np.arange(60), "city": ["Lagos", "Accra", "Nairobi"] * 20, "Unnamed: 2": np.arange(60) * 1.5})
    result = pdq.check(df, baseline=False)
    header = [f for f in result.findings if f.code == "no_header"]
    assert header and header[0].level == "warning"
