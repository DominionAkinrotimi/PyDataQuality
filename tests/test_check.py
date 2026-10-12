"""Tests for pdq.check: first-run checks, baselines, rules and the command line."""

import io
import json

import numpy as np
import pandas as pd
import pytest

import pydataquality as pdq
from pydataquality import baseline as base
from pydataquality import semantic as sem
from pydataquality.pdq_cli import main as pdq_main

TODAY = "2026-10-07"


def make_orders(n=600, seed=0, start=1000):
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "order_id": np.arange(start, start + n),
            "customer_id": rng.integers(1, 80, n),
            "order_date": pd.date_range("2026-08-01", periods=n, freq="h").strftime("%Y-%m-%d"),
            "country": rng.choice(["Nigeria", "Ghana", "Kenya"], n),
            "status": rng.choice(["paid", "pending", "refunded"], n),
            "amount": rng.lognormal(4, 0.5, n).round(2),
            "email": [f"c{i}@shop.com" for i in rng.integers(1, 80, n)],
            "age": rng.integers(18, 70, n),
        }
    )


def codes(result):
    return {f.code for f in result.findings}


def finding(result, code):
    return next(f for f in result.findings if f.code == code)


# ---------------------------------------------------------------- semantics
@pytest.mark.parametrize(
    "column, expected",
    [
        ("order_id", sem.ID),
        ("customer_id", sem.NUMBER),  # repeats, so it is a reference not an identifier
        ("order_date", sem.DATE),
        ("country", sem.CATEGORY),
        ("amount", sem.NUMBER),
        ("email", sem.EMAIL),
    ],
)
def test_column_kinds(column, expected):
    assert sem.infer_kind(make_orders()[column], column) == expected


def test_numbers_stored_as_text_are_recognised():
    series = pd.Series(["1,200", "$45.50", "300", "N/A", "12"] * 10)
    assert sem.infer_kind(series, "amount") == sem.NUMBER_AS_TEXT


def test_name_tokens_split_camel_case():
    assert sem.name_tokens("OrderID") == {"order", "id"}
    assert "id" not in sem.name_tokens("paid")


# ------------------------------------------------------------- clean file
def test_clean_file_raises_no_alarm():
    result = pdq.check(make_orders(), today=TODAY)
    assert result.verdict == "ok"
    assert result.findings == []
    assert result.exit_code == 0
    assert result.headline == "NOTHING OBVIOUSLY WRONG"
    assert bool(result)


def test_long_tailed_numbers_are_not_called_extreme():
    df = pd.DataFrame({"income": np.random.default_rng(3).lognormal(10, 1, 5000)})
    assert pdq.check(df).findings == []


def test_reference_ids_that_repeat_are_not_flagged():
    assert "id_repeats" not in codes(pdq.check(make_orders(), today=TODAY))


# -------------------------------------------------------- first-run checks
def test_planted_problems_are_all_found():
    df = make_orders()
    df.loc[0, "age"] = 999
    df.loc[1, "age"] = -5
    df.loc[2:4, "email"] = "not-an-email"
    df.loc[5:7, "order_date"] = "2031-01-01"
    df.loc[8:20, "country"] = "nigeria "
    df["amount"] = df["amount"].astype(object)
    df.loc[30, "amount"] = "N/A"
    df = pd.concat([df, df.iloc[100:110]], ignore_index=True)

    result = pdq.check(df, today=TODAY)

    assert result.verdict == "problems" and result.exit_code == 2
    assert finding(result, "duplicates").count == 10
    assert finding(result, "impossible").count == 2
    assert finding(result, "bad_email").count == 3
    assert finding(result, "future_date").count == 3
    assert finding(result, "spelling").count == 13
    assert finding(result, "not_a_number").count == 1
    # Problems are listed before warnings
    levels = [f.level for f in result.findings]
    assert levels == sorted(levels, key=["problem", "warning", "note"].index)


def test_messages_are_plain_language():
    df = make_orders()
    df.loc[0, "age"] = 999
    message = finding(pdq.check(df, today=TODAY), "impossible").message
    assert "999" in message and "age" in message
    assert "IQR" not in message and "999.0" not in message


def test_due_dates_may_be_in_the_future():
    df = pd.DataFrame({"due_date": ["2031-01-01"] * 30, "created_at": ["2031-01-01"] * 30})
    result = pdq.check(df, today=TODAY)
    flagged = {f.column: f.level for f in result.findings if f.code == "future_date"}
    assert flagged == {"created_at": "problem"}


def test_mixed_date_formats():
    df = pd.DataFrame({"visit_date": ["2026-01-05"] * 40 + ["05/01/2026"] * 3 + ["soon"]})
    result = pdq.check(df, today=TODAY)
    assert finding(result, "mixed_dates").count == 3
    assert finding(result, "bad_date").count == 1


