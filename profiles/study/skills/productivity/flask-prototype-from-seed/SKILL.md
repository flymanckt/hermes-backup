---
name: flask-prototype-from-seed
description: 当需要快速构建领域逻辑验证原型并配上可操作Web界面时，用此技能。Flask + Jinja2 模板实现多页面 Web UI，零额外依赖，适合 MRP/ERP/制造业逻辑验证。
version: 1.0.0
author: Druid
tags: [flask, web, prototype, verification]
---

# Flask 原型快速构建技能

## 何时使用

用户说"需要验证模型"、"做个可操作的界面"、"轻量原型"、"演示用"的场景。
不追求 Django/Streamlit 的完整性，只需要快速可用的 Web 界面。

## 关键发现（经验）

### hermes venv 中安装依赖的正确方式

hermes venv 没有 pip，直接 `uv pip install` 会失败（报 `--system` flag 问题）。
正确方式：

```python
subprocess.run([
    'uv', 'pip', 'install', 'flask',
    '--python', '/home/kent/.hermes/hermes-agent/venv/bin/python'
], ...)
```

### 文件结构

```
project/
├── mrp_web.py          # Flask 入口 + 路由 + API
├── mrp_core.py         # 核心业务逻辑（与 Web 解耦）
├── mrp_models.py       # 数据模型
├── seed_data.py        # Mock 数据
├── templates/          # Jinja2 模板
│   ├── index.html
│   ├── page2.html
│   └── ...
└── requirements.txt    # 如需
```

### Web 界面三件套

- **Flask route → API endpoint**：返回 JSON，用于 AJAX/Fetch
- **Flask route → render_template**：返回 HTML 页面（用于页面导航）
- **模板页面**：纯 HTML + CSS + Vanilla JS，无框架依赖

### 启动

```bash
/home/kent/.hermes/hermes-agent/venv/bin/python mrp_web.py
# 访问 http://localhost:5050
```

## MRP 验证原型示例结构（可直接套用）

### 核心逻辑（mrp_core.py）

与 Web 层完全解耦，纯函数：

```python
def run_full_mrp_flow(order, policies, recipe_boms, ...):
    report = {"steps": []}
    # Step1: 订单分类
    # Step2: BOM解析
    # Step3: 批次筛选
    # Step4: ATP判断
    # Step5: MPS冻结
    # Step6: 锁批
    # Step7: MRP建议
    return report
```

### Web 层（mrp_web.py）

```python
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html", orders=orders)

@app.route("/run_mrp", methods=["POST"])
def run_mrp():
    data = request.json
    report = run_full_mrp_flow(...)
    return jsonify(serialize(report))  # 序列化 dataclass
```

### 序列化辅助

dataclass 对象直接 jsonify 会报错，需要展平：

```python
def serialize(obj):
    if hasattr(obj, "__dataclass_fields__"):
        return {k: serialize(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, list):
        return [serialize(i) for i in obj]
    if hasattr(obj, "value"):  # Enum
        return obj.value
    return obj
```

### 前端页面模板要点

- 导航栏 + 3个链接（订单页、品质页、产品页）
- 卡片式布局 + CSS变量
- Fetch POST → 动态渲染表格
- 无需 npm/Webpack，单个 .html 文件包含 CSS+JS

## 验证步骤

启动后依次访问：
1. `http://localhost:5050/` — 主页
2. `/batch_quality` — 数据展示页
3. `/products` — 产品配置页
4. POST `/run_mrp` — API 正常返回 JSON

## 手机 H5 化经验（本次新增）

当用户不是只要“能用的 Web 原型”，而是明确要：
- 手机端可访问
- H5 风格
- 可直接外网演示

应直接把 Flask 原型升级为 **移动优先 H5**，不要停留在桌面表格页。

### 推荐改法

#### 1. 保持 Flask + Jinja2，不要急着上前端框架
对这种 MRP/ERP/制造业逻辑验证模型：
- 业务核心在 Python 规则
- 页面数量少（通常 2~5 页）
- 交互主要是 fetch + 渲染结果

此时继续用 Flask 模板是最短路径，没必要引入 Vue/React。

#### 2. 抽公共静态样式文件
不要把 CSS 全塞在每个模板里。建议新增：

```text
static/app.css
```

把以下能力统一进去：
- 顶部品牌区
- 底部/顶部导航 tabs
- 卡片式 KPI
- 移动优先栅格
- 表格横向滚动
- badge / status box / progress bar

