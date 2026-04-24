---
name: feishu-docx-api
description: 通过飞书开放平台 API 直接新建并写入飞书文档（Docx），适用于机器人已具备文档权限、但浏览器未登录或不适合走网页交互的场景。
---

# Feishu Docx API 直写技能

## 适用场景
当用户说：
- “写入飞书文档”
- “新建一篇飞书文档”
- “把内容同步到飞书文档里”
- “这个飞书机器人已经开通了新建文档权限”

且当前浏览器未登录、扫码不方便、或网页交互不稳定时，优先使用本技能。

## 核心结论
不要先假设必须网页登录。
先检查环境变量里是否存在飞书开放平台凭证：
- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`

如果存在，优先走 API：
1. 获取 `tenant_access_token`
2. 创建 Docx 文档
3. 通过 blocks/children 接口写入内容
4. 返回文档 ID 和可打开链接

## 已验证可用的接口

### 1）获取 tenant access token
```bash
python3 - <<'PY'
import os, json, urllib.request
app_id=os.environ['FEISHU_APP_ID']
app_secret=os.environ['FEISHU_APP_SECRET']
url='https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
req=urllib.request.Request(url, data=json.dumps({'app_id':app_id,'app_secret':app_secret}).encode(), headers={'Content-Type':'application/json'})
with urllib.request.urlopen(req, timeout=30) as r:
    print(r.read().decode())
PY
```

### 2）创建文档
```bash
python3 - <<'PY'
import os, json, urllib.request
app_id=os.environ['FEISHU_APP_ID']
app_secret=os.environ['FEISHU_APP_SECRET']
# token
req=urllib.request.Request('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal', data=json.dumps({'app_id':app_id,'app_secret':app_secret}).encode(), headers={'Content-Type':'application/json'})
with urllib.request.urlopen(req, timeout=30) as r:
    token=json.loads(r.read().decode())['tenant_access_token']
# create doc
req=urllib.request.Request('https://open.feishu.cn/open-apis/docx/v1/documents', data=json.dumps({'title':'API测试文档'}).encode(), headers={'Content-Type':'application/json','Authorization':'Bearer '+token}, method='POST')
with urllib.request.urlopen(req, timeout=30) as r:
    print(r.read().decode())
PY
```

### 3）写入正文块
**关键点：** 直接向根 block 的 children 追加 paragraph/text block。

已验证可用的 payload 结构：
```json
{
  "children": [
    {
      "block_type": 2,
      "text": {
        "elements": [
          {
            "text_run": {
              "content": "测试段落A"
            }
          }
        ],
        "style": {
          "align": 1
        }
      }
    }
  ],
  "index": -1,
  "client_token": "uuid"
}
```

接口：
```text
POST /open-apis/docx/v1/documents/{document_id}/blocks/{document_id}/children
```

### 4）读取回写后的文本验证
```text
GET /open-apis/docx/v1/documents/{document_id}/raw_content
```

## 可直接复用的 Python 模板
```python
import os, json, time, uuid, urllib.request

def api(method, url, token=None, data=None, attempts=4):
    headers={'Content-Type':'application/json'}
    if token:
        headers['Authorization']='Bearer '+token
    payload = json.dumps(data).encode() if data is not None else None
    last=None
    for i in range(attempts):
        try:
            req=urllib.request.Request(url, data=payload, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            last=e
            time.sleep(1.5*(i+1))
    raise last

app_id=os.environ['FEISHU_APP_ID']
app_secret=os.environ['FEISHU_APP_SECRET']
resp=api('POST','https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal', data={'app_id':app_id,'app_secret':app_secret})
token=resp['tenant_access_token']

create=api('POST','https://open.feishu.cn/open-apis/docx/v1/documents', token=token, data={'title':'示例文档'})
doc_id=create['data']['document']['document_id']

paragraphs=['第一段','第二段','第三段']
children=[]
for p in paragraphs:
    children.append({
        'block_type':2,
        'text':{
            'elements':[{'text_run':{'content':p}}],
            'style':{'align':1}
        }
    })

url=f'https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children'
for i in range(0, len(children), 5):
    batch=children[i:i+5]
    api('POST', url, token=token, data={
        'children': batch,
        'index': -1,
        'client_token': str(uuid.uuid4())
    })

raw=api('GET', f'https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/raw_content', token=token)
print(doc_id)
print(raw['data']['content'])
```

## 实战经验 / 坑点

### 1）不要先执着于网页登录
这次最初走了浏览器登录页，结果卡在扫码登录。后来发现环境里已有：
- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`

结论：**如果用户说机器人已有飞书文档权限，先查环境变量，再决定是否需要网页登录。**

### 2）创建接口可用
已验证：
```text
POST https://open.feishu.cn/open-apis/docx/v1/documents
```
返回 `document_id`。

### 3）写入时用 `text`，不是一开始猜的 `paragraph`
尝试过程中，`block_type:2 + text` 的结构可直接成功。
不要先凭印象写复杂结构，先小样本验证一个 block。

### 4）网络偶发断连，要加重试
实测会出现：
- `RemoteDisconnected: Remote end closed connection without response`

处理方式：
- 封装 `api()` 重试
- 分批写入（建议每批 5 个 block）
- 每批之间 sleep 0.5~1 秒

### 5）文档链接不要只猜 docs.feishu.cn
`drive/v1/metas/batch_query` 能拿到标题等元信息，但 `url` 可能为空。
实践中可返回：
- 文档 ID
- 常见打开链接格式：`https://<tenant-domain>.feishu.cn/docx/<document_id>`

如果 tenant 域名未知，至少要给出 `document_id`，避免用户拿不到结果。

### 6）验证必须做
写入后必须调用：
```text
GET /docx/v1/documents/{document_id}/raw_content
```
确认内容确实落库，而不是只返回“创建成功”。

## 推荐工作流
1. 用户要求写飞书文档
2. 先检查环境变量是否有飞书凭证
3. 有凭证：直接 API 创建并写入
4. 没凭证：再考虑浏览器登录或让用户提供文档链接/人工配合
5. 写入后读取 raw_content 验证
6. 返回标题、document_id、可打开链接

## 完成定义
满足以下条件才算完成：
- 文档创建成功
- 正文内容写入成功
- `raw_content` 验证通过
- 已把 `document_id` 和打开方式回给用户
