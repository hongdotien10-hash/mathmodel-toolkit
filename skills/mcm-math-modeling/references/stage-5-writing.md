---
name: 5writing
description: "数学建模竞赛论文撰写阶段，支持 Typst 和 LaTeX 双引擎。根据 ANALYSIS_MODELING_REPORT.md、RESULTS_REPORT.md 和 figures/*.pdf 选择比赛模板、排版引擎、组织章节，并在论文正文中按章节直接插入图表。"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch
---

# 竞赛论文撰写（Typst / LaTeX）

本 skill 承接 `3coding-visual` 和 `4drawio`。前序阶段只提供真实数据、图表 PDF 和记录文件；本阶段负责选择比赛模板和排版引擎、组织论文结构，并决定每张图表放入哪个章节。

**Typst 引擎**下可调用 typst-author skill 学习 typst 写法；**LaTeX 引擎**参考本文件末尾的"LaTeX 写作要点"小节。

## 论文密度硬性标准（不可跳过）

**2024 CUMCM C 题教训：10 页 6 图过于单薄，竞赛论文应有 20-25 页、15-22 张图。评委翻论文的第一印象来自厚度和可视化密度。**

| 指标 | 最低要求 | 推荐值 | 说明 |
| --- | --- | --- | --- |
| **正文页数** | ≥ 18 页 | 20-25 页 | 不含附录；含摘要。低于 15 页视为工作量不足 |
| **数据图表数** | ≥ 12 张 | 15-20 张 | 仅统计 `3coding-visual` 生成的数据驱动图 |
| **流程/结构图** | ≥ 3 张 | 4-6 张 | 技术路线图 + 求解流程图 + 模型结构图 + 数据处理流程 |
| **图表总占比** | ≥ 50% 页面含图 | 60-70% | 美赛获奖论文平均 68% |
| **每核心章节图表** | ≥ 2 张 | 3-4 张 | 问题建模与求解章节不能纯文字 |
| **附录页数** | ≥ 3 页 | 5-8 页 | 详细结果表 + 核心代码片段 + 补充分析 |
| **核心章节字数** | **每节 ≥ 800 字** | 1000-1500 字 | B题教训：节均300字→7页论文 |
| **填充图禁令** | **0 张填充图** | — | B题教训：10张sin/copy图，直接降档 |
| **总页数（含附录）** | ≥ 22 页 | 25-30 页 | — |

## 时间约束

**当用户说「国赛标准」或「按国赛流程」时，时间不是约束条件。** 代码可以跑几小时甚至十几个小时，论文可以写几千字。质量是唯一优先级。不要因为「跑太久了用户会不耐烦」而走捷径——走捷径的后果（7页论文、填充图、参数拍脑袋）已被C/A/B三道题验证。用户要的是结果正确，不是速度快。

## 论文质量指南（非强制KPI——写完后自查）

写论文时不用盯着这些数字。写完后通读一遍，用以下清单自查：

- 每个子问题是否完成了「建模→求解→结果→小结」闭环？
- 是否至少有1张表展示核心计算数据（峰值/迭代/误差）？
- 是否讨论了结果的不确定性来源？
- 参考文献是否有至少2篇来自该方法领域的期刊论文（不只是教材）？
- 有没有TikZ画的原理示意图？（加分项，非必须）

**对标国赛获奖论文**：好的论文不需要凑字数。干净的三线表、清晰的数学推导、每一段话都在论证一个问题——这些比300字的讨论子节更有价值。

**图表不足时的处理**：
- 如果 `figures/` 中数据图不足 12 张 → **停止论文撰写**，回到 `3coding-visual` 补图
- 如果核心章节某章无图 → 该章至少补一张结果对比图或分布图
- 附录必须包含：① 完整种植方案/结果表；② 核心求解代码（不超过 5 页）；③ 补充灵敏度分析

**美赛特别要求**：图表占比底线 65%，Summary Sheet 独立一页。

## 数学建模规范参考

如需领域判断，读取 `references/math_modeling_norms.md`（相对 skill 根目录，下同） 中的”论文写作””图表与可视化”和”非数据图工具选择”小节。

