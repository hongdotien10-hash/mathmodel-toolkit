"""MathModel Toolkit — 获奖级论文
====================================
用法：python start.py
增强：多模型竞赛 + 深度灵敏度 + 误差诊断 + 专业图表组 + AI写作
"""

import sys, json, re
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import warnings; warnings.filterwarnings('ignore')

sys.path.insert(0, str(Path(__file__).parent))

from mathmodel.utils import set_seed, Timer
from mathmodel.utils.helpers import safe_call
from mathmodel.analyzer import ProblemClassifier, ModelKnowledgeBase
from mathmodel.models import EvaluationSolver, StatsSolver, OptimizationSolver, MLSolver
from mathmodel.sensitivity import SensitivityAnalyzer
from mathmodel.visualization import Plotter, set_style, get_colors
from mathmodel.paper.word_writer import generate_paper
from mathmodel.paper.latex_writer import generate_latex_paper
from mathmodel.pro import (ModelContest, DeepSensitivity, ResultNarrator,
                           ChartSuite, ErrorDiagnostics)
from mathmodel.pipeline.rich_progress import PhaseTracker, print_header, print_section, print_result_summary

set_seed(42)

PROBLEMS_DIR = Path(__file__).parent / "problems"
OUTPUT_DIR = Path(__file__).parent / "output"



