---
name: stock-news-announcements
description: A股个股资讯获取 — 公告、新闻、研报、异动公告、重要事件。用于事件驱动分析。
triggers:
  - "查公告"
  - "查新闻"
  - "重大事项"
  - "异动"
  - "研报"
  - "公司新闻"
---

# A股个股资讯获取

## 公告查询（东方财富）

```python
import urllib.request, json

def get_announcements(symbol, count=10):
    """
    获取个股公告
    symbol: 6位股票代码
    """
    # 东方财富公告接口
    url = f"https://np-anotice-stock.eastmoney.com/api/security/ann?cb=jQuery&sr=-1&page_size={count}&page_index=1&ann_type=SHA,CYB,SZA,BJA&client_source=web&f_list=secid%2Cnotice_code%2Cnotice_time%2Cshort_title"
    
    # 实际需要 secid 来筛选，用股票代码构造
    # 沪市: 1.代码，深市: 0.代码
    market = "1" if symbol.startswith("6") else "0"
    secid = f"{market}.{symbol}"
    
    url = f"https://np-listapi.eastmoney.com/api/qt/clist/get?cb=jQuery&pn=1&pz=5&po=1&np=1&fltt=2&invt=2&fid=f57&fs=m:0+b:4,m:0+b:5,m:1+b:4,m:1+b:5&fields=f57,f58,f59,f60,f61,f62&ut=fa5fd1943c7b386f172d6893dbfba10b"
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10)
    raw = resp.read().decode('utf-8')
    return raw[:500]
```

## 新闻查询（东方财富个股新闻）

```python
import urllib.request, json

def get_stock_news(symbol, count=10):
    """
    获取个股新闻
    """
    url = f"https://newsapi.eastmoney.com/kuaixun/v1/getlist_101_ajaxResult_50_{count}.html"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read().decode('utf-8'))
    return data
```

## 异动公告（个股龙虎榜/异常波动）

```python
import urllib.request, json

def get_stock_alert(secid):
    """
    获取个股异常波动提示
    secid: 1.603341 或 0.002969
    """
    fields = "f2,f3,f4,f5,f6,f12,f14,f15,f16,f17,f18,f57,f58,f104,f105,f106,f107"
    url = f"https://push2.eastmoney.com/api/qt/stock/get?fltt=2&invt=2&fields={fields}&secid={secid}&ut=fa5fd1943c7b386f172d6893dbfba10b"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read().decode('utf-8'))['data']
    
    # 涨停相关信息
    print(f"名称: {data['f14']}")
    print(f"现价: {data['f2']}")
    print(f"涨跌幅: {data['f3']}%")
    print(f"涨停状态: {data.get('f57', 'N/A')}")  # 涨停价
    print(f"跌停状态: {data.get('f58', 'N/A')}")  # 跌停价
    print(f"成交量: {data['f5']}")
    print(f"成交额: {data['f6']/10000:.0f}万")
```

## 业绩预告/年报查询

```python
import urllib.request, json

def get_earnings_forecast(symbol):
    """
    获取业绩预告/快报
    """
    # 使用东方财富业绩预告接口
    url = f"https://datacenter-web.eastmoney.com/api/data/v1/get?callback=jQuery&sortColumns=REPORT_DATE&sortTypes=-1&pageSize=5&pageIndex=1&reportName=RPT业绩预告_CLASS&columns=ALL&quoteColumns=&filter=(SECUCODE%3D%22{symbol}.SH%22%20OR%20SECUCODE%3D%22{symbol}.SZ%22)"
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10)
    raw = resp.read().decode('utf-8')
    json_str = re.sub(r'jQuery\((.*)\)', r'\1', raw)
    data = json.loads(json_str)
    return data
```

## 重要事件列表（财联社电报）

财联社是国内最快的A股资讯源，可用以下方式获取：

```python
def get_cailian_press():
    """
    获取财联社电报（今日重要个股事件）
    """
    url = "https://www.cls.cn/nodeapi/updateTelegraph?app=CLS&os=web&sv=7.8.4&page=1&rn=20&type=1"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read().decode('utf-8'))
    
    for item in data['data']['roll_data'][:10]:
        print(f"[{item['ctime']}] {item['title']}")
```

## 公告原文获取（巨潮资讯）

```python
import urllib.request

def get_announcement_detail(announcement_id):
    """
    获取公告详细内容
    announcement_id: 公告ID，从列表接口获取
    """
    url = f"http://www.cninfo.com.cn/new/hisAnnouncement/query?announcement_id={announcement_id}&page=1&pageSize=10"
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json'
    })
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read().decode('utf-8'))
    return data
```

## 事件分析框架

### 需要重点关注的事件

| 事件类型 | 利好程度 | 说明 |
|----------|----------|------|
| 业绩预增/扭亏 | ⭐⭐⭐⭐⭐ | 最实在的驱动 |
| 行业政策利好 | ⭐⭐⭐⭐ | 板块性机会 |
| 大订单/中标 | ⭐⭐⭐⭐ | 实质订单驱动 |
| 股权激励 | ⭐⭐⭐ | 中长期利好 |
| 高送转 | ⭐⭐ | 短期炒作 |
| 大股东增持 | ⭐⭐⭐ | 管理层背书 |
| 要约收购 | ⭐⭐⭐⭐ | 确定性高 |
| 资产重组/并购 | ⭐⭐⭐⭐ | 视项目质量 |

### 需要警惕的事件

| 事件类型 | 风险程度 | 说明 |
|----------|----------|------|
| 业绩预减/首亏 | ⚠️⚠️⚠️⚠️⚠️ | 最直接的利空 |
| 监管问询/调查 | ⚠️⚠️⚠️⚠️ | 不确定性高 |
| 大股东减持 | ⚠️⚠️⚠️ | 内部人信心不足 |
| 商誉减值 | ⚠️⚠️⚠️⚠️ | 一次性大额亏损 |
| 债务违约 | ⚠️⚠️⚠️⚠️⚠️ | 可能致命 |

### 事件驱动分析检查清单

1. **事件真实性**：公告来源（巨潮/上交所/深交所）> 媒体报道
2. **事件性质**：实质性利好 vs 主题炒作
3. **市场预期差**：是否超出市场预期（PE、EPS预测）
4. **时间窗口**：事件催化的时间跨度（短期/中期/长期）
5. **筹码与流动性**：利好兑现时是否有足够承接
6. **前期涨幅**：已累计涨幅过大，利好可能出货
