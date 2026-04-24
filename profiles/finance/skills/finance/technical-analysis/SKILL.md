---
name: technical-analysis
description: A股技术面分析 — 支撑压力、均线系统、成交量分析、K线形态、止损计算。用于盘中监控和入场判断。
triggers:
  - "技术分析"
  - "支撑位"
  - "压力位"
  - "止损计算"
  - "趋势判断"
---

# A股技术面分析

## 支撑压力位判断

### 方法一：近期高低点
```python
# 使用近期日线数据判断支撑压力
# 读取近20日数据，从 eastmoney 获取日K

import urllib.request, json

def get_daily_kline(secid, days=30):
    """获取日K线数据"""
    fields = "f1,f2,f3,f4,f5,f6"
    url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57&klt=101&fqt=1&lmt={days}&end=20500101&ut=fa5fd1943c7b386f172d6893dbfba10b"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read().decode('utf-8'))
    return data['data']['klines']

# secid 格式：沪市 1.代码，深市 0.代码
klines = get_daily_kline("0.002969")
print(f"最近30天K线数据条数: {len(klines)}")
# 每条格式: "日期,开,收,高,低,成交量"
```

### 方法二：均线系统计算
```python
# 从K线数据计算均线
closes = [float(k.split(',')[2]) for k in klines]
ma5  = sum(closes[-5:])  / 5
ma10 = sum(closes[-10:]) / 10
ma20 = sum(closes[-20:]) / 20
ma60 = sum(closes[-60:]) / 60 if len(closes) >= 60 else None

print(f"MA5={ma5:.2f} MA10={ma10:.2f} MA20={ma20:.2f}")
```

## 关键支撑/压力判断

| 价格类型 | 计算方法 | 含义 |
|----------|----------|------|
| 前高/前低 | 近20日最高/最低价 | 重要阻力/支撑 |
| 均线支撑 | 价格在MA5/MA10/MA20上方 | 上升趋势中的回踩位 |
| 均线压力 | 价格在均线下方反弹受阻 | 下降趋势中的阻力 |
| 成交密集区 | 近期成交量最大的价格区间 | 筹码集中区 |
| 布林带下轨 | MA20 - 2*标准差 | 超卖参考 |
| 成本价附近 | 大量持仓成本分布 | 心理关口 |

## 止损计算

```python
def calc_stop_loss(entry_price, position_type="long", atr=None, multiplier=2.0):
    """
    计算止损位
    position_type: "long" 做多, "short" 做空
    atr: 平均真实波幅（可选），若提供则用ATR方法
    multiplier: ATR倍数（默认2.0）
    """
    if atr:
        if position_type == "long":
            return entry_price - multiplier * atr
        else:
            return entry_price + multiplier * atr
    else:
        # 默认用成本比例
        if position_type == "long":
            return entry_price * 0.95  # 默认5%止损
        else:
            return entry_price * 1.05

def calc_position_size(account, risk_pct, entry, stop):
    """计算仓位"""
    risk_amount = account * risk_pct
    risk_per_share = abs(entry - stop)
    shares = int(risk_amount / risk_per_share)
    return shares
```

## 成交量分析

```python
def analyze_volume(klines):
    """分析成交量是否异常"""
    volumes = [int(k.split(',')[5]) for k in klines[-20:]]
    avg_vol = sum(volumes) / len(volumes)
    today_vol = volumes[-1]
    
    ratio = today_vol / avg_vol
    if ratio > 2.0:
        return "异常放量"
    elif ratio < 0.5:
        return "异常缩量"
    else:
        return "正常量"

def volume_price_confirm(klines):
    """
    量价配合判断
    上涨+放量 = 确认
    上涨+缩量 = 需警惕
    下跌+放量 = 确认
    下跌+缩量 = 可能见底
    """
    recent = klines[-3:]
    results = []
    for k in recent:
        parts = k.split(',')
        open_, close_, vol = float(parts[1]), float(parts[2]), int(parts[5])
        trend = "涨" if close_ > open_ else "跌"
        results.append((trend, vol))
    return results
```

## K线形态识别（基础）

```python
def recognize_candle(kline_str):
    """识别单根K线类型"""
    parts = kline_str.split(',')
    date, open_, close_, high, low = [float(x) for x in parts[1:5]]
    
    body = abs(close_ - open_)
    upper_shadow = high - max(open_, close_)
    lower_shadow = min(open_, close_) - low
    body_pct = body / (high - low) if high != low else 0
    
    if body_pct < 0.1:
        return "十字星（观望）"
    elif lower_shadow > body * 2 and upper_shadow < body * 0.5:
        return "锤子线（可能见底）"
    elif upper_shadow > body * 2 and lower_shadow < body * 0.5:
        return "射击星（可能见顶）"
    elif close_ > open_ and body_pct > 0.6:
        return "大阳线（强势）"
    elif close_ < open_ and body_pct > 0.6:
        return "大阴线（弱势）"
    else:
        return "普通K线"
```

## 分析报告输出格式

```
## 技术分析：XXX（代码）

### 走势概况
- 当前价：X元
- 近期趋势：（上升/下降/震荡）
- 关键均线：MA5=X, MA10=X, MA20=X

### 支撑与压力
- 压力位1：X元（近期前高）
- 压力位2：X元（MA60）
- 支撑位1：X元（MA20）
- 支撑位2：X元（布林下轨）
- 硬止损：X元

### 成交量信号
- 今日量能：X万手（较均量X%）
- 量价配合：（正常/异常放量/异常缩量）

### K线形态
- 今日形态：（锤子线/十字星/大阴线等）

### 结论
- 趋势：（强/中/弱）
- 建议：（持有/买入/止损/观望）
```

## 快速查询命令

```bash
# 获取单只股票日K（30天）
python3 -c "
import urllib.request, json
secid='0.002969'
url=f'https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57&klt=101&fqt=1&lmt=30&end=20500101&ut=fa5fd1943c7b386f172d6893dbfba10b'
req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
resp=urllib.request.urlopen(req,timeout=10)
data=json.loads(resp.read().decode('utf-8'))
for k in data['data']['klines'][-5:]:
    print(k)
"
```
