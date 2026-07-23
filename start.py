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

    for q in range(1, sub_count + 1):
        print(f"\n  Q{q}: Running deterministic solver...")
        # Try each solver type, pick the one that fits the data
        df = None
        for k, v in data_files.items():
            if not k.endswith("_norm") and v.select_dtypes(include=np.number).shape[1] >= 2:
                df = v; break
        if df is None:
            all_results[f"sub_{q}"] = {"summary": "No numeric data found", "status": "skipped"}
            continue

        numeric = df.select_dtypes(include=np.number)
        nan_ratio = numeric.isnull().sum().sum() / max(numeric.size, 1)

        # Auto-detect: sparse matrix → routing
        if nan_ratio > 0.15 and numeric.shape[1] >= numeric.shape[0] - 2:
            first_col = numeric.iloc[:, 0].dropna().tolist()
            if len(first_col) >= 3 and first_col[:3] == [1.0, 2.0, 3.0]:
                sparse = numeric.iloc[:, 1:].values.astype(float)
            else:
                sparse = numeric.values.astype(float)
            result = solve_routing(sparse)
            all_results[f"sub_{q}"] = {
                "total_distance": result["distance"],
                "tour": result["tour"],
                "tour_labels": [str(t+1) for t in result["tour"]],
                "n_locations": result["n_locations"],
                "method": result["method"],
                "summary": f"最短配送回路: {result['distance']}km, {result['n_locations']}个地点"
            }
            print(f"  Q{q}: TSP solved — {result['distance']}km")
        # Dense matrix with many columns → evaluation
        elif numeric.shape[1] >= 3 and nan_ratio < 0.1:
            try:
                matrix = numeric.values.astype(float)
                result = solve_topsis(matrix)
                all_results[f"sub_{q}"] = {
                    "scores": result["scores"], "rank": result["rank"],
                    "weights": result["weights"],
                    "labels": df.iloc[:, 0].tolist() if not pd.api.types.is_numeric_dtype(df.iloc[:, 0]) else [f"Item{i+1}" for i in range(len(df))],
                    "summary": f"TOPSIS综合评价完成, {len(result['scores'])}个方案"
                }
                print(f"  Q{q}: TOPSIS solved")
            except Exception as e:
                all_results[f"sub_{q}"] = {"summary": f"TOPSIS failed: {e}"}
        # Time series → grey forecast
        elif numeric.shape[1] <= 2 and numeric.shape[0] >= 4:
            try:
                data = numeric.iloc[:, 0].dropna().tolist()
                result = solve_grey_forecast(data, steps=3)
                all_results[f"sub_{q}"] = {
                    "forecast": [round(v,2) for v in result["forecast"]],
                    "fitted": [round(v,2) for v in result["fitted"]],
                    "mape": result["mape"], "grade": result["grade"],
                    "summary": f"GM(1,1)预测: MAPE={result['mape']:.2f}%, 预测值={[round(v,1) for v in result['forecast']]}"
                }
                print(f"  Q{q}: GM(1,1) solved — MAPE={result['mape']:.2f}%")
            except Exception as e:
                all_results[f"sub_{q}"] = {"summary": f"Forecast failed: {e}"}
        else:
            all_results[f"sub_{q}"] = {"summary": f"Data format not recognized", "status": "unknown"}

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
