# `datetime`

## 概述
纯 Flavent 实现的日期时间解析与格式化工具（ISO 风格）。

支持格式：
- 日期：`YYYY-MM-DD`
- 时间：`HH:MM:SS` 或 `HH:MM:SS.mmm`
- 日期时间：`YYYY-MM-DDTHH:MM:SS` 或 `YYYY-MM-DDTHH:MM:SS.mmm`

## 导入
```flavent
use datetime
```

## 类型
<!-- AUTO-GEN:START TYPES -->
```flavent
type Date = { year: Int, month: Int, day: Int }
type Time = { hour: Int, minute: Int, second: Int, millis: Int }
type DateTime = { date: Date, time: Time }
```
<!-- AUTO-GEN:END TYPES -->

## 函数
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn makeDate(year: Int, month: Int, day: Int) -> Date = { year = year, month = month, day = day }
fn makeTime(hour: Int, minute: Int, second: Int, millis: Int) -> Time = { hour = hour, minute = minute, second = second, millis = millis }
fn makeDateTime(date: Date, time: Time) -> DateTime = { date = date, time = time }
fn isLeapYear(year: Int) -> Bool = (_mod(year, 4) == 0) and ((_mod(year, 100) != 0) or (_mod(year, 400) == 0))
fn daysInMonth(year: Int, month: Int) -> Int = match month == 1 or month == 3 or month == 5 or month == 7 or month == 8 or month == 10 or month == 12:
fn dateIsValid(d: Date) -> Bool = do:
fn timeIsValid(t: Time) -> Bool = t.hour >= 0 and t.hour <= 23 and t.minute >= 0 and t.minute <= 59 and t.second >= 0 and t.second <= 59 and t.millis >= 0 and t.millis <= 999
fn dateTimeIsValid(dt: DateTime) -> Bool = dateIsValid(dt.date) and timeIsValid(dt.time)
fn parseDate(s: Str) -> Result[Date, Str] = do:
fn parseTime(s: Str) -> Result[Time, Str] = do:
fn parseDateTime(s: Str) -> Result[DateTime, Str] = do:
fn formatDate(d: Date) -> Str = _pad4(d.year) + "-" + _pad2(d.month) + "-" + _pad2(d.day)
fn formatTime(t: Time) -> Str = do:
fn formatDateTime(dt: DateTime) -> Str = formatDate(dt.date) + "T" + formatTime(dt.time)
```
<!-- AUTO-GEN:END FUNCTIONS -->
