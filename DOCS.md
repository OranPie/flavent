# Flavent Programming Language Documentation

Flavent is a domain-specific language designed for building actor-based systems with a strong focus on data-flow, effects, and sector-based isolation.

## 1. Indentation and Blocks

Flavent uses Python-style indentation to define blocks. Blocks are introduced by a colon (`:`) and must be followed by a newline and an increased indentation level.

```flavent
sector main:
  on Event.Start -> do:
    stop()
```

- Only spaces are allowed for indentation (Tabs will cause a lexical error).
- Indentation is strictly enforced for `do:`, `sector:`, `match:`, `if:`, `for:`, etc.

## 2. Type System

### 2.1 Basic Types
- `Int`, `Float`, `Bool`, `Str`, `Bytes`, `Unit`.

### 2.2 Complex Types
- **Records (types)**: `{ field: Type, ... }`
- **Records (literals)**: `{ field = expr, ... }`
- **Sum Types**: `Variant1 | Variant2(Payload) | ...`
- **Generics**: `List[T]`, `Map[K, V]`, `Option[T]`, `Result[T, E]`.

```flavent
type User = { id: Int, name: Str }
type Status = Active | Inactive(Str)
```

Implementation note:
- `List` and `Map` are provided by stdlib (not hardcoded builtins).
- Type aliases (including generic aliases) are supported by the typechecker.
- Generic record types are supported by the typechecker (record literals and field access).

### 2.3 Unit literal
`Unit` has a value literal `()`.

```flavent
fn noop() -> Unit = ()
```

## 3. Sectors and Isolation

Sectors are the unit of state isolation. Each sector owns its local variables and functions.

```flavent
sector Counter:
  let count = 0
  fn@Counter inc() -> Int = do:
    count = count + 1
    return count
```

## 4. Effects and Interaction

Flavent tracks effects to ensure safe interaction between sectors.

- **`pure`**: No side effects.
- **`@Sector`**: Accesses or modifies state in a specific sector.
- **`event`**: Interacts with the global event system (`emit`, `await`).

### 4.1 Cross-Sector Calls
To call a function in another sector, you must use `rpc` (request-response) or `call` (fire-and-forget).

```flavent
sector UI:
  on Event.Click -> do:
    let newCount = rpc Counter.inc()
    stop()
```

## 5. Control Flow

### 5.1 Match
Pattern matching works on sum types and literals.

```flavent
match result:
  Ok(val) -> val
  Err(msg) -> 0
```

Match arms can use either:
- An expression body: `Pat -> expr`
- A block body: `Pat -> do: ...` (use `return` inside the block)

```flavent
match xs:
  Nil -> 0
  Cons(x, rest) -> do:
    if x > 0:
      return x
    else:
      return 0
```

### 5.2 Try Suffix (`?`)
The `?` operator propagates errors or empty values. It works in functions returning `Result` or `Option`, and in handlers (where it triggers an abort).

```flavent
fn demo() -> Result[Int, Str] = do:
  let x = parse()?
  return Ok(x)
```

## 6. Mixins (Advanced)

Mixins allow weaving cross-cutting concerns into sectors or types.

```flavent
mixin Logging v1 into sector S:
  around fn foo(...) -> T = do:
    // logic before
    let res = proceed(...)
    // logic after
    return res
```

### 6.1 Type mixins (into type)
Type-target mixins support:
- Record field injection (record types only)
- Method injection as `Type.method(x)` (no `x.method()` sugar)

### 6.2 Pattern alias
You can define a pattern alias and reuse it in `match`.

```flavent
pattern IsOk = Ok(_)

fn f(x: Result[Int, Str]) -> Int = match x:
  IsOk -> 1
  Err(_) -> 0
```

Pattern aliases cannot bind variables (use `_`).

### 6.3 Bool patterns
`match` supports boolean patterns `true` / `false`.

## 7. Program Entry
Every Flavent program must end with `run()` to start the execution environment.

## 8. Standard library and Python boundary

### 8.1 Module layout
`use a.b.c` loads:
- `stdlib/a/b/c.flv`, or
- `stdlib/a/b/c/__init__.flv` if the file does not exist.

