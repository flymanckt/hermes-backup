---
name: intraday-analysis
description: A股盘中综合分析 — 整合大盘+持仓+技术面的盘中分析流程。用于回答"要不要补仓/持有/止损"类问题。
triggers:
  - "盘中分析"
  - "要不要补"
  - "还能持有吗"
  - "怎么看"
---

# A股盘中综合分析

## 调用顺序（标准化流程）

### Step 1：大盘指数（ulist 批量查询，分批）

```python
import urllib.request, json

def get_ulist(secids, fields="f2,f3,f4,f5,f12,f14,f15,f16,f17,f18"):
    """EastMoney ulist API，secids 建议不超过5个否则可能返回空"""
    url = (f"https://push2.eastmoney.com/api/qt/ulist.np/get"
           f"?fltt=2&invt=2&fields={fields}&secids={secids}"
           f"&ut=fa5fd1943c7b386f172d6893dbfba10b")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read().decode('utf-8'))['data']['diff']

# 分批调用
indices = get_ulist("1.000001,0.399001,0.399006,1.000300")
positions = get_ulist("1.603341,0.002969,1.603316,1.560390")
```

### Step 2：持仓K线（技术面）

```python
def get_kline(secid, days=30):
    """获取日K线，每条格式：日期,开,收,高,低,成交量"""
    url = (f"https://push2his.eastmoney.com/api/qt/stock/kline/get"
           f"?secid={secid}&fields1=f1,f2,f3,f4,f5,f6"
           f"&fields2=f51,f52,f53,f54,f55,f56,f57"
           f"&klt=101&fqt=1&lmt={days}&end=20500101"
           f"&ut=fa5fd1943c7b386f172d6893dbfba10b")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read().decode('utf-8'))
    return data['data']['klines']

def calc_ma(klines, n):
    closes = [float(k.split(',')[2]) for k in klines]
    return sum(closes[-n:]) / n

def analyze_levels(klines, price, cost, stop, shares):
    """计算均线、支撑压力、盈亏"""
    closes = [float(k.split(',')[2]) for k in klines]
    highs  = [float(k.split(',')[3]) for k in klines[-20:]]
    lows   = [float(k.split(',')[4]) for k in klines[-20:]]
    
    ma5  = calc_ma(klines, 5)
    ma10 = calc_ma(klines, 10)
    ma20 = calc_ma(klines, 20)
    
    recent_high = max(highs)
    recent_low  = min(lows)
    
    pnl     = (price - cost) * shares
    pnl_pct = (price - cost) / cost * 100
    # ⚠️ 注意：只有 price > stop 时才计算距止损；price <= stop 则已破止损
    dist_stop = (price - stop) / stop * 100 if stop and price > stop else None
    stop_status = "🚨 已破止损" if (stop and price <= stop) else (f"{dist_stop:.1f}%" if dist_stop else "未设止损")

    # 量能
    recent_vols = [int(k.split(',')[5]) for k in klines[-5:]]
    avg_vol = sum(recent_vols) / len(recent_vols)
    today_vol = recent_vols[-1]
    vol_ratio = today_vol / avg_vol if avg_vol > 0 else 0
    
    # 趋势判断
    if price > ma5 > ma10 > ma20:
        trend = "上升趋势"
    elif price < ma5 < ma10 < ma20:
        trend = "下降趋势"
    elif price < ma5 and ma5 < ma10:
        trend = "弱势整理"
    elif price > ma20 and ma5 > ma10:
        trend = "偏强整理"
    else:
        trend = "震荡"
    
    return {
        "ma5": round(ma5,3), "ma10": round(ma10,3), "ma20": round(ma20,3),
        "trend": trend, "pnl": round(pnl), "pnl_pct": round(pnl_pct,1),
        "dist_stop": dist_stop, "stop_status": stop_status, "vol_ratio": round(vol_ratio,1),
        "recent_high": round(recent_high,2), "recent_low": round(recent_low,2)
    }
```

### Step 3：量价结构（近5日）

```python
def vol_price_profile(klines, count=5):
    """近5日量价简表"""
    for k in klines[-count:]:
        parts = k.split(',')
        date, o, c, h, l, vol = parts[0], float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4]), int(parts[5])
        trend = "阳" if c > o else "阴"
        print(f"  {date}: 开{o:.2f} 收{c:.2f} 高{h:.2f} 低{l:.2f} {trend} {vol}手")
```

## 已知接口问题（踩坑记录）

| 接口 | 问题 | 解决方案 |
|------|------|----------|
| ulist 批量>5个secids | 返回空 | 分批调用（指数/持仓分开） |
| clist 行业资金流向 | RemoteDisconnected | 改用新浪财经接口（见下方） |
| 北向资金 API | 常返回 null | 暂时跳过 |
| 财联社 API | RemoteDisconnected | 跳过 |
| push2his K线（批量） | 批量请求返回空 | 单票串行请求，或用新浪替代 |

