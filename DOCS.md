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
