# FLM (Flavent Manifest) Specification

This document defines the Flavent package/project manifest format (`flm.json`), the lockfile format (`flm.lock.json`), and the loader/runtime conventions.

The design goals are:
- **Reproducible builds**: Lockfile pins exact sources.
- **Extensibility**: Unknown fields are preserved; `extensions` is namespaced.
- **Security boundaries**: Python integration must use a strict adapter protocol (v2 = subprocess isolation).

---

## 1. Files

- **`flm.json`**: Human-authored manifest.
- **`flm.lock.json`**: Machine-generated lockfile.
- **`vendor/`**: Installed source dependencies.
- **`.flavent/`**: Cache directory for downloads/build artifacts (git cache, etc.).

---

## 2. `flm.json` (Manifest)

### 2.1 Top-level schema (v1)

```json
{
  "flmVersion": 1,
  "package": {
    "name": "myproj",
    "version": "0.1.0",
    "entry": "src/main.flv"
  },
  "toolchain": {
    "flavent": ">=0.1.0"
  },
  "dependencies": {
    "mylib": { "path": "../mylib" },
    "netlib": { "git": "ssh://git@host/org/netlib.git", "rev": "<commit-or-tag>" }
  },
  "devDependencies": {},
  "pythonAdapters": [],
  "extensions": {
    "org.example.feature": {
      "any": "json"
    }
  }
}
```

### 2.2 Field semantics

- **`flmVersion`**: Manifest format version. Must be an integer.
- **`package.name`**: Project name.
- **`package.version`**: Semver-like string.
- **`package.entry`**: Entry `.flv` path, relative to project root.
- **`toolchain.flavent`**: Required Flavent version range (string).

### 2.3 Dependencies

`dependencies` and `devDependencies` are objects mapping dependency names to a **dependency spec**:

- **Path dependency**:
  - `{ "path": "../somewhere" }`
- **Git dependency**:
  - `{ "git": "ssh://...", "rev": "<commit/tag>" }`

Notes:
- v1 intentionally does **not** define a central registry.
- v2+ may add `{ "registry": "...", "version": "..." }`.

### 2.4 Extensions

`extensions` is reserved for third-party metadata.
- Keys should be **reverse-DNS** (e.g., `org.orangepie.xxx`).
- The core tool must preserve unknown extension objects when rewriting the manifest.

---

## 3. `flm.lock.json` (Lockfile)

### 3.1 Schema (v1)

```json
{
  "flmLockVersion": 1,
  "resolved": {
    "mylib": { "path": "../mylib" },
    "netlib": { "git": "ssh://git@host/org/netlib.git", "rev": "<pinned-commit>" }
  }
}
```

- `resolved` should contain only **fully resolved** specs.
- For git dependencies, the `rev` should be a pinned commit hash.

Implementation note (current):
- `flavent pkg install` clones git deps into `.flavent/git/<name>` and writes `vendor/<name>` as a symlink to that cached repo.
- Lockfile pins `rev` to the checked-out commit hash (`git rev-parse HEAD`).

---

## 4. Module Loading Rules (Resolver Integration)

When resolving `use a.b`, the resolver searches:
1. `module_roots` (project `src/`, project `vendor/`, project root)
2. Flavent `stdlib/`

Each root is searched in the following way:
- File module: `<root>/a/b.flv`
- Package module: `<root>/a/b/__init__.flv`

This makes it possible for installed dependencies in `vendor/<dep>/...` to be imported as `use <dep>...`.

---

## 5. CLI Commands (v1)

### 5.1 `flavent pkg init [path]`
- Creates `flm.json` at the project root.
- Creates skeleton directories:
  - `src/`, `tests_flv/`, `vendor/`

### 5.2 `flavent pkg add <name> (--path <p> | --git <url> [--rev <rev>]) [--dev]`
- Adds a dependency to `flm.json`.

### 5.3 `flavent pkg list`
- Prints dependencies from `flm.json`.