**撰写论文前必须读取 `references/excellent_paper_template.md`**。

## 每个子问题强制闭环（不可跳过）

**六道题的共性问题：每个子问题写到结果就停了，缺方法选型论证、缺结果合理性解释、缺小结。这不是「写得不够好」，是结构不完整。**

每个子问题章节必须包含以下五个子节：

```markdown
\subsection{模型建立}
- 数学推导过程，≥2个编号公式
- 说明「为什么选这个方法」——列出至少1个被排除的替代方法及排除理由

\subsection{求解过程}
- 算法核心步骤（伪代码或自然语言描述）
- 算法选择理由（为什么不选另一个方法？）

\subsection{结果分析}
- 用图表和表格呈现结果
- **结果合理性验证**：用至少一种方式验证（量级是否合理？退化到简化情形是否一致？与已知基准是否吻合？）

\subsection{方法对比}（可选但加分）
- 将本方法与至少一种替代方法的结果对比
- 说明差异原因

\subsection{小结}
- 1-2句话直接回应题目问题
- 给出明确数值结论
```

**CP3 将检查**：每个子问题是否有「模型建立」「求解」「结果」「小结」标记。覆盖率<50% → FAIL。

**2022 A题教训**：Q2(2) Pmax=2437W 远超入射功率680W，如果有「结果合理性验证」这一步，就会发现数值不可能——但当时没有这步，直接写进了论文。

## 模板族

本技能内捆绑的模板位于：

```text
assets/templates/zh/<竞赛>/main.typ         # Typst 模板
assets/templates/zh/<竞赛>-latex/main.tex   # LaTeX 模板
assets/templates/en/<竞赛>/main.typ         # Typst 模板
assets/templates/en/<竞赛>-latex/main.tex   # LaTeX 模板
```

**LaTeX 模板覆盖范围**：所有中文模板和英文模板均已提供 LaTeX 版本（`-latex` 后缀），使用 xelatex 编译。

支持的中文模板（Typst + LaTeX 双版本）：

```text
apmcm, changsanjiao, cumcm, default, diangongbei, dongsansheng,
huashubei, huaweibei, huazhongbei, mathorcup, mcm, shuweibei, stats, wuyibei
```

华为杯、华中杯、五一杯统一使用 `huaweibei`、`huazhongbei`、`wuyibei` 作为模板。

支持的英文模板（Typst + LaTeX 双版本）：

```text
apmcm, default, mcm
```

论文中的所有数值图表结论必须来自 `reports/RESULTS_REPORT.md` 或 `figures/*`。不得编造、估算或使用不同的四舍五入方式。


## 工作流

### 步骤 -1：撰写论文大纲（必做，不可跳过）

**在写任何正文内容之前，必须先读取 `references/excellent_paper_template.md`，然后生成论文大纲文件 `paper/OUTLINE.md`（或 `output/paper/OUTLINE.md`）。**

大纲格式：
```markdown
# 论文大纲

## 摘要
- 覆盖六要素：[背景]、[思路]、[模型]、[结果]、[亮点]、[关键词]

## 问题重述与分析
- 要点1: [提炼问题背景与研究意义]
- 要点2: [拆分子问题与递进关系]
- 图: 技术路线图

## 模型假设
- 分类: [几何假设/测量假设/环境假设], ≥5条
- 每条对应后续建模依据

## 符号说明
- 核心符号≥10个，表格形式

## 问题X建模与求解 (X=一,二,三,四)
### X.1 模型建立
- 要点: [数学推导, ≥2个公式]
### X.2 求解过程
- 算法: [方法名+选择理由]
### X.3 结果分析
- 图X-1: [图表描述+数据来源]
- 表X-1: [表格内容]
### X.4 小结
- [一句话结论]

## 灵敏度/模型检验
- 灵敏度: [关键参数+扰动范围]
- 检验: [验证方法]
- 图: [Tornado/收敛图等]

## 模型评价与推广
- 优点≥3条, 缺点≥2条, 推广≥2个方向

## 附录
- 核心代码清单, 补充数据表
```

