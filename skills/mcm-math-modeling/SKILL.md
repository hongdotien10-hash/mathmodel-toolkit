---
name: mcm-math-modeling
description: Runs an end-to-end mathematical modeling competition workflow (MCM/ICM, CUMCM, and regional Chinese contests) from problem statement to a submission-ready paper, enforced by executable quality checkpoints. Use when the user mentions math modeling, 数模, 建模, MCM, ICM, COMAP, CUMCM, 国赛, 美赛, or asks to analyze a competition problem, select a model, solve it, generate figures, or write and check a contest paper.
when_to_use: |
  - User mentions math modeling, 数模, 建模, MCM, ICM, COMAP, CUMCM, 国赛, 美赛, 杯赛
  - User provides a competition problem statement (PDF/DOCX/TXT) plus data attachments
  - User asks to analyze a modeling problem, choose a model, solve it, or produce figures
  - User asks to write, structure, or check a competition paper (English for MCM/ICM)
  - User asks for model selection comparison, sensitivity analysis, or O/F-award benchmarking
  - Do NOT use for: general data analysis without a competition framing, or pure software debugging
argument-hint: Path to the problem statement folder or competition problem file
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch
version: 1.0.0
---

# Mathematical Modeling Competition Workflow

A complete, checkpoint-enforced pipeline from a competition problem statement to a
submission-ready paper. Every stage has hard gates that must pass before the next one starts.

**This skill's core premise:** in modeling contests, the score is decided by *model selection*,
*constraint completeness*, and *argument quality* — not by whether the code runs. So this
workflow spends most of its enforcement on those three, and treats computation as a means.

The hard rules below are derived from real contest failures (documented in
`references/math_modeling_norms.md`): a 2024 CUMCM problem where a team miscounted the
sub-problems; a 2022 problem where an optimization variable was silently fixed at 0.5,
inflating a result 10x; a 2025 problem where a statistics problem was solved as a physics
problem; a 2024 problem that produced a 10-page, 6-figure paper and was downgraded.

---

## What this package is

A **skill package** — a complete methodology for running a modeling contest: how to read
the statement, split sub-problems, choose a model, trace every constraint into a formula
and a code interface, write the paper, and accept the result.

Packaging it as a skill exists so the methodology can be **reused** rather than re-explained
every time. It has two equivalent modes, and both are first-class:

- **Installed in an agent** — the agent reads this file and drives the workflow.
- **Used as a working guide** — a person (or a team) reads this file and the stage guides
  and follows them, running the checkpoint scripts to self-verify.

The gates hold in both modes. That is the point of the package.

This package is **not tied to any particular agent or model**. Anything that can read
Markdown and run shell commands can use it — and so can a person.

## Package layout

```
mcm-math-modeling/
├── SKILL.md              ← this file (entry point, all workflow rules)
├── install.sh / install.bat   ← one-command install into any agent's skills directory
├── icon.png / _icon.png  ← 512×512 marketplace icon
├── references/           ← stage guides + domain knowledge (read on demand)
│   ├── stage-2-analysis-modeling.md    modeling design & constraint tracing
│   ├── stage-3-coding-visual.md        solver authenticity & figure standards
│   ├── stage-4-drawio.md               non-data figures (flow/architecture diagrams)
│   ├── stage-5-writing.md              paper writing & density standards
│   ├── stage-6-verity.md               final acceptance checks
│   ├── aux-*.md                        decision gate, model comparison, sensitivity,
│   │                                   literature evidence, abstract polish, ideation
│   ├── math_modeling_norms.md          domain norms + pitfall checklist
│   ├── excellent_paper_template.md     award-paper structure template
│   ├── innovations.md                  innovation-point design reference
│   ├── mcm-format-rules.md             COMAP rules, AI-use disclosure, page budget
│   ├── judging-criteria.md             MCM/ICM judging dimensions
│   ├── o-papers-catalog.md             O/F award paper catalog
│   ├── excellence-patterns.md         patterns found in winning papers
│   ├── paper-writing.md, abstract-polish.md, chart-selection.md, ...
│   └── journal-specs.md, pitfalls.md, figure-cookbook.md, ...
├── scripts/              ← executable helpers
│   ├── verify_checkpoint.py            ★ CP1/CP2/CP3 enforcement (stdlib only)
│   ├── solver_templates.py             GA/PSO/SA/bisection/grid search (numpy, scipy)
│   ├── writing_check.sh                text quality gate (bash + grep)
│   ├── nature_plot.py                  Nature-style matplotlib templates (numpy, matplotlib)
│   ├── flowchart.py                    flow/framework diagram helpers (numpy, matplotlib)
│   ├── check_mcm_format.py             MCM page/format compliance checker (stdlib only)
│   └── journal_fig.py                  journal figure spec audit (matplotlib)
└── assets/templates/     ← 34 competition templates (Typst + LaTeX)
    ├── zh/<contest>/{main.typ, main.tex, references, sections/}
    └── en/<contest>/{main.typ, main.tex, references, sections/}
```

