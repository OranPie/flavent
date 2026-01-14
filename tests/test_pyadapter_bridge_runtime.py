from __future__ import annotations

import json
from pathlib import Path

from flavent.lexer import lex
from flavent.parser import parse_program
from flavent.lower import lower_resolved
from flavent.resolve import resolve_program_with_stdlib
from flavent.runtime import Bridge, run_hir_program
from flavent.typecheck import check_program
from flavent.pyadapter import AdapterManager


class _PyBridge(Bridge):
    def __init__(self, root: Path):
        self.mgr = AdapterManager(root)

    def call(self, name: str, args: list[object]) -> object:
        # Only allow the single bridge entrypoint.
        if name != "pyAdapterCall":
            raise RuntimeError(f"unexpected bridge call: {name}")
        adapter = str(args[0])
        fn = str(args[1])
        payload = bytes(args[2])
        try:
            out = self.mgr.call(adapter, fn, payload)
            return ("Ok", [out])
        except Exception as e:
            return ("Err", [str(e)])

    def close(self) -> None:
        self.mgr.close()


def test_pyadapter_call_via_bridge_runtime(tmp_path: Path):
    # Project root with a demo adapter
    root = tmp_path / "proj"
    (root / "vendor" / "py_demo").mkdir(parents=True)
    (root / "src").mkdir(parents=True)

    adapter_root = root / "vendor" / "py_demo"
    (adapter_root / "flavent_adapter.py").write_text(
        "PLUGIN_ID = 'org.example.demo'\n"
        "API_VERSION = 1\n"
        "CAPABILITIES = ['pure_math']\n"
        "EXPORTS = {'echo': {'args': ['Bytes'], 'ret': 'Bytes'}}\n"
        "def dispatch(fn: str, payload: bytes) -> bytes:\n"
        "  if fn == 'echo':\n"
        "    return payload + b'!'\n"
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

    src = (
        "use flvtest\n"
        "use py\n"
        "use bytelib\n\n"
        "type Event.Test = {}\n\n"
        "sector main:\n"
        "  on Event.Test -> do:\n"
        "    let r = rpc py.invoke(\"demo\", \"echo\", b\"hi\")\n"
        "    match r:\n"
        "      Ok(b) -> do:\n"
        "        assertEq(bytesLen(b), 3)?\n"
        "        assertEq(bytesGet(b, 2), 33)?\n"
        "      Err(e) -> do:\n"
        "        assertTrue(false)?\n"
        "    stop()\n\n"
        "run()\n"
    )

    p = root / "src" / "main.flv"
    prog = parse_program(lex(str(p), src))
    res = resolve_program_with_stdlib(
        prog,
        use_stdlib=True,
        module_roots=[root / "src", root / "vendor", root],
    )
    hir = lower_resolved(res)
    check_program(hir, res)

    bridge = _PyBridge(root)
    try:
        run_hir_program(hir, res, entry_event_type="Event.Test", bridge=bridge)
    finally:
        bridge.close()
