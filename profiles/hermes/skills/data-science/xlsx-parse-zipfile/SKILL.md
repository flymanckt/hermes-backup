---
name: xlsx-parse-zipfile
description: Parse xlsx files using Python stdlib zipfile+xml when openpyxl is unavailable. Used when reading Excel attachments in conversations.
version: 1.0.0
---

# xlsx-parse-zipfile

## 触发条件
读取 .xlsx 文件时，环境中没有 `openpyxl` 且 `pip` 不可用（hermes WSL 环境常见）。

## 方法
用 Python 标准库 `zipfile` + `xml.etree.ElementTree` 直接解析 xlsx 的 XML 结构。

## 标准步骤

1. 用 `zipfile.ZipFile(path, 'r')` 打开文件
2. 读取 `xl/sharedStrings.xml` → 解析所有共享字符串
3. 读取 `xl/workbook.xml` → 解析 sheet 名称列表
4. 逐个读取 `xl/worksheets/sheet{N}.xml` → 按行解析单元格
5. 单元格 `t='s'` 时，从 sharedStrings 取值；否则直接取 `v` 元素文本

## 关键代码模板

```python
import zipfile, xml.etree.ElementTree as ET

def read_xlsx(path):
    NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    with zipfile.ZipFile(path, 'r') as z:
        # shared strings
        ss = []
        ss_root = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in ss_root.findall(f'{{{NS}}}si'):
            text = ''.join(t.text or '' for t in si.iter(f'{{{NS}}}t'))
            ss.append(text)
        
        # sheet names
        wb = ET.fromstring(z.read('xl/workbook.xml'))
        sheets = [s.get('name') for s in wb.iter(f'{{{NS}}}sheet')]
        
        # each sheet
        results = []
        for i, name in enumerate(sheets, 1):
            ws = ET.fromstring(z.read(f'xl/worksheets/sheet{i}.xml'))
            rows = []
            for row in ws.iter(f'{{{NS}}}row'):
                row_data = []
                for c in row:
                    t = c.get('t', '')
                    v_el = c.find(f'{{{NS}}}v')
                    if v_el is not None and v_el.text:
                        row_data.append(ss[int(v_el.text)] if t == 's' else v_el.text)
                    else:
                        row_data.append('')
                if any(row_data):
                    rows.append(row_data)
            results.append((name, rows))
        return results
```

## 已知限制
- 不保留单元格格式、公式、样式
- 只读值（适合读取数据清单、配置表）
- 如果文件有密码保护，此方法不适用

## 验证
读取后 print 第一个 sheet 的第一行确认表头是否正确。
