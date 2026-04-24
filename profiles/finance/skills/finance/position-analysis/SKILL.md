---
name: position-analysis
description: A股持仓综合分析 — 读取持仓文件，结合实时行情、K线、主力资金流进行持仓诊断，输出风险评级和操作建议。
triggers:
  - "我的持仓"
  - "分析持仓"
  - "要不要卖"
  - "要不要止损"
  - "还拿着吗"
  - "持仓分析"
---

# A股持仓综合分析

## 数据获取顺序

### 1. 读取持仓文件

```python
# 路径
path = "/home/kent/.hermes/profiles/finance/workspace/positions.json"

# 字段结构
{
  "positions": [
    {
      "symbol": "603341",
      "name": "龙旗科技",
      "shares": 100,
      "cost": 45.551,      # 持仓成本
      "hardStop": 41.00,    # 硬止损（必须执行）
      "type": "stock",
      "status": "watch"
    }
  ],
  "account": {
    "availableCash": 4111.20
  }
}
```

> ⚠️ 注意：positions.json 最后更新是 2026-03-29（一个月前的数据），每次分析前需确认数据是否仍是最新。日期格式 `"updatedAt": "2026-03-29T23:35:00+08:00"`。

### 2. 实时行情（新浪，GBK）

```python
import urllib.request, re, json

def fetch(url, encoding='utf-8', retries=2):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Referer': 'https://finance.sina.com.cn/'
            })
            resp = urllib.request.urlopen(req, timeout=10)
            return resp.read().decode(encoding, errors='replace')
        except:
            import time; time.sleep(1)
    return None

# codes 格式: sh6xxxxx 或 sz0/3xxxxx
# ETF 也用 sh 格式（如 sh560390）
url = f"https://hq.sinajs.cn/list={','.join(codes)}"
raw = fetch(url, encoding='gbk')
# 解析同 sina_quote()
```

> ETF 格式注意：`电网设备ETF(560390)` 在新浪是 `sh560390`（不是 `sz560390`）。

### 3. K线历史（新浪）

```python
def sina_kline(symbol, scale=240, days=20):
    url = (f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php"
           f"/CN_MarketData.getKLineData?symbol={symbol}&scale={scale}&ma=5&datalen={days}")
    raw = fetch(url)
    return json.loads(raw)
```

### 4. 主力资金流（AKShare）

```python
import akshare as ak, warnings
warnings.filterwarnings('ignore')

# market 参数: "sz" 或 "sh"
df = ak.stock_individual_fund_flow(stock="002969", market="sz")
t = df.iloc[-1]
main_net = t['主力净流入-净额'] / 1e8  # 亿元
main_pct = t['主力净流入-净占比']
```

## 分析维度

### 风险信号检测

| 信号 | 判断条件 | 严重程度 |
|------|---------|---------|
| 触及硬止损 | cur <= hardStop | 🚨 必须清仓 |
| 距止损<3% | (cur - hardStop) / cur < 3% | ⚠️ 准备好出 |
| 浮亏>10% | pnl_pct < -10% | 🚨 止损线已破 |
| 均线空头 | cur < ma5 | ⚠️ 短期弱 |
| 主力净流出>10% | main_pct < -10% | ⚠️ 机构在卖 |
| 今日下跌>3% | chg_pct < -3% | ⚠️ 注意 |
| 下影线>3% + 下跌 | lower > 3 and chg_pct < 0 | 🟡 下方有支撑 |

### 均线系统

```python
ma5 = sum(closes[-5:]) / 5
ma10 = sum(closes[-10:]) / 10
ma20 = sum(closes[-20:]) / 20

if cur > ma5 > ma10 > ma20: print("✅ 均线多头排列")
elif cur < ma5: print("⚠️ 均线空头排列")
else: print("🟡 震荡")
```

### 持仓位置分析

```python
# 在近10日区间中的位置
recent_high = max(highs[-10:])
recent_low = min(lows[-10:])
pos_in_range = (cur - recent_low) / (recent_high - recent_low) * 100

if pos_in_range > 80: print("🟠 高位区，风险积累")
elif pos_in_range < 20: print("🟢 低位区，可能有机会")
```

## 输出格式

```markdown
## 持仓分析报告 · YYYY-MM-DD

---

### [股票名](代码) — [结论]
| 项目 | 数据 |
|------|------|
| 现价 | X.XX |
| 今日 | +X.XX% |
| 成本 | X.XX |
| 浮盈亏 | +X.X%（+XXX元）|
| 硬止损 | X.XX（距止损 X.X%）|
| 主力资金 | X.XX亿（X.X%）|
| 均线 | MA5=X.XX [状态] |
| 风险信号 | [列表] |

**结论**: [结论]
**操作**: [操作建议]
```

> ⚠️ **止损已破的判断逻辑**：当 `现价 <= 硬止损` 时，输出 `已破止损` 而非 `距止损X%`。
> - ❌ 错误输出："距止损23.50仅剩7.85%"（当现价21.79 < 23.50时）
> - ✅ 正确输出："已破止损23.50，建议立即执行"
>
> 原因：低于止损位的持仓，每持有一天都是额外的赌博，不能用"还有多少空间"来描述。
>
> ```python
> if cur <= hardStop:
>     stop_status = f"🚨 已破止损（现价{cur} < 止损{hardStop}），建议立即执行"
> else:
>     dist = (cur - hardStop) / cur * 100
>     stop_status = f"距止损 {hardStop} 还有 {dist:.1f}%"
> ```

## 踩坑记录

### ETF 代码格式（新浪）
- `电网设备ETF(560390)` → 代码 `sh560390`（不是 sz）
- 先试 sz，再试 sh

### positions.json 可能过期
- 文件最后更新是 2026-03-29
- 每次分析前要确认用户是否有新增/卖出操作
- 当前日期是 2026-04-21，数据可能已变化

### 新浪实时行情编码
- `hq.sinajs.cn` 必须用 `encoding='gbk'`，不能用 utf-8
- 否则返回乱码

### 硬止损规则
- 触及硬止损必须执行，没有例外
- 亏损达到一定程度后，止损不能再"等一等"
