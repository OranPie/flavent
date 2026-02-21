# Flavent 文档中心（简体中文 / zh-CN）

本目录是 Flavent 的简体中文文档入口。

如果你更习惯使用 `cn` 路径，也可以从 `docs/cn/README.md` 进入（该入口指向本目录）。

## 语言切换

- English docs hub: [`docs/en/README.md`](../en/README.md)
- 文档总入口：[`docs/README.md`](../README.md)

## 核心规范

- [语言规范与标准库文档](./DOCS.md)
- [FLM（包管理与插件）规范](./FLM_SPEC.md)
- [编译器与执行流程](./COMPILER.md)

## 指南与参考

- [Mixin 使用指南](./mixin_guide.md)
- [标准库（逐模块页面）](./stdlib/index.md)
- [发布说明](./release_notes.md)
- [告警目录](./warning_catalog.md)

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
