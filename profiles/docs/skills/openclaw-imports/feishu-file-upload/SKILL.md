---
name: feishu-file-upload
description: Upload files to Feishu and send as attachments via the Feishu Open API. Use when send_message tool with MEDIA isn't working.
tags:
  - feishu
  - lark
  - file-upload
  - attachment
  - docx
---

# Feishu File Upload & Send — Direct API

## When to Use
When you need to send a file (docx, xlsx, PDF, PPTX, etc.) to a Feishu user via the Feishu Open API, and the Hermes send_message tool with MEDIA isn't working or accessible.

## Prerequisites
- `FEISHU_APP_ID` and `FEISHU_APP_SECRET` from the Feishu app credentials
- Target user's `open_id` (starts with `ou_`) or chat_id
- File path on local filesystem

## Step 1: Get Tenant Access Token

```bash
TOKEN_RESP=$(curl -s --connect-timeout 10 -m 30 \
  https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal \
  -X POST \
  -H "Content-Type: application/json" \
  -d "{\"app_id\":\"$FEISHU_APP_ID\",\"app_secret\":\"$FEISHU_APP_SECRET\"}")

TOKEN=$(echo "$TOKEN_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tenant_access_token',''))")
```

Or with Python:
```python
import requests
resp = requests.post(
    'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
    json={'app_id': FEISHU_APP_ID, 'app_secret': FEISHU_APP_SECRET},
    timeout=30
)
token = resp.json()['tenant_access_token']
```

## Step 2: Upload File

**Critical**: The Feishu file upload API requires THREE separate multipart fields:
```
file_type=doc       # e.g. "doc" for .docx, "xlsx" for .xlsx
file_name=xxx.docx  # the display filename
file=@<filepath>       # the binary file
```

Wrong (returns code 234001):
```bash
curl -F "file=@file.docx;type=...;filename=file.docx" ...
```

Correct:
```bash
curl -s --connect-timeout 30 -m 60 \
  "https://open.feishu.cn/open-apis/im/v1/files" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file_type=doc" \
  -F "file_name=BIT003.docx" \
  -F "file=@/path/to/file.docx"
```

File type mappings:
- `.docx` → `file_type=doc`
- `.xlsx` → `file_type=xlsx`
- `.pdf` → `file_type=pdf`
- `.pptx` → `file_type=pptx`
- `.mp4` / video → `file_type=mp4`
- other → `file_type=file`

Success: `{"code":0,"data":{"file_key":"file_v3_..."},"msg":"success"}`

## Step 3: Send File Message

```python
import requests, json

resp = requests.post(
    'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id',
    headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    },
    json={
        'receive_id': '<user_open_id>',
        'msg_type': 'file',
        'content': json.dumps({'file_key': '<file_key_from_step2>'})
    },
    timeout=30
)
```

## Key Pitfalls

1. **execute_code sandbox httpx timeout** — httpx library times out in sandbox even though network is fine. **Always use curl CLI** (fast, ~0.2s), not httpx/python requests in sandbox context.
2. **Missing file_type/file_name fields** — Upload fails with code 234001 if omitted or embedded in the file field. These must be separate multipart fields.
3. **Bearer token format** — Must be exactly `Bearer <token>` with a space.
4. **receive_id_type** — Use `open_id` when sending to user open_ids (ou_...), not chat_ids.

## Credentials Path
`~/.hermes/profiles/consulting/.env` — contains `FEISHU_APP_ID` and `FEISHU_APP_SECRET`.
