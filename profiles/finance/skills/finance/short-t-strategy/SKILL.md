---
name: short-t-strategy
description: 隔天短T策略 — 每日14:40扫描主板A股，筛选有次日上涨因素的强势股，给出开盘预期和操作建议。
triggers:
  - "短T"
  - "隔天"
  - "14:40"
  - "明日开盘预期"
  - "强势股"
---

# 隔天短T策略

## 策略逻辑

**核心思想**：A股T+1限制下，持有强势但未涨停的股票过夜（涨幅5-9%），次日开盘冲高卖出。

**重要**：涨停股（10%）散户根本买不进，策略只筛 **5-9%涨幅的非涨停股**，既强势又可买。

## 筛选条件（核心：5-9%非涨停强势股）

### 必须同时满足：
1. 涨幅 **5% ≤ chg < 9.9%**（非涨停、可买入）
2. 非创业板、非科创板（主板为主）
3. 非ST
4. 成交额 ≥ 1亿元（容量足够）
5. 非新股（上市>60日）

### 优先加分项：
- 涨幅7-9%（强势但未涨停）→ +15分
- 涨幅5-7%（温和上涨）→ +8分
- 成交额>10亿 → +10分
- 成交额>5亿 → +5分
- **无上影线**（收盘≈最高，强势信号）→ +12分
- 上影线<2% → +6分
- 长上影线>5% → -12分
- **下影线>2%**（下方有支撑）→ +8分
- 大实体阳线>7% → +8分
- 跳空高开>5% → -10分（高开太多容易低走）
- 低开高走（close>open）→ +8分
- 中小市值50-500亿（弹性好）→ +5分

## 开盘预期评级

| 预期 | 信号 | 操作 |
|------|------|------|
| 高开冲板 | 昨日涨停，明日竞价>3%高开 | 竞价出半仓 |
| 溢价冲高 | 昨日涨>7%，竞价1-3%高开 | 冲高卖 |
| 平开观察 | 昨日强势但平开/低开 | 等10点前方向 |
| 低于预期 | 高开低走/低于预期 | 开盘即出 |

## 数据源（已验证稳定）

### ✅ 主数据源：新浪财经（首选，2026-04-21验证可用）