#### 3. 模板按“移动优先”重写
页面结构建议：
- `index.html`：订单池 + 运行按钮 + MRP结果卡片 + 明细表
- `batch_quality.html`：批次卡片 + 等级筛选 + 质量进度条
- `products.html`：产品主数据卡片化

移动优先的关键不是“缩小 PC 页面”，而是：
- 一屏只承载一层重点信息
- 点击区域足够大
- 指标先卡片化再表格化
- 明细表允许横向滚动而不是强行压缩

#### 4. 首页增加摘要接口
建议新增：

```python
@app.route('/api/summary')
def api_summary():
    ...
```

用于返回：
- 订单数
- 可执行数
- 冻结订单数
- P1 批次数

这样首页可直接做顶部 KPI，不必把统计逻辑塞进模板。

#### 5. 增加健康检查接口
建议新增：

```python
@app.route('/healthz')
def healthz():
    return jsonify({"status": "ok", ...})
```

这是后续外网验证、反向代理、systemd、隧道检查的基础。

## 从演示原型升级为“桌面录入后台”的经验（本次新增）

当用户需求从“能演示的页面”转成：
- 桌面网页端优先
- 稳定录入业务测试数据
- 不要继续折腾手机 H5 交互
- 要按规格书逐步扩主数据、台账、规则配置

应立即把 Flask 原型改造成 **服务端渲染的桌面录入后台**，不要继续堆前端 JS 交互。

### 什么时候该放弃 H5 方案
若出现这些信号，直接切回桌面后台：
- 用户明确说“先放弃手机版”
- 主要目标变成录入、维护、试算，而不是手机演示
- 页面点击/切换体验不稳定，且继续修前端收益低
- 用户需要大量主数据表单和台账页面

### 推荐架构
继续保持 Flask + Jinja2，但把页面定位改成后台管理系统：

```text
project/
├── mrp_web.py                # 路由、表单提交、试算编排
├── data_store.py             # JSON持久化、默认数据、评分辅助
├── mrp_core.py               # 核心MRP逻辑
├── mrp_models.py             # dataclass模型
├── data/                     # 持久化目录
│   ├── products.json
│   ├── materials.json
│   ├── bom_headers.json
│   ├── bom_lines.json
│   ├── orders.json
│   ├── inventory.json
│   ├── strategy_params.json
│   ├── quality_rule_headers.json
│   ├── quality_rule_lines.json
│   ├── lock_headers.json
│   ├── lock_lines.json
│   ├── supply_suggestions.json
│   └── planning_exceptions.json
└── templates/
    ├── base.html
    ├── dashboard.html
    ├── materials.html
    ├── products.html
    ├── boms.html
    ├── orders.html
    ├── inventory.html
    ├── strategy_params.html
    ├── quality_rules.html
    ├── locks.html
    └── suggestions.html
```

### 为什么用 JSON 持久化而不是先上数据库
在“逻辑验证 + 规格书对齐 + 快速补页面”阶段：
- JSON 足够承载几十到几百条测试数据
- 改字段成本低
- 易于人工检查和备份
- 非常适合多轮试错和结构调整

适合先把系统从“只读演示”升级成“可录入、可试算、可落台账”。

### 关键页面分层
最低应包含：
- `MRP试算`：选择订单快照，执行试算，展示试算结果
- `物料主数据`
- `产品主数据`
- `BOM主数据`
- `订单快照`
- `批次质量库存`
- `策略参数`
- `质量规则`
- `锁批台账`
- `供应/异常台账`

### 规格书驱动的 4 个高价值增强点
#### 1. 订单改成“订单快照”
不要只存基础订单字段，至少补：
- `priority`
- `policy_id`
- `recipe_header_id`
- `snapshot_status`

这样后续做策略分配、锁批状态、快照冻结才有落点。

#### 2. 批次库存接入“质量规则模板”
库存录入时不要让用户手填最终评分作为唯一来源。推荐：
- 录原始属性（长度、强力、马值、含杂、含水、白度）
- 选择评分模板
- 后端自动计算 `quality_score`
- 自动映射 `planning_grade`

这是从“录库存”升级到“录批次质量”的关键。

#### 3. MRP 试算结果要落台账
不要只显示结果页面。每次试算后，至少把这些内容持久化：
- 锁批单头 `lock_headers`
- 锁批明细 `lock_lines`
- 供应建议 `supply_suggestions`
- 异常台账 `planning_exceptions`

