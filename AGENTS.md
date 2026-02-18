# Repository Guidelines

## Project Structure & Module Organization
- `flavent/` contains the compiler pipeline and CLI (`lexer`, `parser`, `resolve`, `lower`, `typecheck`, `cli`).
- `flvtest/` provides the Flavent test runner and pytest plugin integration.
- `tests/` holds Python unit/integration tests; `tests_flv/` holds `.flv` language behavior tests.
- `stdlib/` contains standard library modules organized by package name (`stdlib/json`, `stdlib/socket`, etc.).
- `examples/` provides runnable sample programs; `docs/en` and `docs/zh` contain user docs.
- `scripts/` stores maintenance utilities (for example, `scripts/docgen_stdlib.py`).

## Build, Test, and Development Commands
- `python3 -m pip install -e .` — install in editable mode for local development.
- `python3 -m flavent check examples/minimal.flv` — run parse/resolve/lower/check pipeline on a file.
- `python3 -m flavent check examples/minimal.flv --strict --report-junit reports/check.xml` — fail on warnings and emit JUnit XML for CI.
- `python3 -m flavent lex <file.flv>` / `parse` / `resolve` / `hir` — inspect each compilation stage.
- `python3 -m pytest` — run the full Python + `.flv` test suite.
- `python3 -m pytest tests -k lexer` — run a focused subset while iterating.
- `python3 -m pytest -m integration` / `-m e2e` — run tagged test tiers when adding broader changes.
- `python3 -m pytest -q --junit-xml=reports/junit.xml` — produce CI-friendly JUnit artifacts locally.
- `python3 scripts/docgen_stdlib.py` — regenerate stdlib docs when APIs change.

## Coding Style & Naming Conventions
- Target Python 3.10+; use 4-space indentation, type hints, and small focused functions.
- Follow existing naming patterns: modules/functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.
- Keep imports explicit and local abstractions clear; mirror nearby style when editing.
- Flavent source (`.flv`) must use spaces (tabs are invalid) and clear, descriptive identifiers.

## Testing Guidelines
- Name Python tests as `tests/test_*.py`; group by subsystem (`test_lexer_*`, `test_stdlib_*`, etc.).
- Name Flavent tests as `tests_flv/test_*.flv`.
- Add or update tests with every behavior change in compiler, package manager, bridge, or stdlib code.
- Before opening a PR, run `python3 -m pytest` and include any targeted commands used.

## Commit & Pull Request Guidelines
- Follow the repository’s commit style seen in history: `feat(scope): ...`, `fix(scope): ...`, `docs: ...`.
- Use imperative, concise commit subjects and keep each commit scoped to one logical change.
- PRs should include: problem statement, key implementation notes, and test evidence (commands run).
- Link related issues/spec docs (`DOCS.md`, `FLM_SPEC.md`) and include CLI output snippets for user-visible behavior changes.
