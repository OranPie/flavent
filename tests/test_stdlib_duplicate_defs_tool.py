from __future__ import annotations

import json
import subprocess
from pathlib import Path


def test_stdlib_duplicate_defs_report_detects_cross_module_symbol(tmp_path: Path):
    out = tmp_path / "dup.json"
    subprocess.run(
        [
            "python3",
            "scripts/stdlib_duplicate_defs.py",
            "--json-out",
            str(out),
        ],
        check=True,
    )
    data = json.loads(out.read_text(encoding="utf-8"))
    dups = data.get("duplicates", [])
    target = next((d for d in dups if d.get("kind") == "fn" and d.get("name") == "exists"), None)
    assert target is not None
    mods = set(target.get("modules", []))
    assert "file" in mods
    assert "fslib" in mods


def test_stdlib_duplicate_defs_allowlist_marks_approved_and_fails_on_unapproved(tmp_path: Path):
    stdlib_root = tmp_path / "stdlib"
    (stdlib_root / "a").mkdir(parents=True)
    (stdlib_root / "b").mkdir(parents=True)
    (stdlib_root / "c").mkdir(parents=True)
    (stdlib_root / "a" / "__init__.flv").write_text("fn foo(x: Int) -> Int = x\n", encoding="utf-8")
    (stdlib_root / "b" / "__init__.flv").write_text("fn foo(x: Int) -> Int = x\nfn bar(x: Int) -> Int = x\n", encoding="utf-8")
    (stdlib_root / "c" / "__init__.flv").write_text("fn bar(x: Int) -> Int = x\n", encoding="utf-8")

    allowlist = tmp_path / "allowlist.json"
    allowlist.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "kind": "fn",
                        "name": "foo",
                        "modules": ["a", "b"],
                        "canonical": "a",
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    out = tmp_path / "dup.json"
    cp = subprocess.run(
        [
            "python3",
            "scripts/stdlib_duplicate_defs.py",
            "--stdlib-root",
            str(stdlib_root),
            "--allowlist",
            str(allowlist),
            "--json-out",
            str(out),
            "--fail-on-duplicates",
        ],
        check=False,
    )
    assert cp.returncode == 1

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["duplicate_count"] == 2
    assert data["approved_count"] == 1
    assert data["unapproved_count"] == 1
    dups = {(d["name"], tuple(d["modules"])): d for d in data["duplicates"]}
    assert dups[("foo", ("a", "b"))]["approved"] is True
    assert dups[("bar", ("b", "c"))]["approved"] is False


def test_stdlib_duplicate_defs_ignores_internal_modules_by_default(tmp_path: Path):
    stdlib_root = tmp_path / "stdlib"
    (stdlib_root / "time").mkdir(parents=True)
    (stdlib_root / "_bridge_python.flv").write_text(
        "sector _bridge_python:\n  fn nowMillis() -> Int = 0\n",
        encoding="utf-8",
    )
    (stdlib_root / "time" / "__init__.flv").write_text(
        "sector time:\n  fn nowMillis() -> Int = rpc _bridge_python.nowMillis()\n",
        encoding="utf-8",
    )

    out_public = tmp_path / "public.json"
    subprocess.run(
        [
            "python3",
            "scripts/stdlib_duplicate_defs.py",
            "--stdlib-root",
            str(stdlib_root),
            "--json-out",
            str(out_public),
        ],
        check=True,
    )
    public_report = json.loads(out_public.read_text(encoding="utf-8"))
    assert public_report["duplicate_count"] == 0

    out_all = tmp_path / "all.json"
    subprocess.run(
        [
            "python3",
            "scripts/stdlib_duplicate_defs.py",
            "--stdlib-root",
            str(stdlib_root),
            "--include-internal-modules",
            "--json-out",
            str(out_all),
        ],
        check=True,
    )
    all_report = json.loads(out_all.read_text(encoding="utf-8"))
    assert all_report["duplicate_count"] == 1
