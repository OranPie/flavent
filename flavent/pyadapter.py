from __future__ import annotations

import json
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from queue import Queue
from typing import Any

from .flm import FLM_FILENAME, FlmError, read_json


@dataclass(frozen=True)
class PythonAdapterDecl:
    name: str
    source_path: Path
    capabilities: list[str]
    allow: list[str]


@dataclass(frozen=True)
class _Response:
    ok: bool
    payload: bytes
    error: str | None


class AdapterProcess:
    def __init__(self, adapter_root: Path):
        self.adapter_root = adapter_root.resolve()
        self._proc: subprocess.Popen[str] | None = None
        self._next_id = 1
        self._pending: dict[int, Queue[_Response]] = {}
        self._lock = threading.Lock()
        self._reader: threading.Thread | None = None
        self._meta_cache: dict[str, Any] | None = None

    def start(self) -> None:
        if self._proc is not None:
            return

        cmd = [sys.executable, "-m", "flavent.pyadapter_host", str(self.adapter_root)]
        self._proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        assert self._proc.stdout is not None

        def _read_loop() -> None:
            assert self._proc is not None
            assert self._proc.stdout is not None
            for line in self._proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                    rid = int(msg.get("id"))
                    ok = bool(msg.get("ok"))
                    if ok:
                        import base64

                        payload = base64.b64decode(str(msg.get("payload_b64", "")).encode("ascii"))
                        resp = _Response(ok=True, payload=payload, error=None)
                    else:
                        resp = _Response(ok=False, payload=b"", error=str(msg.get("error", "")))
                except Exception as e:
                    # Unparseable output: treat as a global error.
                    resp = _Response(ok=False, payload=b"", error=f"bad adapter response: {e}")
                    rid = 0

                with self._lock:
                    q = self._pending.get(rid)
                if q is not None:
                    q.put(resp)

        self._reader = threading.Thread(target=_read_loop, name=f"pyadapter-reader-{self.adapter_root}", daemon=True)
        self._reader.start()

    def call(self, method: str, payload: bytes, *, timeout_seconds: float = 5.0) -> bytes:
        self.start()
        assert self._proc is not None
        assert self._proc.stdin is not None

        import base64
        import time

        with self._lock:
            rid = self._next_id
            self._next_id += 1
            q: Queue[_Response] = Queue(maxsize=1)
            self._pending[rid] = q

        req = {"id": rid, "method": method, "payload_b64": base64.b64encode(payload).decode("ascii")}
        self._proc.stdin.write(json.dumps(req, ensure_ascii=False) + "\n")
        self._proc.stdin.flush()

        deadline = time.time() + timeout_seconds
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                with self._lock:
                    self._pending.pop(rid, None)
                raise TimeoutError(f"pyadapter call timeout: {method}")
            try:
                resp = q.get(timeout=remaining)
            except Exception:
                continue
            finally:
                with self._lock:
                    self._pending.pop(rid, None)

            if not resp.ok:
                raise RuntimeError(resp.error or "pyadapter error")
            return resp.payload

    def close(self) -> None:
        if self._proc is None:
            return
        try:
            if self._proc.stdin is not None:
                self._proc.stdin.close()
        except Exception:
            pass
        try:
            self._proc.terminate()
        except Exception:
            pass
        try:
            self._proc.wait(timeout=2)
        except Exception:
            try:
                self._proc.kill()
            except Exception:
                pass
        self._proc = None
        self._meta_cache = None


