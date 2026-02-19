# `url`

## Overview
Pure-Flavent URL and query-string helpers.

Use this module for:
- Percent-encoding/decoding URL components.
- Query-string encode/decode with `+` as space.
- Parsing/building key-value query pairs.

## Import
```flavent
use url
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
type UrlQueryParam = { key: Str, value: Str }
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn encodeComponent(s: Str) -> Str = _encodeAcc(s, 0, strLen(s), false, "")
fn decodeComponent(s: Str) -> Result[Str, Str] = _decodeAcc(s, 0, strLen(s), false, "")
fn queryEncode(s: Str) -> Str = _encodeAcc(s, 0, strLen(s), true, "")
fn queryDecode(s: Str) -> Result[Str, Str] = _decodeAcc(s, 0, strLen(s), true, "")
fn queryParse(q: Str) -> Result[List[UrlQueryParam], Str] = do:
fn queryBuild(parts: List[UrlQueryParam]) -> Str = _buildMany(parts, "")
```
<!-- AUTO-GEN:END FUNCTIONS -->
