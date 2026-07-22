---
name: 画图
description: 使用matplotlib生成论文级质量图表，支持柱状图、折线图、热力图、散点图、饼图、箱线图等
trigger:
  - "画图"
  - "绘制图表"
  - "生成图表"
  - "优化图表"
  - "美化图表"
---

# 画图技能

## 目的

使用 matplotlib 生成论文级质量图表，每张图150dpi，中文坐标轴和图例。

## 环境配置（必须）

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# 中文字体（跨平台兼容）
plt.rcParams['font.sans-serif'] = ['STHeiti', 'SimHei', 'Heiti TC',
    'Arial Unicode MS', 'Hiragino Sans GB', 'PingFang SC',
    'Microsoft YaHei', 'Songti SC', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['savefig.bbox'] = 'tight'
```

## ⛔ 唯一绘图库

**只允许 matplotlib**，严禁 seaborn、plotly、plotnine、altair、bokeh、holoviews。

| 禁止 | 替代方案 |
|------|----------|
| `import seaborn as sns` | matplotlib 原生 API |
| `sns.set_style()` | `plt.rcParams` + `ax.grid()` |
| `sns.color_palette()` | `plt.cm.viridis(np.linspace(0.1, 0.9, n))` |
| `sns.heatmap()` | `ax.imshow()` + `plt.colorbar()` |
| `sns.despine()` | `ax.spines['top'].set_visible(False)` |

## 通用美化函数

```python
def despine(ax):
    """去除顶部和右侧边框"""
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

def apply_style(ax):
    """通用样式"""
    ax.grid(alpha=0.3, linestyle='--')
    despine(ax)
    # 图上不画 set_title()，标题由论文 \caption{} 承担
```

## 配色方案

```python
# 方案1: Viridis（默认推荐）
colors = plt.cm.viridis(np.linspace(0.1, 0.9, n))

# 方案2: RdBu_r（对比型）
colors = plt.cm.RdBu_r(np.linspace(0.15, 0.85, n))

# 方案3: tab10（离散类别）
colors = [f'C{i}' for i in range(n)]

# 方案4: Set3（柔和色）
colors = plt.cm.Set3(np.linspace(0, 1, n))
```

## 各类型图表模板

### 柱状图

```python
fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(len(categories))
bars = ax.bar(x, values, width=0.6, edgecolor='white',
              linewidth=0.5, color=plt.cm.viridis(np.linspace(0.1, 0.9, len(categories))))
ax.set_xticks(x)
ax.set_xticklabels(categories, rotation=30, ha='right')
ax.set_ylabel('数值')
# 柱顶标注数值
for bar, val in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            f'{val:.2f}', ha='center', va='bottom', fontsize=9)
apply_style(ax)
```

### 折线图

```python
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(x, y, linewidth=2, marker='o', markersize=5,
        color='C0', markerfacecolor='white', markeredgewidth=1.5)
ax.set_xlabel('X轴标签')
ax.set_ylabel('Y轴标签')
apply_style(ax)
```

### 多系列折线图

```python
fig, ax = plt.subplots(figsize=(10, 6))
for i, (label, data) in enumerate(series.items()):
    ax.plot(x, data, linewidth=2, marker='o', markersize=4, label=label)
ax.set_xlabel('X轴标签')
ax.set_ylabel('Y轴标签')
ax.legend(loc='best', frameon=True, fancybox=True)
apply_style(ax)
```

### 热力图

```python
fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(data_matrix, cmap='RdBu_r', aspect='auto',
                vmin=np.min(data_matrix), vmax=np.max(data_matrix))
cbar = plt.colorbar(im, ax=ax, shrink=0.8)
cbar.set_label('数值')
ax.set_xticks(range(len(col_labels)))
ax.set_xticklabels(col_labels, rotation=45, ha='right')
ax.set_yticks(range(len(row_labels)))
ax.set_yticklabels(row_labels)
# 格子内显示数值
for i in range(data_matrix.shape[0]):
    for j in range(data_matrix.shape[1]):
        ax.text(j, i, f'{data_matrix[i,j]:.2f}', ha='center', va='center', fontsize=8)
