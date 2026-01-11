from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional

from .span import Span


SymbolId = int
TypeId = int


class SymbolKind(Enum):
    TYPE = auto()
    SECTOR = auto()
    MIXIN = auto()
    FN = auto()
    VAR = auto()
    CONST = auto()
    NEED = auto()
    HANDLER = auto()
    CTOR = auto()


@dataclass(frozen=True, slots=True)
class Symbol:
    id: SymbolId
    kind: SymbolKind
    name: str
    span: Span
    owner: Optional[SymbolId] = None
    data: dict[str, Any] | None = None


@dataclass(slots=True)
class Scope:
    parent: Optional["Scope"]
    values: dict[str, list[SymbolId]]
    types: dict[str, list[SymbolId]]
    sectors: dict[str, list[SymbolId]]
    mixins: dict[str, list[SymbolId]]

    @staticmethod
    def root() -> "Scope":
        return Scope(parent=None, values={}, types={}, sectors={}, mixins={})

    def child(self) -> "Scope":
        return Scope(parent=self, values={}, types={}, sectors={}, mixins={})

    def define(self, ns: str, name: str, sym_id: SymbolId) -> None:
        table: dict[str, list[SymbolId]] = getattr(self, ns)
        table.setdefault(name, []).append(sym_id)

    def lookup(self, ns: str, name: str) -> list[SymbolId]:
        s: Optional[Scope] = self
        while s is not None:
            table: dict[str, list[SymbolId]] = getattr(s, ns)
            if name in table:
                return table[name]
            s = s.parent
        return []
