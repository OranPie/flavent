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

## Documentation

- [Language Specification & Library Docs](DOCS.md)
- [Bridge API Summary](BRIDGE_PYTHON_SUMMARY.md)
