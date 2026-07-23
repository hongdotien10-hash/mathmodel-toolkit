"""MathModel Toolkit — AI全权驱动
用法：python start.py
适用任何国赛/美赛/电工杯题目，AI自动分析、求解、写论文"""
import sys, json, re, warnings, datetime
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
warnings.filterwarnings('ignore')

sys.path.insert(0, str(Path(__file__).parent))

from mathmodel.utils import set_seed
from mathmodel.visualization import Plotter, set_style
from mathmodel.paper.word_writer import generate_paper
from mathmodel.pipeline.rich_progress import PhaseTracker, print_header, print_section, print_result_summary

set_seed(42)
PROBLEMS_DIR = Path(__file__).parent / "problems"
OUTPUT_DIR = Path(__file__).parent / "output"
INTERACTIVE = "--interactive" in sys.argv or "-i" in sys.argv

def _pause(msg="Continue?"):
    if INTERACTIVE:
        try: input(f"\n  [PAUSE] {msg} (Enter to continue) ")
        except (EOFError, KeyboardInterrupt): print("\nStopped."); sys.exit(0)


def main():
    # === Step 0: Menu ===
    from mathmodel.pipeline.menu import show_menu
    contest_type, max_questions, max_pages, max_figures, user_notes = show_menu()

    tracker = PhaseTracker(title="MathModel Toolkit")
    print_header(f"MathModel Toolkit — AI-Powered Universal Solver")

    # === Step 1: Load problem + data ===
    problem_dirs = sorted([d for d in PROBLEMS_DIR.iterdir()
                           if d.is_dir() and not d.name.startswith('.')])
    if not problem_dirs:
        print("ERROR: No problems found in problems/"); sys.exit(1)
    selected = problem_dirs[0]
    out_dir = OUTPUT_DIR / selected.name
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Output: {out_dir}")

    problem_text = ""
    data_files = {}
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
            except Exception as e: print(f"[doc] {f.name}: {e}")
        elif s in ('.xlsx', '.xls'):
            df = pd.read_excel(f, nrows=500) if f.stat().st_size > 5e6 else pd.read_excel(f)
            data_files[f.stem] = df
            print(f"[data] {f.name} {df.shape}")
        elif s == '.csv':
            df = pd.read_csv(f, low_memory=True, nrows=500) if f.stat().st_size > 5e6 else pd.read_csv(f)
            data_files[f.stem] = df
            print(f"[data] {f.name} {df.shape}")

    if not problem_text:
        print("ERROR: No problem text found"); sys.exit(1)

    # Get API key
    api_key = ""
    try:
        from api.config import APIConfig
        cfg = APIConfig()
        api_key = cfg.api_key if cfg.is_configured else ""
    except: pass

    # === Step 2: AI analyzes everything ===
    print_section("Phase 1: AI Problem Analysis")
    all_results = {}
    sub_problems = []

    if api_key:
        from mathmodel.pipeline.universal_solver import UniversalSolver
        us = UniversalSolver(api_key=api_key)
        analysis = us.analyze_problem(problem_text, data_files)
        print(f"  AI Analysis: {us.calls} calls")

        # === Step 3: AI solves each sub-problem ===
        print_section("Phase 2: AI Solving Each Sub-Problem")
        sub_count = min(max_questions, 4)  # default 4, use AI to determine
        for q in range(1, sub_count + 1):
            if q > max_questions: break
            print(f"\n  {'='*40}")
            print(f"  Q{q}: AI Solving...")
            print(f"  {'='*40}")

            sp_desc = f"子问题{q}。题目文本:\n{problem_text}\n\n分析:\n{analysis.get('refined','')[:2000]}"
            if user_notes:
                sp_desc += f"\n\n用户要求:\n{user_notes}"

            result = us.solve_sub_problem(q, sp_desc, data_files, str(fig_dir), max_rounds=20)
            all_results[f"sub_{q}"] = {
                "summary": result.get("final_output", "")[:500],
                "rounds": len(result.get("rounds", [])),
            }
            print(f"  Q{q} done: {len(result.get('rounds',[]))} rounds")

        _pause("All questions solved. Continue to paper writing?")

        # === Step 4: AI writes paper ===
        print_section("Phase 3: AI Paper Writing")
        sub_list = [{"id": q, "title": f"子问题{q}", "type": "综合"} for q in range(1, sub_count + 1)]
        paper_sections = us.write_paper(problem_text, sub_list, all_results, str(fig_dir), contest_type)

        # Build ai_content for word_writer
        ai_content = {}
        if paper_sections.get('title'): pass  # title used below
        if paper_sections.get('abstract'):
            ai_content['abstract'] = paper_sections['abstract']
        for q in range(1, sub_count + 1):
            if paper_sections.get(f'model_{q}'):
                ai_content[f'section_{q}'] = paper_sections[f'model_{q}']
        if paper_sections.get('sensitivity'):
            ai_content['sensitivity'] = paper_sections['sensitivity']
        if paper_sections.get('evaluation'):
            ai_content['evaluation'] = paper_sections['evaluation']
        if paper_sections.get('conclusion'):
            ai_content['conclusion'] = paper_sections['conclusion']

        print(f"  Total AI calls: {us.calls}")
    else:
        print("  No API key — using rule-based fallback")
        sub_count = min(max_questions, 2)
        sub_list = [{"id": q, "title": f"子问题{q}", "type": "综合"} for q in range(1, sub_count + 1)]
        ai_content = {}
        paper_sections = {}

    # === Step 5: Generate Word paper ===
    print_section("Phase 4: Paper Generation")
    ts = datetime.datetime.now().strftime("%H%M%S")
    paper_title = paper_sections.get('title', '数学建模竞赛论文') if api_key else '数学建模竞赛论文'

    try:
        paper_path = generate_paper(
            output_path=str(out_dir / f"{paper_title[:20]}_{ts}.docx"),
            problem_text=problem_text,
            analysis={"sub_problems": sub_list},
            recommendations=[{"summary": "AI-driven solving", "sub_problems": sub_list}],
            results=all_results, figures_dir=str(fig_dir), ai_content=ai_content)
        print(f"  Word: {paper_path}")
    except Exception as e:
        print(f"  Word failed: {e}")
        # Fallback minimal paper
        try:
            from docx import Document
            doc = Document()
            doc.add_heading(paper_title, 0)
            doc.add_paragraph(problem_text[:1000])
            for q in range(1, sub_count + 1):
                doc.add_heading(f"Q{q} Results", 1)
                r = all_results.get(f"sub_{q}", {})
                doc.add_paragraph(r.get("summary", str(r)[:500]))
            paper_path = out_dir / f"论文_{ts}.docx"
            doc.save(str(paper_path))
        except: paper_path = "FAILED"

    # === Done ===
    tracker.finish()
    print_result_summary(sub_list, all_results)
    print(f"\n{'='*60}")
    print(f"  OUTPUT: {out_dir}")
    print(f"  Paper:  {paper_path}")
    print(f"  Figures: {fig_dir}")
    print(f"{'='*60}")


def _serialize(obj):
    if isinstance(obj, dict): return {str(k): _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list): return [_serialize(v) for v in obj]
    if isinstance(obj, (np.integer,)): return int(obj)
    if isinstance(obj, (np.floating,)): return float(obj)
    if isinstance(obj, np.ndarray): return obj.tolist()
    return obj


if __name__ == "__main__":
    main()
