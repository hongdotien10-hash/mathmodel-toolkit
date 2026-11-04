# 美赛（COMAP）格式硬规则 · 与优秀论文的差距 · 易错清单

> 本文件是**格式落地的唯一依据**。它来自三类材料：
> ①2026 赛季官方规则（COMAP Contest Rules / Problem C 卷首页）；
> ②2021 年 MCM 特等奖论文 C 题的**实测**版式（PDF 逐页量取）；
> ③2026 DWTS 论文实战中真实踩过的坑（每条都附了症状与修法）。
>
> **写完论文后必须回到本文件逐条自检**，尤其是第 4 节「易错清单」。

---

## 1. COMAP 2026 格式硬规则（违反即扣分或退回）

### 1.1 提交物

| 项目 | 硬性要求 |
|---|---|
| 文件 | **只提交一个 Adobe PDF**，不要交 Word/LaTeX 源文件 |
| 总页数 | **不超过 25 页**。含 Summary Sheet、目录、正文、Memo、参考文献、**附录** |
| 唯一豁免 | `Report on Use of AI` 附在 25 页之后，**无页数限制、不计入 25 页**，但**必须在同一个 PDF 里** |
| 身份信息 | **任何一页都不得出现**学生姓名、指导教师、所在院校 |
| 队号 | 只出现在页眉（`Team # 0000000`），Summary Sheet 上写题号与队号 |

> ⚠️ 25 页是**硬上限**，不是建议值。评分表上有一栏"是否遵守格式要求"。

### 1.2 版面

- **纸张**：US Letter（8.5×11 in）**或** A4（210×297 mm）——两者都合规，选哪个都行。
  实测差别：A4 的正文框比 Letter 大约 3.8%（`6.27×9.69 in` vs `6.5×9 in`），
  同样内容能少约半页。**如果卡页数，换 A4 往往比删内容划算。**
- **页边距**：四边 **≥ 2.54 cm（1 in）**。这是下限，可以正好取 1 in。
- **正文字号**：**≥ 12 pt**（Times/新罗马系）。标题 14–16 pt 加粗；图表标题 10 pt。
- **行距**：官方只要求可读，**没有规定磅值**。实测 2021 特等奖论文正文为 **12 pt / 14.5 pt（≈单倍）**。
  ⚠️ 教练常说的"18–22 磅行距"与 25 页上限**互相冲突**：按 18 pt 排，一篇有 10 图 7 表的论文会变 29 页而撞破上限。
  **建议按 14–14.5 pt 排**，并在 README 里注明取舍理由。
- **页眉**：**每一页都要有**，包含队号与页码，格式 `Team # 0000000, Page X of 25`。
  ⚠️ **第 1 页（Summary Sheet）也要页眉**——最常见的失分点。

### 1.3 章节与图表

- **Summary Sheet**：**独立成页、只占 1 页**，必须含**具体数值结果或结论**（不能是纯文字概述），末尾有 `Keywords`。
- **Table of Contents**：官方"encouraged"，**计入页数**。列到二级标题即可。
- **图题在下、表题在上**：格式 `Figure X: Description` / `Table X: Description`，编号**全篇连续**。
- **表格**：三线表（`\toprule/\midrule/\bottomrule`），**无竖线**；**数值列右对齐、文字列左对齐**。
- **公式**：居中，**编号右对齐**，**按出现顺序从 (1) 连续编号**（不要按章编号）。
- **参考文献**：编号连续，**每一条都必须在正文被引用过**（零引用条目会被视为凑数）。
- **附录**：计入 25 页。

### 1.4 AI 使用声明（2026 新增，最容易漏）

官方原文要求：*"Clearly indicate the use of LLMs or other AI tools in your report, including
which model was used and for what purpose. Please use inline citations and the reference
section. Also append the Report on Use of AI after your 25-page solution. This section has no
page limit and will not be counted as part of the 25-page solution."*

**三处缺一不可：**

