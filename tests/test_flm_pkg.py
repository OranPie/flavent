from __future__ import annotations

import json
from pathlib import Path

from flavent.flm import FLM_FILENAME, FLM_LOCK_FILENAME, add_dependency, init_project, install, read_json


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
