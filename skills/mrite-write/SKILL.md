---
name: 写论文
description: 根据求解结果自动生成LaTeX论文，包含摘要、引言、模型建立与求解、检验、评价等完整章节
trigger:
  - "写论文"
  - "生成论文"
  - "撰写论文"
  - "论文生成"
---

# 写论文

## 目的

根据求解阶段的代码输出和数值结果，自动生成完整的LaTeX论文，包含从摘要到附录的全部章节。

## 论文目录结构

```
论文/
├── 论文.tex                    ← 主文件
├── format.cls                   ← 格式文件（预置）
├── fonts/                       ← 字体文件（预置）
├── 0.摘要.tex
├── 1.引言.tex
├── 2.总体分析.tex
├── 3.模型假设.tex
├── 4.符号说明.tex
├── 5.模型的建立与求解.tex       ← 主文件，\input 5.X子文件
├── 5.1.问题1的建立求解.tex     ← \input 5.1.1 和 5.1.2
├── 5.1.1.分析与准备.tex        ← 具体分析 + 流程图 + 模型准备
├── 5.1.2.建模与求解.tex       ← 模型建立 + 模型求解
├── 5.2.问题2的建立求解.tex     ← 从5.1复制改名
├── ...
├── 6.模型检验.tex
├── 7.模型评价.tex
├── 8.模型改进推广.tex
├── 9.参考文献.tex
└── 10.附录.tex
```

## 写作顺序

按以下顺序逐章生成：

### 1. 论文.tex 主文件

```latex
\PassOptionsToPackage{quiet}{xeCJK}
\documentclass[withoutpreface,bwprint]{format}
\usepackage{etoolbox}
\usepackage{ctex}
\BeforeBeginEnvironment{tabular}{\zihao{-5}}
\usepackage[framemethod=TikZ]{mdframed}
\usepackage{url}
\usepackage{array}
\usepackage{tabularx}
\usepackage{longtable}
\newcolumntype{C}{>{\centering\arraybackslash}X}
\newcolumntype{R}{>{\raggedleft\arraybackslash}X}
\newcolumntype{L}{>{\raggedright\arraybackslash}X}

\renewcommand{\textbf}[1]{{\song\bfseries #1}}

\usepackage{tikz}
\usetikzlibrary{arrows.meta}
\tikzset{
  box/.style={rectangle, draw, minimum width=3.2cm, minimum height=0.9cm, align=center},
  arrow/.style={thick, -{Stealth}}
}

\title{论文标题}

\begin{document}

\maketitle
\thispagestyle{empty}

\input{0.摘要.tex}
\thispagestyle{empty}

\tableofcontents
\thispagestyle{empty}
\newpage

\setcounter{page}{1}

\input{1.引言.tex}
\input{2.总体分析.tex}
\input{3.模型假设.tex}
\input{4.符号说明.tex}
\input{5.模型的建立与求解.tex}
\input{6.模型检验.tex}
\input{7.模型评价.tex}
\input{8.模型改进推广.tex}
\input{9.参考文献.tex}
\input{10.附录.tex}
\end{document}
```

### 2. 0.摘要.tex — 字数硬约束

| 段落 | 字数 | 说明 |
|------|------|------|
| 开头段 | ≤30字 | 固定 |
| 结尾段 | ≤20字 | 固定 |
| **总计** | **≤900字** | **不可超过** |
| 页数 | 必须=1页 | 编译后验证 |

**三种问题类型模板：**

**① 有数据型**：
```
\textbf{针对问题X：}本问是【类型】问题，需【要求】。首先，对附件数据预处理，提取【特征】，【清洗/标准化等操作】。接着，【变量筛选/降维/参数选择】。然后，采取【模型】进行【求解过程】。最后，【对比/验证/排序】，给出【输出】。结果讨论显示，\textbf{【数值结果】}，模型有效地【评价】。
```

