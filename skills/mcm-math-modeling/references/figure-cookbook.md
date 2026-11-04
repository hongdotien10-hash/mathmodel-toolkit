# 美赛论文图型总目录（49 种，Nature 风格）

> 本文件是 `scripts/nature_plot.py` 的配套索引。**先按"要证明什么"选图，再查表找函数，最后照抄代码片段。**
> 规范（配色/字号/尺寸/caption）见 `nature-figures.md`；"该不该用某图型"的决策见 `chart-selection.md`。

## 用法三步

```python
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from nature_plot import *          # 或按需 import
apply_nature_style()               # 每次绘图前调用一次
fig, ax = new_figure("onehalf")    # single(89mm)/onehalf(140mm)/double(183mm)
bar_chart(ax, cats, vals, ylabel="Medals")
save_figure(fig, "fig3_medals")    # 输出 同名.pdf + 同名.png(300dpi)
```

工具函数：`new_figure(size, nrows, ncols)`、`save_figure(fig, name)`、`panel_label(ax, "(a)")`、
`despine(ax)`、`plot_with_band(ax, x, mean, std, color)`、`add_significance_bracket(ax, x1, x2, y, pval)`。

---

## 速查总表（49 图型）

| # | 图型 | 函数 | 一句话用途 | 对应代码节 |
|---|---|---|---|---|
| 1 | 柱状图 | `bar_chart` | 类别数值对比 | 1 |
| 2 | 分组柱状 | `grouped_bar` | 多方案×多类别 | 1 |
| 3 | 堆叠柱状 | `stacked_bar` | 构成随类别变化 | 1 |
| 4 | 箱线+散点 | `box_strip_plot` | n<10 的组间分布对比 | 2 |
| 5 | 小提琴 | `violin_plot` | 分布形态对比 | 2 |
| 6 | 配对云雨 | `paired_raincloud` | 配对前后对比 | 2 |
| 7 | 直方+KDE | `hist_kde` | 单变量分布 | 3 |
| 8 | 山脊图 | `density_ridge` | 多组分布叠加 | 3 |
| 9 | 散点+回归 | `scatter_with_fit` | 两变量关系+R² | 4 |
| 10 | 相关热图 | `correlation_heatmap` | 多变量相关矩阵 | 5 |
| 11 | 混淆矩阵 | `confusion_matrix` | 分类结果 | 5 |
| 12 | 雷达图 | `radar_chart` | 多指标评价 | 6 |
| 13 | 堆叠面积 | `stacked_area` | 构成随时间 | 7 |
| 14 | 桑基风格流 | `sankey_style_flow` | 状态转移/流量分配 | 7 |
| 15 | 相图 | `phase_portrait` | 动力系统轨迹/零斜线 | 8 |
| 16 | 向量场 | `quiver_field` | 方向场 | 8 |
| 17 | 等高线响应面 | `contour_surface` | 双参数影响输出 | 9 |
| 18 | 3D 曲面 | `surface_3d` | 响应面（慎用） | 9 |
| 19 | 时间线/甘特 | `timeline` | 调度/资源分配 | 10 |
| 20 | 龙卷风图 | `tornado_plot` | 单参数敏感性排序 | 11 |
| 21 | 棒棒糖 | `lollipop_chart` | 排名/单序列（比柱轻） | 12 |
| 22 | 正负发散柱 | `diverging_bar` | 增减量对比 | 12 |
| 23 | 点图 | `dot_plot` | 多对象指标排序 | 12 |
| 24 | 环形图 | `donut_chart` | 占比（≤5 类，慎用） | 13 |
| 25 | 华夫图 | `waffle_chart` | 占比（方格计数，更易读） | 13 |
| 26 | 百分比堆叠 | `stacked_bar_100` | 份额结构变化 | 13 |
| 27 | 瀑布图 | `waterfall_chart` | 增减分解/贡献度 | 13 |
| 28 | ECDF | `ecdf_plot` | 多分布累积对比 | 14 |
| 29 | QQ 图 | `qq_plot` | 正态性检验 | 14 |
| 30 | 残差图 | `residual_plot` | 回归诊断 | 14 |
| 31 | ROC 曲线 | `roc_curve` | 二分类性能+AUC | 15 |
| 32 | PR 曲线 | `pr_curve` | 不平衡数据性能+AP | 15 |
| 33 | 收敛曲线 | `learning_curve` | 训练/验证损失 | 16 |
| 34 | 特征重要性 | `feature_importance` | 变量贡献排序 | 16 |
| 35 | 森林图 | `forest_plot` | 效应量+置信区间 | 16 |
| 36 | 扇形预测 | `fan_chart` | 预测+多档区间 | 17 |
| 37 | 预测vs实际 | `pred_vs_actual` | 模型验证（+1:1线） | 17 |
| 38 | 气泡图 | `bubble_chart` | 大小+颜色三通道 | 18 |
| 39 | 2D 密度 | `density_2d` | 大样本重叠 | 18 |
| 40 | 散点矩阵 | `pairplot` | 全变量两两关系 | 18 |
| 41 | 网络图 | `network_graph` | 节点-边关系 | 18 |
| 42 | 平行坐标 | `parallel_coordinates` | 多变量概览 | 18 |
| 43 | 标注热图 | `heatmap_annotated` | 通用矩阵+数值 | 19 |
| 44 | 聚类热图 | `clustermap` | 行列重排热图 | 19 |
| 45 | 树状图 | `dendrogram_plot` | 层次聚类（需 scipy） | 19 |
| 46 | 斜率图 | `slope_chart` | 两时点变化连线 | 20 |
| 47 | 哑铃图 | `dumbbell_plot` | 两方案成对对比 | 20 |
| 48 | 小倍数 | `small_multiples` | 分面网格 | 20 |
| 49 | 极坐标柱 | `polar_bar` | 环形排布（≤8 类） | 20 |

