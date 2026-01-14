# `base64`

## 概述
（自动生成的 API 参考页。可在此基础上补充示例与行为/边界说明。）

## 导入
```flavent
use base64
```

## 函数
```flavent
fn encode(b: Bytes) -> Str = encodeStd(b)
fn decode(s: Str) -> Bytes = decodeStd(s)
fn urlsafeEncode(b: Bytes) -> Str = encodeUrl(b)
fn urlsafeDecode(s: Str) -> Bytes = decodeUrl(s)
```

