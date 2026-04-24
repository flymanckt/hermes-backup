---
name: a-share-alpha-signals
description: A股特有的短线情绪指标、资金结构、涨跌停分析、龙虎榜、主力资金追踪。适用于事件驱动和短线择时。核心理念：A股纯看基本面失真，资金和情绪才是第一驱动。
triggers:
  - "涨跌停"
  - "情绪"
  - "龙虎榜"
  - "主力资金"
  - "短线"
  - "打板"
  - "炸板"
  - "融资融券"
  - "北向资金"
---

# A股短线情绪与资金分析

## A股特殊制度背景

A股和美股/港股最大的区别：**制度约束导致的博弈结构**。

| 制度 | 说明 | 分析含义 |
|------|------|----------|
| 涨跌停板 | ±10%（主板）、±20%（科创/创业）、±5%（ST） | 涨停是稀缺资源，代表情绪最强点 |
| T+1 | 当日买不能当日卖 | 打板资金次日才能出，炸板代价大 |
| 龙虎榜 | 日涨幅±7%或换手率>20%上榜 | 追踪营业部席位，判断主力行为 |
| 涨跌停家数 | 市场情绪温度计 | 跌停>30家=极弱，跌停<5家=偏强 |

**基本面在A股只能排第三，前两个是资金和情绪。**

## 1. 涨跌停数据（东方财富）

```python
import urllib.request, json, re

def get_limit_up():
    """今日涨停股池"""
    url = ("https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=100&po=1&np=1&fltt=2&invt=2"
           "&fid=f3&fs=m:0+t:6,m:0+t:13,m:1+t:2,m:1+t:23&fields=f2,f3,f12,f14,f15,f62&ut=fa5fd1943c7b386f172d6893dbfba10b")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10)
    raw = resp.read().decode('utf-8')
    json_str = re.sub(r'jQuery[\d\w_]*\((.*)\)', r'\1', raw)
    data = json.loads(json_str)
    stocks = data.get('data', {}).get('diff', [])
    print(f"今日涨停: {len(stocks)}家")
    for s in stocks[:10]:
        print(f"  {s['f14']}({s['f12']}): +{s['f3']}%")
    return stocks

def get_limit_down():
    """今日跌停股池"""
    url = ("https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=100&po=1&np=1&fltt=2&invt=2"
           "&fid=f3&fs=m:0+t:7,m:0+t:14,m:1+t:3,m:1+t:24&fields=f2,f3,f12,f14&ut=fa5fd1943c7b386f172d6893dbfba10b")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10)
    raw = resp.read().decode('utf-8')
    json_str = re.sub(r'jQuery[\d\w_]*\((.*)\)', r'\1', raw)
    data = json.loads(json_str)
    stocks = data.get('data', {}).get('diff', [])
    print(f"今日跌停: {len(stocks)}家")
    return stocks
```

## 2. 主力资金净流入

```python
def get_mainfund_flow(secid):
    """
    获取单只股票主力净流入
    secid: 1.600156 (沪市) 或 0.002969 (深市)
    """
    url = (f"https://push2.eastmoney.com/api/qt/stock/get?fltt=2&invt=2&fields=f2,f3,f12,f14,f62,f184&secid={secid}&ut=fa5fd1943c7b386f172d6893dbfba10b")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read().decode('utf-8'))['data']
    
    main_net = data.get('f62', 0) or 0  # 主力净流入（元）
    main_pct = data.get('f184', 0) or 0  # 主力净流入占比%
    
    level = "强流入" if main_pct > 5 else "中流入" if main_pct > 2 else "弱流出" if main_pct > -2 else "强流出"
    return {
        "stock": data['f14'],
        "main_net_yuan": main_net,
        "main_net_wan": round(main_net / 10000, 0),
        "main_pct": main_pct,
        "level": level
    }
```

## 3. 融资融券（杠杆资金）

融资余额=借钱买股（多头力量）
融券余额=借股做空（空头力量）
融资余额持续增加=做多情绪强

```python
def get_margin(symbol, count=5):
    """融资融券近5日"""
    url = (f"https://datacenter-web.eastmoney.com/api/data/v1/get?callback=jQuery&sortColumns=MARGIN_DATE&sortTypes=-1"
           f"&pageSize={count}&pageIndex=1&reportName=RPT_MUTUAL_FUND_DETAILS&columns=ALL"
           f"&filter=(SECUCODE%3D%22{symbol}.SH%22%20OR%20SECUCODE%3D%22{symbol}.SZ%22)")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10)
    raw = resp.read().decode('utf-8')
    json_str = re.sub(r'jQuery[\d\w_]*\((.*)\)', r'\1', raw)
    data = json.loads(json_str)
    items = data.get('result', {}).get('data', [])
    
    for item in items:
        rzye = int(item.get('RZYE') or 0)
        rqye = int(item.get('RQYE') or 0)
        print(f"{item['MARGIN_DATE']}: 融资={rzye/10000:.0f}万 融券={rqye/10000:.0f}万")
```

