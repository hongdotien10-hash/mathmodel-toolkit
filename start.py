"""
====================================================================
 MathModel Toolkit — 一键启动
====================================================================
把赛题和数据放到 problems/ 文件夹，运行 python start.py 即可
论文和图表自动输出到 output/ 文件夹
====================================================================
"""

import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from mathmodel.utils import set_seed, Timer
from mathmodel.analyzer import ProblemClassifier, ModelKnowledgeBase
from mathmodel.models import EvaluationSolver, StatsSolver, OptimizationSolver
from mathmodel.sensitivity import SensitivityAnalyzer
from mathmodel.visualization import Plotter, set_style
from mathmodel.paper.word_writer import generate_paper
import matplotlib.pyplot as plt

set_seed(42)

PROBLEMS_DIR = Path(__file__).parent / "problems"
OUTPUT_DIR = Path(__file__).parent / "output"

print("=" * 60)
print("  MathModel Toolkit — 一键求解")
print("=" * 60)
print()

# ================================================================
# 扫描题目
# ================================================================
problem_dirs = sorted([
    d for d in PROBLEMS_DIR.iterdir()
    if d.is_dir() and not d.name.startswith('.')
])

if not problem_dirs:
    print("ERROR: No problems found!")
    print(f"  Put your problem files in: {PROBLEMS_DIR}")
    print("  Example: problems/my_problem/题目.txt")
    print("           problems/my_problem/附件1.xlsx")
    sys.exit(1)

print(f"Found {len(problem_dirs)} problem(s):")
for i, d in enumerate(problem_dirs):
    files = list(d.iterdir())
    print(f"  [{i+1}] {d.name}  ({len(files)} files)")

if len(problem_dirs) == 1:
    choice = 1
else:
    try:
        choice = int(input("\nSelect problem number: ") or "1")
    except (ValueError, EOFError):
        choice = 1

selected_dir = problem_dirs[choice - 1]
problem_name = selected_dir.name
output_dir = OUTPUT_DIR / problem_name
fig_dir = output_dir / "figures"
fig_dir.mkdir(parents=True, exist_ok=True)

print(f"\n{'='*50}")
print(f"  Solving: {problem_name}")
print(f"{'='*50}\n")

# ================================================================
# 读取文件
# ================================================================
problem_text = ""
data_files = {}

for f in sorted(selected_dir.iterdir()):
    suffix = f.suffix.lower()
    if suffix == '.txt':
        problem_text = f.read_text(encoding='utf-8')
        print(f"[doc] {f.name} ({len(problem_text)} chars)")
    elif suffix in ('.xlsx', '.xls'):
        df = pd.read_excel(f)
        data_files[f.stem] = df
        print(f"[data] {f.name} {df.shape}")
    elif suffix == '.csv':
        df = pd.read_csv(f)
        data_files[f.stem] = df
        print(f"[data] {f.name} {df.shape}")

if not problem_text:
    for f in selected_dir.iterdir():
        if f.suffix == '.txt':
            problem_text = f.read_text(encoding='utf-8')
            break

if not problem_text:
    problem_text = "(No problem text found — please add a .txt file)"

print()

# ================================================================
# 题目分析 & 模型推荐
# ================================================================
print("-" * 40)
print("  PHASE 1: Problem Analysis & Model Recommendation")
print("-" * 40)

classifier = ProblemClassifier()
kb = ModelKnowledgeBase()

# 拆分子问题
lines = problem_text.split('\n')
sub_problems_raw = []
for i, line in enumerate(lines):
    line = line.strip()
    if not line:
        continue
    if '问题' in line and any(c in line for c in '123456789一二三四五六七八九'):
        ctx = line
        for j in range(i+1, min(i+5, len(lines))):
            if '问题' in lines[j] and any(c in lines[j] for c in '123456789'):
                break
            ctx += ' ' + lines[j].strip()
        sub_problems_raw.append({"id": len(sub_problems_raw)+1, "text": ctx[:500]})
        if len(sub_problems_raw) >= 5:
            break

if not sub_problems_raw:
    sub_problems_raw = [{"id": 1, "text": problem_text[:500]}]

