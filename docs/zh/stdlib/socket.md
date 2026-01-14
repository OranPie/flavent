# `socket`

## 概述
TCP socket（通过 host bridge）。

推荐把 `socket` 当成“聚合入口”，实际 API 定义在：
- `socket.types`
- `socket.api`

本页提供整体使用说明与示例；签名列表由文档生成器写入下方的 AUTO-GEN 区块。

## 导入
```flavent
use socket
```

## 常见用法

### 连接 + 发送 + 接收

```flavent
use socket

sector main:
  fn run() -> Unit = do:
    let s = rpc socket.tcpConnect("127.0.0.1", 8080)?
    let _ = rpc socket.sendAll(s, b"hello")?
    let resp = rpc socket.recvAll(s, 4096)?
    let _ = rpc socket.close(s)
    return ()
```

## 注意事项
- **必须 close**：成功/失败路径都尽量确保 `rpc socket.close(s)`。
- `recvAll` 会一直读到对端关闭连接（收到空 bytes）。
- 如需避免阻塞，可使用 `setTimeoutMillis`。

## 关联页面
- `socket.types`
- `socket.api`

## 类型
<!-- AUTO-GEN:START TYPES -->
```flavent
```
<!-- AUTO-GEN:END TYPES -->

## 函数
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
```
<!-- AUTO-GEN:END FUNCTIONS -->

