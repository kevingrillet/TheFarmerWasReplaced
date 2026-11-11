"""Export public Steam leaderboard entries; never starts or submits a game run."""

from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from project_config import load_project_values

REPO = Path(__file__).resolve().parents[1]
APP_ID = "2060160"
FIELDS = (
    "fetched_at_utc",
    "app_id",
    "leaderboard_id",
    "category",
    "status",
    "time",
    "seconds",
    "global_rank",
    "repo_commit",
    "error",
)


@dataclass
class Node:
    tag: str = ""
    attrs: dict[str, str | None] = field(default_factory=dict)
    children: list[Node | str] = field(default_factory=list)

    def text(self) -> str:
        return "".join(x if isinstance(x, str) else x.text() for x in self.children)

    def find(self, *, tag: str = "", cls: str = "") -> list[Node]:
        matches = (not tag or self.tag == tag) and (
            not cls or cls in (self.attrs.get("class") or "").split()
        )
        result = [self] if matches else []
        for child in self.children:
            if isinstance(child, Node):
                result.extend(child.find(tag=tag, cls=cls))
        return result


class SteamPage(HTMLParser):
    def __init__(self, html: str):
        super().__init__()
        self.root = Node()
        self.stack = [self.root]
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in {
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        }:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)

    def options(self) -> list[Node]:
        selectors = [
            n for n in self.root.find(tag="select") if n.attrs.get("name") == "lb"
        ]
        if len(selectors) != 1:
            raise ValueError("Steam leaderboard selector missing or ambiguous")
        return selectors[0].find(tag="option")


def profile_root(value: str) -> str:
    url = urlsplit(value)
    parts = url.path.strip("/").split("/")
    if (
        url.scheme not in {"http", "https"}
        or url.netloc.lower() != "steamcommunity.com"
        or len(parts) not in {2, 4}
        or parts[0] not in {"id", "profiles"}
        or not re.fullmatch(r"[A-Za-z0-9_-]+", parts[1])
        or (parts[0] == "profiles" and not parts[1].isdigit())
        or (len(parts) == 4 and parts[2:] != ["stats", APP_ID])
    ):
        raise ValueError("Expected a Steam /id/name or /profiles/number profile URL")
    return "https://steamcommunity.com/" + "/".join(parts[:2])


def board_url(profile: str, board_id: str = "") -> str:
    query = {"tab": "leaderboards", "l": "english"}
    if board_id:
        query["lb"] = board_id
    return f"{profile}/stats/{APP_ID}/?{urlencode(query)}"


def fetch_page(url: str) -> tuple[str, str]:
    request = Request(
        url,
        headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.9"},
    )
    with urlopen(request, timeout=25) as response:
        return response.read().decode("utf-8", errors="replace"), response.url


def discover_boards(page: SteamPage) -> list[tuple[str, str]]:
    boards = [(n.attrs.get("value") or "", n.text().strip()) for n in page.options()]
    if (
        not boards
        or any(not ident.isdigit() or not name for ident, name in boards)
        or len({ident for ident, _ in boards}) != len(boards)
    ):
        raise ValueError("Invalid or empty Steam leaderboard catalog")
    return boards


def seconds_from_time(value: str) -> str:
    match = re.fullmatch(r"(?:(\d+):)?([0-5]?\d):([0-5]\d)\.(\d{3})", value)
    if not match:
        raise ValueError(f"Unrecognized Steam time: {value!r}")
    hours, minutes, seconds, millis = (int(x or 0) for x in match.groups())
    total = hours * 3600 + minutes * 60 + seconds
    return f"{total}.{millis:03d}"


