# mcm-math-modeling

**A complete, checkpoint-enforced mathematical modeling competition workflow — from problem
statement to submission-ready paper.**

Works for MCM/ICM (COMAP), CUMCM (国赛), and the regional Chinese contests (华为杯, 华中杯,
五一杯, Mathorcup, 数模杯, 三等杯...). Includes 34 competition paper templates, a mechanical
quality-gate script, and the domain knowledge that separates an award paper from an ordinary one.

---

## 这是什么

一个**技能包**（skill package）。它本身是一套完整的方法论：怎么读题、怎么拆子问题、
怎么选模型、怎么把约束一条条落到公式和代码、怎么写论文、怎么验收。

包装成技能包，只是为了让这套方法论能被**直接复用**，而不是每次重新讲一遍。

**两种用法，同等重要：**

| 用法 | 适合谁 | 怎么做 |
|------|--------|--------|
| **A. 装进智能体** | 想让 AI 按竞赛标准跑完整流程 | 把本文件夹放进任意智能体的 skills 目录，之后说人话触发 |
| **B. 当行动指南读** | 想自己掌控每一步、或者带人组队 | 直接读 `SKILL.md` 和 `references/`，照着做，门禁脚本拿来自查 |

两者用的是同一份内容。用法 A 是把执行权交给智能体，用法 B 是自己照着走 ——
**门禁脚本在两种用法下都成立**，这是这个包的核心价值。

> 它跟"用哪个智能体、哪个大模型"无关。任何能读 Markdown 并执行 shell 命令的智能体都能用，
> 人也能直接读。

---

## 用法 A：装进智能体

### 一键安装

进入本目录执行：

**Windows**

```bat
install.bat
```

**macOS / Linux**

```bash
chmod +x install.sh && ./install.sh
```

脚本自动探测本机已装的智能体并复制到对应目录：

```
✓ 已安装到 C:\Users\<你>\.claude\skills\mcm-math-modeling
✓ 已安装到 C:\Users\<你>\.workbuddy\skills\mcm-math-modeling
```

只装某一个，或先看能装哪些：

```bash
./install.sh --list      # 列出识别到的智能体
./install.sh claude      # 只装 Claude Code
./install.sh workbuddy   # 只装 WorkBuddy
```

装完**重启智能体**（或新开会话）。

### 手动安装

把整个 `mcm-math-modeling/` 文件夹复制到目标智能体的 skills 目录：

| 智能体 | 用户级目录（全局可用） | 项目级目录（仅当前项目） |
|--------|------------------------|--------------------------|
| **WorkBuddy** | `~/.workbuddy/skills/` | `<项目>/.workbuddy/skills/` |
| **WorkBuddy 国际版** | `~/.workbuddy-intl/skills/` | `<项目>/.workbuddy-intl/skills/` |
| **Claude Code** | `~/.claude/skills/` | `<项目>/.claude/skills/` |
| **Cursor** | `~/.cursor/skills/` | `<项目>/.cursor/skills/` |
| **Codex** | `~/.codex/skills/` | — |
| **Gemini CLI** | `~/.gemini/skills/` | — |
| **OpenCode** | `~/.config/opencode/skills/` | — |
| **Windsurf** | `~/.windsurf/skills/` | — |

> Windows 下 `~` 即 `C:\Users\<你的用户名>`。装到项目级目录时，该目录会跟着仓库走，
> 适合团队共享。

### 装完怎么用

不需要记命令，也不需要点名技能：

> 这是 2025 MCM C 题的题面和附件，帮我按竞赛流程做一遍

或者：

> 帮我做这道数模题，LaTeX 排版，中文论文

`description` 里带了触发词（数模 / 建模 / MCM / CUMCM / 国赛 / 美赛 / 杯赛…），
智能体会自行判断该不该加载本技能。加载后它会先问你四件事：

1. **排版引擎** —— Typst 还是 LaTeX？
2. **竞赛类型** —— MCM/ICM、国赛、华为杯、华中杯、五一杯、Mathorcup？
3. **论文语言** —— 英文（MCM/ICM 按 COMAP 规定必须英文）还是中文？
4. **子问题数量** —— 已知还是从题面判断？

