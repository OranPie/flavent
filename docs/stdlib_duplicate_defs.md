# Stdlib Duplicate Definitions Report

Scope: public-only symbols
Module scope: public modules only (excludes `_...` and `testns.*`)
Allowlist: `docs/stdlib_duplicate_allowlist.json`
Duplicate symbols across modules: `5`
Approved duplicates: `5`
Unapproved duplicates: `0`
Stale allowlist entries: `0`

## Approved Duplicates

### `fn exists` (2 modules)
- canonical: `file`
- note: Keep `file.exists` as the app-facing API; `fslib.exists` remains as low-level bridge surface.
- `file` (`file/__init__.flv:45`)
- `fslib` (`fslib/__init__.flv:12`)

### `fn listDir` (2 modules)
- canonical: `file`
- note: Keep `file.listDir` as the app-facing API; `fslib.listDir` remains as low-level bridge surface.
- `file` (`file/__init__.flv:47`)
- `fslib` (`fslib/__init__.flv:11`)

### `fn remove` (2 modules)
- canonical: `file`
- note: Keep `file.remove` as the app-facing API; `fslib.remove` remains as low-level bridge surface.
- `file` (`file/__init__.flv:42`)
- `fslib` (`fslib/__init__.flv:14`)

### `fn tempDir` (2 modules)
- canonical: `file`
- note: Keep `file.tempDir` as the app-facing API; `fslib.tempDir` remains as low-level bridge surface.
- `file` (`file/__init__.flv:51`)
- `fslib` (`fslib/__init__.flv:17`)

### `fn tempFile` (2 modules)
- canonical: `file`
- note: Keep `file.tempFile` as the app-facing API; `fslib.tempFile` remains as low-level bridge surface.
- `file` (`file/__init__.flv:49`)
- `fslib` (`fslib/__init__.flv:16`)
