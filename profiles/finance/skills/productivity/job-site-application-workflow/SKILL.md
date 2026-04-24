---
name: job-site-application-workflow
description: 在 Hermes 中执行前程无忧 / 猎聘 / BOSS 这类招聘站点的半自动批量投递工作流。适用于需要浏览器上传简历、批量搜岗、结果页抽取、入队、逐条投递、提交前确认与日志留痕的场景。
version: 1.0.0
---

# 招聘网站半自动投递工作流

## 适用场景
- 用户要在 51job / 猎聘 / BOSS 上投简历
- 需要浏览器上传本地简历文件
- 需要批量管理多个岗位，而不是一次只投一个
- 需要“提交前确认”，不希望全自动盲投

## 关键结论
这类任务不要直接从浏览器 click/type 开始硬做。
正确分层是：
1. `recruitment_workflow` 负责站点规则、批量计划、候选岗位解析、入队、结果记录
2. `browser_*` 负责真实页面交互
3. 最终提交前必须经过 `confirm_submit`
4. 简历上传统一用 `browser_upload`

## 当前可用能力
### 浏览器层
- `browser_upload(ref, paths)`
  - 用于上传 PDF / Word 简历到 file input
  - 会检查文件存在性
  - 会阻止敏感文件（如 `.env`、密钥、凭据类文件）

### 工作流层：`recruitment_workflow`
支持动作：
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

## 推荐执行顺序
### 单岗位投递
1. `recruitment_workflow(action="prepare", ...)`
2. `browser_navigate(job_url)`
3. `browser_snapshot()`
4. 如页面有附件上传框：`browser_upload(ref, paths=[resume_path])`
5. 补填表单：`browser_type(...)`
6. 提交前：`recruitment_workflow(action="confirm_submit", confirm=true, ...)`
7. 最后再 `browser_click(...)`
8. 完成后：`recruitment_workflow(action="record_result", status="submitted", ...)`

### 批量投递
1. `create_batch_plan`
2. `browser_navigate(search_url)`
3. `get_search_extract_script(site=...)`
4. `browser_console(expression=<返回脚本>)` 抓结果页原始岗位卡片
5. `parse_search_page(batch_id=..., page_data=..., auto_enqueue=true)`
6. 可选先跑一轮自动 runner：
   - `run_batch_once(batch_id=..., task_id=...)`
   - 当队列为空时，它会自动打开搜索页、执行站点脚本、解析并入队，然后打开下一条职位页并返回 `prepared`
7. 手动/半自动继续：
   - `next_job`
   - 进入岗位页投递
   - `mark_job(status=...)`
8. 用 `batch_status` 看整批进度

## 三站结果页抓取方式
### 1. 先取站点专用脚本
示例：
```json
{
  "action": "get_search_extract_script",
  "site": "liepin"
}
```

### 2. 在当前搜索结果页执行
把返回的 `script` 直接喂给：
```json
{
  "expression": "...script contents..."
}
```
工具：`browser_console`

### 3. 解析并入队
```json
{
  "action": "parse_search_page",
  "batch_id": "batch_xxx",
  "page_data": [...],
  "auto_enqueue": true
}
```

## 批量计划建议参数
### `create_batch_plan`
建议至少提供：
- `site`
- `resume_path`
- `keywords`

可选：
- `city`
- `salary_min`
- `salary_max`

示例：
```json
{
  "action": "create_batch_plan",
  "site": "boss",
  "resume_path": "/mnt/c/Users/Kent/Documents/resume.pdf",
  "keywords": ["IT经理", "信息化负责人"],
  "city": "深圳",
  "salary_min": 25000,
  "salary_max": 40000
}
```

### 自动跑一轮
`run_batch_once` 会做一轮半自动执行：
1. 如果 batch 里没有 pending 岗位：
   - 打开搜索页
   - 自动获取站点脚本模板
   - 调用 `browser_console(expression=<script>)`
   - 自动执行 `parse_search_page(..., auto_enqueue=true)`
2. 取 `next_job`
3. 打开职位详情页
4. 自动执行 `prepare`
5. 返回下一步建议（通常是上传简历、补填字段、提交前确认）

示例：
```json
{
  "action":"run_batch_once",
  "batch_id":"batch_xxx",
  "task_id":"runner-task"
}
```

返回重点字段：
- `queue_refreshed`
- `extracted_count`
- `next_job`
- `prepared`
- `runner_steps`

### 单条记录
`record_result` 会写入：
- 时间
- 站点
- 公司
- 岗位
- URL
- 状态
- 备注
- 可带 `batch_id`

### 批量记录
`mark_job` 会更新批次中的岗位状态，并同步写入结果日志。

默认日志位置：
- `~/.hermes/recruitment/application_log.jsonl`
- `~/.hermes/recruitment/batches/<batch_id>.json`

## 重大阻塞：IP 反爬问题（2026-04-21 新发现）

**根因**：WSL 出口 IP `120.229.47.219` 属于**中国移动数据中心 IP（AS9808）**，非住宅网络，三家平台均识别并拦截。