---

## 按美赛题型选图（速配）

| 题型 | 高频分析目标 | 首选图型（函数） |
|---|---|---|
| **A 连续/物理** | 模型拟合、轨迹、稳定性、参数敏感性 | 9 `scatter_with_fit`、15 `phase_portrait`、36 `fan_chart`、17 `contour_surface`、35 `forest_plot` |
| **B 离散/优化** | 方案对比、资源分配、收敛 | 2 `grouped_bar`、19 `timeline`、33 `learning_curve`、35 `forest_plot`、27 `waterfall_chart` |
| **C 数据/统计** | 预测、相关、分类、首现、分解 | 37 `pred_vs_actual`、10 `correlation_heatmap`、31 `roc_curve`、28 `ecdf_plot`、40 `pairplot`、38 `bubble_chart` |
| **D 运筹/网络** | 网络结构、路径、流量 | 41 `network_graph`、14 `sankey_style_flow`、19 `timeline` |
| **E 环境/可持续** | 时空演化、构成、情景 | 13 `stacked_area`、26 `stacked_bar_100`、36 `fan_chart`、48 `small_multiples` |
| **F 政策/评价** | 多指标权重、排序、敏感性 | 12 `radar_chart`、23 `dot_plot`、34 `feature_importance`、20 `tornado_plot`、25 `waffle_chart` |

---

## 关键图型的用法与 caption 模板

### 模型验证三件套（C/预测类必用）
```python
# (1) 预测 vs 实际
fig, ax = new_figure("single"); pred_vs_actual(ax, y_true, y_pred, xlabel="Actual", ylabel="Predicted")
# (2) 残差诊断
fig, ax = new_figure("single"); residual_plot(ax, y_pred, y_true - y_pred)
# (3) 预测区间扇形
fig, ax = new_figure("onehalf"); fan_chart(ax, years, [(lo90,hi90),(lo50,hi50)], xlabel="Year")
```
> **Figure 4 | Model validation.** (a) Predicted versus actual medal counts (dashed line: y = x).
> (b) Residuals show no systematic bias across the fitted range. (c) Forecasts with 50% and 90% prediction intervals.

### 敏感性/稳健性
```python
fig, ax = new_figure("single"); tornado_plot(ax, params, effects)               # 单参数排序
fig, ax = new_figure("onehalf"); contour_surface(ax, x, y, Z, kind="filled")    # 双参数
fig, ax = new_figure("single");  forest_plot(ax, names, est, lo, hi)            # 效应量+CI
```

### 多指标评价
```python
fig = plt.figure(figsize=(4.5, 4.5)); ax = fig.add_subplot(111, polar=True)
radar_chart(ax, criteria, [row1, row2], labels=["Plan A", "Plan B"])
# 或排序
fig, ax = new_figure("single"); dot_plot(ax, schemes, scores, xlabel="Composite score")
```

### 分类性能
```python
fig, ax = new_figure("single"); roc_curve(ax, y_true, scores)
fig, ax = new_figure("single"); pr_curve(ax, y_true, scores)    # 类别不平衡时补上
```

### 构成/份额
```python
stacked_bar_100(ax, groups, series, values)   # 份额变化
waffle_chart(ax, values, labels)              # 单时点占比（替代饼图）
waterfall_chart(ax, labels, deltas)           # 增减分解
```

---

## 组合多面板（论文主图）

```python
fig, axes = new_figure("double", nrows=1, ncols=3)
panels = [lambda ax: scatter_with_fit(ax, x, y),
          lambda ax: hist_kde(ax, res),
          lambda ax: bar_chart(ax, cats, vals)]
for ax, fn, lab in zip(axes, panels, "(a)(b)(c)"):
    fn(ax); panel_label(ax, lab)
save_figure(fig, "fig1_main")
```

- 面板数 2–6 个；同一主图共用配色与轴尺度，便于横向比较
- 面板标签统一 `(a)(b)(c)`，10–12pt 加粗，放左上角
- 超过 6 个面板改用 `small_multiples` 或拆图

---

## 避坑清单（与 chart-selection.md 一致）

- 类别占比优先 `waffle_chart`/`stacked_bar`，**不要**用 `donut_chart`（除非 ≤4 类）
- 3D 图（`surface_3d`）仅在没有更好 2D 表达时用；优先 `contour_surface(kind="filled")`
- 均值柱必须有原始点 → 用 `box_strip_plot` 或 `dot_plot`
- 热图必带 `colorbar` + 标签（函数已内置）
- 匹配图：`correlation_heatmap`（-1~1，`RdBu_r`）；计数：`heatmap_annotated`（`viridis`/`YlGnBu`）
- 每张图只讲一个论点；>5 条线或量级差 >10 倍 → 拆图

## scipy 依赖说明

除 `clustermap`、`dendrogram_plot`（层次聚类）与 `hist_kde`/`paired_raincloud` 的 KDE 平滑需要 scipy 外，
其余图型仅依赖 numpy + matplotlib。缺 scipy 时会自动降级（如 `clustermap` 改为按均值排序），不会报错。
