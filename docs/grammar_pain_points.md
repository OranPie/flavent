# Grammar Pain Points Baseline

Date: 2026-02-18

This note captures current grammar friction points before Phase 2 parser/diagnostics work.

## 1) String and bytes literal edge cases

- Escapes now support common ASCII forms plus `\xNN`, but unknown escapes are preserved literally for compatibility.
- This is useful for regex-style text (`"\d+"`) but can hide mistakes like `"\q"` typos.
- Current behavior is permissive first; diagnostics should distinguish:
  - clearly invalid forms (bad `\x` digits, unterminated literals),
  - compatibility-preserved unknown escapes (warn-level candidate).

## 2) Operator and pipe precedence visibility

- Expression precedence exists in parser tables (`or`, `and`, compare, add, mul), and pipe (`|>`) is parsed as an outer chain.
- Behavior is stable but not obvious to users without reading parser code/tests.
- We need a compact published precedence table with examples such as:
  - `a + b |> f` (pipe after arithmetic),
  - `not a and b`,
  - `x |> f(y) |> g`.

## 3) Pattern matching ambiguity and ergonomics

- Pattern parsing uses an uppercase heuristic: single-name uppercase identifiers are treated as constructors; lowercase as binders.
- This is practical but implicit and surprising for mixed naming styles.
- Diagnostics should explicitly explain whether a name was interpreted as a constructor or variable binder.

## 4) Parser diagnostics and recovery quality

- Some parse failures still return broad messages like `Expected expression` / `Unexpected top-level token`.
- Near-term improvement target: expected-token hints and localized context in common failure points (call args, trailing separators, match arms, block indentation transitions).

## 5) Test grammar split visibility (`tests_flv`)

- `tests_flv/*.flv` uses `flvtest` case syntax (`test "..." -> do:`) that is rewritten before normal parse.
- This split is intentional, but not obvious to contributors reading parser errors directly.
- Contributor docs should call out this rewrite boundary to reduce confusion during grammar debugging.