```

### 散点图

```python
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(x, y, alpha=0.7, edgecolors='black', linewidth=0.5,
           c=color_values, cmap='viridis', s=50)
ax.set_xlabel('X轴标签')
ax.set_ylabel('Y轴标签')
apply_style(ax)
```

### 回归散点图（带拟合线）

```python
from scipy import stats
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(x, y, alpha=0.7, edgecolors='black', linewidth=0.5, s=50, label='数据点')
slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
x_fit = np.linspace(x.min(), x.max(), 100)
ax.plot(x_fit, slope * x_fit + intercept, 'r--', linewidth=2,
        label=f'拟合线 (R²={r_value**2:.4f})')
ax.set_xlabel('X轴标签')
ax.set_ylabel('Y轴标签')
ax.legend(loc='best')
apply_style(ax)
```

### 饼图

```python
fig, ax = plt.subplots(figsize=(8, 8))
wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%',
    colors=plt.cm.Set3(np.linspace(0, 1, len(labels))),
    startangle=90, pctdistance=0.85,
    wedgeprops=dict(width=0.5, edgecolor='white'))
for autotext in autotexts:
    autotext.set_fontsize(10)
```

### 箱线图

```python
fig, ax = plt.subplots(figsize=(10, 6))
bp = ax.boxplot(data_list, labels=labels, patch_artist=True,
                showfliers=True, showmeans=True,
                meanprops=dict(marker='D', markerfacecolor='red', markersize=6))
for patch, color in zip(bp['boxes'], plt.cm.viridis(np.linspace(0.1, 0.9, len(data_list)))):
    patch.set_facecolor(color)
ax.set_ylabel('数值')
apply_style(ax)
```

### 多子图布局

```python
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()

# 子图1
ax = axes[0]
# ... 画图 ...
apply_style(ax)

# 子图2
ax = axes[1]
# ...

plt.tight_layout(pad=2)
```

### 双Y轴图

```python
fig, ax1 = plt.subplots(figsize=(10, 6))
ax2 = ax1.twinx()

ax1.plot(x, y1, 'b-', linewidth=2, marker='o', markersize=4, label='系列1')
ax2.plot(x, y2, 'r--', linewidth=2, marker='s', markersize=4, label='系列2')

ax1.set_xlabel('X轴标签')
ax1.set_ylabel('Y1轴 (蓝色)')
ax2.set_ylabel('Y2轴 (红色)')

# 合并图例
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='best')

despine(ax1)
ax2.spines['top'].set_visible(False)
```

## 保存图片

```python
def save_fig(fig, name_cn, fig_dir='图片'):
    fig.savefig(os.path.join(fig_dir, name_cn))
    plt.close(fig)

# 使用
save_fig(fig, '问题X_特征分布对比.png')
```

## 图表命名规范

图片文件名中文，格式：`问题X_内容_类型.png`

| 示例 | 说明 |
|------|------|
| `问题一_特征分布对比.png` | 柱状图 |
| `问题一_销售额趋势变化.png` | 折线图 |
| `问题二_相关性热力图.png` | 热力图 |
| `问题二_回归分析散点图.png` | 散点图 |
| `问题三_类别占比分布.png` | 饼图 |
| `问题三_模型性能对比.png` | 分组柱状图 |
| `问题四_灵敏度分析曲线.png` | 折线图 |

## 常见问题

| 问题 | 解决方法 |
|------|----------|
| 中文显示方框 | 在字体列表前添加 `'STHeiti'`，或安装思源字体 |
| 图例中文乱码 | 检查 `font.sans-serif` 配置 |
| 保存图片空白 | 确保 `save_fig` 在 `plt.show()` 前 |
| 图片分辨率低 | 确认 `dpi=150` |
| 坐标轴标签重叠 | `rotation=30, ha='right'` |
| 负号显示问题 | `axes.unicode_minus = False` |

## 输出

每张图保存为150dpi PNG文件，无 `set_title()`，坐标轴和图例全中文。