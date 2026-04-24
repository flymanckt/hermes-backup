---
name: xlsx-zipfile-parse
description: 用 Python 标准库（zipfile + xml.etree.ElementTree）直接解析 xlsx 文件，不需要 openpyxl/pandas。适用场景：openpyxl 不可用、无 pip、容器环境最小化依赖时。
version: 1.0.0
---

# XLSX 直接解析（标准库法）

无需 `pip install openpyxl`，纯 Python stdlib 即可读取 xlsx 内容。

## 核心原理

xlsx 本质是 ZIP 包，内含 XML 文件：
- `xl/sharedStrings.xml` → 共享字符串表
- `xl/worksheets/sheet{N}.xml` → 各工作表数据
- `xl/workbook.xml` → 工作表名称列表

## 标准模板代码

```python
import zipfile, xml.etree.ElementTree as ET

def read_xlsx(path):
    NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    
    with zipfile.ZipFile(path, 'r') as z:
        # 1. 读取共享字符串表（所有文本值）
        ss_root = ET.fromstring(z.read('xl/sharedStrings.xml'))
        shared_strings = []
        for si in ss_root.findall(f'{{{NS}}}si'):
            text = ''.join(t.text or '' for t in si.iter(f'{{{NS}}}t'))
            shared_strings.append(text)
        
        # 2. 读取工作表名称
        wb_root = ET.fromstring(z.read('xl/workbook.xml'))
        sheets = []
        for s in wb_root.iter(f'{{{NS}}}sheet'):
            sheets.append(s.get('name'))
        
        # 3. 逐 sheet 读取数据行
        results = {}
        for i, name in enumerate(sheets, 1):
            ws_root = ET.fromstring(z.read(f'xl/worksheets/sheet{i}.xml'))
            rows = []
            for row in ws_root.iter(f'{{{NS}}}row'):
                row_data = []
                for c in row:
                    t = c.get('t', '')
                    v_el = c.find(f'{{{NS}}}v')
                    if v_el is not None and v_el.text is not None:
                        row_data.append(
                            shared_strings[int(v_el.text)] if t == 's' else v_el.text
                        )
                    else:
                        row_data.append('')
                if any(row_data):
                    rows.append(row_data)
            results[name] = rows
        
        return results
```

## 输出格式

```python
{
    'Sheet1': [['列1', '列2', '列3'], ['值1', '值2', '值3'], ...],
    'Sheet2': [...],
    ...
}
```

## 适用条件

- xlsx 无公式/样式/宏，仅需读取数据值
- 字符串值走 sharedStrings（`t='s'`），数字直接读 `v`
- 布尔值（`t='b'`）、日期等类型可按需扩展解析逻辑
