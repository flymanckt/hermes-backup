---
name: eastmoney-stock-fetch
description: Fetch A-share real-time stock quotes via EastMoney API using Python urllib (not browser)
triggers:
  - "获取A股实时行情"
  - "查询股票价格"
  - "fetch stock quote"
  - "real-time stock data"
---

# EastMoney A股实时行情获取

## 核心发现
- EastMoney 的 `push2.eastmoney.com/api/qt/ulist.np/get` 接口可获取实时行情
- **Python `urllib` 直连 EastMoney 经常被阻断**（2026-04-22 实测：Remote end closed connection）
- **浏览器访问个股页面数据可能显示"-"（未刷新），不可直接依赖**
- **Sina Finance API (`hq.sinajs.cn`) 最可靠，推荐首选使用**

## 方法一：Sina Finance API（推荐首选）

```bash
curl -s "https://hq.sinajs.cn/list=sh603341,sz002969,sh603316,sh560390" \
  -H "Referer: https://finance.sina.com.cn"
```

返回格式（GBK编码，每行一只股票）：
```
var hq_str_sh603341="龙旗科技,37.510,38.760,38.100,38.160,37.130,38.100,38.110,7174093,270406628.000,...,2026-04-22,13:27:10,00";
```

字段顺序（逗号分隔，共31+字段）：
```
name, open, prev_close, current, high, low, volume(部分), ..., date, time, status
```

解析示例：
```python
import urllib.request, re

codes = "sh603341,sz002969,sh603316,sh560390"
url = f"https://hq.sinajs.cn/list={codes}"
req = urllib.request.Request(url, headers={
    'Referer': 'https://finance.sina.com.cn',
    'User-Agent': 'Mozilla/5.0'
})
resp = urllib.request.urlopen(req, timeout=10)
raw = resp.read().decode('gbk')

for match in re.finditer(r'hq_str_(\w+)="([^"]+)"', raw):
    code, data = match.group(1), match.group(2).split(',')
    name, open_p, prev_close, current = data[0], float(data[1]), float(data[2]), float(data[3])
    high, low = float(data[4]), float(data[5])
    date, time = data[30], data[31]
    chg_pct = (current - prev_close) / prev_close * 100
    print(f"{name}({code}): {current} ({chg_pct:+.2f}%) H:{high} L:{low} {date} {time}")
```

## 方法二：EastMoney API（备用，可能被阻断）

```python
import urllib.request, json

secids = "1.603341,0.002969,1.603316,1.560390"
fields = "f2,f3,f4,f5,f6,f12,f14"
url = f"https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&invt=2&fields={fields}&secids={secids}&ut=fa5fd1943c7b386f172d6893dbfba10b"

req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read().decode('utf-8'))
    for d in data['data']['diff']:
        print(f"{d['f14']}({d['f12']}): 现价={d['f2']}, 涨跌幅={d['f3']}%")
except Exception as e:
    print(f"EastMoney API 失败，切换到 Sina Finance: {e}")
```

## 指数行情（大盘）
```bash
curl -s "https://hq.sinajs.cn/list=s_sh000001,s_sh000300,s_sz399006" \
  -H "Referer: https://finance.sina.com.cn"
# 上证指数 sh000001, 沪深300 sh000300, 创业板指 sz399006
```

## Sina API 字段说明（方法一）

| 索引 | 含义 |
|------|------|
| data[0] | 股票名称 |
| data[1] | 今日开盘价 |
| data[2] | 昨日收盘价 |
| data[3] | 当前价格 |
| data[4] | 今日最高 |
| data[5] | 今日最低 |
| data[30] | 日期 (YYYY-MM-DD) |
| data[31] | 时间 (HH:MM:SS) |

## EastMoney API 字段说明（方法二）

| 字段 | 含义 |
|------|------|
| f2 | 当前价格 |
| f3 | 涨跌幅(%) |
| f4 | 涨跌额 |
| f5 | 成交量(手) |
| f6 | 成交额(元) |
| f12 | 股票代码 |
| f14 | 股票名称 |

## 注意事项

- **首选 Sina Finance API**（更稳定，从未被阻断）
- EastMoney push2 API 在部分环境/时段会被阻断（`Remote end closed connection`），建议作为备用
- **腾讯 Finance API (`qt.gtimg.cn`) 也是可靠的备用选项**（2026-04-23 验证：同样返回实时行情，GBK编码，格式与 Sina 类似）
  ```python
  # 腾讯 API 示例
  url = "https://qt.gtimg.cn/q=sh603316,sh560390,sz002792,sz002969"
  req = urllib.request.Request(url, headers={'Referer': 'https://finance.qq.com', 'User-Agent': 'Mozilla/5.0'})
  resp = urllib.request.urlopen(req, timeout=10)
  raw = resp.read().decode('gbk')
  # 返回格式：v_sh603316="1~诚邦股份~603316~15.42~...~20260423150202~..."
  # 字段[3]=当前价, [4]=今开, [5]=昨收, [6]=成交量, [32]=时间, [33]=涨跌额, [34]=涨跌幅
  ```
- 浏览器直接访问 EastMoney 个股页面时，行情数据不会出现在 accessibility snapshot 中（JS 动态渲染）
- Sina API 返回 GBK 编码，需 `decode('gbk')` 而非 UTF-8
- 不需要 API key，直接可用
- 批量查询时 codes 用逗号分隔，沪市加 `sh` 前缀，深市加 `sz` 前缀
- 基金/ETF（如电网E 560390）使用 `sh` 前缀：`sh560390`
