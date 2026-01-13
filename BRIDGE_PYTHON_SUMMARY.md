# Flavent Python Bridge Boundary Summary

This file summarizes the current `_bridge_python` boundary in the Flavent stdlib.

## 1) Pure bridge primitives (top-level fns in `stdlib/_bridge_python.flv`)

These are declared as pure Flavent functions but are intended to be implemented by the host (Python) runtime.

### String primitives
- `strLen(s: Str) -> Int`
- `strCodeAt(s: Str, i: Int) -> Int`
- `strSlice(s: Str, start: Int, end: Int) -> Str`
- `strFromCode(code: Int) -> Str`

### Bytes primitives (minimal bytes boundary)
- `_pyBytesLen(b: Bytes) -> Int`
- `_pyBytesGet(b: Bytes, i: Int) -> Int`  (0..255)
- `_pyBytesSlice(b: Bytes, start: Int, end: Int) -> Bytes`
- `_pyBytesConcat(a: Bytes, b: Bytes) -> Bytes`
- `_pyBytesFromByte(x: Int) -> Bytes`

### U32 / bitops primitives (32-bit wrap semantics)
- `_pyU32Wrap(x: Int) -> Int`
- `_pyU32And(a: Int, b: Int) -> Int`
- `_pyU32Or(a: Int, b: Int) -> Int`
- `_pyU32Xor(a: Int, b: Int) -> Int`
- `_pyU32Not(a: Int) -> Int`
- `_pyU32Shl(a: Int, n: Int) -> Int`
- `_pyU32Shr(a: Int, n: Int) -> Int` (logical)

### Hash primitives (bridge-backed, where not yet self-hosted)
- `_pyMd5Digest(b: Bytes) -> Bytes`
- `_pyMd5Hex(b: Bytes) -> Str`
- `_pySha1Digest(b: Bytes) -> Bytes`
- `_pySha1Hex(b: Bytes) -> Str`
- `_pySha512Digest(b: Bytes) -> Bytes`
- `_pySha512Hex(b: Bytes) -> Str`

## 2) Effectful bridge API (`sector _bridge_python` in `stdlib/_bridge_python.flv`)

These are effectful host interop calls and should be accessed via `rpc/call`.

### Time
- `nowMillis() -> Int`
- `nowNanos() -> Int`
- `monoMillis() -> Int`
- `monoNanos() -> Int`
- `sleep(ms: Int) -> Unit`

### Console IO
- `consolePrint(s: Str) -> Unit`
- `consolePrintln(s: Str) -> Unit`
- `consolePrintErr(s: Str) -> Unit`
- `consolePrintlnErr(s: Str) -> Unit`
- `consoleReadLine() -> Str`
- `consoleFlush() -> Unit`

### File system (used by `stdlib/fslib`)
- `fsReadFileBytes(path: Str) -> Bytes`
- `fsReadFileStr(path: Str) -> Str`
- `fsWriteFileBytes(path: Str, data: Bytes) -> Unit`
- `fsWriteFileStr(path: Str, data: Str) -> Unit`
- `fsListDir(path: Str) -> List[Str]`
- `fsExists(path: Str) -> Bool`
- `fsMkdirs(path: Str) -> Unit`
- `fsRemove(path: Str) -> Unit`
- `fsTempFile(prefix: Str, suffix: Str) -> Str`
- `fsTempDir(prefix: Str) -> Str`

### UUID
- `uuid4Bytes() -> Bytes`  (used by `stdlib/uuid`)

### Sockets (used by `stdlib/socket`)
- `sockTcpConnect(host: Str, port: Int) -> Result[Int, Str]`
- `sockTcpListen(host: Str, port: Int, backlog: Int) -> Result[Int, Str]`
- `sockTcpAccept(s: Int) -> Result[BridgeSockAccept, Str]`
- `sockSend(s: Int, data: Bytes) -> Result[Int, Str]`
- `sockRecv(s: Int, n: Int) -> Result[Bytes, Str]`
- `sockClose(s: Int) -> Result[Unit, Str]`
- `sockShutdown(s: Int) -> Result[Unit, Str]`
- `sockSetTimeoutMillis(s: Int, ms: Int) -> Result[Unit, Str]`

## 3) Stdlib modules built on the bridge

### Pure stdlib wrappers
- `stdlib/bytelib`: pure wrapper over `_pyBytes*` + list-based ByteArray helpers
- `stdlib/u32`: pure wrapper over `_pyU32*`

### Effectful stdlib wrappers
- `stdlib/consoleIO`: wraps console functions
- `stdlib/time`: wraps time functions
- `stdlib/fslib`: wraps filesystem functions
- `stdlib/tempfile`: wraps `fslib.tempFile/tempDir`
- `stdlib/socket`: wraps host TCP sockets

### Self-hosted stdlib (mostly native)
- `stdlib/base64`: now implemented in pure Flavent (`base64/core.flv`) using `bytelib` + string primitives
- `stdlib/hashlib`: now prefers native `sha256` (`hashlib/sha256.flv`) using `bytelib` + `u32`; other hashes still use bridge

## 4) Host work remaining

If/when an actual evaluator/runtime is added, the host must provide implementations for the above bridge declarations.

## 5) Enforcement and safety

### Compile-time enforcement
- User programs are **not allowed** to `use _bridge_python`.
- User programs are **not allowed** to reference or call any `_bridge_python` symbol directly (pure shims like `_pyU32Wrap` included).
- The only supported way to access these capabilities is through **stdlib wrapper modules** (e.g. `time`, `consoleIO`, `fslib`, `file`, `bytelib`, `u32`).

### Resource safety / cleanup expectations
- Any bridge-backed capability that can fail must surface errors as `Result[..., Str]` in stdlib wrappers.
- Any future bridge API that allocates resources (files/handles/sockets/etc.) must provide an explicit close/release API, and stdlib should expose a structured “acquire/use/release” pattern so callers cannot leak resources.
