from __future__ import annotations

import json
from pathlib import Path

import pytest

from flavent.flm import FlmError
from flavent.pyadapter import AdapterManager


def test_pyadapter_v2_allows_only_allowlisted_calls(tmp_path: Path):
    # Project root with flm.json
    root = tmp_path / "proj"
    root.mkdir(parents=True)

    # Adapter package
    adapter_root = root / "vendor" / "py_demo"
    adapter_root.mkdir(parents=True)
    (adapter_root / "flavent_adapter.py").write_text(
        "PLUGIN_ID = 'org.example.demo'\n"
        "API_VERSION = 1\n"
        "CAPABILITIES = ['pure_math']\n"
        "EXPORTS = {'echo': {'args': ['Bytes'], 'ret': 'Bytes'}, 'nope': {'args': [], 'ret': 'Bytes'}}\n"
        "def dispatch(fn: str, payload: bytes) -> bytes:\n"
        "  if fn == 'echo':\n"
        "    return payload + b'!'\n"
        "  if fn == 'nope':\n"
        "    return b'nope'\n"
        "  raise RuntimeError('unknown fn')\n",
        encoding="utf-8",
    )

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
                        "capabilities": ["pure_math"],
                        "allow": ["echo"],
                    }
                ],
                "extensions": {},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    mgr = AdapterManager(root)
    try:
        out = mgr.call("demo", "echo", b"hi")
        assert out == b"hi!"

        with pytest.raises(Exception):
            mgr.call("demo", "nope", b"")
    finally:
        mgr.close()


@pytest.mark.parametrize(
    ("adapters", "msg_re"),
    [
        ([123], r"pythonAdapters\[0\].*object"),
        ([{"source": {"path": "vendor/py_demo"}}], r"pythonAdapters\[0\].*missing name"),
        (
            [{"name": "demo", "source": {"path": "vendor/py_demo"}}, {"name": "demo", "source": {"path": "vendor/py_demo"}}],
            r"duplicate adapter name",
        ),
        ([{"name": "demo", "source": {"path": "vendor/py_demo"}, "allow": [123]}], r"pythonAdapters\[demo\]\.allow"),
    ],
)
def test_pyadapter_v2_rejects_invalid_manifest_entries(
    tmp_path: Path,
    adapters: list[object],
    msg_re: str,
):
    root = tmp_path / "proj"
    root.mkdir(parents=True)
    (root / "flm.json").write_text(
        json.dumps(
            {
                "flmVersion": 1,
                "package": {"name": "proj", "version": "0.1.0", "entry": "src/main.flv"},
                "toolchain": {"flavent": ">=0.1.0"},
                "dependencies": {},
                "devDependencies": {},
                "pythonAdapters": adapters,
                "extensions": {},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(FlmError, match=msg_re):
        AdapterManager(root)