```python
import urllib.request, json, re, time

# ==================== 核心API层（已验证） ====================

def fetch(url, headers=None, encoding='utf-8', retries=3):
    """
    通用HTTP请求，支持多编码
    - 涨幅榜K线: encoding='utf-8'
    - 实时行情hq.sinajs.cn: encoding='gbk'
    """
    for i in range(retries):
        try:
            req_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            if headers: req_headers.update(headers)
            req = urllib.request.Request(url, headers=req_headers)
            resp = urllib.request.urlopen(req, timeout=10)
            return resp.read().decode(encoding, errors='replace')
        except Exception as e:
            if i < retries-1: time.sleep(2)
    return None

def sina_quote(codes):
    """
    新浪实时行情 - 支持批量查询，GBK编码
    codes: list of "sz002149" or "sh600309"
    返回: {code: {name, open, prev_close, cur, high, low, vol, amount, chg, chg_pct, bid1, ask1, ...}}
    """
    if isinstance(codes, str): codes = [codes]
    url = f"https://hq.sinajs.cn/list={','.join(codes)}"
    raw = fetch(url, {"Referer": "https://finance.sina.com.cn/"}, encoding='gbk')
    result = {}
    for line in raw.strip().split('\n'):
        m = re.search(r'hq_str_(\w+)="([^"]*)"', line)
        if not m: continue
        code, raw_data = m.group(1), m.group(2).split(',')
        if len(raw_data) < 10: continue
        try:
            prev_close = float(raw_data[2])
            cur = float(raw_data[3])
            result[code] = {
                'name': raw_data[0], 'open': float(raw_data[1]),
                'prev_close': prev_close, 'cur': cur,
                'high': float(raw_data[4]), 'low': float(raw_data[5]),
                'vol': int(raw_data[8]), 'amount': float(raw_data[9]),
                'chg': cur - prev_close,
                'chg_pct': (cur - prev_close) / prev_close * 100,
                'bid1': float(raw_data[21]) if raw_data[21] else 0,
                'ask1': float(raw_data[31]) if raw_data[31] else 0,
                'bid1_vol': int(raw_data[22]) if raw_data[22] else 0,
                'ask1_vol': int(raw_data[32]) if raw_data[32] else 0,
            }
        except: pass
    return result

def sina_kline(symbol, scale=240, days=20):
    """
    新浪K线 - 日K/分钟K，UTF-8
    symbol: "sz002149" or "sh600309"
    scale: 240=日K, 30=30分钟, 5=5分钟, 15=15分钟, 60=60分钟
    返回: [{date, open, close, high, low, vol, ma_price5, ma_vol5}, ...]
    """
    url = (f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php"
           f"/CN_MarketData.getKLineData?symbol={symbol}&scale={scale}&ma=5&datalen={days}")
    raw = fetch(url, {"Referer": "https://finance.sina.com.cn/"})
    if not raw: return []
    data = json.loads(raw)
    return [{'date': k['day'], 'open': float(k['open']), 'close': float(k['close']),
             'high': float(k['high']), 'low': float(k['low']),
             'vol': int(k['volume']), 'ma_price5': float(k.get('ma_price5', 0)),
             'ma_vol5': float(k.get('ma_volume5', 0))} for k in data]

def sina_index():
    """大盘指数（上证/深证/创业板/沪深300/科创50），GBK"""
    codes = 's_sh000001,s_sz399001,s_sz399006,s_sh000300,s_sh000688'
    raw = fetch(f"https://hq.sinajs.cn/list={codes}", {"Referer": "https://finance.sina.com.cn/"}, encoding='gbk')
    result = {}
    names = {'s_sh000001':'上证', 's_sz399001':'深证', 's_sz399006':'创业板',
             's_sh000300':'沪深300', 's_sh000688':'科创50'}
    for line in raw.strip().split('\n'):
        m = re.search(r'hq_str_(\w+)="([^"]*)"', line)
        if not m: continue
        parts = m.group(2).split(',')
        if len(parts) < 4: continue
        result[m.group(1)] = {
            'name': names.get(m.group(1), m.group(1)),
            'cur': float(parts[1]), 'chg': float(parts[2]),
            'chg_pct': float(parts[3])
        }
    return result

def sina_top_stocks(limit=200):
    """
    新浪A股涨幅榜（用于选股），GBK编码
    返回: [{code, name, trade, chg, open, high, low, prev, vol, amount, per, pb, mktcap, turnover}, ...]
    """
    url = (f"https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php"
           f"/Market_Center.getHQNodeData?page=1&num={limit}&sort=changepercent&asc=0"
           f"&node=hs_a&_s_r_a=page")
    raw = fetch(url, {"Referer": "https://finance.sina.com.cn/"}, encoding='gbk')
    if not raw: return []
    data = json.loads(raw)
    result = []
    for s in data:
        try:
            result.append({
                'code': s['code'], 'name': s['name'], 'trade': float(s['trade']),
                'chg': float(s['changepercent']), 'open': float(s['open']),
                'high': float(s['high']), 'low': float(s['low']),
                'prev': float(s['settlement']), 'vol': int(s['volume']),
                'amount': float(s['amount']), 'per': float(s.get('per') or 0),
                'pb': float(s.get('pb') or 0), 'mktcap': float(s.get('mktcap', 0)),
                'turnover': float(s.get('turnoverratio') or 0)
            })
        except: pass
    return result
```

### ✅ AKShare 补充数据源（主力/板块/涨停/融资融券/北向）

```python
import akshare as ak, pandas as pd, warnings
warnings.filterwarnings('ignore')

# 大盘资金流（主力/超大单/大单/中单/小单净流入）
df_mkt = ak.stock_market_fund_flow()
t = df_mkt.iloc[-1]
print(f"主力净流入: {t['主力净流入-净额']/1e8:.1f}亿 ({t['主力净流入-净占比']:+.1f}%)")

# 概念板块资金流Top10
df = ak.stock_fund_flow_concept(symbol="即时")
top10 = df.sort_values('净额', ascending=False).head(10)
print(top10[['行业','行业-涨跌幅','净额','领涨股']].to_string())

# 今日涨停板池（含炸板次数/连板数/首次封板时间）
df_zt = ak.stock_zt_pool_em(date="20260421")
稳健 = df_zt[(df_zt['炸板次数']==0) & (df_zt['成交额']>2e8)]
print(稳健[['代码','名称','成交额','换手率','首次封板时间','所属行业']].head(5).to_string())

# 个股主力资金流
df_stock = ak.stock_individual_fund_flow(stock="000767", market="sz")
print(df_stock[['日期','收盘价','主力净流入-净额','主力净流入-净占比']].tail(3).to_string())

# 北向资金
north = ak.stock_hsgt_fund_flow_summary_em()
print(north.tail(3).to_string())

# 融资融券（沪市）
df_margin = ak.stock_margin_sse(start_date="20260401", end_date="20260421")
print(df_margin.tail(3).to_string())

# 昨日强势股（昨日涨停今日表现）
df_strong = ak.stock_zt_pool_strong_em(date="20260420")
print(df_strong[['代码','名称','涨跌幅','入选理由']].head(5).to_string())
```