这样系统才开始接近业务后台而不是单次计算器。

#### 4. 异常台账先打底，不必一开始就做审批流
先记录：
- 缺料
- MPS冻结
- 锁批不足
- 严重度
- 审批状态（默认待审批）

即使没有真正 OA 审批，也先把业务对象和状态存下来。

### 重要经验：页面交互尽量走服务端表单
对后台管理类场景：
- 录入页优先使用 `<form method="post">`
- 提交成功后 `redirect()`
- 查询页服务端直接 render_template

避免把录入后台做成大量 fetch + JS 状态管理。这样更稳，排障更简单。

### 验证顺序（非常关键）
每次结构扩展后按这个顺序验：
1. `py_compile` 检查 Python 语法
2. Flask `test_client()` 逐页检查 GET 200
3. 对关键 POST 表单做集成测试
4. 对 `/run_mrp_page` 做一次真实提交
5. 再检查台账页面是否出现新记录

典型验收脚本要覆盖：
- 新增主数据成功
- 新增订单快照成功
- 新增库存且自动评分成功
- 执行试算成功
- 锁批台账有记录
- 供应/异常台账可见

## 桌面录入后台化经验（适合 MRP/ERP 测试系统）

当用户明确表示：
- 不要手机 H5，改做桌面后台
- 需要录入真实/半真实测试数据
- 需要把试算结果沉淀为台账

不要继续停留在“展示型页面”，应升级为 **桌面测试后台**。

### 推荐升级方向

#### 1. 数据持久化先用 JSON 文件，不必一开始上数据库
对于验证阶段，优先采用：

```text
project/data/
├── products.json
├── materials.json
├── bom_headers.json
├── bom_lines.json
├── orders.json
├── inventory.json
├── strategy_params.json
├── quality_rule_headers.json
├── quality_rule_lines.json
├── lock_headers.json
├── lock_lines.json
├── supply_suggestions.json
└── planning_exceptions.json
```

优点：
- 开发快
- 易导入/导出
- 方便直接看数据
- 适合单机测试和规则验证

#### 2. 先做 data_store.py 统一管理持久化
不要把 JSON 读写散落在路由里。建议新增：

```text
data_store.py
```

集中提供：
- bootstrap 初始化默认数据
- load_* / save_*
- all_*_rows
- next_id
- 评分/等级计算辅助方法

这样 Web 层只负责接表单和渲染。

#### 3. 订单不要只叫“订单”，要按规格书升级为“订单快照”
至少补这些字段：
- `priority`
- `policy_id`
- `recipe_header_id`
- `snapshot_status`

这样才能承接：
- 待分配
- 已分配
- 已锁定
- 策略分流
- 配方快照关联

#### 4. 批次库存要升级为“批次质量库存”
不要只存库存数量；要接近：
- 原始质检属性
- 自动评分
- 自动计划等级
- 使用的评分模板/公式

建议：库存录入时根据质量模板自动算：
- `quality_score`
- `planning_grade`
- `score_formula_used`

#### 5. 先把“结果页面”升级成“结果落台账”
每次 MRP 试算后，不要只显示结果，要同步写入：
- 锁批单头 `lock_headers.json`
- 锁批明细 `lock_lines.json`
- 供应建议 `supply_suggestions.json`
- 异常审批 `planning_exceptions.json`

这样系统才开始具备闭环雏形。

### 推荐的最小台账闭环

#### 锁批台账
页面：`/locks`

能力：
- 查看锁批单头
- 查看锁批明细
- 更新锁批状态
- 释放/解锁
- 删除

#### 供应/异常台账
页面：`/suggestions`

能力：
- 供应建议状态流转：待确认 / 已确认 / 已下达 / 已关闭
- 异常审批状态流转：待审批 / 已审批 / 已关闭
- 删除记录

### 主数据后台必须具备的 CRUD 能力

验证型系统也不能只有“新增”。至少要补：
- 编辑
- 删除
- 删除前引用校验

推荐最小删除校验：
- 物料被 BOM / 库存引用时禁止删除
- 产品被 BOM / 订单引用时禁止删除
- BOM 被订单快照引用时禁止删除
- 订单已生成锁批台账时禁止删除
- 库存批次已被锁批明细引用时禁止删除

### 导入导出经验

对于测试系统，非常值得尽早补：
- Excel 导出
- CSV 导出
- Excel/CSV 导入

