from __future__ import annotations

import json
import os
import shutil
import subprocess
import re
from pathlib import Path
from typing import Any


FLM_FILENAME = "flm.json"
FLM_LOCK_FILENAME = "flm.lock.json"

_FLV_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class FlmError(RuntimeError):
    pass


def find_project_root(start: Path) -> Path | None:
    p = start.resolve()
    if p.is_file():
        p = p.parent
    while True:
        if (p / FLM_FILENAME).exists():
            return p
        if p.parent == p:
            return None
        p = p.parent


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise FlmError(f"Missing {path}") from e


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def default_manifest(*, name: str) -> dict[str, Any]:
    return {
        "flmVersion": 1,
        "package": {
            "name": name,
            "version": "0.1.0",
            "entry": "src/main.flv",
        },
        "toolchain": {"flavent": ">=0.1.0"},
        "dependencies": {},
        "devDependencies": {},
        "pythonAdapters": [],
        "extensions": {},
    }


def ensure_project_skeleton(root: Path, *, name: str) -> None:
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "tests_flv").mkdir(parents=True, exist_ok=True)
    (root / "vendor").mkdir(parents=True, exist_ok=True)
    main = root / "src" / "main.flv"
    if not main.exists():
        main.write_text(
            "use consoleIO\n\nsector main:\n  fn run() -> Unit = do:\n    rpc print(\"hello\")\n    return ()\n\nrun()\n",
            encoding="utf-8",
        )


def init_project(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    mf = root / FLM_FILENAME
    if mf.exists():
        raise FlmError(f"{FLM_FILENAME} already exists")
    name = root.name
    ensure_project_skeleton(root, name=name)
    write_json(mf, default_manifest(name=name))
    return mf


def add_dependency(
    root: Path,
    *,
    name: str,
    git: str | None = None,
    rev: str | None = None,
    path: str | None = None,
    dev: bool = False,
) -> None:
    mf_path = root / FLM_FILENAME
    mf = read_json(mf_path)
    deps_key = "devDependencies" if dev else "dependencies"
    deps = mf.get(deps_key)
    if not isinstance(deps, dict):
        raise FlmError(f"bad manifest: {deps_key} must be an object")

    if git is not None:
        spec: dict[str, Any] = {"git": git}
        if rev:
            spec["rev"] = rev
    elif path is not None:
        spec = {"path": path}
    else:
        raise FlmError("dependency must specify --git or --path")

    deps[name] = spec
    mf[deps_key] = deps
    write_json(mf_path, mf)


def list_dependencies(root: Path) -> list[tuple[str, dict[str, Any]]]:
    mf = read_json(root / FLM_FILENAME)
    deps = mf.get("dependencies")
    if not isinstance(deps, dict):
        return []
    out: list[tuple[str, dict[str, Any]]] = []
    for k, v in deps.items():
        if isinstance(v, dict):
            out.append((k, v))
    return out


def install(root: Path) -> None:
    root = root.resolve()
    vendor = root / "vendor"
    vendor.mkdir(parents=True, exist_ok=True)

    cache_root = root / ".flavent" / "git"
    cache_root.mkdir(parents=True, exist_ok=True)

    mf = read_json(root / FLM_FILENAME)
    deps = mf.get("dependencies", {})
    if not isinstance(deps, dict):
        raise FlmError("bad manifest: dependencies must be an object")

    adapters_any = mf.get("pythonAdapters", [])
    if adapters_any is None:
        adapters_any = []
    if not isinstance(adapters_any, list):
        raise FlmError("bad manifest: pythonAdapters must be a list")

    resolved: dict[str, Any] = {}

    for name, spec_any in deps.items():
        if not isinstance(spec_any, dict):
            continue
        dst = vendor / name

        if "path" in spec_any:
            src = (root / str(spec_any["path"])) if not str(spec_any["path"]).startswith("/") else Path(str(spec_any["path"]))
            src = src.resolve()
            if not src.exists():
                raise FlmError(f"path dependency not found: {name}: {src}")
            if dst.is_symlink():
                dst.unlink()
            elif dst.is_dir():
                shutil.rmtree(dst)
            elif dst.exists():
                dst.unlink()
            os.symlink(src, dst, target_is_directory=True)
            resolved[name] = {"path": str(spec_any["path"])}
            continue

        if "git" in spec_any:
            git_url = str(spec_any["git"])
            rev = str(spec_any.get("rev", ""))
            repo = cache_root / name
            if repo.exists():
                # Keep existing clone.
                pass
            else:
                subprocess.run(["git", "clone", git_url, str(repo)], check=True)
            if rev:
                subprocess.run(["git", "-C", str(repo), "checkout", rev], check=True)

            # Pin actual commit in lock.
            head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()

            # vendor/<name> is a symlink to cached repo.
            if dst.is_symlink():
                dst.unlink()
            elif dst.is_dir():
                shutil.rmtree(dst)
            elif dst.exists():
                dst.unlink()
            os.symlink(repo, dst, target_is_directory=True)

            resolved[name] = {"git": git_url, "rev": head}
            continue

    _generate_py_wrappers(root, adapters_any)

    lock = {
        "flmLockVersion": 1,
        "resolved": resolved,
    }
    write_json(root / FLM_LOCK_FILENAME, lock)


def export_manifest(root: Path, *, out_path: Path) -> None:
    mf = read_json(root / FLM_FILENAME)
    lock_path = root / FLM_LOCK_FILENAME
    if lock_path.exists():
        lock = read_json(lock_path)
        mf["lock"] = lock
    write_json(out_path, mf)


def _ensure_ident(s: str, *, what: str) -> str:
    if not _FLV_IDENT_RE.match(s):
        raise FlmError(f"invalid {what} identifier: {s}")
    return s


def _generate_py_wrappers(root: Path, adapters_any: list[Any]) -> None:
    out_dir = root / "vendor" / "pyadapters"
    out_dir.mkdir(parents=True, exist_ok=True)

    names: list[str] = []
    for it in adapters_any:
        if not isinstance(it, dict):
            continue
        name = str(it.get("name", ""))
        if not name:
            continue
        _ensure_ident(name, what="pythonAdapters.name")
        allow_any = it.get("allow", [])
        if allow_any is None:
            allow_any = []
        if not isinstance(allow_any, list):
            raise FlmError(f"bad pythonAdapters[{name}]: allow must be a list")
        allow = [str(x) for x in allow_any]

        # Generate: vendor/pyadapters/<name>.flv
        mod_path = out_dir / f"{name}.flv"
        lines: list[str] = []
        lines.append("use py\n")
        lines.append("\n")
        lines.append(f"sector {name}:\n")
        for m in allow:
            _ensure_ident(m, what=f"pythonAdapters[{name}].allow")
            # All adapters are bytes-in/bytes-out for now.
            lines.append(
                f"  fn {m}(payload: Bytes) -> Result[Bytes, Str] = rpc py.invoke(\"{name}\", \"{m}\", payload)\n"
            )
        mod_path.write_text("".join(lines), encoding="utf-8")
        names.append(name)

    # Generate barrel module: vendor/pyadapters/__init__.flv
    init_path = out_dir / "__init__.flv"
    init_lines = ["".join([f"use pyadapters.{n}\n" for n in sorted(names)])]
    init_path.write_text("".join(init_lines), encoding="utf-8")