**规则**：
- 大纲中每个「图X-X」必须注明数据来源（solver输出/参数扫描/题面数据），不允许「合成数据」
- 大纲中每个「表X-X」必须注明表头内容和行数
- CP3 将检查 OUTLINE.md 是否存在。不存在 → **CP3 FAIL**

### 步骤 0：确定排版引擎

**撰写论文前必须让用户选择排版引擎。** 引擎决定后续所有步骤（模板路径、章节文件扩展名、图片插入语法、编译命令），选错会导致整篇论文格式错误。

使用 AskUserQuestion 工具向用户询问："撰写论文使用哪种排版引擎？"

- 选项 1：LaTeX（xelatex 编译，数学建模竞赛主流，模板已全部就绪）— 推荐选项放第一位
- 选项 2：Typst（typst 编译，调用 typst-author skill 辅助写作）

询问前先读取 `plan.md` 的"用户偏好 → 排版引擎"字段作为预选项：
- 若 plan.md 已记录引擎选择，向用户确认："检测到之前选择的引擎是 <LaTeX/Typst>，是否沿用？"
- 若 plan.md 不存在或未记录引擎选择，直接询问用户选择。
- 若用户未明确指定或跳过，**默认使用 LaTeX**。

根据确定的引擎选择对应模板族：

- **Typst 引擎**：使用 `assets/templates/<lang>/<竞赛>/main.typ`，调用 typst-author skill。编译命令 `typst compile main.typ`。
- **LaTeX 引擎**：使用 `assets/templates/<lang>/<竞赛>-latex/main.tex`，xelatex 编译（中文和英文均需跑两遍解决交叉引用）。编译命令 `xelatex -interaction=nonstopmode main.tex`（执行两次）。

**后续步骤中的所有代码示例、文件扩展名、图片插入语法都必须按所选引擎选择对应版本，不要混用。**

### 步骤 1：选择语言和模板


除非用户明确要求中文，否则 MCM/ICM/COMAP 一律使用英文。所有中文竞赛名称使用中文。

模板键示例（Typst 引擎）：

```text
长三角 -> zh/changsanjiao
APMCM 英文版 -> en/apmcm
全国赛/国赛/CUMCM -> zh/cumcm
统计建模 -> zh/stats
MCM/ICM/COMAP -> en/mcm
```

模板键示例（LaTeX 引擎）：

```text
全国赛/国赛/CUMCM -> zh/cumcm-latex
MCM/ICM/COMAP -> en/mcm-latex
```

### 步骤 2：准备模板

用以下命令检查捆绑模板是否可访问（`SKILL_DIR` 为本 skill 所在目录）：

**Typst 模板**：

```bash
ls "$SKILL_DIR/assets/templates/zh/<竞赛>/main.typ" 2>/dev/null && echo "OK" || echo "MISSING"
```

- **文件存在（OK）**：直接将 `assets/templates/zh/<竞赛>/` 整目录复制到 `paper/`。这些模板是自包含入口文件，不依赖额外共享样式文件。
- **文件不存在（MISSING）**：说明 skill 未完整安装或在沙箱中，此时依照本 SKILL.md 步骤 3 列出的对应节文件结构，从零重建最小可编译 Typst 框架，并在 `paper/` 内注明"重建自 default 结构"。

存在匹配模板时，绝不从零开始写论文。

**LaTeX 模板**：

```bash
ls "$SKILL_DIR/assets/templates/zh/<竞赛>-latex/main.tex" 2>/dev/null && echo "OK" || echo "MISSING"
```

- **文件存在（OK）**：将 `assets/templates/zh/<竞赛>-latex/` 整目录复制到 `paper/`。
- **文件不存在（MISSING）**：说明 skill 未完整安装或在沙箱中，此时依照本 SKILL.md 步骤 3 列出的对应节文件结构，从零重建最小可编译 LaTeX 框架，并在 `paper/` 内注明"重建自 default-latex 结构"。


### 步骤 3：构建图表规划

在写正文各节之前，根据 `figures/*.pdf`、`reports/RESULTS_REPORT.md`，以及 `reports/DRAWIO_REPORT.md`（如果存在）构建图表规划：

