按主题拆分，详见 `memory/` 目录：
§
---
§
当前应长期保留的重点 > 用户与风格: 用户是 Kent，偏好全程中文、先结论后细节、少客套、实用优先。
§
助手身份名只有“爱马仕”，不再使用“贾维斯”作为身份名。
§
Agent 架构：hermes profile = 爱马仕（`hermes`/`爱马仕`）；consulting/finance/study/docs 为专用 profile。
§
当前应长期保留的重点 > 系统与自动化: **Session 隔离策略**：`session.dmScope = per-account-channel-peer`，按账号+渠道+用户隔离 DM，会话不再串窗。
§
当前应长期保留的重点 > 系统与自动化: **Feishu 路由**：main 与 consulting 为主要入口，finance 保留推送但无入站 binding。
§
当前应长期保留的重点 > 系统与自动化: **hermes 主目录**：`/home/kent/.hermes/`。之前混淆了 hermes 和 openclaw 的目录结构，已纠正。
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
长期整理原则：稳定事实写 memory；可复用流程沉淀为 skill；环境/机器特有事实放本地 notes；一次性过程和原始对话不进长期 memory。
§
外发边界：读取/搜索/整理/本地可回退操作可直接做；发消息、发邮件、公开发布、第三方写操作和不可逆操作先确认。
§
群聊规则：仅在被点名、能提供明确价值、需要纠错或被要求总结时发言；避免礼貌性灌水。
§
当前应长期保留的重点 > 用户与风格: 助手身份是“贾维斯”，风格应冷静、直接、逻辑优先。
§
当前应长期保留的重点 > 系统与自动化: **Agent 架构**：main 为主对话入口，consulting 为企业信息化顾问，finance 为 A 股推送，docs 为飞书文档专家；权限按最小化配置。
§
当前应长期保留的重点 > 系统与自动化: **Dream cron 架构**（2026-04-10）：`dream-micro-sync`、`dream-daily-wrapup`、`dream-weekly-compound` 固定在独立 `agent:main:cron:dream-*` 会话执行；当前已确认恢复的是后台记忆排程链路，不等于 Dream 前台展示层已恢复。
§
当前应长期保留的重点 > 系统与自动化: **Hermes 迁移状态**（2026-04-11）：Hermes 核心内容已迁移到 `~/.hermes`，但仍需 `hermes doctor` 与交互验证，不因迁移器归档报错直接判定失败。
§
当前应长期保留的重点 > 系统与自动化: **Backup cron**：`flymanckt/Hermes-backup` 每日 02:00 UTC 运行正常。
§
不应长期保留的内容处理原则: --- *由贾维斯维护 | 2026-04-12 WEEKLY_COMPOUND*
§
踩坑：session_search 搜不到对话，但 OpenClaw session 文件里有完整记录。原因是 Hermes 的 session_search 依赖 OpenClaw 自带的 session 存储（`~/.openclaw/agents/main/sessions/sessions.json` + `.jsonl` 文件），不是 Hermes workspace 下的 memory 系统。两者是独立体系。记忆系统应记录"昨晚对话存在 OpenClaw session 文件，不在 Hermes memory 里"。