def parse_score(page: SteamPage, profile: str, board_id: str) -> dict[str, str]:
    selected = [n for n in page.options() if "selected" in n.attrs]
    if len(selected) != 1 or selected[0].attrs.get("value") != board_id:
        raise ValueError("Steam returned a different leaderboard")
    entries = page.root.find(cls="lbentry")
    own = []
    for entry in entries:
        players = entry.find(cls="playerName")
        if not players:
            raise ValueError("Unrecognized Steam leaderboard entry")
        href = players[0].attrs.get("href") or ""
        if profile_root(href).lower() == profile.lower():
            own.append(entry)
    if not own:
        # Only classify an absent score when the expected structure/message exists.
        if (
            entries
            or "nor their friends have an entry in this leaderboard!"
            in page.root.text()
        ):
            return {"status": "no_score"}
        raise ValueError(
            "Neither a score nor Steam's empty-leaderboard message was found"
        )
    if len(own) != 1:
        raise ValueError("Ambiguous Steam profile entry")
    scores = own[0].find(cls="scoreh") or own[0].find(cls="score")
    ranks = own[0].find(cls="globalRankh") or own[0].find(cls="globalRank")
    if len(scores) != 1 or len(ranks) != 1:
        raise ValueError("Steam score or global rank missing or ambiguous")
    time = scores[0].text().strip()
    rank = re.fullmatch(r"Global rank:\s*#([\d,]+)", ranks[0].text().strip())
    if not rank:
        raise ValueError("Unrecognized Steam global rank")
    return {
        "status": "ok",
        "time": time,
        "seconds": seconds_from_time(time),
        "global_rank": str(int(rank[1].replace(",", ""))),
    }


def collect_scores(profile: str, fetched_at: str, commit: str, fetch=fetch_page):
    html, canonical_url = fetch(board_url(profile))
    profile = profile_root(canonical_url)
    boards = discover_boards(SteamPage(html))

    def collect(board):
        ident, name = board
        url = board_url(profile, ident)
        row = dict.fromkeys(FIELDS, "")
        row.update(
            fetched_at_utc=fetched_at,
            app_id=APP_ID,
            leaderboard_id=ident,
            category=name,
            repo_commit=commit,
        )
        try:
            html, final_url = fetch(url)
        except (OSError, ValueError) as exc:
            row.update(status="error", error=str(exc))
            return row
        try:
            if profile_root(final_url).lower() != profile.lower():
                raise ValueError("Steam returned a different profile")
            row.update(parse_score(SteamPage(html), profile, ident))
        except ValueError as exc:
            row.update(status="parse_error", error=str(exc))
        return row

    with ThreadPoolExecutor(max_workers=3) as pool:
        return list(pool.map(collect, boards))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def current_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile", help="Steam profile URL (default: TFWR_STEAM_PROFILE in .env)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="CSV to update (default: docs/benchmarks/steam-leaderboards.csv)",
    )
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    output = args.output or REPO / "docs/benchmarks/steam-leaderboards.csv"
    try:
        value = args.profile
        if value is None:
            value = load_project_values()["TFWR_STEAM_PROFILE"]
        if not value:
            raise ValueError("Set TFWR_STEAM_PROFILE in .env or pass --profile")
        profile = profile_root(value)
        rows = collect_scores(
            profile, now.isoformat(timespec="seconds"), current_commit()
        )
    except (OSError, ValueError) as exc:
        print(f"Export failed: {exc}", file=sys.stderr)
        return 1
    counts = {
        status: sum(row["status"] == status for row in rows)
        for status in ("ok", "no_score", "error", "parse_error")
    }
    print(
        f"{counts['ok']} scores, {counts['no_score']} without score, "
        f"{counts['error'] + counts['parse_error']} errors"
    )
    for row in rows:
        if row["error"]:
            print(f"{row['category']}: {row['error']}", file=sys.stderr)
    if counts["error"] or counts["parse_error"]:
        print("Export failed; existing CSV preserved.", file=sys.stderr)
        return 1
    try:
        write_csv(output, rows)
    except OSError as exc:
        print(f"Export failed: {exc}", file=sys.stderr)
        return 1
    print(f"Updated {len(rows)} categories in {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