**Locate the package root first.** Paths below are written relative to the skill folder.
Find it with:

```bash
SKILL_DIR="$(dirname "$(find ~ -path '*mcm-math-modeling/SKILL.md' 2>/dev/null | head -1)")"
```

Then always reference scripts as `"$SKILL_DIR/scripts/..."` — never hardcode a path.

---

## Stage 0 — Entry and preferences

**Do this before reading the problem.**

1. **Read the core rule files** (non-negotiable):
   - `references/stage-2-analysis-modeling.md` — Step 0A deep question reading, Step 0B problem typing
   - `references/stage-5-writing.md` — paper density standards
   Confirm both were read.

2. **Verify the checkpoint script is runnable**:
   ```bash
   python "$SKILL_DIR/scripts/verify_checkpoint.py" --help
   ```
   Confirm: "CP script ready".

3. **Ask the user** (only these four — they materially change everything downstream):
   - **Typesetting engine**: Typst or LaTeX? (LaTeX uses `xelatex`, run twice; Typst uses `typst`)
   - **Contest**: MCM/ICM, CUMCM, Huawei Cup, Huazhong Cup, Wuyi Cup, Mathorcup, ...?
   - **Paper language**: English (mandatory for MCM/ICM per COMAP) or Chinese (default for others)
   - **Number of sub-problems**: known, or to be determined from the statement

4. **Write `plan.md`** (workflow + preferences + risk control) and **`todo.md`** (staged checklist)
   in the working directory.

5. **Declare the flow to the user** so they know the pacing:
   deep reading → problem typing → per-problem model discussion → per-problem figure proposal →
   per-problem solve+verify → per-problem pause → cross-check → paper writing → CP3.

> **Time is not a constraint.** When the user asks for contest-grade output, code may run for
> hours and the paper may run thousands of words. Do not shortcut. The shortcuts that
> produce failures are known and specific: greedy instead of MILP, synthetic instead of real
> data, filler figures instead of real ones.

---

## Stage 1 — Problem analysis and modeling design

Full detail: `references/stage-2-analysis-modeling.md`. Produce
`reports/ANALYSIS_MODELING_REPORT.md`.

### Step 0 — Statement completeness check (do this first)

Missing a sub-problem costs 15-20 points. Non-negotiable.

1. Read **every page** of the problem statement. If it is K pages, all K must be extracted.
2. If text extraction is garbled, cross-verify key passages with **at least two different
   tools** (e.g. `pdftotext` + `pypdfium2`/`pymupdf`).
3. List every numbered sub-problem verbatim ("Problem 1", "问题一", ...), including
   sub-items like (1)(2).
4. **Hard rule:** the sub-problem count declared in the report must match the statement
   exactly. Mismatch → CP1 fails, do not proceed.

### Step 0A — Ideation before deep reading

Read `references/aux-brainstorming.md` and generate 2-3 non-template research angles or
innovation directions for this specific problem. You are not obliged to adopt them — the point
is to break the habit of "see optimization → fire up GA". Record the output in `DECISIONS.md`.

### Step 0A-2 — Deep question reading (reject template matching)

**Do not apply a standard method reflexively.** Recent contests actively penalize
AI-templated solutions — every problem has its own traps.

Answer these three in the report before any modeling:

1. **What makes this problem distinctive?**
   - How does it differ in substance from textbook problems or past contests?
   - Which condition/parameter/constraint is most easily overlooked but actually decisive?
   - If you applied a ready-made standard method, what would you miss?

2. **What traps did the setter likely plant?**
   - Which parameter definition is easy to misread (coordinate direction, percentage vs.
     proportion, interval vs. point value)?
   - Which constraint is implicit and easy to skip as "obviously true"?
   - Which sub-problem looks simple but is easiest to get wrong?

