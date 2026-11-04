# Agensi 上架清单 — mcm-math-modeling

提交入口：https://www.agensi.io/dashboard/submit

> **自用说明**：这份清单是给"上架到 Agensi 市场"用的。
> 如果只是想自己用（装进智能体，或当行动指南读），**不用管下面的表单**——
> 见本包 `README.md` 的「用法 A：装进智能体」和「用法 B：当行动指南读」两节。
> 一句话版本：进目录跑 `./install.sh`（Windows 跑 `install.bat`）即可。

---

## 一、提交表单字段（照抄即可）

| 表单字段 | 填写内容 |
| --- | --- |
| **Skill 文件** | 上传 `mcm-math-modeling.zip`（见下方"打包"） |
| **名称 / Name** | `MCM Math Modeling Competition Workflow` |
| **slug** | `mcm-math-modeling`（须与 zip 内文件夹名、SKILL.md 的 `name:` 三者一致） |
| **定价 / Price** | 建议 **$39**（见下方"定价建议"） |
| **分类 / Category** | 选最接近的：Writing & Content / Research & Analysis / Education & Learning |
| **标签 / Tags** | `math-modeling`, `mcm`, `icm`, `cumcm`, `mathematical-modeling`, `data-analysis`, `scientific-writing`, `python`, `latex`, `typst`, `academic` |
| **图标 / Icon** | 见下方"图标" |
| **Listing 描述** | 复制下方"Listing 描述"整段 |
| **版本 / Version** | `1.0.0`（与 SKILL.md frontmatter 一致） |

**账号准备：** 注册 agensi.io → Dashboard → Settings 开启 Creator Mode。
付费上架需先配收款：Creator Studio → Payouts（Stripe Connect，或 Stripe 不可用时用 Zoneless 走 USDC）。免费上架不需要收款配置。

---

## 二、Listing 描述（复制这一段）

```
A checkpoint-enforced mathematical modeling competition workflow — from problem statement to a submission-ready paper, for MCM/ICM (COMAP), CUMCM, and the regional Chinese contests (Huawei Cup, Huazhong Cup, Wuyi Cup, Mathorcup).

Most "AI solves your modeling contest" tools generate a plausible-looking paper. That is exactly what judges are trained to detect, and it is why templated solutions now get downgraded. This skill takes the opposite approach: it forces the hard parts to be done properly, and uses an executable script — not good intentions — as the enforcer.

Every rule traces to a real contest failure:
• A team miscounted the sub-problems (2024) → statement completeness check; the count must match the statement or the pipeline is blocked
• An optimization variable was silently fixed at 0.5, inflating a result 10x (2022) → optimization variable inventory; every "XX∈[A,B]" must be listed
• A statistics problem solved as a physics problem, scored 39 (2025) → mandatory statistics checklist (normality tests, R² floor, VIF, cross-validation)
• Over 90% of papers missed a constraint and produced infeasible solutions (2024) → constraint traceability matrix, every constraint → formula → code interface, all must be ✅
• A 10-page, 6-figure paper downgraded (2024) → density floor: ≥18 body pages, ≥12 data figures, ≥3 structure diagrams, ≥800 words per section
• 10 filler sin/copy figures triggered an automatic downgrade (2022) → filler figures: 0; every figure must trace to real data
• Greuristic algorithms used as the only solution method → solver authenticity gate; logs must show real solver output

WHAT'S INCLUDED
• SKILL.md — the whole workflow: 6 stages, every hard rule, every gate
• references/ (29 files) — stage guides plus the domain knowledge: modeling norms, problem-type pitfall tables, selection decision trees, award-paper structure, innovation dimensions, COMAP rules and AI-use disclosure, MCM judging criteria, O/F award paper benchmarks, paper-writing and figure guidance
• scripts/ (8 files) — verify_checkpoint.py (the CP1/CP2/CP3 gate, stdlib only), solver_templates.py (GA/PSO/SA/bisection/grid search), writing_check.sh, check_mcm_format.py, nature_plot.py, flowchart.py, journal_fig.py, make_icon.py (regenerates icon.png)
• assets/templates/ (382 files) — 34 competition templates (CUMCM, Huawei Cup, Huazhong Cup, Wuyi Cup, Mathorcup, MCM, ICM, APIMCM and more) in both Typst and LaTeX

HOW IT RUNS
Stage 0 Entry → Stage 1 Modeling (deep reading → problem typing → constraint matrix → variable inventory → analytic-solubility check) → Stage 2 Solving (solver authenticity → solve → validate → ≥2 figures per sub-problem) → Stage 3 Diagrams → Stage 4 Writing (outline → sections → compile) → Stage 5 Verification (including PDF visual inspection).

Three mechanical gates block progress: a non-zero exit from verify_checkpoint.py halts the pipeline. Self-declared ✅ does not substitute. The agent must also pause for your choice at three decision gates (model selection, figure selection, narrative focus) — it will not pick your model for you.

WHAT MAKES IT DIFFERENT
The checkpoints are executable, not aspirational. They check what actually loses contests: sub-problem counts, unsolved constraints, missing decision variables, greedy-as-only-solver, figure counts, and numerical traceability from every number in the paper back to the results file.

BUILT FOR ANY AGENT
Written to the open SKILL.md standard — runs on Claude Code, Cursor, Codex CLI, OpenCode, Copilot, and 20+ others. Where an agent lacks a capability (user interaction, vision, shell), the skill degrades honestly and explicitly rather than silently skipping the gate.
```

