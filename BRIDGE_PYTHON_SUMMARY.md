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
- `_pySha256Digest(b: Bytes) -> Bytes` (stdlib now prefers native sha256)
- `_pySha256Hex(b: Bytes) -> Str` (stdlib now prefers native sha256)
- `_pySha512Digest(b: Bytes) -> Bytes`
- `_pySha512Hex(b: Bytes) -> Str`

### Base64 primitives (historical; stdlib now prefers native base64)
- `_pyBase64Encode(b: Bytes) -> Str`
- `_pyBase64Decode(s: Str) -> Bytes`
- `_pyBase64UrlEncode(b: Bytes) -> Str`
- `_pyBase64UrlDecode(s: Str) -> Bytes`

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

## 3) Stdlib modules built on the bridge

### Pure stdlib wrappers
- `stdlib/bytelib`: pure wrapper over `_pyBytes*` + list-based ByteArray helpers
- `stdlib/u32`: pure wrapper over `_pyU32*`

### Effectful stdlib wrappers
- `stdlib/consoleIO`: wraps console functions
- `stdlib/time`: wraps time functions
- `stdlib/fslib`: wraps filesystem functions
- `stdlib/tempfile`: wraps `fslib.tempFile/tempDir`

### Self-hosted stdlib (mostly native)
- `stdlib/base64`: now implemented in pure Flavent (`base64/core.flv`) using `bytelib` + string primitives
- `stdlib/hashlib`: now prefers native `sha256` (`hashlib/sha256.flv`) using `bytelib` + `u32`; other hashes still use bridge

## 4) Host work remaining

If/when an actual evaluator/runtime is added, the host must provide implementations for the above bridge declarations.
