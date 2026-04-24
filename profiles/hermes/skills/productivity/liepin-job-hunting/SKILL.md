---
name: liepin-job-hunting
description: 猎聘批量找职位 + 链接发给用户自己投。适用于 BOSS/51job captcha 拦路时切换平台。
triggers:
  - BOSS 直聘 captcha 拦路
  - 51job captcha 拦路
  - 需要快速获取猎聘深圳 IT 经理相关职位链接
---
steps:
  1. 导航到猎聘搜索页（无需登录，可绕过 captcha）
     - 深圳 IT 信息化经理：https://www.liepin.com/city-sz/zpitxxhjl/
     - 深圳 IT 负责人：https://www.liepin.com/zpitfuzeren/
     - 深圳 IT 岗位：https://www.liepin.com/city-sz/zpitgangwei/
  2. browser_navigate → 读取 page snapshot
  3. 从 snapshot 的 job list 中提取 job 链接（格式：/job/XXXX.shtml 或 /a/XXXX.shtml）
  4. 按薪资/公司/地点整理成列表，发给用户
  5. 用户确认后，导航到目标 job URL，提取 JD 确认内容
  6. 用户自行投递
  7. 记录已投职位，避免重复投递
pitfalls:
  - Windows 浏览器登录状态和自动化浏览器 session 隔离，无法共享 cookie
  - 猎聘 captcha 会随机触发，若 navigation 后遇到验证码需换时机重试
  - 链接有 /job/ 和 /a/ 两种格式，均有效
  - 部分公司名被脱敏（"某深圳XX公司"），从 snapshot 中公司 link 提取
notes:
  - 自动化浏览器 IP 会被 BOSS/51job 识别为机器人并触发 captcha，但猎聘搜索页对此 IP 较宽容
  - 猎聘搜索页不需要登录即可访问，这是切换平台的核心原因
  - 用户明确：不需提取 JD 分析，直接发链接让用户自己判断
