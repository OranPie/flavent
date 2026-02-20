# Warning Catalog

This document defines stable warning/error codes for reporting and CI policy.

## `flavent check`

- `WBR001` (`warning`, stage `bridge_audit`)
  - Deprecated bridge shim usage detected by bridge audit.
  - Supports suppression (`--suppress-warning WBR001`) and escalation (`--warn-code-as-error WBR001`).
- `ECHECKWARN` (`error`, stage `check`)
  - Emitted when warning policy fails (`--strict`, `--warn-as-error`, `--warn-code-as-error`, `--max-warnings`).

## Stdlib policy scripts

- `ESTDLIBDUP001` (`error`, stage `stdlib_duplicate_defs`)
  - Unapproved duplicate stdlib definition across modules.
- `WSTDLIBDUP001` (`warning`, stage `stdlib_duplicate_defs`)
  - Stale duplicate-allowlist entry.
- `ESTDLIBBRIDGE001` (`error`, stage `stdlib_bridge_boundary`)
  - Unapproved direct `_bridge_python` import in stdlib.
- `WSTDLIBBRIDGE001` (`warning`, stage `stdlib_bridge_boundary`)
  - Stale bridge-boundary allowlist entry.

## Policy guidance

- Use `--warn-code-as-error` for staged rollout of specific warnings.
- Use `--suppress-warning` only with documented migration notes in CI/PR context.
- Prefer reducing warnings to zero; treat suppressions as temporary debt.
