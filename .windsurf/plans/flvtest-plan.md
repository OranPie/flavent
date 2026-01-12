# flvtest Plan (Native Flavent Test Framework)

This plan introduces `flvtest`, a standalone multi-file package that runs Flavent tests end-to-end using the compiler pipeline plus a deterministic HIR interpreter runtime.

## Goals
- Provide a **Flavent-native testing API** (assertions, test cases) that feels like writing normal `.flv` code.
- Provide a **Python runner package** (`flvtest`) that:
  - compiles tests via `lex/parse/resolve/lower/typecheck`
  - executes them with the deterministic runtime harness
  - outputs a concise pass/fail report
- Keep host/bridge effects controllable via test doubles (fake clock/fs/console/rng).

Confirmed decisions:
- Assertions live under `stdlib/flvtest`.
- Default discovery path is `tests_flv/**/*.flv`.
- Provide **pytest integration** in addition to the standalone `flvtest` CLI.

## Scope (MVP)
### Test declaration format
- Tests are ordinary `.flv` programs (or `tests_flv/` directory) that end with `run()`.
- A test file defines one or more test cases in a dedicated sector, e.g. `sector Test:`.

### Native assertion API (Flavent stdlib module)
Add `stdlib/flvtest/__init__.flv` with:
- `fn assertTrue(cond: Bool) -> Unit`
- `fn assertEq[T](a: T, b: T) -> Unit` (requires `==`)
- `fn fail(msg: Str) -> Unit`

MVP implementation detail:
- Assertions return `Result[Unit, Str]` so tests can use the existing `?` operator to abort the handler.

Design choice (recommended): assertions are implemented as `emit`/`abort` semantics once runtime exists:
- On failure: emit `Event.TestFail(msg)` and abort current handler.
- On success: continue.

## Runner package (Python, standalone)
Create a new top-level Python package:
- `flvtest/__init__.py`
- `flvtest/cli.py`  (entrypoint `python -m flvtest` or console script)
- `flvtest/runner.py` (discover files, compile, execute, collect results)
- `flvtest/report.py` (format output)
- `flvtest/bridge_fakes.py` (fake `_bridge_python` for tests)

Pytest integration (new):
- `flvtest/pytest_plugin.py`
  - Adds a `pytest` test collector for `tests_flv/**/*.flv`.
  - Each `.flv` file becomes one pytest test item (or one per declared test case, if/when we add discovery inside a file).
  - Failure surfaces as a pytest failure with a readable trace.

CLI MVP:
- `flvtest run tests_flv/` discovers `*.flv` tests and runs them.
- Exit code `0` if all pass; nonzero otherwise.

## Runtime integration points
- The runner depends on the runtime harness from `runtime-tests-plan.md`:
  - deterministic scheduler
  - captured console output
  - injectable time/fs/rng

## Bridge policy for tests
- Default: disallow real host effects.
- Provide controlled capabilities:
  - `uuid4Bytes` backed by deterministic RNG
  - `fs*` backed by a sandbox temp directory
  - `console*` captured in-memory

## Acceptance criteria
- A simple test file with `assertEq(1 + 1, 2)` passes.
- A failing assertion yields a readable failure report with file/span if possible.
- CI can run `flvtest` deterministically.
