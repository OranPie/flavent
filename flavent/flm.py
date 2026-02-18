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
    _ensure_ident(name, what="dependency name")
    if rev and not git:
        raise FlmError("dependency rev requires --git")
    if git and path:
        raise FlmError("dependency must specify only one source: --git or --path")

    mf_path = root / FLM_FILENAME
    mf = read_json(mf_path)
    deps_key = "devDependencies" if dev else "dependencies"
    deps = mf.get(deps_key)
    if not isinstance(deps, dict):
        raise FlmError(f"bad manifest: {deps_key} must be an object")

    if git is not None:
        spec = _normalize_dependency_spec(name, {"git": git, **({"rev": rev} if rev else {})})
    elif path is not None:
        spec = _normalize_dependency_spec(name, {"path": path})
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


def _normalize_dependency_spec(name: str, spec_any: Any) -> dict[str, str]:
    if not isinstance(spec_any, dict):
        raise FlmError(f"bad manifest: dependency '{name}' must be an object")

    has_git = "git" in spec_any
    has_path = "path" in spec_any
    if has_git == has_path:
        raise FlmError(f"bad manifest: dependency '{name}' must specify exactly one of 'git' or 'path'")

    if has_git:
        git = str(spec_any.get("git", "")).strip()
        if not git:
            raise FlmError(f"bad manifest: dependency '{name}' has empty git url")
        out = {"git": git}
        if "rev" in spec_any:
            rev = str(spec_any.get("rev", "")).strip()
            if not rev:
                raise FlmError(f"bad manifest: dependency '{name}' has empty rev")
            out["rev"] = rev
        return out

    path = str(spec_any.get("path", "")).strip()
    if not path:
        raise FlmError(f"bad manifest: dependency '{name}' has empty path")
    if "rev" in spec_any:
        raise FlmError(f"bad manifest: dependency '{name}' cannot set rev without git")
    return {"path": path}


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

    for name_any, spec_any in deps.items():
        name = str(name_any)
        _ensure_ident(name, what="dependency name")
        spec = _normalize_dependency_spec(name, spec_any)
        dst = vendor / name

        if "path" in spec:
            src = (root / spec["path"]) if not spec["path"].startswith("/") else Path(spec["path"])
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
            resolved[name] = {"path": spec["path"]}
            continue

        if "git" in spec:
            git_url = spec["git"]
            rev = spec.get("rev", "")
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


def _adapter_names_from_list(items: Any, *, what: str) -> list[str]:
    if items is None:
        return []
    if not isinstance(items, list):
        raise FlmError(f"bad {what}: must be a list")
    names: list[str] = []
    seen: set[str] = set()
    for i, it in enumerate(items):
        if isinstance(it, str):
            name = it.strip()
            if not name:
                raise FlmError(f"bad {what}[{i}]: empty name")
            _ensure_ident(name, what=f"{what}[{i}]")
            if name in seen:
                raise FlmError(f"bad {what}: duplicate name: {name}")
            seen.add(name)
            names.append(name)
            continue
        if isinstance(it, dict):
            name = str(it.get("name", "")).strip()
            if not name:
                raise FlmError(f"bad {what}[{i}]: missing name")
            _ensure_ident(name, what=f"{what}[{i}].name")
            if name in seen:
                raise FlmError(f"bad {what}: duplicate name: {name}")
            seen.add(name)
            names.append(name)
            continue
        raise FlmError(f"bad {what}[{i}]: invalid entry")
    return names


