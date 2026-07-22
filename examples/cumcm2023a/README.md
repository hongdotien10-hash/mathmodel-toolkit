# CUMCM 2023 A 题 — 定日镜场优化设计

本题为 2023 年高教社杯全国大学生数学建模竞赛 A 题。
详见: https://cumcm.cnki.net/

## 使用 MathModel Toolkit 求解

```python
from mathmodel import Pipeline

pipe = Pipeline()
pipe.run(
    problem="2023年国赛A题.pdf",
    data=["附件.xlsx"],
    output_dir="./output_cumcm2023a",
)
```

## 预期输出

```
output_cumcm2023a/
├── paper.pdf          # 完整论文
├── figures/           # 图表
├── codes/             # 求解代码
├── progress.json      # 进度记录
├── results.json       # 数值结果
├── recommendations.json  # 模型推荐
└── config.yaml        # 运行配置
```