def test_near_unique_id_repeats_are_a_problem():
    df = make_orders()
    df.loc[5, "order_id"] = df.loc[6, "order_id"]
    result = pdq.check(df, today=TODAY)
    assert finding(result, "id_repeats").level == "problem"


def test_rare_extreme_value_is_flagged_once():
    df = make_orders()
    df.loc[0, "amount"] = 9_000_000
    result = pdq.check(df, today=TODAY)
    assert finding(result, "extreme").count == 1


def test_empty_file_and_empty_column():
    assert finding(pdq.check(make_orders().iloc[:0]), "no_rows").level == "problem"
    df = make_orders()
    df["notes"] = np.nan
    assert finding(pdq.check(df, today=TODAY), "empty_column").column == "notes"


def test_bad_rows_carry_reasons():
    df = make_orders()
    df.loc[0, "age"] = 999
    df.loc[0, "email"] = "nope"
    rows = pdq.check(df, today=TODAY).bad_rows()
    assert len(rows) == 1
    reason = rows.iloc[0][pdq.checker.REASON_COLUMN]
    assert "age: impossible" in reason and "email: bad email" in reason


# ----------------------------------------------------------------- baseline
@pytest.fixture
def folder(tmp_path):
    make_orders(seed=1).to_csv(tmp_path / "orders_september_2026.csv", index=False)
    make_orders(seed=2, start=5000).to_csv(tmp_path / "orders_october_2026.csv", index=False)
    return tmp_path


def test_dataset_name_ignores_dates_and_copies():
    assert base.dataset_name("Orders_November_2026 (1).csv") == "orders"
    assert base.dataset_name("sales-export-final-v2.xlsx") == "sales"
    assert base.dataset_name("2026-10.csv") == "2026_10"


def test_next_file_finds_the_baseline_and_passes(folder):
    path = pdq.accept(str(folder / "orders_september_2026.csv"))
    assert path.endswith("orders.yml")

    result = pdq.check(str(folder / "orders_october_2026.csv"), today=TODAY)
    assert result.has_baseline
    assert result.verdict == "ok", result.to_text()
    assert result.headline == "LOOKS LIKE LAST TIME"


def test_changes_since_the_baseline_are_reported(folder):
    pdq.accept(str(folder / "orders_september_2026.csv"))
    df = make_orders(n=200, seed=3, start=9000).drop(columns=["status"])
    df["amount"] = df["amount"] * 3
    df.loc[:9, "country"] = "Togo"
    df.loc[20, "order_id"] = df.loc[21, "order_id"]
    df["channel"] = "web"
    df.loc[:79, "age"] = np.nan
    target = folder / "orders_november_2026.csv"
    df.to_csv(target, index=False)

    result = pdq.check(str(target), today=TODAY)

    assert result.verdict == "problems"
    assert "status" in finding(result, "column_missing").message
    assert "channel" in finding(result, "column_new").message
    assert finding(result, "row_count").level == "warning"
    assert finding(result, "new_values").count == 10
    assert finding(result, "shifted").column == "amount"
    assert finding(result, "missing_jump").column == "age"
    assert finding(result, "not_unique").column == "order_id"
    assert "id_repeats" not in codes(result)  # not said twice
    assert "channel" not in result.clean_columns()


def test_same_file_sent_again(folder):
    september = str(folder / "orders_september_2026.csv")
    pdq.accept(september)
    assert "same_file" in codes(pdq.check(september, today=TODAY))


def test_type_change_is_a_problem(folder):
    pdq.accept(str(folder / "orders_september_2026.csv"))
    df = make_orders(seed=4, start=7000)
    df["amount"] = "about " + df["amount"].astype(str)
    target = folder / "orders_december_2026.csv"
    df.to_csv(target, index=False)
    result = pdq.check(str(target), today=TODAY)
    assert "used to hold numbers" in finding(result, "type_changed").message


def test_baseline_false_never_compares(folder):
    pdq.accept(str(folder / "orders_september_2026.csv"))
    assert not pdq.check(str(folder / "orders_october_2026.csv"), baseline=False).has_baseline


def test_user_sections_survive_re_accepting(folder):
    import yaml

    september = str(folder / "orders_september_2026.csv")
    path = pdq.accept(september)
    saved = base.load(path)
    saved["rules"] = {"amount": ["greater than 0"]}
    saved["ignore"] = ["same_file:(whole file)"]
    with open(path, "w", encoding="utf-8") as handle:
        yaml.safe_dump(saved, handle)

    pdq.accept(september)
    again = base.load(path)
    assert again["rules"] == {"amount": ["greater than 0"]}

    result = pdq.check(september, today=TODAY)
    assert "same_file" not in codes(result) and result.hidden == 1


