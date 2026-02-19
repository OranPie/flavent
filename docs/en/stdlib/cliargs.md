# `cliargs`

## Overview
Deterministic CLI argument parser for list-based argv inputs.

Supports:
- Long flags/options: `--verbose`, `--port=8080`, `--port 8080`
- Short flag bundles: `-abc` => `a`, `b`, `c`
- Positional args and `--` option terminator

## Import
```flavent
use cliargs
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
type CliArgs = {
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn cliEmpty() -> CliArgs = { flags = setEmpty(), options = mapEmpty(), positionals = Nil, raw = Nil }
fn cliParse(argv: List[Str]) -> Result[CliArgs, Str] = _parseAcc(argv, false, setEmpty(), mapEmpty(), Nil, Nil)
fn cliHasFlag(args: CliArgs, name: Str) -> Bool = setHas(args.flags, name)
fn cliGetOption(args: CliArgs, key: Str) -> Option[Str] = mapGet(args.options, key)
fn cliGetOptionOr(args: CliArgs, key: Str, default: Str) -> Str = mapGetOr(args.options, key, default)
fn cliPositionals(args: CliArgs) -> List[Str] = args.positionals
fn cliRaw(args: CliArgs) -> List[Str] = args.raw
```
<!-- AUTO-GEN:END FUNCTIONS -->
