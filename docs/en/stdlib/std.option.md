# `std.option`

## Overview
`Option[T]` for nullable values.

Import:
```flavent
use std.option
```

## Type
- `Option[T] = Some(T) | None`

## API
- `unwrapOr(o, default) -> T`
- `isSome(o) -> Bool`
- `isNone(o) -> Bool`
- `orElse(o, other) -> Option[T]`
- `okOr(o, err) -> Result[T, E]`
- `unwrapOrZeroInt(o: Option[Int]) -> Int`
- `unwrapOrEmptyStr(o: Option[Str]) -> Str`
- `toList(o) -> List[T]`
- `fromBool(cond, v) -> Option[T]`