3. **What is the physical/domain intuition?**
   - In plain language, no formulas: what is moving? What is constrained? What magnitude
     should the answer have?
   - Extreme-case test: as a key parameter approaches 0 or infinity, what should the system do?
     This becomes a validation baseline for the solver later.

**Do not enter modeling until these three are answered.**

### Step 0B — Problem typing (activates pitfall warnings)

Typing exists to switch on known traps, not to pick a canned method. Read the table in
`references/math_modeling_norms.md` and activate the matching checklists:

| Type | Activated checks |
| --- | --- |
| Optimization | constraint traceability matrix, solver log, sensitivity |
| Statistics / data analysis | normality test, no manual binning, SMOTE for imbalance |
| Mechanics / dynamics | energy conservation, dimensional consistency, degenerate-case validation |
| Geometry | case analysis (≥4 cases), degenerate configurations |
| Forecasting / time series | ADF test, TimeSeriesSplit |
| Evaluation / decision | indicator direction, weights sum to 1, CR < 0.1 |
| Graph / network | directed vs. undirected declaration, negative-weight detection |
| Queueing / stochastic | ρ < 1, distribution fitting, fixed seed |

The report must contain a `题型分类` section. Missing → CP1 fails.

### Step 1 — Sub-problem decomposition

Only top-level numbered items count as sub-problems. Background text, data descriptions, and
submission requirements are not sub-problems.

The report must contain, verbatim:

```
本赛题共 X 个子问题。
```

For each sub-problem specify: input data and known conditions; decision variables or
prediction targets; objective function or evaluation metric; constraints; dependencies on
other sub-problems; which figures/tables to produce.

### Step 1A — Constraint traceability matrix (the single most valuable artifact)

**A 2024 CUMCM problem: over 90% of papers failed because a constraint was missed and the
solution was infeasible.** Trace every constraint at modeling time.

Include this table in the report, one row per constraint:

```markdown
| # | 题面原文关键表述 | 约束类型 | 数学模型表达式 | 代码实现接口 | 状态 |
| --- | --- | --- | --- | --- | --- |
| C1 | 每块地每年只能种一种作物 | 地块单季 | Σ_j x_ij^t ≤ A_i | problem.py: area_constraint() | ✅ |
| C2 | 平地/梯田/山坡地只种粮食(豆类) | 作物适配 | x_ij>0 ⇒ j∈Grain∪Legume | problem.py: crop_fit_check() | ✅ |
```

**Source checklist — every one of these must appear as a row:**

1. Every "要求 / 必须 / 不能 / 只能 / 限制" in the statement body
2. Every rule in the "说明" column of each attachment
3. Implicit constraints from the data (seasons, land-type compatibility)
4. Common-sense constraints (non-negativity, integrality)
5. **Methods and geometric parameters given by the statement** — these are not options, they
   are mandatory. Substitute your own method (e.g. Bézier instead of the specified tangent
   arcs) and the problem scores zero.

Category **G** (given method) deserves its own table:

```markdown
| # | 题面原文 | 类型 | 是否必须遵守 | 违反后果 | 状态 |
| G1 | 掉头路径为两段相切圆弧 | 给定方法 | 不可替换 | 零分 | ✅ |
| G2 | 前弧半径:后弧半径=2:1 | 给定参数 | 不可修改 | 严重扣分 | ✅ |
```

**Any row marked ❌ must be resolved before Stage 2.** CP1 checks this row by row.

### Step 1C — Optimization variable inventory

**2022 lesson:** the power exponent α∈[0,1] in Q2(2) was a decision variable, but only the
damping coefficient was listed, so α was fixed at 0.5 and Pmax came out 10x too high.

For every optimization sub-problem, list **all** decision variables:

```markdown
| # | 所属问题 | 变量名 | 类型 | 取值范围 | 来源 | 状态 |
| V1 | Q2(1) | 阻尼系数c | 连续 | [0, 100000] | 题面 | ✅ |
| V2 | Q2(2) | 幂指数α | 连续 | [0, 1] | 题面 | ✅ |
```

Every "XX在[A,B]内取值" in the statement = one decision variable. A count mismatch with the
statement's declared optimization parameters → CP1 fails.

### Step 1D — Closed-form feasibility check

**The line between a national first prize and an ordinary paper.** For each sub-problem:

