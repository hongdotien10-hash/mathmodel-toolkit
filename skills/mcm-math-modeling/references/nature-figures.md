# Nature 风格作图规范（美赛获奖级插图指南）

美赛评委每天看上百篇论文，**图的专业度是最直观的信号**。目标：让每一张图看起来像从 Nature/Science 论文里截出来的。

## 0. 每张图必须先回答的问题

在动笔/写代码前，先写出这张图要证明的**一句话结论**。图是为论点服务的，不是为数据服务的。

| 问题 | 示例回答 |
|---|---|
| 这张图要证明什么？ | 模型预测误差随训练数据量增大而下降并趋于稳定。 |
| 读者第一眼应该看到什么？ | 红色曲线（我们的模型）始终低于蓝色曲线（基准）。 |
| 如果删掉这张图，正文是否还能说清楚？ | 不能。 |

## 1. 配色方案

### NPG（Nature Publishing Group）主配色 —— 首选
```
红色    #E64B35    蓝色    #4DBBD5
绿色    #00A087    橙色    #F39B7F
深蓝    #3C5488    棕色    #8491B4
紫色    #91D1C2    暗红    #B09C85
```
- 两组对比：蓝 #4DBBD5 + 红 #E64B35
- 三组：红/蓝/绿；四组：加橙
- 模型 vs 数据：模型用实线深色，数据用散点

### Okabe-Ito 色盲友好配色（审稿安全）
```
橙色 #E69F00   天蓝 #56B4E9   蓝绿 #009E73
黄色 #F0E442   蓝色 #0072B2   朱红 #D55E00   紫红 #CC79A7
```

### 连续色图
- 顺序数据：`viridis`（Nature 默认）或 `cividis`
- 发散数据（正负对比）：`RdBu_r` 或 `coolwarm`，中心值取 0
- **禁用 `jet`/彩虹色图**

### 配色纪律
- 单张图 ≤ 5 种颜色
- 同一变量全文颜色一致
- 避免纯黑 #000000，用近黑 #1A1A1A；避免纯白背景上的浅色（< #CCCCCC）

## 2. 字体与字号

- 字体：**Arial**（Nature 官方指定）或 Helvetica
- 字号：
  - 坐标轴标签：7-9 pt
  - 刻度标签：7-8 pt
  - 图例：7-8 pt
  - 面板标签 (a)(b)(c)：10-12 pt 加粗
- 单位放括号里："Time (day)", "Temperature (°C)", "Population (×10³)"

## 3. 图幅尺寸

| 用途 | 宽 × 高 (mm) | 宽 × 高 (inch) |
|---|---|---|
| 单栏图 | 89 × 62 | 3.5 × 2.4 |
| 1.5 栏 | 140 × 92 | 5.5 × 3.6 |
| 双栏/全宽 | 183 × 120 | 7.2 × 4.7 |

- 主结果图用 1.5 栏，多面板组合图用全宽
- 高宽比接近 0.618
- 导出：**PDF（矢量）+ PNG（300 dpi）**

## 4. 版式细节

- 只保留左、下脊柱，去掉上、右边框
- 刻度**朝外**，长度 3.5pt
- 脊柱与刻度线宽 0.8-1.0 pt；数据线宽 1.5-2 pt
- 图例**无边框**，尽量放图内空白处
- 不用网格线；必要时用极浅的横向虚线（alpha=0.3）
- 误差棒/置信区间用半透明填充带
- 子图间距紧凑但标签不重叠

## 5. 各类图制作要点

### 5.1 框架流程图
- 结构：Problem → Data → Model → Validation → Conclusion
- 每框 ≤ 6 词，字号 ≥ 8pt
- 同阶段同色系，关键模块用强调色
- 详见 `flowchart-framework.md`

### 5.2 折线图 / 时间序列
- 数据点 + 拟合线：散点 + 实线
- 多曲线：颜色区分为主，线型为辅
- 关键数值可用 `annotate` 直接标注
- 函数：`nature_plot.plot_with_band()` / 直接 `ax.plot()`

### 5.3 柱状图
- 分组/堆叠/横向排序，按值排序更直观
- 柱顶可标注数值
- 函数：`bar_chart`, `grouped_bar`, `stacked_bar`

### 5.4 箱线图 / 小提琴图
- n<10 时**必须显示每个点**（stripplot 叠加）
- n≥10 时小提琴+箱线
- 函数：`box_strip_plot`, `violin_plot`, `paired_raincloud`

### 5.5 散点 + 回归
- 必加拟合线、R²、p 值
- 函数：`scatter_with_fit`

### 5.6 热图 / 相关矩阵 / 混淆矩阵
- 连续数据用 viridis；正负对比用 RdBu_r
- 必须加 colorbar 和 label
- 函数：`correlation_heatmap`, `confusion_matrix`

