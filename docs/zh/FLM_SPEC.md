# FLM（Flavent Manifest）规范（中文）

本文档描述 Flavent 的工程/包管理系统：
- `flm.json`（清单，人工维护）
- `flm.lock.json`（锁文件，机器生成）
- `vendor/`（依赖源码入口）
- `.flavent/`（缓存目录，git 缓存等）

设计目标：
- **可复现构建**：lock pin 到具体 commit。
- **可扩展**：保留未知字段，`extensions` 命名空间化。
- **安全边界**：Python 只能通过严格 adapter 接口（v2：子进程隔离），不能直接 import。

---

## 1. 文件与目录

- `flm.json`：工程清单
- `flm.lock.json`：锁文件
- `vendor/`：安装后的依赖入口
- `.flavent/`：缓存目录（当前实现包含 `.flavent/git/<name>`）

---

## 2. flm.json（清单）

### 2.1 结构（v1）

```json
{
  "flmVersion": 1,
  "package": {
    "name": "myproj",
    "version": "0.1.0",
    "entry": "src/main.flv"
  },
  "toolchain": {
    "flavent": ">=0.1.0"
  },
  "dependencies": {
    "mylib": { "path": "../mylib" },
    "netlib": { "git": "ssh://git@host/org/netlib.git", "rev": "<commit-or-tag>" }
  },
  "devDependencies": {},
  "pythonAdapters": [],
  "extensions": {}
}
```

### 2.2 依赖说明

- Path 依赖：`{ "path": "../somewhere" }`
- Git 依赖：`{ "git": "ssh://...", "rev": "<commit/tag>" }`

---

## 3. flm.lock.json（锁文件）

当前实现：
- git 依赖会 clone 到 `.flavent/git/<name>`
- `vendor/<name>` 是指向缓存 repo 的 **软链接**
- lockfile 中 `rev` 会 pin 为 `git rev-parse HEAD` 的 commit hash

---

## 4. 模块加载规则（resolver）

当解析 `use a.b` 时，会按顺序搜索：
1. `module_roots`（通常是项目 `src/`、`vendor/`、项目根目录）
2. `stdlib/`

搜索方式：
- `<root>/a/b.flv`
- `<root>/a/b/__init__.flv`

---

## 5. CLI（v1）

- `flavent pkg init [path]`：初始化工程（生成 `flm.json`、`src/`、`tests_flv/`、`vendor/`）
- `flavent pkg add <name> (--path <p> | --git <url> [--rev <rev>]) [--dev]`
- `flavent pkg list`
- `flavent pkg install`
  - 安装依赖
  - 写入 `flm.lock.json`
  - 生成 python adapter wrappers（见下文）
- `flavent pkg export <out>`

---

## 6. Python Adapters（v2：子进程隔离）

### 6.1 清单声明

```json
{
  "pythonAdapters": [
    {
      "name": "demo",
      "source": { "path": "vendor/py_demo" },
      "capabilities": ["pure_math"],
      "allow": ["echo"]
    }
  ]
}
```

### 6.2 adapter 包结构

```
<adapter-root>/
  flavent_adapter.py
```

### 6.3 adapter 必须提供的接口

`flavent_adapter.py` 必须定义：
- `PLUGIN_ID: str`
- `API_VERSION: int`
- `CAPABILITIES: list[str]`
- `EXPORTS: dict[...]`
- `dispatch(fn: str, payload: bytes) -> bytes`

### 6.4 子进程通信协议（newline JSON）

请求：
```json
{"id": 1, "method": "echo", "payload_b64": "..."}
```

响应：
```json
{"id": 1, "ok": true, "payload_b64": "..."}
```

错误：
```json
{"id": 1, "ok": false, "error": "message"}
```

Meta 查询：
- `method = "__meta__"` 会返回 JSON bytes：
  - `plugin_id`, `api_version`, `capabilities`, `exports`

### 6.5 安全校验

运行时会校验：
- `capabilities` 必须是 adapter `CAPABILITIES` 的子集
- `allow` 必须是 adapter `EXPORTS` 的子集

---

## 7. 自动生成 wrapper：pyadapters

执行 `flavent pkg install` 后会生成：
- `vendor/pyadapters/<adapter>.flv`
- `vendor/pyadapters/__init__.flv`

用法：

```flavent
use pyadapters.demo
let r = rpc demo.echo(b"hi")
```
