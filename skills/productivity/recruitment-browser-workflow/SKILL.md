---
name: recruitment-browser-workflow
description: 使用 Hermes 浏览器工具在 51job / 猎聘 / BOSS 上做半自动批量投递，包括搜索页抓取、入队、单岗位准备、上传简历、提交确认与结果记录。
version: 1.0.0
author: 爱马仕
---

# Recruitment Browser Workflow

适用场景：
- 用户要在前程无忧、猎聘、BOSS 这类网站批量投简历
- 需要半自动而不是纯手工点点点
- 希望保留最终提交前确认，不做盲投

## 已有能力

依赖的底层/高层工具：
- `browser_navigate`
- `browser_snapshot`
- `browser_console`
- `browser_upload`
- `browser_click`
- `recruitment_workflow`

`recruitment_workflow` 当前支持：
- `site_profile`
- `prepare`
- `confirm_submit`
- `record_result`
- `list_results`
- `create_batch_plan`
- `enqueue_jobs`
- `next_job`
- `mark_job`
- `batch_status`
- `extract_search_results`
- `parse_search_page`
- `get_search_extract_script`
- `run_batch_once`

## 推荐工作流

### 1. 创建批量计划
先建一个 batch：

```json
{
  "action": "create_batch_plan",
  "site": "liepin",
  "resume_path": "/mnt/c/Users/Kent/Documents/resume.pdf",
  "keywords": ["IT经理", "信息化负责人"],
  "city": "深圳",
  "salary_min": 25000,
  "salary_max": 40000
}
```

输出重点：
- `batch_id`
- `search_url`

### 2. 获取站点专用抓取脚本

```json
{
  "action": "get_search_extract_script",
  "site": "liepin"
}
```

返回：
- `script`
- `usage_steps`

### 3. 在搜索结果页抓岗位卡片
先打开搜索结果页：
- `browser_navigate(search_url)`

然后把 `script` 喂给：
- `browser_console(expression=<script>)`

注意：`browser_console` 一般会返回：
- `{"success": true, "result": [...]}`

### 4. 解析并自动入队
把上一步的 `result` 作为 `page_data`：

```json
{
  "action": "parse_search_page",
  "batch_id": "batch_xxx",
  "page_data": [...],
  "auto_enqueue": true
}
```

### 5. 取下一个待投岗位

```json
{
  "action": "next_job",
  "batch_id": "batch_xxx"
}
```

### 6. 半自动 runner
如果想省掉“手工抓搜索页 -> 手工 next_job”的步骤，用：

```json
{
  "action": "run_batch_once",
  "batch_id": "batch_xxx",
  "task_id": "runner-task"
}
```

它会自动：
1. 检查 batch 里是否已有 pending 岗位
2. 如果没有，就：
   - 打开搜索页
   - 取站点脚本
   - 执行 `browser_console(expression=script)`
   - 调 `parse_search_page(auto_enqueue=true)`
3. 取 `next_job`
4. 打开职位详情页
5. 跑 `prepare`

返回里会给你：
- `queue_refreshed`
- `extracted_count`
- `next_job`
- `prepared`
- `runner_steps`

## 单岗位投递闭环

当 `run_batch_once` 或 `next_job` 已经把职位页打开后：

### Step A: 查看页面元素
- `browser_snapshot()`

### Step B: 上传简历
找到文件输入框 ref 后：

```json
{
  "ref": "@e12",
  "paths": ["/mnt/c/Users/Kent/Documents/resume.pdf"]
}
```

工具：`browser_upload`

### Step C: 投递前准备校验

```json
{
  "action": "prepare",
  "site": "liepin",
  "resume_path": "/mnt/c/Users/Kent/Documents/resume.pdf",
  "job_url": "https://www.liepin.com/job/xxx.shtml",
  "company": "某公司",
  "title": "IT经理"
}
```

### Step D: 最终提交前确认

```json
{
  "action": "confirm_submit",
  "site": "liepin",
  "company": "某公司",
  "title": "IT经理",
  "confirm": true
}
```