def test_dataframe_with_explicit_baseline(tmp_path):
    path = pdq.accept(make_orders(seed=1), path=str(tmp_path / "orders.yml"))
    result = pdq.check(make_orders(seed=2, start=5000), baseline=path, today=TODAY)
    assert result.has_baseline and result.verdict == "ok"


# -------------------------------------------------------------------- rules
@pytest.mark.parametrize(
    "column, rule, broken",
    [
        ("amount", "greater than 0", 1),
        ("amount", "at least 0", 1),
        ("amount", "between 0 and 100000", 1),
        ("status", "one of paid, pending", None),
        ("status", "one of PAID, pending, refunded", 0),
        ("order_id", "unique", 0),
        ("email", "is email", 1),
        ("email", "not empty", 0),
        ("order_date", "is date", 0),
        ("order_date", "on or after 2026-08-01", 0),
        ("order_date", "before 2026-08-02", None),
        ("order_date", "not in the future", 0),
        ("ship_date", "on or after order_date", 2),
        ("order_id", r"matches \d{4}", 0),
    ],
)
def test_rules(column, rule, broken):
    df = make_orders(n=100)
    df.loc[0, "amount"] = -1
    df.loc[1, "email"] = "nope"
    df["ship_date"] = df["order_date"]
    df.loc[2:3, "ship_date"] = "2026-07-01"

    mask = base.rule_mask(df, column, rule)
    if broken is None:
        assert 0 < mask.sum() < len(df)
    else:
        assert mask.sum() == broken


def test_rule_violations_are_problems_and_typos_are_reported():
    df = make_orders(n=100)
    df.loc[0, "amount"] = -1
    result = pdq.check(
        df,
        rules={"amount": ["greater than 0", "wibble"], "nowhere": "unique"},
        today=TODAY,
    )
    messages = [f.message for f in result.findings if f.code == "rule"]
    assert len(messages) == 3
    assert any("1 row breaks your rule" in m for m in messages)
    assert any("could not be understood" in m for m in messages)
    assert any("no such column" in m for m in messages)
    assert result.exit_code == 2


def test_column_and_only_filters():
    df = make_orders()
    df.loc[0, "age"] = 999
    df.loc[1, "email"] = "nope"
    assert codes(pdq.check(df, columns=["age"], today=TODAY)) == {"impossible"}
    assert codes(pdq.check(df, only=["bad_email"], today=TODAY)) == {"bad_email"}


# ------------------------------------------------------------ command line
def run_cli(*args):
    out = io.StringIO()
    code = pdq_main([str(a) for a in args], out=out)
    return code, out.getvalue()


def test_cli_accept_then_check(folder):
    code, text = run_cli("accept", folder / "orders_september_2026.csv")
    assert code == 0 and "Saved what normal looks like" in text

    code, text = run_cli(folder / "orders_october_2026.csv")  # bare file means check
    assert code == 0 and "LOOKS LIKE LAST TIME" in text


def test_cli_exit_codes_and_json(folder):
    df = make_orders()
    df.loc[0, "age"] = 999
    bad = folder / "people.csv"
    df.to_csv(bad, index=False)

    code, text = run_cli("check", bad, "--json")
    payload = json.loads(text)
    assert code == 2 and payload["verdict"] == "problems"
    assert payload["findings"][0]["code"] == "impossible"

    code, text = run_cli("check", bad, "--rule", "age: less than 30", "--only", "rule")
    assert code == 2 and "your rule" in text and "impossible" not in text


def test_cli_rows_writes_reasons(folder):
    df = make_orders()
    df.loc[0, "age"] = 999
    bad = folder / "people.csv"
    df.to_csv(bad, index=False)

    code, text = run_cli("rows", bad)
    saved = pd.read_csv(folder / "people_problem_rows.csv")
    assert code == 0 and len(saved) == 1
    assert saved.loc[0, "_pdq_reason"] == "age: impossible"


def test_cli_unreadable_file(tmp_path):
    code, _ = run_cli("check", tmp_path / "missing.csv")
    assert code == 3


# ------------------------------------------------------------------ loading
def test_semicolon_and_latin1_csv(tmp_path):
    path = tmp_path / "ventes.csv"
    path.write_bytes("ville;montant\nOrléans;10\nNîmes;20\n".encode("cp1252"))
    df = pdq.load_file(str(path))
    assert list(df.columns) == ["ville", "montant"]
    assert df.loc[0, "ville"] == "Orléans"


def test_excel_round_trip(tmp_path):
    pytest.importorskip("openpyxl")
    path = tmp_path / "orders.xlsx"
    make_orders(n=50).to_excel(path, index=False)
    assert pdq.check(str(path), today=TODAY).verdict == "ok"
