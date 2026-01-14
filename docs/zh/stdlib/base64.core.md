# `base64.core`

## 概述
（自动生成的 API 参考页。可在此基础上补充示例与行为/边界说明。）

## 导入
```flavent
use base64.core
```

## 函数
```flavent
fn encodeStd(b: Bytes) -> Str = _b64Encode(_b64AlphaStd(), b)
fn encodeUrl(b: Bytes) -> Str = _b64Encode(_b64AlphaUrl(), b)
fn decodeStd(s: Str) -> Bytes = _b64Decode(_b64AlphaStd(), s)
fn decodeUrl(s: Str) -> Bytes = _b64Decode(_b64AlphaUrl(), s)
```

