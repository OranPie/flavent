from __future__ import annotations

from pathlib import Path

import pytest

from .runner import discover_cases, run_file


def pytest_collect_file(parent, file_path: Path):
    # Collect Flavent tests under tests_flv/**/*.flv
    if file_path.suffix != ".flv":
        return None
    parts = file_path.parts
    if "tests_flv" not in parts:
        return None
    return FlvFile.from_parent(parent, path=file_path)


class FlvFile(pytest.File):
    def collect(self):
        src = self.path.read_text(encoding="utf-8")
        cases = discover_cases(src)
        if not cases:
            yield FlvItem.from_parent(self, name=self.path.name, case=None)
            return
        for c in cases:
            yield FlvItem.from_parent(self, name=f"{self.path.name}::{c}", case=c)


class FlvItem(pytest.Item):
    def __init__(self, *, case: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.case = case

    def runtest(self):
        res = run_file(self.path, case=self.case)
        if not res.ok:
            raise AssertionError(res.error or "flvtest failed")

    def repr_failure(self, excinfo):
        return str(excinfo.value)

    def reportinfo(self):
        if self.case is None:
            return self.path, 0, f"flvtest: {self.path}"
        return self.path, 0, f"flvtest: {self.path}::{self.case}"
