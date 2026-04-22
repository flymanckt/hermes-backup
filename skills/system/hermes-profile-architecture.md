# Hermes Profile 架构管理

## 触发条件

当需要理解、更新或整理 hermes 的 profile 架构时使用。

## 关键事实

### 目录结构
```
/home/kent/.hermes/                        # Hermes 主目录（运行时根）
├── PROFILES.md                             # Profile 架构总览
├── SOUL.md                                 # 主人格定义
├── config.yaml                             # 主配置
├── profiles/                               # 各 profile 配置目录
│   ├── hermes/                            # 爱马仕主入口
│   │   ├── SOUL.md
│   │   ├── config.yaml
│   │   ├── skills/ → /home/kent/.hermes/skills/  # 符号链接
│   │   └── workspace/                     # 工作目录（真实内容）
│   ├── consulting/
│   ├── finance/
│   ├── study/
│   ├── docs/
│   └── dev/                               # 德鲁伊开发 profile
```

### 重要原则
1. **Hermes 就是 Hermes**，不是 OpenClaw。OpenClaw 是底层运行时框架，不是身份的一部分。
2. **主目录是 `/home/kent/.hermes/`**，不是 `/home/kent/.openclaw/workspace/`。
3. **各 profile workspace 真实内容**在 `/home/kent/.hermes/profiles/<name>/workspace/`。
4. 迁移后必须同步更新对应 `config.yaml` 的 `terminal.cwd` 字段。

### config.yaml 关键字段
```yaml
model:
  default: MiniMax-M2.7-highspeed
  provider: minimax-cn
toolsets:
- hermes-cli
terminal:
  backend: local
  cwd: /home/kent/.hermes/profiles/<name>/workspace  # 必须与实际路径匹配
  timeout: 180
```

## 常用操作

### 查看所有 profile 状态
```bash
for p in hermes consulting finance study docs; do
  echo "=== $p ==="
  grep "cwd:" /home/kent/.hermes/profiles/$p/config.yaml
  ls /home/kent/.hermes/profiles/$p/workspace/ | head -5
done
```

### 迁移 workspace
```bash
# 从原路径迁移到 profile workspace
cp -r <原路径>/* /home/kent/.hermes/profiles/<name>/workspace/
```

### 同步更新 config.yaml cwd
使用 patch 替换 `terminal.cwd:` 行。

## 已知分散路径（历史遗留，已迁移）
- `/home/kent/repos/main-agent/` → consulting
- `/home/kent/repos/finance/stock-agent/` → finance
- `/home/kent/repos/finance/study-agent/` → study
- `/home/kent/.openclaw/workspace/` → hermes
- `/home/kent/.openclaw/workspace/docs-agent/` → docs
