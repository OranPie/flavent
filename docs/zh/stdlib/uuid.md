# `uuid`

## 概述
（自动生成的 API 参考页。可在此基础上补充示例与行为/边界说明。）

## 导入
```flavent
use uuid
```

## 类型
```flavent
type UUID = { bytes: Bytes }
```

## 函数
```flavent
fn parse(s: Str) -> Option[UUID] = do:
fn toString(u: UUID) -> Str = _uStrAcc(bytesToList(u.bytes), 0, "")
fn uuid4() -> UUID = do:
```