```markdown
| 子问题 | 系统类型 | 可解析？ | 若可解析：方法 | 若不可：原因 |
| Q1 | 线性ODE(简谐激励) | 是 | 拉普拉斯变换/特征值法 | — |
| Q3 | 非线性ODE | 否 | — | 非线性阻尼无闭式解 |
```

- Linear systems (constant-coefficient ODE, harmonic forcing, regular geometry) →
  **derive the analytic solution first**; numerics only validate it.
- Nonlinear systems → at minimum give analytic limiting analysis for degenerate cases
  (damping → 0, damping → ∞).
- No analytic derivation anywhere → CP1 warning (reviewers deduct).

### Step 1E — Statistics/data-analysis specific checks

**2025 lesson:** a statistics problem was solved as a physics problem — load data, run
regression, report numbers. Scored 39 and eliminated. When the problem involves correlation,
regression, hypothesis testing, or classification, the report must contain:

```markdown
## 统计题规范检查
### 1. 数据探索
- [ ] 描述性统计（均值/标准差/中位数/四分位数/缺失率）
- [ ] 正态性检验（Shapiro-Wilk n≤50；K-S n>50）→ 据此选 Pearson / Spearman
- [ ] 异常值检测（IQR / 3σ）
### 2. 建模策略
- [ ] OLS 已尝试 → R² = ___
- [ ] 若 R²<0.3: 至少再试一种非线性方法（GAM/LME/多项式/对数变换）
- [ ] 多变量: 变量筛选（LASSO/逐步回归/VIF 共线性诊断）
- [ ] 分组问题: 必须数据驱动（K-means/层次/DBSCAN），禁止手工等距分组
### 3. 模型诊断
- [ ] 残差分析（正态性/方差齐性/独立性）
- [ ] 共线性诊断（VIF）
- [ ] 交叉验证（≥5折）
```

Missing this section → CP1 fails (statistics problems only).

### Step 1F — Literature evidence (recommended)

After modeling, before coding, run `references/aux-lit-evidence.md` to find ≥3 real papers
supporting the core method choice. Not ceremonial — a genuine case where this method was
applied to a similar problem. If none found, honestly record "no direct literature found" and
argue from logic instead. Output to `LITERATURE_EVIDENCE.md`.

### Steps 2-5 — Assumptions, data, model report

Read `references/stage-2-analysis-modeling.md` for the assumption-sensitivity pre-check,
data-understanding pass, and the required model-report structure (variables, assumptions,
objective, constraints, solution method, I/O, code notes, validation plan).

The report must end with a **code implementation task list**:

```markdown
| 任务 | 输入 | 输出 | 方法 | 校验 |
```

### 🚦 Decision gate 1 — model selection (never decide alone)

**Do not pick the model unilaterally.**

1. Run `references/aux-model-comparison.md` → `MODEL_SELECTION_REPORT.md` (≥3 candidate
   methods per sub-problem, compared on accuracy / complexity / interpretability / data needs).
2. Run the decision gate (`references/aux-decision-gate.md`) and present to the user:
   - candidate methods per sub-problem with a recommendation rating (⭐⭐⭐/⭐⭐/⭐)
   - innovation-level options (solid / locally innovative / fully innovative)
   - anything you genuinely cannot decide, with why
3. **Wait for confirmation**, then write the choices into `DECISIONS.md`.
   Only then may Stage 2 begin.

CP1 checks that `DECISIONS.md` records a model selection.

---

## Stage 2 — Implementation, solving, and data figures

Full detail: `references/stage-3-coding-visual.md`. Produce `code/`, `results/`, `figures/`,
and `reports/RESULTS_REPORT.md`.

### Solver authenticity (hard requirement)

Pretending to solve is worse than failing to solve. Every sub-problem must show genuine
solver output.

| Problem type | Required method | Proof of real solving |
| --- | --- | --- |
| Optimization | PuLP/CBC, Gurobi, CPLEX, OR-Tools, SciPy.optimize, cvxpy | Log shows Optimal/Feasible/Iteration/Node/Branch/Gap |
| Prediction / classification | sklearn/statsmodels/pytorch fit+predict | Log shows train/val split, model params, eval metrics |
| Simulation / mechanics | scipy.integrate or simulation framework | Log shows step size / iteration / convergence |
| Heuristic | May generate initial solutions or serve as comparison | **Never the only method**; compare against exact solver, report gap |

**Forbidden:**

- Sobol sensitivity where each evaluation is a formula substitution — each evaluation must
  re-solve the model.
