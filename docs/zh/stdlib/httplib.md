# `httplib`

## 概述
基于 `socket` 的最小 HTTP/1.1 工具库。

导入：
```flavent
use httplib
```

拆分：
- `httplib.core`：纯函数（构造请求、解析响应）
- `httplib.client`：有副作用的 `sector httplib`

## core API
- `buildRequest(method, host, path, headers, body) -> Bytes`
- `buildGetRequest(host, path) -> Bytes`
- `buildGetRequestWith(host, path, headers) -> Bytes`
- `buildPostRequest(host, path, headers, body) -> Bytes`
- `parseResponse(raw) -> Result[HttpResponse, Str]`

请求默认头（缺省时自动补）：
- `Host`
- `User-Agent: flavent-httplib/0`
- `Connection: close`
- `Content-Length`（body 非空时）

## client API（sector `httplib`）
- `request(host, port, method, path, headers, body) -> Result[HttpResponse, Str]`
- `get(host, port, path) -> Result[HttpResponse, Str]`
- `getWith(host, port, path, headers) -> Result[HttpResponse, Str]`
- `post(host, port, path, body) -> Result[HttpResponse, Str]`
- `postWith(host, port, path, headers, body) -> Result[HttpResponse, Str]`

## 限制
暂不支持 TLS、chunked、流式 body。
