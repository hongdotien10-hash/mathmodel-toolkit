"""MathModel Toolkit — 专用求解器 + Skills管线，5M token/篇
用法：python start.py
求解: 确定性算法(Floyd/TOPSIS/GM/IP)保证正确
管线: 6阶段×195次AI调用 深度分析+写作+验证"""
import sys, json, warnings, datetime
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
warnings.filterwarnings('ignore')

sys.path.insert(0, str(Path(__file__).parent))

from mathmodel.utils import set_seed
from mathmodel.paper.word_writer import generate_paper
from mathmodel.pipeline.rich_progress import PhaseTracker, print_header, print_section

set_seed(42)
PROBLEMS_DIR = Path(__file__).parent / "problems"
OUTPUT_DIR = Path(__file__).parent / "output"
INTERACTIVE = "--interactive" in sys.argv or "-i" in sys.argv


def main():
    # === Menu ===
    from mathmodel.pipeline.menu import show_menu
    contest_type, max_questions, max_pages, max_figures, user_notes = show_menu()
    tracker = PhaseTracker(title="MathModel Toolkit")
    print_header("MathModel Toolkit — Solvers + AI Pipeline")

    # === Load problem + data ===
    problem_dirs = sorted([d for d in PROBLEMS_DIR.iterdir()
                           if d.is_dir() and not d.name.startswith('.')])
    if not problem_dirs: print("ERROR: No problems found"); sys.exit(1)
    selected = problem_dirs[0]
    out_dir = OUTPUT_DIR / selected.name; out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir = out_dir / "figures"; fig_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Output: {out_dir}")

    problem_text = ""; data_files = {}
    for f in sorted(selected.iterdir()):
        s = f.suffix.lower()
        if s == '.txt': problem_text = f.read_text(encoding='utf-8'); print(f"[doc] {f.name} ({len(problem_text)} chars)")
        elif s == '.pdf':
            try:
                import pdfplumber
                with pdfplumber.open(str(f)) as pdf:
                    problem_text = '\n\n'.join(p.extract_text() or "" for p in pdf.pages)
                print(f"[doc] {f.name} ({len(problem_text)} chars)")
            except Exception as e: print(f"[doc] {f.name}: {e}")
        elif s in ('.xlsx', '.xls'):
            df = pd.read_excel(f, nrows=500) if f.stat().st_size > 5e6 else pd.read_excel(f)
            data_files[f.stem] = df; print(f"[data] {f.name} {df.shape}")
        elif s == '.csv':
            df = pd.read_csv(f, low_memory=True, nrows=500) if f.stat().st_size > 5e6 else pd.read_csv(f)
            data_files[f.stem] = df; print(f"[data] {f.name} {df.shape}")

    if not problem_text: print("ERROR: No problem text"); sys.exit(1)

    # === Get API key ===
    api_key = ""
    try:
        from api.config import APIConfig
        cfg = APIConfig(); api_key = cfg.api_key if cfg.is_configured else ""
    except: pass

    # === Phase 1: Dedicated solvers (deterministic, fast, correct) ===
    print_section("Phase 1: Deterministic Solving")
    from mathmodel.pipeline.dedicated_solvers import solve_routing, solve_knapsack, solve_topsis, solve_grey_forecast, solve_kmeans

    all_results = {}
    sub_count = min(max_questions, 4)  # AI will determine actual count later

    # AI-driven solver selection: let AI analyze data and pick the right solver
    for q in range(1, sub_count + 1):
        print(f"\n  Q{q}: AI selecting best solver for this data...")
        df = None
        for k, v in data_files.items():
            if not k.endswith("_norm") and v.select_dtypes(include=np.number).shape[1] >= 2:
                df = v; break
        if df is None:
            all_results[f"sub_{q}"] = {"summary": "No numeric data found"}
            continue

        numeric = df.select_dtypes(include=np.number)
        nan_ratio = numeric.isnull().sum().sum() / max(numeric.size, 1)
        n_rows, n_cols = numeric.shape

        # Build data profile for AI decision
        data_profile = f"Rows={n_rows}, Cols={n_cols}, NaN={nan_ratio:.1%}, "
        data_profile += f"Columns={list(numeric.columns)[:8]}, "
        data_profile += f"Sample:\n{numeric.head(3).to_string()}"

        solver_choice = "routing"  # default
        if api_key:
            # AI decides which solver to use
            try:
                from mathmodel.pipeline.universal_solver import UniversalSolver
                us = UniversalSolver(api_key=api_key)
                choice = us._call(
                    "分析这个数据表格的特征,从以下选择最合适的求解器: "
                    "routing(稀疏距离矩阵→TSP/VRP), evaluation(多指标→TOPSIS/AHP), "
                    "prediction(时序→GM(1,1)/ARIMA), optimization(成本收益→背包/IP), "
                    "statistics(多变量→相关分析/PCA), clustering(样本→KMeans)。"
                    "只回复一个英文单词。",
                    f"数据:\n{data_profile}", max_tok=50)
                solver_choice = choice.strip().lower()
                print(f"  AI chose: {solver_choice}")
            except: pass

        # Execute the chosen solver
        if "routing" in solver_choice and nan_ratio > 0.1:
            first_col = numeric.iloc[:, 0].dropna().tolist()
            if len(first_col) >= 3 and first_col[:3] == [1.0, 2.0, 3.0]:
                sparse = numeric.iloc[:, 1:].values.astype(float)
            else: sparse = numeric.values.astype(float)
            result = solve_routing(sparse)
            all_results[f"sub_{q}"] = {
                "total_distance": result["distance"], "tour": result["tour"],
                "n_locations": result["n_locations"], "method": result["method"],
                "summary": f"TSP: {result['distance']}km, {result['n_locations']}地点"
            }
            print(f"  Q{q}: TSP — {result['distance']}km")
        elif "evaluation" in solver_choice or ("tops" in solver_choice and n_cols >= 3):
            try:
                result = solve_topsis(numeric.values.astype(float))
                labels = df.iloc[:,0].tolist() if not pd.api.types.is_numeric_dtype(df.iloc[:,0]) else [f"Item{i+1}" for i in range(n_rows)]
                all_results[f"sub_{q}"] = {
                    "scores": result["scores"], "rank": result["rank"],
                    "weights": result["weights"], "labels": labels,
                    "summary": f"TOPSIS: {n_rows}方案×{n_cols}指标"
                }
                print(f"  Q{q}: TOPSIS done")
            except Exception as e: all_results[f"sub_{q}"] = {"summary": f"Eval failed: {e}"}
        elif "prediction" in solver_choice and n_rows >= 4:
            try:
                data = numeric.iloc[:,0].dropna().tolist()
                result = solve_grey_forecast(data, steps=3)
                all_results[f"sub_{q}"] = {
                    "forecast": [round(v,2) for v in result["forecast"]],
                    "mape": result["mape"], "grade": result["grade"],
                    "summary": f"GM(1,1): MAPE={result['mape']:.2f}%"
                }
                print(f"  Q{q}: GM(1,1) — MAPE={result['mape']:.2f}%")
            except Exception as e: all_results[f"sub_{q}"] = {"summary": f"Pred failed: {e}"}
        elif "optimization" in solver_choice or ("knapsack" in solver_choice and n_cols >= 2):
            try:
                costs = numeric.iloc[:,1].values.astype(float).tolist()
                benefits = numeric.iloc[:,2].values.astype(float).tolist() if n_cols>2 else numeric.iloc[:,0].tolist()
                result = solve_knapsack(costs, benefits)
                all_results[f"sub_{q}"] = {"selection": result["selection"],
                    "total_cost": result["total_cost"], "total_benefit": result["total_benefit"],
                    "summary": f"Knapsack: {len(result['selection'])} selected"}
                print(f"  Q{q}: Knapsack — {len(result['selection'])} items")
            except Exception as e: all_results[f"sub_{q}"] = {"summary": f"Opt failed: {e}"}
        else:
            all_results[f"sub_{q}"] = {"summary": f"AI chose '{solver_choice}' but could not execute", "status": "unknown"}
            print(f"  Q{q}: Unknown solver '{solver_choice}'")

    # === Phase 2: Skills pipeline (5M token AI) ===
    ai_content = {}
    if api_key:
        print_section("Phase 2: AI Skills Pipeline (6 stages, ~5M tokens)")
        from mathmodel.pipeline.skills_pipeline import SkillsPipeline
        sp = SkillsPipeline(api_key=api_key)
        pipeline_result = sp.run(problem_text, data_files, str(fig_dir), all_results, sub_count)

        # Extract paper content
        paper = pipeline_result.get("paper", {})
        ai_content["abstract"] = paper.get("abstract", "")
        ai_content["title"] = paper.get("title", "")
        for q in range(1, sub_count + 1):
            ai_content[f"section_{q}"] = paper.get(f"section_{q}", "")
        ai_content["sensitivity"] = paper.get("sensitivity", "")
        ai_content["evaluation"] = paper.get("evaluation", "")
        ai_content["conclusion"] = paper.get("conclusion", "")
        total_tok = (sp.total_in + sp.total_out) // 1000
        print(f"\n  Pipeline: {sp.calls} calls, {total_tok}K tokens")

    # === Phase 3: Generate Word paper ===
    print_section("Phase 3: Paper Generation")
    ts = datetime.datetime.now().strftime("%H%M%S")
    sub_list = [{"id": q, "title": f"子问题{q}", "type": "综合"} for q in range(1, sub_count + 1)]

    try:
        paper_path = generate_paper(
            output_path=str(out_dir / f"论文_{selected.name}_{ts}.docx"),
            problem_text=problem_text,
            analysis={"sub_problems": sub_list},
            recommendations=[{"summary": "Solvers + AI Pipeline", "sub_problems": sub_list}],
            results=all_results, figures_dir=str(fig_dir), ai_content=ai_content)
        print(f"  Word: {paper_path}")
    except Exception as e:
        print(f"  Word failed: {e}")
        from docx import Document
        doc = Document()
        doc.add_heading("论文", 0)
        for q in range(1, sub_count + 1):
            doc.add_heading(f"Q{q}", 1)
            doc.add_paragraph(all_results.get(f"sub_{q}", {}).get("summary", ""))
        paper_path = out_dir / f"论文_{ts}.docx"; doc.save(str(paper_path))

    # === Done ===
    tracker.finish()
    print(f"\n{'='*60}")
    print(f"  OUTPUT: {out_dir}")
    print(f"  Paper:  {paper_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
