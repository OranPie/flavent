# Bridge Reduction Plan (Flavent)

This plan reduces Python-bridge surface area by tightening the `_bridge_python` boundary, adding compiler-level auditing, and migrating stdlib functionality to native Flavent wherever practical.

## Current State (facts observed)
- There is a **compiler pipeline** (`lex/parse/resolve/lower/typecheck`) and CLI (`flavent/cli.py`).
- Stdlib is loaded via `resolve_program_with_stdlib()` and `_expand_std_uses()` in `flavent/resolve.py`.
- The bridge boundary is currently declared in `stdlib/_bridge_python.flv` and summarized in `BRIDGE_PYTHON_SUMMARY.md`.
- Runtime/interpreter is not present yet (Phase 6 exists as a design in `PLAN.md`, but not implemented in code).

## Design Principles (to match the language philosophy)
- **Pure primitives only for “unavoidable” operations** (string codepoints, bytes indexing/slicing/concat, u32 bitops).
- **All effectful interop is sector-scoped** (`sector _bridge_python`) and accessed only via `rpc/call`.
- **Stdlib should be native-by-default**: bridge-backed functions should be temporary shims.
- **Auditability**: bridge usage should be measurable and enforceable.

## Phase 0 — Inventory + Policy (no behavior change)
- **Inventory**
  - Treat `stdlib/_bridge_python.flv` as the authoritative boundary declaration.
  - Maintain `BRIDGE_PYTHON_SUMMARY.md` as a generated (or curated) artifact.
- **Policy definition**
  - Define the “allowed” bridge list (pure + effectful).
  - Define a “deprecation list” for bridge functions stdlib no longer uses (e.g. base64/sha256 wrappers if native).

## Phase 1 — Compiler-Level Bridge Auditing (base-system controlling changes)
Goal: make bridge usage visible and enforceable, without changing runtime semantics.

Planned changes (Python compiler):
- **Bridge usage report** (new feature)
  - During resolve/lower/typecheck, record references to:
    - `use _bridge_python`
    - `rpc _bridge_python.*` / `call _bridge_python.*`
    - top-level `_py*` functions
  - Output a report (JSON + human readable) from CLI (e.g. `flavent check --bridge-report`).
- **Bridge lint mode**
  - Optionally fail if stdlib/user code calls a non-whitelisted bridge symbol.
  - Optionally warn on deprecated bridge symbols.

Acceptance criteria:
- A program can be typechecked while producing a stable bridge usage report.
- We can assert “no new bridge calls” in CI.

## Phase 2 — Standardize the Boundary Surface
Goal: make the boundary smaller and more consistent.

Planned changes (stdlib + compiler expectations):
- **Split “pure primitives” vs “effectful”**
  - Keep pure primitives as top-level fns in `_bridge_python.flv`.
  - Keep effectful capability under `sector _bridge_python`.
- **Normalize return/value semantics**
  - Avoid ambiguous nullary constructor typing pitfalls by providing typed helpers in stdlib when necessary (e.g. `nil()` already exists; similar helpers like `jNull()` in json).
  - Consider a compiler/typechecker improvement later: treat nullary sum ctors as values uniformly.

Acceptance criteria:
- `_bridge_python` contents are minimal and consistent.
- Stdlib modules expose ergonomic wrappers so most code never calls `_bridge_python` directly.

## Phase 3 — Bridge Reduction Roadmap (stdlib migrations)
Goal: migrate major functionality off bridge.

Suggested migration order:
- **hashlib**
  - Keep `sha256` native (done). Next: `sha1`, `md5` native using `bytelib + u32`.
  - Keep `sha512` bridge until `u64` exists.
- **random / uuid4 source**
  - Keep `uuid4Bytes()` as a single effectful primitive; everything else stays native.
- **base64**
  - Ensure native is default; mark `_pyBase64*` as deprecated.
- **fs/glob/tempfile**
  - Keep filesystem effects under `fslib`; keep glob matching native.

Acceptance criteria:
- Bridge report shows decreasing usage over time.
- For each migration, add deterministic test vectors (see runtime test plan).

## Open Questions (need your confirmation)

Confirmed decisions:
- **Auditing scope**: enforce for **both stdlib and user code**.
- **Deprecated bridge policy**: keep backward-compatible shims, emit **warnings** (no hard removal initially).

Still to confirm (if you want to deviate from the default order):
- Default implementation order is **compiler-level auditing/enforcement first**, then stdlib migrations.