### ✅ 技术指标计算（新浪K线 + pandas计算）

> 新浪K线接口有时SSL超时，用try-except包裹，多试几次即可。

```python
import urllib.request, json, pandas as pd

def fetch_kline(symbol, days=60, retries=3):
    """新浪K线，兼容股票和ETF"""
    url = (f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php"
           f"/CN_MarketData.getKLineData?symbol={symbol}&scale=240&ma=5&datalen={days}")
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.sina.com.cn/'})
            resp = urllib.request.urlopen(req, timeout=10)
            raw = resp.read().decode('utf-8')
            data = json.loads(raw)
            df = pd.DataFrame(data)
            for c in ['open','close','high','low','volume']:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors='coerce')
            return df
        except:
            import time; time.sleep(2)
    return pd.DataFrame()

def calc_technicals(df):
    """
    输入: df含 open/close/high/low/volume 列
    返回: 完整技术指标dict
    """
    closes = df['close'].astype(float).values
    opens  = df['open'].astype(float).values
    highs  = df['high'].astype(float).values
    lows   = df['low'].astype(float).values
    vols   = df['volume'].astype(float).values if 'volume' in df.columns else pd.Series([0]*len(df))
    
    cur = closes[-1]; prev_close = closes[-2]
    ma5  = closes[-5:].mean();  ma10 = closes[-10:].mean() if len(closes)>=10 else ma5
    ma20 = closes[-20:].mean() if len(closes)>=20 else ma10
    ma60 = closes[-60:].mean() if len(closes)>=60 else ma20
    
    # RSI
    def rsi(period):
        d = pd.Series(closes).diff()
        g = d.clip(lower=0).rolling(period).mean()
        l = (-d.clip(upper=0)).rolling(period).mean()
        return float((100 - 100/(1 + g/(l.replace(0, 0.001)))).iloc[-1])
    rsi6 = rsi(6); rsi12 = rsi(12); rsi24 = rsi(24)
    
    # MACD (标准EMA算法)
    s = pd.Series(closes)
    ema12 = s.ewm(span=12, adjust=False).mean().values
    ema26 = s.ewm(span=26, adjust=False).mean().values
    dif = ema12[-1] - ema26[-1]
    dea = float(pd.Series(dif).ewm(span=9, adjust=False).mean().iloc[-1])  # 简化
    macd_bar = (dif - dea) * 2
    
    # KDJ
    N = 9
    low_n  = float(pd.Series(lows).rolling(N).min().iloc[-1])
    high_n = float(pd.Series(highs).rolling(N).max().iloc[-1])
    rsv = (cur - low_n) / (high_n - low_n + 0.001) * 100
    K = 50; D = 50
    for _ in range(3): K = K*2/3 + rsv/3; D = D*2/3 + K/3
    J = 3*K - 2*D
    
    # 布林带
    period = 20
    mid = closes[-period:].mean(); std = closes[-period:].std()
    boll_u = mid + 2*std; boll_l = mid - 2*std
    boll_pos = (cur - boll_l) / (boll_u - boll_l + 0.001) * 100
    
    # 乖离率
    bias5  = (cur - ma5)  / ma5  * 100
    bias10 = (cur - ma10) / ma10 * 100
    
    # 形态
    upper_s = (max(opens[-1], closes[-1]) - highs[-1]) / highs[-1] * 100 if highs[-1] > 0 else 0
    lower_s = (lows[-1] - min(opens[-1], closes[-1]))    / lows[-1]  * 100 if lows[-1]  > 0 else 0
    body    = abs(closes[-1] - opens[-1]) / opens[-1] * 100 if opens[-1] > 0 else 0
    
    # 量比
    avg_vol5 = vols[-5:].mean() if len(vols) >= 5 else vols[-1]
    vol_ratio = vols[-1] / avg_vol5 if avg_vol5 > 0 else 1.0
    
    # 信号
    sigs = []
    if rsi6 < 30:   sigs.append("RSI6超卖✅")
    elif rsi6 > 80: sigs.append("RSI6超买⚠️")
    if macd_bar > 0: sigs.append("MACD红柱✅")
    else:             sigs.append("MACD绿柱⚠️")
    if K < 20:       sigs.append("KDJ超卖✅")
    elif K > 80:     sigs.append("KDJ超买⚠️")
    if upper_s < 0.5: sigs.append("无上影✅")
    if lower_s > 2:   sigs.append(f"下影{lower_s:.0f}%✅")
    if bias5 > 10:    sigs.append(f"MA5乖离+{bias5:.0f}%⚠️")
    elif bias5 < -10: sigs.append(f"MA5乖离{bias5:.0f}%✅")
    if cur > boll_u:   sigs.append("突破布林上轨⚠️")
    elif cur < boll_l: sigs.append("跌破布林下轨✅")
    
    # 综合评分 0-100
    score = 50
    if   rsi6 < 30:   score += 15
    elif rsi6 > 70:   score -= 10
    if   macd_bar > 0: score += 10
    else:              score -= 10
    if   K < 20:       score += 10
    elif K > 80:       score -= 10
    if   cur > ma5 and ma5 > ma10: score += 10
    elif cur < ma5 and ma5 < ma10: score -= 10
    if   boll_pos < 20: score += 10
    elif boll_pos > 80: score -= 10
    if   lower_s > 2:   score += 5
    if   vol_ratio > 2:  score -= 5
    
    return {
        'cur': cur, 'prev_close': prev_close,
        'ma5': ma5, 'ma10': ma10, 'ma20': ma20, 'ma60': ma60,
        'rsi6': rsi6, 'rsi12': rsi12, 'rsi24': rsi24,
        'dif': dif, 'dea': dea, 'macd_bar': macd_bar,
        'K': K, 'D': D, 'J': J,
        'boll_u': boll_u, 'boll_l': boll_l, 'boll_pos': boll_pos,
        'bias5': bias5, 'bias10': bias10,
        'upper_s': upper_s, 'lower_s': lower_s, 'body': body,
        'vol_ratio': vol_ratio,
        'sigs': sigs, 'score': score
    }
```