def _normalize_args(args_any: Any, *, adapter: str, method: str, codec: str) -> list[tuple[str, str]]:
    if args_any is None:
        if codec == "bytes":
            return [("payload", "Bytes")]
        raise FlmError(f"bad pythonAdapters[{adapter}].wrappers[{method}]: args must be a list")
    if not isinstance(args_any, list):
        raise FlmError(f"bad pythonAdapters[{adapter}].wrappers[{method}]: args must be a list")

    out: list[tuple[str, str]] = []
    for i, arg in enumerate(args_any):
        if isinstance(arg, str):
            out.append((f"arg{i}", str(arg)))
            continue
        if isinstance(arg, dict):
            name = str(arg.get("name", ""))
            typ = str(arg.get("type", ""))
            if not name or not typ:
                raise FlmError(
                    f"bad pythonAdapters[{adapter}].wrappers[{method}]: args[{i}] requires name and type"
                )
            _ensure_ident(name, what=f"pythonAdapters[{adapter}].wrappers[{method}].args[{i}].name")
            out.append((name, typ))
            continue
        raise FlmError(f"bad pythonAdapters[{adapter}].wrappers[{method}]: args[{i}] invalid")
    return out


def _json_expr_for_type(arg_name: str, typ: str, *, adapter: str, method: str) -> str:
    if typ == "Int":
        return f"JInt({arg_name})"
    if typ == "Float":
        return f"JFloat({arg_name})"
    if typ == "Bool":
        return f"JBool({arg_name})"
    if typ == "Str":
        return f"JStr({arg_name})"
    if typ == "JsonValue":
        return arg_name
    if typ == "Unit":
        return "JNull"
    raise FlmError(f"bad pythonAdapters[{adapter}].wrappers[{method}]: unsupported json arg type: {typ}")


def _json_decode_match(typ: str, *, adapter: str, method: str) -> list[str]:
    err = f"pyadapters.{adapter}.{method}: expected {typ}"
    if typ == "Int":
        return ["        JInt(v) -> Ok(v)\n", f"        _ -> Err(\"{err}\")\n"]
    if typ == "Float":
        return ["        JFloat(v) -> Ok(v)\n", f"        _ -> Err(\"{err}\")\n"]
    if typ == "Bool":
        return ["        JBool(v) -> Ok(v)\n", f"        _ -> Err(\"{err}\")\n"]
    if typ == "Str":
        return ["        JStr(v) -> Ok(v)\n", f"        _ -> Err(\"{err}\")\n"]
    if typ == "JsonValue":
        return ["        _ -> Ok(j)\n"]
    if typ == "Unit":
        return ["        JNull -> Ok(())\n", f"        _ -> Err(\"{err}\")\n"]
    raise FlmError(f"bad pythonAdapters[{adapter}].wrappers[{method}]: unsupported json ret type: {typ}")