- Finding a critical value (collision moment, minimum clearance, maximum speed) by trying a
  few hand-picked parameters — use bisection / golden section / Newton and report convergence
  tolerance.

Import the provided solvers instead of writing your own:

```python
import sys
sys.path.insert(0, r"<SKILL_DIR>/scripts")
from solver_templates import GA, PSO, SA, bisection_search, adaptive_grid_search
```

### Debugging discipline

When code fails or results look wrong, use a structured debugging approach — categorize the
error, find the root cause, apply a targeted fix. Do not blindly edit parameters in a loop;
it wastes time and often fixes the wrong thing. (A 2025 problem burned 6 rounds of blind
parameter edits before the real bug surfaced.)

### Figure minimums (hard requirement)

| Problem type | Minimum data figures | Per sub-problem | Typical total (incl. diagrams) |
| --- | --- | --- | --- |
| Optimization | ≥ 15 | ≥ 2 | 18-22 |
| Prediction | ≥ 12 | ≥ 2 | 15-18 |
| Evaluation | ≥ 12 | ≥ 2 | 15-18 |
| Mechanics/dynamics | ≥ 15 | ≥ 2 | 18-22 |
| Statistics/data analysis | ≥ 12 | ≥ 2 | 15-18 |
| Mixed | ≥ 15 | ≥ 2 | 18-22 |

**Per sub-problem, before solving it, propose at least 2 figure types with their argument
purpose and let the user pick.** Two is the floor.

### Figure diversity (anti-monotony)

Every paper must cover three dimensions — missing any one is a failure:

1. **Data type**: bar, line, scatter, heatmap, distribution/box, 3D surface, network/geo
2. **Analysis type**: comparison, trend, composition, correlation, distribution, process,
   sensitivity, error/diagnosis
3. **Purpose type**: show the result, show the method, show the robustness, show the mechanism

If the figure set contains fewer than 3 of {bar, line, scatter, heatmap, schematic}, it is
too monotonous — add more.

Also: **every figure must trace to real data**. Save intermediate data, model parameters,
iteration history, constraint checks, and run logs alongside the figures.

### Intermediate data discipline

Save the key intermediate state as data, not just as prose: cleaned-data summaries, model
parameters, iteration history, constraint checks, sensitivity outputs, and the data behind
every figure. Prefer `figures/` or `code/outputs/`, and document each file's purpose in
`reports/RESULTS_REPORT.md`.

The results report must include a **solver log summary**.

### 🚦 Decision gate 2 — figure selection

Before writing, ask the user which figures go in the main text and which go to the appendix.
Append the answer to `DECISIONS.md`.

### Recommended — deep sensitivity

`references/aux-deep-sensitivity.md`: Sobol/Morris global indices, phase-transition boundary
detection, constraint sensitivity. Output `reports/SENSITIVITY_REPORT.md`. Each evaluation must
be a full re-solve.

---

## Stage 3 — Non-data figures

Full detail: `references/stage-4-drawio.md`. Produce `figures/*.drawio`, `figures/*.pdf`, and
`reports/DRAWIO_REPORT.md`.

This stage handles **conceptual** diagrams only: technical roadmap, algorithm flow, model
structure, data-processing flow. **Do not regenerate data-driven figures here** — that is
Stage 2's job.

At least one `fig_roadmap` technical roadmap is expected in a competition paper. If any
diagram type is deliberately skipped, say why in the report. Every diagram must correspond to
a real method in the modeling report.

If `drawio` CLI is unavailable, produce the `.drawio` XML source directly and export PDF via
another route; record the failure and the export command used.

---

## Stage 4 — Paper writing

Full detail: `references/stage-5-writing.md`. Produce `paper/`.

### Before writing anything: read `references/excellent_paper_template.md`

Then write `paper/OUTLINE.md` first. Skipping the outline is a known cause of runaway drafts.

### Paper density standards (hard requirements)

**2024 lesson: a 10-page, 6-figure paper reads as thin work. Award papers run 20-25 pages with
15-22 figures. The reviewer's first impression comes from thickness and visualization density.**