没传 `confirm=true` 时，应该拒绝最终提交。

### Step E: 点击最终按钮
确认通过后，再用：
- `browser_click(ref)`

### Step F: 记录结果
提交后立刻记日志：

```json
{
  "action": "mark_job",
  "batch_id": "batch_xxx",
  "job_url": "https://www.liepin.com/job/xxx.shtml",
  "status": "submitted",
  "notes": "已确认后提交"
}
```

## 日志与状态文件

日志：
- `~/.hermes/recruitment/application_log.jsonl`

批次文件：
- `~/.hermes/recruitment/batches/<batch_id>.json`

## 推荐执行策略

### 策略一：用户提供具体职位 URL（最可靠，绕过登录/captcha）
当用户已有目标公司/职位时：
1. 用户在 Windows Chrome 搜索并筛选后，把具体职位 URL 发给 Agent
2. Agent 用 `next_job` / `run_batch_once` 逐个投递
3. 不依赖自动化浏览器登录态

### 策略二：用户辅助登录自动化浏览器（需人工介入）
当用户没有具体目标，想先搜索时：
1. Agent 发送登录 URL，用户在**自动化浏览器**里完成登录（不是自己 Windows 浏览器）
2. 用户确认登录完成，Agent 继续执行搜索和投递
3. 注意：自动化浏览器会被 captcha 拦截，需要用户手动通过验证

### 保守模式（推荐）
- 自动：搜索页抓取、入队
- 人工：筛选目标城市岗位、打开职位页检查、最终确认、提交

### 猎聘最优工作流（城市精确过滤版）— 2026-04-22 更新
由于猎聘搜索结果城市过滤不准、IP 验证在搜索页触发，且 WSL 自动化浏览器无法继承用户登录态，最优方式是：

1. **用户在自己浏览器（Windows Chrome）手动搜索**并用 UI 筛选目标城市/薪资/关键词
2. 把**具体职位 URL 列表**（不是搜索页 URL，是每个职位的详情页 URL）发给 Agent，如 `https://www.liepin.com/job/1981690407.shtml`
3. Agent 直接打开各职位详情页并投递（不走搜索页，不过 IP 验证）
4. 入队后逐个打开投递

> ⚠️ **登录注意事项**：WSL 自动化浏览器和 Windows 浏览器是完全隔离的 session。"帮我登录" 意味着你要在**自动化浏览器打开的页面**里登录，不是自己打开浏览器登录后告诉我完成。

## 平台反爬强度与投递可行性（2026-04-20 实测）

| 平台 | 拦截类型 | 拦截频率 | 当前自动化可行性 |
|------|----------|----------|----------------|
| 51job | 滑块验证码 | 每个职位详情页必触发 | ❌ 硬性阻塞 |
| 猎聘 | IP验证（搜索页触发） | 仅搜索页触发，详情页正常 | ⚠️ 搜索走用户浏览器或用备选方案 |
| BOSS直聘 | IP级别安全验证 | 搜索页即触发 | ❌ 数据中心IP必拦截 |

### 🚫 51job 滑块验证码 — 硬性阻塞
**现象**：前程无忧每个职位详情页都会触发滑块验证，当前浏览器工具无法完成拖拽操作。
**验证**：2026-04-20 实测两个不同职位页，均触发验证。
**对策**：立即切换到 BOSS 或猎聘，不要继续尝试 51job。

### 🚫 猎聘安全验证 — 频繁触发（架构层面说明）
**现象**：连续打开 3-4 个职位页后，猎聘触发"行为异常"安全验证，出现"点击验证"按钮。
**根因**：猎聘对自动化浏览器有强 IP + 行为指纹检测。

**🚨 核心架构限制 — WSL 自动化浏览器与 Windows 浏览器完全隔离（2026-04-22 确认）**

WSL 内的自动化浏览器（CDP session）和用户 Windows 浏览器是**完全隔离的两个独立 session**，cookie 不互通。

