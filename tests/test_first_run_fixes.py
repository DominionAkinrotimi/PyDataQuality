"""Regression tests for defects a first-time user hit in 0.1.0."""

import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

import pydataquality as pdq
from pydataquality.cli import main as cli_main
from pydataquality.reporter import QualityReportGenerator


@pytest.fixture
def people():
    rng = np.random.default_rng(0)
    n = 200
    return pd.DataFrame(
        {
            "customer_id": np.arange(n),
            "age": rng.integers(18, 70, n),
            "email": [f"user{i}@mail.com" for i in range(n)],
            "country": rng.choice(["NG", "GH", "KE"], n),
            "is_active": rng.choice([True, False], n),
        }
    )


def test_importing_package_does_not_load_matplotlib():
    code = "import sys, pydataquality; print('matplotlib' in sys.modules)"
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert out.stdout.strip() == "False"


def test_visualizer_still_reachable_from_package():
    assert pdq.DataQualityVisualizer.__name__ == "DataQualityVisualizer"


def test_column_rules_are_applied(people):
    people.loc[0, "age"] = 150
    people.loc[1, "age"] = -5
    rules = {"column_rules": {"age": {"min": 0, "max": 120}}}

    without = pdq.DataQualityAnalyzer(people)
    with_rules = pdq.DataQualityAnalyzer(people, rules=rules)

    violations = [i for i in with_rules.issues if i.issue_type == "rule_violation"]
    assert len(with_rules.issues) == len(without.issues) + 1
    assert violations[0].affected_count == 2
    assert violations[0].severity == "critical"
    bad = with_rules.get_problematic_rows("age", "rule_violation")
    assert sorted(bad["age"].tolist()) == [-5, 150]


def test_rules_for_missing_column_are_reported(people):
    rules = {"column_rules": {"salary": {"min": 0}}}
    analyzer = pdq.DataQualityAnalyzer(people, rules=rules)
    assert any(
        i.issue_type == "rule_violation" and i.column == "salary"
        for i in analyzer.issues
    )


def test_rule_thresholds_override_defaults(people):
    analyzer = pdq.DataQualityAnalyzer(
        people, rules={"thresholds": {"outlier_threshold": 9.0}}
    )
    assert analyzer.config["outlier_threshold"] == 9.0


def test_duplicate_rows_are_flagged(people):
    doubled = pd.concat([people, people.iloc[:15]], ignore_index=True)
    analyzer = pdq.DataQualityAnalyzer(doubled)
    issue = next(i for i in analyzer.issues if i.issue_type == "duplicate_rows")
    assert issue.affected_count == 15
    # Reports must cope with an issue that is not tied to one column
    assert "duplicate" in pdq.generate_report(analyzer, format="html").lower()


def test_text_columns_are_categorical_not_other(people):
    types = pdq.DataQualityAnalyzer(people).get_summary()["column_types"]
    assert types.get("categorical") == 2
    assert "other" not in types


def test_drift_skips_identifier_columns(people):
    ref = pdq.analyze_dataframe(people.iloc[:100])
    cur = pdq.analyze_dataframe(people.iloc[100:])
    drift = pdq.compare_drift(ref, cur).set_index("column")
    assert drift.loc["customer_id", "drift_status"] == "not_applicable"
    assert drift.loc["email", "drift_status"] == "not_applicable"
    assert drift.loc["country", "drift_status"] == "stable"
    assert drift.loc["is_active", "drift_status"] == "stable"


def test_ai_prompt_withholds_personal_values():
    df = pd.DataFrame(
        {
            "email": ["Ada@mail.com", "ada@mail.com"]
            + [f"person{i}@mail.com" for i in range(48)],
            "city": ["Lagos", "lagos"] * 25,
        }
    )
    reporter = QualityReportGenerator(pdq.DataQualityAnalyzer(df))

    safe = reporter.generate_ai_remediation_prompt()
    assert "@mail.com" not in safe
    assert "lagos" in safe.lower()  # low-cardinality values are still useful context

    explicit = reporter.generate_ai_remediation_prompt(include_values=True)
    assert "@mail.com" in explicit


def test_cli_visualize_runs(people, tmp_path, monkeypatch):
    monkeypatch.setenv("MPLBACKEND", "Agg")
    data = tmp_path / "people.csv"
    people.to_csv(data, index=False)
    cli_main([str(data), "--output", str(tmp_path), "--report", "none", "--visualize"])
    assert (tmp_path / "visualizations").is_dir()


def test_cli_fail_on_sets_exit_code(people, tmp_path):
    people.loc[:120, "age"] = np.nan  # >30% missing is critical
    data = tmp_path / "people.csv"
    people.to_csv(data, index=False)

    cli_main([str(data), "--report", "none"])  # default never fails

    with pytest.raises(SystemExit) as exit_info:
        cli_main([str(data), "--report", "none", "--fail-on", "critical"])
    assert exit_info.value.code == 2


def test_cli_reads_format_and_rules(people, tmp_path):
    data = tmp_path / "people.data"  # unknown extension, format given explicitly
    people.to_json(data)
    rules = tmp_path / "rules.yaml"
    rules.write_text("column_rules:\n  age:\n    max: 30\n")

    with pytest.raises(SystemExit) as exit_info:
        cli_main(
            [
                str(data),
                "--format",
                "json",
                "--rules",
                str(rules),
                "--report",
                "none",
                "--fail-on",
                "critical",
            ]
        )
    assert exit_info.value.code == 2