然后按 6 阶段推进，在三个决策门停下来等你拍板。

---

## 用法 B：当行动指南读

不想装也行。`SKILL.md` 就是一份完整的作业指导书，从头到尾读完就能上手。

**推荐的读法**：

| 你处在哪 | 读什么 |
|---------|--------|
| 刚拿到新题，不知道从哪下手 | `SKILL.md` 的 Stage 0 和 Stage 1 |
| 模型选不定 | `references/aux-model-comparison.md`、`references/aux-decision-gate.md` |
| 想知道这题型有什么坑 | `references/math_modeling_norms.md`（含题型防错速查表） |
| 要写论文了 | `references/stage-5-writing.md`、`references/excellent_paper_template.md` |
| 交稿前自查 | `references/stage-6-verity.md`，并跑门禁脚本 |
| 想冲奖 | `references/o-papers-catalog.md`、`references/excellence-patterns.md`、`references/innovations.md` |

**边做边查的门禁**：

```bash
# 建模做完了 —— 检查子问题数、约束追溯、变量清单
python scripts/verify_checkpoint.py cp1 ./你的项目目录

# 求解做完了 —— 检查求解器真实性、约束回代、图表数量
python scripts/verify_checkpoint.py cp2 ./你的项目目录

# 论文写完了 —— 检查章节完整性、页数、图表嵌入、数值可追溯
python scripts/verify_checkpoint.py cp3 ./你的项目目录
```

非零退出即不合格。脚本查的是**结构性问题**（数量、追溯、一致性）——
比如"子问题数与题面声明不符""某条约束没有对应公式""图片重复""论文里的数字找不到出处"。

它查不了模型本身是否科学合理——那部分靠 Stage 2 的量级校验和交叉验证。

**脚本是可选的**：不装任何依赖也能用，因为 `verify_checkpoint.py` 只依赖 Python 标准库。
不想用脚本，手工按 `references/stage-*.md` 里的清单逐条核对也成立。

---

## 依赖

```bash
python -m pip install -r requirements.txt   # numpy / matplotlib / scipy
```

**依赖是可选的**，只有绘图（`nature_plot.py` / `flowchart.py` / `journal_fig.py`）
和求解器模板（`solver_templates.py`）需要它们。核心的门禁脚本
`verify_checkpoint.py` **只用 Python 标准库**。

> 注意：用 `python -m pip install` 而非 `pip install` —— 两者可能指向不同解释器，
> 前者保证装到当前 `python` 对应的环境里。

---

## 为什么要用它

Most "AI solves your modeling contest" tools generate a plausible-looking paper. That is
exactly what judges are trained to detect, and it is why templated solutions now get
downgraded.

This skill takes the opposite approach: it **forces the hard parts to be done properly**, and
uses an executable script — not good intentions — as the enforcer.

Every rule in this package traces to a real contest failure:

| Real failure | What this skill does about it |
| --- | --- |
| A team miscounted the sub-problems (2024) | Statement completeness check; sub-problem count must match the statement or CP1 blocks the pipeline |
| An optimization variable was silently fixed at 0.5, inflating a result 10x (2022) | Optimization variable inventory; every "XX∈[A,B]" must be listed as a decision variable |
| A statistics problem was solved as a physics problem, scored 39 (2025) | Mandatory statistics checklist: normality tests, R² floor, VIF, cross-validation |
| Over 90% of papers missed a constraint and produced infeasible solutions (2024) | Constraint traceability matrix: every constraint → formula → code interface, all must be ✅ |
| A 10-page, 6-figure paper was downgraded (2024) | Paper density floor: ≥18 body pages, ≥12 data figures, ≥3 structure diagrams, ≥800 words per section |
| 10 filler sin/copy figures triggered an automatic downgrade (2022) | Filler figures: 0. Every figure must trace to real data |
| Heuristic algorithms used as the only solution method | Solver authenticity gate: logs must show real solver output; greedy alone is a FAIL |

---

## What's in the box