sub_problems = []
for sp in sub_problems_raw:
    clf = classifier.classify(sp["text"])
    candidates = kb.query(problem_type=clf["type"], top_k=3)
    m = candidates[0] if candidates else {"model": "待定", "score": 0, "reason": ""}
    sub_problems.append({
        "id": sp["id"],
        "title": sp["text"][:150],
        "full_text": sp["text"],
        "type": clf["type"],
        "type_scores": clf.get("scores", {}),
        "model": m.get("model", ""),
        "score": m.get("score", 0),
        "reason": m.get("reason", ""),
    })
    print(f"  Q{sp['id']}: [{clf['type']}] -> {m.get('model','?')} "
          f"(score:{m.get('score',0):.0%})")

print()

# ================================================================
# 模型求解
# ================================================================
print("-" * 40)
print("  PHASE 2: Model Solving")
print("-" * 40)

all_results = {}

for sp in sub_problems:
    ptype = sp["type"]
    print(f"\n  >> Q{sp['id']}: {sp['model']}")

    # ---- 评价 ----
    if ptype == "评价" and data_files:
        with Timer() as t:
            evaluator = EvaluationSolver()
            # 找多列数值表
            name, df = None, None
            for k, v in data_files.items():
                if v.select_dtypes(include=np.number).shape[1] >= 3:
                    name, df = k, v
                    break
            if df is None:
                name, df = next(iter(data_files.items()))

            numeric = df.select_dtypes(include=np.number)
            matrix = numeric.values.astype(float)
            labels = df.iloc[:, 0].tolist()

            # 确定指标方向（含成本和环境的为负向）
            impacts = []
            for col in numeric.columns:
                if any(kw in str(col) for kw in ["成本", "环境", "影响", "费用", "cost"]):
                    impacts.append(-1)
                else:
                    impacts.append(1)

            # 熵权
            ew = evaluator.entropy_weight(matrix)
            # TOPSIS
            res = evaluator.topsis(matrix, weights=ew["weights"], impacts=impacts)

            all_results[f"sub_{sp['id']}"] = {
                "labels": labels,
                "scores": [round(float(s), 4) for s in res["scores"]],
                "rank": [int(r) for r in res["rank"]],
                "weights": {str(c): round(float(w), 4) for c, w in zip(numeric.columns, ew["weights"])},
                "d_plus": [round(float(d), 4) for d in res["d_plus"]],
                "d_minus": [round(float(d), 4) for d in res["d_minus"]],
            }
            best = labels[int(np.argmax(res["scores"]))]
            print(f"     Best: {best} (score: {max(res['scores']):.4f})")
            print(f"     Ranking: {' > '.join(str(labels[i]) for i in np.argsort([-s for s in res['scores']]))}")
        print(f"     Time: {t.duration}")

    # ---- 预测 ----
    elif ptype == "预测" and data_files:
        with Timer() as t:
            solver = StatsSolver()
            # 找时序型数据
            name, df = None, None
            for k, v in data_files.items():
                if v.select_dtypes(include=np.number).shape[1] <= 3 and v.shape[0] >= 4:
                    name, df = k, v
                    break
            if df is None:
                name, df = next(iter(data_files.items()))

            # 找数值列（非年份、非序号）
            data_col = None
            for col in df.columns:
                if df[col].dtype in ("int64", "float64"):
                    if any(kw in str(col).lower() for kw in ["需求", "量", "值", "demand", "产量", "销量"]):
                        data_col = col
                        break
            if data_col is None:
                for col in df.columns:
                    if df[col].dtype in ("int64", "float64") and df[col].max() > 10:
                        data_col = col
                        break

            if data_col:
                data = df[data_col].tolist()
                pred = solver.grey_forecast(data, forecast_steps=3)
                all_results[f"sub_{sp['id']}"] = {
                    "original": data,
                    "fitted": [round(v, 4) for v in pred["fitted"]],
                    "forecast": [round(v, 4) for v in pred["forecast"]],
                    "mape": round(pred["mape"], 2),
                    "grade": pred["grade"],
                    "params": pred["params"],
                }
                print(f"     MAPE: {pred['mape']:.2f}% [{pred['grade']}]")
                print(f"     Forecast: {[round(v, 1) for v in pred['forecast']]}")
        print(f"     Time: {t.duration}")

    # ---- 优化 ----
    elif ptype == "优化" and data_files:
        with Timer() as t:
            opt = OptimizationSolver()
            # 找多列数值表
            name, df = None, None
            for k, v in data_files.items():
                if v.select_dtypes(include=np.number).shape[1] >= 3:
                    name, df = k, v
                    break
            if df is None:
                name, df = next(iter(data_files.items()))

            numeric = df.select_dtypes(include=np.number)
            cols = numeric.columns.tolist()
            labels_all = df.iloc[:, 0].tolist()

            cost_col, benefit_col = None, None
            for c in cols:
                if any(kw in str(c) for kw in ["成本", "费用", "cost"]):
                    cost_col = c
                elif any(kw in str(c) for kw in ["覆盖", "人口", "收益", "效益", "benefit", "pop"]):
                    benefit_col = c
            if cost_col is None:
                cost_col = cols[1] if len(cols) > 1 else cols[0]
            if benefit_col is None:
                benefit_col = cols[2] if len(cols) > 2 else cols[1]

            costs = numeric[cost_col].tolist()
            benefits = numeric[benefit_col].tolist()

            c = [-float(b) for b in benefits]
            A_ub = [[float(x) for x in costs]]
            b_ub = [100.0]

            try:
                ip_result = opt.integer_program(
                    c=c, A_ub=A_ub, b_ub=b_ub,
                    bounds=(0, 1), binary=True,
                )
                if ip_result.success:
                    solution = [int(v > 0.5) for v in ip_result.x]
                    selected = [labels_all[i] for i, v in enumerate(solution) if v]
                    total_cost = sum(costs[i] for i, v in enumerate(solution) if v)
                    total_pop = sum(benefits[i] for i, v in enumerate(solution) if v)
                    all_results[f"sub_{sp['id']}"] = {
                        "selection": selected,
                        "total_cost": round(total_cost, 1),
                        "total_population": round(total_pop, 1),
                        "solution": solution,
                        "costs": costs,
                        "benefits": benefits,
                        "budget": 100.0,
                    }
                    print(f"     Selected: {selected}")
                    print(f"     Cost: {total_cost:.0f} / Budget: 100")
                    print(f"     Population: {total_pop:.0f}")
                else:
                    print(f"     FAILED: {ip_result.message}")
            except Exception as e:
                print(f"     ERROR: {e}")
        print(f"     Time: {t.duration}")

