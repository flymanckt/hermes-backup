---
name: PPT-GEN
description: 生成结构化 PPT 的 OpenClaw 技能。用于根据 Word、PDF、Markdown、TXT、飞书文档、飞书云盘文件、方案稿、纪要或汇报材料生成 `.pptx`，支持 Kimi/OpenAI/Anthropic/Gemini/OpenRouter/DeepSeek，多模型可切换，默认套用本地企业模板。
metadata:
  openclaw:
    emoji: "🧭"
    requires:
      bins:
        - python3
---

# PPT-GEN

把文档、方案稿、会议纪要、项目汇报材料，生成成结构化的 `.pptx` 汇报文件。

默认目标不是“做一份能看”的普通 PPT，而是生成一份满足 IT 软件项目汇报标准、在电脑端 PowerPoint 打开不触发修复的稳定版文档。

## 能力

- 默认使用本地企业模板：`templates/company-default.pptx` + `templates/company-default-theme.json`
- 支持模型预设：`config/ppt_model_catalog.json`
- 支持输入文件：`docx` / `pdf` / `md` / `txt`
- 支持飞书来源：`feishu doc/docx` 链接 / `feishu wiki` 链接 / `feishu drive` 文件
- 支持 provider：`kimi` / `openai` / `anthropic` / `gemini` / `openrouter` / `deepseek`

## 生成原则（重要）

- 主链路默认走稳定模式：`python-pptx` 安全渲染 + 保存后结构校验
- 企业模板只作为品牌背景/尺寸来源，不再把整份模板当作输出底包直接改写
- 输出优先级固定为：`可打开性 > 结构完整性 > 内容质量 > 视觉复杂度`
- 默认采用“页面类型驱动”的生成方式：不同页面按 `摘要 / 痛点 / 架构 / 范围 / 流程 / 里程碑 / 风险 / 指标 / 下一步` 分配不同版式，而不是整套都用同一类 bullet 页
- 除非用户明确要求，不要把 `fill_template.py` 这类直接 XML 拼装脚本作为默认产出链路

## IT 项目汇报标准（默认）

默认页面骨架按下面顺序组织，目标读者是管理层、CIO/CTO、项目 Steering Committee：

1. 封面
2. 管理摘要
3. 项目背景与建设目标
4. 现状痛点与建设诉求
5. 方案架构与集成边界
6. 建设范围与核心模块
7. 关键业务场景与流程优化
8. 实施路径与里程碑
9. 风险与关键依赖
10. 预期收益与成功标准
11. 下一步行动

写作要求：

- 页面标题要“结论化”，不要只写“系统介绍”“项目概述”“汇报目录”
- 每页 3-5 条要点，每条尽量是“结论 + 支撑”
- 优先保留原文中的系统名、角色、时间点、指标、边界、依赖
- 流程页优先写“现状痛点 / 目标状态 / 关键变化”
- 指标页优先写“当前 / 目标 / 管理价值”
- 摘要页优先输出 4 个管理卡片；流程/里程碑页优先输出 4 步；收益页优先输出 3-4 个可衡量指标

## 默认页面类型与版式

`kimi_ppt_gen.py` 现在默认按页面语义选择稳定版式：

| 页面类型 | 默认视觉 |
|---------|---------|
| `summary` | 2x2 摘要卡片 |
| `problem` | 风险/痛点卡片 |
| `architecture` | 架构与边界卡片 |
| `scope` | 模块/范围卡片 |
| `process` | 横向 4 步流程 |
| `timeline` | 横向阶段/里程碑流程 |
| `risk` | 风险依赖卡片 |
| `metrics` | 指标卡片 |
| `next-step` | 行动步骤页 |

说明：

- 这些版式都走 `python-pptx` 安全渲染，不依赖复杂 XML 拼图
- 即使没有 API Key，仅靠本地内容拆解，也会按页面类型输出不同版式
- 如果模型返回了 `slide_kind`，会优先采用；未返回时脚本会按标题语义自动推断

## 模板机制（重要）

模板是真实的 `.pptx` 文件，**不是 JSON 配置**。核心原则：

