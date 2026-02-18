from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from flavent.lexer import lex
from flavent.lower import lower_resolved
from flavent.parser import parse_program
from flavent.resolve import resolve_program_with_stdlib
from flavent.runtime import Bridge, run_hir_program
from flavent.typecheck import check_program


@dataclass(frozen=True)
class CmdMetric:
    name: str
    cmd: list[str]
    wall: float
    maxrss_kb: int
    summary: str


def _run_cmd(name: str, cmd: list[str]) -> CmdMetric:
    helper = (
        "import json,resource,subprocess,sys,time\n"
        "c=json.loads(sys.argv[1])\n"
        "t=time.perf_counter()\n"
        "p=subprocess.run(c,capture_output=True,text=True,check=False)\n"
        "dt=time.perf_counter()-t\n"
        "ru=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss\n"
        "lines=[ln.strip() for ln in p.stdout.splitlines() if ln.strip()]\n"
        "summary=lines[-1] if lines else f'rc={p.returncode}'\n"
        "print(json.dumps({'wall':dt,'maxrss_kb':ru,'summary':summary,'rc':p.returncode}))\n"
    )
    wrapped = subprocess.run(
        [sys.executable, "-c", helper, json.dumps(cmd)],
        capture_output=True,
        text=True,
        check=True,
    )
    out = json.loads(wrapped.stdout.strip())
    return CmdMetric(name=name, cmd=cmd, wall=float(out["wall"]), maxrss_kb=int(out["maxrss_kb"]), summary=str(out["summary"]))


def _top_rows(path: str, file_hint: str, top_n: int) -> list[tuple[float, float, int, str, int, str]]:
    import pstats

    st = pstats.Stats(path)
    rows: list[tuple[float, float, int, str, int, str]] = []
    for (filename, lineno, funcname), (_cc, nc, tt, ct, _callers) in st.stats.items():
        if file_hint in filename:
            rows.append((ct, tt, nc, filename, lineno, funcname))
    rows.sort(reverse=True)
    return rows[:top_n]


class _NoBridge(Bridge):
    def call(self, name: str, args: list[object]) -> object:
        raise RuntimeError(f"bridge call not allowed: {name}")


def _profile_pipeline() -> list[tuple[float, float, int, str, int, str]]:
    import cProfile

    src = Path("examples/minimal.flv").read_text(encoding="utf-8")
    prof = cProfile.Profile()
    prof.enable()
    for _ in range(120):
        prog = parse_program(lex("minimal.flv", src))
        res = resolve_program_with_stdlib(prog, use_stdlib=True)
        hir = lower_resolved(res)
        check_program(hir, res)
    prof.disable()
    out = "/tmp/flavent_profile_pipeline.pstats"
    prof.dump_stats(out)
    rows = []
    rows.extend(_top_rows(out, "/flavent/resolve.py", 3))
    rows.extend(_top_rows(out, "/flavent/typecheck.py", 2))
    rows.extend(_top_rows(out, "/flavent/lexer.py", 2))
    rows.sort(reverse=True)
    return rows[:6]


def _profile_runtime() -> list[tuple[float, float, int, str, int, str]]:
    import cProfile

    runtime_src = """use flvtest

type Event.Ping = Ping | PingAlt
type Event.Pong = Pong | PongAlt

sector main:
  let cycles = 0

  on Event.Ping as e -> do:
    let _p = await Event.Pong
    cycles = cycles + 1
    if cycles < 30:
      emit Ping()
    else:
      stop()

  on Event.Ping as e -> do:
    emit Pong()

run()
"""
    prog = parse_program(lex("runtime_hot.flv", runtime_src))
    res = resolve_program_with_stdlib(prog, use_stdlib=True)
    hir = lower_resolved(res)
    check_program(hir, res)

    prof = cProfile.Profile()
    prof.enable()
    for _ in range(160):
        run_hir_program(hir, res, entry_event_type="Event.Ping", bridge=_NoBridge())
    prof.disable()
    out = "/tmp/flavent_profile_runtime.pstats"
    prof.dump_stats(out)
    return _top_rows(out, "/flavent/runtime.py", 6)


def _fmt_cmd(metric: CmdMetric) -> str:
    return (
        f"- {metric.name}: `{metric.wall:.3f}s` wall, `{metric.maxrss_kb}` KB max RSS, "
        f"summary: `{metric.summary}`"
    )


def _fmt_prof_row(row: tuple[float, float, int, str, int, str]) -> str:
    ct, tt, nc, fn, ln, name = row
    short = fn.split("/root/flavent/")[-1]
    return f"- `{short}:{ln} {name}` — cum `{ct:.4f}s`, self `{tt:.4f}s`, calls `{nc}`"


def main() -> int:
    metrics = [
        _run_cmd("Full test suite", ["python3", "-m", "pytest", "-q"]),
        _run_cmd("Runtime determinism tests", ["python3", "-m", "pytest", "-q", "tests/test_runtime_determinism.py"]),
        _run_cmd("Compiler check (strict, minimal)", ["python3", "-m", "flavent", "check", "examples/minimal.flv", "--strict"]),
    ]
    pipeline_hot = _profile_pipeline()
    runtime_hot = _profile_runtime()

    print("# Performance Snapshot")
    print()
    print(f"Date: {time.strftime('%Y-%m-%d')}")
    print()
    print("## Benchmarks + Memory")
    for m in metrics:
        print(_fmt_cmd(m))
    print()
    print("## Pipeline Hotspots (cProfile)")
    for row in pipeline_hot:
        print(_fmt_prof_row(row))
    print()
    print("## Runtime Hotspots (cProfile)")
    for row in runtime_hot:
        print(_fmt_prof_row(row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