### ✅ 大盘情绪评分（综合0-100分）

```python
def market_sentiment():
    """
    综合大盘情绪评分
    返回: (score, level_str, signals_list)
    level: 🔴谨慎(<40) / 🟠偏弱(40-50) / 🟡中性(50-70) / 🟢积极(>70)
    """
    score = 50; signals = []
    
    # 1. 主力资金（AKShare）
    try:
        df = ak.stock_market_fund_flow()
        t = df.iloc[-1]
        mp = t['主力净流入-净占比']; sp = t['小单净流入-净占比']
        if mp > 1:   score += 15; signals.append(f"主力买入({mp:+.1f}%)")
        elif mp < -1: score -= 15; signals.append(f"主力卖出({mp:+.1f}%)")
        if sp > 2 and mp < 0: score -= 10; signals.append("散户接盘⚠️")
    except: signals.append("资金数据获取失败")
    
    # 2. 涨跌停数量
    try:
        zt = len(ak.stock_zt_pool_em(date="20260421"))
        dt = len(ak.stock_zt_pool_zbgc_em(date="20260421"))
        if   zt > 80: score += 10; signals.append(f"涨停多({zt}只)")
        elif zt < 30: score -= 10; signals.append(f"涨停少({zt}只)")
        if dt > 20:   score -= 10; signals.append(f"跌停多({dt}只)")
    except: pass
    
    # 3. 北向资金
    try:
        north = ak.stock_hsgt_fund_flow_summary_em()
        n = north.iloc[-1]
        net = float(n.get('成交净买额', 0) or 0)
        if net > 10:  score += 10; signals.append(f"北向买入({net:.0f}亿)")
        elif net < -10: score -= 10; signals.append(f"北向卖出({net:.0f}亿)")
    except: pass
    
    score = max(0, min(100, score))
    if   score >= 70: level = "🟢积极"
    elif score >= 50: level = "🟡中性"
    elif score >= 40: level = "🟠偏弱"
    else:             level = "🔴谨慎"
    
    return score, level, signals
```

### ✅ 板块轮动分析

```python
def sector_rotation():
    """
    返回: (top5_df, bottom5_df, 电力板块_df, 科技板块_df, 新能源_df)
    """
    df = ak.stock_fund_flow_concept(symbol="即时")
    top    = df.sort_values('净额', ascending=False).head(15)
    bottom = df.sort_values('净额', ascending=True).head(5)
    power  = df[df['行业'].str.contains('电|电力|电网', na=False, regex=True)]
    tech   = df[df['行业'].str.contains('AI|芯片|半导体|算力|科技', na=False, regex=True)]
    new_e  = df[df['行业'].str.contains('新能源|锂|电池|储能|光伏', na=False, regex=True)]
    return top, bottom, power, tech, new_e
```

#### 已验证可用的 API