---

## 三、定价建议

Agensi 官方指引：**$5-15** 适合单一功能小工具，**$20-50** 适合"编码深度领域 expertise 或替代大量人工流程"的 skill。

这套东西属于后者 —— 它替代的是整个建模赛流程里最容易翻车、最耗时的部分。建议：

| 策略 | 价格 | 说明 |
| --- | --- | --- |
| **推荐** | **$39** | 深度领域知识 + 可执行质量门 + 34 套模板库，符合 $20-50 区间 |
| 稳妥起步 | $29 | 更容易转化，但显得低估内容 |
| 免费引流 | $0 | 不建议——内容体量摆在这，容易被白嫖；免费版可只放 SKILL.md + 3-5 个核心 references |

**分拆上架也可以**：把 `mcm-math-modeling`（主流程，$39）和「论文模板库单独一份」（$15）拆成两个 listing，模板库那部分几乎零成本、纯文件。

---

## 四、图标

Agensi 的图标是**正方形图片**（市场首页展示为 80×80，实际建议上传 512×512 PNG）。

**✅ 已生成：`icon.png`（512×512 PNG，15 KB）**，直接上传这个文件。

设计：深色底 `#11151C` + 白色 `f(x) = max` 主体 + 三色节点（子问题拆解）
+ 底部约束括号（三段约束追溯），配色取自本包 `nature_plot.py` 的 NPG_COLORS，
与包内绘图风格统一。

想改配色或换符号，重新生成：

```bash
python scripts/make_icon.py
```

脚本可直接改 `DARK_BG` / `FG` / 主体表达式，或调整节点与括号位置。

> **别用截图** —— 数学符号比界面截图在列表里更抓眼。

---

## 五、打包

**zip 结构要求（Agensi）：** 根目录必须是一个 skill 文件夹，文件夹里放 `SKILL.md` + 支撑文件。不要把 SKILL.md 直接放在 zip 根。

正确结构：

```
mcm-math-modeling.zip
└── mcm-math-modeling/          ← 文件夹名 = SKILL.md 的 name
    ├── SKILL.md                 ← 必须在
    ├── README.md
    ├── requirements.txt
    ├── references/
    ├── scripts/
    └── assets/
```

打包命令（在包目录下执行，**不要**把外层目录也压进去）：

```bash
cd agensi-mcm-skill
zip -r mcm-math-modeling.zip mcm-math-modeling -x "*.pyc" -x "*__pycache__*"
```

上传前自检：

```bash
unzip -l mcm-math-modeling.zip | head -20
# 确认第一层是 mcm-math-modeling/ 而不是散文件
```

---

## 六、提交后

- **安全扫描**：自动 8 点扫描（文件结构 / 文件类型 / 危险命令 / 密钥 / 环境变量采集 / 网络访问 / 混淆 / prompt 注入）。本包已自检通过。
- **人工审核**：通过扫描后进入人工审核，官方称多数干净的提交 24-48 小时内通过。
- **收益**：创作者保留 **70%**，平台收 30% 单次费率，无上架费、无最低门槛。

---

## 七、审核常见退回原因（自查）

- [ ] `SKILL.md` 的 `name:` 与文件夹名、与 slug 三者完全一致（全小写、连字符分隔）
- [ ] `description` 含明确触发词（agensi 官方建议 3-5 个触发短语）
- [ ] 无任何硬编码密钥
- [ ] 无 `rm -rf` / `sudo` / `curl | sh` 等危险命令
- [ ] 至少有一个支撑文件（本包有 427 个）
- [ ] zip 结构正确，SKILL.md 在文件夹根
- [ ] 引用文件全部真实存在（本包已全量扫描，0 断链）
- [ ] 脚本能实际运行（本包已实测 CP1 正反双向）
