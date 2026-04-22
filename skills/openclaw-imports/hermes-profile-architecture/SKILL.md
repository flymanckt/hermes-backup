---
name: hermes-profile-architecture
description: Hermes agent profile 架构与目录结构
---
# Hermes Profile Architecture

## 身份锚点
- 名字：**爱马仕**
- 主目录：`/home/kent/.hermes/`
- 底层框架：OpenClaw（框架本身不是身份的一部分）
- 飞书入口：ou_0c9c77215f618dfa35fdbcace870f6ec

## Profile 架构
每个 profile 是平级 agent，不是 hermes 的子集：

| Profile | 用途 | Workspace 路径 |
|---------|------|---------------|
| hermes | 主助手（爱马仕） | `/home/kent/.hermes/profiles/hermes/workspace/` |
| consulting | 企业信息化顾问 | `/home/kent/.hermes/profiles/consulting/workspace/` |
| finance | A股交易情报 | `/home/kent/.hermes/profiles/finance/workspace/` |
| study | 合规学习助手 | `/home/kent/.hermes/profiles/study/workspace/` |
| docs | 文档处理 | `/home/kent/.hermes/profiles/docs/workspace/` |

## Skills 共享
所有 profile 的 skills 都是符号链接，指向 `/home/kent/.hermes/skills/`，共 26 个分类。

## 主目录 vs OpenClaw 目录（重要区分）
- `/home/kent/.hermes/` — Hermes agent 运行时目录（我的根目录）
- `/home/kent/.openclaw/` — OpenClaw 框架目录
- `/home/kent/.openclaw/workspace/` — OpenClaw workspace 模板（不是我的主目录）

## 重启后注意
修改 `plugins/` 下的 `.ts` 文件后需清理 `/tmp/jiti/` 缓存，再重启 OpenClaw Gateway。