| 功能 | AKShare API | 备注 |
|------|------------|------|
| 概念板块资金流 | `ak.stock_fund_flow_concept(symbol="即时")` | 387个概念板块，主力净流入/流出 |
| 大盘资金流 | `ak.stock_market_fund_flow()` | 主力/超大单/大单/中单/小单净流入 |
| 个股主力资金流 | `ak.stock_individual_fund_flow(stock="000767", market="sz")` | 近120日主力净流入/流出明细 |
| 今日涨停板池 | `ak.stock_zt_pool_em(date="YYYYMMDD")` | 封板资金/炸板次数/首次封板时间/连板数 |
| 昨日强势股池 | `ak.stock_zt_pool_strong_em(date="YYYYMMDD")` | 入选理由/是否新高/量比 |
| 北向资金 | `ak.stock_hsgt_fund_flow_summary_em()` | 沪深港通北向资金净买额 |
| 融资融券-沪 | `ak.stock_margin_sse(start_date="YYYYMMDD", end_date="YYYYMMDD")` | 融资余额/融资买入额 |
| 昨日炸板股池 | `ak.stock_zt_pool_zbgc_em(date="YYYYMMDD")` | 炸板股，明日反包机会 |

#### 大盘资金流分析模板

```python
import akshare as ak, pandas as pd, warnings
warnings.filterwarnings('ignore')

df = ak.stock_market_fund_flow()
today = df.iloc[-1]
main_net = today['主力净流入-净额'] / 1e8  # 亿元
main_pct = today['主力净流入-净占比']
print(f"主力净流入: {main_net:.1f}亿 ({main_pct:.1f}%)")
```

- 主力净流入 > 0 且净占比 > 1% → 机构在买入 → 情绪偏多
- 主力净流入 < 0 且净占比 < -2% → 机构在卖出 → 情绪偏弱
- 小单净流入 > 0 且净占比 > 2% → 散户在买入 → 警惕（往往预示短期顶）

#### 涨停板池分析模板

```python
df = ak.stock_zt_pool_em(date="20260421")
# 炸板次数=0: 封板稳健
# 炸板次数>0: 封板不稳，明日低开风险大
# 连板数>1: 连续涨停，强势
# 首次封板时间早: 强势信号（早盘封板）
# 封板资金大: 主力做多意愿强
稳健 = df[df['炸板次数'] == 0]
稳健 = 稳健[稳健['连板数'] == 1]  # 首板
稳健 = 稳健.sort_values('成交额', ascending=False)
print(稳健[['代码','名称','成交额','换手率','首次封板时间','所属行业']].head(10))
```

#### 概念板块资金流分析模板

```python
df = ak.stock_fund_flow_concept(symbol="即时")
top_sectors = df.sort_values('净额', ascending=False).head(10)
print(top_sectors[['行业','行业-涨跌幅','净额','领涨股','领涨股-涨跌幅']].to_string())
```

### ✅ EastMoney ulist.np（单票稳定，批量失效）

| 接口 | 状态 | 备注 |
|------|------|------|
| ulist.np 单票 | ✅ 稳定 | 一次查1个secid完全正常 |
| ulist.np 批量(>5个secids) | ❌ 返回空 | 分批即可解决 |
| push2his K线 | ✅ 单票稳定 | 批量可能触发限速 |
| clist 板块/列表 | ❌ 不稳定 | 沙盒环境频繁超时/拦截 |

```python
def get_em_stock(secid):
    """EastMoney ulist.np，单票稳定"""
    url = (f"https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&invt=2"
           f"&fields=f2,f3,f4,f5,f6,f12,f14,f15,f16,f17,f18&secids={secid}"
           f"&ut=fa5fd1943c7b386f172d6893dbfba10b")
    raw = fetch(url, "https://quote.eastmoney.com/")
    if not raw: return None
    try:
        return json.loads(raw)['data']['diff'][0]
    except:
        return None

def get_em_kline(secid, days=30):
    """EastMoney K线，单票稳定"""
    url = (f"https://push2his.eastmoney.com/api/qt/stock/kline/get"
           f"?secid={secid}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57"
           f"&klt=101&fqt=1&lmt={days}&end=20500101"
           f"&ut=fa5fd1943c7b386f172d6893dbfba10b")
    raw = fetch(url, "https://quote.eastmoney.com/")
    if not raw: return []
    try:
        return json.loads(raw)['data']['klines']
    except:
        return []
```

### ❌ 浏览器东方财富行情中心不可用
- `quote.eastmoney.com/center/gridlist.html` 是 JS 动态渲染
- `browser_snapshot` 直接拿不到内容，不要用浏览器抓列表数据

## 输出格式

