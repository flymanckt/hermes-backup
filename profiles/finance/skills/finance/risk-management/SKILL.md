---
name: risk-management
description: A股风控规则 — 止损体系、仓位计算、账户风险监控、纪律执行。用于交易前决策和持仓风险评估。
triggers:
  - "止损"
  - "仓位计算"
  - "风控"
  - "风险"
  - "持仓风险"
---

# A股风控体系

## 核心原则

1. **没有止损位，不给买入建议**
2. **没有失效条件，不算交易计划**
3. 连续高潮后的利好，优先考虑兑现风险
4. 市场退潮期，默认保守
5. 技术指标不能单独作为结论依据

## 止损体系

### 硬止损 vs 软止损

| 类型 | 含义 | 使用场景 |
|------|------|----------|
| 硬止损 | 绝对不能破的价格，破了必须走 | 短线、亏损持仓 |
| 软止损 | 观察位，破了优先减仓，不一定全走 | 趋势持仓、盈利仓位 |

### 个股止损位设置

```python
def set_stop_levels(entry_price, position_type="long", klines=None):
    """
    设置止损位
    entry_price: 成本价
    position_type: long/short
    """
    if position_type == "long":
        # 短线（持有<2周）：-5%~7% 止损
        hard_stop = entry_price * 0.93
        soft_stop = entry_price * 0.95
        
        # 计算ATR如果提供了K线
        if klines:
            atr = calc_atr(klines, 14)
            hard_stop = entry_price - 2 * atr
            soft_stop = entry_price - 1.5 * atr
        
        return {
            "hard_stop": round(hard_stop, 2),
            "soft_stop": round(soft_stop, 2),
            "risk_pct": round((1 - hard_stop/entry_price) * 100, 1)
        }
```

### 持仓预警规则

```python
# 亏损幅度触发不同响应
def evaluate_position_risk(entry, current, hard_stop, soft_stop):
    """
    评估持仓风险等级
    """
    loss_pct = (current - entry) / entry * 100  # 负数为亏损
    
    if current <= hard_stop:
        return {
            "level": "🔴 强制止损",
            "action": "必须立即止损",
            "reason": "跌破硬止损位"
        }
    elif current <= soft_stop:
        return {
            "level": "🟡 预警",
            "action": "建议减仓50%或观望",
            "reason": "接近硬止损，盈亏比恶化"
        }
    elif loss_pct < -10:
        return {
            "level": "🟠 重仓预警",
            "action": "审视买入逻辑是否失效",
            "reason": "亏损超过10%"
        }
    elif loss_pct < -5:
        return {
            "level": "🟡 轻微浮亏",
            "action": "持有，观察能否收复",
            "reason": "正常波动范围"
        }
    else:
        return {
            "level": "🟢 正常",
            "action": "持有",
            "reason": "在成本附近或小幅盈利"
        }
```

## 仓位管理

### 总仓位控制

```python
def calc_total_position_risk(positions, total_capital):
    """
    计算整体持仓风险
    positions: [{symbol, shares, entry, hard_stop}, ...]
    total_capital: 总资金
    """
    total_risk = 0
    details = []
    
    for pos in positions:
        risk_per_share = pos['entry'] - pos['hard_stop']
        total_risk_amount = risk_per_share * pos['shares']
        risk_pct = total_risk_amount / total_capital * 100
        
        details.append({
            "symbol": pos['symbol'],
            "risk_amount": round(total_risk_amount, 2),
            "risk_pct": round(risk_pct, 1)
        })
        total_risk += total_risk_amount
    
    return {
        "total_risk_amt": round(total_risk, 2),
        "total_risk_pct": round(total_risk/total_capital*100, 1),
        "details": details
    }
```

### 单只股票仓位上限

