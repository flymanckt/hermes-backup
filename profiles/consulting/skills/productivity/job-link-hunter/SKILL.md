---
name: job-link-hunter
description: 在猎聘/51job/BOSS上自动搜索并提取简历投递链接，发给用户自己投
---

# Job Link Hunter

在中文招聘平台上自动搜索并提取职位链接，发给用户手动投递。

## 平台访问结果（2026-04-22 实测）

| 平台 | 结果 | 说明 |
|------|------|------|
| 猎聘 | ✅ 可用 | 分类页可直接访问，搜索页可能触发 captcha |
| 51job | ✅ 可用 | 搜索框输入关键词后正常 |
| BOSS | ❌ 拦截 | WSL IP 全部触发安全验证 captcha |

## 猎聘（可用）

### 有效 URL 格式
```
https://www.liepin.com/city-sz/zpitxxhjl/        # 深圳IT信息化经理
https://www.liepin.com/zpitfuzeren/              # IT负责人
https://www.liepin.com/city-sz/zpit123/          # 深圳IT招聘
https://www.liepin.com/city-sz/zpitgangwei/      # 深圳IT岗位
```

**关键发现**：分类/列表页绕过 captcha，直接导航即可。搜索页（`/zhaopin/?keyword=...`）可能触发验证。

### 操作步骤
1. `browser_navigate` → 分类页 URL
2. `browser_snapshot` → 提取职位链接
3. 从 snapshot 的 link 元素中找 `job/xxxx.shtml` 或 `a/xxxx.shtml` 格式的 URL
4. 整理成列表发给用户

## 51job（可用）

### 搜索方式
```
https://we.51job.com/pc/search  → 搜索框输入关键词 → Enter
```

### 操作步骤
1. `browser_navigate` → `https://we.51job.com/pc/search`
2. `browser_click` → 搜索框
3. `browser_type` → 关键词（如 "IT经理 深圳"）
4. `browser_press` → Enter
5. `browser_snapshot` → 提取链接

## BOSS（不可用）

所有 URL 均触发安全验证 captcha，自动化 session 无法绕过。用户需在自己浏览器手动投。

## 职位链接格式

| 平台 | 链接格式 | 示例 |
|------|---------|------|
| 猎聘 | `liepin.com/job/xxxx.shtml` 或 `liepin.com/a/xxxx.shtml` | `https://www.liepin.com/job/1979344497.shtml` |
| 51job | `jobs.51job.com/all/xxxx.html` | `https://jobs.51job.com/all/coVDRSNV46BTgBbFc0VzY.html` |

## 关键文件

- 简历：`/mnt/d/简历/陈凯特的简历.pdf`
- 工具：`~/.hermes/hermes-agent/tools/recruitment_tool.py`
- 批次库：`~/.hermes/recruitment-batches/`（尚未初始化）