**实测验证**：
- 用户在 Windows Chrome 完成猎聘登录 → 登录成功确认
- WSL 自动化浏览器访问猎聘 → `document.cookie` 仍为空，`blocked: false`
- 结论：用户在 Windows 浏览器完成的登录，自动化浏览器**完全不可见**

**影响**：
- 所有需要登录的招聘平台（猎聘/BOSS/51job），自动化浏览器都无法继承用户的登录态
- 自动化浏览器必须自己完成登录（但往往被 captcha 拦截）
- 这不是临时问题，是架构级限制

**应对策略（强制排序）**：
1. **用户提供具体职位 URL**（最可靠）→ Agent 直接打开详情页投递，绕过登录/captcha
2. **用户辅助登录自动化浏览器**：用户在自动化浏览器里完成登录（不能在自己 Windows 浏览器），登录 URL 发送后等用户确认完成，再继续
3. **住宅代理**：解决 IP captcha 问题，但需要额外配置

> 注意：即使 `browser.defaultProfile` 改为 `user`，gateway 重启后会因找不到 `/tmp/chrome-uds` socket 而失败（ENONENT）。chrome-mcp 桥接需要额外配置才能跨 WSL 工作，当前不可用。

**已确认的平台 captcha 行为（2026-04-22 更新）**：

| 平台 | 搜索页 | 详情页直接打开 |
|------|--------|--------------|
| BOSS直聘 | ❌ 必触发安全验证 | 未知（未单独测试） |
| 51job | ❌ 触发滑块验证 | 未测试 |
| 猎聘 | ⚠️ 搜索页触发，详情页正常 | ✅ 直接打开职位 URL 通常正常 |

**重要架构发现（2026-04-21）**：
- OpenClaw `openclaw` profile：走 CDP (Chromium DevTools Protocol)，独立 browser session，IP 来自 WSL 出口（Verizon Business 数据中心 IP），**必定被拦截**
- OpenClaw `user` profile：走 chrome-mcp 桥接 Windows Chrome，有用户登录态，但需要 Windows Chrome 开启远程调试 socket
- **关键限制**：两套 browser session 完全隔离——用户在 Windows Chrome 完成的验证，CDP session 不会继承
- Hermes browser 工具目前绑定的是 `openclaw` profile，不是 `user` profile
- 切换 `browser.defaultProfile` 到 `user` 后仍需要 Windows Chrome 开启远程调试（`/tmp/chrome-uds` socket 在 WSL 里不存在）

**当前可行方案**：
1. **用户辅助验证**：用户在 Windows Chrome 完成验证后，快速在 CDP 浏览器里操作（但验证有效期短，且每次搜索都会重新触发）
2. **URL 提取方案**：用户在自己浏览器搜好并筛选后，把搜索结果页 URL 发给 Agent，Agent 用 `web_extract` 抓取岗位列表，再在 CDP 浏览器里逐个打开详情页投递（绕过搜索页的 IP 验证）
3. **住宅代理**：购买中国住宅代理解决 IP 问题（最可靠但需付费）

**注意**：即使 `browser.defaultProfile` 改为 `user`，gateway 重启后会因找不到 `/tmp/chrome-uds` socket 而失败（ENONENT）。chrome-mcp 桥接需要额外的配置才能跨 WSL 工作。
**现象**（2026-04-21 订正）：猎聘的 IP 验证拦截**在搜索结果页触发**，不在职位详情页。直接打开一个具体职位 URL 不会触发，连续打开 3-4 个职位也**不会**触发（与之前记录不符）。触发的是搜索 URL 中的 `safe.liepin.com` 重定向。
**实测**：用 WSL 出口 IP（Verizon Business，AS701 数据中心）直接打开 `liepin.com/job/xxx.shtml` → 正常加载无验证；打开搜索结果 URL → 触发"行为异常"验证页。
**对策**：
1. **最优解**：用户把猎聘上筛选好的搜索结果页 URL 发给 Agent，Agent 绕过搜索页直接用该 URL 作为入口抓取（但需验证是否同被拦）
2. **备选**：用户提供具体目标公司名称/职位，Agent 用 web_search 找对应职位 URL，再直接打开详情页投递
3. **换 Windows 浏览器**：用户在 Windows Chrome 登录后，Windows 浏览器可正常使用，Agent 通过 Windows 浏览器接管

