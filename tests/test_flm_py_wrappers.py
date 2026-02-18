from __future__ import annotations

import json
from pathlib import Path

import pytest

from flavent.flm import FlmError, init_project, install
from flavent.lexer import lex
from flavent.lower import lower_resolved
from flavent.parser import parse_program
from flavent.resolve import resolve_program_with_stdlib
from flavent.typecheck import check_program


def test_flm_install_generates_pyadapter_wrappers(tmp_path: Path):
    root = tmp_path / "proj"
    init_project(root)

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
                        "allow": ["echo", "echoText", "sum"],
                        "wrappers": [
                            "echo",
                            {"name": "echoText", "codec": "text", "args": ["Str"], "ret": "Str"},
                            {"name": "sum", "codec": "json", "args": ["Int", "Int"], "ret": "Int"},
                        ],
                    }
                ],
                "extensions": {},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    install(root)

    assert (root / "vendor" / "pyadapters" / "demo.flv").exists()
    assert (root / "vendor" / "pyadapters" / "__init__.flv").exists()

    src = (
        "use flvtest\n"
        "use pyadapters.demo\n"
        "use bytelib\n\n"
        "type Event.Test = {}\n\n"
        "sector main:\n"
        "  on Event.Test -> do:\n"
        "    let r = rpc demo.echo(b\"hi\")\n"
        "    match r:\n"
        "      Ok(b) -> do:\n"
        "        assertTrue(bytesLen(b) >= 0)?\n"
        "      Err(e) -> do:\n"
        "        assertTrue(true)?\n"
        "    let r2 = rpc demo.sum(1, 2)\n"
        "    match r2:\n"
        "      Ok(v) -> assertEq(v, 3)?\n"
        "      Err(e) -> assertTrue(true)?\n"
        "    stop()\n\n"
        "run()\n"
    )

    p = root / "src" / "main.flv"
    prog = parse_program(lex(str(p), src))
    res = resolve_program_with_stdlib(prog, use_stdlib=True, module_roots=[root / "src", root / "vendor", root])
    hir = lower_resolved(res)
    check_program(hir, res)


@pytest.mark.parametrize(
    ("adapters", "msg_re"),
    [
        ([123], r"pythonAdapters\[0\].*object"),
        ([{"source": {"path": "vendor/py_demo"}}], r"pythonAdapters\[0\].*missing name"),
        (
            [{"name": "demo", "allow": ["echo"]}, {"name": "demo", "allow": ["echo"]}],
            r"duplicate adapter name",
        ),
        ([{"name": "demo", "allow": [123], "wrappers": ["echo"]}], r"pythonAdapters\[demo\]\.allow"),
        ([{"name": "demo", "allow": ["echo"], "wrappers": [123]}], r"wrappers\[0\].*invalid entry"),
        ([{"name": "demo", "allow": ["echo"], "wrappers": ["echo", "echo"]}], r"duplicate name"),
    ],
)
def test_flm_install_rejects_invalid_python_adapter_wrapper_specs(
    tmp_path: Path,
    adapters: list[object],
    msg_re: str,
):
    root = tmp_path / "proj"
    init_project(root)
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
        install(root)
