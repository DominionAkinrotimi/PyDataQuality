"""
The ``pdq`` command.

    pdq check orders.csv      is this file safe to use?
    pdq accept orders.csv     remember this file as normal
    pdq rows orders.csv       save the affected rows, with reasons
    pdq report orders.csv     write a one-page summary to share
    pdq ui                    open a page where you can drop a file in

Exit codes for ``check``: 0 nothing found, 1 warnings, 2 problems, 3 the file
could not be read.
"""

import argparse
import json
import os
import sys

COMMANDS = ("check", "accept", "rows", "report", "ui")
EXIT_UNREADABLE = 3


def _supports(stream, text: str) -> bool:
    try:
        text.encode(getattr(stream, "encoding", None) or "ascii")
        return True
    except (UnicodeEncodeError, LookupError):
        return False


def _use_color(stream, disabled: bool) -> bool:
    if disabled or os.environ.get("NO_COLOR") or not getattr(stream, "isatty", lambda: False)():
        return False
    if os.name == "nt":
        os.system("")  # switches the Windows console to ANSI colour mode
    return True


def _split(values):
    """Accept both repeated flags and comma-separated lists."""
    items = []
    for value in values or []:
        items += [part.strip() for part in value.split(",") if part.strip()]
    return items or None


def _parse_rules(pairs):
    """--rule "price: greater than 0" -> {'price': ['greater than 0']}"""
    rules = {}
    for pair in pairs or []:
        column, separator, rule = pair.partition(":")
        if not separator or not rule.strip():
            raise SystemExit(f'A rule looks like "column: rule", for example "price: greater than 0". Got: {pair}')
        rules.setdefault(column.strip(), []).append(rule.strip())
    return rules or None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdq",
        description="Know whether a data file is safe to use, and what changed since the last one.",
        epilog="Everything runs on this computer. Your data is not sent anywhere.",
    )
    commands = parser.add_subparsers(dest="command")

    check = commands.add_parser("check", help="check a file (the default command)")
    check.add_argument("file", help="CSV, TSV, Excel, JSON or Parquet file")
    check.add_argument("--baseline", help="baseline file or dataset name to compare with (default: found automatically)")
    check.add_argument("--no-baseline", action="store_true", help="do not compare with any earlier file")
    check.add_argument("--column", action="append", help="only show findings for this column (repeatable)")
    check.add_argument("--only", action="append", help="only show this kind of finding, e.g. duplicates (repeatable)")
    check.add_argument("--rule", action="append", metavar='"COLUMN: RULE"', help='add a check, e.g. "price: greater than 0"')
    check.add_argument("--why", action="store_true", help="explain how each finding was decided")
    check.add_argument("--json", action="store_true", help="print the result as JSON")
    check.add_argument("--no-color", action="store_true", help="plain text output")

    accept = commands.add_parser("accept", help="remember a file as normal; later files are compared with it")
    accept.add_argument("file")
    accept.add_argument("--as", dest="name", help="dataset name (default: taken from the file name)")

    rows = commands.add_parser("rows", help="save the affected rows to a CSV file, with the reason for each")
    rows.add_argument("file")
    rows.add_argument("-o", "--output", help="where to save (default: <file>_problem_rows.csv)")
    rows.add_argument("--baseline")
    rows.add_argument("--no-baseline", action="store_true")

    report = commands.add_parser("report", help="write a one-page HTML summary to share with whoever sent the file")
    report.add_argument("file")
    report.add_argument("-o", "--output", help="where to save (default: <file>_check.html)")
    report.add_argument("--baseline")
    report.add_argument("--no-baseline", action="store_true")

    ui = commands.add_parser("ui", help="open a page in your browser where you can drop a file in")
    ui.add_argument("--port", type=int, default=0, help="port to use (default: any free port)")
    ui.add_argument("--no-browser", action="store_true", help="do not open the browser automatically")
    return parser