## 新浪财经数据源（稳定可靠，优先使用）

```python
import urllib.request, json, re

def fetch(url, retries=2):
    """通用HTTP请求封装"""
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://finance.sina.com.cn/'
            })
            resp = urllib.request.urlopen(req, timeout=12)
            return resp.read().decode('utf-8')
        except:
            import time; time.sleep(1)
    return None

def get_sina_stock_list(sort='changepercent', num=100):
    """
    新浪A股列表接口（最可靠的股票池数据）
    sort: changepercent(涨幅) / amount(成交额) / mktcap(市值)
    返回: 包含 name, code, trade, changepercent, open, high, low,
          settlement, volume, amount, per, pb, mktcap, nmc 等字段
    """
    url = (f"https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php"
           f"/Market_Center.getHQNodeData?page=1&num={num}&sort={sort}"
           f"&asc=0&node=hs_a&_s_r_a=page")
    raw = fetch(url)
    if not raw: return []
    return json.loads(raw)

# 示例：获取涨幅前100
stocks = get_sina_stock_list('changepercent', 100)

# 筛选涨幅>7%的主板股
filtered = []
for s in stocks:
    code = s.get('code',''); name = s.get('name','')
    chg = float(s.get('changepercent', 0)); amt = float(s.get('amount', 0))
    if code.startswith(('688','300','4','8')): continue  # 排除科创/创业/北交所
    if 'ST' in name: continue
    if chg < 7.0 or amt < 1e8: continue
    filtered.append(s)
```

## 新浪实时报价（单票详细数据）

```python
def get_sina_realtime(code):
    """
    新浪实时行情单票接口
    code: 6位股票代码（自动判断沪/深）
    返回: 32位逗号分隔数据，索引2=昨收，1=今开，3=今收，4=最高，5=最低，8=成交量，9=成交额
    """
    sym = f"sh{code}" if code.startswith('6') else f"sz{code}"
    raw = fetch(f"https://hq.sinajs.cn/list={sym}")
    if not raw: return None
    m = re.search(r'"([^"]*)"', raw)
    if not m: return None
    parts = m.group(1).split(',')
    return {
        'name': parts[0], 'open': float(parts[1]), 'prev': float(parts[2]),
        'close': float(parts[3]), 'high': float(parts[4]), 'low': float(parts[5]),
        'vol': int(parts[8]), 'amount': float(parts[9]),
        'chg_pct': (float(parts[3])-float(parts[2]))/float(parts[2])*100 if float(parts[2])>0 else 0
    }
```

## EastMoney K线（单票，推荐）

```python
def get_kline_em(secid, days=30):
    """EastMoney K线接口，单票稳定"""
    url = (f"https://push2his.eastmoney.com/api/qt/stock/kline/get"
           f"?secid={secid}&fields1=f1,f2,f3,f4,f5,f6"
           f"&fields2=f51,f52,f53,f54,f55,f56,f57"
           f"&klt=101&fqt=1&lmt={days}&end=20500101"
           f"&ut=fa5fd1943c7b386f172d6893dbfba10b")
    raw = fetch(url)
    if not raw: return []
    try:
        return json.loads(raw)['data']['klines']
    except:
        return []
```

## 板块资金流向（东方财富 clist，不稳定时的替代方案）

```python
def get_sector_flow():
    """
    新浪行业板块涨跌榜（替代东方财富clist）
    注意：此接口数据较简单，建议用东方财富clist作为主要来源，失败时用此兜底
    """
    url = ("https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php"
           "/Market_Center.getHQNodeData?page=1&num=20&sort=changepercent"
           "&asc=0&node=sw_a&_s_r_a=page")
    raw = fetch(url)
    if not raw: return []
    return json.loads(raw)
```

## 分析结论输出格式

```
## 持仓技术分析：标的名称

| 指标 | 数值 |
|------|------|
| 现价 | X（±X%）|
| 成本 / 盈亏 | X / ±X元(±X%) |
| MA5 / MA10 / MA20 | X / X / X |
| 止损 / 距止损 | X / **X%** 或 **🚨 已破止损** |
| 量能 | Xx均量 |
| 趋势 | X |
```

## 操作建议判断规则

| 条件 | 建议 |
|------|------|
| 止损已破 + 下降趋势 | 不补，止损优先 |
| 均线多头 + 盈利持仓 | 可持有，等回调 |
| 缩量回调至均线附近 | 可补（ETF/指数更安全） |
| 大盘高开低走 + 创业板弱 | 管住手，不补 |
| 止损未破 + 缩量整理 | 持有观望 |
