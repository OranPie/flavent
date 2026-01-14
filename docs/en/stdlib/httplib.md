# `httplib`

## Overview
Minimal HTTP/1.1 helpers built on `socket`.

Import:
```flavent
use httplib
```

Split:
- `httplib.core`: pure request building + response parsing
- `httplib.client`: effectful `sector httplib`

## Core API
- `buildRequest(method, host, path, headers, body) -> Bytes`
- `buildGetRequest(host, path) -> Bytes`
- `buildGetRequestWith(host, path, headers) -> Bytes`
- `buildPostRequest(host, path, headers, body) -> Bytes`
- `parseResponse(raw) -> Result[HttpResponse, Str]`

Request defaults (if missing):
- `Host`
- `User-Agent: flavent-httplib/0`
- `Connection: close`
- `Content-Length` (when body non-empty)

## Client API (`sector httplib`)
- `request(host, port, method, path, headers, body) -> Result[HttpResponse, Str]`
- `get(host, port, path) -> Result[HttpResponse, Str]`
- `getWith(host, port, path, headers) -> Result[HttpResponse, Str]`
- `post(host, port, path, body) -> Result[HttpResponse, Str]`
- `postWith(host, port, path, headers, body) -> Result[HttpResponse, Str]`

## Limitations
No TLS, no chunked encoding, no streaming.
