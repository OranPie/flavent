# `hashlib.sha256`

## Overview
(Edit this page freely. The generator only updates the marked API blocks.)

## Import
```flavent
use hashlib.sha256
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn sha256DigestNative(b: Bytes) -> Bytes = do:
fn sha256HexNative(b: Bytes) -> Str = _shaHexAcc(bytesToList(sha256DigestNative(b)), "")
```
<!-- AUTO-GEN:END FUNCTIONS -->
