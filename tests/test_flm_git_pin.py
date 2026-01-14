from __future__ import annotations

import json
import subprocess
from pathlib import Path

from flavent.flm import FLM_LOCK_FILENAME, init_project, install, read_json


def _git(cmd: list[str], cwd: Path) -> str:
    out = subprocess.check_output(["git", *cmd], cwd=str(cwd), text=True)
    return out.strip()


def test_flm_install_git_pins_commit_and_uses_cache(tmp_path: Path):
    # Create local git repo to avoid network.
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["init"], repo)
    _git(["config", "user.email", "test@example.com"], repo)
    _git(["config", "user.name", "test"], repo)

    (repo / "lib.flv").write_text("fn x() -> Int = 1\n", encoding="utf-8")
    _git(["add", "lib.flv"], repo)
    _git(["commit", "-m", "init"], repo)
    commit = _git(["rev-parse", "HEAD"], repo)

    root = tmp_path / "proj"
    init_project(root)
    (root / "flm.json").write_text(
        json.dumps(
            {
                "flmVersion": 1,
                "package": {"name": "proj", "version": "0.1.0", "entry": "src/main.flv"},
                "toolchain": {"flavent": ">=0.1.0"},
                "dependencies": {"dep": {"git": str(repo)}},
                "devDependencies": {},
                "pythonAdapters": [],
                "extensions": {},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    install(root)

    lock = read_json(root / FLM_LOCK_FILENAME)
    assert lock["resolved"]["dep"]["rev"] == commit

    cached = root / ".flavent" / "git" / "dep"
    vend = root / "vendor" / "dep"
    assert cached.is_dir()
    assert vend.is_symlink()
    assert vend.resolve() == cached.resolve()
