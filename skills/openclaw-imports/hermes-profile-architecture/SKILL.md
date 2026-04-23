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

## Skills 共享（当前实际状态）
当前采用 **中心共享 + 各 profile 本地挂载** 的结构：

- 中心共享库：`/home/kent/.hermes/skills/`
- 各 profile 入口：`/home/kent/.hermes/profiles/<profile>/skills/`
- 共享类目在各 profile 中保留真实分类目录，分类下的具体 skill 目录以**符号链接**指向中心共享库
- profile 专属类目（如 `consulting`、`finance`、`a-share-stock-data-tencent`）继续保留在各自 profile 本地

这样可以兼顾两点：
1. 新增到中心共享库的通用 skill 可同步分发到各 profile
2. 不破坏按分类扫描 skill 的兼容性

自动同步由脚本和 systemd user timer 维护：
- 脚本：`/home/kent/.hermes/scripts/sync_shared_skills.py`
- 定时器：`hermes-shared-skills-sync.timer`（每 2 分钟同步一次）

## 主目录 vs OpenClaw 目录（重要区分）
- `/home/kent/.hermes/` — Hermes agent 运行时目录（我的根目录）
- `/home/kent/.openclaw/` — OpenClaw 框架目录
- `/home/kent/.openclaw/workspace/` — OpenClaw workspace 模板（不是我的主目录）

## 重启后注意
修改 `plugins/` 下的 `.ts` 文件后需清理 `/tmp/jiti/` 缓存，再重启 OpenClaw Gateway。
