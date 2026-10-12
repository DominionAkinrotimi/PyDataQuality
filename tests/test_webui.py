"""Tests for the shareable summary page."""

import io

import numpy as np
import pandas as pd

import pydataquality as pdq
from pydataquality.pdq_cli import main as pdq_main


def people(n=200, seed=0):
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "person_id": np.arange(n),
            "age": rng.integers(18, 70, n),
            "city": rng.choice(["Lagos", "Accra", "Nairobi"], n),
        }
    )


# ------------------------------------------------------------------ report
def test_report_is_self_contained_and_escaped():
    df = people()
    df.loc[0, "age"] = 999
    df.loc[1, "city"] = "<script>alert(1)</script>"
    page = pdq.check(df, name="people.csv").to_html()

    assert page.startswith("<!doctype html>")
    assert "Problems found" in page and "999" in page
    assert "<script>alert(1)</script>" not in page
    assert "http://" not in page and "https://" not in page  # no outside resources


def test_notebook_display():
    assert "Nothing obviously wrong" in pdq.check(people())._repr_html_()


def test_cli_report_writes_file(tmp_path):
    data = tmp_path / "people.csv"
    people().to_csv(data, index=False)
    out = io.StringIO()
    assert pdq_main(["report", str(data)], out=out) == 0
    assert (tmp_path / "people_check.html").read_text(encoding="utf-8").startswith("<!doctype html>")
