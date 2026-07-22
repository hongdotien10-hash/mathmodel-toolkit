# 🚀 MathModel Toolkit

> 数学建模竞赛全自动求解器 —— **上传题目，一键生成论文**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MATLAB](https://img.shields.io/badge/MATLAB-R2020a+-orange.svg)](matlab/)

---

## ✨ 核心亮点

- 🧠 **智能模型选择** — 根据题目特征自动推荐最优模型（40+ 算法库）
- ⚡ **一键生成论文** — PDF题目 + Excel数据 → 完整论文 PDF
- 📊 **实时进度追踪** — Rich 终端面板 + JSON 双通道进度展示
- 🎨 **论文级可视化** — matplotlib 图表直接用于竞赛论文
- 🔧 **模块可插拔** — 每个环节可单独使用或替换
- 🌐 **双语言** — Python + MATLAB 工具箱

---

## 📦 快速开始

### 安装

```bash
# 基础安装
pip install mathmodel-toolkit

# 全功能安装（含 PDF 解析、优化、Web UI）
pip install mathmodel-toolkit[all]
```

### 一键运行

```bash
# CLI 命令行
mathmodel run --problem 2024国赛A题.pdf --data 附件1.xlsx 附件2.csv

# Python API
from mathmodel import Pipeline

pipe = Pipeline()
pipe.run(problem="赛题.pdf", data=["附件.xlsx"])
paper = pipe.get_paper()
print(f"论文已生成: {paper}")
```

### 仅分析和推荐模型

```bash
mathmodel analyze --problem 赛题.pdf --data 附件.xlsx
```

### 启动 Web 界面

```bash
mathmodel web --port 8501
```

---

## 🏗️ 流水线架构

```
📄 赛题PDF → 🔍 解析 → 🧠 分析+推荐 → ⚙️ 求解 → 📊 图表 → 📝 论文 → 📕 PDF
                  │         │            │         │          │
                  │    ┌────▼────┐       │    ┌────▼────┐     │
                  │    │题型分类器│       │    │论文级图表│     │
                  │    │知识库   │       │    │流程图生成│     │
                  │    │推荐引擎 │       │    │灵敏度分析│     │
                  │    └─────────┘       │    └─────────┘     │
                  │                     │                    │
             进度面板 ◄─────────────────┴────────────────────┘
             (Rich UI + progress.json)
```

---

## 📂 项目结构

```
mathmodel-toolkit/
├── mathmodel/                  # Python 核心库
│   ├── pipeline/               # 流水线引擎（调度、进度、配置）
│   ├── parser/                 # 文档解析 (PDF/DOCX)
│   ├── analyzer/               # 题目分析 & 模型推荐
│   ├── preprocessing/          # 数据预处理
│   ├── models/                 # 模型库 (6大类 40+ 算法)
│   │   ├── optimization.py     # 优化模型
│   │   ├── differential.py     # 微分方程
│   │   ├── statistics.py       # 统计模型
│   │   ├── ml.py               # 机器学习
│   │   ├── graph.py            # 图论/网络
│   │   └── evaluation.py       # 评价模型
│   ├── solver/                 # 自动求解引擎
│   ├── sensitivity/            # 灵敏度分析
│   ├── visualization/          # 论文级可视化
│   ├── paper/                  # 论文自动生成
│   ├── io/                     # 数据读写
│   └── utils/                  # 通用工具
├── matlab/                     # MATLAB 工具箱
├── templates/                  # 论文模板 (LaTeX + Typst)
├── webui/                      # Web 界面
├── examples/                   # 赛题示例
├── tests/                      # 测试
└── docs/                       # 文档
```

---

## 🧠 支持的模型

| 类别 | 算法 | 典型应用场景 |
|------|------|-------------|
| **优化** | 线性规划、整数规划、非线性规划、多目标优化、动态规划 | 资源分配、生产调度 |
| **预测** | 灰色预测 GM(1,1)、ARIMA、回归、XGBoost、指数平滑 | 趋势预测、时序预测 |
| **评价** | TOPSIS、AHP、熵权法、模糊综合评价、灰色关联、CRITIC、VIKOR | 方案评选、指标体系 |
| **分类** | K-means、DBSCAN、层次聚类、SVM、随机森林、PCA、t-SNE | 模式识别、降维聚类 |
| **微分方程** | ODE求解器、SIR模型、Logistic模型、PDE求解 | 动力学、传染病 |
| **图论** | Dijkstra、Floyd、最大流、最小生成树、TSP、A* | 路径规划、网络分析 |
| **统计** | t检验、卡方检验、ANOVA、相关分析、K-S检验 | 假设检验、回归诊断 |

---

## 📊 自动模型选择逻辑

```
题目文本 → 关键词提取 → 题型分类 ─→ 知识库检索 → 多维打分 → Top-K推荐
                            │         │              │
                            │    ┌────▼────────────────▼─────┐
                            │    │  数据匹配度 (样本量/类型)  │
                            │    │  约束满足度 (线性/非线性)  │
                            │    │  可解释性 (竞赛要求)      │
                            │    │  历史使用率 (竞赛频率)    │
                            │    └──────────────────────────┘
                            │                │
                            └────────────────┘
```

---

## 🎯 模块 API 速览

```python
from mathmodel import Pipeline, PipelineConfig
from mathmodel.preprocessing import MissingHandler, OutlierDetector, Normalizer
from mathmodel.models import OptimizationSolver, EvaluationSolver, StatsSolver
from mathmodel.visualization import Plotter, set_style
from mathmodel.io import read_data, to_latex_table
from mathmodel.analyzer import ModelKnowledgeBase

# 单独使用各模块
evaluator = EvaluationSolver()
result = evaluator.topsis(matrix, weights)
print(f"得分: {result['scores']}")

# 灰色预测
solver = StatsSolver()
pred = solver.grey_forecast([10, 15, 20, 26, 33], forecast_steps=3)
print(f"预测: {pred['forecast']}")

# 绘制论文图表
plotter = Plotter(language="zh")
fig, ax = plotter.line(x, y, xlabel="时间/天", ylabel="值", title="趋势分析")
plotter.save(fig, "trend.pdf")
```

---

## 🖥️ Web UI

```
mathmodel web --port 8501
```

打开浏览器 `http://localhost:8501`：
1. 📤 拖拽上传题目 PDF 和数据文件
2. 👀 实时查看分析进度和模型推荐
3. 📥 一键下载论文 PDF 和完整求解代码

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

```bash
git clone https://github.com/username/mathmodel-toolkit.git
cd mathmodel-toolkit
pip install -e ".[dev]"
pytest tests/
```

---

## 📄 许可证

MIT License — 详见 [LICENSE](LICENSE)

---

## 🙏 致谢

- 姜启源《数学模型》
- 司守奎《数学建模算法与应用》
- 全国大学生数学建模竞赛 (CUMCM)
- MCM/ICM 美国大学生数学建模竞赛