# ================================================================
# 灵敏度分析
# ================================================================
print()
print("-" * 40)
print("  PHASE 3: Sensitivity Analysis")
print("-" * 40)

sa = SensitivityAnalyzer()
for key, value in all_results.items():
    if "fitted" in value and len(value["fitted"]) >= 4:
        def gm_model(params):
            s = StatsSolver()
            r = s.grey_forecast(params.tolist(), forecast_steps=3)
            return float(r["forecast"][-1])

        data_arr = np.array(value["fitted"])
        robust = sa.robustness_check(gm_model, data_arr, noise_pct=0.05, n_samples=500)
        value["sensitivity"] = {
            "cv": round(robust["cv"], 4),
            "is_robust": robust["is_robust"],
            "ci_95": [round(v, 2) for v in robust.get("ci_95", [0, 0])],
        }
        print(f"  GM(1,1) robustness: CV={robust['cv']:.4f} "
              f"({'STABLE' if robust['is_robust'] else 'UNSTABLE'})")

# ================================================================
# 图表生成（PDF + PNG）
# ================================================================
print()
print("-" * 40)
print("  PHASE 4: Generating Figures")
print("-" * 40)

set_style("zh", "default")
plotter = Plotter(language="zh")
fig_count = 0

for key, value in all_results.items():
    if "scores" in value and "labels" in value:
        labels = value["labels"]
        scores = [float(s) for s in value["scores"]]
        fig, ax = plotter.bar(
            x=labels, y=scores,
            xlabel="Location", ylabel="TOPSIS Score",
            title="TOPSIS Comprehensive Evaluation Scores",
            labels=labels,
        )
        # 保存 PDF + PNG
        plotter.save(fig, fig_dir / "topsis_scores.pdf", dpi=300)
        plotter.save(fig, fig_dir / "topsis_scores.png", dpi=200)
        fig_count += 1
        print(f"  [{fig_count}] TOPSIS bar chart -> topsis_scores.pdf / .png")

    if "forecast" in value and "fitted" in value:
        fitted = value["fitted"]
        forecast = value["forecast"]
        all_y = fitted + forecast
        n = len(fitted)
        x = list(range(2018, 2018 + len(all_y)))
        fig, ax = plotter.line(
            x=x, y=all_y,
            xlabel="Year", ylabel="Demand (10,000 tons)",
            title="GM(1,1) Grey Forecast of Logistics Demand",
            markers=True,
        )
        ax.scatter(x[:n], fitted, color="#d62728", s=60, zorder=5, label="Fitted")
        ax.scatter(x[n:], forecast, color="#2ca02c", s=60, zorder=5, label="Forecast")
        ax.axvline(x=x[n]-0.5, color="gray", linestyle="--", alpha=0.5, label="Forecast Start")
        ax.legend(fontsize=9)
        plotter.save(fig, fig_dir / "forecast.pdf", dpi=300)
        plotter.save(fig, fig_dir / "forecast.png", dpi=200)
        fig_count += 1
        print(f"  [{fig_count}] Forecast line chart -> forecast.pdf / .png")

    if "selection" in value:
        labels = value.get("labels_all", ["A", "B", "C", "D", "E"])
        costs = value.get("costs", [30, 45, 25, 50, 35])
        benefits = value.get("benefits", [15, 22, 12, 28, 18])
        solution = value.get("solution", [0]*5)
        n_loc = len(labels)
        x_pos = range(n_loc)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
        # Cost chart
        colors = ["#2ca02c" if s > 0.5 else "#d62728" for s in solution]
        ax1.bar(x_pos, costs, color=colors, alpha=0.8)
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(labels)
        ax1.set_ylabel("Cost (10,000 yuan)")
        ax1.set_title("Construction Cost by Location")

        # Population chart
        ax2.bar(x_pos, benefits, color=colors, alpha=0.8)
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(labels)
        ax2.set_ylabel("Population (10,000)")
        ax2.set_title("Covered Population by Location")

        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor="#2ca02c", label="Selected"),
            Patch(facecolor="#d62728", label="Not Selected"),
        ]
        fig.legend(handles=legend_elements, loc="upper center", ncol=2, fontsize=9)

        fig.tight_layout(rect=[0, 0, 1, 0.92])
        plotter.save(fig, fig_dir / "site_selection.pdf", dpi=300)
        plotter.save(fig, fig_dir / "site_selection.png", dpi=200)
        fig_count += 1
        print(f"  [{fig_count}] Site selection chart -> site_selection.pdf / .png")

