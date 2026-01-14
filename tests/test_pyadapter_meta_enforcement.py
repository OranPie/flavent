from __future__ import annotations

import json
from pathlib import Path

import pytest

from flavent.pyadapter import AdapterManager


def _write_project(root: Path, *, caps: list[str], allow: list[str]) -> None:
    (root / "flm.json").write_text(
        json.dumps(
            {
                "flmVersion": 1,
                "package": {"name": "proj", "version": "0.1.0", "entry": "src/main.flv"},
                "toolchain": {"flavent": ">=0.1.0"},
                "dependencies": {},
                "devDependencies": {},
                "pythonAdapters": [
                    {
                        "name": "demo",
                        "source": {"path": "vendor/py_demo"},
                        "capabilities": caps,
                        "allow": allow,
                    }
                ],
                "extensions": {},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_pyadapter_meta_rejects_missing_capability(tmp_path: Path):
    root = tmp_path / "proj"
    (root / "vendor" / "py_demo").mkdir(parents=True)

    adapter_root = root / "vendor" / "py_demo"
    (adapter_root / "flavent_adapter.py").write_text(
        "PLUGIN_ID = 'org.example.demo'\n"
        "API_VERSION = 1\n"
        "CAPABILITIES = []\n"
        "EXPORTS = {'echo': {'args': ['Bytes'], 'ret': 'Bytes'}}\n"
        "def dispatch(fn: str, payload: bytes) -> bytes:\n"
        "  return payload\n",
        encoding="utf-8",
    )

    _write_project(root, caps=["pure_math"], allow=["echo"])

    mgr = AdapterManager(root)
    try:
        with pytest.raises(Exception):
            mgr.call("demo", "echo", b"hi")
    finally:
        mgr.close()


def test_pyadapter_meta_rejects_allow_not_in_exports(tmp_path: Path):
    root = tmp_path / "proj"
    (root / "vendor" / "py_demo").mkdir(parents=True)

    adapter_root = root / "vendor" / "py_demo"
    (adapter_root / "flavent_adapter.py").write_text(
        "PLUGIN_ID = 'org.example.demo'\n"
        "API_VERSION = 1\n"
        "CAPABILITIES = ['pure_math']\n"
        "EXPORTS = {}\n"
        "def dispatch(fn: str, payload: bytes) -> bytes:\n"
        "  return payload\n",
        encoding="utf-8",
    )

    _write_project(root, caps=["pure_math"], allow=["echo"])

    mgr = AdapterManager(root)
    try:
        with pytest.raises(Exception):
            mgr.call("demo", "echo", b"hi")
    finally:
        mgr.close()
