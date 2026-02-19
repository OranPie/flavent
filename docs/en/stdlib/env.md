# `env`

## Overview
Environment-like key/value store API with `Result`-based operations.

This module provides a deterministic env state value:
- Read/write string values by key.
- List all key/value pairs.
- Clear or remove keys.

## Import
```flavent
use env
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
type Env = Map[Str, Str]
type EnvVar = { key: Str, value: Str }
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn envEmpty() -> Env = mapEmpty()
fn envGet(state: Env, key: Str) -> Result[Option[Str], Str] = Ok(mapGet(state, key))
fn envGetOr(state: Env, key: Str, default: Str) -> Result[Str, Str] = Ok(mapGetOr(state, key, default))
fn envSet(state: Env, key: Str, value: Str) -> Result[Env, Str] = Ok(mapPut(state, key, value))
fn envUnset(state: Env, key: Str) -> Result[Env, Str] = Ok(mapRemove(state, key))
fn envHas(state: Env, key: Str) -> Result[Bool, Str] = Ok(mapHasKey(state, key))
fn envList(state: Env) -> Result[List[EnvVar], Str] = Ok(_envVarsFromMapEntries(mapToList(state)))
fn envClear(state: Env) -> Result[Env, Str] = Ok(mapEmpty())
```
<!-- AUTO-GEN:END FUNCTIONS -->
