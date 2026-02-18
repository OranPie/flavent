# Flavent

A safe, modern, and minimal functional programming language designed for reliability and ease of use.

## Overview

Flavent is a statically typed, expression-oriented functional language that compiles to a high-performance bytecode (or transpiles to Python for the host bridge). It features:

- **Algebraic Data Types (ADTs)**: Powerful `type` system with sum types and product types.
- **Pattern Matching**: Exhaustive `match` expressions for safe data processing.
- **Sectors & Effects**: Explicit side-effect management using `sector` and `rpc`.
- **Lightweight Concurrency**: Built-in async/await model with event loop support.
- **Rich Standard Library**: Minimal but highly functional stdlib (JSON, Regex, HTTP, Sockets, etc.).

## Installation

```bash
# Clone the repository
git clone https://github.com/OranPie/flavent.git
cd flavent

# Install dependencies
pip install -e .
```

## Quick Start

Create a file `hello.flv`:

```flavent
use consoleIO

sector main:
  fn run() -> Unit = do:
    rpc print("Hello, Flavent!")
    return ()

run()
```

Run it:

```bash
python3 -m flavent hello.flv
```

## Testing

Flavent comes with a built-in test runner `flvtest`.

```bash
# Run all tests
python3 -m pytest
```

For CI-oriented compiler checks:

```bash
python3 -m flavent check examples/minimal.flv --strict --report-junit reports/check.xml
```

For CI-style pytest output artifacts:

```bash
python3 -m pytest -q --junit-xml=reports/junit.xml
```

## Documentation

- [Language Specification & Library Docs](DOCS.md)
- [Bridge API Summary](BRIDGE_PYTHON_SUMMARY.md)
- [Stdlib Docs (one page per module)](docs/en/stdlib/index.md)

## Package Management (flm)

Flavent projects can be managed with a JSON manifest `flm.json`.

Common commands:

```bash
flavent pkg init
flavent pkg add mylib --path ../mylib
flavent pkg add netlib --git ssh://git@codeberg.org/OrangePie/netlib.git --rev <rev>
flavent pkg install
flavent pkg list
```

See:

- [FLM Spec](FLM_SPEC.md)

## Python Adapters (v2: subprocess isolation)

Python integration is **not** done by direct imports. Instead, Flavent calls Python through a strict adapter interface and a single controlled bridge entrypoint.

Workflow:

1. Declare adapters in `flm.json` under `pythonAdapters`.
2. Run `flavent pkg install`.
3. Import and call generated wrappers:

```flavent
use pyadapters.demo

// demo.echo(payload) -> Result[Bytes, Str]
let r = rpc demo.echo(b"hello")
```

## 中文文档 (Chinese)

- [docs/zh/README.md](docs/zh/README.md)
- [docs/zh/FLM_SPEC.md](docs/zh/FLM_SPEC.md)
- [docs/zh/DOCS.md](docs/zh/DOCS.md)
- [docs/zh/COMPILER.md](docs/zh/COMPILER.md)
- [docs/zh/stdlib/index.md](docs/zh/stdlib/index.md)