| Metric | Minimum | Recommended | Note |
| --- | --- | --- | --- |
| Body pages | ≥ 18 | 20-25 | excluding appendix, including abstract. < 15 = insufficient work |
| Data figures | ≥ 12 | 15-20 | Stage 2 data-driven figures only |
| Flow/structure diagrams | ≥ 3 | 4-6 | roadmap + solve flow + model structure + data flow |
| Figure page coverage | ≥ 50% | 60-70% | MCM winners average 68% |
| Figures per core chapter | ≥ 2 | 3-4 | modeling chapters cannot be text-only |
| Appendix pages | ≥ 3 | 5-8 | full result tables + core code + supplementary analysis |
| Words per core section | **≥ 800** | 1000-1500 | 2022 lesson: 300-word sections → 7-page paper |
| Filler figures | **0** | — | 2022 lesson: 10 sin/copy figures → automatic downgrade |
| Total pages incl. appendix | ≥ 22 | 25-30 | — |

**MCM-specific:** figure coverage floor is 65%, and the Summary Sheet must be its own page.

If `figures/` has fewer than 12 data figures → **stop writing**, go back to Stage 2.

### Mandatory closed loop per sub-problem

Every sub-problem chapter must contain all five subsections:

1. **Model establishment** — why this method, with ≥1 excluded alternative and why
2. **Assumptions** — each with justification and effect if wrong
3. **Solution** — algorithm, parameters, convergence
4. **Result analysis** — **plausibility validation**: magnitude sanity check, degenerate-case
   consistency, agreement with known benchmarks
5. **Comparison with an alternative method**

### Numerical integrity

**Every number, figure, and conclusion in the paper must come from `reports/RESULTS_REPORT.md`
or the generated figures.** No fabrication, no estimation, no different rounding. This is the
single most common disqualification cause.

### Template families

Templates live in `assets/templates/`. Pick by contest and engine, then copy into `paper/`.

Chinese (14 contests, Typst + LaTeX each):

```
apmcm  changsanjiao  cumcm  default  diangongbei  dongsansheng
huashubei  huaweibei  huazhongbei  mathorcup  mcm  shuweibei  stats  wuyibei
```

English (3 contests, Typst + LaTeX each):

```
apmcm  default  mcm
```

Huawei Cup / Huazhong Cup / Wuyi Cup use the `huaweibei` / `huazhongbei` / `wuyibei` templates.

**Engine commands:**

```bash
# LaTeX — run twice for cross-references
xelatex -interaction=nonstopmode main.tex   # ×2
# Typst
typst compile main.typ
```

> **LaTeX font note:** the bundled Chinese templates default to `fontset=mac` (Songti SC /
> Heiti SC / Kaiti SC) so they work out of the box on macOS. On Windows, change
> `\documentclass[fontset=mac, ...]{ctexart}` to `fontset=windows` to use SimSun/SimHei/KaiTi.
> On Linux, install `fonts-noto-cjk` and use `fontset=none` with explicit font settings.

**Do not mix engines.** Use one engine's syntax for every file. Figures are embedded relative
to the file that references them:

```typ
#figure(image("../../figures/fig_q1.pdf", width: 85%), caption: [...])
```
```latex
\begin{figure}[H]\centering\includegraphics[width=0.85\textwidth]{../../figures/fig_q1.pdf}\caption{...}\label{fig:q1}\end{figure}
```

### Recommended — abstract polish

`references/aux-abstract-polish.md`: generate multiple versions, score against the judging
rubric, and merge the best. Output `reports/ABSTRACT_VERSIONS.md`.

For MCM/ICM, also apply `references/mcm-format-rules.md` — it is the authoritative source for
COMAP hard rules (page limits, team/control numbers), the AI-use disclosure statement, and the
page budget. Verify the final paper with:

```bash
python "$SKILL_DIR/scripts/check_mcm_format.py" <paper_dir>
```

### 🚦 Decision gate 3 — narrative focus

Ask the user which emphasis the paper should carry: methodological innovation, result depth,
or engineering completeness. Append to `DECISIONS.md`.

---

## Stage 5 — Verification and acceptance

Full detail: `references/stage-6-verity.md`. Produce `reports/VERIFY_REPORT.md`.

This stage does not re-model and does not rewrite the paper. It finds hard errors, fixes
directly fixable ones, and reports what remains.

### Step 1 — Text quality gate

```bash
bash "$SKILL_DIR/scripts/writing_check.sh" <paper_dir>
```

`FAIL` here is a hard error. Fix and rerun.

### Steps 2-8

