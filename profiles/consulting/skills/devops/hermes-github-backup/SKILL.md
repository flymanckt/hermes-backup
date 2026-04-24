---
name: hermes-github-backup
description: 把 ~/.hermes 目录备份到 GitHub，新电脑可 clone 后直接运行
---

# Hermes → GitHub Backup Skill

## When to Use
用户想把 `~/.hermes/` 目录备份到 GitHub，在新电脑可以直接 `git clone` 后运行。

## Core Problem
`~/.hermes/` 通常 3-5GB，包含模型缓存（profiles/）、虚拟环境（venv/）、node_modules，直接上传会超过 GitHub 5GB 限制。

## Upload Scope (48MB 级)

### 上传
- `memories/` — 记忆数据
- `skills/` — 技能目录
- `hermes-agent/` — 主体代码（排除 venv/node_modules/__pycache__）
- `recruitment/` — 招聘工具 + batches
- `workspace/`、`scripts/`
- 根目录：`config.yaml`、`SOUL.md`、`PROFILES.md`

### 不上传（运行时会自动生成/下载）
- `profiles/` — 模型缓存（运行时会自动下载）
- `migration/` — 迁移遗留产物
- `venv/`、`node_modules/`、`__pycache__/`
- `.db-shm`、`.db-wal`、`state.db` — 数据库临时文件
- `sessions/`、`checkpoints/` — 临时运行产物
- `logs/`、`cache/`

## 操作步骤

### 1. 准备本地仓库
```bash
cd /tmp
git clone https://github.com/flymanckt/hermes-backup.git
cd hermes-backup
```

### 2. 整理文件（使用 rsync 排除大目录）
```bash
mkdir hermes-upload
rsync -av \
  --exclude='venv' \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  ~/.hermes/hermes-agent/ ./hermes-agent/
cp -r ~/.hermes/memories/ .
cp -r ~/.hermes/skills/ .
```

### 3. 复制配置文件
```bash
cp ~/.hermes/SOUL.md .
cp ~/.hermes/PROFILES.md .
cp ~/.hermes/config.yaml .
cp -r ~/.hermes/recruitment .
cp -r ~/.hermes/workspace .
cp -r ~/.hermes/scripts .
```

### 4. 清理 embedded git repo（踩坑）
`skills/openclaw-imports/openclaw-workspace` 内含独立 `.git`，会导致 git 报警：
```
warning: adding embedded git repository
```
修复：
```bash
rm -rf skills/openclaw-imports/openclaw-workspace/.git
```

### 5. 写入 .gitignore 并推送
```bash
cat > .gitignore << 'EOF'
__pycache__/
*.pyc
*.egg-info/
venv/
node_modules/
.env
*.log
.DS_Store
*.db-shm
*.db-wal
state.db
*.pid
gateway_state.json
processes.json
feishu_seen_message_ids.json
interrupt_debug.log
EOF

git init
git add -A
git commit -m "hermes backup"
git remote add origin https://github.com/flymanckt/hermes-backup.git
git branch -M main
git push -u origin main
```

## 新电脑恢复步骤
```bash
git clone https://github.com/flymanckt/hermes-backup.git ~/.hermes
cd ~/.hermes/hermes-agent
pip install -e .
hermes run
```

## 踩坑记录
- `profiles/` 包含 ~2GB 模型缓存，不能上传
- `migration/` 有 ~1.3GB 迁移产物，不用上传
- embedded `.git` 会导致整个 commit 失败，需提前删除
- `hermes-agent/` 用 rsync 比 `cp -r` 更安全（可细粒度排除）