def main():
    tracker = PhaseTracker(title="MathModel Toolkit PRO")
    print_header("MathModel Toolkit PRO — Award-Level")

    # === Step 1: Scan & Load (same as free version) ===
    problem_dirs = sorted([d for d in PROBLEMS_DIR.iterdir()
                           if d.is_dir() and not d.name.startswith('.')])
    if not problem_dirs:
        print("ERROR: No problems found in problems/")
        sys.exit(1)
    selected = problem_dirs[0]
    out_dir = OUTPUT_DIR / selected.name
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    problem_text, data_files, data_profiles = "", {}, {}
    for f in sorted(selected.iterdir()):
        s = f.suffix.lower()
        if s == '.txt':
            problem_text = f.read_text(encoding='utf-8')
            print(f"[doc] {f.name} ({len(problem_text)} chars)")
        elif s == '.pdf':
            try:
                import pdfplumber
                with pdfplumber.open(str(f)) as pdf:
                    problem_text = '\n\n'.join(p.extract_text() or "" for p in pdf.pages)
                print(f"[doc] {f.name} ({len(problem_text)} chars)")
            except Exception as e: print(f"[doc] {f.name} — {e}")
        elif s in ('.xlsx', '.xls'):
            df = pd.read_excel(f, nrows=500) if f.stat().st_size > 5e6 else pd.read_excel(f)
            data_files[f.stem] = df
            data_profiles[f.stem] = {"name": f.stem, "path": str(f), "shape": df.shape,
                                     "columns": list(df.columns), "size_category":
                                     "large" if f.stat().st_size > 5e6 else "medium" if df.shape[0] > 1000 else "small",
                                     "sample": df.head(5)}
            print(f"[data] {f.name} {df.shape}")
        elif s == '.csv':
            df = pd.read_csv(f, low_memory=True, nrows=500) if f.stat().st_size > 5e6 else pd.read_csv(f)
            data_files[f.stem] = df
            data_profiles[f.stem] = {"name": f.stem, "path": str(f), "shape": df.shape,
                                     "columns": list(df.columns), "size_category":
                                     "large" if f.stat().st_size > 5e6 else "small",
                                     "sample": df.head(5)}
            print(f"[data] {f.name} {df.shape}")

    # === Step 2: AI Analysis (same as free) ===
    sub_problems = _analyze(problem_text, data_profiles)
    print_section("Phase 1: AI Analysis")
    for sp in sub_problems:
        print(f"  Q{sp['id']}: [{sp['type']}] → {sp['model']} ({sp['score']:.0%}) [{sp.get('source','rule')}]")

    # === Step 3: API client for Pro modules ===
    api_key = ""
    try:
        from api.config import APIConfig
        cfg = APIConfig()
        if cfg.is_configured: api_key = cfg.api_key
    except Exception: pass

    # === Step 4: 🆕 PRO — Multi-Model Contest (本地或AI对比) ===
    print_section("PRO Phase 2: Multi-Model Contest")
    contest_results = {}
    mc = ModelContest(api_key=api_key)  # 无API时自动用指标对比
    for sp in sub_problems:
        if sp["type"] in ("评价", "预测", "优化", "统计"):
            print(f"\n  >> Q{sp['id']}: Running {sp['type']} model contest...")
            cr = safe_call(lambda s=sp: mc.contest(s, data_files),
                          desc=f"Q{sp['id']} model contest", timeout=300,
                          default={"winner": sp.get("model","?"), "candidates": [],
                                   "ai_reason": "contest skipped (timeout)"})
            contest_results[f"sub_{sp['id']}"] = cr
            print(f"     Winner: {cr.get('winner','?')} | {cr.get('ai_reason','')[:80]}...")
    if not api_key:
        print("  [本地对比] 基于指标数值自动选优")

    # === Step 5: Solve with best models ===
    print_section("Phase 3: Solving with Best Models")
    all_results = {}
    for sp in sub_problems:
        sp_id = sp["id"]
        ptype = sp["type"]

        # Use contest winner if available
        winner_model = ""
        if f"sub_{sp_id}" in contest_results:
            best = contest_results[f"sub_{sp_id}"]
            best_result = next((c for c in best.get("candidates", [])
                                if c["model"] == best.get("winner")), {})
            all_results[f"sub_{sp_id}"] = best_result.get("result", {})
            winner_model = best.get("winner", "")
            print(f"  Q{sp_id}: [{winner_model}] — contest winner")
            continue

        # Fallback: local solver
        df = _find_df(data_files, ptype)
        if df is None: continue
        numeric = df.select_dtypes(include=np.number)
        if ptype == "评价" and numeric.shape[1] >= 2:
            ev = EvaluationSolver()
            m = numeric.values.astype(float)
            ew = ev.entropy_weight(m)
            res = ev.topsis(m, weights=ew["weights"], impacts=[1]*m.shape[1])
            labels = df.iloc[:,0].tolist()
            all_results[f"sub_{sp_id}"] = {"labels": labels,
                "scores": [round(float(s),4) for s in res["scores"]],
                "rank": [int(r) for r in res["rank"]],
                "weights": {str(c): round(float(w),4) for c,w in zip(numeric.columns, ew["weights"])}}
            print(f"  Q{sp_id}: TOPSIS done")
        elif ptype == "预测" and numeric.shape[1] >= 1:
            ss = StatsSolver()
            data = numeric.iloc[:,0].dropna().tolist()
            if len(data) >= 4:
                pred = ss.grey_forecast(data, 3)
                all_results[f"sub_{sp_id}"] = {"original": data,
                    "fitted": [round(v,4) for v in pred["fitted"]],
                    "forecast": [round(v,4) for v in pred["forecast"]],
                    "mape": round(pred["mape"],2), "grade": pred["grade"]}
                print(f"  Q{sp_id}: GM(1,1) MAPE={pred['mape']:.2f}%")
        elif ptype == "优化" and numeric.shape[1] >= 2:
            costs = numeric.iloc[:,1].values.astype(float).tolist()
            benefits = numeric.iloc[:,2].values.astype(float).tolist() if numeric.shape[1] > 2 else numeric.iloc[:,0].tolist()
            budget = sum(costs)*0.6
            ratios = sorted([(benefits[i]/max(costs[i],1e-6),i) for i in range(len(costs))], key=lambda x:-x[0])
            sel = []; rem = budget; cost_total = 0; benefit_total = 0
            for _, i in ratios:
                if costs[i] <= rem: sel.append(i); rem -= costs[i]; cost_total += costs[i]; benefit_total += benefits[i]
            labels = df.iloc[:,0].tolist()
            all_results[f"sub_{sp_id}"] = {"selection": [str(labels[i]) for i in sel],
                "total_cost": round(cost_total,1), "total_population": round(benefit_total,1),
                "budget": round(budget,1), "solution": [1 if i in sel else 0 for i in range(len(costs))],
                "costs": costs, "benefits": benefits, "labels_all": labels}
            print(f"  Q{sp_id}: Optimization done ({len(sel)} selected)")

    # === Step 6: 🆕 PRO — Deep Sensitivity ===
    print_section("PRO Phase 4: Deep Sensitivity")
    ds = DeepSensitivity()
    sens_results = {}
    for key, val in all_results.items():
        if "forecast" in val and len(val["fitted"]) >= 4:
            def gm(p): s = StatsSolver(); r = s.grey_forecast(p.tolist(), 3); return float(r["forecast"][-1])
            base = val["fitted"]
            tornado = ds.tornado(gm, base, [f"Point {i+1}" for i in range(len(base))])
            mc = ds.monte_carlo(gm, base, noise_pct=0.05, n_samples=500)
            sens_results[key] = {"tornado": tornado, "monte_carlo": mc}
            ds.plot_tornado(tornado["impacts"], title="Parameter Sensitivity",
                            output_path=str(fig_dir / f"{key}_tornado.pdf"))
            ds.plot_mc_distribution([gm(np.array(base)*np.random.normal(1,0.05,len(base))) for _ in range(500)],
                                   output_path=str(fig_dir / f"{key}_mc_dist.pdf"))
            print(f"  {key}: Tornado top={tornado['most_sensitive']}, MC CV={mc['cv']:.4f}")

    # === Step 7: 🆕 PRO — Error Diagnostics ===
    print_section("PRO Phase 5: Error Diagnostics")
    ed = ErrorDiagnostics()
    diag_results = {}
    for key, val in all_results.items():
        if "forecast" in val and "fitted" in val and "original" in val:
            ra = ed.residual_analysis(val["original"], val["fitted"])
            intervals = ed.prediction_intervals(val["fitted"], val["forecast"], np.std(ra["residuals"]))
            diag_results[key] = {"residual_analysis": ra, "prediction_intervals": intervals}
            ed.plot_residuals(val["original"], val["fitted"],
                             output_path=str(fig_dir / f"{key}_residuals.png"))
            ed.plot_prediction_interval(val["fitted"], val["forecast"], intervals["intervals"],
                                        output_path=str(fig_dir / f"{key}_pred_intervals.png"))
            print(f"  {key}: MAPE={ra['mape']:.2f}%, DW={ra['dw']:.3f}, Normal={ra['is_normal']}")

    # === Step 8: 🆕 PRO — Chart Suite ===
    print_section("PRO Phase 6: Professional Chart Suites")
    cs = ChartSuite()
    for key, val in all_results.items():
        if "forecast" in val and "fitted" in val:
            cs.prediction_suite(val.get("original", []), val["fitted"], val["forecast"],
                                output_path=str(fig_dir / f"{key}_pred_suite.png"))
            print(f"  [{key}] Prediction suite generated")
        if "scores" in val and "labels" in val and "weights" in val:
            cs.evaluation_suite(val["scores"], val["labels"], val["weights"],
                               output_path=str(fig_dir / f"{key}_eval_suite.png"))
            print(f"  [{key}] Evaluation suite generated")
        if "selection" in val and "costs" in val:
            cs.optimization_suite(val["costs"][:20], val["benefits"][:20], val.get("labels_all", val["selection"])[:20],
                                  val["solution"][:20] if "solution" in val else [1]*len(val["costs"][:20]),
                                  val.get("budget", 100),
                                  output_path=str(fig_dir / f"{key}_opt_suite.png"))
            print(f"  [{key}] Optimization suite generated")

    # === Step 9: 🆕 PRO — Result-Driven Writing ===
    ai_content = {}
    if api_key:
        print_section("PRO Phase 7: Result-Driven Writing")
        rn = ResultNarrator(api_key=api_key)
        for sp in sub_problems:
            sp_id = sp["id"]
            result = all_results.get(f"sub_{sp_id}", {})
            cr = contest_results.get(f"sub_{sp_id}", {})
            text = safe_call(lambda s=sp, r=result, c=cr: rn.narrate_result(s, r, c),
                           desc=f"Q{sp_id} result writing", timeout=180,
                           default=rn._fallback_narrative(sp, result))
            ai_content[f"section_{sp_id}"] = text
            print(f"  Q{sp_id}: {len(text)} chars")

        # AI abstract and evaluation
        try:
            from mathmodel.pipeline.smart_orchestrator import AIDrivenPipeline
            ai = AIDrivenPipeline(api_key=api_key, model="deepseek-chat")
            dsum = "\n".join(f"{n}: {p['shape'][0]}r x {p['shape'][1]}c" for n, p in data_profiles.items())
            plan = ai.analyze_and_plan(problem_text, dsum)
            analyses = ai.interpret_results(plan, all_results)
            ai_content["abstract"] = ai.write_abstract(problem_text, plan, all_results, analyses)
            ai_content["sensitivity"] = ai.write_sensitivity_section(all_results)
            ai_content["evaluation"] = ai.write_evaluation_section(sub_problems, all_results)
            print(f"  Abstract: {len(ai_content.get('abstract',''))} chars")
        except Exception as e:
            print(f"  AI writing failed: {e}")

    # === Step 10: Generate Papers ===
    print_section("Phase 8: Paper Generation")
    import datetime
    ts = datetime.datetime.now().strftime("%H%M%S")
    paper_path = generate_paper(
        output_path=str(out_dir / f"Pro论文_{selected.name}_{ts}.docx"),
        problem_text=problem_text, analysis={"sub_problems": sub_problems},
        recommendations=[{"summary": "Pro: multi-model contest", "sub_problems": sub_problems}],
        results=all_results, figures_dir=str(fig_dir), ai_content=ai_content)
    print(f"  Word: {paper_path}")
    try:
        tex_path = generate_latex_paper(str(out_dir / "latex"), problem_text,
                                        {"sub_problems": sub_problems}, all_results,
                                        str(fig_dir), ai_content)
        print(f"  LaTeX: {tex_path}")
    except Exception as e: print(f"  LaTeX: skipped ({e})")

    # === Save ===
    with open(out_dir / "pro_results.json", "w", encoding="utf-8") as f:
        json.dump({"sub_problems": sub_problems, "results": _serialize(all_results),
                   "contest": {k: {"winner": v["winner"]} for k, v in contest_results.items()},
                   "sensitivity": {k: {"tornado_top": v["tornado"]["most_sensitive"]}
                                   for k, v in sens_results.items()}},
                  f, ensure_ascii=False, indent=2, default=str)

    tracker.finish()
    print_result_summary(sub_problems, all_results)
    print_header(f"PRO DONE! Paper -> {paper_path}")
    print(f"  Figures: {fig_dir}")


