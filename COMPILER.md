# Flavent Compiler & Execution Flow

This document details the internal architecture of the Flavent compiler and the lifecycle of a program from source code to execution.

## 1. Overview of the Pipeline

The Flavent compiler follows a traditional multi-pass architecture, with a heavy emphasis on early name resolution and structured lowering before typechecking.

1.  **Lexing (`lexer.py`)**: Converts UTF-8 source into a stream of tokens. Handles indentation-based scoping.
2.  **Parsing (`parser.py`)**: Consumes tokens to produce an Abstract Syntax Tree (AST).
3.  **Resolution (`resolve.py`)**: 
    - Loads Standard Library modules.
    - Resolves all identifiers to unique Symbol IDs.
    - Handles imports and namespace management.
4.  **Lowering (`lower.py`)**: Converts the high-level AST into High-level Intermediate Representation (HIR).
    - Desugars complex constructs.
    - Flattens nested expressions into structured statements.
5.  **Typechecking (`typecheck.py`)**:
    - Performs bidirectional type inference.
    - Validates ADT exhaustiveness in match expressions.
    - Checks sector/effect constraints.
6.  **Runtime (`runtime.py`)**:
    - Translates HIR to Python-level execution (via an interpreter or direct mapping).
    - Manages the Event Loop and Sector effects.

---

## 2. Phase Details

### 2.1 Lexing (`lexer.py`)
Flavent uses an indentation-based syntax similar to Python but more rigid for functional purity.
- **Indentation Tracking**: The lexer maintains an indentation stack to emit `INDENT` and `DEDENT` tokens.
- **Top-level restriction**: Files must start at column 1.
- **Significant Whitespace**: Newlines are converted to `NEWLINE` tokens except inside parentheses or after specific operators.

### 2.2 Parsing (`parser.py`)
A recursive descent parser that builds the AST defined in `ast.py`.
- **Expression-Oriented**: Almost everything in Flavent is an expression.
- **Recovery**: The parser is designed to stop at the first fatal error but provides spans for diagnostics.

### 2.3 Name Resolution (`resolve.py`)
This is a critical phase in Flavent. Unlike many languages that typecheck and resolve names simultaneously, Flavent separates them.
- **Symbol Table**: Every unique variable, function, and type is assigned a `SymbolId`.
- **Standard Library Expansion**: When `use stdlib_module` is encountered, the compiler recursively parses and resolves those files.
- **Ambiguity Detection**: Rejects duplicate names in the same scope or ambiguous imports.

### 2.4 Lowering (`lower.py`)
Transforms AST to HIR (`hir.py`).
- **Desugaring**: Converts `match` expressions into a series of primitive decision trees.
- **RPC Flattening**: Ensures `rpc` calls (effects) are properly tagged for the runtime.
- **Variable Normalization**: Rewrites variables to reference their `SymbolId` directly.

### 2.5 Typechecking (`typecheck.py`)
A robust type system supporting:
- **Parametric Polymorphism**: Generic types like `List[T]`.
- **ADT Validation**: Ensures that every constructor of a sum type is handled in `match` blocks.
- **Sector Isolation**: Ensures that code in one `sector` cannot perform illegal rpc calls without permission.

### 2.6 Runtime & Event Loop (`runtime.py`)
Flavent doesn't just run code; it manages an execution environment.
- **Effect Handlers**: When an `rpc` call is made, the runtime looks up the handler in the active `sector`.
- **Asynchronous Execution**: Supports non-blocking I/O through an internal event loop.
- **Python Bridge**: Marshals data between Flavent types and Python types for host operations (e.g., `socket`, `file`).

---

## 3. Execution Flow Summary

To run a Flavent program:
1. `flavent.cli` initializes the pipeline.
2. `resolve_program_with_stdlib` is called to merge the user code with necessary standard library files.
3. The resulting resolved program is lowered to HIR.
4. The HIR is typechecked.
5. If successful, `runtime.run_hir` starts the event loop and executes the `main` sector.
