# Stdlib API Ownership (Phase 1)

Date: 2026-02-19

This table defines source-of-truth modules for overlapping stdlib capabilities.
Use this as migration guidance and as the policy backing `docs/stdlib_duplicate_allowlist.json`.

| Capability | Canonical module | Compatibility wrappers | Notes |
|---|---|---|---|
| App-facing file operations (`exists`, `listDir`, `remove`, `tempFile`, `tempDir`) | `file` | `fslib` | Prefer `file.*` in user code for stable app-level IO surface. |
| Bridge-near filesystem primitives (`readFile*`, `writeFile*`, `mkdirs`, bridge RPC mapping) | `fslib` | None | `fslib` remains the low-level filesystem boundary over `_bridge_python`. |
| Time API (`now*`, `mono*`, `sleep*`) | `time` | `_bridge_python` internal primitives | Use `time.*` only. `_bridge_python` is internal and blocked for direct user use. |
| Runtime bridge primitives | `_bridge_python` (internal) | None | Internal module; excluded from public duplicate checks by default. |

## Migration Notes

- New code should import `file` for common filesystem operations.
- Keep `fslib` for low-level or bridge-oriented behaviors.
- Keep `time` as the only public time namespace; do not import `_bridge_python`.