```python
# 单只股票最大仓位（建议规则）
MAX_SINGLE_POSITION_PCT = 30  # 不超过总资金30%

def check_position_size(shares, price, total_capital):
    """检查仓位是否超限"""
    position_value = shares * price
    position_pct = position_value / total_capital * 100
    
    if position_pct > MAX_SINGLE_POSITION_PCT:
        return {
            "ok": False,
            "excess_pct": round(position_pct - MAX_SINGLE_POSITION_PCT, 1),
            "max_shares": int(total_capital * MAX_SINGLE_POSITION_PCT / 100 / price)
        }
    return {"ok": True, "position_pct": round(position_pct, 1)}
```

### 加仓规则（等比/金字塔）

```python
# 金字塔加仓法（仅适用于盈利持仓）
def add_position_tiers(entry_price, current_price, base_shares, max_tiers=3):
    """
    分档加仓策略
    每涨5%加仓一次，最多加3次
    """
    tiers = []
    for i in range(1, max_tiers + 1):
        trigger_price = entry_price * (1 + 0.05 * i)
        add_shares = base_shares // (i * 2)  # 越加越少
        tiers.append({
            "tier": i,
            "trigger_pct": f"+{i*5}%",
            "trigger_price": round(trigger_price, 2),
            "add_shares": add_shares
        })
    return tiers

# 示例
# 成本14.39的诚邦股份，当前15.63
# 第一档：14.39*1.05=15.11（已过，可加）
# 第二档：14.39*1.10=15.83（接近）
# 第三档：14.39*1.15=16.55（远）
```

## 账户风险监控

### 账户预警线

```python
# 账户核心指标
TOTAL_CAPITAL = 10000  # 总资金
INITIAL_CAPITAL = 10000  # 初始资金
STOP_LOSS_LINE = INITIAL_CAPITAL * 0.93  # 止损线（-7%）
DANGER_LINE = INITIAL_CAPITAL * 0.88  # 危险线（-12%）

def check_account_health(positions, available_cash, total_capital):
    """
    定期检查账户健康度
    """
    position_value = sum(p['shares'] * p['current'] for p in positions)
    total_assets = position_value + available_cash
    
    drawdown = (total_assets - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
    
    warnings = []
    if total_assets <= STOP_LOSS_LINE:
        warnings.append(f"🔴触及止损线！当前总资产{total_assets:.0f}，需严格风控")
    if total_assets <= DANGER_LINE:
        warnings.append(f"🔴极度危险！资产{drawdown:.1f}%，建议清仓观望")
    if drawdown < -10:
        warnings.append(f"🟠回撤超过10%，检查持仓逻辑")
    
    return {
        "total_assets": round(total_assets, 2),
        "position_value": round(position_value, 2),
        "available_cash": round(available_cash, 2),
        "drawdown_pct": round(drawdown, 2),
        "warnings": warnings
    }
```

### 止损执行检查清单

```
止损前确认：
□ 现价是否确实跌破硬止损？
□ 今日成交量是否正常（非乌龙指）？
□ 是否有重大未兑现的利好（若有，可观察一天）？
□ 止损后资金是否需要调配？

执行原则：
□ 亏损不超过总资金5%（单只）
□ 止损不要犹豫，越拖越被动
□ 止损后不要立即反手追入，等企稳
```

## 持仓分析报告格式

```
## 持仓风险报告 · [日期]

### 账户概览
- 总资产：X元
- 可用资金：X元
- 当前回撤：X%
- 风险状态：🟢/🟡/🔴

### 持仓逐个分析
| 标的 | 成本 | 现价 | 盈亏 | 硬止损 | 距止损% | 风险等级 |
|------|------|------|------|--------|---------|---------|
| XXX | X | X | X | X | X% | 🟢/🟡/🔴 |

### 操作建议
- 需止损：X（立即执行）
- 需减仓：X（优先处理）
- 可持有：X
- 现金仓位：X%（建议保留X%）

### 纪律执行
- 昨日止损执行情况：✅/❌
- 本周累计止损次数：X次
- 最大单日亏损：X元
```
