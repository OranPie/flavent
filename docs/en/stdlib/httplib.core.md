# `httplib.core`

## Overview
Pure helpers for HTTP/1.1 request building and response parsing.

Behavior:
- `buildRequest` auto-adds headers if missing:
  - `Host`
  - `User-Agent` (from `defaultUserAgent()`)
  - `Connection: close`
  - `Content-Length` (when `body` is non-empty)

Limitations:
- No TLS
- No chunked encoding
- No streaming

## Import
```flavent
use httplib.core
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
type Header = { key: Str, value: Str }
type HttpResponse = { status: Int, reason: Str, headers: List[Header], body: Bytes }
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn header(key: Str, value: Str) -> Header = { key = key, value = value }
fn headersHas(xs: List[Header], key: Str) -> Bool = _headerHas(xs, key)
fn defaultUserAgent() -> Str = "flavent-httplib/0"
fn intToStr(n: Int) -> Str = match n == 0:
fn headersToBytes(xs: List[Header]) -> Bytes = do:
fn buildRequest(method: Str, host: Str, path: Str, headers: List[Header], body: Bytes) -> Bytes = do:
fn asciiFromBytes(b: Bytes) -> Str = _asciiFromBytesAcc(b, 0, bytesLen(b), "")
fn asciiToBytes(s: Str) -> Bytes = bytesFromList(_asciiCodesAcc(s, 0, strLen(s), Nil))
fn strFind(h: Str, needle: Str, start: Int) -> Int = do:
fn parseIntDigits(s: Str) -> Int = _parseIntDigitsAcc(s, 0, strLen(s), 0)
fn bytesFind(h: Bytes, needle: Bytes, start: Int) -> Int = do:
fn trimLeftSpaces(s: Str) -> Str = _trimLeftSpacesAcc(s, 0, strLen(s))
fn parseHeadersBytes(b: Bytes) -> List[Header] = _parseHeadersBytesAcc(b, Nil)
fn buildGetRequest(host: Str, path: Str) -> Bytes = do:
fn buildGetRequestWith(host: Str, path: Str, headers: List[Header]) -> Bytes = buildRequest("GET", host, path, headers, b"")
fn buildPostRequest(host: Str, path: Str, headers: List[Header], body: Bytes) -> Bytes = buildRequest("POST", host, path, headers, body)
fn parseResponse(raw: Bytes) -> Result[HttpResponse, Str] = do:
```
<!-- AUTO-GEN:END FUNCTIONS -->
