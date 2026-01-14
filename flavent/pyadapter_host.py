from __future__ import annotations

import base64
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


def _load_adapter(adapter_root: Path):
    adapter_file = adapter_root / "flavent_adapter.py"
    if not adapter_file.exists():
        raise RuntimeError(f"missing flavent_adapter.py in {adapter_root}")

    spec = importlib.util.spec_from_file_location("_flavent_adapter", adapter_file)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load adapter module")

    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    # Validate required interface.
    for attr in ("PLUGIN_ID", "API_VERSION", "CAPABILITIES", "EXPORTS", "dispatch"):
        if not hasattr(mod, attr):
            raise RuntimeError(f"adapter missing required attribute: {attr}")

    dispatch = getattr(mod, "dispatch")
    if not callable(dispatch):
        raise RuntimeError("adapter dispatch is not callable")

    return mod


def _b64_decode(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"))


def _b64_encode(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 1:
        print("usage: python -m flavent.pyadapter_host <adapter_root>", file=sys.stderr)
        return 2

    adapter_root = Path(argv[0]).resolve()
    mod = _load_adapter(adapter_root)
    dispatch = getattr(mod, "dispatch")

    meta = {
        "plugin_id": str(getattr(mod, "PLUGIN_ID")),
        "api_version": int(getattr(mod, "API_VERSION")),
        "capabilities": list(getattr(mod, "CAPABILITIES")),
        "exports": dict(getattr(mod, "EXPORTS")),
    }

    # Protocol: newline-delimited JSON.
    # Request:  {"id": 1, "method": "name", "payload_b64": "..."}
    # Response: {"id": 1, "ok": true, "payload_b64": "..."}
    # Error:    {"id": 1, "ok": false, "error": "..."}
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            rid = int(req.get("id"))
            method = str(req.get("method"))
            payload_b64 = str(req.get("payload_b64", ""))
            payload = _b64_decode(payload_b64)

            if method == "__meta__":
                out = json.dumps(meta, ensure_ascii=False).encode("utf-8")
            else:
                out = dispatch(method, payload)
            if not isinstance(out, (bytes, bytearray)):
                raise RuntimeError("dispatch must return bytes")

            resp = {"id": rid, "ok": True, "payload_b64": _b64_encode(bytes(out))}
        except Exception as e:
            rid_any = None
            try:
                rid_any = int(json.loads(line).get("id"))
            except Exception:
                rid_any = 0
            resp = {"id": rid_any, "ok": False, "error": str(e)}

        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
