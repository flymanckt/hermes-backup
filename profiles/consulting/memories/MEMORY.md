按主题拆分，详见 `memory/` 目录：
§
---
§
当前应长期保留的重点 > 用户与风格: 用户是 Kent，偏好全程中文、先结论后细节、少客套、实用优先。
§
当前应长期保留的重点 > 用户与风格: 助手身份是“爱马仕”，风格应冷静、直接、逻辑优先。
§
当前应长期保留的重点 > 系统与自动化: **Agent 架构**：main 为主对话入口，consulting 为企业信息化顾问，finance 为 A 股推送，docs 为飞书文档专家；权限按最小化配置。
§
当前应长期保留的重点 > 系统与自动化: **Session 隔离策略**：`session.dmScope = per-account-channel-peer`，按账号+渠道+用户隔离 DM，会话不再串窗。
§
当前应长期保留的重点 > 系统与自动化: **Feishu 路由**：main 与 consulting 为主要入口，finance 保留推送但无入站 binding。
§
当前应长期保留的重点 > 系统与自动化: **Dream cron 架构**（2026-04-10）：`dream-micro-sync`、`dream-daily-wrapup`、`dream-weekly-compound` 已切到独立 `agent:main:cron:dream-*` 会话执行，避免主聊天会话超时。
§
当前应长期保留的重点 > 系统与自动化: **Windows 自动化边界**：当前 WSL 无 GUI，桌面自动化应转到 Windows 宿主机 node 执行，不继续依赖 WSL 拉起桌面程序。
§
当前应长期保留的重点 > 系统与自动化: **Backup cron**：`flymanckt/openclaw-backup` 每日 02:00 UTC 运行正常。
§
当前应长期保留的重点 > 排查备忘: **main 响应慢时**：优先查 Node 子进程 CPU 100%、memory 插件可用性、Gateway 与 service 状态一致性。
§
当前应长期保留的重点 > 投资相关: 当前持仓与跟踪重点见 `memory/system-config.md`。
§
当前应长期保留的重点 > 投资相关: 嘉美包装（002969）止损位 23.5 元。
§
当前应长期保留的重点 > 投资相关: ---
§
不应长期保留的内容处理原则: 一次性任务、临时故障、短期项目过程，留在 `memory/YYYY-MM-DD.md`。
§
不应长期保留的内容处理原则: 稳定规则进入 `AGENTS.md` 或对应 skill。
§
不应长期保留的内容处理原则: 环境事实进入 `TOOLS.md`。
§
不应长期保留的内容处理原则: --- *由爱马仕维护 | 2026-04-10 WEEKLY_COMPOUND*
§
2026-03-22 记忆 > MICRO_SYNC @ 22:00 > Scope: agent:tech: 原因：需要更系统的记忆管理
§
2026-03-22 记忆 > MICRO_SYNC @ 22:00 > Scope: agent:tech: 发现：已有 three-layer-memory 技能包，包含 micro-sync/daily-wrapup/weekly-compound 脚本
§
2026-03-22 记忆 > MICRO_SYNC @ 22:00 > Scope: agent:tech: 结论：安装并配置 cron 作业（10/13/16/19/22 点 micro-sync，01:00 daily-wrapup，03:00 weekly）
§
2026-03-22 记忆 > MICRO_SYNC @ 22:00 > Scope: agent:tech: 涉及文件：MEMORY.md 初始化，cron 配置
§
2026-03-22 记忆 > MICRO_SYNC @ 22:00 > Scope: agent:tech: **self-improving-agent 技能安装**
§
2026-03-22 记忆 > MICRO_SYNC @ 22:00 > Scope: agent:tech: 原因：用户要求安装 clawhub 技能
§
2026-03-22 记忆 > MICRO_SYNC @ 22:00 > Scope: agent:tech: 发现：URL 中 slug 有误（pskoett/self-improving-agent → self-improving-agent）
§
2026-03-22 记忆 > MICRO_SYNC @ 22:00 > Scope: agent:tech: 结论：成功安装到 ~/.openclaw/workspace/skills/self-improving-agent