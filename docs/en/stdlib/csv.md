# `csv`

## Overview
Pure-Flavent CSV helpers for parsing and formatting rows.

Features:
- Configurable delimiter and quote characters.
- RFC-style quote escaping (`""` inside quoted fields).
- Line-based parse/stringify helpers.

## Import
```flavent
use csv
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
type CsvOptions = { delimiter: Str, quote: Str }
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn csvDefaultOptions() -> CsvOptions = { delimiter = ",", quote = "\"" }
fn csvParseLineWith(line: Str, opts: CsvOptions) -> Result[List[Str], Str] = do:
fn csvParseLine(line: Str) -> Result[List[Str], Str] = csvParseLineWith(line, csvDefaultOptions())
fn csvParseWith(text: Str, opts: CsvOptions) -> Result[List[List[Str]], Str] = do:
fn csvParse(text: Str) -> Result[List[List[Str]], Str] = csvParseWith(text, csvDefaultOptions())
fn csvEncodeFieldWith(field: Str, opts: CsvOptions) -> Str = do:
fn csvEncodeField(field: Str) -> Str = csvEncodeFieldWith(field, csvDefaultOptions())
fn csvStringifyLineWith(fields: List[Str], opts: CsvOptions) -> Str = _csvJoinFieldsAcc(fields, opts, "")
fn csvStringifyLine(fields: List[Str]) -> Str = csvStringifyLineWith(fields, csvDefaultOptions())
fn csvStringifyWith(rows: List[List[Str]], opts: CsvOptions) -> Str = joinLines(_csvStringifyRowsAcc(rows, opts, Nil))
fn csvStringify(rows: List[List[Str]]) -> Str = csvStringifyWith(rows, csvDefaultOptions())
```
<!-- AUTO-GEN:END FUNCTIONS -->