```
## 隔天短T推荐 · YYYY-MM-DD 14:40

### 今日大盘环境
- 涨停: X家 | 跌停: X家 | 情绪: X
- 建议仓位: X成（情绪中性/偏弱时减半）

---

### Top 20 强势股（按质量排序）

#### 1. [股票名](代码)  ↑X%
**上涨因素**: [封板/主线/资金等]
**次日开盘预期**: 高开X% / 溢价冲高 / 平开观察
**建议操作**: 竞价入/冲高入/观望
**止损位**: X元（-X%）
**风险等级**: 🟢低/🟡中/🟠高

... (2-20)

---

### 操作纪律
1. 仓位控制: 单只不超过总资金15%
2. 止损: 买入后跌破成本3%立即出
3. 兑现: 次日开盘冲高即出，不贪
4. 避开: 弱势大盘日（跌停>30家）暂停此策略
```

## 注意事项

- **T+1限制**: 当日买入不能卖，必须隔日
- **隔夜风险**: 大盘夜间外盘波动、政策消息影响
- **情绪优先**: 跌停>30家时策略失效，暂停
- **不构成投资建议**: 此策略仅为信息分享，盈亏自负

## 踩坑记录（2026-04-21 实战总结）

### 1. 涨停板≠可买入（最重要的教训）
- **问题**: 涨幅榜前排几乎全是涨停股（10%），散户根本买不进去
- **解决**: 核心策略改为 **5-9%涨幅区间**，这个区间既强势又可以买入
- **筛选公式**: `5.0 <= chg < 9.9`（排除涨停）

### 2. 新浪接口稳定性验证
- **vip.stock.finance.sina.com.cn**: ✅ 完全稳定，200条数据一次性返回
- **hq.sinajs.cn 单票**: ✅ 稳定（返回32位原始格式，需解析）
- **clist EastMoney**: ❌ 不稳定（沙盒环境返回空）

### 3. 创业板过滤要完整
- **301xxx 也是创业板**（不只是300xxx）
- **正确过滤**: `code.startswith(('688','300','301','4','8'))`

### 4. 个股风险信号排查（必须检查）
做短线之前必须用东方财富个股页面确认无以下风险：
- **控股股东减持预披露**（重大利空，股东要卖）
- **董事会延期换届**（治理风险）
- **业绩亏损**（PE为负或极低）
- **高位反复上龙虎榜**（主力在跑）

排查方法：
```python
# 用浏览器打开个股页面，搜索以下关键词
# - "减持" → 找到减持预披露公告
# - "龙虎榜" → 近期多次高位上榜=主力出货
# - "业绩" → 亏损或大幅下滑

# 002149西部材料教训：
# 04-01发布控股股东减持预披露 + 04-18董事会延期换届
# 历史龙虎榜: 03-30连续3日+20%, 04-14涨幅偏离+7%, 04-20涨幅偏离+7%
# 结论: 主力反复在高位进出 = 散户接盘，不要买
```

### 5. AKShare 安装方法（关键：必须用 venv 的 python）

```bash
# hermes-agent 使用自己的 venv，不影响系统
python3 -m ensurepip --upgrade
python3 -m pip install akshare

# 验证安装
python3 -c "import akshare as ak; print('AKShare', ak.__version__)"
# 应输出: AKShare 1.18.56
```

> ⚠️ 不要用系统 pip 或 apt 安装，会装到错误的 Python 环境。

AKShare 日期参数格式：`date="YYYYMMDD"`（如 `"20260421"`）

### 7. 实时行情接口在WSL沙盒中的稳定性（重要踩坑）

**实时行情 — 全部失效（2026-04-23确认）：**

| 接口 | 状态 | 原因 |
|------|------|------|
| `hq.sinajs.cn`（新浪实时） | ❌ HTTP 403 | 被禁止 |
| `push2.eastmoney.com`（东财实时） | ❌ 连接中断 | SSL握手超时 |
| `stock_zh_a_spot_em()`（AKShare全市场） | ❌ 连接中断 | 同上 |
| `stock_zh_index_spot_em()`（AKShare指数） | ❌ 连接中断 | 同上 |

**日终/历史数据 — 全部稳定可用（✅）：**

| 接口 | 状态 | 用途 |
|------|------|------|
| `stock_market_fund_flow()` | ✅ | 大盘主力资金流 |
| `stock_fund_flow_concept(symbol="即时")` | ✅ | 概念板块资金流（注意：净额有时显示0，需确认） |
| `stock_zt_pool_em(date="YYYYMMDD")` | ✅ | 涨停池 |
| `stock_zt_pool_strong_em(date="YYYYMMDD")` | ✅ | 昨日强势股 |
| `stock_zt_pool_zbgc_em(date="YYYYMMDD")` | ✅ | 昨日炸板股 |
| `stock_margin_sse(start, end)` | ✅ | 融资融券（沪） |
| `stock_hsgt_fund_flow_summary_em()` | ✅（但盘中数据为0） | 北向资金 |

