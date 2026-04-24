---
name: pptx-to-consulting-summary
description: 从 PPTX 文件提取内容并输出咨询类产出（收益总结、一页说明、量化指标）。触发条件：用户上传 .pptx 文件并要求输出收益、价值、总结类内容。
version: 1.0.0
---

# PPTX 内容提取与咨询产出技能

## 触发条件
- 用户上传 `.pptx` 文件
- 要求输出：收益总结、一页说明、价值分析、量化指标、核心收益

## 提取方法（Python 标准库，无需第三方包）

```python
import zipfile, re

def extract_pptx_text(path):
    """从 PPTX 文件提取所有幻灯片文本内容"""
    slides_content = {}
    with zipfile.ZipFile(path) as z:
        slides = sorted([f for f in z.namelist()
                         if f.startswith('ppt/slides/slide') and f.endswith('.xml')])
        for i, sl in enumerate(slides):
            with z.open(sl) as f:
                content = f.read().decode('utf-8')
                texts = re.findall(r'<a:t>(.*?)</a:t>', content)
                slides_content[i+1] = [t.strip() for t in texts if t.strip()]
    return slides_content
```

**关键点**：
- PPTX 本质是 ZIP 压缩包，内部为 XML
- 文本节点标签：`<a:t>...</a:t>`
- 无需 python-pptx、pip install 等，用标准库即可

## 典型输出结构（按用户需求分层）

### L1：产出收益总结（含指标）
```
## [项目名] — 产出收益总结

### 采购效率提升
| 指标 | 现状痛点 | 建成后目标 |

### 供应商管理优化
| 指标 | 现状痛点 | 建成后目标 |

### 成本管控能力
| 指标 | 现状痛点 | 建成后目标 |

### 系统架构与扩展
| 指标 | 现状痛点 | 建成后目标 |
```

### L2：一页说明（精要版）
```
## [项目名] — 一页说明

**项目背景**：...（1-2句，点痛点）

**建设内容**：...（核心模块，1-2句）

**核心收益**：
- 安全：...
- 效率：...
- 管控：...

**投资概览**：总投入 X 万元，覆盖 Y，分 Z 期

**一句话定位**：...
```

### L3：量化指标模板（适用于企业规划文档）
```
| 维度 | 现状基准 | 建成后目标 |
|------|---------|-----------|
```

## 咨询输出原则
- 先结论后细节
- 有数据填数据，无数据用"现状痛点→建成目标"结构
- 量化指标需要用户自己填基准数据时，主动说明框架+请用户提供数字
- 管理层汇报用 L2 一页版，业务讨论用 L1 详细版

## 经验记录
- markitdown / python-pptx / LibreOffice 在本环境中均不可用，zipfile+regex 是唯一可靠方案
- 提取时加 `if t.strip()` 过滤空节点
- slides 可能有多页，按编号顺序遍历即可
