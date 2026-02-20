from __future__ import annotations

import json
import subprocess
from pathlib import Path


def test_stdlib_bridge_boundary_repo_allowlist_clean(tmp_path: Path):
    out = tmp_path / "bridge-boundary.json"
    subprocess.run(
        [
            "python3",
            "scripts/stdlib_bridge_boundary.py",
            "--allowlist",
            "docs/stdlib_bridge_boundary_allowlist.json",
            "--json-out",
            str(out),
            "--fail-on-violations",
            "--fail-on-stale",
        ],
        check=True,
    )
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["schema_version"] == "1.0"
    payload = report["artifacts"]["stdlib_bridge_boundary"]
    assert payload["violation_count"] == 0
    assert payload["stale_count"] == 0


def test_stdlib_bridge_boundary_detects_unapproved_module(tmp_path: Path):
    stdlib_root = tmp_path / "stdlib"
    stdlib_root.mkdir(parents=True)
    (stdlib_root / "_bridge_python.flv").write_text(
        "fn strLen(s: Str) -> Int = 0\nsector _bridge_python:\n  fn nowMillis() -> Int = 0\n",
        encoding="utf-8",
    )
    (stdlib_root / "bad").mkdir(parents=True)
    (stdlib_root / "bad" / "__init__.flv").write_text(
        "use _bridge_python\nfn f() -> Int = rpc _bridge_python.nowMillis()\n",
        encoding="utf-8",
    )

    allowlist = tmp_path / "allow.json"
    allowlist.write_text(json.dumps({"entries": []}, indent=2), encoding="utf-8")
    out = tmp_path / "bridge-boundary.json"
    cp = subprocess.run(
        [
            "python3",
            "scripts/stdlib_bridge_boundary.py",
            "--stdlib-root",
            str(stdlib_root),
            "--allowlist",
            str(allowlist),
            "--json-out",
            str(out),
            "--fail-on-violations",
        ],
        check=False,
    )
    assert cp.returncode == 1
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["status"] == "failed"
    payload = report["artifacts"]["stdlib_bridge_boundary"]
    assert payload["violation_count"] == 1
    assert payload["violations"][0]["module"] == "bad/__init__"


def test_stdlib_bridge_boundary_detects_stale_allowlist(tmp_path: Path):
    stdlib_root = tmp_path / "stdlib"
    stdlib_root.mkdir(parents=True)
    (stdlib_root / "_bridge_python.flv").write_text(
        "fn strLen(s: Str) -> Int = 0\nsector _bridge_python:\n  fn nowMillis() -> Int = 0\n",
        encoding="utf-8",
    )
    (stdlib_root / "ok").mkdir(parents=True)
    (stdlib_root / "ok" / "__init__.flv").write_text(
        "use _bridge_python\nfn f() -> Int = rpc _bridge_python.nowMillis()\n",
        encoding="utf-8",
    )

    allowlist = tmp_path / "allow.json"
    allowlist.write_text(
        json.dumps(
            {
                "entries": [
                    {"module": "ok/__init__", "note": "ok"},
                    {"module": "old/__init__", "note": "stale"},
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    out = tmp_path / "bridge-boundary.json"
    cp = subprocess.run(
        [
            "python3",
            "scripts/stdlib_bridge_boundary.py",
            "--stdlib-root",
            str(stdlib_root),
            "--allowlist",
            str(allowlist),
            "--json-out",
            str(out),
            "--fail-on-stale",
        ],
        check=False,
    )
    assert cp.returncode == 1
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["status"] == "failed"
    payload = report["artifacts"]["stdlib_bridge_boundary"]
    assert payload["stale_count"] == 1
    assert payload["stale_allowlist"][0]["module"] == "old/__init__"
