# mcm-math-modeling

**A complete, checkpoint-enforced mathematical modeling competition workflow — from problem
statement to submission-ready paper.**

Works for MCM/ICM (COMAP), CUMCM (国赛), and the regional Chinese contests (华为杯, 华中杯,
五一杯, Mathorcup, 数模杯, 三等杯...). Includes 34 competition paper templates, a mechanical
quality-gate script, and the domain knowledge that separates an award paper from an ordinary one.

---

## Why this exists

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
├── requirements.txt            numpy, matplotlib, scipy
├── references/  (29 files)     stage guides + domain knowledge, read on demand
├── scripts/     (7 files)      checkpoint enforcement, solvers, plotting, format check
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

## Usage

The agent reads `SKILL.md` and drives the workflow. Typical request:

> "这里是 2025 MCM Problem C 的题面和附件，帮我按竞赛流程做一遍"

The agent will ask for engine / contest / language, then run the stages, pausing at each
decision gate for your input.

### Installing manually

```bash
pip install -r requirements.txt
# place the mcm-math-modeling folder under your agent's skills directory
```

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
