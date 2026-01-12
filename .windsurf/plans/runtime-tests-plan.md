# Runtime Tests Plan (Flavent)

This plan defines a staged test strategy for Flavent execution semantics and bridge behavior, starting from the existing compile/typecheck tests and extending to a deterministic runtime harness.

## Current State (facts observed)
- Tests today are mostly **compile-time**: parse/resolve/lower/typecheck.
- `rpc/call/await/emit` are type/effect checked, but there is **no interpreter/runtime** implementation in the Python codebase yet.
- `PLAN.md` defines a future runtime (Phase 6: sectors/event loop), but code is not implemented.

## Goal
Add **runtime tests** that validate Flavent program behavior end-to-end, including:
- Sector state isolation
- Event scheduling + handler selection
- `rpc` (request/response) vs `call` (fire-and-forget)
- `await` and mailbox semantics
- Bridge interop contracts (console/time/fs/random)

## Test Layers
### Layer A — Compile-time regression (keep + expand)
- Existing tests remain the baseline.
- Add “bridge usage report” golden tests if bridge auditing is implemented.

### Layer B — Deterministic runtime harness (new)
Implement a minimal Python runtime to execute lowered HIR (or a simplified IR), then add tests against it.

Harness requirements:
- Compile pipeline integration: `lex -> parse -> resolve(+stdlib) -> lower -> typecheck -> run`.
- Deterministic scheduler:
  - deterministic handler order
  - deterministic fairness budgeting
  - deterministic `yield()` behavior
- Capturable outputs:
  - capture console output from `consoleIO` wrappers
  - capture emitted events
  - allow injecting a fake clock
- Bridge fakes/stubs:
  - `sector _bridge_python` functions are replaced by a test double.
  - filesystem operations run against a temp directory sandbox.

### Layer C — Stdlib runtime behavior tests (new)
Once the runtime harness exists:
- `base64`: encode/decode roundtrip vectors
- `hashlib/sha256`: known test vectors
- `json`: loads/dumps roundtrip; reject invalid inputs
- `uuid`: parse/toString roundtrip; uuid4 shape
- `glob`: pattern matching behavior with a sandbox directory

## Proposed Milestones
### Milestone 1 — Minimal runtime to run Event.Start
- Ability to run a program that ends with `run()`.
- Synthesize `Event.Start` and execute matching handler(s).
- Support `stop()`.

Acceptance criteria:
- A test program can print to console (captured) and stop deterministically.

### Milestone 2 — Event loop + await/emit
- Implement `emit` queues + `await` suspension.
- Implement handler selection order rules (as per refs).

Acceptance criteria:
- Deterministic tests for `emit` causing handler execution.
- Deterministic tests for `await` resuming.

### Milestone 3 — rpc/call and sector state
- Implement sector state cells (`let`, `need` later).
- Implement `rpc` request/response semantics.

Acceptance criteria:
- Cross-sector counter example behaves as expected.

### Milestone 4 — bridge contract tests
- Provide a shared “bridge conformance suite” that any host runtime must pass.

Acceptance criteria:
- One test double passes; a deliberately broken stub fails with clear error.

## Open Questions (need your confirmation)

Confirmed decisions:
- **Runtime tests target**: a **HIR interpreter** (interpreter first, tests follow).

Still to confirm (optional):
- Whether to add placeholder runtime tests as skip/xfail before the runtime exists.

Integration note:
- This runtime harness is intended to be used by the planned standalone `flvtest` runner package.
