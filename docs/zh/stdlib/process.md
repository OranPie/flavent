# `process`

## 概述
带结构化结果/错误的 process API（确定性模拟实现）。

当前行为是运行时局部、可预测的：
- 构建进程规格（`program`、`args`、`cwd`、`env`）。
- 通过 `spawn/start/wait` 工作流运行。
- 返回结构化 `ProcessError` 与 `ProcessResult`。

## 导入
```flavent
use process
```

## 类型
<!-- AUTO-GEN:START TYPES -->
```flavent
type ProcessError = { code: Str, message: Str }
type ProcessSpec = {
type ProcessHandle = { id: Int, spec: ProcessSpec, started: Bool }
type ProcessStatus = { exitCode: Int, success: Bool }
type ProcessOutput = { stdout: Str, stderr: Str }
type ProcessResult = { status: ProcessStatus, output: ProcessOutput }
type ProcessWait = { handle: ProcessHandle, result: ProcessResult }
```
<!-- AUTO-GEN:END TYPES -->

## 函数
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn processSpec(program: Str, args: List[Str]) -> ProcessSpec = {
fn processWithCwd(spec: ProcessSpec, cwd: Str) -> ProcessSpec = {
fn processWithEnv(spec: ProcessSpec, key: Str, value: Str) -> ProcessSpec = {
fn processWithExitCode(spec: ProcessSpec, code: Int) -> ProcessSpec = {
fn processWithStdout(spec: ProcessSpec, out: Str) -> ProcessSpec = {
fn processWithStderr(spec: ProcessSpec, err: Str) -> ProcessSpec = {
fn processValidate(spec: ProcessSpec) -> Result[Unit, ProcessError] = do:
fn processSpawn(spec: ProcessSpec) -> Result[ProcessHandle, ProcessError] = do:
fn processStart(handle: ProcessHandle) -> Result[ProcessHandle, ProcessError] = do:
fn processWait(handle: ProcessHandle) -> Result[ProcessWait, ProcessError] = do:
fn processRun(spec: ProcessSpec) -> Result[ProcessResult, ProcessError] = do:
fn processExitCode(result: ProcessResult) -> Int = result.status.exitCode
fn processSucceeded(result: ProcessResult) -> Bool = result.status.success
fn processFailed(result: ProcessResult) -> Bool = not result.status.success
fn processStdout(result: ProcessResult) -> Str = result.output.stdout
fn processStderr(result: ProcessResult) -> Str = result.output.stderr
```
<!-- AUTO-GEN:END FUNCTIONS -->
