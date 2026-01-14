# Flavent（中文文档）

本目录提供 Flavent 的中文文档翻译版本。

## 文档入口

- [语言规范与标准库文档](./DOCS.md)
- [FLM（包管理与插件）规范](./FLM_SPEC.md)
- [编译器与执行流程](./COMPILER.md)
- [标准库（逐模块页面）](./stdlib/index.md)

## 快速开始

1) 初始化工程：

```bash
flavent pkg init
```

2) 安装依赖：

```bash
flavent pkg add mylib --path ../mylib
flavent pkg install
```

3) 运行/检查：

```bash
flavent check src/main.flv
```