### 5.7 敏感性分析图
- 单参数：多条曲线叠加 或 Tornado 图
- 双参数：热图
- 函数：`tornado_plot` + 热图示例
- 高级分析见 `sensitivity-advanced.md`

### 5.8 雷达图（多指标评价）
- 适合方案/模型多维度对比
- 类别数 4-8 个为宜
- 函数：`radar_chart`

### 5.9 堆叠面积图
- 适合展示组成随时间变化
- 颜色顺序从下到上要有逻辑
- 函数：`stacked_area`

### 5.10 相图 / 向量场
- 适合微分方程/动力系统
- 用 streamplot + 零斜线
- 函数：`phase_portrait`, `quiver_field`

### 5.11 响应面 / 等高线
- 适合展示两个参数共同影响输出
- 推荐 2D 等高线，慎用 3D
- 函数：`contour_surface`, `surface_3d`

### 5.12 时间线 / Gantt
- 适合调度/资源分配问题
- 任务块内文字清晰可读
- 函数：`timeline`

### 5.13 直方图 + KDE
- 适合展示分布
- 必加中位数虚线
- 函数：`hist_kde`

### 5.14 分布诊断（ECDF / QQ / 残差）
- ECDF 比较多个分布，比直方图更干净：`ecdf_plot`
- QQ 图检验正态性（残差是否落在 45° 线上）：`qq_plot`
- 残差图诊断系统偏差：`residual_plot`
- 山脊图叠加多组分布：`density_ridge`

### 5.15 排序与构成（棒棒糖 / 点图 / 发散柱 / 瀑布 / 华夫）
- 排名单序列：`lollipop_chart`；多对象指标：`dot_plot`
- 增减量：`diverging_bar`；贡献度分解：`waterfall_chart`
- 占比：优先 `waffle_chart` 或 `stacked_bar` 或 `stacked_bar_100`；`donut_chart` 仅 ≤4 类

### 5.16 分类性能
- ROC + AUC：`roc_curve`；类别不平衡时补 PR + AP：`pr_curve`；混淆矩阵：`confusion_matrix`

### 5.17 模型训练与验证
- 收敛曲线（训练/验证损失）：`learning_curve`
- 特征重要性排序：`feature_importance`
- 预测 vs 实际（+1:1 线）：`pred_vs_actual`；预测区间扇形：`fan_chart`
- 效应量 + 置信区间总览：`forest_plot`

### 5.18 高维与关系
- 三通道编码（大小+颜色）：`bubble_chart`；大样本重叠：`density_2d`
- 全变量两两关系：`pairplot`；多变量概览：`parallel_coordinates`
- 网络/关系：`network_graph`；状态转移：`sankey_style_flow`
- 矩阵重排：`clustermap`；层次聚类：`dendrogram_plot`（后两者需 scipy）

### 5.19 两时点对比
- 斜率图（连线表示变化）：`slope_chart`；成对哑铃：`dumbbell_plot`；配对云雨：`paired_raincloud`

> 全部 49 种图型的用途、函数与代码片段见 `figure-cookbook.md`。

## 6. Caption 写作模板

Nature 式 caption = 标题句 + 自解释描述。

```
Figure 3 | Sensitivity of total population to the growth rate r.
(a) Population trajectories for r varying from 0.8r₀ to 1.2r₀. The dashed
line denotes the baseline scenario. (b) Relative deviation of the final
population from baseline after 50 years. Shaded bands represent 95%
confidence intervals over 100 Monte Carlo runs.
```

- 第一行加粗式标题句，概括结论
- 说明每个面板、线型、颜色的含义
- 注明样本量、误差含义、参数取值

## 7. 反面清单

- ❌ Excel 默认蓝橙配色 + 灰色网格背景
- ❌ jet 彩虹热图
- ❌ 图例带粗黑边框、遮住数据
- ❌ 3D 柱状图/饼图
- ❌ 截图粘贴（模糊、带软件边框）
- ❌ 坐标轴无单位、刻度朝内、四边全框
- ❌ 图上标题（标题写进 caption）
- ❌ 位图拉伸失真

## 8. 工具链

- **matplotlib + `scripts/nature_plot.py`**（主用）
- 流程图：draw.io / Graphviz
- 地图：geopandas + cartopy
- 后处理：Inkscape/Illustrator 微调矢量图

## 9. 与 `chart-selection.md` / `figure-cookbook.md` 的协作

作图前先读 `references/chart-selection.md` 确定最合适的图型，再用 `references/figure-cookbook.md` 找到对应函数与代码片段。不要上来就选"默认柱状图"。