```text
图表规划
fig_roadmap.pdf -> 引言/问题重述
fig_flow_q1.pdf -> 问题一模型构建
fig_flow_q2.pdf -> 问题二模型构建
fig_pipeline.pdf -> 数据预处理/方法节
结果图 -> 对应的结果节
```

图片路径相对于写入该图片的文件：写在 `paper/main.typ` 或 `paper/main.tex` 中通常用 `../figures/xxx.pdf`，写在 `paper/sections/*.typ` 或 `paper/sections/*.tex` 中通常用 `../../figures/xxx.pdf`。

**Typst 引擎**图片插入：

```typst
#figure(
  image("../../figures/fig_q1_error_dist.pdf", width: 85%),
  caption: [问题一预测误差分布],
)
```

**LaTeX 引擎**图片插入：

```latex
\begin{figure}[H]
  \centering
  \includegraphics[width=0.85\textwidth]{../../figures/fig_q1_error_dist.pdf}
  \caption{问题一预测误差分布}
  \label{fig:q1_error}
\end{figure}
```

英文论文使用英文图注。

### 步骤 4：撰写各节

**以下章节文件名按所选引擎使用 `.typ`（Typst）或 `.tex`（LaTeX）扩展名。** 例如 Typst 引擎用 `1_restatement.typ`，LaTeX 引擎用 `1_restatement.tex`。文件名主体保持一致。

中文数学建模通用模板各节文件（`changsanjiao`、`diangongbei`、`huashubei`、`mathorcup`、`wuyibei`）：

```text
1_restatement.typ  - 问题重述与分析
2_analysis.typ     - 数据理解与总体思路
3_assumptions.typ  - 模型假设
4_symbols.typ      - 符号说明
5_problem1.typ     - 问题一建模与求解
6_problem2.typ     - 问题二建模与求解
7_problem3.typ     - 问题三建模与求解
...         - 根据题目调整问题数量  
8_evaluation.typ   - 灵敏度分析、模型评价与推广
A_code.typ         - 附录代码
```

国赛/华中杯/华为杯（`cumcm`、`huazhongbei`、`huaweibei`）按以下章节结构：

```text
1_restatement.typ
2_analysis.typ
3_assumptions.typ
4_symbols.typ
5_problem1.typ
6_problem2.typ
7_problem3.typ
...        - 根据题目调整问题数量
8_sensitivity.typ
9_evaluation.typ
A_code.typ
```

东三省模板（`dongsansheng`）额外使用单独摘要文件：

```text
abstract.typ
1_restatement.typ
2_analysis.typ
3_assumptions.typ
4_symbols.typ
5_problem1.typ
6_problem2.typ
7_problem3.typ
...       - 根据题目调整问题数量
8_evaluation.typ
A_code.typ
```

数维杯模板（`shuweibei`）保留原 LaTeX 的示例入口命名：

```text
Abstract.typ
Introduction.typ
2_analysis.typ
3_assumptions.typ
4_symbols.typ
5_problem1.typ
6_problem2.typ
7_problem3.typ
...      - 根据题目调整问题数量
8_evaluation.typ
Appendices1.typ
A_code.typ
```

中文默认模板（`default`）：

```text
1_restatement.typ
2_assumptions.typ
3_symbols.typ
4_problem1.typ
5_problem2.typ
6_problem3.typ
...      - 根据题目调整问题数量
7_sensitivity.typ
8_evaluation.typ
A_code.typ
```

中文统计建模各节文件：

```text
1_introduction.typ
2_method.typ
3_data.typ
4_analysis.typ
5_results.typ
6_conclusion.typ
A_code.typ
```

英文 MCM/APMCM 各节文件（`en/mcm`、`en/apmcm`、`zh/mcm`、`zh/apmcm`）：

```text
1_introduction.typ
2_assumptions.typ
3_model_design.typ
4_solution.typ
5_sensitivity.typ
6_strengths_weaknesses.typ
7_conclusions.typ
A_code.typ
```

**LaTeX 模板章节文件**（对应 `-latex` 后缀模板，结构与 Typst 版本一一对应）：

国赛 LaTeX 模板（`zh/cumcm-latex`，对应 `cumcm` Typst 版本）：

