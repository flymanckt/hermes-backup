# MEMORY.md — 爱马仕 finance 长期记忆

## 用户与风格
- 用户是 Kent，IT管理者，全程中文，先结论后细节，少客套实用优先
- 不给没止损位的买入建议，没有失效条件不算交易计划
- 市场退潮期默认保守，连续高潮后的利好优先考虑兑现风险

## 当前持仓（2026-04-21更新）
- positions.json: `/home/kent/.hermes/profiles/finance/workspace/positions.json`
- watchlist.json: `/home/kent/.hermes/profiles/finance/workspace/watchlist.json`

### 持仓
| 标的 | 代码 | 股数 | 成本 | 硬止损 | 状态 |
|------|------|------|------|--------|------|
| 诚邦股份 | 603316 | 100股 | 14.39 | 14.43 | 减半，持有一半 |
| 电网设备ETF | 560390 | 4100股 | 1.047 | 0.94 | 持有 |

### 已止损出局
| 标的 | 代码 | 亏损 |
|------|------|------|
| 龙旗科技 | 603341 | -679元（100股@38.76止损） |
| 嘉美包装 | 002969 | -1118元（300股@21.79止损） |

### 资金
- 可用现金：约16091元（龙旗+嘉美止损后回血）

## 系统能力（免费，已验证）

### 数据源
| 数据 | 来源 | 备注 |
|------|------|------|
| 实时行情 | `hq.sinajs.cn` (GBK) | 稳定 |
| K线历史 | `money.finance.sina.com.cn` (UTF-8) | 日K/分钟K |
| 涨幅榜选股 | `vip.stock.finance.sina.com.cn` (GBK) | 200条 |
| 主力资金流 | AKShare `stock_market_fund_flow()` | 主力/超大单/大单/中单/小单 |
| 概念板块资金流 | AKShare `stock_fund_flow_concept(symbol="即时")` | 387个板块 |
| 个股主力资金 | AKShare `stock_individual_fund_flow()` | 近120日明细 |
| 今日涨停池 | AKShare `stock_zt_pool_em()` | 含炸板次数/连板数/封板时间 |
| 昨日强势股 | AKShare `stock_zt_pool_strong_em()` | 含入选理由 |
| 昨日炸板股池 | AKShare `stock_zt_pool_zbgc_em()` | 明日反包机会 |
| 北向资金 | AKShare `stock_hsgt_fund_flow_summary_em()` | 沪深港通 |
| 融资融券（沪） | AKShare `stock_margin_sse()` | 融资余额/买入额 |

### 技术指标（新浪K线 + pandas计算）
- MA5/MA10/MA20/MA60
- RSI6/RSI12/RSI24
- MACD（DIF/DEA/MACD柱）
- KDJ（K/D/J值）
- 布林带（上下轨+位置%）
- 乖离率（MA5乖离/MA10乖离）
- 形态（上下影线/实体/K线类型）

### 分析模块
1. **大盘情绪评分**（0-100分）：综合主力资金+涨跌停数量+北向资金
2. **板块轮动**：今日净流入Top5 + 净流出严重板块
3. **个股技术分析**：RSI/MACD/KDJ/布林带综合评分
4. **选股策略**：5-9%涨幅 + 技术评分 + 形态过滤

## Cron任务
| 任务 | 时间 | job_id |
|------|------|--------|
| 盘前报告 08:30 | 08:30 | 857f7fc3fcd2 |
| 盘中报告 13:25 | 13:25 | 9f2436bf61a1 |
| 盘中报告 14:00 | 14:00 | a9ad30c447cb |
| 盘中报告 14:25 | 14:25 | 907d3a253af2 |
| 盘后复盘 15:05 | 15:05 | a980df4de8fd |
| **短线推荐 14:40** | 14:40 | fd105d2e7898（升级版）|

## Skills
- `short-t-strategy`: 完整选股+分析技能包（含AKShare+新浪数据源、大盘情绪、板块轮动、技术指标、仓位计算器、情绪温度计）
- 位置: `~/.hermes/profiles/finance/skills/finance/short-t-strategy/SKILL.md`

## 关键规则
1. 无止损位 → 不给买入建议
2. 无失效条件 → 不算交易计划
3. 连续高潮后利好 → 优先兑现
4. 市场退潮 → 默认保守
5. 技术指标不能单独作为结论依据

## API踩坑记录
- 东方财富接口在WSL沙盒中不稳定，`push2his.eastmoney.com` SSL握手超时
- 新浪接口：`hq.sinajs.cn` 必须用 `encoding='gbk'`，其他用utf-8
- AKShare腾讯K线 `stock_zh_a_hist_tx` 慢（6800+行），新浪K线更快
- 新浪K线接口SSL超时：重试3次，每次sleep 1秒

## Tushare Pro（待开通）
- 注册地址：https://tushare.pro
- 基础积分可免费获取：龙虎榜明细、融资融券、股本结构
- 龙虎榜详细买卖数据（机构vs游资分离）对短线很有价值
- 注册后找我接入API