def _generate_py_wrappers(root: Path, adapters_any: list[Any]) -> None:
    out_dir = root / "vendor" / "pyadapters"
    out_dir.mkdir(parents=True, exist_ok=True)

    names: list[str] = []
    seen_adapters: set[str] = set()
    for i, it in enumerate(adapters_any):
        if not isinstance(it, dict):
            raise FlmError(f"bad pythonAdapters[{i}]: must be an object")

        name = str(it.get("name", "")).strip()
        if not name:
            raise FlmError(f"bad pythonAdapters[{i}]: missing name")
        _ensure_ident(name, what=f"pythonAdapters[{i}].name")
        if name in seen_adapters:
            raise FlmError(f"bad pythonAdapters: duplicate adapter name: {name}")
        seen_adapters.add(name)

        allow_any = it.get("allow", [])
        wrappers_any = it.get("wrappers")
        allow = _adapter_names_from_list(allow_any, what=f"pythonAdapters[{name}].allow")
        if wrappers_any is None:
            wrappers_any = allow_any

        # Generate: vendor/pyadapters/<name>.flv
        mod_path = out_dir / f"{name}.flv"
        lines: list[str] = []
        lines.append("use py\n")
        uses_json = False
        uses_list = False
        wrapper_specs: list[dict[str, Any]] = []

        if wrappers_any is None:
            wrappers_any = []
        if not isinstance(wrappers_any, list):
            raise FlmError(f"bad pythonAdapters[{name}].wrappers: must be a list")
        for wi, entry in enumerate(wrappers_any):
            if isinstance(entry, str):
                m = entry.strip()
                if not m:
                    raise FlmError(f"bad pythonAdapters[{name}].wrappers[{wi}]: empty name")
                wrapper_specs.append({"name": m, "codec": "bytes"})
                continue
            if isinstance(entry, dict):
                wrapper_specs.append(entry)
                continue
            raise FlmError(f"bad pythonAdapters[{name}].wrappers[{wi}]: invalid entry")
        for spec in wrapper_specs:
            codec = str(spec.get("codec", "bytes"))
            if codec == "json":
                uses_json = True
                uses_list = True
        if uses_json:
            lines.append("use json\n")
        if uses_list:
            lines.append("use collections.list\n")
        lines.append("\n")
        lines.append(f"sector {name}:\n")
        seen_wrappers: set[str] = set()
        for wi, spec in enumerate(wrapper_specs):
            m = str(spec.get("name", "")).strip()
            if not m:
                raise FlmError(f"bad pythonAdapters[{name}].wrappers[{wi}]: missing name")
            _ensure_ident(m, what=f"pythonAdapters[{name}].wrappers[{m}].name")
            if m in seen_wrappers:
                raise FlmError(f"bad pythonAdapters[{name}].wrappers: duplicate name: {m}")
            seen_wrappers.add(m)
            if allow and m not in allow:
                raise FlmError(f"bad pythonAdapters[{name}].wrappers[{m}]: not in allow list")
            codec = str(spec.get("codec", "bytes"))
            args = _normalize_args(spec.get("args"), adapter=name, method=m, codec=codec)
            ret = str(spec.get("ret", "Bytes" if codec == "bytes" else "Str" if codec == "text" else "JsonValue"))

            if codec == "bytes":
                if len(args) != 1 or args[0][1] != "Bytes" or ret != "Bytes":
                    raise FlmError(
                        f"bad pythonAdapters[{name}].wrappers[{m}]: bytes codec requires (Bytes) -> Bytes"
                    )
                arg_name = args[0][0]
                lines.append(
                    f"  fn {m}({arg_name}: Bytes) -> Result[Bytes, Str] = rpc py.invoke(\"{name}\", \"{m}\", {arg_name})\n"
                )
                continue

            if codec == "text":
                if len(args) != 1 or args[0][1] != "Str" or ret != "Str":
                    raise FlmError(f"bad pythonAdapters[{name}].wrappers[{m}]: text codec requires (Str) -> Str")
                arg_name = args[0][0]
                lines.append(
                    f"  fn {m}({arg_name}: Str) -> Result[Str, Str] = rpc py.invokeText(\"{name}\", \"{m}\", {arg_name})\n"
                )
                continue

            if codec == "json":
                arg_list: list[str] = []
                for arg_name, typ in args:
                    arg_list.append(f"{arg_name}: {typ}")
                args_sig = ", ".join(arg_list)
                exprs = [_json_expr_for_type(n, t, adapter=name, method=m) for n, t in args]
                list_expr = "Nil"
                for expr in reversed(exprs):
                    list_expr = f"Cons({expr}, {list_expr})"
                payload_expr = f"JArr({list_expr})"
                lines.append(f"  fn {m}({args_sig}) -> Result[{ret}, Str] = do:\n")
                lines.append(f"    let payload = {payload_expr}\n")
                if ret == "JsonValue":
                    lines.append(f"    return rpc py.invokeJson(\"{name}\", \"{m}\", payload)\n")
                else:
                    lines.append(f"    let res = rpc py.invokeJson(\"{name}\", \"{m}\", payload)\n")
                    lines.append("    return match res:\n")
                    lines.append("      Ok(j) -> match j:\n")
                    lines.extend(_json_decode_match(ret, adapter=name, method=m))
                    lines.append("      Err(e) -> Err(e)\n")
                continue

            raise FlmError(f"bad pythonAdapters[{name}].wrappers[{m}]: unknown codec {codec}")
        mod_path.write_text("".join(lines), encoding="utf-8")
        names.append(name)

    # Generate barrel module: vendor/pyadapters/__init__.flv
    init_path = out_dir / "__init__.flv"
    init_lines = ["".join([f"use pyadapters.{n}\n" for n in sorted(names)])]
    init_path.write_text("".join(init_lines), encoding="utf-8")