| 平台 | 症状 | 是否可绕 |
|------|------|---------|
| 51job | 滑块 CAPTCHA | 不可绕（浏览器无法自动完成拖拽） |
| 猎聘 | 频繁"安全验证"弹窗，需手动点击验证 | 每次打开1-2个职位就触发，无法持续 |
| BOSS直聘 | 搜索页即触发验证 | IP 级别阻断，无法绕过 |

**结论**：无住宅代理（Residential Proxy）的情况下，三家平台均无法持续自动化投递。

**解决方案**：配置住宅代理（SmartProxy/Oxylabs/Bright Data），在浏览器 stealth 配置中添加代理参数。

**简历路径**：`D:\简历\陈凯特的简历.pdf`（Windows）

## 经验与坑
1. 不要让模型直接“看到按钮就点提交”
   - 必须先走 `confirm_submit`
   - 这能显著降低误投风险

2. 先做“结果页抽取 → 入队”，再逐条投递
   - 不要边搜边投，状态难追踪
   - 队列化后可以暂停、恢复、跳过、复盘

3. 招聘站点差异大，先用站点专用脚本模板
   - 不要一开始追求一个万能 DOM 选择器
   - 先针对 51job / 猎聘 / BOSS 提供独立模板更稳

4. `parse_search_page` 和 `extract_search_results` 不同
   - `parse_search_page`：输入是真实页面抓出来的原始 card 数据
   - `extract_search_results`：输入已经是较规范的 candidates

5. 简历上传不要绕过 `browser_upload`
   - 该工具已经做了本地文件存在性与敏感路径校验

6. 51job 搜索页不要只信首屏 DOM
   - `we.51job.com/pc/search?...` 首屏常先渲染 SEO/推荐内容，URL 里的城市/薪资条件不一定立刻反映在可见卡片上
   - 更稳做法：在已打开的 51job 搜索页里，用 `browser_console(expression=...)` 直接 `fetch('https://we.51job.com/api/job/search-pc?...')`
   - 然后从返回 JSON 提取 `jobName / fullCompanyName / jobAreaString / jobHref / providesalaryText`，再按 `area.includes('深圳')` 等条件做二次过滤
   - 过滤后的候选岗位再喂给 `extract_search_results(auto_enqueue=true)` 或 `parse_search_page`

7. 51job 职位详情页可能先触发滑块验证
   - 搜索结果可抓到，但打开具体 `jobs.51job.com/...` 职位页时，可能直接进入“访问验证 / 请按住滑块拖到最右边”页面
   - 当前 Hermes 浏览器工具无法稳定完成拖拽滑块；遇到这种情况不要反复硬点
   - 应立刻 `mark_job(status='blocked', notes='滑块验证')`，并切换到猎聘/BOSS 或让用户先人工过验证

8. BOSS 在 Hermes 浏览器里可能出现白屏
   - 如果 `browser_navigate(search_url)` 后是 `Empty page`，先重试一次，并用 `browser_vision` / `browser_console` 判断是否真白屏
   - 若仍为空白且无明确报错，不要在 BOSS 上继续耗时，直接改走猎聘或 51job

9. 招聘站点登录/验证是优先检查项
   - 猎聘职位详情通常能打开，但右侧投递区可能要求先登录
   - 进入投递动作前，先判断是否有登录框、验证码、滑块，而不是先找“投递”按钮
   - 若需登录，先让用户完成登录，再继续推进到 `prepare -> 上传 -> confirm_submit`

## 可复用命令骨架
### 获取站点规则
```json
{"action":"site_profile","site":"51job"}
```

### 投递前校验
```json
{
  "action":"prepare",
  "site":"liepin",
  "resume_path":"/mnt/c/Users/Kent/Documents/resume.pdf",
  "job_url":"https://www.liepin.com/job/xxxx.shtml",
  "company":"某公司",
  "title":"IT经理"
}
```

### 提交前确认
```json
{
  "action":"confirm_submit",
  "site":"boss",
  "company":"某公司",
  "title":"信息化经理",
  "confirm":true
}
```

### 从结果页自动入队
```json
{
  "action":"parse_search_page",
  "batch_id":"batch_xxx",
  "page_data":[...],
  "auto_enqueue":true
}
```

### 取下一个待投岗位
```json
{
  "action":"next_job",
  "batch_id":"batch_xxx"
}
```

### 标记投递结果
```json
{
  "action":"mark_job",
  "batch_id":"batch_xxx",
  "job_url":"https://www.zhipin.com/job_detail/1.html",
  "status":"submitted",
  "notes":"已投递"
}
```

**简历路径**：Windows `D:\简历\陈凯特的简历.pdf`

**用户信息**：Kent，深圳，IT经理/信息化负责人/项目经理，月薪目标 25k-40k

**求职平台 IP 问题**：当前 WSL IP `120.229.47.219`（中国移动数据中心 AS9808）被 51job/猎聘/BOSS 全部拦截，需住宅代理才能继续

**用户偏好**：坚持尝试突破，不轻易放弃

## 边界
当前是“半自动批量投递工作流”，不是无人值守海投：
- 验证码 / 短信 / 滑块通常仍需人工配合
- 最终提交建议保留人工确认
- 真正全自动翻页抓取、多页循环、持续运行 runner 需要再单独实现