def _analyze(problem_text, data_profiles):
    """AI analysis with rule fallback"""
    lines = problem_text.split('\n')
    sub_raw = []
    for i, line in enumerate(lines):
        line = line.strip()
        if not line: continue
        if '问题' in line and any(c in line for c in '123456789一二三四五六七八九'):
            ctx = line
            for j in range(i+1, min(i+8, len(lines))):
                if '问题' in lines[j] and any(c in lines[j] for c in '123456789'): break
                ctx += ' ' + lines[j].strip()
            sub_raw.append({"id": len(sub_raw)+1, "text": ctx[:500]})
            if len(sub_raw) >= 6: break
    if not sub_raw: sub_raw = [{"id": 1, "text": problem_text[:500]}]

    try:
        from api.config import APIConfig
        cfg = APIConfig()
        if cfg.is_configured:
            from api.analyzer import AIAnalyzer
            analyzer = AIAnalyzer(cfg)
            analysis = analyzer.full_analysis(problem_text, "\n".join(
                f"{n}: {p['shape']} cols={p['columns'][:5]}" for n, p in data_profiles.items()))
            sub_problems = []
            for sp in analysis.get("problem_analysis", {}).get("sub_problems", []):
                recs = analysis.get("model_recommendations", [])
                ai_model = ""; ai_score = 0.85
                for r in recs:
                    if r.get("sub_problem_id") == sp.get("id"):
                        rc = r.get("recommendations", [])
                        if rc: ai_model = rc[0].get("model", ""); ai_score = rc[0].get("score", 0.85)
                        break
                sub_problems.append({"id": sp.get("id", len(sub_problems)+1),
                    "title": sp.get("title","")[:150], "full_text": sp.get("title",""),
                    "type": sp.get("type","综合"), "model": ai_model or f"{sp.get('type','')}相关模型",
                    "score": ai_score, "reason": sp.get("reason",""), "source": "ai"})
            if sub_problems: return sub_problems
    except Exception: pass

    # Rule fallback
    classifier = ProblemClassifier(); kb = ModelKnowledgeBase()
    sub_problems = []
    for sp in sub_raw:
        clf = classifier.classify(sp["text"])
        cand = kb.query(problem_type=clf["type"], top_k=3)
        m = cand[0] if cand else {"model": "待定", "score": 0, "reason": ""}
        sub_problems.append({"id": sp["id"], "title": sp["text"][:150], "full_text": sp["text"],
            "type": clf["type"], "model": m["model"], "score": m["score"],
            "reason": m["reason"], "source": "rule"})
    return sub_problems


def _find_df(data_files, ptype):
    for k, v in data_files.items():
        if k.endswith("_norm"): continue
        if v.select_dtypes(include=np.number).shape[1] >= 2: return v
    return list(data_files.values())[0] if data_files else None


def _serialize(obj):
    if isinstance(obj, dict): return {str(k): _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list): return [_serialize(v) for v in obj]
    if isinstance(obj, (np.integer,)): return int(obj)
    if isinstance(obj, (np.floating,)): return float(obj)
    if isinstance(obj, np.ndarray): return obj.tolist()
    return obj


if __name__ == "__main__":
    main()
