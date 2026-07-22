---
name: 数据预处理
description: 数学建模数据预处理，包含缺失值处理、异常值检测、标准化/归一化、特征工程
trigger:
  - "数据预处理"
  - "预处理数据"
  - "数据清洗"
  - "清洗数据"
---

# 数据预处理

## 目的

对原始数据进行系统化预处理，为建模提供清洁规整的输入数据。

## 预处理流程

### Step 1: 数据读取与理解

```python
import pandas as pd
import numpy as np
import chardet

# 自动检测编码（对CSV文件）
with open('文件.csv', 'rb') as f:
    result = chardet.detect(f.read())
    print(f"检测编码: {result['encoding']}")

# 读取数据
df = pd.read_excel('数据/data.xlsx', sheet_name='Sheet1')

# 基础信息
print(f"数据规模: {df.shape}")
print(f"列名: {list(df.columns)}")
print(f"数据类型:\n{df.dtypes}")
print(f"缺失值:\n{df.isnull().sum()}")
print(f"描述统计:\n{df.describe()}")
```

### Step 2: 数据清洗

#### 2.1 缺失值处理

```python
# 统计缺失情况
missing_ratio = df.isnull().sum() / len(df)
print("缺失比例:\n", missing_ratio)

# 策略选择
for col in df.columns:
    ratio = df[col].isnull().sum() / len(df)
    if ratio == 0:
        continue
    elif ratio < 0.05:  # <5%: 直接删除缺失行
        df = df.dropna(subset=[col])
        print(f"  [{col}] 缺失{ratio:.1%}，删除缺失行")
    elif ratio < 0.20:  # 5%-20%: 插补
        if df[col].dtype in ['float64', 'int64']:
            df[col] = df[col].fillna(df[col].median())  # 数值列用中位数
        else:
            df[col] = df[col].fillna(df[col].mode()[0])  # 分类列用众数
        print(f"  [{col}] 缺失{ratio:.1%}，已插补")
    else:  # >20%: 考虑删除该列
        print(f"  ⚠ [{col}] 缺失{ratio:.1%}，比例过高，建议删除或特殊处理")
```

#### 2.2 异常值检测

```python
def detect_outliers(df, method='iqr'):
    """检测异常值"""
    outliers = {}
    for col in df.select_dtypes(include=[np.number]).columns:
        if method == 'iqr':
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            mask = (df[col] < lower) | (df[col] > upper)
        elif method == 'zscore':
            from scipy import stats
            z = np.abs(stats.zscore(df[col].dropna()))
            mask = pd.Series(z > 3, index=df[col].dropna().index)

        if mask.sum() > 0:
            outliers[col] = {
                'count': mask.sum(),
                'ratio': mask.sum() / len(df),
                'indices': df[mask].index.tolist()
            }
    return outliers

outliers = detect_outliers(df, method='iqr')
for col, info in outliers.items():
    print(f"  [{col}] 异常值 {info['count']} 个 ({info['ratio']:.1%})")

# 处理异常值：使用中位数替换
for col in outliers:
    median = df[col].median()
    df.loc[df.index.isin(outliers[col]['indices']), col] = median
```

#### 2.3 重复值处理

```python
duplicates = df.duplicated().sum()
print(f"重复行: {duplicates}")
if duplicates > 0:
    df = df.drop_duplicates()
```

### Step 3: 标准化/归一化

#### Min-Max 归一化

\begin{equation}
x' = \frac{x - x_{min}}{x_{max} - x_{min}}
\end{equation}

```python
from sklearn.preprocessing import MinMaxScaler

scaler = MinMaxScaler()
numeric_cols = df.select_dtypes(include=[np.number]).columns
df[numeric_cols] = scaler.fit_transform(df[numeric_cols])

# 保存scaler用于逆变换
import joblib
joblib.dump(scaler, '结果/minmax_scaler.pkl')
```

#### Z-Score 标准化

\begin{equation}
x' = \frac{x - \mu}{\sigma}
\end{equation}

```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
numeric_cols = df.select_dtypes(include=[np.number]).columns
df[numeric_cols] = scaler.fit_transform(df[numeric_cols])

# 输出每列的μ和σ供论文引用
for i, col in enumerate(numeric_cols):
    print(f"  {col}: μ={scaler.mean_[i]:.4f}, σ={scaler.scale_[i]:.4f}")
```

### Step 4: 特征工程

#### 相关性分析

```python
# 计算相关性矩阵
corr_matrix = df[numeric_cols].corr()

# 高相关性特征对（相关系数>0.9）
high_corr = []
for i in range(len(corr_matrix.columns)):
    for j in range(i+1, len(corr_matrix.columns)):
        if abs(corr_matrix.iloc[i, j]) > 0.9:
            high_corr.append({
                'feature1': corr_matrix.columns[i],
                'feature2': corr_matrix.columns[j],
                'correlation': corr_matrix.iloc[i, j]
            })
# 保留相关性最高的一对中的一个
```

#### 特征选择

```python
from sklearn.feature_selection import SelectKBest, f_regression

# 基于F统计量的特征选择
selector = SelectKBest(score_func=f_regression, k=min(10, len(numeric_cols)))
X_selected = selector.fit_transform(df[numeric_cols], target)
selected_cols = [numeric_cols[i] for i in selector.get_support(indices=True)]
print(f"选中的特征: {selected_cols}")
```

### Step 5: 预处理结果输出

```python
def print_preprocessing_report(df_before, df_after, numeric_cols):
    """输出预处理前后对比"""
    print("\n" + "="*60)
    print("预处理结果报告")
    print("="*60)

    print(f"\n数据规模: {df_before.shape} → {df_after.shape}")

    print(f"\n{'列名':<15} {'处理前均值':>10} {'处理后均值':>10} "
          f"{'处理前std':>10} {'处理后std':>10} {'缺失处理':>8}")
    print("-"*65)

    for col in numeric_cols:
        before_mean = df_before[col].mean()
        after_mean = df_after[col].mean()
        before_std = df_before[col].std()
        after_std = df_after[col].std()
        missing = df_before[col].isnull().sum()
        print(f"{col:<15} {before_mean:>10.4f} {after_mean:>10.4f} "
              f"{before_std:>10.4f} {after_std:>10.4f} {missing:>8}")

# 保存预处理后的数据
df_clean.to_csv('求解/预处理数据.csv', index=False, encoding='utf-8-sig')
```

### Step 6: 保存处理日志

```python
log = {
    '原始规模': df_before.shape,
    '处理后规模': df_after.shape,
    '删除缺失行数': dropped_rows,
    '删除列数': dropped_cols,
    '异常值处理数': sum(o['count'] for o in outliers.values()),
    '标准化方法': 'Min-Max' if use_minmax else 'Z-Score',
    '保留特征数': len(selected_cols) if feature_selection_done else len(numeric_cols),
}
```

## 输出

1. `求解/预处理数据.csv` — 清洗后的数据（问题1必须输出）
2. 预处理结果报告（供论文引用）
3. `scaler.pkl`（如有标准化）
4. 预处理前后统计量对比表