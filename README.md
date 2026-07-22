# 🚀 MathModel Toolkit

> 数学建模竞赛全自动求解器 —— **上传题目，一键生成论文**

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## ⚡ 5 分钟上手

### 1. 下载

```bash
git clone https://github.com/hongdotien10-hash/mathmodel-toolkit.git
cd mathmodel-toolkit
pip install -e .
```

### 2. 放入题目

把赛题和数据放到 `problems/` 文件夹：

```
problems/
└── 我的赛题/
    ├── 题目.pdf          # PDF / DOCX / TXT
    ├── 附件1.xlsx
    └── 附件2.csv
```

### 3. 一键运行

```bash
python start.py
```

论文和图表自动生成到 `output/我的赛题/`。

---

## 🤖 AI 增强（可选）

接入大语言模型获得更智能的分析，默认使用 **DeepSeek V4 Pro**。

```bash
# 1. 配置 API Key
cp api/.env.example .env
# 编辑 .env，填入你的 DeepSeek Key

# 2. 使用 AI 分析
python -c "
from api import AIAnalyzer
analyzer = AIAnalyzer()
result = analyzer.analyze_problem('你的赛题文本...')
print(result)
"
```

| 提供商 | 获取 Key |
|--------|---------|
| DeepSeek（默认） | [platform.deepseek.com](https://platform.deepseek.com) |
| OpenAI | [platform.openai.com](https://platform.openai.com) |
| Anthropic | [console.anthropic.com](https://console.anthropic.com) |
| 智谱 / 通义千问 / Kimi | 各自官网 |

API 不可用时自动回退本地规则引擎。

---

## 🧩 模块功能

### 模型求解（40+ 算法）

```python
from mathmodel.models import EvaluationSolver, StatsSolver, OptimizationSolver

# TOPSIS 评价
result = EvaluationSolver().topsis(matrix, weights, impacts=[1, -1, 1])

# 灰色预测 GM(1,1)
pred = StatsSolver().grey_forecast([12, 15, 19, 24, 30, 38], forecast_steps=3)

# 0-1 整数规划
result = OptimizationSolver().integer_program(c=[-15, -22], A_ub=[[30, 45]], b_ub=[100], binary=True)
```

### 论文级图表

```python
from mathmodel.visualization import Plotter, set_style
set_style("zh")
plotter = Plotter()
fig, ax = plotter.bar(x=["A","B","C"], y=[0.64, 0.32, 0.53], title="TOPSIS得分")
plotter.save(fig, "figures/scores.pdf")
```

---

## 📖 支持的模型

| 类别 | 算法 |
|------|------|
| **优化** | 线性规划、整数规划、非线性规划、多目标优化、动态规划 |
| **预测** | GM(1,1)、ARIMA、回归、XGBoost、指数平滑 |
| **评价** | TOPSIS、AHP、熵权法、模糊综合评价、灰色关联、CRITIC |
| **分类** | K-means、DBSCAN、层次聚类、SVM、随机森林、PCA |
| **微分方程** | ODE 求解、SIR、Logistic、PDE |
| **图论** | Dijkstra、Floyd、最大流、TSP、A* |
| **统计** | t检验、卡方、ANOVA、相关分析 |

---

## 🗂️ 项目结构

```
├── start.py                   # ⚡ 一键启动
├── problems/                  # 📂 题目放这里
├── output/                    # 📁 论文自动输出
├── api/                       # 🤖 LLM 接口
│   ├── config.py              #   6大提供商预设
│   ├── client.py              #   统一调用
│   └── analyzer.py            #   AI 增强分析器
├── mathmodel/                 # 🧠 核心引擎
│   ├── analyzer/              #   题目分析+知识库
│   ├── models/                #   模型库
│   ├── visualization/         #   论文图表
│   └── paper/                 #   Word 论文生成
├── skills/                    # 📚 数模工作流(17个)
├── matlab/                    # MATLAB 工具箱
└── webui/                     # Web 界面
```

---

## 📄 许可证

MIT License