实现方式可直接用 `pandas + openpyxl`：
- `send_file(BytesIO(...))` 导出 xlsx/csv
- `pd.read_excel()` / `pd.read_csv()` 导入

建议优先支持：
- 物料
- 产品
- BOM 表头/表行
- 订单快照
- 批次质量库存

### 页面结构建议

左侧导航建议升级为：
- MRP试算
- 策略参数
- 质量规则
- 物料主数据
- 产品主数据
- BOM主数据
- 订单快照
- 批次质量库存
- 锁批台账
- 供应/异常台账

这样更符合规格书导向的后台结构。

### 重要经验：不要为了“交互好看”过早押注 H5
如果用户真正要的是：
- 稳定录入
- 真实数据测试
- 业务后台验证

优先做桌面管理后台，而不是继续打磨手机 H5。H5 容易在交互、外网接入、调试上花掉大量时间，却无法提升测试效率。

## 生产运行最小化做法（原型可外网演示）

### 1. 不要用 Flask debug server 直接对外
生产/演示至少切到 gunicorn：

```text
requirements.txt
wsgi.py
deploy.sh
```

示例：

```python
# wsgi.py
from mrp_web import app
```

```bash
# deploy.sh
/home/kent/.hermes/hermes-agent/venv/bin/python -m gunicorn \
  --bind 0.0.0.0:5050 \
  --workers 2 \
  --threads 4 \
  --timeout 120 \
  wsgi:app
```

### 2. Hermes 环境安装 gunicorn
如果 hermes venv 没有 gunicorn，用：

```bash
uv pip install --python /home/kent/.hermes/hermes-agent/venv/bin/python -r requirements.txt
```

### 3. 先用 Flask test_client 做快速验收
在真正启动浏览器前，先这样验：

```python
from mrp_web import app
client = app.test_client()
print(client.get('/').status_code)
print(client.get('/healthz').status_code)
print(client.post('/run_mrp', json={'order_no':'SO-2024-001'}).status_code)
```

这一步可以快速排除模板错误、接口错误、序列化错误。

## 临时公网暴露经验（适合演示，不适合正式生产）

本次实践中，下载 `cloudflared` 出现超时/阻塞，因此更稳的备用方案是：

### 使用 localhost.run 反向 SSH 隧道
前提：本机已有 `ssh`

```bash
ssh -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=30 \
    -R 80:127.0.0.1:5050 \
    nokey@localhost.run
```

会在输出中返回公网 HTTPS 地址，例如：

```text
https://xxxxx.lhr.life
```

#### 适用场景
- 客户临时演示
- 让手机直接扫码/打开访问
- 快速证明“系统可公网访问”

#### 限制
- 地址是临时的
- 隧道进程停掉就失效
- 不适合长期生产使用

## 推荐验收顺序（非常实用）

1. `py_compile` 检查 Python 文件
2. `test_client()` 检查核心路由
3. gunicorn 本地启动
4. `curl http://127.0.0.1:5050/healthz`
5. browser 打开首页，点一遍主流程
6. 再做公网隧道
7. `curl https://公网域名/healthz`
8. browser 再验一次公网首页

## 从 H5 回退到桌面录入后台的经验（本次新增）

当用户真实需求从“演示页面”转为：
- 需要稳定录入测试数据
- 需要维护主数据（物料 / 产品 / BOM / 订单 / 库存）
- 更关注桌面端效率，而不是手机端展示

应果断从移动 H5 切回 **桌面 Web 后台**，不要继续在 H5 交互上打磨。

### 判断信号

如果用户反馈出现以下任一情况：
- “按钮点击报错”
- “页面切换不了”
- “先放弃手机版”
- “我要录生产测试数据”

优先方案应改为：
- 左侧导航 + 右侧工作区的桌面后台布局
- 服务器端表单提交优先
- 降低前端 JS 依赖
- 先把录入、保存、查询、试算跑通

### 桌面后台推荐菜单

至少拆成 6 个页面：

1. `MRP试算`：选择订单后执行试算，展示结果
2. `物料主数据`
3. `产品主数据`
4. `BOM主数据`
5. `订单录入`
6. `库存录入`

这是制造业 / MRP 验证原型里最实用的一套最小后台。

### 交互建议：优先服务端表单，不要过度依赖 JS

对于录入型后台，推荐：
- `<form method="post">` 直提服务端
- 提交后 `redirect(url_for(...))`
- 录入结果直接刷新列表

