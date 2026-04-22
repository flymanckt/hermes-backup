---
name: feishu-gateway-recovery
description: 飞书频道假死诊断与恢复流程。触发条件：飞书机器人无响应、日志中所有 feishu channel 同时收到 abort 信号。根因：多个 openclaw profile gateway 并发运行时，后启动的会向先运行的发送 abort 信号关闭其 channel，但目标 gateway 可能未重启导致 channel 无法自恢复。
category: devops
---

# 飞书 Gateway 假死恢复流程

## 触发条件

- 飞书机器人无响应
- 日志中出现大量 `feishu[xxx]: abort signal received, stopping`
- 所有飞书 channel 同时中断，之后无 reconnect 日志

## 根因（经验确认）

**直接原因：** dev gateway 和 main gateway 同机运行，端口相同（18790），后启动的 gateway 向先运行的 gateway 发送 abort 信号，关闭其所有飞书 channel。dev 配置里没有飞书 channel，所以关掉后没有自动重连。

**触发路径：** 今早 snap 脚本（`/tmp/hermes-snap-*.sh`）自动拉起了 dev gateway：
```
PID 2798: bash -c source /tmp/hermes-snap-*.sh → eval 'nohup openclaw gateway run --profile dev'
PID 2817: openclaw-gateway（dev 实例，与 main 抢 18790 端口）
```

**main gateway 来源：** `~/.config/systemd/user/openclaw-gateway.service`，enabled，开机自启，监听 18790。

**dev gateway 来源：** 今早 Hermes 会话的 snap 脚本残留，端口与 main 冲突，auth 缺失（无 API key），本身无法正常工作。

**关键日志标志：**
- 所有飞书 channel 同时收到 `abort signal received, stopping`
- 之之后无 `feishu[xxx]: WebSocket client started` 重连日志
- `bot open_id resolved: unknown` → 该 channel 未成功连接

## 诊断步骤

### 1. 检查 gateway 状态
```bash
openclaw status
# 关注: Gateway reachable / unreachable
# 关注: Agents sessions 数量
```

### 2. 检查飞书 channel 日志
```bash
tail -100 /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log 2>/dev/null | grep -E "feishu|abort|WebSocket"
```

关键日志信号：
- `abort signal received, stopping` → channel 被强制关闭
- 无 `feishu[xxx]: starting WebSocket` → 未重连
- `bot open_id resolved` → 重连成功

### 3. 确认所有 channel 状态
从日志中确认以下 5 个 channel 是否都有 WebSocket 重连日志：
- `feishu[main]`
- `feishu[default]`  
- `feishu[consulting]`
- `feishu[docs]`
- `feishu[finance]`

## 恢复操作

### 重启主 gateway
```bash
openclaw gateway restart
# 等价于: systemctl restart openclaw-gateway.service
```

### 验证恢复
```bash
# 等待 10 秒后检查日志
sleep 10 && tail -50 /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log | grep -E "feishu|bot.*open_id|WebSocket.*started"
```

成功信号（全部出现）：
```
feishu[xxx]: bot open_id resolved: ou_xxxxxxxxxxxx
feishu[xxx]: WebSocket client started
```

## 自动恢复（Watchdog）

对于频繁发生的假死，可部署自动 watchdog：

### 脚本：`~/.hermes/scripts/feishu-watchdog.sh`

```bash
#!/bin/bash
LOG_FILE="/tmp/openclaw/openclaw-$(date +%Y-%m-%d).log"
STATE_FILE="/tmp/feishu-watchdog.state"
NOW=$(date +%s)
MAX_GAP=600  # 超过10分钟无重连则重启

last_ts=$(grep -E "feishu\[[a-z]+\]: WebSocket client started" "$LOG_FILE" 2>/dev/null | tail -1 | \
  python3 -c "import sys,re;
l=sys.stdin.read().strip()
m=re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', l)
print(int(__import__('time').mktime(__import__('datetime').datetime.strptime(m.group(1),'%Y-%m-%dT%H:%M:%S').timetuple())))" 2>/dev/null || echo 0)

DIFF=$((NOW - last_ts))

if [ "$last_ts" = "0" ] || [ "$DIFF" -gt "$MAX_GAP" ]; then
  # 冷却机制：5分钟内不重复重启
  if [ -f "$STATE_FILE" ]; then
    last_restart=$(cat "$STATE_FILE" | cut -d: -f2)
    [ $((NOW - last_restart)) -lt 300 ] && exit 0
  fi
  openclaw gateway restart
  echo "$(date '+%Y-%m-%d %H:%M:%S'):$NOW" > "$STATE_FILE"
fi
```