### 母版文件结构
```
templates/
  company-default.pptx        # 企业母版（含5张预制页：封面/章节/TOC/内容/结尾，11种布局）
  company-default-theme.json  # 主题配置（颜色、字体、布局参数，含 loose/standard/compact 三变体）
```

### PPTX 内部结构（理解关键）
- `ppt/slides/slideN.xml` — 每页内容（XML格式）
- `ppt/slides/_rels/slideN.xml.rels` — 每页的关系（引用布局、图片）
- `ppt/presentation.xml` — 幻灯片列表引用
- `ppt/_rels/presentation.xml.rels` — 幻灯片文件路径映射
- `[Content_Types].xml` — 所有文件的内容类型声明

### 什么时候才使用直接 XML

只有在用户明确要求“复刻指定母版上的复杂图形页”时，才考虑走 XML 级脚本：

1. 解压模板 `shutil.unpack_archive()`
2. 复制 `slide4.xml`（内容页模板）→ `slideN.xml`
3. 复制 `slide4.xml.rels` → `slideN.xml.rels`
4. 修改 `slideN.xml` 内容（替换占位符、注入新图形XML）
5. 在 `presentation.xml` 的 `<p:sldIdLst>` 末尾添加 `<p:sldId id="NNN" r:id="rIdK"/>`
6. 在 `presentation.xml.rels` 末尾添加关系
7. 在 `[Content_Types].xml` 末尾添加 Override
8. 用 `zipfile.ZipFile` 重新打包（**不要用 `shutil.make_archive`**，后者会破坏结构）

### XML 操作注意事项
- 所有新增 shape 的 XML 必须用 `zipfile` 直接写入，不要用 `python-pptx` 添加幻灯片（会破坏母版背景图）
- 颜色值：`#0F1423`（深海军蓝）、`#6096E6`（科技蓝）、`#58B6E5`（浅蓝）、`#56CA95`（薄荷绿）、`#FFBA55`（橙黄）、`#F18870`（珊瑚橙）、`#EC5F74`（粉红）
- 字体：中文用 `微软雅黑`，英文用 `Arial`
- 单位：EMU，914400 EMU = 1cm
- 颜色值在 XML 中写为 `srgbClr val="RRGGBB"`（无 `#`）
- 文本中的 `&` 必须转义为 `&amp;`

### 图形 shape 命名（华孚模板）
| Shape 名称 | 用途 |
|-----------|------|
| `文本框 5/6/7/11/12` | 固定位置文本框 |
| `矩形 6` | 内容页标题占位符（`标题文字替换`） |
| `矩形 4` | 标题栏背景 |
| `图片 5` | 内容页背景图 |
| `THANK YOU.` | 感谢页文字 |

## 主要文件

| 文件 | 说明 |
|------|------|
| `scripts/kimi_ppt_gen.py` | LLM 增强版（需 API Key，调用 Kimi/OpenAI 等生成内容） |
| `scripts/gen_professional_ppt.py` | 专业图形版（正确使用企业母版，内置泳道图/对比图/集成图/流程图/表格渲染） |
| `scripts/fill_template.py` | 填充母版脚本（直接 XML 操作，实验用） |
| `scripts/gen_fund_system_ppt.py` | 资金系统 PPT 专用生成器（参考实现） |
| `templates/company-default.pptx` | 企业母版（含5张预制页：封面/章节/目录/内容/结尾） |
| `templates/company-default-theme.json` | 主题配置（含三套布局参数 loose/standard/compact） |
| `data/*.json` | 幻灯片结构化定义（gen_professional_ppt.py 的输入格式） |
| `docs/ppt-generation.md` | 详细使用文档 |

## 两种生成模式

| 模式 | 脚本 | 适用场景 | 依赖 |
|------|------|----------|------|
| LLM 增强版 | `kimi_ppt_gen.py` | 文档 → PPT（自动提炼内容） | API Key |
| 专业图形版 | `gen_professional_ppt.py` | 已有结构化内容 → 专业图形 PPT | 无（自包含） |

