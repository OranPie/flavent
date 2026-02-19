# `log`

## 概述
基于 `consoleIO` 的分级日志辅助模块。

提供：
- `LogLevel` 预置等级（trace/debug/info/warn/error）
- `Logger` 配置（`name`、`minPriority`）
- 纯函数格式化/过滤能力，以及带副作用的输出函数

## 导入
```flavent
use log
```

## 类型
<!-- AUTO-GEN:START TYPES -->
```flavent
type LogLevel = { name: Str, priority: Int }
type Logger = { name: Str, minPriority: Int }
type LogRecord = { level: LogLevel, logger: Str, message: Str }
```
<!-- AUTO-GEN:END TYPES -->

## 函数
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn logLevelTrace() -> LogLevel = { name = "TRACE", priority = 10 }
fn logLevelDebug() -> LogLevel = { name = "DEBUG", priority = 20 }
fn logLevelInfo() -> LogLevel = { name = "INFO", priority = 30 }
fn logLevelWarn() -> LogLevel = { name = "WARN", priority = 40 }
fn logLevelError() -> LogLevel = { name = "ERROR", priority = 50 }
fn logDefault() -> Logger = { name = "", minPriority = logLevelInfo().priority }
fn logNamed(name: Str) -> Logger = { name = name, minPriority = logLevelInfo().priority }
fn logWithName(logger: Logger, name: Str) -> Logger = { name = name, minPriority = logger.minPriority }
fn logWithMinLevel(logger: Logger, level: LogLevel) -> Logger = { name = logger.name, minPriority = level.priority }
fn logShouldEmit(logger: Logger, level: LogLevel) -> Bool = level.priority >= logger.minPriority
fn logRecord(level: LogLevel, logger: Logger, message: Str) -> LogRecord = {
fn logFormat(rec: LogRecord) -> Str = do:
fn logPrepare(logger: Logger, level: LogLevel, message: Str) -> Option[Str] = match logShouldEmit(logger, level):
```
<!-- AUTO-GEN:END FUNCTIONS -->