**② 无数据型**：
```
\textbf{针对问题X：}本问是【类型】问题，需【要求】。首先，分析【机理/物理过程/目标约束】，建立【方程/动力学/优化模型】。接着，设定【参数/初始条件】。然后，通过【数值方法/仿真工具/求解算法】进行求解，得到【结果】。结果讨论显示，\textbf{【数值结果】}，模型有效地【评价】。
```

**③ 建议型**：
```
\textbf{针对问题X：}本问是建议总结问题，需【要求】。基于前文分析，从【角度1】和【角度2】出发，给出【建议数量】条建议。核心结论为\textbf{【要点】}。
```

### 3. 1.引言.tex

| 部分 | 要求 |
|------|------|
| 问题背景 | 2-3段自然段，宏观背景→问题来源→当前困境→解决渴求 |
| 研究意义（可选） | 1段，社会意义 + 科研意义 |
| 问题重述 | `\textbf{问题N：}` 每问≤2行，本质缩写 |

### 4. 2.总体分析.tex

三段式：
- 第1段：一句话总体表达
- 第2段：针对问题X建立了XX来解决XX（逐问串联）
- 第3段：总结各问题之间的递进关系

不画流程图。

### 5. 3.模型假设.tex

- 两段式：第1段"为简化问题，本文做出以下假设："
- itemize，每条 `\textbf{假设N：}`，≤2行

### 6. 4.符号说明.tex

统一使用 `longtable` + `>{\centering\arraybackslash}p{}`：

```latex
\begin{longtable}{>{\centering\arraybackslash}p{0.18\textwidth}>{\centering\arraybackslash}p{0.78\textwidth}}
  \caption{符号说明}
  \label{tab:符号说明} \\
  \toprule
  符号 & 含义 \\
  \midrule
  \endfirsthead
  \caption{符号说明（续）} \\
  \toprule
  符号 & 含义 \\
  \midrule
  \endhead
  \bottomrule
  \endfoot
  内容 & ... \\
\end{longtable}
```

**列宽强制规则**：比例总和 = 1.04 − 0.04 × N

| 列数 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|------|---|---|---|---|---|---|---|---|---|
| 比例总和 | 0.96 | 0.92 | 0.88 | 0.84 | 0.80 | 0.76 | 0.72 | 0.68 | 0.64 |

### 7. 5.模型的建立与求解.tex — 核心

按N动态生成，每个问题拆为2个子文件：

```latex
% 5.X.问题X的建立求解.tex
\subsection{问题X的模型的建立和求解}
\input{5.X.1.分析与准备.tex}
\input{5.X.2.建模与求解.tex}
```

#### 5.X.1 分析与准备

**具体分析**（文字 + 流程图）：
- 三段式：问题类型+方法 → 步骤串联 → "分析流程如图X所示"
- 固定9框流程图模板，只替换{}中文字，每框≤7字

```latex
\begin{figure}[ht]
  \begin{center}
    \begin{tikzpicture}[x=1cm, y=0.7cm]
      \node[box] (n11) at (0, 0) {...};
      \node[box] (n12) at (5, 0) {...};
      \node[box] (n13) at (10, 0) {...};
      \node[box] (n22) at (5, -3) {...};
      \node[box] (n21) at (0, -3) {...};
      \node[box] (n23) at (10, -3) {...};
      \node[box] (n31) at (0, -6) {...};
      \node[box] (n32) at (5, -6) {...};
      \node[box] (n33) at (10, -6) {...};
      \draw[arrow] (n11) -- (n12);
      \draw[arrow] (n12) -- (n13);
      \draw[arrow] (n23) -- (n22);
      \draw[arrow] (n22) -- (n21);
      \draw[arrow] (n13) -- ++(0,-1.0) -| (n23);
      \draw[arrow] (n21) -- (n31);
      \draw[arrow] (n31) -- (n32);
      \draw[arrow] (n32) -- (n33);
    \end{tikzpicture}
    \caption{问题X分析流程图}
    \label{fig:analysisX_flow}
  \end{center}
\end{figure}
```