### 专业图形版 slide type（gen_professional_ppt.py）

支持以下页面类型，通过 JSON 定义输入：

| type | 说明 | 关键参数 |
|------|------|----------|
| `content` | 内容页（标题栏+摘要条+bullets） | title, summary, bullets[], tag |
| `swimlane` | 三层泳道图 | title, lanes[{title, color, boxes[{label,sub}]}] |
| `comparison` | 左右对比（现状 vs 目标） | title, left/right_title, left/right_color, left/right_items[] |
| `integration` | 系统集成图（中心+周边节点） | title, center, nodes[{label,color}] |
| `flow` | 横向流程图 | title, summary, steps[{label,sub,color}] |
| `table` | 彩色表头数据表 | title, headers[], rows[][] |
| `section` | 章节标题页 | num, title, subtitle |
| `toc` | 目录页 | items[] |
| `thankyou` | 结尾致谢页 | company |

颜色代码：C=珊瑚橙 F18870，G=薄荷绿 56CA95，B1=科技蓝 6096E6，B2=浅蓝 58B6E5，O=橙黄 FFBA55，Pk=粉红 EC5F74，P=深蓝 0F1423

## Feishu 机器人工作流

当用户在飞书里附带飞书文档链接时：

1. **docx 链接** → `feishu_doc` 读取正文
2. **wiki 链接** → `feishu_wiki` + `feishu_doc` 定位并读取
3. **云盘文件** → `feishu_drive` 获取 `file_token`，再传 `--feishu-file-token`
4. 交给 `scripts/kimi_ppt_gen.py` 生成 `.pptx`

## 快速用法

### 专业图形版（推荐，通用可复用）

准备 JSON 定义文件（参考 `data/fund_system_slides.json` 格式），然后：

```bash
python3 scripts/gen_professional_ppt.py \
  --slides-file data/your_slides.json \
  --output out/your-output.pptx
```

特点：正确使用企业母版（封面/章节/TOC/内容/结尾），内置泳道图/对比图/集成图/流程图/表格，无需 API Key。

### 稳定模式生成 PPT（推荐）

```bash
python3 scripts/kimi_ppt_gen.py \
  --input-file ../../data/your_source.md \
  --preset kimi-balanced \
  --output ../../out/your-output.pptx
```

说明：

- 默认按 IT 软件项目汇报结构生成
- 默认进行保存后结构校验
- 如果模板兼容性有风险，会自动降级为纯主题模式重试

### 填充母版生成 PPT（直接 XML，无需 LLM，仅实验/特殊模板页）
```bash
# 编辑 scripts/fill_template.py 中的 PAGES 和 BODY_SLIDES 定义
# 然后运行：
python3 scripts/fill_template.py
# 输出: out/fill_output.pptx
```

## 环境变量

- `KIMI_API_KEY` / `MOONSHOT_API_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY` / `GOOGLE_API_KEY`
- `OPENROUTER_API_KEY`
- `DEEPSEEK_API_KEY`

## 推荐策略

| 场景 | 推荐预设 |
|------|---------|
| 中文管理汇报 | `kimi-balanced` |
| 最终成稿润色 | `claude-premium` |
| 通用高质量 | `openai-premium` |
| 大材料处理 | `gemini-long-context` |
| 批量低成本初稿 | `deepseek-cost` |

## 常见问题排查

### PowerPoint 报"需要修复"
- 原因：模板底包直接改写、ZIP 结构破坏、XML 未转义，或关系引用不完整
- 解决：优先使用 `kimi_ppt_gen.py` 的稳定模式；不要默认走 XML 直拼；检查 `&` `<` `>` 转义和关系文件完整性

### 新增幻灯片空白/内容丢失
- 原因：`presentation.xml` 的 `sldId` 和 `rels` 未正确添加
- 解决：确认新幻灯片的 `rId` 在 `presentation.xml.rels` 中有映射

### 背景图丢失
- 原因：用 `python-pptx.add_slide()` 复制幻灯片时丢失母版背景
- 解决：直接复制 `slide4.xml` 并修改内容，不要用 `add_slide()`
