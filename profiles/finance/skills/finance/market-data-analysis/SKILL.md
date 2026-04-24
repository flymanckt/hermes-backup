---
name: market-data-analysis
description: A股大盘与板块分析 — 指数行情、市场情绪、资金流向、板块轮动。配合 eastmoney-stock-fetch 使用。
triggers:
  - "大盘分析"
  - "市场情绪"
  - "板块资金"
  - "行业轮动"
---

# A股大盘与板块分析

## 数据获取

### 1. 大盘指数（EastMoney ulist API）

```python
import urllib.request, json

# 常用指数 secids
indices = {
    "上证指数": "1.000001",
    "深证成指": "0.399001",
    "创业板指": "0.399006",
    "沪深300": "1.000300",
    "中小100": "0.399005",
    "科创50": "1.000688",
    "上证50": "1.000016",
}

secids = ",".join(indices.values())
fields = "f2,f3,f4,f5,f6,f12,f14,f15,f16,f17,f18"
url = f"https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&invt=2&fields={fields}&secids={secids}&ut=fa5fd1943c7b386f172d6893dbfba10b"

req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=10)
data = json.loads(resp.read().decode('utf-8'))

for d in data['data']['diff']:
    print(f"{d['f14']}: {d['f2']} {d['f3']}% 今开={d['f15']} 最高={d['f16']} 最低={d['f17']} 昨收={d['f18']}")
```

### 2. 板块资金流向（概念/行业）

```python
import urllib.request, json

# 行业板块资金流向
url = "https://push2.eastmoney.com/api/qt/clist/get?cb=jQuery&pn=1&pz=20&po=1&np=1&fltt=2&invt=2&fid=f62&fs=m:90+t:2&fields=f2,f3,f4,f5,f6,f12,f14,f62,f184&ut=fa5fd1943c7b386f172d6893dbfba10b"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=10)
raw = resp.read().decode('utf-8')
# 返回的是 jQuery JSONP 格式，需要手动去包裹
import re
json_str = re.sub(r'jQuery\((.*)\)', r'\1', raw)
data = json.loads(json_str)
for d in data['data']['diff'][:10]:
    print(f"{d['f14']}: {d['f3']}% 主力净流入={d['f62']/10000:.0f}万")
```

### 3. 北向资金（沪深港通）

```python
import urllib.request, json

# 北向资金实时
url = "https://push2.eastmoney.com/api/qt/kamt.rtmin/get?fields=f2,f3,f4,f12,f14&ut=fa5fd1943c7b386f172d6893dbfba10b"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=10)
data = json.loads(resp.read().decode('utf-8'))
print(json.dumps(data['data'], ensure_ascii=False, indent=2))
```

## 分析框架

### 大盘环境判断（4个维度）

| 维度 | 信号 | 含义 |
|------|------|------|
| 指数涨跌幅 | 三大指数同向涨跌>0.5% | 趋势确认 |
| 高开/低走 | 今开>昨收 but 现价<今开 | 卖压强，偏弱 |
| 创业板 vs 上证 | 创业板涨幅持续落后上证>0.5% | 资金偏防守 |
| 成交量 | 相比上一交易日放大/缩量 | 趋势是否可信 |

### 强势市场特征
- 三大指数同步上涨，创业板不弱
- 成交量放大（量价齐升）
- 有明确主线板块（至少3个关联股涨停）
- 跌停板<10家

### 弱势市场特征
- 高开低走收阴
- 创业板领跌
- 成交量萎缩
- 跌停板>20家
- 北向资金持续流出

### 板块轮动判断
- 资金从创业板/科技流向主板/防御板块（消费/电力）= 偏弱
- 资金从防御板块流向科技/题材 = 情绪回暖
- 某板块连续3日资金净流入 = 主线可能形成

## 输出格式

大盘分析报告应包含：
1. **指数一览**：主要指数涨跌幅 + 走势特征（高开低走/低开高走）
2. **市场情绪判断**：强势/弱势/分化，给出强/中/弱评级
3. **主线方向**：有无明确主线，板块资金集中在哪里
4. **北向资金**：（如有数据）当日净流入方向
5. **操作建议**：当前适合补仓/持有/减仓