def load_python_adapters(project_root: Path) -> list[PythonAdapterDecl]:
    mf_path = project_root / FLM_FILENAME
    mf = read_json(mf_path)
    adapters_any = mf.get("pythonAdapters", [])
    if adapters_any is None:
        return []
    if not isinstance(adapters_any, list):
        raise FlmError("bad manifest: pythonAdapters must be a list")

    out: list[PythonAdapterDecl] = []
    for it in adapters_any:
        if not isinstance(it, dict):
            continue
        name = str(it.get("name", ""))
        if not name:
            continue
        source = it.get("source")
        if not isinstance(source, dict):
            raise FlmError(f"bad pythonAdapters[{name}]: source must be an object")
        if "path" not in source:
            raise FlmError(f"bad pythonAdapters[{name}]: only source.path is supported in v2 MVP")
        sp = str(source.get("path"))
        source_path = (project_root / sp).resolve() if not sp.startswith("/") else Path(sp).resolve()

        caps_any = it.get("capabilities", [])
        allow_any = it.get("allow", [])
        wrappers_any = it.get("wrappers", [])
        if not isinstance(caps_any, list):
            raise FlmError(f"bad pythonAdapters[{name}]: capabilities must be a list")
        allow: list[str] = []
        if isinstance(allow_any, list):
            for entry in allow_any:
                if isinstance(entry, str):
                    allow.append(entry)
                elif isinstance(entry, dict):
                    name_entry = str(entry.get("name", ""))
                    if not name_entry:
                        raise FlmError(f"bad pythonAdapters[{name}]: allow entry missing name")
                    allow.append(name_entry)
        elif allow_any is not None:
            raise FlmError(f"bad pythonAdapters[{name}]: allow must be a list")

        if not allow and wrappers_any is not None:
            if not isinstance(wrappers_any, list):
                raise FlmError(f"bad pythonAdapters[{name}]: wrappers must be a list")
            for entry in wrappers_any:
                if isinstance(entry, str):
                    allow.append(entry)
                elif isinstance(entry, dict):
                    name_entry = str(entry.get("name", ""))
                    if not name_entry:
                        raise FlmError(f"bad pythonAdapters[{name}]: wrappers entry missing name")
                    allow.append(name_entry)

        caps = [str(x) for x in caps_any]
        out.append(PythonAdapterDecl(name=name, source_path=source_path, capabilities=caps, allow=allow))

    return out


def _load_adapter_meta(proc: AdapterProcess) -> dict[str, Any]:
    if proc._meta_cache is not None:
        return proc._meta_cache
    raw = proc.call("__meta__", b"", timeout_seconds=5.0)
    try:
        meta = json.loads(raw.decode("utf-8"))
        if not isinstance(meta, dict):
            raise FlmError("meta is not an object")
        proc._meta_cache = meta
        return meta
    except Exception as e:
        raise FlmError(f"bad adapter meta response: {e}")


def _ensure_subset(required: list[str], available: list[str], *, what: str) -> None:
    missing = [x for x in required if x not in available]
    if missing:
        raise FlmError(f"python adapter {what} not supported: {missing}")


class AdapterManager:
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.adapters = {a.name: a for a in load_python_adapters(self.project_root)}
        self._procs: dict[str, AdapterProcess] = {}

    def call(self, adapter: str, fn: str, payload: bytes) -> bytes:
        spec = self.adapters.get(adapter)
        if spec is None:
            raise FlmError(f"unknown python adapter: {adapter}")
        if fn not in spec.allow:
            raise FlmError(f"python adapter call not allowed: {adapter}.{fn}")
        proc = self._procs.get(adapter)
        if proc is None:
            proc = AdapterProcess(spec.source_path)
            self._procs[adapter] = proc

        # v2 enforcement: adapter-declared meta must cover requested capabilities and allowed methods.
        meta = _load_adapter_meta(proc)
        caps_avail = list(meta.get("capabilities", []))
        exports = meta.get("exports", {})
        if not isinstance(exports, dict):
            exports = {}
        _ensure_subset(spec.capabilities, caps_avail, what="capabilities")
        _ensure_subset(spec.allow, list(exports.keys()), what="exports")

        return proc.call(fn, payload)

    def close(self) -> None:
        for p in list(self._procs.values()):
            p.close()
        self._procs.clear()
