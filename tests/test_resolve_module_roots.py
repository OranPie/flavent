from __future__ import annotations

from pathlib import Path

from flavent.lexer import lex
from flavent.parser import parse_program
from flavent.resolve import resolve_program_with_stdlib


def test_resolve_with_module_roots_loads_vendor_module(tmp_path: Path):
    root = tmp_path / "proj"
    (root / "src").mkdir(parents=True)
    (root / "vendor").mkdir(parents=True)

    # Create a vendor dependency module: vendor/depmod/__init__.flv
    dep = root / "vendor" / "depmod"
    dep.mkdir(parents=True)
    (dep / "__init__.flv").write_text("fn answer() -> Int = 42\n", encoding="utf-8")

    src = (
        "use depmod\n\n"
        "type Event.X = {}\n\n"
        "sector main:\n"
        "  on Event.X -> do:\n"
        "    let _a = answer()\n"
        "    stop()\n\n"
        "run()\n"
    )

    p = root / "src" / "main.flv"
    prog = parse_program(lex(str(p), src))
    res = resolve_program_with_stdlib(prog, use_stdlib=True, module_roots=[root / "src", root / "vendor", root])

    # Ensure answer() symbol exists in resolved symbols.
    assert any(s.name == "answer" for s in res.symbols)