### 8.2 Collections
The collections standard library is implemented in Flavent (no builtin `List`/`Map`):
- `collections.list`: `List[T] = Nil | Cons(T, List[T])`
- `collections.queue`: `Queue[T]` (two-list queue)
- `collections.heap`: `Heap` (Int-only skew heap)
- `collections.map`: `Map[K,V]` as a type alias over `List[Entry]`

### 8.3 `_bridge_python`
For capabilities that cannot be self-hosted (system time, IO, etc.), stdlib may call an internal sector `_bridge_python` via `rpc/call`.

## 9. Grammar Specification

Flavent grammar is indentation-sensitive, similar to Python.

### 9.1 Program Structure
A program consists of imports (`use`), type definitions, sector definitions, and an optional entry call (`run()`).

```antlr
program: statement* 'run' '(' ')'
statement: use_stmt | type_def | sector_def | fn_def | mixin_def
```

### 9.2 Expressions & Operators
- **Arithmetic**: `+`, `-`, `*`, `/`, `%`
- **Comparison**: `==`, `!=`, `<`, `<=`, `>`, `>=`
- **Logical**: `and`, `or`, `not`
- **Special**: `?` (try-suffix for Result/Option propagation)

### 9.3 Definitions
- **Functions**: `fn name(args) -> RetType = expr` or `fn name(args) -> RetType = do: ...`
- **Sectors**: `sector Name: [definitions]`
- **Types**: `type Name = { field: Type, ... }` or `type Name = A | B(T)`

## 10. Module Specification

### 10.1 Name Resolution
- Modules are resolved relative to `stdlib/` or current workspace.
- `use a.b` maps to `a/b.flv` or `a/b/__init__.flv`.
- Symbols within a module are public by default.

### 10.2 Namespaces
- Imported modules create a namespace. `use collections.list` allows using `list.Nil` or just `Nil` if it doesn't conflict.
- Function calls can be qualified: `math.sin(x)`.

## 11. Standard Library Introduction

Flavent's standard library is designed to be minimal but extensible, with a focus on safety and pure-Flavent implementations where possible.

### 11.1 Core Modules
- **`std.option`**: `Option[T]` (Some/None) for nullable values.
- **`std.result`**: `Result[T, E]` (Ok/Err) for error handling.
- **`collections`**: Persistent data structures (`list`, `map`, `set`, `queue`, `heap`).

### 11.2 System & Utilities
- **`bytelib`**: Low-level `Bytes` manipulation.
- **`u32`**: 32-bit unsigned integer arithmetic (wrapped).
- **`stringlib`**: Basic string utilities (find/prefix/suffix/trim/split/join).
- **`stringfmt`**: String formatting with positional and named placeholders.
- **`regex`**: Regular expression matching (pure Flavent backtracking).
- **`struct`**: Binary data packing/unpacking (compatible with Python `struct`).
- **`httplib`**: Minimal HTTP/1.1 client helpers (request build + response parse), built on `socket`.

### 11.3 Side Effects (Bridge)
- **`fslib` / `file`**: Filesystem operations (returns `Result`).
- **`consoleIO`**: Terminal input/output.
- **`time`**: System clock and sleep.
- **`random`**: Deterministic PRNG with explicit state.
- **`socket`**: TCP sockets (connect/listen/accept/send/recv) via host bridge.

---

## 12. Library Call Standard & Conventions

To ensure consistency across the Flavent ecosystem, all standard libraries and third-party modules should adhere to the following standards.

### 12.1 Naming Conventions
- **Modules**: Lowercase, singular where appropriate (e.g., `socket`, `json`, `stringlib`). Use dot notation for hierarchy (e.g., `collections.list`).
- **Functions**: `camelCase` (e.g., `parseResponse`, `strFind`).
- **Types**: `PascalCase` (e.g., `HttpResponse`, `Option[T]`).
- **Internal Helpers**: Prefix with underscore `_` (e.g., `_strEqAt`).

### 12.2 Argument Ordering
1. **The "Subject" first**: For functions operating on a specific type, the primary object should be the first argument.
   - `strFind(haystack, needle, ...)`
   - `mapPut(map, key, value)`