def _run_check(args, out):
    from .checker import check

    result = check(
        args.file,
        baseline=False if args.no_baseline else args.baseline,
        rules=_parse_rules(args.rule),
        columns=_split(args.column),
        only=_split(args.only),
    )
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, default=str), file=out)
        return result.exit_code

    print(result.to_text(color=_use_color(out, args.no_color), why=args.why, unicode=_supports(out, "✖✓")), file=out)
    hints = []
    if result.findings and any(f.rows is not None for f in result.findings):
        hints.append((f"pdq rows {args.file}", "save the affected rows with reasons"))
    if result.findings:
        hints.append((f"pdq report {args.file}", "one-page summary to send to whoever made the file"))
    if not result.has_baseline:
        hints.append((f"pdq accept {args.file}", "remember this file as normal and compare the next one with it"))
    elif not result.ok:
        hints.append((f"pdq accept {args.file}", "this is fine, make it the new normal"))
    if result.findings and not args.why:
        hints.append((f"pdq check {args.file} --why", "see how each finding was decided"))
    if hints:
        width = max(len(command) for command, _ in hints)
        print("", file=out)
        for position, (command, meaning) in enumerate(hints):
            lead = "Next:  " if position == 0 else "       "
            print(f"{lead}{command.ljust(width)}   {meaning}", file=out)
    return result.exit_code


def _run_accept(args, out):
    from . import baseline as base
    from .checker import accept

    path = accept(args.file, name=args.name)
    learned = base.load(path)
    columns = learned["columns"]
    print(f"Saved what normal looks like: {learned['rows']:,} rows, {len(columns)} columns.", file=out)
    for column, info in columns.items():
        facts = [info["type"]]
        if info.get("unique"):
            facts.append("no repeats")
        if "values" in info:
            facts.append(f"{len(info['values'])} allowed values")
        if "min" in info:
            facts.append(f"{info['min']:,.6g} to {info['max']:,.6g}")
        if info.get("missing_pct", 0) >= 1:
            facts.append(f"{info['missing_pct']:.0f}% empty")
        print(f"  {column}: {', '.join(facts)}", file=out)
    print(f"\nBaseline file: {path}", file=out)
    print("You can open it and add your own rules. The next file of this kind is compared with it.", file=out)
    return 0


def _run_rows(args, out):
    from .checker import check

    result = check(args.file, baseline=False if args.no_baseline else args.baseline)
    rows = result.bad_rows()
    if rows.empty:
        print("No rows are affected. Nothing was saved.", file=out)
        return 0
    output = args.output or f"{os.path.splitext(args.file)[0]}_problem_rows.csv"
    rows.to_csv(output, index=False)
    print(f"Saved {len(rows):,} rows to {output}", file=out)
    print("The last column, _pdq_reason, says why each row is listed.", file=out)
    return 0


def _run_report(args, out):
    from .checker import check

    result = check(args.file, baseline=False if args.no_baseline else args.baseline)
    output = args.output or f"{os.path.splitext(args.file)[0]}_check.html"
    with open(output, "w", encoding="utf-8") as handle:
        handle.write(result.to_html())
    print(f"Saved the summary to {output}", file=out)
    print("It is a single file. You can email it or open it in any browser.", file=out)
    return 0


def _run_ui(args, out):
    from .webui import serve

    serve(port=args.port, open_browser=not args.no_browser, out=out)
    return 0


def main(argv=None, out=None) -> int:
    from .checker import DataFileError

    out = out or sys.stdout
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] not in COMMANDS and not argv[0].startswith("-"):
        argv.insert(0, "check")  # "pdq orders.csv" means "pdq check orders.csv"

    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help(out)
        return 0
    try:
        handlers = {
            "check": _run_check,
            "accept": _run_accept,
            "rows": _run_rows,
            "report": _run_report,
            "ui": _run_ui,
        }
        return handlers[args.command](args, out)
    except DataFileError as error:
        print(f"Could not check the file. {error}", file=sys.stderr)
        return EXIT_UNREADABLE


def run():
    """Console entry point."""
    sys.exit(main())


if __name__ == "__main__":
    run()
