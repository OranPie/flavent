# `stringlib`

## Overview
Basic ASCII string helpers.

Import:
```flavent
use stringlib
```

## API
- `strFind(haystack, needle, start) -> Int`
- `strContains(haystack, needle) -> Bool`
- `startsWith(haystack, prefix) -> Bool`
- `endsWith(haystack, suffix) -> Bool`
- `trimLeftSpaces(s) -> Str`
- `trimRightSpaces(s) -> Str`
- `trimSpaces(s) -> Str`
- `split(s, sep) -> List[Str]`
- `join(xs, sep) -> Str`

Notes:
- `trim*Spaces` only treats ASCII space (code 32) as whitespace.
