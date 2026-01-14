from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


_RE_TYPE = re.compile(r"^type\s+([^=\s]+)\s*=\s*(.*)$")
_RE_TYPE_NOEQ = re.compile(r"^type\s+([^=\s]+)\s*$")
_RE_FN = re.compile(r"^fn\s+([^\s(]+)\s*(\(.*)$")


@dataclass(frozen=True)
class Decl:
    kind: str  # 'type' | 'fn'
    sig: str


AUTO_TYPES_START = "<!-- AUTO-GEN:START TYPES -->"
AUTO_TYPES_END = "<!-- AUTO-GEN:END TYPES -->"
AUTO_FNS_START = "<!-- AUTO-GEN:START FUNCTIONS -->"
AUTO_FNS_END = "<!-- AUTO-GEN:END FUNCTIONS -->"


def _extract_decls(src: str) -> list[Decl]:
    out: list[Decl] = []
    for raw in src.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("//"):
            continue
        if line.startswith("type "):
            m = _RE_TYPE.match(line)
            if m:
                name = m.group(1)
                rhs = m.group(2).strip()
                if name.startswith("_"):
                    continue
                out.append(Decl("type", f"type {name} = {rhs}"))
                continue
            m2 = _RE_TYPE_NOEQ.match(line)
            if m2:
                name = m2.group(1)
                if name.startswith("_"):
                    continue
                out.append(Decl("type", f"type {name}"))
                continue
        if line.startswith("fn "):
            m = _RE_FN.match(line)
            if not m:
                continue
            name = m.group(1)
            if name.startswith("_"):
                continue
            # keep full line (usually includes return type)
            out.append(Decl("fn", line))
    return out


def _module_name_for_flv(stdlib_root: Path, flv_path: Path) -> str:
    rel = flv_path.relative_to(stdlib_root)
    if rel.name == "__init__.flv":
        rel = rel.parent
    else:
        rel = rel.with_suffix("")
    parts = list(rel.parts)
    return ".".join(parts)


def _doc_path_for_module(doc_root: Path, module: str) -> Path:
    # We store module docs as <module>.md, with dots kept.
    return doc_root / f"{module}.md"


def _render_md_en(module: str, decls: list[Decl]) -> str:
    types = [d.sig for d in decls if d.kind == "type"]
    fns = [d.sig for d in decls if d.kind == "fn"]

    lines: list[str] = []
    lines.append(f"# `{module}`\n\n")
    lines.append("## Overview\n")
    lines.append("(Edit this page freely. The generator only updates the marked API blocks.)\n\n")
    lines.append("## Import\n")
    lines.append("```flavent\n")
    lines.append(f"use {module}\n")
    lines.append("```\n\n")

    lines.append("## Types\n")
    lines.append(AUTO_TYPES_START + "\n")
    lines.append("```flavent\n")
    lines.extend([t + "\n" for t in types])
    lines.append("```\n")
    lines.append(AUTO_TYPES_END + "\n\n")

    lines.append("## Functions\n")
    lines.append(AUTO_FNS_START + "\n")
    lines.append("```flavent\n")
    lines.extend([fn + "\n" for fn in fns])
    lines.append("```\n")
    lines.append(AUTO_FNS_END + "\n")

    return "".join(lines)


def _render_md_zh(module: str, decls: list[Decl]) -> str:
    types = [d.sig for d in decls if d.kind == "type"]
    fns = [d.sig for d in decls if d.kind == "fn"]

    lines: list[str] = []
    lines.append(f"# `{module}`\n\n")
    lines.append("## 概述\n")
    lines.append("（本页可自由补充示例/说明；生成器只会更新标记的 API 区块。）\n\n")
    lines.append("## 导入\n")
    lines.append("```flavent\n")
    lines.append(f"use {module}\n")
    lines.append("```\n\n")

    lines.append("## 类型\n")
    lines.append(AUTO_TYPES_START + "\n")
    lines.append("```flavent\n")
    lines.extend([t + "\n" for t in types])
    lines.append("```\n")
    lines.append(AUTO_TYPES_END + "\n\n")

    lines.append("## 函数\n")
    lines.append(AUTO_FNS_START + "\n")
    lines.append("```flavent\n")
    lines.extend([fn + "\n" for fn in fns])
    lines.append("```\n")
    lines.append(AUTO_FNS_END + "\n")

    return "".join(lines)


def _replace_block(text: str, start: str, end: str, new_block: str) -> str:
    si = text.find(start)
    ei = text.find(end)
    if si < 0 or ei < 0 or ei < si:
        return text
    ei2 = ei + len(end)
    return text[:si] + new_block + text[ei2:]


def _upsert_module_doc(path: Path, full_text: str) -> None:
    if not path.exists():
        path.write_text(full_text, encoding="utf-8")
        return

    cur = path.read_text(encoding="utf-8")
    # Old stub pages were fully auto-generated and start with this note.
    is_old_stub = "(Auto-generated API reference" in cur and AUTO_TYPES_START not in cur
    if is_old_stub:
        path.write_text(full_text, encoding="utf-8")
        return

    # If the page has markers, update only those blocks.
    if AUTO_TYPES_START in cur and AUTO_TYPES_END in cur and AUTO_FNS_START in cur and AUTO_FNS_END in cur:
        # Extract the two blocks from generated full_text.
        new_types = full_text[
            full_text.find(AUTO_TYPES_START) : full_text.find(AUTO_TYPES_END) + len(AUTO_TYPES_END)
        ]
        new_fns = full_text[
            full_text.find(AUTO_FNS_START) : full_text.find(AUTO_FNS_END) + len(AUTO_FNS_END)
        ]

        out = cur
        out = _replace_block(out, AUTO_TYPES_START, AUTO_TYPES_END, new_types)
        out = _replace_block(out, AUTO_FNS_START, AUTO_FNS_END, new_fns)
        path.write_text(out, encoding="utf-8")
        return

    # Otherwise: leave file untouched (assume it is hand-written).
    return


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    stdlib_root = repo_root / "stdlib"

    en_root = repo_root / "docs" / "en" / "stdlib"
    zh_root = repo_root / "docs" / "zh" / "stdlib"
    en_root.mkdir(parents=True, exist_ok=True)
    zh_root.mkdir(parents=True, exist_ok=True)

    flv_files: list[Path] = []
    for p in stdlib_root.rglob("*.flv"):
        # skip generated vendor modules etc.
        if "/vendor/" in str(p).replace("\\", "/"):
            continue
        flv_files.append(p)

    modules: dict[str, list[Decl]] = {}
    for p in sorted(flv_files):
        mod = _module_name_for_flv(stdlib_root, p)
        src = p.read_text(encoding="utf-8")
        decls = _extract_decls(src)
        # Merge (some modules have multiple .flv files like httplib.core/client)
        modules.setdefault(mod, [])
        modules[mod].extend(decls)

    for mod, decls in modules.items():
        # De-dup while preserving order
        seen: set[tuple[str, str]] = set()
        uniq: list[Decl] = []
        for d in decls:
            k = (d.kind, d.sig)
            if k in seen:
                continue
            seen.add(k)
            uniq.append(d)

        _upsert_module_doc(_doc_path_for_module(en_root, mod), _render_md_en(mod, uniq))
        _upsert_module_doc(_doc_path_for_module(zh_root, mod), _render_md_zh(mod, uniq))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