### 部署
```bash
chmod +x ~/.hermes/scripts/feishu-watchdog.sh
# 加到 crontab
(crontab -l 2>/dev/null | grep -v feishu-watchdog; \
  echo "*/5 * * * * ~/.hermes/scripts/feishu-watchdog.sh >> ~/.hermes/logs/feishu-watchdog.log 2>&1") | crontab -
```

### 验证
```bash
~/.hermes/scripts/feishu-watchdog.sh  # 应输出 OK 或 ALERT + restart
tail ~/.hermes/logs/feishu-watchdog.log
```

## 预防措施

1. **清理残留 dev gateway** — 每次假死后必须检查并 kill：
   ```bash
   pgrep -f "openclaw.*dev"    # 查看残留进程
   kill $(pgrep -f "openclaw.*dev")  # 清理
   ```
   dev gateway 由今早 snap 脚本拉起，属于不应长期运行的临时进程。

2. **禁止同机运行多 profile gateway** — dev profile 专用于开发调试，不需要也不应该跑独立 gateway 实例。改用 `openclaw agent` 模式或其他不需要 gateway 的方式。

3. **systemd user service 管理**（main gateway）：
   ```bash
   systemctl --user status openclaw-gateway   # 查看状态
   systemctl --user stop openclaw-gateway      # 手动停
   systemctl --user disable openclaw-gateway   # 禁止自启（慎用）
   ```

4. **检查方式：** `ps aux | grep openclaw` 看是否有多个 gateway 进程（正常只有一个 main gateway）。

## 附录：Gateway 进程识别

| 进程 | 来源 | 端口 | 飞书 | 正常状态 |
|------|------|------|------|------|
| openclaw-gateway（main） | systemd user service | 18790 | ✅ | 应长期运行 |
| openclaw-gateway（dev） | snap 脚本残留 | 18790（冲突） | ❌ | 应清理 |

dev gateway 日志路径：`~/.hermes/profiles/dev/logs/gateway.log`，可辅助判断是否为残留。

## 已知问题

- 飞书 ping 超时（`timeout of 10000ms exceeded`）通常是 WSL 访问飞书服务器网络问题，不等于 channel 不可用，需结合 bot open_id 判断
- `bot open_id resolved: unknown` 会触发后台重试（60s, 120s, 300s, 600s, 900s...），不影响其他已连接 channel
- `openclaw sessions list` 命令不存在（不接受参数），列出会话用 `openclaw sessions`

## 排查分支：WebSocket 在线但 bot identity 持续失败

**症状：** 所有 channel WebSocket 均已连接（`WebSocket client started`），但 bot identity 重试持续失败（`ECONNREFUSED 127.0.0.1:10809` 或类似），`open_id` 始终为 `unknown`。

**诊断步骤：**
```bash
# 1. 确认代理端口状态
ss -tlnp | grep -E "7897|10809"

# 2. 查 systemd service 的代理环境（已正确配置空代理）
systemctl --user show openclaw-gateway.service | grep -E "Environment|UnsetEnvironment" | grep -i proxy

# 3. 确认代理是否实际在监听
curl -s --max-time 3 http://127.0.0.1:10809 2>&1
curl -s --max-time 3 http://127.0.0.1:7897 2>&1
```

**根因：** 代理服务（如 Clash、v2ray 等）已关闭，但 Node 进程通过 systemd environment.d 或用户级环境配置继承了 `HTTP_PROXY=/HTTPS_PROXY=`。systemd service 虽然设置了 `UnsetEnvironment=HTTP_PROXY HTTPS_PROXY...`，但如果 service 文件或 override.conf 中的变量赋值早于 unset，或者进程通过 `systemctl --user set-environment` 设置了代理变量，仍可能导致进程启动时代理被写入环境。

**恢复方案：**

- **方案 A：** 重启代理服务（推荐），gateway 会自动重试并恢复
- **方案 B：** 清除残留代理环境变量：
  ```bash
  systemctl --user unset-environment HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy
  openclaw gateway restart
  ```

**验证恢复：**
```bash
sleep 5 && tail -50 /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log | grep -E "bot open_id resolved|ECONNREFUSED"
```
成功信号：各 channel 出现 `bot open_id resolved: ou_xxxxxxxxxxxx`
