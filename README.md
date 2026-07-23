# 🚀 MathModel Toolkit

> 数学建模竞赛全自动求解器 —— **上传题目，一键生成论文**

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## ⚡ 5 分钟上手（无需懂代码）

### 1. 下载

> **直接下载 ZIP**：[点我下载](https://github.com/hongdotien10-hash/mathmodel-toolkit/archive/refs/heads/main.zip)

解压到任意文件夹。

### 2. 安装

双击 `install.bat`（Windows），等待自动安装完成。

> Mac/Linux：终端运行 `bash install.sh`

### 3. 放入题目

把赛题和数据放到 `problems/` 文件夹：

```
problems/
└── 我的赛题/
    ├── 题目.pdf          # PDF / DOCX / TXT
    ├── 附件1.xlsx
    └── 附件2.csv
```

### 3. 配置 AI（可选，推荐）

**双击 `setup_api.bat`**，粘贴你的 API Key。

> 推荐用 DeepSeek：[platform.deepseek.com](https://platform.deepseek.com) 注册即送额度。
> 不配 API 也能用，但 AI 增强后论文质量显著提升。费用：Free版 ¥0.5-1，Pro版 ¥3-5。

### 4. 一键运行

**双击 `run.bat`**，自动开始。
首次运行会自动提示配 API。

> 或者手动运行：
> ```bash
> python start.py
> ```

论文和图表自动生成到 `output/我的赛题/`。~10-20分钟，API费用 ¥3-5。

---
### 用什么软件打开？

| 方式 | 难度 | 说明 |
|------|------|------|
| **双击 `run.bat`** | ⭐ 最简单 | 自动找Python，选择版本，一键运行 |
| **终端运行** | ⭐⭐ | `Win+R` → `cmd` → `python start.py` |
| **VS Code** | ⭐⭐⭐ | 装 Python 插件后按 `F5` 运行 |
| **PyCharm** | ⭐⭐⭐ | 专业 Python IDE，右键 `Run` |

---

## 🎯 核心功能

| 功能 | 说明 |
|------|------|
| **多模型竞赛** | 每问2-3种方法对比（TOPSIS/AHP/灰色关联/GM/ARIMA/IP），AI选最优 |
| **深度灵敏度** | Tornado图 + Sobol指数 + 蒙特卡洛置信区间 |
| **误差诊断** | 残差图 + QQ图 + 预测区间 + DW检验 + 排名稳定性 |
| **专业图表** | 2×2/1×3多面板图表组，300dpi高清输出 |
| **AI写作** | 拿到真实数值写分析（现象→原因→建议），非模板填充 |
| **论文页数** | 20-25页 Word + LaTeX 双格式 |
| **预估耗时** | ~10-20 分钟 |
| **API费用** | ¥3-5（约20-25次DeepSeek调用） |
| **费用** | 永远免费开源 |

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
qq:1164217385
有不成熟的地方欢迎大家提建议
使用说明： https://v.douyin.com/ke9D1HscMD0/ 

## 📄 许可证

MIT License
