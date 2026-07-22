# MathModel Toolkit — MATLAB 工具箱

数学建模竞赛 MATLAB 工具箱，与 Python 库功能对齐。

## 目录

```
matlab/
├── preprocessing/     # 数据预处理
│   ├── missing.m      # 缺失值处理
│   ├── outlier.m      # 异常值检测
│   └── normalize.m    # 数据标准化
├── models/            # 模型库
│   ├── optimization/  # 优化模型
│   │   ├── linear_programming.m
│   │   ├── nonlinear_programming.m
│   │   └── integer_programming.m
│   ├── statistics/    # 统计模型
│   │   ├── grey_forecast.m       # 灰色预测 GM(1,1)
│   │   ├── linear_regression.m   # 线性回归
│   │   └── t_test.m              # t检验
│   ├── evaluation/    # 评价模型
│   │   ├── topsis.m              # TOPSIS
│   │   ├── ahp.m                 # AHP
│   │   ├── entropy_weight.m      # 熵权法
│   │   └── fuzzy_comprehensive.m # 模糊综合评价
│   ├── ml/            # 机器学习
│   │   ├── kmeans.m
│   │   └── pca.m
│   ├── graph/         # 图论
│   │   ├── dijkstra.m
│   │   └── max_flow.m
│   └── differential/  # 微分方程
│       ├── ode_solver.m
│       └── sir_model.m
├── visualization/     # 可视化
│   ├── set_style.m    # 论文风格设置
│   ├── line_plot.m    # 折线图
│   ├── bar_plot.m     # 柱状图
│   └── scatter_plot.m # 散点图
└── io/                # 数据读写
    ├── read_data.m
    └── write_data.m
```

## 使用

将 `matlab/` 目录及其子目录添加到 MATLAB 路径：

```matlab
addpath(genpath('matlab/'));
```

## 示例

```matlab
% 灰色预测
data = [10, 15, 20, 26, 33];
result = grey_forecast(data, 3);
disp(result.forecast);

% TOPSIS 评价
matrix = [1 2; 3 4; 5 6];
weights = [0.5, 0.5];
scores = topsis(matrix, weights);
disp(scores);
```

## 与 Python 库的对应关系

| Python | MATLAB |
|--------|--------|
| `StatsSolver.grey_forecast()` | `grey_forecast.m` |
| `EvaluationSolver.topsis()` | `topsis.m` |
| `EvaluationSolver.ahp()` | `ahp.m` |
| `OptimizationSolver.linear_program()` | `linear_programming.m` |
| `GraphSolver.dijkstra()` | `dijkstra.m` |