1. **正文内联披露**（放在 Introduction 末尾或 Method 开头，一段即可）：

   ```latex
   A language-model assistant \cite{aiwork} was used in preparing this report.
   Its role was restricted to drafting and editing the English prose, to
   writing the code that produces the figures, and to checking the
   typesetting against the published rules. The modelling assumptions, the
   derivations, the computation and every number reported below were
   produced and verified by the team; the tools used and the way their
   output was checked are described in the Report on Use of AI that
   follows this report.
   ```

2. **参考文献里列出该工具**（与正文 `\cite` 对应）：

   ```latex
   \bibitem{aiwork}
   MiniMax. (2026) \emph{MiniMax-M3.1-Flash}, conversational assistant used for
   drafting and editing the English prose, for writing the figure and analysis
   code, and for checking the typesetting against the published rules.
   \url{https://www.minimaxi.com/}
   ```

3. **文末附 `Report on Use of AI`**（同一 PDF，25 页之后，**不加页眉**），建议五节：
   1. Tools used（工具与版本）
   2. What the model was used for, and what it was **not** used for（**划清边界**）
   3. Representative queries（代表性提示词 3–5 条）
   4. How the output was verified（**怎么验证**——独立脚本复算、与枚举/解析结果对照）
   5. Intellectual responsibility（责任归属）

> ⚠️ 报告里要写明"本节不计入 25 页，解答正文止于上一页"，否则检查脚本无法区分解答页与 AI 页。

---

## 2. 我们与特等奖论文的差距（差距不大，但都在"闭环"上）

以 2021 特等奖论文 C 题（4 篇合集，150 页）为基准，逐项对照后得到的结论：

| 维度 | 特等奖做法 | 我们的做法 | 差距 |
|---|---|---|---|
| **骨架** | Introduction / Assumptions / Notation / Analysis / Sensitivity / Evaluation / References / Memo | 同构，且多出"Problem 1–4 分章" | **无差距**（甚至更强） |
| **命题—证据闭环** | 每个结论后面紧跟"用什么数据、怎么算、算出多少" | 同构 | 无差距 |
| **验证的独立性** | 自己写了脚本**从原始 CSV 重新复算**，与正文解耦 | 同构（V1–V8 八项检查） | 无差距 |
| **不确定性口径** | 区分"数据决定的集合"与"模型决定的区间" | 同构（exact polytope vs bootstrap） | 无差距（这是加分项） |
| **语气与克制** | 大量"我们不认为……""这个结论依赖……" | 接近 | 略欠：应更多**主动写出对自己不利的证据** |
| **图表信息密度** | 每张图都在回答一个明确问题，caption 承担解释 | 同构 | 略欠：部分图可再减一个面板 |
| **篇幅效率** | 24 页讲完 3 个问题 | 25 页讲完 5 个问题 | 我们的**信息密度更高**，但也更容易触页上限 |

**一句话总结**：差距不在"有没有做"，而在**"敢不敢把对自己不利的证据写进正文"**。
特等奖论文常见的写法是——"这说明我们的重建**不能**回答这个问题""在这个子样本上结论**不成立**"，
这类句子反而是拿分点。**不足可以少写，重点是别藏。**

---

## 3. 篇幅预算（写之前先算）

25 页正文的经验预算（Letter、12pt/14.5pt、10 图 7 表时）：

| 部件 | 占页 | 说明 |
|---|---|---|
| Summary Sheet | 1.0 | 硬性 1 页 |
| 目录 | 0.5–1.0 | 行数 = 章数 + 二级标题数 |
| 正文纯文字 | ≈ 0.36 页 / 1000 字符（LaTeX 源码，含命令） | 约 3,000 字符/页 |
| 每张图（含 caption） | ≈ 0.25–0.30 | 图高 ≈ 1.6 in + caption 3–5 行 |
| 每张三线表（含 caption） | ≈ 0.20–0.25 | 9.5 pt 字、22 行约 0.35 页 |
| Memo | 1.0–2.0 | 题目要求 1–2 页 |
| 参考文献 | 0.5 | 11 条约 0.5 页（10.5 pt） |
| 附录 | 0.5–1.0 | 计入 25 页 |