```text
1_restatement.tex
2_analysis.tex
3_assumptions.tex
4_symbols.tex
5_problem1.tex
6_problem2.tex
7_problem3.tex
8_sensitivity.tex
9_evaluation.tex
A_code.tex
```

MCM/ICM LaTeX 模板（`en/mcm-latex`）：

```text
1_introduction.tex
2_assumptions.tex
3_model_design.tex
4_solution.tex
5_sensitivity.tex
6_strengths_weaknesses.tex
7_conclusions.tex
A_code.tex
```

其余 LaTeX 模板（`changsanjiao-latex`、`default-latex`、`huashubei-latex`、`mathorcup-latex`、`wuyibei-latex`、`huazhongbei-latex`、`huaweibei-latex`、`diangongbei-latex`、`dongsansheng-latex`、`shuweibei-latex`、`stats-latex`、`apmcm-latex`、`mcm-latex`、`en/apmcm-latex`、`en/default-latex`）的章节文件命名与上述结构类似，以 `main.tex` 中 `\input{}` 引用的文件名为准。

英文默认模板（`en/default`）：

```text
1_introduction.typ
2_assumptions.typ
3_notations.typ
4_model.typ
5_sensitivity.typ
6_evaluation.typ
7_conclusions.typ
A_code.typ
```

**正文写作应使用连贯的学术段落。避免在最终论文中出现工作流内部名称，如 `reports/`、`figures/` 或 `CLAUDE.md`。**

### 步骤 5：参考文献

只使用真实存在的参考文献。文件名按引擎选择：Typst 用 `paper/references.typ`，LaTeX 用 `paper/references.tex`。

**Typst 引擎**：

```typst
#set enum(numbering: "[1]")
#enum[
  作者. 题名[J]. 期刊名, 年份, 卷(期): 页码.
  Author. "Title." Journal or Conference, year.
]
```

正文上标引用：`相关研究已用于物流网络优化#super("[1]")。`

**LaTeX 引擎**：

```latex
\begin{thebibliography}{99}
  \bibitem{ref1} 作者. 题名[J]. 期刊名, 年份, 卷(期): 页码.
  \bibitem{ref2} Author. "Title." Journal, year.
\end{thebibliography}
```

正文引用用 `\cite{ref1}` 或 `\cite{ref1,ref2}`。

### 步骤 6：最后撰写摘要或总结

在所有章节完成后撰写中文摘要或英文 Summary Sheet。必须包含每个子问题的方法和精确的数值结果。

### 步骤 7：自修复编译循环（必须执行，对标 Modex 质量门）

论文写完后，不是「跑一次 xelatex/typst」就完了。必须进入**编译→诊断→修复→重编译**闭环，直到 0 错误 + 警告受控。

#### 7a. 首轮编译

**LaTeX 引擎**：
```bash
cd paper && xelatex -interaction=nonstopmode main.tex 2>&1 | tee compile.log
```

**Typst 引擎**：
```bash
cd paper && typst compile main.typ 2>&1 | tee compile.log
```

#### 7b. 错误分类与修复策略

读取编译日志中的错误和警告，按以下策略自动修复：

| 错误类型 | 检测关键词 | 自动修复策略 |
| --- | --- | --- |
| **未定义引用** | `undefined reference`, `Citation undefined`, `Reference ... undefined` | 运行第二遍 xelatex（交叉引用需要两遍编译） |
| **缺失宏包** | `file ... not found`, `Unknown option` | 安装缺失包（`tlmgr install`）或替换为标准包 |
| **字体缺失** | `Font ... not found`, `cannot find font` | 替换为系统可用字体（如 SimSun→Noto Serif CJK SC） |
| **图片缺失** | `file ... not found` (图片路径) | 检查 `figures/` 路径，相对路径相对于 section 文件修正 |
| **Overfull hbox** | `Overfull \hbox` | 调整换行或微调表格列宽；超过 5 个才修复，否则标记为可接受 |
| **Underfull hbox** | `Underfull \hbox` | 通常可忽略；超过 10 个才处理 |
| **数学公式错误** | `Missing $`, `Extra }`, `Missing \right` | 定位行号，补全或移除配对符号 |
| **Typst 语法错误** | `error:` | 根据 typst 错误信息中的行号和提示修复 |
| **编码问题** | `Invalid UTF-8`, `inputenc` | 确保文件保存为 UTF-8 |

