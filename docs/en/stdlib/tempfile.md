# `tempfile`

## Overview
(Edit this page freely. The generator only updates the marked API blocks.)

## Import
```flavent
use tempfile
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn mkstemp(prefix: Str, suffix: Str) -> Result[Str, Str] = rpc fslib.tempFile(prefix, suffix)
fn mkdtemp(prefix: Str) -> Result[Str, Str] = rpc fslib.tempDir(prefix)
```
<!-- AUTO-GEN:END FUNCTIONS -->