**模型准备**（问题1必写）：

包含**数据预处理**和**算法选择**两部分。

数据预处理必须包含：
1. 预处理原因（数据来源、存在问题的说明）
2. 数据理解与提取（关键信息、特征数量、样本规模）
3. 预处理步骤（清洗→归一化→特征提取，含公式）
4. 预处理结果（统计量对比表）
5. 总结

算法选择必须包含：
1. 问题本质定性
2. 候选算法+评估维度
3. 对比表（具体算法名+评估等级优/良/中/差）
4. 分析对比结果
5. 总结+引出

#### 5.X.2 建模与求解

**模型建立**（三段式）：
- 开篇引文："针对问题X，本节将从XX角度建立XX模型"
- 中间展开：按编号步骤逐步建模，每步6-7公式，公式间用推导文字串联
- 总结桥接："综上所述，本节完成了XX模型的建立，接下来将基于此进行求解"

各类型步骤划分：

| 类型 | 编号步骤 |
|------|----------|
| 优化类 | 1.目标函数建立 → 2.约束条件建立 → 3.核心机理建模 → 4.求解算法建模 |
| 评价类 | 1.评价指标体系 → 2.指标权重确定 → 3.综合评价方法 |
| 分类/预测类 | 1.特征工程 → 2.模型构建 → 3.模型训练与评估 |
| 机理分析 | 1.机理分析框架 → 2.关键变量关系建模 → 3.模型整合与参数确定 |

**模型求解**：引文→表/图→分析。

### 8. 6.模型检验.tex

结构：开头引文→二级标题→文字解释→表/图→分析

| 必须包含 | 方法 |
|----------|------|
| 误差分析 | 优先5折交叉验证 |
| 灵敏度分析 | 引用求解阶段的结果 |

### 9. 7.模型评价.tex

优点4条 + 缺点2条，按模型写不按问题写。

```latex
\begin{itemize}
  \item \textbf{优点1：}...
  \item \textbf{优点2：}...
  \item \textbf{优点3：}...
  \item \textbf{优点4：}...
  \item \textbf{缺点1：}...
  \item \textbf{缺点2：}...
\end{itemize}
```

### 10. 8.模型改进推广.tex

各一段自然段落，不分点。

### 11. 9.参考文献.tex

**必须根据论文实际内容生成，禁止保留模板示例文献。**

- 每条 `\bibitem{标签}` 用 `作者姓氏+年份+关键词` 格式
- 国标 GB/T 7714-2015 格式，纯文本，严禁格式命令
- **数量**：8-15 条
- **引用要求**：每条必须在正文被 `\cite{}` 引用
- 写完论文后对照正文 `\cite{}` 逐一核对

### 12. 10.附录.tex

附件说明表，两列 `{LX}`。

## 写作规范速查

| 规则 | 说明 |
|------|------|
| 自然段落 | 正文禁止分点符号（1. 2. 3. 或 ● ○） |
| 禁止正文加粗 | `\textbf` 仅用于摘要"针对问题X"和问题重述"问题N：" |
| 图宽 | `0.8\textwidth` |
| 表宽 | `\textwidth` |
| 图表引用 | 所有图表必须被引用（"如图X所示""如表X所示"） |
| 图表文字 | 标题/caption/坐标轴全中文 |
| 禁止断页 | 全文任何位置不加 `\newpage`（仅目录后一处） |
| 图不画标题 | `set_title()` 不用，标题由 `\caption{}` 承担 |
| 表格文字 | 格子文字一行显示，不换行 |
| 禁止硬套模板 | 如不适配题目实际内容，AI自行调整 |

## 输出

所有 tex 文件写入 `论文/` 目录，tex 文件中只写可编译的 LaTeX 代码，不可出现模板指令提示语。完成后自动进入编译阶段。