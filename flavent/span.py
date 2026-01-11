from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Span:
    file: str
    start: int
    end: int
    line: int
    col: int

    def merge(self, other: "Span") -> "Span":
        if self.file != other.file:
            return self
        start = min(self.start, other.start)
        end = max(self.end, other.end)
        line = self.line if self.start <= other.start else other.line
        col = self.col if self.start <= other.start else other.col
        return Span(file=self.file, start=start, end=end, line=line, col=col)
