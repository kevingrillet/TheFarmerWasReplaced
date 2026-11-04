"""Exercise configuration and save utilities against temporary fixture folders."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from project_config import load_project_config


REPO = Path(__file__).resolve().parents[1]
WINDOWS_BASH = (
    Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe"
)
BASH = str(WINDOWS_BASH) if WINDOWS_BASH.is_file() else shutil.which("bash")


class ConfigTests(unittest.TestCase):
    def test_literal_paths_and_precedence(self):
        with tempfile.TemporaryDirectory(prefix="tfwr-config-") as directory:
            repo = Path(directory)
            (repo / ".env").write_text(
                '# Comment\nTFWR_GAME_DIR="Game with spaces"\n'
                "TFWR_SAVE_DIR='Literal $HOME #folder'\nTFWR_REPO_SAVE_DIR=Save0\n",
                encoding="utf-8",
            )
            config = load_project_config(
                repo, {"TFWR_GAME_DIR": str(repo / "override")}
            )
            self.assertEqual(config["TFWR_GAME_DIR"], repo / "override")
            self.assertEqual(config["TFWR_SAVE_DIR"], repo / "Literal $HOME #folder")
            self.assertEqual(config["TFWR_REPO_SAVE_DIR"], repo / "Save0")

    def test_malformed_config_fails(self):
        with tempfile.TemporaryDirectory(prefix="tfwr-config-") as directory:
            repo = Path(directory)
            (repo / ".env").write_text('TFWR_GAME_DIR="unclosed\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_project_config(repo, {})

    def test_profile_placeholder_from_file_and_environment(self):
        with tempfile.TemporaryDirectory(prefix="tfwr-config-") as directory:
            repo = Path(directory)
            profile = repo / "profile with spaces"
            (repo / ".env").write_text(
                'TFWR_SAVE_DIR="%USERPROFILE%/AppData/LocalLow/Game/Saves/Save0"\n',
                encoding="utf-8",
            )
            environment = {"USERPROFILE": str(profile)}
            config = load_project_config(repo, environment)
            self.assertEqual(
                config["TFWR_SAVE_DIR"], profile / "AppData/LocalLow/Game/Saves/Save0"
            )
            environment["TFWR_SAVE_DIR"] = "%USERPROFILE%/override"
            config = load_project_config(repo, environment)
            self.assertEqual(config["TFWR_SAVE_DIR"], profile / "override")

    def test_profile_placeholder_falls_back_to_home(self):
        with tempfile.TemporaryDirectory(prefix="tfwr-config-") as directory:
            repo = Path(directory)
            (repo / ".env").write_text(
                'TFWR_SAVE_DIR="%USERPROFILE%/Game"\n', encoding="utf-8"
            )
            self.assertEqual(
                load_project_config(repo, {})["TFWR_SAVE_DIR"], Path.home() / "Game"
            )

    def test_missing_explicit_config_fails(self):
        with tempfile.TemporaryDirectory(prefix="tfwr-config-") as directory:
            with self.assertRaises(FileNotFoundError):
                load_project_config(Path(directory), {"TFWR_ENV_FILE": "missing.env"})


@unittest.skipUnless(BASH, "Bash is required for script integration tests")
class ScriptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="tfwr-scripts-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / "game save with spaces"
        self.local = self.root / "local scripts"
        self.game.mkdir()
        self.local.mkdir()
        self.env_file = self.root / ".env"
        self.env_file.write_text(
            f'TFWR_GAME_DIR="{(self.root / "Game with spaces").as_posix()}"\r\n'
            f'TFWR_SAVE_DIR="{self.game.as_posix()}"\r\n'
            f'TFWR_REPO_SAVE_DIR="{self.local.as_posix()}"\r\n',
            encoding="utf-8",
        )
        self.environment = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("TFWR_")
        }
        self.environment["TFWR_ENV_FILE"] = str(self.env_file)

    def run_script(self, name, *args, answer="", environment=None):
        return subprocess.run(
            [BASH, (REPO / "scripts" / name).as_posix(), *args],
            input=answer,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=self.root,
            env=environment or self.environment,
            timeout=30,
        )

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_dry_run_creates_nothing(self):
        (self.game / "new.py").write_text("new", encoding="utf-8")
        (self.game / "save.json").write_text("snapshot", encoding="utf-8")
        result = self.run_script("tfwrImport.sh", "--dryrun", "-d", "new destination")
        self.assert_success(result)
        self.assertIn("new.py", result.stdout)
        self.assertIn("save.json", result.stdout)
        self.assertFalse((self.root / "new destination").exists())
        self.assertEqual(list(self.local.iterdir()), [])

    def test_import_only_overwrites_expected_files(self):
        (self.game / "main.py").write_text("new", encoding="utf-8")
        (self.game / "__builtins__.py").write_text("stub", encoding="utf-8")
        (self.game / "save.json").write_text("live", encoding="utf-8")
        (self.game / "other.json").write_text("unrelated", encoding="utf-8")
        (self.local / "main.py").write_text("old", encoding="utf-8")
        (self.local / "keep.py").write_text("keep", encoding="utf-8")
        (self.local / "notes.txt").write_text("keep", encoding="utf-8")
        self.assert_success(self.run_script("tfwrImport.sh", answer="y\n"))
        self.assertEqual((self.local / "main.py").read_text(), "new")
        self.assertEqual((self.local / "keep.py").read_text(), "keep")
        self.assertEqual((self.local / "notes.txt").read_text(), "keep")
        self.assertTrue((self.local / "__builtins__.py").is_file())
        self.assertEqual((self.local / "save.json").read_text(), "live")
        self.assertFalse((self.local / "other.json").exists())

    def test_import_cancel_does_not_change_files(self):
        (self.game / "main.py").write_text("new", encoding="utf-8")
        (self.local / "main.py").write_text("old", encoding="utf-8")
        (self.game / "save.json").write_text("new state", encoding="utf-8")
        (self.local / "save.json").write_text("old state", encoding="utf-8")
        self.assert_success(self.run_script("tfwrImport.sh", answer="n\n"))
        self.assertEqual((self.local / "main.py").read_text(), "old")
        self.assertEqual((self.local / "save.json").read_text(), "old state")

    def test_import_save_without_python_files(self):
        (self.game / "save.json").write_text("live", encoding="utf-8")
        self.assert_success(self.run_script("tfwrImport.sh"))
        self.assertEqual((self.local / "save.json").read_text(), "live")

    def test_export_preserves_live_builtins_and_non_python(self):
        (self.local / "main.py").write_text("new", encoding="utf-8")
        (self.local / "__builtins__.py").write_text("old stub", encoding="utf-8")
        (self.local / "notes.txt").write_text("local", encoding="utf-8")
        (self.local / "save.json").write_text("outdated local state", encoding="utf-8")
        (self.game / "__builtins__.py").write_text("live stub", encoding="utf-8")
        (self.game / "save.json").write_text("live", encoding="utf-8")
        self.assert_success(self.run_script("tfwrExport.sh"))
        self.assertEqual((self.game / "main.py").read_text(), "new")
        self.assertEqual((self.game / "__builtins__.py").read_text(), "live stub")
        self.assertEqual((self.game / "save.json").read_text(), "live")
        self.assertFalse((self.game / "notes.txt").exists())

    def test_diff_handles_changes_and_one_sided_files(self):
        (self.local / "changed.py").write_text("old\n", encoding="utf-8")
        (self.game / "changed.py").write_text("new\n", encoding="utf-8")
        (self.local / "only-local.py").write_text("local\n", encoding="utf-8")
        (self.game / "only-game.py").write_text("game\n", encoding="utf-8")
        (self.local / "ignored.txt").write_text("local", encoding="utf-8")
        result = self.run_script("tfwrDiff.sh")
        self.assert_success(result)
        for name in ("changed.py", "only-local.py", "only-game.py"):
            self.assertIn(name, result.stdout)
        self.assertNotIn("ignored.txt", result.stdout)

    def test_environment_and_cli_override_file(self):
        override = self.root / "override"
        override.mkdir()
        (override / "override.py").write_text("override", encoding="utf-8")
        environment = dict(self.environment, TFWR_SAVE_DIR=str(override))
        self.assertIn(
            "override.py",
            self.run_script(
                "tfwrImport.sh", "--dryrun", environment=environment
            ).stdout,
        )
        result = self.run_script(
            "tfwrImport.sh",
            "--dryrun",
            "-s",
            "game save with spaces",
            environment=environment,
        )
        self.assert_success(result)
        self.assertNotIn("override.py", result.stdout)

    def test_invalid_source_and_arguments_fail(self):
        for args in (("-s",), ("-s", "missing"), ("-d", str(self.game))):
            self.assertNotEqual(self.run_script("tfwrImport.sh", *args).returncode, 0)
        self.assertEqual(list(self.local.iterdir()), [])

    def test_profile_placeholder_in_bash_and_python(self):
        self.env_file.write_text(
            self.env_file.read_text(encoding="utf-8").replace(
                self.game.as_posix(), "%USERPROFILE%/game save with spaces"
            ),
            encoding="utf-8",
        )
        environment = dict(self.environment, USERPROFILE=str(self.root))
        config = load_project_config(REPO, environment)
        self.assertEqual(config["TFWR_SAVE_DIR"], self.game)
        (self.game / "profile-test.py").write_text("pass", encoding="utf-8")
        for args in (
            ("--dryrun",),
            ("--dryrun", "-s", "%USERPROFILE%/game save with spaces"),
        ):
            result = self.run_script("tfwrImport.sh", *args, environment=environment)
            self.assert_success(result)
            self.assertIn("profile-test.py", result.stdout)
        self.assertEqual(list(self.local.iterdir()), [])

    def test_config_is_literal_and_not_executed(self):
        with self.env_file.open("a", encoding="utf-8") as stream:
            stream.write("TFWR_GAME_DIR='$(touch should-not-exist)'\n")
        self.assert_success(self.run_script("tfwrImport.sh", "--dryrun"))
        self.assertFalse((self.root / "should-not-exist").exists())


if __name__ == "__main__":
    unittest.main()
