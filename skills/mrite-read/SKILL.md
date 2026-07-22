---
name: 读取题目
description: 读取数学建模竞赛的题目文件(PDF/DOCX)和数据文件(xlsx/docx)，输出数据总览
trigger:
  - "读取题目"
  - "读取数据"
  - "分析题目"
  - "查看赛题"
---

# 读取题目与数据

## 目的

完整读取赛题和数据，输出数据总览，自动识别问题数量。

## 执行步骤

### 1. 读取题目文件

```python
# 如果是PDF
from PyPDF2 import PdfReader
reader = PdfReader("题目/题目.pdf")
for page in reader.pages:
    print(page.extract_text())

# 如果是DOCX
from docx import Document
doc = Document("题目/题目.docx")
for para in doc.paragraphs:
    print(para.text)
```

### 2. 读取数据文件（全量读取）

```python
import pandas as pd
import openpyxl

# 对于xlsx，先检查所有sheet
wb = openpyxl.load_workbook("数据/data.xlsx", data_only=True)
print(f"Sheet 数量: {len(wb.sheetnames)}")
print(f"Sheet 名称: {wb.sheetnames}")

for sheet_name in wb.sheetnames:
    ws = wb[sheet_name]
    print(f"\n=== {sheet_name} ===")
    print(f"行数: {ws.max_row}, 列数: {ws.max_column}")
    # 检查是否有合并单元格
    print(f"合并单元格: {ws.merged_cells.ranges if ws.merged_cells.ranges else '无'}")

# 然后pandas读取
for sheet_name in wb.sheetnames:
    df = pd.read_excel("数据/data.xlsx", sheet_name=sheet_name, header=None)
    print(f"\n=== {sheet_name}: {df.shape[0]}行 × {df.shape[1]}列 ===")
    print(f"前5行:\n{df.head()}")
```

### 3. 数据质量检查（必须逐项输出）

| 检查项 | 方法 | 输出要求 |
|--------|------|----------|
| 列数一致性 | 逐行检查每行列数是否一致 | 异常行号+列数 |
| 数据类型一致性 | 每列检查是否数值列混入文字 | 异常行号+内容 |
| 合并单元格 | openpyxl检查 | 合并区域列表 |
| 多级表头 | 目视前5行判断 | 标注表头行号 |
| 空行分隔 | 检查全空行 | 空行位置 |
| 底部备注行 | 检查末尾非数据行 | 备注内容 |
| 隐藏sheet | wb.sheetnames检查 | 如有则列出 |

### 4. 打印数据总览

```python
for sheet_name in wb.sheetnames:
    df = pd.read_excel("数据/data.xlsx", sheet_name=sheet_name)
    print(f"\n{'='*60}")
    print(f"Sheet: {sheet_name}")
    print(f"规模: {df.shape[0]}行 × {df.shape[1]}列")
    print(f"列名: {list(df.columns)}")
    print(f"数据类型:\n{df.dtypes}")
    print(f"缺失值:\n{df.isnull().sum()}")
    print(f"数值列统计:\n{df.describe()}")
    # 异常行
    for col in df.select_dtypes(include='number').columns:
        # 检测明显异常值（超过3倍标准差）
        if len(df[col].dropna()) > 0:
            mean, std = df[col].mean(), df[col].std()
            outliers = df[abs(df[col] - mean) > 3*std]
            if len(outliers) > 0:
                print(f"异常值 [{col}]: {len(outliers)}行")
```

### 5. 自动识别问题数量

从题目文本中搜索"问题一/二/三/四/五/1/2/3/4/5"等模式，输出：
- 问题总数 N
- 每问的简要描述（1-2句）
- 每问的输入数据/附件
- 每问的类型（建模求解/数据分析/建议总结）

## 输出

完成后输出：
1. 题目摘要（每问一句话）
2. 数据总览表（每个sheet的行列数、列名类型、缺失值、异常行）
3. 问题数量N及每问类型分类