### 🚫 BOSS直聘 IP级别验证 — 数据中心IP必拦
**现象**：搜索页即触发"当前 IP 地址可能存在异常访问行为"，显示"点击按钮进行验证"。
**根因**：WSL 出口 IP 被 BOSS 识别为非住宅 IP。
**验证**：在 Windows Chrome 登录后正常，WSL 浏览器被拦。
**对策**：Agent 通过 Windows 浏览器接管；或用户提供具体目标职位 URL 列表。

### 🚫 猎聘搜索结果城市过滤不准确
**现象**：`create_batch_plan` 时传入 `city=深圳`，但搜索结果混杂大量非深圳岗位。CSS 选择器也无法提取公司名和薪资。
**对策**：使用下方"城市精确过滤版工作流"。

## 风险点
- 登录态失效
- **IP 被平台识别为数据中心 IP**：WSL 出口 IP 可能被三家平台识别，搜索页会被拦，但直接打开职位详情页（不走搜索）有时可正常访问；如遇拦截，换用 Windows 浏览器或用户提供具体职位 URL 列表
- 滑块验证码（51job 硬阻塞，当前无解）
- 页面 DOM 改版导致脚本失效
- 文件上传控件不是标准 file input
- 最终按钮文案变化

## 排障建议

### 排障：所有平台均触发验证码
**若打开任意招聘页面立即显示验证码页面，先检查 IP 类型**：
1. 先用 `browser_navigate` 打开该招聘平台首页
2. 观察是否直接跳转到安全验证页
3. 若首页即拦 → 数据中心 IP，自动化受限
4. 若详情页能打开但搜索页拦 → 说明 IP 仅影响搜索，详情页可正常投递

**可行绕过方案（按推荐顺序）**：
1. **用户提供搜索页 URL**：用户在自己浏览器（正常 IP）上做好城市/薪资筛选，把结果页 URL 发给 Agent
2. **用户提供具体公司/职位名**：Agent 用 web_search 找目标职位 URL 列表，直接打开详情页投递（不走搜索页）
3. **换用户 Windows 浏览器**：用户在 Windows Chrome 登录账号，Agent 通过 Windows 浏览器接管操作
4. **住宅代理**：购买 Bright Data / Oxylabs / SmartProxy 住宅代理，在 `openclaw.json` 中配置 `proxy` 字段

### 1. 搜索页抓不到岗位
- 先 `browser_snapshot(full=true)` 看页面结构
- 再 `browser_console(expression=<script>)` 看返回内容
- 如 DOM 改版，更新 `get_search_extract_script` 对应站点模板

### 2. 解析后 count=0
- 检查 `browser_console` 返回的是不是 `{"success": true, "result": [...]}` 
- 确认 `page_data` 真的是数组
- 确认每一项至少有 `job_url` / `url` / `href`

### 3. 上传失败
- 先确认文件路径存在
- 再确认文件输入框是标准上传控件
- 必要时用 `browser_console(expression=...)` 看 `input[type=file]`

### 4. 页面打开了但没法提交
- 用 `browser_snapshot()` 找最终按钮 ref
- 再用 `confirm_submit(confirm=true)` 放行
- 最后再 `browser_click()`
- 触发时需要人工操作"点击验证"按钮通过
- 建议改用"城市精确过滤版工作流"（见上方推荐执行策略），减少无效职位访问

## 触发词建议
以下用户意图可直接联想到本技能：
- “批量投简历”
- “自动投递招聘网站”
- “前程无忧/猎聘/BOSS 自动投”
- “批量找岗位并投递”

## 当前边界
本技能是“半自动批量投递工作流”，不是完全无人值守海投器。
默认保留最终提交确认，不要直接无脑代投。
