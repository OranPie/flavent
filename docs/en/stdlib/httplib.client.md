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
fn requestWithQuery(host: Str, port: Int, method: Str, path: Str, query: List[QueryParam], headers: List[Header], body: Bytes) -> Result[HttpResponse, Str] = do:
fn getQuery(host: Str, port: Int, path: Str, query: List[QueryParam]) -> Result[HttpResponse, Str] = requestWithQuery(host, port, "GET", path, query, Nil, b"")
fn getWithQuery(host: Str, port: Int, path: Str, query: List[QueryParam], headers: List[Header]) -> Result[HttpResponse, Str] = requestWithQuery(host, port, "GET", path, query, headers, b"")
fn head(host: Str, port: Int, path: Str) -> Result[HttpResponse, Str] = request(host, port, "HEAD", path, Nil, b"")
fn headWith(host: Str, port: Int, path: Str, headers: List[Header]) -> Result[HttpResponse, Str] = request(host, port, "HEAD", path, headers, b"")
fn put(host: Str, port: Int, path: Str, body: Bytes) -> Result[HttpResponse, Str] = request(host, port, "PUT", path, Nil, body)
fn putWith(host: Str, port: Int, path: Str, headers: List[Header], body: Bytes) -> Result[HttpResponse, Str] = request(host, port, "PUT", path, headers, body)
fn patch(host: Str, port: Int, path: Str, body: Bytes) -> Result[HttpResponse, Str] = request(host, port, "PATCH", path, Nil, body)
fn patchWith(host: Str, port: Int, path: Str, headers: List[Header], body: Bytes) -> Result[HttpResponse, Str] = request(host, port, "PATCH", path, headers, body)
fn delete(host: Str, port: Int, path: Str) -> Result[HttpResponse, Str] = request(host, port, "DELETE", path, Nil, b"")
fn deleteWith(host: Str, port: Int, path: Str, headers: List[Header], body: Bytes) -> Result[HttpResponse, Str] = request(host, port, "DELETE", path, headers, body)
fn requestJson(host: Str, port: Int, method: Str, path: Str, headers: List[Header], jsonText: Str) -> Result[HttpResponse, Str] = do:
fn postJson(host: Str, port: Int, path: Str, jsonText: Str) -> Result[HttpResponse, Str] = requestJson(host, port, "POST", path, Nil, jsonText)
fn postJsonWith(host: Str, port: Int, path: Str, headers: List[Header], jsonText: Str) -> Result[HttpResponse, Str] = requestJson(host, port, "POST", path, headers, jsonText)
fn putJson(host: Str, port: Int, path: Str, jsonText: Str) -> Result[HttpResponse, Str] = requestJson(host, port, "PUT", path, Nil, jsonText)
fn patchJson(host: Str, port: Int, path: Str, jsonText: Str) -> Result[HttpResponse, Str] = requestJson(host, port, "PATCH", path, Nil, jsonText)
```
<!-- AUTO-GEN:END FUNCTIONS -->
