# 🚀 MathModel Toolkit

> **数学建模竞赛工具箱** —— 装进智能体，一句人话生成论文

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Skill](https://img.shields.io/badge/skill-mcm--math--modeling-purple)](skills/mcm-math-modeling/)

---

## 这是什么

一个**数学建模竞赛工具箱**，由两部分组成：

| | 是什么 | 扮演什么角色 |
|---|--------|------------|
| **技能包** `skills/mcm-math-modeling/` | 一套完整的工作流方法论 + **可执行门禁** | **主路径** —— 装进智能体，按竞赛标准跑完整流程 |
| **Python 引擎** `mathmodel/` | 40+ 求解算法、论文图表、Word/LaTeX 论文生成 | **底座** —— 提供算力，被智能体调用 |

**主次关系要说清楚：**

> **"一键生成论文"这件事，只有装进智能体才成立。**
>
> 技能包装好后，你说一句"这是赛题，帮我做一遍"，智能体自己读题、拆子问题、
> 选模型、跑求解、写论文、跑验收 —— 门禁不通过就停下来整改，不会交一份
> 看起来像模像样、实则经不起评委推敲的稿子。
>
> Python 引擎**单独跑不出好论文**。它是一堆求解器和绘图工具，负责"算得准、
> 画得对"，但"怎么组织成一篇合规的竞赛论文"由技能包定义。引擎的最佳用法
> 是**被智能体调用**。

---

## ⚡ 快速开始

### 装进智能体（出论文的主路径）

**Windows**

```bat
cd skills\mcm-math-modeling
install.bat
```

**macOS / Linux**

```bash
cd skills/mcm-math-modeling
chmod +x install.sh && ./install.sh
```

脚本自动探测本机已装的智能体并安装：

```
✓ 已安装到 C:\Users\<你>\.claude\skills\mcm-math-modeling
✓ 已安装到 C:\Users\<你>\.workbuddy\skills\mcm-math-modeling
```

| 智能体 | 用户级目录 | 项目级目录 |
|--------|-----------|-----------|
| **WorkBuddy** | `~/.workbuddy/skills/` | `<项目>/.workbuddy/skills/` |
| **WorkBuddy 国际版** | `~/.workbuddy-intl/skills/` | `<项目>/.workbuddy-intl/skills/` |
| **Claude Code** | `~/.claude/skills/` | `<项目>/.claude/skills/` |
| **Cursor** | `~/.cursor/skills/` | `<项目>/.cursor/skills/` |
| **Codex** | `~/.codex/skills/` | — |
| **Gemini CLI** | `~/.gemini/skills/` | — |
| **OpenCode** | `~/.config/opencode/skills/` | — |
| **Windsurf** | `~/.windsurf/skills/` | — |

> Windows 下 `~` 即 `C:\Users\<你的用户名>`。装到项目级目录时该目录跟着仓库走，适合团队共享。
> 只想装某一个：`./install.sh claude`；先看能装哪些：`./install.sh --list`。

**装完直接说人话**，不用记命令：

> 这是 2025 MCM C 题的题面和附件，帮我按竞赛流程做一遍

智能体会自动加载技能（`description` 里带了触发词：数模 / 建模 / MCM / CUMCM / 国赛 / 美赛 / 杯赛…），
先问你四件事：

1. **排版引擎** —— Typst 还是 LaTeX？
2. **竞赛类型** —— MCM/ICM、国赛、华为杯、华中杯、五一杯、Mathorcup？
3. **论文语言** —— 英文（MCM/ICM 按 COMAP 规定必须英文）还是中文？
4. **子问题数量** —— 已知还是从题面判断？

然后按 6 阶段推进，在三个决策门停下来等你拍板（模型选型、图表选型、叙述主线）。

### 引擎：装上，让智能体去调

引擎是底座，不是独立产品。装依赖：

```bash
# Python 3.10+
python -m pip install -e .
python -m pip install -e ".[pdf,optimization,timeseries]"   # 可选：PDF解析/优化/时间序列
```

> **建议用 `python -m pip install` 而不是 `pip install`** —— 两者可能指向不同解释器，
> 前者保证装到当前 `python` 对应的环境里。

装完引擎就绪，智能体在跑流程时会调用它做求解和绘图。**你不需要手动跑它。**

想手动用引擎写代码：

```python
import numpy as np
from mathmodel.models import EvaluationSolver, StatsSolver, OptimizationSolver

# TOPSIS 评价 —— 返回 dict：scores 综合得分，rank 排名
r = EvaluationSolver().topsis(
    np.array([[0.1, 0.2, 0.3], [0.4, 0.3, 0.2], [0.3, 0.5, 0.4]]),
    weights=[0.3, 0.3, 0.4], impacts=[1, -1, 1])
print(r["scores"], r["rank"])          # [0.461 0.563 0.546] [3 1 2]

# 灰色预测 GM(1,1) —— forecast 未来值，mape 拟合误差，grade 分级
p = StatsSolver().grey_forecast([12, 15, 19, 24, 30, 38], forecast_steps=3)
print(p["forecast"], p["mape"], p["grade"])

# 0-1 整数规划 —— success 是否最优，x 解，fun 目标值
res = OptimizationSolver().integer_program(
    c=[-15, -22], A_ub=[[30, 45]], b_ub=[100], binary=True)
print(res.success, res.x, res.fun)     # True [1. 1.] -37.0
```

**AI 增强（可选）**：配 API Key 后，智能体在分析、选型、写作环节能调用大模型，
API 不可用时自动回退本地规则引擎。

```bash
cp api/.env.example .env      # 编辑 .env 填 Key
```

| 提供商 | 默认模型 | 获取 Key |
|--------|---------|---------|
| DeepSeek（默认） | `deepseek-reasoner` | [platform.deepseek.com](https://platform.deepseek.com) |
| OpenAI | `gpt-4o` | [platform.openai.com](https://platform.openai.com) |
| Anthropic | `claude-sonnet-5` | [console.anthropic.com](https://console.anthropic.com) |
| 智谱 GLM | `glm-4-plus` | [open.bigmodel.cn](https://open.bigmodel.cn) |
| 通义千问 | `qwen-plus` | [dashscope.aliyuncs.com](https://dashscope.aliyuncs.com) |
| Moonshot (Kimi) | `moonshot-v1-8k` | [platform.moonshot.cn](https://platform.moonshot.cn) |

> DeepSeek 注册即送额度。AI 增强显著提升论文质量，费用约 ¥3-5 / 题（约 20-25 次调用）。

### 当行动指南读（不装智能体也行）

`SKILL.md` 本身就是一份完整的作业指导书，自己照着走。

| 你处在哪 | 读什么 |
|---------|--------|
| 刚拿到新题，不知道从哪下手 | `SKILL.md` 的 Stage 0、Stage 1 |
| 模型选不定 | `references/aux-model-comparison.md`、`references/aux-decision-gate.md` |
| 想知道这题型有什么坑 | `references/math_modeling_norms.md`（含题型防错速查表） |
| 要写论文了 | `references/stage-5-writing.md`、`references/excellent_paper_template.md` |
| 交稿前自查 | `references/stage-6-verity.md` + 跑门禁脚本 |
| 想冲奖 | `references/o-papers-catalog.md`、`references/excellence-patterns.md`、`references/innovations.md` |

**门禁脚本在所有用法下都成立** —— 自己照着做，也能拿它逐条自查。

> 这个包**跟用什么智能体、什么大模型无关**。任何能读 Markdown 并执行 shell 命令的智能体都能用，人也能直接读。

---

## 🚦 门禁：可执行的，不是口号

技能包设 **CP1 / CP2 / CP3** 三道强制检查点，由脚本实测校验：

```bash
python skills/mcm-math-modeling/scripts/verify_checkpoint.py cp1|cp2|cp3 ./你的项目目录
```

非零退出即阻断流程 —— **自报 ✅ 不能替代脚本判定**。它查的是结构性问题：
子问题数与题面是否一致、每条约束有没有落到公式和代码、图表是不是重复、
论文里的数字能不能追溯回结果文件。

这些规则不是拍脑袋定的，每一条都对应一次真实的翻车：

| 真实翻车 | 这个包怎么防 |
|---------|------------|
| 2024：数错子问题数量 | 题面完整性校验，子问题数与题面声明不符 → CP1 阻断 |
| 2022：优化变量被偷偷固定成 0.5，结果差 10 倍 | 优化变量清单，每个「XX∈[A,B]」必须登记 |
| 2025：统计题当物理题做，得 39 分 | 强制统计清单：正态性检验、R² 下限、VIF、交叉验证 |
| 2024：90% 论文漏约束，解不可行 | 约束追溯矩阵：约束 → 公式 → 代码接口，逐条 ✅ |
| 2024：10 页 6 图，被降档 | 密度下限：≥18 正文页、≥12 数据图、≥3 结构图、每节 ≥800 字 |
| 2022：10 张凑数/复用图，触发自动降档 | 填充图 = 0，每张图必须追溯到真实数据 |
| 贪心算法当唯一解法 | 求解器真实性门禁：日志要有真实求解输出，纯贪心 = FAIL |

---

## 📦 技能包里有什么

```
skills/mcm-math-modeling/
├── SKILL.md              6 阶段完整流程，所有硬规则与门禁定义
├── install.sh / .bat     一键装进任意智能体
├── requirements.txt      numpy / matplotlib / scipy（可选）
├── icon.png              512×512 图标
├── references/  (29)     阶段指南 + 领域知识
├── scripts/     (8)      门禁校验、求解器模板、绘图、格式检查
└── assets/templates/ (382)  34 套赛题模板
```

| 目录 | 内容 |
|------|------|
| `references/` (29) | 建模规范、题型防错表、模型选型决策树、获奖论文结构、创新维度、COMAP 规则与 AI 使用声明、MCM 评分标准、O/F 奖论文剖析、论文写作与图表规范 |
| `scripts/` (8) | `verify_checkpoint.py`（CP 门禁，纯标准库）、`solver_templates.py`（GA/PSO/SA/二分/网格）、`writing_check.sh`、`check_mcm_format.py`、`nature_plot.py`、`flowchart.py`、`journal_fig.py`、`make_icon.py` |
| `assets/templates/` (382) | 34 套赛题模板，Typst + LaTeX 双版本 |

**支持范围**：中文 14 个赛制（国赛、华为杯、华中杯、五一杯、Mathorcup、三等杯…）
+ 英文 3 个赛制（APMCM / MCM / ICM），Typst 与 LaTeX 双引擎。

**依赖是可选的** —— 只有绘图和求解器模板需要 numpy/matplotlib/scipy，
核心门禁脚本 `verify_checkpoint.py` **只用 Python 标准库**。

---

## 🧩 引擎能算什么

40+ 求解算法，覆盖绝大多数赛题题型：

| 类别 | 算法 |
|------|------|
| **优化** | 线性规划、整数规划、非线性规划、多目标优化、动态规划 |
| **预测** | GM(1,1)、ARIMA、回归、XGBoost、指数平滑 |
| **评价** | TOPSIS、AHP、熵权法、模糊综合评价、灰色关联、CRITIC |
| **分类** | K-means、DBSCAN、层次聚类、SVM、随机森林、PCA |
| **微分方程** | ODE 求解、SIR、Logistic、PDE |
| **图论** | Dijkstra、Floyd-Warshall、最大流、TSP/VRP、A* |
| **统计** | t 检验、卡方、ANOVA、相关分析 |
| **灵敏度** | Tornado 图、Sobol 指数、蒙特卡洛置信区间 |

论文级图表（中英文风格、多面板、300dpi）：

```python
from mathmodel.visualization import Plotter, set_style

set_style("zh")
plotter = Plotter()
fig, ax = plotter.bar(x=["A", "B", "C"], y=[0.64, 0.32, 0.53], ylabel="TOPSIS得分")
plotter.save(fig, "figures/scores.pdf")
```

---

## 🗂️ 项目结构

```
├── start.py                   ⚡ 引擎编排入口（由智能体调用）
├── run.bat / install.bat      Windows 一键运行 / 安装
├── setup_api.bat              配置 API Key
│
├── skills/                    📚 工作流技能包
│   ├── mcm-math-modeling/     ⭐ 6 阶段工作流 + 34 套模板 + 门禁脚本
│   └── systematic-debugging/  通用调试流程
│
├── mathmodel/                 🧠 引擎核心
│   ├── analyzer/              题目分析 + 知识库
│   ├── parser/                题面/附件解析
│   ├── preprocessing/         数据清洗
│   ├── models/                40+ 求解算法
│   ├── solver/                求解调度
│   ├── sensitivity/           灵敏度分析
│   ├── visualization/         论文图表
│   ├── paper/                 Word / LaTeX 论文生成
│   ├── pipeline/              编排 + 进度显示
│   └── io/ · utils/ · pro/
│
├── api/                       🤖 LLM 接口（6 家提供商 + 自定义）
├── webui/app.py               🖥️ Streamlit 网页界面
├── matlab/                    MATLAB 工具箱
│
├── problems/                  📂 题目放这里
├── output/                    📁 论文自动输出
├── reports/                   📋 分析/结果/验收报告
├── figures/                   📈 图表（PDF + DrawIO 源文件）
├── code/                      💻 求解代码
├── paper/                     📄 论文（LaTeX 源文件）
├── demo/                      🎬 演示数据与用法
├── examples/                  📚 往届真题示例
├── tests/                     ✅ 测试
└── templates/                 引擎侧 LaTeX 模板
```

---

## ❓ 常见问题

**Q：装技能包需要联网吗？**
不需要。解压后本地安装即可，联网只是为了你之后用 AI API。

**Q：一定要装 numpy/scipy 吗？**
不用。门禁脚本只用标准库。引擎本身需要完整依赖（`python -m pip install -e .`）。

**Q：我能不能不装智能体，直接跑 `python start.py`？**
能跑，但**不建议**。`start.py` 是引擎编排入口，它会跑流程，
但"按竞赛标准做"的那套判断、决策门、门禁校验都在技能包里。
**想要能交的论文，装进智能体。**

**Q：Windows 上中文模板编译报错？**
中文 LaTeX 模板默认 `fontset=mac`（macOS 字体）。Windows 改成 `fontset=windows`
用宋体/黑体/楷体。macOS 之外的 Linux 装 `fonts-noto-cjk` 并用 `fontset=none`。

**Q：技能包和引擎哪个必须？**
都不必须。技能包能单独用（当指南读），引擎能单独用（写代码调用）。
配套用效果最好 —— 引擎算，技能包按标准组织。

**Q：能贡献吗？**
太能了。提 Issue 或 PR 都欢迎。

---

## 📮 联系

- qq：1164217385
- 使用说明视频：https://v.douyin.com/ke9D1HscMD0/

---

## 📄 许可证

MIT License
