# `regex`

## Overview
Pure Flavent regex engine.

Import:
```flavent
use regex
```

## API
- `compile(pattern: Str) -> Result[Regex, Str]`
- `isMatch(re: Regex, s: Str) -> Bool`
- `findFirst(re: Regex, s: Str) -> Option[Str]`
