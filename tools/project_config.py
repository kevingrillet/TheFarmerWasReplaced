"""Project paths with a %USERPROFILE% placeholder; no .env code is executed."""

from __future__ import annotations

import os
from pathlib import Path
import re
from collections.abc import Mapping


REPO = Path(__file__).resolve().parents[1]
PATH_KEYS = ("TFWR_GAME_DIR", "TFWR_SAVE_DIR", "TFWR_REPO_SAVE_DIR")


def load_project_config(
    repo: Path = REPO, environ: Mapping[str, str] | None = None
) -> dict[str, Path]:
    environment = os.environ if environ is None else environ
    profile = str(environment.get("USERPROFILE") or Path.home())

    def expand_profile(value: str) -> Path:
        return Path(value.replace("%USERPROFILE%", profile))

    env_file = expand_profile(str(environment.get("TFWR_ENV_FILE") or repo / ".env"))
    if not env_file.is_absolute():
        env_file = repo / env_file
    values = {}
    if environment.get("TFWR_ENV_FILE") and not env_file.is_file():
        raise FileNotFoundError(f"Configuration file not found: {env_file}")
    if env_file.is_file():
        for number, raw in enumerate(
            env_file.read_text(encoding="utf-8").splitlines(), 1
        ):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)", line)
            if not match:
                raise ValueError(f"Invalid assignment at {env_file}:{number}")
            key, value = match.groups()
            if key not in PATH_KEYS:
                continue
            if value[:1] in ("'", '"'):
                if len(value) < 2 or value[-1] != value[0]:
                    raise ValueError(f"Unclosed quote at {env_file}:{number}")
                value = value[1:-1]
            if not values.get(key):
                values[key] = value
    defaults = {
        "TFWR_GAME_DIR": "C:/Program Files (x86)/Steam/steamapps/common/The Farmer Was Replaced",
        "TFWR_SAVE_DIR": str(
            Path(profile)
            / "AppData/LocalLow/TheFarmerWasReplaced/TheFarmerWasReplaced/Saves/Save0"
        ),
        "TFWR_REPO_SAVE_DIR": "Save0",
    }
    result = {}
    for key in PATH_KEYS:
        path = expand_profile(environment.get(key) or values.get(key) or defaults[key])
        result[key] = (path if path.is_absolute() else repo / path).resolve()
    return result