plotter.close_all()
print(f"\n  Generated {fig_count} figures in: {fig_dir}")

# ================================================================
# 生成论文
# ================================================================
print()
print("-" * 40)
print("  PHASE 5: Generating Paper")
print("-" * 40)

paper_path = generate_paper(
    output_path=str(output_dir / f"论文_{problem_name}.docx"),
    problem_text=problem_text,
    analysis={"sub_problems": sub_problems},
    recommendations=[{
        "summary": " -> ".join(sp["model"] for sp in sub_problems),
        "confidence": sum(sp["score"] for sp in sub_problems) / max(len(sub_problems), 1),
        "sub_problems": sub_problems,
    }],
    results=all_results,
    figures_dir=str(fig_dir),
)
print(f"  Paper: {paper_path}")

# ================================================================
# 保存结果
# ================================================================
results_json = {
    "problem": problem_name,
    "sub_problems": [
        {"id": sp["id"], "title": sp["title"], "type": sp["type"],
         "model": sp["model"], "score": sp["score"], "reason": sp["reason"]}
        for sp in sub_problems
    ],
    "results": all_results,
}
with open(output_dir / "results.json", "w", encoding="utf-8") as f:
    json.dump(results_json, f, ensure_ascii=False, indent=2, default=str)

# ================================================================
# 完成
# ================================================================
print()
print("=" * 60)
print("  DONE!")
print("=" * 60)
print(f"  Paper : output/{problem_name}/论文_{problem_name}.docx")
print(f"  Figures: output/{problem_name}/figures/")
print(f"  Data  : output/{problem_name}/results.json")
print()
print("  Next: Put new problems in problems/ folder, run 'python start.py'")
print("=" * 60)