2. **Options/Configs last**: If a function takes optional configuration or non-primary arguments, place them at the end.

### 12.3 Error Handling
- **Pure functions**: Return `Option[T]` if the failure is "expected" (e.g., `list.head`) or `Result[T, Str]` if the failure needs explanation (e.g., `json.loads`).
- **Effectful functions**: **Must** return `Result[T, Str]` if they perform I/O that can fail (e.g., `socket.tcpConnect`). Use the `?` operator to propagate errors.

### 12.4 Module Structure (The Barrel Pattern)
- **`__init__.flv`**: Acts as a public API surface. It should mostly contain `use` statements to export sub-modules.
- **`.types`**: Dedicated file for shared type definitions.
- **`.core`**: Pure logic, parsing, and data transformations.
- **`.api` / `.client`**: Effectful sectors and high-level workflows.

---

## 13. Library docs: `socket`

### 13.1 Overview
`socket` provides a Python-style **TCP socket** interface through the host bridge. All operations that can fail return `Result[..., Str]`.

### 13.2 Public API (stable)
Import:

```flavent
use socket
```

Types:
- `Socket`: opaque handle (`Int`)
- `TcpPeer`: `{ host: Str, port: Int }`
- `TcpAccept`: `{ sock: Socket, peer: TcpPeer }`

Functions:
- `tcpPeer(host, port) -> TcpPeer`

Sector API (`sector socket`):
- `tcpConnect(host, port) -> Result[Socket, Str]`
- `tcpListen(host, port, backlog) -> Result[Socket, Str]`
- `tcpAccept(sock) -> Result[TcpAccept, Str]`
- `send(sock, data) -> Result[Int, Str]`
- `recv(sock, n) -> Result[Bytes, Str]`
- `sendAll(sock, data) -> Result[Unit, Str]`
- `recvAll(sock, chunk) -> Result[Bytes, Str]`
- `shutdown(sock) -> Result[Unit, Str]`
- `close(sock) -> Result[Unit, Str]`
- `setTimeoutMillis(sock, ms) -> Result[Unit, Str]`

### 13.3 Resource safety
- Always call `socket.close(sock)` once you are done.
- Prefer `sendAll` for request-like protocols (HTTP) to avoid partial writes.

---

## 14. Library docs: `stringlib`

### 14.1 Overview
`stringlib` provides basic string manipulation utilities for ASCII strings.

### 14.2 Public API
Import:
```flavent
use stringlib
```

Functions:
- `strFind(haystack, needle, start) -> Int`: Returns the index of the first occurrence of `needle` in `haystack` starting from `start`, or `-1` if not found.
- `strContains(haystack, needle) -> Bool`: Returns `true` if `needle` is present in `haystack`.
- `startsWith(haystack, prefix) -> Bool`: Returns `true` if `haystack` starts with `prefix`.
- `endsWith(haystack, suffix) -> Bool`: Returns `true` if `haystack` ends with `suffix`.
- `trimLeftSpaces(s) -> Str`: Removes leading spaces.
- `trimRightSpaces(s) -> Str`: Removes trailing spaces.
- `trimSpaces(s) -> Str`: Removes both leading and trailing spaces.
- `split(s, sep) -> List[Str]`: Splits string `s` into a list of substrings based on the separator `sep`.
- `join(xs, sep) -> Str`: Joins a list of strings `xs` into a single string using separator `sep`.

---

## 15. Library docs: `bytelib`

### 15.1 Overview
`bytelib` provides low-level manipulation of the `Bytes` type.

### 15.2 Public API
Import:
```flavent
use bytelib
```

Functions:
- `bytesLen(b) -> Int`: Returns the number of bytes.
- `bytesGet(b, i) -> Int`: Returns the byte value at index `i`.
- `bytesSlice(b, start, end) -> Bytes`: Returns a sub-slice of bytes.
- `bytesConcat(a, b) -> Bytes`: Concatenates two byte sequences.
- `bytesFind(haystack, needle, start) -> Int`: Returns the index of `needle` in `haystack`.
- `bytesStartsWith(haystack, prefix) -> Bool`: Returns `true` if `haystack` starts with `prefix`.
- `bytesEndsWith(haystack, suffix) -> Bool`: Returns `true` if `haystack` ends with `suffix`.
- `bytesToList(b) -> List[Int]`: Converts bytes to a list of integers.
- `bytesFromList(xs) -> Bytes`: Converts a list of integers to bytes.

