# `httplib.client`

## Overview
Effectful HTTP client built on `socket`.

Behavior:
- `request` connects, sends the request, `recvAll(4096)`, then closes the socket.
- This is a one-shot request model (no keep-alive).

## Import
```flavent
use httplib.client
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn request(host: Str, port: Int, method: Str, path: Str, headers: List[Header], body: Bytes) -> Result[HttpResponse, Str] = do:
fn get(host: Str, port: Int, path: Str) -> Result[HttpResponse, Str] = do:
fn getWith(host: Str, port: Int, path: Str, headers: List[Header]) -> Result[HttpResponse, Str] = request(host, port, "GET", path, headers, b"")
fn post(host: Str, port: Int, path: Str, body: Bytes) -> Result[HttpResponse, Str] = request(host, port, "POST", path, Nil, body)
fn postWith(host: Str, port: Int, path: Str, headers: List[Header], body: Bytes) -> Result[HttpResponse, Str] = request(host, port, "POST", path, headers, body)
```
<!-- AUTO-GEN:END FUNCTIONS -->
