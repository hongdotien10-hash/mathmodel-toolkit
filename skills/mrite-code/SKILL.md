---
name: 逐题求解
description: 按求解计划逐题编写Python代码求解，包含数据预处理、建模、求解、画图、灵敏度分析
trigger:
  - "逐题求解"
  - "开始求解问题"
  - "求解问题"
  - "运行模型"
---

# 逐题求解

## 目的

为每个子问题编写Python求解脚本，先算后画，每题至少4-6张图，完成灵敏度分析。

## 代码结构（每个问题一个py文件）

### 文件命名与位置

```
求解/
├── 问题一/
│   ├── 问题一_<描述>.py
│   ├── 图片/
│   └── 结果/
├── 问题二/
│   ...
```

### 公共头部（每个脚本复制）

```python
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os, warnings
warnings.filterwarnings('ignore')

# 中文字体（跨平台）
plt.rcParams['font.sans-serif'] = ['STHeiti', 'SimHei', 'Heiti TC',
    'Arial Unicode MS', 'Hiragino Sans GB', 'PingFang SC',
    'Microsoft YaHei', 'Songti SC', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['savefig.bbox'] = 'tight'

def despine(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(BASE_DIR, '图片')
OUT_DIR = os.path.join(BASE_DIR, '结果')
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

def save_fig(fig, name_cn):
    fig.savefig(os.path.join(FIG_DIR, name_cn))
    plt.close(fig)

def save_csv(df, name_cn):
    df.to_csv(os.path.join(OUT_DIR, name_cn), index=False, encoding='utf-8-sig')
```

## 两阶段执行（严格执行）

### 第一阶段：纯计算

```
数据加载 → 预处理 → 建模 → 求解 → 得到所有数值结果
```

**必须打印的统计量**（供论文引用）：
```python
def print_stats(data, name):
    print(f"\n=== {name} 统计 ===")
    print(f"样本数: {len(data)}")
    print(f"最小值: {data.min():.4f}")
    print(f"最大值: {data.max():.4f}")
    print(f"均值: {data.mean():.4f}")
    print(f"标准差: {data.std():.4f}")
    print(f"变异系数(CV): {data.std()/data.mean():.4f}")
    print(f"振幅: {data.max()-data.min():.4f}")
```

### 第二阶段：检查 + 绘图

在确认所有计算结果正确后，再进行画图。

## 各类型问题的建模模板

### 优化类
```python
# 步骤1：目标函数的建立
# 步骤2：约束条件的建立（逐个约束编号）
# 步骤3：核心机理建模（子模型）
# 步骤4：求解算法实现

from scipy.optimize import minimize, differential_evolution
# 或使用遗传算法、粒子群等
```

### 评价类
```python
# 步骤1：评价指标体系构建
# 步骤2：指标权重确定（熵权法/AHP）
# 步骤3：综合评价（TOPSIS/模糊综合评价）

from sklearn.preprocessing import MinMaxScaler
# 熵权法计算权重
def entropy_weight(matrix):
    # 归一化
    p = matrix / matrix.sum(axis=0)
    # 计算熵值
    e = -np.sum(p * np.log(p + 1e-10), axis=0) / np.log(len(matrix))
    # 计算权重
    w = (1 - e) / np.sum(1 - e)
    return w
```

### 分类/预测类
```python
# 步骤1：特征工程（相关性分析+降维+特征选择）
# 步骤2：模型构建（完整数学表达式）
# 步骤3：模型训练与评估（交叉验证+指标）

from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import r2_score, mean_squared_error, accuracy_score
```

### 机理分析类
```python
# 步骤1：机理分析框架（核心变量关系）
# 步骤2：关键变量关系建模（逐个关系+公式+推导）
# 步骤3：模型整合与参数确定（联立方程+参数辨识）
```

## 绘图规范

### 绘图库限制

**只允许 matplotlib**，严禁 seaborn 及任何其他可视化库。

| 禁止 | 替代 |
|------|------|
| `sns.set_style()` | `plt.rcParams` + `ax.grid(alpha=0.3, linestyle='--')` |
| `sns.color_palette()` | `plt.cm.viridis(np.linspace(0.1, 0.9, n))` |
| `sns.heatmap()` | `ax.imshow()` + `plt.colorbar()` |
| `sns.despine()` | `ax.spines['top'].set_visible(False)` 等 |

### 图表美观设置
```python
# 配色方案
colors = plt.cm.viridis(np.linspace(0.1, 0.9, n))  # 或 RdBu_r, tab10, Set3

# 折线图
ax.plot(x, y, linewidth=1.5, marker='o', markersize=4)

# 柱状图
ax.bar(x, y, edgecolor='white', linewidth=0.5, color=colors)

# 散点图
ax.scatter(x, y, alpha=0.7, edgecolors='black', linewidth=0.5)

# 通用
ax.grid(alpha=0.3, linestyle='--')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
# 图上不画 set_title()，标题由论文 \caption{} 承担
```

### 图表类型与场景

| 图表类型 | 适用场景 | 最低要求 |
|----------|----------|----------|
| 柱状图 | 类别对比、分组对比 | 每题至少1张 |
| 折线图 | 趋势变化、时间序列 | 有趋势必画 |
| 热力图 | 矩阵数据、相关性 | 有矩阵必画 |
| 散点图 | 两变量关系、分布 | 有回归必画 |
| 饼图 | 占比构成 | 有占比必画 |
| 箱线图 | 多组分布对比 | 有分组必画 |

每题至少 4-6 张图，覆盖主要分析维度，多多益善。

### 保存图片
```python
fig, ax = plt.subplots(figsize=(10, 6))
# ... 画图 ...
ax.set_xlabel('X轴标签')
ax.set_ylabel('Y轴标签')
ax.legend(loc='best')
despine(ax)
save_fig(fig, '问题X_描述.png')  # 只用 save_fig，不用 plt.savefig
```

## 灵敏度分析（前置）

每个建模问题在求解阶段就测试关键参数：

```python
# 参数扫描示例
param_range = np.linspace(0.1, 2.0, 20)
results = []
for param in param_range:
    result = run_model(param=param)  # 对每个参数值求解
    results.append(result)

# 画灵敏度曲线
fig, ax = plt.subplots()
ax.plot(param_range, results, 'o-', linewidth=1.5)
ax.set_xlabel('参数值')
ax.set_ylabel('结果指标')
despine(ax)
save_fig(fig, '问题X_灵敏度分析.png')

# 输出最佳参数
best_idx = np.argmax(results)  # 或argmin
print(f"最佳参数: {param_range[best_idx]}, 最佳结果: {results[best_idx]}")
```

## 错误处理

```python
# 每个脚本外部包裹try-except
try:
    # 全部求解逻辑
    ...
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
    # 自动修复常见问题后重试
```

常见问题自动修复：
- 中文字体渲染警告 → 调整字体配置
- 数值溢出 → 数据标准化
- 收敛失败 → 增加迭代次数或换初始值
- 内存不足 → 分批处理数据

## 输出

每个问题的脚本运行后输出：
1. 控制台打印所有统计量（供论文引用）
2. `图片/` 目录下至少 4-6 张PNG（150dpi）
3. `结果/` 目录下的CSV文件

**脚本报错必须修复后重跑，通过后才能进入下一问。**