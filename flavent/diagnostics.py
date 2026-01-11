from __future__ import annotations

from dataclasses import dataclass

from .span import Span


class FlaventError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class Diagnostic:
    message: str
    span: Span


class LexError(FlaventError):
    def __init__(self, message: str, span: Span):
        super().__init__(message)
        self.message = message
        self.span = span


class ParseError(FlaventError):
    def __init__(self, message: str, span: Span):
        super().__init__(message)
        self.message = message
        self.span = span


class ResolveError(FlaventError):
    def __init__(self, message: str, span: Span):
        super().__init__(message)
        self.message = message
        self.span = span


class LowerError(FlaventError):
    def __init__(self, message: str, span: Span):
        super().__init__(message)
        self.message = message
        self.span = span


class TypeError(FlaventError):
    def __init__(self, message: str, span: Span):
        super().__init__(message)
        self.message = message
        self.span = span


class EffectError(FlaventError):
    def __init__(self, message: str, span: Span):
        super().__init__(message)
        self.message = message
        self.span = span


def format_diagnostic(source: str, diag: Diagnostic) -> str:
    span = diag.span
    lines = source.splitlines()
    line_idx = max(0, min(len(lines) - 1, span.line - 1))
    line_text = lines[line_idx] if lines else ""
    caret_col = max(1, span.col)
    # Underline a span range on the current line.
    # Span.start/end are absolute offsets; we approximate width using (end-start) and clamp.
    width = max(1, span.end - span.start)
    max_width = max(1, len(line_text) - (caret_col - 1))
    width = min(width, max_width)
    caret_line = " " * (caret_col - 1) + ("^" * width)
    return (
        f"{span.file}:{span.line}:{span.col}: {diag.message}\n"
        f"{line_text}\n"
        f"{caret_line}\n"
    )