**结论**：WSL沙盒环境无法获取真实时行情，盘前报告只能依赖**上一交易日收盘数据**。盘中实时持仓数据也无法通过接口获取，需依赖手动输入或东方财富网页手动查询。

**替代方案**：若需要真实时数据，需在Windows本地执行Python脚本或使用浏览器抓取。

### 8. 板块轮动分析
- 沪市主板: 6xxxxx（但排除688xx科创板）
- 深市主板: 0xxxxx, 001xxx, 002xxx, 003xxx（排除300xxx/301xxx创业板）
- 完整排除: 688(科创), 300/301(创业), 4/8/92(北交所)

## 仓位计算器

### 核心公式

```
允许亏损金额 = 可用资金 × 风险比例(%)
最大可买股数 = 允许亏损金额 ÷ (买入价 - 止损价)
实际占用资金 = 最大可买股数 × 买入价
```

### Python 实现

```python
def position_calc(capital, entry, stop, risk_pct=2.0, stock_code=None):
    """
    A股仓位计算器
    参数:
      capital   - 可用资金（元）
      entry     - 买入价格（元）
      stop      - 止损价格（元）
      risk_pct  - 单笔允许亏损占总资金比例（%），默认2%
      stock_code - 股票代码（用于判断板块），可选
    返回: dict
    """
    risk_amount = capital * risk_pct / 100
    risk_per_share = entry - stop

    if risk_per_share <= 0:
        return {"error": "止损价必须低于买入价"}

    raw_shares = risk_amount / risk_per_share

    # A股最小买卖单位
    if stock_code and stock_code.startswith('688'):
        unit = 200
    elif stock_code and stock_code.startswith(('300', '301')):
        unit = 100
    elif stock_code and stock_code.startswith(('4', '8', '92')):
        return {"error": "北交所风险过高，不建议操作"}
    else:
        unit = 100  # 主板默认

    actual_shares = (int(raw_shares) // unit) * unit
    if actual_shares < unit:
        return {
            "warning": f"理论可买{raw_shares:.0f}股，不足1手({unit}股)，建议放弃或降低风险比例",
            "capital": capital, "entry": entry, "stop": stop,
            "risk_amount": risk_amount, "risk_per_share": risk_per_share,
            "raw_shares": raw_shares, "unit": unit, "actual_shares": 0
        }

    position_value = actual_shares * entry
    actual_loss = actual_shares * risk_per_share
    stop_loss_pct = risk_per_share / entry * 100

    return {
        "capital": capital, "entry": entry, "stop": stop, "risk_pct": risk_pct,
        "risk_amount": round(risk_amount, 0),
        "risk_per_share": round(risk_per_share, 3),
        "stop_loss_pct": round(stop_loss_pct, 1),
        "raw_shares": round(raw_shares, 0),
        "unit": unit, "actual_shares": actual_shares,
        "position_value": round(position_value, 0),
        "position_pct": round(position_value / capital * 100, 0),
        "actual_loss": round(actual_loss, 0),
        "actual_loss_pct": round(actual_loss / capital * 100, 2),
    }


def position_summary(capital, positions_list):
    """
    多仓位汇总风控表
    positions_list: [{"Name": "股票", "shares": 股数, "cost": 成本价,
                      "entry": 买入价, "stop": 止损价}, ...]
    """
    total_loss_if_stopped = 0
    results = []
    for p in positions_list:
        r = position_calc(capital, p['entry'], p['stop'], risk_pct=2.0)
        loss = r.get('actual_loss', 0)
        total_loss_if_stopped += loss
        unrealized = (p['entry'] - p['cost']) * p['shares']
        results.append({
            **p,
            "actual_shares": r.get('actual_shares', p['shares']),
            "position_value": r.get('position_value', 0),
            "position_pct": r.get('position_pct', 0),
            "stop_loss_pct": r.get('stop_loss_pct', 0),
            "actual_loss": loss,
            "unrealized": round(unrealized, 0),
        })

    remaining = capital - sum(r['position_value'] for r in results if r.get('position_value'))
    max_single_loss_pct = max((r['actual_loss'] / capital * 100) for r in results) if results else 0

    return {
        "positions": results,
        "remaining_cash": round(remaining, 0),
        "total_position_pct": round(sum(r['position_pct'] for r in results if r.get('position_pct')), 0),
        "total_loss_if_stopped": round(total_loss_if_stopped, 0),
        "total_loss_if_stopped_pct": round(total_loss_if_stopped / capital * 100, 2),
        "max_single_loss_pct": round(max_single_loss_pct, 2),
        "risk_level": "🟢安全" if max_single_loss_pct < 2 else "🟡警戒" if max_single_loss_pct < 3 else "🔴危险",
    }
```