> **新增加一章的算法**：先估新章需要多少页（正文 + 图 + 表），再从别处找**同样多**的空间。
> 只加不减是最常见的翻车方式。删内容要**整段删**，改写措辞省不下版面（实测：改写 500 字符 = 0 页）。

---

## 4. 易错清单（重点：这些坑本 skill 都踩过）

### A. 页眉 / 目录 / 附录

**A1. 第 1 页漏了页眉。**
症状：Summary Sheet 光秃秃，正文页有 `Team # xxx, Page X of 25`。
修法：页眉由 `\fancyhead` 全局控制，**不要**在首页用 `\thispagestyle{empty}`（那是给 AI 报告用的）。

**A2. `\@starttoc{toc}` 不会打印 "Contents" 标题。**
`\tableofcontents` 会打印，代价是继承 15 pt 的标题样式；手写标题则可控：

```latex
\clearpage
{\noindent\bfseries\fontsize{14}{17}\selectfont Contents\par}
\vspace{8pt}
\begingroup
\fontsize{10.5}{12}\selectfont
\setcounter{tocdepth}{2}
\makeatletter
\renewcommand*\contentsname{Contents}
% 默认 \l@section 会插入 \addvspace{1.0em}，11 个章就是 1/5 页的空白
\renewcommand*\l@section{\@dottedtocline{1}{0em}{2.4em}}
\renewcommand*\l@subsection{\@dottedtocline{2}{1.4em}{2.9em}}
\@starttoc{toc}
\makeatother
\endgroup
```

**A3. 目录溢出到第二页 = 白丢一整页。**
症状：加了两章后目录 51 行，PDF 里目录占了 2 页。
修法：① 目录字号压到 10.5/12；② 去掉 `\l@section` 的 `\addvspace`；③ 必要时 `tocdepth=1`。
**加章后第一件事就是查目录有没有溢出。**

**A4. `\appendix` 会强制换页。**
症状：AI 报告被顶到新的一页；或附录从新页开始、上一页留半页空白。
修法：**不要用 `\appendix`**，手动改计数器：

```latex
\makeatletter
\renewcommand{\thesection}{A}
\renewcommand{\thefigure}{A\arabic{figure}}
\renewcommand{\thetable}{A\arabic{table}}
\makeatother
\section{Appendices}
```

**A5. 浮动体参数太紧会整页留白。**
症状：图放不下就整页跳到下一页，前一页留 200+ pt 空白。
修法（写在 `mcm.sty`）：

```latex
\renewcommand{\topfraction}{0.97}
\renewcommand{\bottomfraction}{0.95}
\renewcommand{\textfraction}{0.02}
\renewcommand{\floatpagefraction}{0.80}
\setcounter{topnumber}{4}\setcounter{bottomnumber}{3}\setcounter{totalnumber}{6}
\setlength{\intextsep}{8pt plus 2pt minus 2pt}
\setlength{\textfloatsep}{10pt plus 2pt minus 2pt}
\setlength{\floatsep}{10pt plus 2pt minus 2pt}
```

### B. 编号与交叉引用

**B1. 公式编号跨节错乱。**
症状：正文里出现 (4.12) → (5.13) → (9.16)。
原因：`\numberwithin{equation}{section}` 与 `\@removefromreset{equation}{section}` 组合使用，
编号在不同节之间累加。
修法：**只用** `\renewcommand{\theequation}{\arabic{equation}}`，再配 `\@removefromreset`（针对命题/引理，不针对公式）。

**B2. 题号被章节号顶替。**
症状：正文写 "Problems 4 and 5"（其实是 Problem 1 和 2）。
原因：用 `\ref{sec:p1}` 打印章节号。
修法：**题号硬编码**，并在源码里留注释说明为什么不用 `\ref`：

