#!/bin/bash
# 飞书 channel 看门狗 — 检测断连并自动恢复
# crontab: */5 * * * * ~/.hermes/scripts/feishu-watchdog.sh >> ~/.hermes/logs/feishu-watchdog.log 2>&1

LOG_FILE="/home/kent/.hermes/logs/agent.log"
STATE_FILE="/tmp/feishu-watchdog.state"
ALERT_FILE="/tmp/feishu-watchdog.alert"
NOW=$(date +%s)
RECONNECT_WINDOW=300  # 5分钟内有重连视为正常
MAX_GAP=600           # 超过10分钟无重连才触发重启

# 找到最后一条飞书 WebSocket 启动日志的时间戳
last_ts=$(grep -E "feishu\[[a-z]+\]: WebSocket client started" "$LOG_FILE" 2>/dev/null | tail -1 | \
  python3 -c "import sys,re; 
l=sys.stdin.read().strip()
m=re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', l)
print(int(__import__('time').mktime(__import__('datetime').datetime.strptime(m.group(1),'%Y-%m-%dT%H:%M:%S').timetuple())))" 2>/dev/null || echo 0)

if [ "$last_ts" = "0" ] || [ -z "$last_ts" ]; then
  # 没有任何飞书重连日志，尝试找最后一条 feishu 日志
  last_ts=$(grep -E "feishu\[" "$LOG_FILE" 2>/dev/null | tail -1 | \
    python3 -c "import sys,re;
l=sys.stdin.read().strip()
m=re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', l)
if m:
  print(int(__import__('time').mktime(__import__('datetime').datetime.strptime(m.group(1),'%Y-%m-%dT%H:%M:%S').timetuple())))
else: print(0)" 2>/dev/null || echo 0)
fi

DIFF=$((NOW - last_ts))
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

if [ "$last_ts" = "0" ] || [ "$DIFF" -gt "$MAX_GAP" ]; then
  echo "[$TIMESTAMP] ALERT: Feishu disconnected for ${DIFF}s (threshold ${MAX_GAP}s), restarting gateway..."
  
  # 写告警标记
  echo "$TIMESTAMP:$DIFF" >> "$ALERT_FILE"
  
  # 避免抖动：上次重启后5分钟内不再重启
  if [ -f "$STATE_FILE" ]; then
    last_restart=$(cat "$STATE_FILE")
    last_restart_ts=$(echo "$last_restart" | cut -d: -f2)
    if [ -n "$last_restart_ts" ]; then
      gap=$((NOW - last_restart_ts))
      if [ "$gap" -lt 300 ]; then
        echo "[$TIMESTAMP] SKIP: Restarted ${gap}s ago, waiting..."
        exit 0
      fi
    fi
  fi
  
  # 执行重启
  /home/kent/.local/bin/openclaw gateway restart 2>&1
  echo "$TIMESTAMP:$NOW" > "$STATE_FILE"
  echo "[$TIMESTAMP] Gateway restarted."
else
  echo "[$TIMESTAMP] OK: Feishu last active ${DIFF}s ago (threshold ${MAX_GAP}s)"
fi
