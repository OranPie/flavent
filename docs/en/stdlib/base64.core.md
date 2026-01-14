# `base64.core`

## Overview
(Edit this page freely. The generator only updates the marked API blocks.)

## Import
```flavent
use base64.core
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn encodeStd(b: Bytes) -> Str = _b64Encode(_b64AlphaStd(), b)
fn encodeUrl(b: Bytes) -> Str = _b64Encode(_b64AlphaUrl(), b)
fn decodeStd(s: Str) -> Bytes = _b64Decode(_b64AlphaStd(), s)
fn decodeUrl(s: Str) -> Bytes = _b64Decode(_b64AlphaUrl(), s)
```
<!-- AUTO-GEN:END FUNCTIONS -->
