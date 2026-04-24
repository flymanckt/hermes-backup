# DEV PROFILE MEMORY

## 用户
- Name: Kent
- Preferences: 全程中文、先结论后细节、少客套、实用优先

## 身份
- Dev profile 名字：**德鲁伊**（Druid）
- 定位：资深全栈开发工程师
- 风格：冷静、直接、逻辑优先；代码优先，少废话

## 系统与自动化
- **Profile 路径**：`/home/kent/.hermes/profiles/dev`
- **Gateway service**：`hermes-gateway-dev.service`
- **Model**：MiniMax-M2.7-highspeed (minimax-cn)

## 配置状态
- dev profile 的飞书 gateway 因缺少真实 APP_SECRET 暂时无法连接
- 独立 systemd service 已注册并运行（2026-04-21）
§
mrp-model 项目目录：/home/kent/.hermes/profiles/dev/home/mrp_model
§
MRP项目路径: /home/kent/.hermes/profiles/dev/home/mrp_model
Flask MRP桌面后台，当前已完成: MRP试算、策略参数、质量规则、物料/产品/BOM主数据、订单快照、批次质量库存、锁批台账、供应建议台账、异常审批台账、编辑/删除校验、Excel导入导出、台账闭环状态流转。数据持久化为JSON文件在data目录。

飞书规格书: https://mcnbity757ix.fealsu.cn/docx/QzAidPssdoIuBjsxZLDYcWBt5nGJ (MRP规格书开发指导文件-v5)

新开发的skill: productivity/premium-pptx-production - 高质量.pptx生成skill，面向所有agent，保证电脑端PowerPoint/WPS可打开，参考Kimi等AI PPT质量标准。已配套qachecklist和ppt-brief模板。

用户当前外网临时地址: https://a0595e54ba17b5.lhr.life (临时不稳定，每次重连会变)

用户不在局域网内但需要外网访问，曾问能否用IP直连但当前环境不支持稳定公网直连，曾问域名申请，后续要稳定访问需要: 固定域名+Cloudflare Tunnel或云服务器固定部署。

用户沟通风格: 直接给指令+简短确认，偏好"继续做"的推进方式。不用过度解释背景信息。
§
Hermes 当前技能机制：中心共享库 `/home/kent/.hermes/skills/` + 各 profile 本地分类目录挂载；共享类目下的具体 skill 目录以符号链接方式同步到 `/home/kent/.hermes/profiles/<profile>/skills/`，并由 `sync_shared_skills.py` + `hermes-shared-skills-sync.timer` 每 2 分钟自动同步。