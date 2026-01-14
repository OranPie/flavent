# `struct`

## Overview
Binary packing/unpacking (Python struct-compatible).

Import:
```flavent
use struct
```

## API
- `calcsize(fmt: Str) -> Result[Int, Str]`
- `pack(fmt: Str, args: List[Int]) -> Result[Bytes, Str]`
- `unpack(fmt: Str, data: Bytes) -> Result[List[Int], Str]`
- `unpackFrom(fmt: Str, data: Bytes, offset: Int) -> Result[List[Int], Str]`
