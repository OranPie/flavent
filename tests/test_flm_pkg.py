from __future__ import annotations

import json
from pathlib import Path

import pytest

from flavent.flm import FLM_FILENAME, FLM_LOCK_FILENAME, FlmError, add_dependency, init_project, install, read_json


def test_flm_init_creates_manifest_and_skeleton(tmp_path: Path):
    root = tmp_path / "proj"
    mf_path = init_project(root)
    assert mf_path == root / FLM_FILENAME
    assert (root / "src").is_dir()
    assert (root / "tests_flv").is_dir()
    assert (root / "vendor").is_dir()
    mf = read_json(mf_path)
    assert mf["flmVersion"] == 1
    assert mf["package"]["entry"] == "src/main.flv"


def test_flm_add_and_install_path_dep(tmp_path: Path):
    # Create project.
    root = tmp_path / "proj"
    init_project(root)

    # Create local dependency.
    dep = tmp_path / "depmod"
    dep.mkdir(parents=True)
    (dep / "__init__.flv").write_text("fn answer() -> Int = 42\n", encoding="utf-8")

    add_dependency(root, name="depmod", path=str(dep))
    mf = read_json(root / FLM_FILENAME)
    assert "depmod" in mf["dependencies"]

    install(root)
    vend = root / "vendor" / "depmod"
    assert vend.exists()
    assert vend.is_symlink() or vend.is_dir()

    lock = read_json(root / FLM_LOCK_FILENAME)
    assert lock["flmLockVersion"] == 1
    assert "depmod" in lock["resolved"]


def test_flm_add_dependency_rejects_conflicting_sources(tmp_path: Path):
    root = tmp_path / "proj"
    init_project(root)

    with pytest.raises(FlmError, match="only one source"):
        add_dependency(root, name="depmod", git="https://example/repo.git", path="../depmod")


def test_flm_add_dependency_rejects_rev_without_git(tmp_path: Path):
    root = tmp_path / "proj"
    init_project(root)

    with pytest.raises(FlmError, match="rev requires --git"):
        add_dependency(root, name="depmod", rev="abc123")


def test_flm_install_rejects_malformed_dependency_specs(tmp_path: Path):
    root = tmp_path / "proj"
    init_project(root)

    cases = [
        ("non-object", {"depmod": "bad"}),
        ("both-git-and-path", {"depmod": {"git": "repo", "path": "../dep"}}),
        ("empty-path", {"depmod": {"path": "  "}}),
        ("rev-without-git", {"depmod": {"path": "../dep", "rev": "abc"}}),
    ]
    for _name, deps in cases:
        (root / FLM_FILENAME).write_text(
            json.dumps(
                {
                    "flmVersion": 1,
                    "package": {"name": "proj", "version": "0.1.0", "entry": "src/main.flv"},
                    "toolchain": {"flavent": ">=0.1.0"},
                    "dependencies": deps,
                    "devDependencies": {},
                    "pythonAdapters": [],
                    "extensions": {},
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        with pytest.raises(FlmError, match="dependency"):
            install(root)