Follow `references/stage-6-verity.md`: section count and heading order; figure/section
matching and image path existence; writing quality and leak detection (internal filenames,
temp paths, residual AI disclaimers); numerical consistency with the results record;
citations and template compliance; compilation; and **PDF visual inspection** — export every
page to PNG and look at it. This catches layout errors that neither text scanning nor the
compiler can see. If the agent has no visual capability, state that explicitly in the report
and still complete all programmatic checks (PDF non-empty, page count, page dimensions).

Do not generate `*_typst_includes.typ` or `*_latex_includes.tex`; figures must be embedded
directly in their sections.

---

## Checkpoints (enforced)

Run the checkpoint script after each stage. A non-zero exit blocks the next stage — no
self-declared ✅ substitutes.

```bash
python "$SKILL_DIR/scripts/verify_checkpoint.py" cp1 <project_dir>   # after modeling
python "$SKILL_DIR/scripts/verify_checkpoint.py" cp2 <project_dir>   # after solving
python "$SKILL_DIR/scripts/verify_checkpoint.py" cp3 <project_dir>   # after writing
```

**CP1 — modeling analysis**

| Check | Standard |
| --- | --- |
| Statement completeness | every page read; sub-problem count matches the statement |
| Sub-problem coverage | every numbered sub-problem has a modeling plan |
| Assumption traceability | each key assumption has rationale, scope, alternative reading |
| Variable definitions | all symbols present with dimensions |
| Objective function | min/max, variable types, bounds stated |
| Constraint traceability matrix | every constraint → formula → code interface, all ✅ |
| Method selection | ≥3 candidate methods compared per sub-problem |
| Data understanding | attachment size/fields/missing values documented |
| Code interface | task list with constraint annotations |

Sub-problem count mismatch, or any ❌ in the constraint matrix → **CP1 FAIL**.

**CP2 — solving**

| Check | Standard |
| --- | --- |
| Code runs | all .py files run clean from scratch |
| Solver authenticity | solver output present in logs; greedy alone is a FAIL |
| Constraints satisfied | optimal solution back-substituted, row-by-row against the CP1 matrix |
| Computation volume | meets the Stage 2 minimum; each evaluation = full re-solve |
| Numerical consistency | code output matches `RESULTS_REPORT.md` exactly |
| Figure count | optimization ≥15 / prediction ≥12 / evaluation ≥12 |
| Figure traceability | every figure traces to generating code and data source |
| Random seed | fixed; stability across reruns verified |
| Sensitivity | meets the deep-sensitivity minimum; each evaluation = full re-solve |

**CP3 — paper readiness**

| Check | Standard |
| --- | --- |
| Section completeness | all required section files exist and are non-empty |
| Body pages | ≥ 18 (excluding appendix); < 15 = FAIL |
| Data figures | optimization ≥15 / prediction ≥12 / evaluation ≥12 |
| Flow/structure diagrams | ≥ 3 |
| Figure embedding | every referenced figure has a real insertion |
| Numerical traceability | every number traces to `RESULTS_REPORT.md` |
| Compilation | self-repairing compile loop ends with 0 errors |
| Page limits | within contest limits |
| No leaks | no internal filenames, temp paths, or AI-disclosure residue |
| References | all real, uniformly formatted |

Page count or figure count failure → **CP3 FAIL**, return to the responsible stage.

Append the checkpoint results to the matching `todo.md` entries.

---

## Working directory layout

```
.
├── plan.md                       # Stage 0
├── todo.md                       # Stage 0
├── reports/
│   ├── ANALYSIS_MODELING_REPORT.md   # Stage 1
│   ├── LITERATURE_EVIDENCE.md        # Stage 1 (recommended)
│   ├── MODEL_SELECTION_REPORT.md     # Stage 1 (recommended)
│   ├── DECISIONS.md                  # decision gate, spans all stages
│   ├── RESULTS_REPORT.md             # Stage 2
│   ├── SENSITIVITY_REPORT.md         # Stage 2 (recommended)
│   ├── DRAWIO_REPORT.md              # Stage 3
│   ├── ABSTRACT_VERSIONS.md          # Stage 4 (recommended)
│   └── VERIFY_REPORT.md              # Stage 5
├── code/                         # Stage 2 — problem1.py, utils.py, ...
├── results/                      # Stage 2
├── figures/                      # Stages 2+3 — *.pdf, *.drawio
└── paper/                        # Stage 4 — main.typ|main.tex, sections/, OUTLINE.md
```

---

## Per-sub-problem loop (Stage 2 in detail)

Do not write all sub-problems at once. For each, in order:

