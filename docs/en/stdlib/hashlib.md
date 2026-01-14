# `hashlib`

## Overview
(Edit this page freely. The generator only updates the marked API blocks.)

## Import
```flavent
use hashlib
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn md5Digest(b: Bytes) -> Bytes = _pyMd5Digest(b)
fn md5Hex(b: Bytes) -> Str = _pyMd5Hex(b)
fn sha1Digest(b: Bytes) -> Bytes = _pySha1Digest(b)
fn sha1Hex(b: Bytes) -> Str = _pySha1Hex(b)
fn sha256Digest(b: Bytes) -> Bytes = sha256DigestNative(b)
fn sha256Hex(b: Bytes) -> Str = sha256HexNative(b)
fn sha512Digest(b: Bytes) -> Bytes = _pySha512Digest(b)
fn sha512Hex(b: Bytes) -> Str = _pySha512Hex(b)
```
<!-- AUTO-GEN:END FUNCTIONS -->