不要一上来就全做成 fetch/AJAX/单页应用。原因：
- 更稳定
- 更容易排查问题
- 更适合低复杂度内部验证系统
- 用户更关心“能不能录进去并跑试算”，不是炫交互

### 数据持久化：优先本地 JSON，足够支撑原型

当用户需要“录入生产测试数据”，不能继续只靠 `seed_data.py` 内存 mock。

推荐新增 `data_store.py`，把数据拆到独立 JSON 文件：

```text
data/
├── products.json
├── materials.json
├── bom_headers.json
├── bom_lines.json
├── orders.json
└── inventory.json
```

#### 为什么先用 JSON
- 比 SQLite 更快落地
- 文件可直接查看和备份
- 便于人工修正测试数据
- 对几十到几百条测试数据完全够用

### 一个关键坑：写 JSON 前必须先把 date / Enum / dataclass 转普通对象

这次遇到的真实问题：
- `orders.json` 初始化写入时，`date` 不能直接 `json.dumps`
- 报错：`TypeError: Object of type date is not JSON serializable`

**正确做法：** 所有写 JSON 的出口统一走 `_to_plain()`，不要直接 `json.dumps(payload)`。

例如：

```python
def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_to_plain(payload), ensure_ascii=False, indent=2), encoding='utf-8')
```

这是桌面原型做持久化时非常容易漏掉的坑。

### MRP 试算页的推荐实现

不要在首页保留复杂卡片交互。

更稳的实现：
- 左侧表单选择订单
- POST 到 `/run_mrp_page`
- 服务端重新 render 模板
- 右侧展示：
  - ATP 结果
  - MPS 冻结
  - 过程步骤
  - 原料需求
  - 锁批明细
  - 供给建议

这比前端拼接 DOM 更稳，尤其适合快速业务验证。

### 推荐验收顺序（桌面录入后台版）

1. 所有页面 `GET` 返回 200
2. 逐页 `POST` 一条测试数据：
   - 物料
   - 产品
   - BOM表头
   - BOM行
   - 库存
   - 订单
3. 再跑一次 `POST /run_mrp_page`
4. 确认新录入数据能参与 MRP 计算

### 桌面录入后台经验（本次新增）

当用户发现手机 H5 交互不稳定、实际需求转向“录生产测试数据 + 桌面端维护”时，应及时收敛为 **桌面后台管理界面**，不要继续在移动端交互上耗时间。

### 适用信号

如果用户开始强调这些需求：
- 页面切换稳定
- 按钮点击可靠
- 能录入测试数据
- 要有物料 / 产品 / BOM / 订单 / 库存维护页

说明目标已经不是“演示型 H5”，而是“桌面验证后台”。

### 推荐做法

#### 1. 首页改成服务端表单提交
不要再依赖首页 JS 选卡片 + fetch + 动态渲染作为唯一入口。
对试算入口，优先改成：

```text
<select name="order_no"> + <form method="post" action="/run_mrp_page">
```

这样可以显著降低前端点击/脚本兼容性问题，尤其适合业务测试环境。

#### 2. 增加独立维护页
建议最少拆成：

- `/materials` 物料主数据
- `/products` 产品主数据
- `/boms` BOM 表头 + 表行
- `/orders` 订单录入
- `/inventory` 库存批次录入
- `/` MRP 试算主页

桌面端布局建议：
- 左侧固定菜单
- 右侧内容区
- 表单 + 表格同屏
- 不追求前端框架，Flask + Jinja2 足够

#### 3. 加本地持久化层
如果还在验证阶段，不必急着接数据库。可先加一个 `data_store.py`，把录入数据持久化到 JSON 文件：

```text
data/
  products.json
  materials.json
  bom_headers.json
  bom_lines.json
  orders.json
  inventory.json
```

注意：
- 写 JSON 前必须统一把 `date/datetime/Enum/dataclass` 转成可序列化结构
- 否则会在初始化或保存时触发 `TypeError: Object of type date is not JSON serializable`

推荐统一用类似 `_to_plain()` 的转换函数，再由 `_write_json()` 调用。

#### 4. 先用 test_client 跑“新增 -> 保存 -> 试算”闭环
不要只测 GET 页面。
应至少自动验证：

