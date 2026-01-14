# `httplib.client`

## 概述
基于 `socket` 的 effectful HTTP client。

行为：
- `request` 会连接、发送请求、`recvAll(4096)`，然后关闭 socket。
- 这是一次性请求模型（不做 keep-alive）。

## 导入
```flavent
use httplib.client
```

## 类型
<!-- AUTO-GEN:START TYPES -->
```flavent
```
<!-- AUTO-GEN:END TYPES -->

## 函数
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn request(host: Str, port: Int, method: Str, path: Str, headers: List[Header], body: Bytes) -> Result[HttpResponse, Str] = do:
fn get(host: Str, port: Int, path: Str) -> Result[HttpResponse, Str] = do:
fn getWith(host: Str, port: Int, path: Str, headers: List[Header]) -> Result[HttpResponse, Str] = request(host, port, "GET", path, headers, b"")
fn post(host: Str, port: Int, path: Str, body: Bytes) -> Result[HttpResponse, Str] = request(host, port, "POST", path, Nil, body)
fn postWith(host: Str, port: Int, path: Str, headers: List[Header], body: Bytes) -> Result[HttpResponse, Str] = request(host, port, "POST", path, headers, body)
```
<!-- AUTO-GEN:END FUNCTIONS -->