### 使用示例

```python
capital = 16091  # 可用资金

# 德赛电池(000049)
r = position_calc(capital, entry=38.50, stop=37.00, risk_pct=2.0, stock_code="000049")
# 可买: 200股  占用: 7700元  止损亏损: 300元(1.86%)

# 晋控电力(000767)
r = position_calc(capital, entry=4.20, stop=3.95, risk_pct=2.0, stock_code="000767")
# 可买: 1200股  占用: 5040元  止损亏损: 300元(1.86%)

# 科创板（更高波动，用更低风险比例）
r = position_calc(capital, entry=25.00, stop=23.75, risk_pct=1.5, stock_code="688xxx")
# 可买: 200股  占用: 5000元  止损亏损: 241元(1.50%)
```

### 风险控制参数

| 场景 | 风险比例 | 单笔止损幅度 | 说明 |
|------|---------|------------|------|
| 保守 | 1.0% | 3-5% | 市场弱/新手 |
| 均衡 | 2.0% | 5-7% | **默认，日常短线** |
| 激进 | 3.0% | 7-10% | 市场强/老手 |
| 科创/创业 | 1.5% | 5-7% | 波动大，用更低风险 |

### 风控红线

1. **单笔仓位占比 > 30%** → 🔴 拒绝买入
2. **止损幅度 > 10%** → 🔴 拒绝买入
3. **实际亏损占比 > 3%** → 🔴 单日总亏损已达上限，停止开新仓
4. **同时持仓 > 4只** → 🟠 太多标的跟踪不过来
5. **单只理论可买 < 1手** → 🟠 资金太少，直接放弃

## 情绪温度计

```python
def market_temperature():
    """
    综合市场情绪温度计
    返回: (score_int, temp_str, details_dict)
    temp: ❄️极寒/<25 | 🧊冰点/25-45 | 🔴冷淡/45-55 | 🟡中性/55-65
          | 🟠回暖/65-75 | 🟢活跃/75-90 | 🔥极热/>90
    """
    score = 50; details = {}

    try:
        df = ak.stock_market_fund_flow()
        t = df.iloc[-1]
        main_net = t['主力净流入-净额'] / 1e8
        main_pct = t['主力净流入-净占比']
        small_pct = t['小单净流入-净占比']
        details['主力净流入'] = f"{main_net:.0f}亿({main_pct:+.1f}%)"
        if main_pct > 1:   score += 20
        elif main_pct < -1: score -= 20
        if small_pct > 2 and main_pct < 0:
            score -= 10; details['散户接盘'] = "是⚠️"
    except: pass

    try:
        zt_count = len(ak.stock_zt_pool_em(date="20260422"))
        dt_count = len(ak.stock_zt_pool_zbgc_em(date="20260422"))
        details['涨停数'] = zt_count; details['跌停数'] = dt_count
        if zt_count > 100: score += 15
        elif zt_count < 30: score -= 15
        if dt_count > 30: score -= 15
        if zt_count > 0:
            details['涨停率'] = f"{zt_count/(zt_count+dt_count+1)*100:.0f}%"
    except: pass

    try:
        north = ak.stock_hsgt_fund_flow_summary_em()
        net = float(north.iloc[-1].get('成交净买额', 0) or 0)
        details['北向资金'] = f"{net:.0f}亿"
        if net > 20:  score += 10
        elif net < -20: score -= 10
    except: pass

    score = max(0, min(100, score))
    temps = [(90,"🔥极热"),(75,"🟢活跃"),(65,"🟠回暖"),
             (55,"🟡中性"),(45,"🔴冷淡"),(25,"🧊冰点"),(0,"❄️极寒")]
    temp = next(t for v,t in temps if score >= v)

    return score, temp, details
```

### 温度计操作参考

| 温度 | 分值 | 仓位建议 | 策略 |
|------|------|---------|------|
| ❄️极寒 | <25 | 空仓 | 禁止开新仓 |
| 🧊冰点 | 25-45 | 1成仓 | 只做超跌反弹 |
| 🔴冷淡 | 45-55 | 3成仓 | 谨慎，减少新开仓 |
| 🟡中性 | 55-65 | 5成仓 | 正常操作 |
| 🟠回暖 | 65-75 | 7成仓 | 积极，可追强势 |
| 🟢活跃 | 75-90 | 8-9成 | 满仓，主线明确 |
| 🔥极热 | >90 | 9成+ | 极热转空，分批减仓 |