```latex
% The problem numbers below are the ones printed on the task sheet, not
% the section numbers of this paper.
Problems~1 and~2
```

**B3. 参考文献零引用。**
症状：bibitem 有 11 条，正文只引了 8 条。
修法：交稿前把每条 bibitem 的 key 在正文里 grep 一遍。

**B4. 图/表编号不连续。**
症状：删了一张图后，后面全部错位。
修法：**永远用 `\label`+`\ref`，不要手写 "Figure 3"**；编译后用脚本从 `.aux` 读 `\newlabel` 核对连续性。

### C. 表格与版面

**C1. 大表放不下会把整页推空。**
症状：Notation 表 22 行放不下，LaTeX 把它整块推到下一页，前一页留白 282 pt。
修法（三管齐下）：表格字号 `\fontsize{9.5}{10.5}\selectfont` + `\renewcommand{\arraystretch}{0.87}`
+ 收紧上面 A5 的三个 `\setlength`；必要时把长表拆成两张。

**C2. 表格的百分号在数学模式里会炸。**
症状：`! Missing $ inserted.`，整段 caption 被当成数学。
修法：caption 里写 `with $95\%$` 是安全的，但**跨行断开** `$95\%$\npercentile` 也安全；
真正出错的是 `\%` 出现在数学模式外或 `$` 数量不成对。**caption 里尽量用纯文字百分比**（"95 per cent"）。

**C3. 三线表与对齐。**
`booktabs` 的 `\toprule/\midrule/\bottomrule`；数值列 `r`、文字列 `l`；
列头用 `\mcmhead{}` 宏把右对齐列头改成居中（自己定义）：

```latex
\newcommand{\mcmhead}[1]{\multicolumn{1}{c}{#1}}
```

**C4. 大表放不放得下，先量再排。**
符号表控制在 **12–16 行**；每行描述不超过一行（`p{4.5in}` 列宽）。

### D. 数据与建模（本 skill 的高价值坑）

**D1. REML 必须把 σ²_e 剖面掉，否则方差分量全部塌成 0。**
症状：所有方差比都是 0，日志像度是 1.000，profile CI 全是 NaN。
原因：把 σ²_e 固定为 1、**线性**惩罚残差平方和 `q`。此时"引入一个有 K 个水平的随机效应"的
对数行列式代价 `2K log σ` 会**压过**残差减少量，任何随机效应都不值得引入。
正解（集中 REML）：

```
ll = -0.5 * [ log|V| + log|X'V^-1 X| + (n-p)·log(q/(n-p)) + (n-p) ]
```

最后两项是 `log` 而不是 `q`——**这一处改动就是本 skill 实战中定位到的最隐蔽的 bug**。
务必用稠密矩阵对照验证（构造小规模随机数据，比对 log-likelihood 与 Δβ），并在模拟数据上确认能复原已知方差比。

**D2. 固定效应嵌套在随机效应里 → 设计矩阵可能奇异。**
症状：bootstrap 或子样本拟合时 `evaluate` 全部返回 −1e12。
原因：某个行业哑变量在重抽样后变成**全零列**（该行业一个样本都没抽到），`XtVX` 奇异。
修法：拟合前做一次**列秩筛选**（改进 Gram–Schmidt，丢掉线性相关的列）。

**D3. 成分数据（份额）的零和约束。**
症状：`log(0)` 报错；或把"份额之和=1"当独立约束重复计入。
修法：① 建模前剔除退赛/退赛后的 0 分记录（但**必须与前文口径一致**，否则同一篇里
"杠杆比 2.77"和"杠杆比 4.05"会同时出现，自相矛盾）；② 周内比较用
`log p − mean_week(log p)`（几何均值中心化），自动吸收周水平与周尺度。