1. 打开维护页
2. POST 新增物料
3. POST 新增产品
4. POST 新增 BOM 表头
5. POST 新增 BOM 行
6. POST 新增库存
7. POST 新增订单
8. POST `/run_mrp_page` 验证结果页出现 ATP 内容

这比单纯浏览器点几下更能证明后台真的可用于录测试数据。

## 关于公网访问稳定性的经验（本次修正）

### 重要结论
匿名 `localhost.run` / 临时反向隧道 **只能用于短期演示**，不适合给用户承诺“稳定链接”。

这类地址常见问题：
- 链接会失效
- 隧道会被远端断开
- 地址每次可能变化
- 用户会反复遇到“刚给的网址又打不开”

### 对用户的正确预期管理
如果用户明确说：
- 要稳定链接
- 不想频繁换地址
- 要外网长期可访问

就不要再继续给临时隧道地址当“稳定方案”。应直接说明：

**真正稳定的方案只有：**
1. 云服务器固定部署（最推荐）
2. Cloudflare Tunnel + 自有域名
3. FRP / Tailscale / 自建反向代理（前提是已有基础设施）

### 建议顺序
1. 本地先把应用做好
2. 临时隧道仅用于快速验收/演示
3. 一旦用户提出“稳定性高”，立即切换到正式部署方案讨论

## 桌面管理后台经验（本次新增）

当用户明确反馈：
- 手机 H5 点击不稳定
- 页面切换/按钮交互出问题
- 更关注“录数据做测试”而不是移动端展示

应立即**切换方向**，不要继续在 H5 交互层死磕。对 MRP/ERP/制造业原型，更稳的做法是改成 **桌面 Web 管理后台**。

### 适用场景
- 需要快速录入主数据和测试数据
- 用户主要在 PC 浏览器操作
- 前端 JS 交互出现偶发错误或不易复现
- 当前阶段目标是“验证业务链路”，不是“打磨移动体验”

### 推荐改法

#### 1. 首页试算改成服务端表单提交
不要强依赖前端 JS 点击逻辑。

把：
- 订单卡片点击
- fetch 异步渲染
- 页面内复杂状态维护

改为：
- `<form method="post" action="/run_mrp_page">`
- 下拉框选订单
- 提交后由 Flask 服务端重新渲染结果页

这样会明显更稳，尤其适合测试后台。

#### 2. 新增“主数据录入页”而不是只做展示页
典型应包含：
- 物料主数据 `/materials`
- 产品主数据 `/products`
- BOM 主数据 `/boms`
- 订单录入 `/orders`
- 库存录入 `/inventory`

每页结构统一：
- 左侧/顶部导航
- 左侧录入表单
- 右侧列表表格
- 提交成功后 redirect 回当前页

#### 3. 用 JSON 做轻量持久化，先别急着上数据库
当用户只是要“能录数据做测试”：
- 新建 `data_store.py`
- 落地到 `data/*.json`
- 启动时 bootstrap 默认 seed 数据
- 表单提交后直接写 JSON

推荐数据文件：
- `data/products.json`
- `data/materials.json`
- `data/bom_headers.json`
- `data/bom_lines.json`
- `data/orders.json`
- `data/inventory.json`

#### 4. 持久化时统一做 date/enum/dataclass 序列化
这次实际踩坑：
- `orders.json` 写入时包含 `date`
- 直接 `json.dumps()` 会报：`TypeError: Object of type date is not JSON serializable`

正确做法：
- 所有写 JSON 的路径统一先过 `_to_plain()`
- 在 `_write_json()` 内部强制调用 `_to_plain(payload)`
- 不要把序列化责任分散到各业务调用点

也就是说，**序列化放基础设施层，不要散落在业务层。**

#### 5. 对“测试后台”优先考虑可维护性，不追求前端炫技
推荐 UI：
- 桌面双栏布局
- 左侧固定导航
- KPI + 表格 + 表单
- 少 JS，多服务端渲染

这种方案对制造业原型特别实用：
- 稳
- 易改
- 用户容易上手
- 后续接 SQLite/MySQL 也顺手

### 验证顺序（桌面后台版）
1. `py_compile` 检查 Python 文件
2. Flask `test_client()` 逐页检查：`/ /materials /products /boms /orders /inventory /healthz`
3. 依次 POST：物料、产品、BOM 表头、BOM 行、库存、订单
4. 再 POST `/run_mrp_page` 验证新录数据能跑通
5. 最后再启动 gunicorn 并做浏览器验收

