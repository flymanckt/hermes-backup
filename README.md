# Hermes - AI 个人助手

Kent 的个人 AI 助手配置仓库，支持多平台（飞书、微信等）和多场景（企业信息化咨询、A 股分析、学习辅助、文档处理）。

---

## 快速安装

### 环境要求

- Python 3.10+
- Git
- Node.js（可选，部分功能需要）

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/flymanckt/hermes-backup.git ~/.hermes

# 2. 进入目录
cd ~/.hermes

# 3. 安装 hermes-agent（主体框架）
cd hermes-agent
pip install -e .

# 4. 初始化配置
# 复制配置模板并填入你的 API Key
cp cli-config.yaml.example ~/.hermes/config.yaml
# 编辑 config.yaml 填入必要的 provider 和 channel 配置

# 5. 启动
hermes run
```

---

## 目录结构

```
~/.hermes/
├── SOUL.md               # 助手身份定义
├── PROFILES.md           # Profile 架构说明
├── config.yaml           # 配置文件（需自行配置）
├── memories/             # 长期记忆数据
├── skills/               # 技能模块
├── hermes-agent/         # Hermes Agent 主体框架
├── recruitment/          # 招聘批量投递工具
├── workspace/            # 工作区
├── scripts/              # 辅助脚本
└── backups/             # 备份记录
```

---

## 各模块说明

### Skills（技能）

| 路径 | 说明 |
|------|------|
| `skills/productivity/` | 文档处理、PPT、PDF、飞书等 |
| `skills/software-development/` | 代码计划、审查、调试 |
| `skills/mlops/` | 模型训练、推理、部署 |
| `skills/research/` | 学术搜索、论文阅读 |
| `skills/openclaw-imports/` | 企业信息化咨询方法论 |

### Profiles（多场景）

通过 `hermes profile` 切换不同场景：

| Profile | 用途 |
|---------|------|
| `hermes`（默认） | 主助手 |
| `consulting` | 企业信息化与数字化顾问 |
| `finance` | A 股交易情报与风控 |
| `study` | 合规学习辅助 |
| `docs` | 飞书文档专家 |

### 招聘批量投递

路径：`recruitment/`

工具：`recruitment_tool.py`

功能：支持猎聘、BOSS、51job 批量搜索、提取 JD、自动填表投递。

```python
# 用法示例（工具内调用）
from recruitment_tool import run_batch_once
result = run_batch_once({
    "batch_id": "your_batch_id",
    "site": "liepin",
    "resume_path": "/path/to/resume.pdf"
})
```

### 企业信息化咨询

路径：`skills/openclaw-imports/consulting-method/`

包含：需求池诊断、P2P/O2C 流程、制造业案例库、咨询方法论模板。

---

## 配置文件说明

`config.yaml` 核心配置项：

```yaml
# 模型 Provider 配置
providers:
  dashscope:
    api_key: "your-api-key"
    model: "qwen-max"

  openai-codex:
    api_key: "your-api-key"
    model: "gpt-5.2"

# 平台渠道（飞书、微信等）
channels:
  feishu:
    app_id: "your-feishu-app-id"
    app_secret: "your-feishu-app-secret"

# 默认 Profile
default_profile: "hermes"
```

---

## 常用命令

```bash
# 启动助手
hermes run

# 切换 Profile
hermes profile switch consulting

# 查看状态
hermes status

# 查看日志
hermes logs

# 更新技能
hermes skills update

# 备份
hermes backup
```

---

## 常见问题

**Q: 模型缓存（profiles/）需要上传吗？**
不需要。`profiles/` 在新电脑运行时会自动下载相应模型，上传反而会超过 GitHub 仓库大小限制。

**Q: auth.json 包含敏感信息，如何处理？**
`auth.json` 未包含在此仓库中。请在新环境手动创建或从旧环境迁移时手动复制。

**Q: 招聘工具无法登录怎么办？**
BOSS/51job 对 WSL IP 识别严格，可能触发安全验证。建议优先使用猎聘（captcha 较少）。详见招聘工具文档。

---

## 更新日志

- **2026-04-22**: 首次全量备份，包含 memories、skills、hermes-agent、recruitment

---

*由 Hermes Agent 管理 | Kent 个人使用*