---

## 17. Library docs: `json`

### 17.1 Overview
`json` provides encoding and decoding for JSON data, mapping between JSON strings and the `JsonValue` ADT.

### 17.2 Public API
Import:
```flavent
use json
```

Types:
- `JsonValue`: Sum type representing JSON structures:
  - `JNull`
  - `JBool(Bool)`
  - `JInt(Int)`
  - `JFloat(Float)`
  - `JStr(Str)`
  - `JArr(List[JsonValue])`
  - `JObj(Map[Str, JsonValue])`

Functions:
- `loads(s: Str) -> Result[JsonValue, Str]`: Parses a JSON string.
- `dumps(v: JsonValue) -> Str`: Serializes a `JsonValue` to string.
- `jNull() -> JsonValue`: Helper for `JNull`.

---

## 18. Library docs: `regex`

### 18.1 Overview
`regex` is a pure Flavent implementation of regular expression matching using a backtracking engine.

### 18.2 Public API
Import:
```flavent
use regex
```

Functions:
- `compile(pattern: Str) -> Result[Regex, Str]`: Compiles a regex string.
- `isMatch(re: Regex, s: Str) -> Bool`: Returns true if the pattern matches anywhere in `s`.
- `findFirst(re: Regex, s: Str) -> Option[Str]`: Returns the first substring that matches.

---

## 19. Library docs: `hashlib`

### 19.1 Overview
`hashlib` provides common cryptographic hashing algorithms (MD5, SHA1, SHA256) via the host bridge.

### 19.2 Public API
Import:
```flavent
use hashlib
```

Functions:
- `md5(data: Bytes) -> Str`: Hex digest of MD5 hash.
- `sha1(data: Bytes) -> Str`: Hex digest of SHA1 hash.
- `sha256(data: Bytes) -> Str`: Hex digest of SHA256 hash.

---

## 20. Library docs: `struct`

### 20.1 Overview
`struct` provides binary data packing and unpacking, compatible with Python's `struct` module.

### 20.2 Public API
Import:
```flavent
use struct
```

Functions:
- `pack(fmt: Str, args: List[Any]) -> Result[Bytes, Str]`: Packs values into bytes according to format.
- `unpack(fmt: Str, data: Bytes) -> Result[List[Any], Str]`: Unpacks bytes into a list of values.
- `calcsize(fmt: Str) -> Result[Int, Str]`: Returns the size of the structure.

---

## 21. Library docs: `random`

### 21.1 Overview
`random` provides deterministic pseudo-random number generation.

### 21.2 Public API
Import:
```flavent
use random
```

Functions:
- `seed(n: Int) -> Unit`: Seeds the global PRNG.
- `randomInt(min: Int, max: Int) -> Int`: Returns a random integer between `min` and `max`.
- `randomFloat() -> Float`: Returns a random float in `[0.0, 1.0)`.

---

## 22. Library docs: `httplib`

### 22.1 Overview
`httplib` is a minimal HTTP/1.1 client built in Flavent. It is split into:
- `httplib.core`: pure request building and response parsing.
- `httplib.client`: effectful `sector httplib` that performs I/O via `socket`.

Import:
```flavent
use httplib
```

### 22.2 Pure helpers (`httplib.core`)
- `buildGetRequest(host, path) -> Bytes`
- `buildGetRequestWith(host, path, headers) -> Bytes`
- `buildPostRequest(host, path, headers, body) -> Bytes`
- `buildRequest(method, host, path, headers, body) -> Bytes`
- `parseResponse(raw) -> Result[HttpResponse, Str]`

### 22.3 Effectful client (`sector httplib`)
- `request(host, port, method, path, headers, body) -> Result[HttpResponse, Str]`
- `get(host, port, path) -> Result[HttpResponse, Str]`
- `getWith(host, port, path, headers) -> Result[HttpResponse, Str]`
- `post(host, port, path, body) -> Result[HttpResponse, Str]`
- `postWith(host, port, path, headers, body) -> Result[HttpResponse, Str]`