### 网络与稳定性经验（本次补充）
- `localhost.run` 匿名隧道会频繁断，地址会不断变化，只适合临时演示
- 若用户追求“稳定链接”，要尽早说明：
  - 局域网优先：直接给内网 IP（如 `http://192.168.x.x:5050`）
  - 公网稳定访问：必须走固定公网入口（云服务器 / Cloudflare Tunnel / 固定域名）
- 看到机器有公网出口 IP 不代表能直接外网访问应用；若浏览器访问公网 IP:端口返回异常（如 502），不能把它当稳定方案承诺给用户

## 从“演示原型”升级到“桌面测试后台”的经验（本次新增）

当用户需求从：
- “先做个 H5 演示”
转成：
- “先别管手机版，先把桌面网页端做好”
- “要能录生产测试数据”
- “要按规格书结构逐步补模块”

不要继续在 H5 交互细节上打补丁，而应**立刻切换到桌面管理后台思路**。

### 推荐升级路径

#### 1. 首页交互从 JS 点击流改成服务端表单流
对验证型后台，优先：
- `<form method="post">`
- 服务端渲染结果

而不是把核心流程绑死在前端 JS 点击事件上。

适用场景：
- 订单选择 → 执行试算
- 新建主数据 → 返回列表
- 手工录入测试数据

优点：
- 更稳
- 浏览器兼容问题更少
- 更适合业务测试用户

#### 2. 先上“主数据台账”，别急着做花哨前端
当用户明确说“我要录一些生产数据做测试”，应优先补下面几页：

- 物料主数据
- 产品主数据 / 产品计划策略
- BOM表头 / BOM行
- 订单录入（最好按“订单快照”思路）
- 批次质量库存

这是制造业 / MRP 验证原型最关键的一层。

#### 3. Demo 阶段用 JSON 持久化非常合适
如果用户当前目标是：
- 先验证业务流程
- 还没要求多人并发
- 还没要求复杂权限

那就不要一开始上数据库迁移和 ORM。优先直接做：

```text
project/data/
  products.json
  materials.json
  bom_headers.json
  bom_lines.json
  orders.json
  inventory.json
```

再用统一的数据访问层（例如 `data_store.py`）做：
- bootstrap 默认数据
- 读取 / 写回
- 日期 / 枚举转换
- 计算字段生成

这比把 JSON 读写逻辑散落在 route 里稳得多。

#### 4. 如果用户给了规格书/指导文件，优先按“模块映射”补能力
不要泛泛地“优化页面”，而要把文档中的业务对象映射到系统模块。

这次实践里，优先补这 4 块最划算：

1. **策略参数模板**
   - 对应：产品策略 / MRP 参数
   - 页面：策略参数配置

2. **质量规则模板**
   - 对应：`quality_rule_template_header/line`
   - 页面：模板 + 规则行

3. **订单快照**
   - 对应：`sales_order_recipe_snapshot`
   - 字段：`priority`、`policy_id`、`recipe_header_id`、`snapshot_status`

4. **批次质量库存**
   - 对应：`batch_quality_lot`
   - 新增：模板选择、自动评分、自动计划等级

#### 5. 自动评分比手输 quality_score 更贴近规格书
如果规格书里有“质量规则模板”概念，库存录入时不要只让用户手输 `quality_score`。
应该：
- 录入原始属性（长度、强力、马值、含杂、回潮/含水、白度等）
- 根据质量规则模板自动算分
- 自动生成计划等级（如 P1/P2/P3/P4）

这样后面锁批和 MRP 试算才更像真正业务流程。

#### 6. 导航结构要跟规格书对象一致
对桌面后台，左侧导航建议按业务对象组织，而不是按“页面风格”组织。

本次实践有效的菜单结构：
- MRP试算
- 策略参数
- 质量规则
- 物料主数据
- 产品主数据
- BOM主数据
- 订单快照
- 批次质量库存

这比“首页 / 展示页 / 分析页”更适合业务录数与验证。

### 一个很实用的判断原则

如果用户说的是：
- “这个按钮有问题，先不做手机版了”
- “我要录数据测试”
- “按规格书思路改”

正确动作不是继续修动效，而是：

**把项目从前端展示原型切到桌面业务后台原型。**

## 桌面录入后台经验（本次新增）

当用户目标从“演示页面”切换为“业务测试后台”时，不要继续沿着 H5/移动端思路硬做。
应立即切到 **桌面 Web 管理端**，优先保证：
- 页面稳定
- 录入效率高
- 表格与批量信息可读
- 业务对象能形成闭环台账

