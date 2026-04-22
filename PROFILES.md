# Hermes Profiles

## 已迁移的 OpenClaw agent 能力

### main

- 定位：原 OpenClaw 主助手人格
- 工作目录：`/home/kent/.openclaw/workspace`
- 启动命令：`main` 或 `main chat`
- 适合问题：通用协作、日常助理、跨项目背景工作、心跳/记忆维护

### consulting

- 定位：企业信息化与数字化顾问
- 工作目录：`/home/kent/repos/main-agent`
- 启动命令：`consulting` 或 `consulting chat`
- 适合问题：流程诊断、系统边界、主数据、集成、路线图、实施风险

### finance

- 定位：A 股交易情报与风控助手
- 工作目录：`/home/kent/repos/finance/stock-agent`
- 启动命令：`finance` 或 `finance chat`
- 适合问题：持仓、观察池、盘前盘中盘后、事件驱动、风控、复盘

### study

- 定位：合规学习助手
- 工作目录：`/home/kent/repos/finance/study-agent`
- 启动命令：`study` 或 `study chat`
- 适合问题：课程进度导出、今日学习清单、学习计划、考试准备

### docs

- 定位：文档处理助手
- 工作目录：`/home/kent/.openclaw/workspace/docs-agent`
- 启动命令：`docs` 或 `docs chat`
- 适合问题：Word / Excel / PPT / PDF 处理、内容提取、文档整理、飞书文档相关任务

## 使用建议

- 想保留通用助手入口：直接用默认 `hermes`
- 想恢复原 OpenClaw 主助手：切到 `main`
- 做企业数字化咨询：切到 `consulting`
- 做 A 股交易分析与提醒：切到 `finance`
- 做学习计划和课程进度管理：切到 `study`
- 做文档处理与整理：切到 `docs`

## 说明

- 所有专用 profile 都复用了现有 Hermes 配置和密钥。
- 所有专用 profile 都额外挂载了 `/home/kent/.agents/skills` 和 `/home/kent/.hermes/skills/openclaw-imports`。
- 专用启动脚本会先切到对应工作目录，确保 `AGENTS.md` 和项目上下文在会话开始时就生效。
- `study` 默认走合规版学习助手，不把旧的代看脚本作为默认入口。
- `docs` 已适配本地文档处理场景；飞书直连能力是否可直接执行，取决于当前 Hermes 的飞书配置是否完善。
