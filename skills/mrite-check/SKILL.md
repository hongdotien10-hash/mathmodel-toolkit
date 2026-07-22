---
name: 代码检查
description: 检查数学建模Python求解代码的规范性，包括绘图标准、执行顺序、依赖限制、统计输出
trigger:
  - "代码检查"
  - "检查代码"
  - "代码规范"
  - "验证脚本"
---

# 代码检查

## 目的

检查数学建模求解脚本是否符合项目规范，自动发现并修复问题。

## 检查清单

### 1. 导入检查

**禁止的导入：**
```python
# ❌ 禁止
import seaborn as sns
import plotly
import plotnine
import altair
import bokeh
import holoviews

# ✅ 允许
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats, optimize
from sklearn import *
import warnings
warnings.filterwarnings('ignore')
```

**检查命令：**
```bash
grep -rn 'seaborn\|plotly\|plotnine\|altair\|bokeh\|holoviews' 求解/
```

### 2. 执行模式检查

**必须使用 Agg 后端：**
```python
matplotlib.use('Agg')  # ✅ 必须
```

**检查命令：**
```bash
grep -rn "matplotlib.use" 求解/
# 每个py文件必须包含 matplotlib.use('Agg')
```

### 3. 字体配置检查

每个脚本必须包含中文字体配置：
```python
plt.rcParams['font.sans-serif'] = ['STHeiti', 'SimHei', ...]
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['savefig.bbox'] = 'tight'
```

### 4. 两阶段执行检查

脚本必须遵循"先算后画"顺序：
```python
# ✅ 第一阶段：纯计算
# 数据加载 → 预处理 → 建模 → 求解 → 数值结果

# ✅ 打印统计量
print_stats(data, '数据集名')  # min/max/mean/std/CV/amplitude

# ✅ 第二阶段：画图
# 所有计算完成后才开始画图
```

**检查要点：**
- 没有在计算之前画图
- 画图前打印了所有必需的统计量
- `plt.savefig` 在 `plt.close()` 之前

### 5. set_title() 检查

图上不能有 `set_title()`，标题由论文 `\caption{}` 承担。

**检查命令：**
```bash
grep -rn '\.set_title(' 求解/
# 应该返回空或仅在注释中
```

### 6. 图表数量检查

每题至少 4-6 张图：

```bash
# 检查每个问题目录下的图片数量
for dir in 求解/问题*/图片/; do
  count=$(ls "$dir"*.png 2>/dev/null | wc -l)
  echo "$dir: $count 张图"
  if [ "$count" -lt 4 ]; then
    echo "  ⚠ 不足4张，需补充"
  fi
done
```

### 7. 输出文件检查

```bash
# 检查CSV输出
for dir in 求解/问题*/结果/; do
  echo "=== $dir ==="
  ls "$dir"*.csv 2>/dev/null || echo "  无CSV输出"
done

# 检查预处理数据
ls 求解/预处理数据.csv 2>/dev/null || echo "  预处理数据.csv 不存在（仅问题1需要）"
```

### 8. 代码结构检查

```python
# 每个脚本必须包含
def despine(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

# 公共函数
def save_fig(fig, name_cn): ...
def save_csv(df, name_cn): ...
def print_stats(data, name): ...

# 路径定义
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(BASE_DIR, '图片')
OUT_DIR = os.path.join(BASE_DIR, '结果')
```

### 9. 错误处理检查

```bash
# 检查是否有 try-except 保护
grep -n 'try:' 求解/问题*/*.py
grep -n 'except' 求解/问题*/*.py
```

### 10. 中文字符检查

文件编码必须是 UTF-8，文件名必须是中文：

```bash
# 检查文件名
ls -la 求解/问题*/

# 检查文件编码
file -bi 求解/问题*/*.py
# 应为 utf-8
```

## 自动修复

运行检查后自动修复以下问题：

| 问题 | 自动修复 |
|------|----------|
| 缺少 `matplotlib.use('Agg')` | 自动在 import matplotlib 后添加 |
| 使用了 sns.xxx | 替换为 matplotlib 等价代码 |
| 有 `set_title()` | 注释掉或删除 |
| 缺少字体配置 | 自动添加标准配置块 |
| 缺少 `despine()` | 自动添加函数定义 |
| 图片不足4张 | 补充缺失的图表类型 |
| 缺少统计输出 | 在计算完成后添加 print_stats 调用 |

## 输出

生成检查报告：
```
=== 代码规范检查报告 ===
检查目录: 求解/
检查时间: 自动

问题汇总:
  [ERROR] 0 项（必须修复）
  [WARNING] X 项（建议修复）
  [OK] Y 项通过

详情:
  ...
```