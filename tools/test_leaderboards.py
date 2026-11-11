"""Check public-score parsing and export failures without contacting Steam."""

import csv
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

from export_leaderboards import (
    SteamPage,
    collect_scores,
    discover_boards,
    main,
    parse_score,
    profile_root,
    seconds_from_time,
    write_csv,
)

PROFILE = "https://steamcommunity.com/id/example_player"
CATALOG = """<select name="lb">
<option value="1" selected>Hay Single</option><option value="2">Rice</option>
</select>"""
ENTRY = """<div class="lbentry"><a class="playerName"
href="https://steamcommunity.com/id/example_player/stats/2060160/">Example Player</a>
<div class="scoreh">6:06:40.082</div>
<div class="globalRankh">Global rank: #1,234</div></div>"""
EMPTY = "Neither Example Player nor their friends have an entry in this leaderboard!"


class LeaderboardTests(unittest.TestCase):
    def test_full_stats_url_and_numeric_profile(self):
        self.assertEqual(profile_root(PROFILE + "/stats/2060160/?lb=1"), PROFILE)
        numeric = "https://steamcommunity.com/profiles/76561198000000000"
        self.assertEqual(profile_root(numeric), numeric)
        for url in ["https://example.com/id/x", PROFILE + "/friends", "file:///tmp/x"]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                profile_root(url)

    def test_discover_catalog_including_unplayed_dlc(self):
        self.assertEqual(
            discover_boards(SteamPage(CATALOG)), [("1", "Hay Single"), ("2", "Rice")]
        )

    def test_durations_preserve_hours_and_milliseconds(self):
        self.assertEqual(seconds_from_time("07:05.493"), "425.493")
        self.assertEqual(seconds_from_time("6:06:40.082"), "22000.082")
        self.assertEqual(seconds_from_time("00:00.001"), "0.001")
        for value in ["", "N/A", "00:61.000", "6:60:00.000", "00:10"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                seconds_from_time(value)

    def test_score_and_rank(self):
        self.assertEqual(
            parse_score(SteamPage(CATALOG + ENTRY), PROFILE, "1"),
            {
                "status": "ok",
                "time": "6:06:40.082",
                "seconds": "22000.082",
                "global_rank": "1234",
            },
        )

    def test_empty_entry_is_not_a_zero_time(self):
        self.assertEqual(
            parse_score(SteamPage(CATALOG + EMPTY), PROFILE, "1"),
            {"status": "no_score"},
        )

    def test_friend_score_is_not_profile_score(self):
        friend = ENTRY.replace("/id/example_player/", "/id/someone_else/")
        self.assertEqual(
            parse_score(SteamPage(CATALOG + friend), PROFILE, "1"),
            {"status": "no_score"},
        )

    def test_login_or_changed_markup_is_not_no_score(self):
        for html in [
            "<html>Sign in</html>",
            CATALOG,
            (CATALOG + ENTRY).replace('class="scoreh"', 'class="changed"'),
        ]:
            with self.subTest(html=html), self.assertRaises(ValueError):
                parse_score(SteamPage(html), PROFILE, "1")

    def test_wrong_category_is_not_accepted(self):
        with self.assertRaises(ValueError):
            parse_score(SteamPage(CATALOG + ENTRY), PROFILE, "2")

    def test_partial_http_failure_retains_success_and_error(self):
        def fetch(url):
            if "lb=2" in url:
                raise URLError("offline")
            return CATALOG + ENTRY, url

        rows = collect_scores(PROFILE, "2026-11-04T00:00:00+00:00", "abc123", fetch)
        self.assertEqual([r["status"] for r in rows], ["ok", "error"])
        self.assertEqual(rows[0]["repo_commit"], "abc123")
        self.assertIn("offline", rows[1]["error"])
        self.assertEqual(rows[1]["seconds"], "")

    def test_wrong_redirect_profile_is_not_accepted(self):
        def fetch(url):
            return CATALOG + ENTRY, url.replace(
                "example_player", "someone_else"
            ) if "lb=" in url else url

        self.assertTrue(
            all(
                r["status"] == "parse_error"
                for r in collect_scores(PROFILE, "now", "commit", fetch)
            )
        )

    def test_csv_roundtrip_and_refresh(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.csv"
            write_csv(path, [{"category": "Rice, Single", "status": "no_score"}])
            with path.open(encoding="utf-8", newline="") as stream:
                row = next(csv.DictReader(stream))
            self.assertEqual(row["category"], "Rice, Single")
            self.assertEqual(row["seconds"], "")
            write_csv(
                path,
                [{"category": "Rice, Single", "status": "ok", "time": "00:01.000"}],
            )
            with path.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["time"], "00:01.000")

    def test_failed_export_preserves_previous_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.csv"
            path.write_text("previous export", encoding="utf-8")
            with (
                patch(
                    "sys.argv",
                    [
                        "export_leaderboards.py",
                        "--profile",
                        PROFILE,
                        "--output",
                        str(path),
                    ],
                ),
                patch(
                    "export_leaderboards.collect_scores",
                    return_value=[
                        {"category": "Hay", "status": "error", "error": "offline"}
                    ],
                ),
                redirect_stdout(io.StringIO()),
                redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(main(), 1)
            self.assertEqual(path.read_text(encoding="utf-8"), "previous export")

    def test_csv_retains_scores_without_exporting_profile_identity(self):
        def fetch(url):
            if "lb=2" in url:
                return CATALOG.replace('value="1" selected', 'value="1"').replace(
                    'value="2"', 'value="2" selected'
                ) + EMPTY, url
            return CATALOG + ENTRY, url

        rows = collect_scores(PROFILE, "now", "commit", fetch)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.csv"
            write_csv(path, rows)
            text = path.read_text(encoding="utf-8")
        self.assertNotIn("example_player", text)
        self.assertNotIn("profile_url", text)
        self.assertNotIn("source_url", text)
        self.assertIn("6:06:40.082", text)
        self.assertIn("1234", text)

    def test_local_profile_is_loaded_and_cli_profile_takes_precedence(self):
        for explicit in (False, True):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "scores.csv"
                args = ["export_leaderboards.py", "--output", str(path)]
                if explicit:
                    args.extend(["--profile", PROFILE])
                with (
                    self.subTest(explicit=explicit),
                    patch("sys.argv", args),
                    patch(
                        "export_leaderboards.load_project_values",
                        return_value={"TFWR_STEAM_PROFILE": PROFILE},
                    ) as config,
                    patch(
                        "export_leaderboards.collect_scores", return_value=[]
                    ) as collect,
                    redirect_stdout(io.StringIO()),
                ):
                    self.assertEqual(main(), 0)
                self.assertEqual(config.call_count, int(not explicit))
                self.assertEqual(collect.call_args.args[0], PROFILE)

    def test_missing_local_profile_fails_before_network_and_preserves_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.csv"
            path.write_text("previous export", encoding="utf-8")
            with (
                patch("sys.argv", ["export_leaderboards.py", "--output", str(path)]),
                patch(
                    "export_leaderboards.load_project_values",
                    return_value={"TFWR_STEAM_PROFILE": ""},
                ),
                patch("export_leaderboards.collect_scores") as collect,
                redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(main(), 1)
            collect.assert_not_called()
            self.assertEqual(path.read_text(encoding="utf-8"), "previous export")


if __name__ == "__main__":
    unittest.main()
