# `stringfmt`

## Overview
String formatting utilities.

Import:
```flavent
use stringfmt
```

## API
- `format(tmpl: Str, args: List[Str]) -> Str`
- `formatWith(tmpl: Str, posArgs: List[Str], namedArgs: Map[Str, Str]) -> Str`
- `formatMap(tmpl: Str, args: Map[Str, Str]) -> Str`