### 22.4 Notes / limitations
- Response parsing is intentionally minimal: it splits headers/body on the first `\r\n\r\n` marker and parses the status line and headers.
- Chunked transfer encoding, streaming bodies, and TLS are not implemented.
- Request builder automatically adds default headers if missing:
  - `Host`
  - `User-Agent` (default `flavent-httplib/0`)
  - `Connection: close`
  - `Content-Length` (when body is non-empty)

---

## 23. Library docs: `fslib` & `file`

### 23.1 Overview
`fslib` provides low-level filesystem operations, while `file` provides a more convenient interface for reading and writing files.

### 23.2 `fslib` Public API
- `exists(path: Str) -> Result[Bool, Str]`
- `isDir(path: Str) -> Result[Bool, Str]`
- `isFile(path: Str) -> Result[Bool, Str]`
- `mkdir(path: Str) -> Result[Unit, Str]`
- `mkdirs(path: Str) -> Result[Unit, Str]`
- `remove(path: Str) -> Result[Unit, Str]`
- `rmdir(path: Str) -> Result[Unit, Str]`
- `rename(src: Str, dst: Str) -> Result[Unit, Str]`

### 23.3 `file` Public API
- `readText(path: Str) -> Result[Str, Str]`
- `readBytes(path: Str) -> Result[Bytes, Str]`
- `writeText(path: Str, content: Str) -> Result[Unit, Str]`
- `writeBytes(path: Str, content: Bytes) -> Result[Unit, Str]`

---

## 24. Library docs: `time`

### 24.1 Overview
`time` provides access to the system clock and sleeping.

### 24.2 Public API
- `now() -> Float`: Returns current Unix timestamp.
- `sleep(seconds: Float) -> Unit`: Suspends execution for the given duration.

---

## 25. Library docs: `uuid`

### 25.1 Overview
`uuid` provides UUID generation.

### 25.2 Public API
- `uuid4() -> Bytes`: Generates a random UUID v4.
- `toString(u: Bytes) -> Str`: Converts UUID bytes to standard string representation.
- `parse(s: Str) -> Result[Bytes, Str]`: Parses a UUID string into bytes.

---

## 26. Library docs: `glob` & `tempfile`

### 26.1 `glob` API
- `glob(pattern: Str) -> Result[List[Str], Str]`: Returns a list of paths matching a pattern.

---

## 27. Library docs: `u32`

### 27.1 Overview
`u32` provides 32-bit unsigned integer arithmetic, which is useful for low-level bitwise operations.

### 27.2 Public API
- `u32And(a: Int, b: Int) -> Int`: Bitwise AND.
- `u32Or(a: Int, b: Int) -> Int`: Bitwise OR.
- `u32Xor(a: Int, b: Int) -> Int`: Bitwise XOR.
- `u32Not(a: Int) -> Int`: Bitwise NOT.
- `u32Shl(a: Int, n: Int) -> Int`: Shift left.
- `u32Shr(a: Int, n: Int) -> Int`: Shift right (logical).

---

## 28. Library docs: `statistics`

### 28.1 Overview
`statistics` provides basic mathematical statistical functions.

### 28.2 Public API
- `mean(xs: List[Float]) -> Float`: Arithmetic mean.
- `median(xs: List[Float]) -> Float`: Median value.
- `stdev(xs: List[Float]) -> Float`: Standard deviation.

---

## 29. Library docs: `consoleIO`

### 29.1 Overview
`consoleIO` provides standard terminal input and output operations.

### 29.2 Public API
- `print(s: Str) -> Unit`: Prints a string followed by a newline.
- `readLine() -> Result[Str, Str]`: Reads a line of input from the user.

---

## 30. Library docs: `base64`

### 30.1 Overview
`base64` provides encoding and decoding of binary data to Base64 strings.

### 30.2 Public API
- `encode(data: Bytes) -> Str`: Encodes bytes to a Base64 string.
- `decode(s: Str) -> Result[Bytes, Str]`: Decodes a Base64 string back to bytes.
