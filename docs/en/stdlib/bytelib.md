# `bytelib`

## Overview
Low-level `Bytes` manipulation.

Import:
```flavent
use bytelib
```

## API
- `bytesLen(b) -> Int`
- `bytesGet(b, i) -> Int`
- `bytesSlice(b, start, end) -> Bytes`
- `bytesConcat(a, b) -> Bytes`
- `bytesFromList(xs: List[Int]) -> Bytes`
- `bytesToList(b) -> List[Int]`

Search helpers:
- `bytesFind(haystack, needle, start) -> Int`
- `bytesStartsWith(haystack, prefix) -> Bool`
- `bytesEndsWith(haystack, suffix) -> Bool`
