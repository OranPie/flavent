# `consoleIO`

## Overview
(Edit this page freely. The generator only updates the marked API blocks.)

## Import
```flavent
use consoleIO
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn print(s: Str) -> Unit = call _bridge_python.consolePrint(s)
fn println(s: Str) -> Unit = call _bridge_python.consolePrintln(s)
fn printErr(s: Str) -> Unit = call _bridge_python.consolePrintErr(s)
fn printlnErr(s: Str) -> Unit = call _bridge_python.consolePrintlnErr(s)
fn readLine() -> Str = rpc _bridge_python.consoleReadLine()
fn flush() -> Unit = call _bridge_python.consoleFlush()
```
<!-- AUTO-GEN:END FUNCTIONS -->
