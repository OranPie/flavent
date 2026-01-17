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
- No chunked *request* encoding
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
type QueryParam = { key: Str, value: Str }
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn header(key: Str, value: Str) -> Header = { key = key, value = value }
fn queryParam(key: Str, value: Str) -> QueryParam = { key = key, value = value }
fn headersHas(xs: List[Header], key: Str) -> Bool = _headerHas(xs, key)
fn headersAdd(xs: List[Header], key: Str, value: Str) -> List[Header] = Cons(header(key, value), xs)
fn lowerAscii(s: Str) -> Str = _lowerAsciiAcc(s, 0, strLen(s), "")
fn headersGet(xs: List[Header], key: Str) -> Option[Str] = _headersGetCI(xs, lowerAscii(key))
fn headersHasCI(xs: List[Header], key: Str) -> Bool = match headersGet(xs, key):
fn headersAddIfMissingCI(xs: List[Header], key: Str, value: Str) -> List[Header] = match headersHasCI(xs, key):
fn defaultUserAgent() -> Str = "flavent-httplib/0"
fn intToStr(n: Int) -> Str = match n == 0:
fn headersToBytes(xs: List[Header]) -> Bytes = do:
fn buildRequest(method: Str, host: Str, path: Str, headers: List[Header], body: Bytes) -> Bytes = do:
fn urlEncode(s: Str) -> Str = _urlEncodeAcc(s, 0, strLen(s), "")
fn buildQuery(xs: List[QueryParam]) -> Str = _buildQueryAcc(xs, "")
fn buildPathWithQuery(path: Str, xs: List[QueryParam]) -> Str = match xs:
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
fn buildHeadRequest(host: Str, path: Str) -> Bytes = buildRequest("HEAD", host, path, Nil, b"")
fn buildHeadRequestWith(host: Str, path: Str, headers: List[Header]) -> Bytes = buildRequest("HEAD", host, path, headers, b"")
fn buildPutRequest(host: Str, path: Str, headers: List[Header], body: Bytes) -> Bytes = buildRequest("PUT", host, path, headers, body)
fn buildPatchRequest(host: Str, path: Str, headers: List[Header], body: Bytes) -> Bytes = buildRequest("PATCH", host, path, headers, body)
fn buildDeleteRequest(host: Str, path: Str, headers: List[Header], body: Bytes) -> Bytes = buildRequest("DELETE", host, path, headers, body)
fn buildJsonRequest(method: Str, host: Str, path: Str, headers: List[Header], jsonText: Str) -> Bytes = do:
fn parseHexDigits(s: Str) -> Result[Int, Str] = _parseHexAcc(s, 0, strLen(s), 0, false)
fn decodeChunked(b: Bytes) -> Result[Bytes, Str] = do:
fn parseResponse(raw: Bytes) -> Result[HttpResponse, Str] = do:
```
<!-- AUTO-GEN:END FUNCTIONS -->
