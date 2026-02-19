# `flvrepr`

## Overview
Helpers for compact string metadata encoding/decoding used by mixin hook and function-target descriptors.

## Import
```flavent
use flvrepr
```

## Examples
```flavent
let meta = encodeFunctionTarget("S.base", "invoke", "10", "anchor:base")
let p = metaGet(meta, "priority")      // Some("10")
let meta2 = metaSet(meta, "priority", "20")
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
type MetaPair = { key: Str, value: Str }
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn pair(key: Str, value: Str) -> MetaPair = { key = key, value = value }
fn encodePair(p: MetaPair) -> Str = p.key + "=" + p.value
fn encodePairs(xs: List[MetaPair]) -> Str = match xs:
fn encodeFunctionTarget(target: Str, point: Str, priority: Str, at: Str) -> Str = encodePairs(
fn decodePairs(meta: Str) -> List[MetaPair] = _decodeFrom(meta, 0, strLen(meta), Nil)
fn metaGet(meta: Str, key: Str) -> Option[Str] = _findPair(decodePairs(meta), key)
fn metaSet(meta: Str, key: Str, value: Str) -> Str = encodePairs(_upsertAcc(decodePairs(meta), key, value, Nil, false))
```
<!-- AUTO-GEN:END FUNCTIONS -->
