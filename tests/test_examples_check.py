from pathlib import Path

import pytest

from flavent.lexer import lex
from flavent.parser import parse_program
from flavent.resolve import resolve_program
from flavent.lower import lower_resolved
from flavent.typecheck import check_program


@pytest.mark.parametrize("path", sorted(Path("examples").glob("*.flv")))
def test_examples_pass_check(path: Path) -> None:
    src = path.read_text(encoding="utf-8")
    res = resolve_program(parse_program(lex(str(path), src)))
    hir = lower_resolved(res)
    check_program(hir, res)
