# `tempfile`

## Overview
Temporary file and directory creation.

Import:
```flavent
use tempfile
```

## API
- `mkstemp(prefix: Str, suffix: Str) -> Result[Str, Str]`
- `mkdtemp(prefix: Str) -> Result[Str, Str]`