### 5.4 `flavent pkg install`
- Populates `vendor/<name>`:
  - `path`: creates a symlink to the source.
  - `git`: clones repo into `.flavent/git/<name>`, checks out requested `rev` (if any), then symlinks `vendor/<name>` to the cache.
- Writes `flm.lock.json`.

Also generates python adapter wrappers (if `pythonAdapters` is present):
- `vendor/pyadapters/<adapter>.flv`
- `vendor/pyadapters/__init__.flv`

### 5.5 `flavent pkg export <out>`
- Writes a combined export JSON for debugging/inspection.

---

## 6. Python Adapters (Security v2: Subprocess Isolation)

**Goal:** Allow Flavent code to call approved Python functionality without exposing direct Python imports or arbitrary execution.

### 6.1 Manifest declaration

```json
{
  "pythonAdapters": [
    {
      "name": "numpy_like",
      "source": { "path": "vendor/flavent-py-numpy" },
      "capabilities": ["pure_math"],
      "allow": ["dot", "mean"],
      "wrappers": [
        "dot",
        { "name": "mean", "codec": "json", "args": ["Float"], "ret": "Float" }
      ]
    }
  ]
}
```

Notes:
- `allow` controls runtime permission (must be a subset of adapter `EXPORTS`).
- `wrappers` is optional and only affects generated `pyadapters` signatures.
- If `wrappers` is omitted, wrappers default to `(Bytes) -> Bytes`.
- Wrapper entries can be strings (same as bytes codec) or objects with `name`, `codec`, `args`, `ret`.

### 6.2 Adapter package layout

An adapter package must contain:

```
<adapter-root>/
  flavent_adapter.py
  pyproject.toml (optional)
  ...
```

### 6.3 Required adapter interface

The adapter must define:
- `PLUGIN_ID: str`
- `API_VERSION: int` (v1)
- `CAPABILITIES: list[str]`
- `EXPORTS: dict[str, {"args": [...], "ret": "..."}]`
- `dispatch(fn: str, payload: bytes) -> bytes`

The payload and response are opaque bytes. In v1, the recommended encoding is JSON bytes.

### 6.4 Subprocess protocol

The runtime starts a Python subprocess for each adapter (or a shared host process) and communicates over stdin/stdout using newline-delimited JSON messages.

Request:
```json
{"id": 1, "method": "mean", "payload_b64": "..."}
```

Response:
```json
{"id": 1, "ok": true, "payload_b64": "..."}
```

Error:
```json
{"id": 1, "ok": false, "error": "message"}
```

Metadata query:
- `method = "__meta__"` returns JSON bytes describing the adapter:
  - `plugin_id`, `api_version`, `capabilities`, `exports`

### 6.5 Enforcement

- Flavent can only call functions in `allow` for that adapter.
- Adapter declared `CAPABILITIES` must be explicitly granted in `flm.json`.
- Runtime validates that manifest `allow` is a subset of adapter `EXPORTS`.
- The adapter runs in a separate process to reduce blast radius.

### 6.6 Wrapper codecs (for generated `pyadapters`)

Supported `codec` values:
- `bytes` (default): `(Bytes) -> Bytes`
- `text`: `(Str) -> Str` (ASCII encoding)
- `json`: arguments are packed into a JSON array, return is a JSON value

`json` codec supports these types in `args`/`ret`:
- `Int`, `Float`, `Bool`, `Str`, `JsonValue`, `Unit`

Example:
```json
{
  "name": "demo",
  "allow": ["sum", "echoText"],
  "wrappers": [
    { "name": "sum", "codec": "json", "args": ["Int", "Int"], "ret": "Int" },
    { "name": "echoText", "codec": "text", "args": ["Str"], "ret": "Str" }
  ]
}
```

---

## 7. Future Work

- Registry support + semantic version resolution.
- A structured cache under `.flavent/`.
- Lockfile transitive dependency graph.
- Stronger OS-level sandboxing (where available).