1. **Deep question reading** for this sub-problem — what is distinctive here, what trap is buried
2. **Model discussion** — 2-3 candidates with ⭐ ratings; wait for user confirmation
3. **Figure proposal** — 3-4 candidate figures with argument purpose; user picks ≥2
4. **Solve** — after each key computation, validate:
   - magnitude sanity check (is this number in a plausible range?)
   - cross-validate with a second method or parameter set
   - **an unvalidated result must not advance to the next step. Time is not the constraint.**
5. **Result plausibility check** — independent verification: degenerate case, extreme
   parameters, domain intuition
6. **Critical review** — if this result were wrong, what is the most likely reason? List 1-2 doubts
7. **Pause and report** — core results, plausibility verdict, doubts, figures produced, and
   explicitly invite the user to challenge or request a redo. Not just "type continue".
8. **Record** — model choice, figures chosen, result confirmation → `reports/DECISIONS.md`.
   Missing entries → CP3 fails.

After all sub-problems: **cross-check consistency across the whole problem** — is the Q1→Q2
correction reasonable? Is the Q3 conclusion self-consistent with Q1/Q2 assumptions? Are
cross-method deviations acceptable? Flag and discuss inconsistencies in the paper.

> Exception: if the user says "do everything then show me" or "don't pause per question",
> skip the pause (not the model discussion or validation).

---

## Rules that override everything

1. **Never fabricate data, results, or citations.** Every number traces to a real run.
2. **Never skip a checkpoint** because it "looks close enough". Script exit code decides.
3. **Never let the agent pick the model silently** — the user chooses.
4. **Never substitute a method the statement prescribed.** (Bézier instead of tangent arcs → zero.)
5. **Never pad the paper with filler figures or invented prose.**
6. **Never report a result you have not sanity-checked.** Plausibility validation is mandatory.
7. **Never mix Typst and LaTeX syntax** in one paper.
8. **Never hardcode absolute paths** to the skill directory — resolve it at runtime.

---

## Environment requirements

| Purpose | Tool | Notes |
| --- | --- | --- |
| Typst | [typst.app](https://typst.app) | `typst compile` |
| LaTeX | TeX Live / MiKTeX | `xelatex`, run twice |
| Python | 3.10+ | see `requirements.txt` |
| Diagrams | drawio | optional CLI; otherwise emit `.drawio` XML |
| PDF inspection | `pdftoppm` / `pymupdf` | for the visual check step |

```bash
pip install -r requirements.txt    # numpy, matplotlib, scipy
```

**Script dependencies (so you can skip what you do not need):**

| Script | Needs |
| --- | --- |
| `verify_checkpoint.py` | Python stdlib only — always runnable |
| `check_mcm_format.py` | Python stdlib only |
| `writing_check.sh` | bash + grep |
| `solver_templates.py` | `numpy`, `scipy` |
| `nature_plot.py`, `flowchart.py`, `journal_fig.py` | `numpy`, `matplotlib` |

If a required tool is missing, say so explicitly and complete every programmatic check that
remains possible, recording what was skipped and why.

---

## Agent capability notes

This skill is written to run on any agent that reads the SKILL.md standard (Claude Code,
Cursor, Codex CLI, OpenCode, Copilot, and others). Some capabilities are optional and change
how smoothly each stage runs:

| Capability | If present | If absent |
| --- | --- | --- |
| **User-interaction tool** (e.g. `AskUserQuestion`) | Use it for the three decision gates and per-sub-problem figure/model confirmations | Ask in plain text and wait for a reply; never silently proceed past a gate |
| **Vision / image input** | Do the PDF page-by-page visual inspection in Stage 5 | State "visual check not executed" in `VERIFY_REPORT.md` and complete PDF non-empty, page-count, and page-dimension checks |
| **Sub-agent support** (`Agent`) | Delegate literature search and figure-catalog matching to parallel sub-agents | Do them inline |
| **Shell access** (`Bash`) | Run the checkpoint scripts, solvers, and compilers | The checkpoint gates cannot be enforced mechanically — state each check's result explicitly in the report and treat any unverifiable item as a warning |
| **Web search / fetch** | Run literature evidence (Stage 1F) and check contest rules against official sources | Record "no external literature verified" honestly; never fabricate citations |

**The gates stay in force regardless of agent.** If the interaction tool is missing, the gate
becomes "ask in text and wait" — it does not become "decide yourself."
