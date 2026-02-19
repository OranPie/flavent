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
