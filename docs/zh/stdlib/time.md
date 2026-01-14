# `time`

## 概述
（自动生成的 API 参考页。可在此基础上补充示例与行为/边界说明。）

## 导入
```flavent
use time
```

## 类型
```flavent
type Duration = { millis: Int }
type Instant = { millis: Int }
```

## 函数
```flavent
fn durationMillis(ms: Int) -> Duration = { millis = ms }
fn durationSeconds(s: Int) -> Duration = durationMillis(s * 1000)
fn durationToMillis(d: Duration) -> Int = d.millis
fn durationToSeconds(d: Duration) -> Int = d.millis / 1000
fn durationAdd(a: Duration, b: Duration) -> Duration = durationMillis(a.millis + b.millis)
fn durationSub(a: Duration, b: Duration) -> Duration = durationMillis(a.millis - b.millis)
fn instantFromMillis(ms: Int) -> Instant = { millis = ms }
fn instantToMillis(t: Instant) -> Int = t.millis
fn instantAdd(t: Instant, d: Duration) -> Instant = instantFromMillis(t.millis + d.millis)
fn instantSub(t: Instant, d: Duration) -> Instant = instantFromMillis(t.millis - d.millis)
fn instantSince(later: Instant, earlier: Instant) -> Duration = durationMillis(later.millis - earlier.millis)
fn instantBefore(a: Instant, b: Instant) -> Bool = a.millis < b.millis
fn nowMillis() -> Int = rpc _bridge_python.nowMillis()
fn nowNanos() -> Int = rpc _bridge_python.nowNanos()
fn nowSeconds() -> Int = nowMillis() / 1000
fn nowInstant() -> Instant = instantFromMillis(nowMillis())
fn monoMillis() -> Int = rpc _bridge_python.monoMillis()
fn monoNanos() -> Int = rpc _bridge_python.monoNanos()
fn sleepMillis(ms: Int) -> Unit = call _bridge_python.sleep(ms)
fn sleepSeconds(s: Int) -> Unit = sleepMillis(s * 1000)
fn sleepDuration(d: Duration) -> Unit = sleepMillis(d.millis)
fn elapsedSince(t0: Instant) -> Duration = durationMillis(nowMillis() - t0.millis)
fn sleep(ms: Int) -> Unit = sleepMillis(ms)
```