### 什么时候要放弃 H5，改做桌面后台
如果用户出现以下诉求，应优先切换桌面方案：
- “按钮点击报错 / 页面切换不了”
- “先别做手机版”
- “我要录大量测试数据”
- “需要物料/BOM/订单/库存维护后台”
- “要给业务做模拟测试，不只是演示”

### 推荐结构（适合制造/MRP 原型）

```text
project/
├── mrp_web.py              # Flask 路由
├── data_store.py           # JSON 持久化、默认数据、读写封装
├── mrp_core.py             # 纯业务计算
├── mrp_models.py           # dataclass 模型
├── data/
│   ├── products.json
│   ├── materials.json
│   ├── bom_headers.json
│   ├── bom_lines.json
│   ├── orders.json
│   ├── inventory.json
│   ├── strategy_params.json
│   ├── quality_rule_headers.json
│   ├── quality_rule_lines.json
│   ├── lock_headers.json
│   ├── lock_lines.json
│   ├── supply_suggestions.json
│   └── planning_exceptions.json
└── templates/
```

### JSON 持久化比纯 mock 更适合测试后台
当用户要反复录测试数据，但还没到正式数据库阶段时：
- 先不要急着上 MySQL/Postgres
- 用 `data_store.py + data/*.json` 就够
- 核心是把读写、默认初始化、序列化集中管理

关键做法：
- 单独封装 `bootstrap()` 初始化默认数据
- `_write_json()` 内部统一做 dataclass/date/enum 转 plain object
- 所有页面只调用 `all_xxx_rows()` / `save_xxx()`，不要自己散写文件

### 规格书驱动扩展的最短路径
当用户给出一份业务规格书，不要一口气全实现。
先补这 4 类“最能体现规格书结构”的模块：
1. **策略参数**（如 product_plan_policy / mrp_parameter）
2. **质量规则模板**（quality_rule_template_header/line）
3. **订单快照**（sales_order_recipe_snapshot）
4. **批次质量库存**（batch_quality_lot + 自动评分）

原因：
- 这几块最容易映射规格书字段
- 能迅速把系统从“演示页”升级成“测试后台”
- 后续锁批、建议、异常都能挂在这些对象上

### 质量规则配置化的实用做法
Demo 阶段不要等产品经理把全部公式定完。
可先：
- 做 `quality_rule_headers.json` / `quality_rule_lines.json`
- 用 `rule_type + operator + target_min/max + weight_percent`
- 录入批次时按模板自动计算 `quality_score`
- 再根据统一阈值映射 `planning_grade`

即使公式还不完美，也比硬编码在页面里强，后续易调整。

### 台账闭环要尽早落地
一旦 MRP 试算已经能产出：
- 锁批结果
- 供给建议
- 异常信息

就应该立即把这些结果落成台账，而不是只显示在页面上。

建议新增：
- `lock_headers.json`
- `lock_lines.json`
- `supply_suggestions.json`
- `planning_exceptions.json`

并在 `run_mrp_page()` / `run_mrp` 后调用统一函数，例如：

```python
def persist_mrp_ledgers(order_no, report):
    ...
```

把试算结果写入台账。

### 台账最小闭环动作
不要只做查询页面。最小闭环至少要有：
- 锁批状态更新
- 锁批释放/解锁
- 供应建议状态流转（待确认/已确认/已下达/已关闭）
- 异常审批状态流转（待审批/已审批/已关闭）
- 删除动作

这是业务测试后台和静态原型的分水岭。

### 重要经验：外网临时隧道不稳定，不要把它当正式入口
`localhost.run` 这类匿名临时隧道：
- 适合临时演示
- 地址会频繁变化
- 会无预警断线
- 不适合业务测试正式入口

如果用户要求“稳定外网访问”，应明确建议：
- Cloudflare Tunnel + 自有域名
- 或云服务器固定部署

## 已知限制

- Flask debug=True 自动重载，生产环境应关闭
- 无用户认证，限于内网原型使用
- 大量数据时前端渲染会慢（无分页）
- `localhost.run` 这类隧道只适合临时外网演示，不适合正式生产
- JSON 持久化适合测试录入，不适合多人并发和正式生产
- JSON 持久化适合原型验证；如果进入多人协作或频繁改数，应切换 SQLite / PostgreSQL