```
mcm-math-modeling/
├── SKILL.md                    entry point — the whole workflow and every hard rule
├── install.sh / install.bat    one-command install into any agent's skills directory
├── requirements.txt            numpy, matplotlib, scipy (optional — see Install)
├── icon.png / _icon.png        512×512 marketplace icon
├── references/  (29 files)     stage guides + domain knowledge, read on demand
├── scripts/     (8 files)      checkpoint enforcement, solvers, plotting, format check
└── assets/templates/ (382)     34 contest templates × Typst + LaTeX
```

### references/ — the knowledge base

| File | What it holds |
| --- | --- |
| `stage-2-analysis-modeling.md` | Deep question reading, problem typing, constraint tracing, variable inventory, analytic-solubility check |
| `stage-3-coding-visual.md` | Solver authenticity, computation-volume minimums, figure diversity rules, debugging discipline |
| `stage-4-drawio.md` | Non-data diagrams: roadmap, algorithm flow, model structure |
| `stage-5-writing.md` | Paper density standards, per-problem closed loop, template families, engine commands |
| `stage-6-verity.md` | Acceptance checks including PDF visual inspection |
| `aux-decision-gate.md` | How to present options and wait for the user to choose |
| `aux-model-comparison.md` | ≥3 candidate methods compared on 4 axes |
| `aux-deep-sensitivity.md` | Sobol/Morris, phase-transition boundaries, constraint sensitivity |
| `aux-lit-evidence.md` | Finding ≥3 real papers supporting the method choice |
| `aux-abstract-polish.md` | Multi-version abstract scoring and merging |
| `aux-brainstorming.md` | Ideation to break template-matching reflexes |
| `math_modeling_norms.md` | Domain norms, problem-type pitfall tables, selection decision trees |
| `excellent_paper_template.md` | Award-paper structure template |
| `innovations.md` | Innovation dimensions and cross-domain method transfer |
| `mcm-format-rules.md` | **COMAP hard rules, AI-use disclosure, page budget** (authoritative) |
| `judging-criteria.md`, `o-papers-catalog.md`, `excellence-patterns.md` | MCM/ICM judging dimensions and O/F award paper benchmarks |
| `paper-writing.md`, `abstract-polish.md`, `chart-selection.md`, `figure-cookbook.md`, `flowchart-framework.md`, `sensitivity-advanced.md`, `nature-figures.md`, `literature-evidence.md` | Paper writing, figures, diagrams, sensitivity, NPG styling |
| `journal-specs.md`, `modeling-competition.md`, `pitfalls.md` | Journal figure standards and audit |

### scripts/ — the enforcers

| Script | Purpose | Deps |
| --- | --- | --- |
| `verify_checkpoint.py` | **CP1/CP2/CP3 gates.** Exit code decides, not judgment. | stdlib |
| `solver_templates.py` | `GA`, `PSO`, `SA`, `bisection_search`, `adaptive_grid_search` | numpy, scipy |
| `writing_check.sh` | Text quality gate on the manuscript | bash, grep |
| `check_mcm_format.py` | MCM page count, margins, fonts, AI disclosure, anonymity | stdlib |
| `nature_plot.py` | Nature/NPG-styled matplotlib figures, vector PDF + 300dpi PNG | numpy, matplotlib |
| `flowchart.py` | Flow and framework diagram helpers | numpy, matplotlib |
| `journal_fig.py` | Journal figure spec audit (column width, min font, DPI, embedded fonts, colorblind-safe) | matplotlib |

### assets/templates/ — 34 competition templates

Chinese contests (14, each in Typst **and** LaTeX):
`apmcm` `changsanjiao` `cumcm` `default` `diangongbei` `dongsansheng` `huashubei` `huaweibei`
`huazhongbei` `mathorcup` `mcm` `shuweibei` `stats` `wuyibei`

English contests (3, each in Typst **and** LaTeX): `apmcm` `default` `mcm`

Each template contains `main.typ` / `main.tex`, `references.*`, and `sections/` with the
standard chapter files.

---

## How it runs

