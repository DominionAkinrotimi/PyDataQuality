"""
Record today's public download numbers, so the history is kept.

GitHub only shows repository traffic for the last 14 days and shows release
download counts as running totals. This writes one row a day to daily.csv and
one row per release file to releases.csv, in the folder given as the argument.
Run by .github/workflows/stats.yml, which keeps that folder on the "stats"
branch.

It counts downloads and page views that GitHub and PyPI already record. It
learns nothing about the people using PyDataQuality: the app sends nothing.

    python .github/scripts/record_stats.py FOLDER

Environment:
    REPO            owner/name
    GH_TOKEN        token for the releases and repository APIs
    TRAFFIC_TOKEN   optional. A personal access token with read access to the
                    repository's administration data. GitHub does not let the
                    workflow's own token read traffic, so without this the
                    traffic columns are left empty.
"""

import csv
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request

DAILY_COLUMNS = [
    "date", "installer_downloads", "windows_downloads", "mac_downloads",
    "pypi_last_day", "pypi_last_week", "pypi_last_month",
    "repo_views_14d", "repo_visitors_14d", "repo_clones_14d", "repo_cloners_14d", "stars",
]
RELEASE_COLUMNS = ["date", "release", "file", "downloads"]


def get(url, token=None):
    """JSON from a URL, or None if it cannot be read."""
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "pydataquality-stats"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
            return json.load(response)
    except (urllib.error.URLError, ValueError, TimeoutError) as error:
        print(f"Could not read {url}: {error}")
        return None


def upsert(path, columns, rows, key):
    """Write rows into a CSV, replacing any existing rows with the same key. Returns all rows."""
    existing = []
    if os.path.isfile(path):
        with open(path, newline="", encoding="utf-8") as handle:
            existing = list(csv.DictReader(handle))
    fresh = {key(row) for row in rows}
    kept = [row for row in existing if key(row) not in fresh] + rows
    kept.sort(key=lambda row: [str(row.get(column, "")) for column in columns[:3]])
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(kept)
    return kept


def collect(repo, token, traffic_token, today):
    api = f"https://api.github.com/repos/{repo}"
    daily = {column: "" for column in DAILY_COLUMNS}
    daily["date"] = today
    release_rows = []

    releases = get(f"{api}/releases?per_page=100", token)
    if isinstance(releases, list):
        windows = mac = total = 0
        for release in releases:
            for asset in release.get("assets", []):
                count = int(asset.get("download_count", 0))
                total += count
                name = asset.get("name", "")
                if name.lower().endswith(".exe"):
                    windows += count
                elif "macos" in name.lower():
                    mac += count
                release_rows.append({"date": today, "release": release.get("tag_name", ""), "file": name, "downloads": count})
        daily.update(installer_downloads=total, windows_downloads=windows, mac_downloads=mac)

    info = get(api, token)
    if isinstance(info, dict):
        daily["stars"] = info.get("stargazers_count", "")

    package = repo.split("/")[-1].lower()
    recent = get(f"https://pypistats.org/api/packages/{package}/recent")
    if isinstance(recent, dict) and isinstance(recent.get("data"), dict):
        data = recent["data"]
        daily.update(pypi_last_day=data.get("last_day", ""), pypi_last_week=data.get("last_week", ""), pypi_last_month=data.get("last_month", ""))

    if traffic_token:
        views = get(f"{api}/traffic/views", traffic_token)
        clones = get(f"{api}/traffic/clones", traffic_token)
        if isinstance(views, dict) and "count" in views:
            daily.update(repo_views_14d=views["count"], repo_visitors_14d=views["uniques"])
        if isinstance(clones, dict) and "count" in clones:
            daily.update(repo_clones_14d=clones["count"], repo_cloners_14d=clones["uniques"])
    else:
        print("No TRAFFIC_TOKEN secret, so repository traffic is left empty.")
    return daily, release_rows


README = """# Download numbers

Written once a day by the "Record download numbers" workflow on the main branch.

- `daily.csv`: one row a day.
- `releases.csv`: one row a day for each file attached to a release.

What the columns mean:

| Column | Meaning |
|:--|:--|
| installer_downloads, windows_downloads, mac_downloads | Running totals of downloads of the release files, as counted by GitHub. Subtract yesterday's row to get a day's downloads. |
| pypi_last_day, pypi_last_week, pypi_last_month | `pip install` downloads from pypistats.org. These include mirrors and automated systems, so they overstate real people. |
| repo_views_14d, repo_visitors_14d, repo_clones_14d, repo_cloners_14d | GitHub's rolling 14-day traffic for the repository page. Empty unless the TRAFFIC_TOKEN secret is set. |
| stars | Stars on the repository. |

These are numbers GitHub and PyPI already record. Nothing here comes from the
PyDataQuality app, which sends nothing.
"""


def main(folder):
    os.makedirs(folder, exist_ok=True)
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    daily, release_rows = collect(os.environ["REPO"], os.environ.get("GH_TOKEN"), os.environ.get("TRAFFIC_TOKEN"), today)
    upsert(os.path.join(folder, "daily.csv"), DAILY_COLUMNS, [daily], key=lambda row: row["date"])
    if release_rows:
        upsert(os.path.join(folder, "releases.csv"), RELEASE_COLUMNS, release_rows, key=lambda row: (row["date"], row["release"], row["file"]))
    with open(os.path.join(folder, "README.md"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(README)
    print(json.dumps(daily))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "stats-data")
