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

    # === Phase 1: AI reads problem → understands each question → picks data+method ===
    print_section("Phase 1: AI Understanding + Solving")
    from mathmodel.pipeline.dedicated_solvers import solve_routing, solve_knapsack, solve_topsis, solve_grey_forecast

    all_results = {}
    sub_count = min(max_questions, 4)

    if api_key:
        # AI reads the problem and figures out what each question needs
        from mathmodel.pipeline.universal_solver import UniversalSolver
        us = UniversalSolver(api_key=api_key)

        for q in range(1, sub_count + 1):
            print(f"\n  Q{q}: AI analyzing problem + matching data...")

            # AI reads the problem to understand this question
            q_analysis = us._call(
                f"分析子问题{q}。回答: 1)这问在求解什么 2)需要什么类型的数据 "
                "3)应该用什么数学方法 4)预期输出什么结果。用中文。",
                f"题目:\n{problem_text[:3000]}\n\n可用的数据文件:\n"
                + "\n".join(f"{k}: {v.shape} cols={list(v.columns)[:5]}" for k,v in data_files.items()),
                max_tok=4000)
            print(f"  Q{q} analysis: {q_analysis[:200]}...")

            # Try the optimal solver first, fall back to others
            result = None
            for df_name, df in data_files.items():
                if df_name.endswith("_norm"): continue
                numeric = df.select_dtypes(include=np.number)
                if numeric.shape[1] < 2: continue

                # Detect data type and solve
                nan_r = numeric.isnull().sum().sum() / max(numeric.size, 1)
                if nan_r > 0.1 and numeric.shape[1] >= numeric.shape[0] - 2:
                    # Sparse matrix → routing
                    fc = numeric.iloc[:,0].dropna().tolist()
                    sparse = (numeric.iloc[:,1:].values.astype(float) if len(fc)>=3 and fc[:3]==[1,2,3]
                              else numeric.values.astype(float))
                    r = solve_routing(sparse)
                    result = {"total_distance": r["distance"], "tour": r["tour"],
                              "n_locations": r["n_locations"], "method": r["method"],
                              "used_file": df_name,
                              "summary": f"TSP最短路径: {r['distance']}km, {r['n_locations']}地点"}
                    print(f"  Q{q}: TSP({df_name}) → {r['distance']}km")
                    break
                elif numeric.shape[1] >= 3:
                    r = solve_topsis(numeric.values.astype(float))
                    labels = df.iloc[:,0].tolist()
                    result = {"scores": r["scores"], "rank": r["rank"], "weights": r["weights"],
                              "labels": labels, "used_file": df_name,
                              "summary": f"TOPSIS: {numeric.shape[0]}方案"}
                    print(f"  Q{q}: TOPSIS({df_name}) done")
                    break
                elif numeric.shape[0] >= 4:
                    r = solve_grey_forecast(numeric.iloc[:,0].dropna().tolist(), 3)
                    result = {"forecast": [round(v,2) for v in r["forecast"]],
                              "mape": r["mape"], "used_file": df_name,
                              "summary": f"GM(1,1): MAPE={r['mape']:.2f}%"}
                    print(f"  Q{q}: GM(1,1)({df_name}) MAPE={r['mape']:.2f}%")
                    break

            if result is not None:
                all_results[f"sub_{q}"] = result
            else:
                all_results[f"sub_{q}"] = {"summary": "No suitable solver found", "status": "skipped"}
    else:
        print("  No API key — using auto-detection only")
        for q in range(1, sub_count + 1):
            all_results[f"sub_{q}"] = {"summary": "Skipped (no API key)"}

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