#### 7c. 修复-重编译循环

```
第 1 轮：编译 → 收集错误/警告
   ↓
第 2 轮：修复错误 → 编译 → 收集剩余错误/警告
   ↓
第 3-N 轮：修复 → 编译 → 检查
   ↓
退出条件：
  ✅ LaTeX: 0 errors + 0 undefined references（两遍 xelatex 后）
  ✅ Typst: 0 errors（typst compile 返回码 0）
  ⚠️ 警告：Overfull hbox ≤ 5 个可接受
  ❌ 超过 10 轮仍未清 0 → 记录未修复问题和原因，交由人工处理
```

#### 7d. 编译日志

在 `paper/` 目录生成 `COMPILE_LOG.md`：

```markdown
# 编译日志

| 轮次 | 时间 | 错误数 | 警告数 | 修复内容 | 状态 |
| --- | --- | --- | --- | --- | --- |
| 1 | 14:32 | 3 | 12 | — | ❌ |
| 2 | 14:33 | 1 | 8 | 修复缺失引用 | ❌ |
| 3 | 14:34 | 0 | 4 | 第2遍xelatex解决交叉引用 | ✅ |

**最终状态**：✅ 编译通过（0 错误，4 警告）
**PDF 路径**：`paper/main.pdf`
**页数**：22 页
```

#### 7e. 编译后的硬性检查

编译通过后，做以下快速人工验证（AskUserQuestion 提示用户检查，而非自动判断）：

1. PDF 能正常打开且无空白页？
2. 所有公式渲染正常（无 `??` 或乱码）？
3. 所有图片可见（无空白框）？
4. 中文/英文全文可读（无 tofu 缺字）？
5. 页数在比赛限制内？

任一项不通过 → 找到原因 → 修复 → 重新编译。

## LaTeX 写作要点

以下要点供 **LaTeX 引擎**使用。Typst 引擎请调用 typst-author skill 获取语法帮助。

### 编译命令

```bash
# 中文模板（xelatex，跑两遍解决交叉引用）
xelatex main.tex && xelatex main.tex

# 英文模板（xelatex，同样跑两遍）
xelatex main.tex && xelatex main.tex
```

### 文档结构

```latex
\documentclass[a4paper,12pt]{article}   % 英文
\documentclass[a4paper,12pt]{ctexart}   % 中文

\usepackage{...}   % 宏包加载
\usepackage{graphicx}   % 图片支持
\usepackage{booktabs}   % 三线表
\usepackage{amsmath,amssymb}   % 数学公式
\usepackage{hyperref}   % 交叉引用（需两遍编译）
```

### 图表插入

```latex
\begin{figure}[H]
  \centering
  \includegraphics[width=0.85\textwidth]{../../figures/fig_q1.pdf}
  \caption{图注}
  \label{fig:q1}
\end{figure}

% 三线表
\begin{table}[htbp]
  \centering
  \caption{表注}
  \begin{tabular}{ccc}
    \toprule
    \textbf{列1} & \textbf{列2} & \textbf{列3} \\
    \midrule
    数据 & 数据 & 数据 \\
    \bottomrule
  \end{tabular}
\end{table}
```

### 交叉引用

```latex
如图~\ref{fig:q1}所示，...   % 图片引用
式~(\ref{eq:objective}) 给出...   % 公式引用
见第~\pageref{fig:q1} 页   % 页码引用
```

### 数学公式

```latex
行内公式：$f(x) = \sum_{i=1}^n \theta_i \phi_i(x)$

行间公式：
\begin{equation}
  \mathcal{L}(\theta) = \frac{1}{N}\sum_{i=1}^N (y_i - \hat{y}_i)^2
  \label{eq:objective}
\end{equation}
```

### 章节和强调

```latex
\section{问题重述}
\subsection{问题背景}
\textbf{问题一：} xxx   % 对应 Typst 的 #strong
```
