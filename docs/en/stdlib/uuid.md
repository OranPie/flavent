# `uuid`

## Overview
(Edit this page freely. The generator only updates the marked API blocks.)

## Import
```flavent
use uuid
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
type UUID = { bytes: Bytes }
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn parse(s: Str) -> Option[UUID] = do:
fn toString(u: UUID) -> Str = _uStrAcc(bytesToList(u.bytes), 0, "")
fn uuid4() -> UUID = do:
```
<!-- AUTO-GEN:END FUNCTIONS -->