## 4. 北向资金（沪深港通持股变化）

```python
def get_hsgt(symbol, count=5):
    """北向资金持股变化"""
    url = (f"https://datacenter-web.eastmoney.com/api/data/v1/get?sortColumns=HOLD_DATE&sortTypes=-1"
           f"&pageSize={count}&pageIndex=1&reportName=RPT_MUTUAL_FUND_SH&columns=ALL"
           f"&filter=(SECUCODE%3D%22{symbol}.SH%22%20OR%20SECUCODE%3D%22{symbol}.SZ%22)")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read().decode('utf-8'))
    items = data.get('result', {}).get('data', [])
    for item in items:
        print(f"{item['HOLD_DATE']}: 持股={item['SHARES']}万股 占流通={item['HOLD_RATIO']}%")
```

## 5. 情绪判断框架

### 涨跌停家数情绪表

| 状态 | 涨停家数 | 跌停家数 | 市场含义 |
|------|----------|----------|----------|
| 极弱 | <10 | >30 | 恐慌蔓延，空头主导 |
| 偏弱 | 10-30 | 15-30 | 情绪低迷，观望 |
| 中性 | 30-50 | 5-15 | 正常结构 |
| 偏强 | 50-80 | <5 | 情绪回暖 |
| 极强 | >80 | <3 | 主升浪，全面做多 |

### 主力行为 K线对照

| 形态 | 技术特征 | 主力意图 |
|------|----------|----------|
| 缩量涨停 | 封板量小，换手低 | 主力控盘锁仓，持股待涨 |
| 天量涨停 | 成交量历史最高 | 主力出货！次日必跌 |
| 高开低走爆量 | 冲高回落+巨量 | 主力出货，不要追 |
| 低位长下影线 | 盘中深跌后拉回 | 试探支撑/吸筹 |
| 尾盘急拉 | 14:30后快速拉升 | 做收盘价骗线 |
| 连续一字板后T字板 | 巨量换手 | 主力砸盘前兆 |

### A股出货形态（绝不能买）

```
高位天量 + 高开低走 + 长上影线 = 主力出货
连续拉升后出现 阴包阳（跌停覆盖昨日涨停）= 情绪极弱
一字板打开后快速封回 + 换手>30% = 主力对敲，离场
```

## 6. 短线择时综合评分

```python
def short_score(secid, price, ma5, ma10, ma20, vol_ratio, main_pct, limit_up=False):
    """
    短线综合评分（0-100）
    趋势(30分) + 资金(30分) + 情绪(20分) + 形态(20分)
    """
    score = 50
    factors = []
    
    # 趋势评分
    if price > ma5 > ma10 > ma20:
        score += 20
        factors.append("均线多头(+20)")
    elif price > ma20 and ma5 > ma10:
        score += 10
        factors.append("偏强整理(+10)")
    elif price < ma5 < ma10:
        score -= 15
        factors.append("均线空头(-15)")
    
    # 资金评分
    if main_pct > 5:
        score += 20
        factors.append("主力强流入(+20)")
    elif main_pct > 2:
        score += 10
        factors.append("主力中流入(+10)")
    elif main_pct < -5:
        score -= 20
        factors.append("主力强流出(-20)")
    
    # 情绪评分
    if limit_up:
        score += 15
        factors.append("涨停(+15)")
    
    # 量价形态
    if vol_ratio > 3:
        score -= 10
        factors.append("异常放量(-10)")
    elif vol_ratio > 2:
        score -= 5
        factors.append("放量过大(-5)")
    
    level = "极强" if score >= 85 else "强" if score >= 70 else "中性" if score >= 40 else "弱" if score >= 25 else "极弱"
    return {"score": score, "level": level, "factors": factors}
```

## A股短线纪律（绝对红线）

1. **没有主线不追高**——全市场无明确热点时，涨停板次日溢价率极低
2. **炸板率>50%不接力**——昨日涨停今日一半炸板=情绪退潮
3. **跟风股快进快出**——非龙头最多持有一天，次日不板就走
4. **高位放量阴线不抄底**——这是主力出货，不是回调
5. **没有止损位不买入**——买入前必须先想好止损价格

## 实际使用例子

华升股份（600156）：
- 今日爆量2.24x + 高开低走 → 主力出货嫌疑 → **短线不能买**
- 均线多头但价格偏离MA20 33% → 正常回调空间充足
- 结论：**等回调到MA5(9.26)附近再考虑，中线可等**