```
Stage 0  Entry        → plan.md, todo.md, engine/contest/language choices
   ↓
Stage 1  Modeling     → ANALYSIS_MODELING_REPORT.md
         (deep reading → typing → constraint matrix → variable inventory → analytic check)
         🚦 decision gate 1: the user picks the model
   ↓
Stage 2  Solving      → code/, results/, figures/, RESULTS_REPORT.md
         (solver authenticity → solve → validate → ≥2 figures per sub-problem)
         🚦 decision gate 2: the user picks figures
   ↓
Stage 3  Diagrams     → figures/*.drawio + *.pdf, DRAWIO_REPORT.md
   ↓
Stage 4  Writing      → paper/ (OUTLINE.md → sections → compile)
         🚦 decision gate 3: the user picks the narrative focus
   ↓
Stage 5  Verification → VERIFY_REPORT.md
```

### The three gates are not optional

```bash
python scripts/verify_checkpoint.py cp1 <project_dir>   # after modeling
python scripts/verify_checkpoint.py cp2 <project_dir>   # after solving
python scripts/verify_checkpoint.py cp3 <project_dir>   # after writing
```

A non-zero exit blocks the next stage. Self-declared ✅ does not substitute.

**CP1** — statement completeness, sub-problem coverage, assumption traceability, variable
definitions, objective function, constraint matrix (every row ✅), ≥3 candidate methods per
sub-problem, data understanding, code interface list.

**CP2** — code runs clean, solver output present in logs, every constraint back-substituted
against the CP1 matrix, computation volume met, numbers match the results report, figure count
met (optimization ≥15 / prediction ≥12 / evaluation ≥12), every figure traceable, random seed
fixed, sensitivity at standard.

**CP3** — section completeness, body ≥18 pages, figure counts met, ≥3 structure diagrams, every
figure really embedded, every number traceable, compilation clean, page limits respected, no
internal filename or AI-disclosure leakage, references real.

---

## Usage (English summary)

This package supports two equivalent modes. See 「这是什么」 above for the full Chinese
version — this section is the condensed English view.

**Mode A — install into an agent.** Copy the `mcm-math-modeling/` folder into the agent's
skills directory (`~/.claude/skills/`, `~/.workbuddy/skills/`, `~/.cursor/skills/`,
`~/.codex/skills/`, …) or run `./install.sh` / `install.bat`, which auto-detects them.
After that, just ask in plain language:

> "Here's the 2025 MCM Problem C statement and attachments — run the full contest workflow"

The agent loads `SKILL.md`, asks for engine / contest / language / sub-problem count,
then runs the stages, pausing at each decision gate for your input. The `description`
field carries the trigger vocabulary (math modeling · 数模 · 建模 · MCM · ICM · COMAP ·
CUMCM · 国赛 · 美赛 · 杯赛), so the skill loads without being named.

**Mode B — use it as a working guide.** Read `SKILL.md` and the relevant
`references/stage-*.md` and follow them yourself, or with your team. The checkpoint
script is available in both modes and enforces the same rules:

```bash
python scripts/verify_checkpoint.py cp1|cp2|cp3 ./your-project-dir
```

A non-zero exit means the stage is not done. The script only needs the Python standard
library — installing numpy/matplotlib/scipy is optional and required solely for the
plotting and solver-template scripts.

**Independent of any particular agent or model.** Anything that can read Markdown and
run shell commands can run this package; so can a person.

---

## Notes and boundaries

- **The gates stay in force on every agent.** If the agent lacks a user-interaction tool, the
  decision gate becomes "ask in plain text and wait" — never "decide silently."
- **If the agent has no vision**, Stage 5 states "visual check not executed" in the report and
  still completes PDF non-empty, page-count, and page-dimension checks.
- **Without shell access**, checkpoint gates cannot run mechanically — report each check's
  result explicitly and treat unverifiable items as warnings.
- **Chinese LaTeX templates default to `fontset=mac`** so they work out of the box on macOS.
  On Windows change `fontset=mac` → `fontset=windows` for SimSun/SimHei/KaiTi.
- **The checkpoints are structural checks** (counts, traceability, consistency). They cannot
  judge whether a model is scientifically sensible — that still requires the magnitude and
  cross-method validation described in Stage 2.

---

## License

MIT