**D4. 随机效应与固定效应都能解释同一件事。**
症状：年龄/行业这类"明星层"变量与明星随机效应共线，系数被压缩到 0。
原因：同一明星内，年龄、行业、舞者都是常数。
正解：**识别只可能来自"舞者跨赛季复用"**——所以必须在论文里**量化这种分离信息**，
例如"舞者解释了搭档年龄 33.3% 的方差，其余 66.7% 才是模型用来区分'年纪大'与
'配了个好舞者'的变异"。**把识别来源写清楚，本身就是得分点。**

**D5. 抽样扰动必须作用在正确的位置。**
症状：α=0（完全不看当周数据）的规则仍然有 22% 的翻转率。
原因：把噪声加在**锚定之后**的向量上。
修法：**先扰动原始量，再锚定**（噪声作用在原始尺度上，最后才做线性组合与归一化）。

**D6. 自己重建的量要和前文口径完全一致。**
症状：第 5 节报"杠杆比 2.77"，第 10 节算出 4.05，读者以为算错了。
原因：两处用了不同的样本（一个含退赛 0 分行、一个不含）**或不同的统计量**
（"均值的均值之比" vs "逐周比值的均值"）。
修法：**在论文里显式定义统计量**（"周杠杆比 λ_t = sd(v_t)/sd(j_t)"），
正文先报聚合量（均值之比）再报逐周分布，并说明两者关系。

### E. 篇幅与节奏

**E1. 改写措辞省不下版面，删整段才省。**
实测：逐句改写 500 字符 → 页数 0 变化；删掉 500 字符的整段 → 才可能少 0.15 页。
**要省版面就整段删，不要改写。**

**E2. 四处分散写"局限性"= 浪费版面。**
本 skill 实战中同时存在 §4.6「Discussion and limitations」、§5.7「Limitations」、
§7.2「Weaknesses」里的局限性、§9.6「Limitations」。**合并成一处（Model Evaluation 的
Weaknesses 列表）**，引用其他章即可。省下约 1 页，且结构更干净。

**E3. 附录也计入 25 页。**
把附录做成"一个表 + 一段说明"而不是"表 + 数据字典表 + 算法清单"。

**E4. 最后 1 页最难砍。**
末页往往只有几百字，却占掉整页。**把附录压成一段紧凑文字（不用浮动表）**，
末页就能并进上一页。

### F. AI 报告

**F1. 只在文末附 AI 报告、不在正文披露** → 不合规。正文要有内联披露 + 参考文献条目。
**F2. 把 AI 报告单独存成第二个 PDF** → 不合规。必须同一个 PDF。
**F3. AI 报告用 `\thispagestyle{empty}`** → 对，但**别把 `\pagestyle{empty}` 漏在解答页上**。
**F4. AI 报告里没写"怎么验证"** → 评审会认为没有验证。必须写独立复算方式。

---

## 5. 交稿前 60 秒自检

```
[ ] PDF 总页数 = 25 + AI 报告页数；解答页 ≤ 25
[ ] 第 1 页有页眉；每页都有页眉，页码连续
[ ] 摘要独立 1 页、含具体数值、有 Keywords
[ ] 目录没有溢出到第 2 页
[ ] 图题在下、表题在上、编号连续、表无竖线
[ ] 公式从 (1) 连续编号，没有按章跳号
[ ] 每条参考文献都在正文被引用过
[ ] 全篇没有出现学生/教师/学校名称
[ ] 正文有 AI 披露段 + 参考文献有 AI 条目 + 文末有 Report on Use of AI
[ ] 同一 PDF 里既有解答又有 AI 报告
[ ] 页边距 ≥ 2.54 cm，正文 ≥ 12 pt
```

自动化做法：用 `pypdf` 逐页取文本，
把**含页眉的页**判定为解答页（AI 报告页无页眉），据此分别计页数。
本包提供的 `scripts/check_mcm_format.py` 覆盖其中的页数、页边距、字体、
AI 披露段与匿名性检查；页眉页判定等定制项可按上述思路自行实现。
