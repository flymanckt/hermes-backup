# Recruitment Workflow Tool Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** 增加一个招聘投递助手工具，给前程无忧、猎聘、BOSS 等站点提供统一的投递准备、站点规则、提交确认与结果记录能力。

**Architecture:** 新增 `tools/recruitment_tool.py` 作为高层工作流工具，不直接替代浏览器操作，而是补齐浏览器之上的“站点规则 + 材料校验 + 明确确认 + 投递日志”层。工具采用 action 模式，避免为每个子动作拆很多工具；状态写入 `~/.hermes/recruitment/` 下的 JSONL 日志，保持可追踪。

**Tech Stack:** Python stdlib、Hermes tool registry、`hermes_constants.get_hermes_home()`、pytest。

---

### Task 1: 明确最小动作集

**Objective:** 把首版范围压缩到可交付且可测试。

**Files:**
- Create: `tools/recruitment_tool.py`
- Test: `tests/tools/test_recruitment_tool.py`

**Step 1: 定义动作**

首版仅做 4 个动作：
- `site_profile`：返回站点特征、常见流程、风控提示
- `prepare`：校验简历文件、生成建议步骤、返回是否就绪
- `confirm_submit`：要求显式 `confirm=true` 才放行最终提交
- `record_result` / `list_results`：写入并读取投递日志

**Step 2: 验证动作足够覆盖首版目标**

覆盖：
- 投递前材料准备
- 不同站点差异提示
- 最终提交前强制确认
- 已投递结果留痕

### Task 2: 先写失败测试

**Objective:** 用测试固定工具 API、行为和接线要求。

**Files:**
- Create: `tests/tools/test_recruitment_tool.py`

**Step 1: 写测试覆盖**

测试点：
- `prepare` 能识别存在/不存在的简历文件
- `prepare` 会阻止敏感文件
- `site_profile` 返回 51job / liepin / boss 三个站点规则
- `confirm_submit` 默认拒绝，只有 `confirm=true` 才通过
- `record_result` 会落盘，`list_results` 能返回记录
- 工具已注册并接入 toolsets / model_tools

**Step 2: 跑失败测试**

Run: `pytest tests/tools/test_recruitment_tool.py -q`
Expected: FAIL — 新工具尚未实现

### Task 3: 实现工具最小闭环

**Objective:** 以最少代码让测试通过。

**Files:**
- Create: `tools/recruitment_tool.py`
- Modify: `model_tools.py`
- Modify: `toolsets.py`

**Step 1: 实现站点配置**

支持：
- `51job`
- `liepin`
- `boss`

每个站点含：
- 登录方式提示
- 常见投递步骤
- 常见阻塞项
- 最终提交关键词

**Step 2: 实现文件校验与准备动作**

逻辑：
- 路径非空
- 文件存在且为普通文件
- 调用 `agent.safety_policy.get_sensitive_read_path_error()` 阻止敏感文件
- 返回 `ready`, `normalized_resume_path`, `next_steps`

**Step 3: 实现确认动作**

逻辑：
- `confirm=false/缺省` => 拒绝最终提交
- `confirm=true` => 返回放行结果与提醒

**Step 4: 实现日志动作**

存储：
- `~/.hermes/recruitment/application_log.jsonl`

记录字段：
- timestamp
- site
- company
- title
- url
- status
- notes

### Task 4: 接入工具注册

**Objective:** 确保模型实际能拿到这个工具。

**Files:**
- Modify: `model_tools.py`
- Modify: `toolsets.py`

**Step 1: 加入 `_discover_tools()`**

新增导入：`tools.recruitment_tool`

**Step 2: 加入 toolsets**

至少加入：
- `_HERMES_CORE_TOOLS`
- `TOOLSETS["browser"]`（因为它服务浏览器投递工作流）

### Task 5: 验证

**Objective:** 验证测试与工具暴露都正确。

**Files:**
- Test: `tests/tools/test_recruitment_tool.py`

**Step 1: 跑新增测试**

Run: `pytest tests/tools/test_recruitment_tool.py -q`
Expected: PASS

**Step 2: 跑相关回归**

Run: `pytest tests/tools/test_recruitment_tool.py tests/tools/test_browser_upload.py -q`
Expected: PASS

**Step 3: 验证工具已暴露**

Run Python snippet via terminal to call `get_tool_definitions(enabled_toolsets=['browser'])`
Expected: 包含 `recruitment_workflow`
