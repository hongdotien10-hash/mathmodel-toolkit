"""MathModel Toolkit — 全部靠AI，不硬编码任何逻辑"""
import sys, json, warnings, datetime, subprocess, tempfile, time
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import urllib.request
warnings.filterwarnings('ignore')

sys.path.insert(0, str(Path(__file__).parent))

PROBLEMS_DIR = Path(__file__).parent / "problems"
OUTPUT_DIR = Path(__file__).parent / "output"
INTERACTIVE = "--interactive" in sys.argv or "-i" in sys.argv


class AI:
    """AI客户端 — 所有决策都通过它"""

    def __init__(self, api_key: str):
        self.key = api_key
        self.calls = 0

    def ask(self, system: str, user: str, max_tok: int = 8000) -> str:
        body = json.dumps({
            "model": "deepseek-chat", "temperature": 0.1, "max_tokens": max_tok,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
        }).encode()
        req = urllib.request.Request("https://api.deepseek.com/v1/chat/completions",
            data=body, headers={"Content-Type": "application/json",
                               "Authorization": f"Bearer {self.key}"}, method="POST")
        for _ in range(3):
            try:
                with urllib.request.urlopen(req, timeout=300) as r:
                    self.calls += 1
                    return json.loads(r.read())["choices"][0]["message"]["content"]
            except: time.sleep(5)
        return ""

    def extract_code(self, text: str) -> str:
        if "```python" in text: return text.split("```python")[1].split("```")[0].strip()
        if "```" in text: return text.split("```")[1].split("```")[0].strip()
        return text.strip()

    def run_code(self, code: str, name: str, cwd: str, timeout: int = 180) -> str:
        path = Path(tempfile.gettempdir()) / f"{name}.py"
        path.write_text(code, encoding="utf-8")
        try:
            r = subprocess.run([sys.executable, str(path)],
                capture_output=True, text=True, timeout=timeout,
                cwd=cwd, encoding='utf-8', errors='replace')
            return (r.stdout[-5000:] or "") + "\n" + (r.stderr[-3000:] or "")
        except subprocess.TimeoutExpired: return "TIMEOUT"
        except Exception as e: return f"ERROR: {e}"


def main():
    print("\n" + "=" * 60)
    print("  MathModel Toolkit — AI-Native Universal Solver")
    print("=" * 60)

    # === API ===
    api_key = ""
    try:
        from api.config import APIConfig
        cfg = APIConfig(); api_key = cfg.api_key if cfg.is_configured else ""
    except: pass
    if not api_key:
        print("ERROR: No API key configured. Edit .env file.")
        sys.exit(1)

    ai = AI(api_key)

    # === Menu ===
    from mathmodel.pipeline.menu import show_menu
    contest_type, max_questions, max_pages, max_figures, user_notes = show_menu()

    # === Load files ===
    problem_dirs = sorted([d for d in PROBLEMS_DIR.iterdir()
                           if d.is_dir() and not d.name.startswith('.')])
    if not problem_dirs: print("ERROR: No problems"); sys.exit(1)
    selected = problem_dirs[0]
    out_dir = OUTPUT_DIR / selected.name; out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir = out_dir / "figures"; fig_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Output: {out_dir}\n")

    problem_text = ""; data_files = {}; file_list = []
    for f in sorted(selected.iterdir()):
        s = f.suffix.lower()
        if s == '.txt': problem_text = f.read_text(encoding='utf-8')
        elif s == '.pdf':
            try:
                import pdfplumber
                with pdfplumber.open(str(f)) as pdf:
                    problem_text = '\n\n'.join(p.extract_text() or "" for p in pdf.pages)
            except: problem_text = f"PDF file: {f.name}"
        elif s in ('.xlsx', '.xls'):
            df = pd.read_excel(f)
            data_files[f.name] = df; file_list.append(f.name)
            print(f"  [data] {f.name} {df.shape}")
        elif s == '.csv':
            df = pd.read_csv(f, low_memory=True)
            data_files[f.name] = df; file_list.append(f.name)
            print(f"  [data] {f.name} {df.shape}")
    print(f"  Files: {file_list}\n  Problem text: {len(problem_text)} chars\n")

    if not problem_text:
        print("  WARNING: No problem text found (PDF/TXT). Will analyze data only.")
        problem_text = f"数据分析任务。数据文件: {file_list}。请分析数据结构，识别变量关系，给出统计描述和有意义的可视化。"

    # Build complete context for AI
    all_data_desc = ""
    for name, df in data_files.items():
        all_data_desc += f"\n{'='*50}\nFILE: {name} ({df.shape[0]}x{df.shape[1]})\n"
        all_data_desc += f"Columns: {list(df.columns)}\n"
        all_data_desc += f"Dtypes:\n{df.dtypes.to_string()}\n"
        all_data_desc += f"First 20 rows:\n{df.head(20).to_string()}\n"
        all_data_desc += f"Describe:\n{df.describe().to_string()}\n"
        all_data_desc += f"NaN count: {df.isnull().sum().sum()}\n"

    full_context = f"PROBLEM:\n{problem_text}\n\nDATA FILES:\n{all_data_desc}"
    if user_notes: full_context += f"\n\nUSER REQUIREMENTS:\n{user_notes}"

    # === AI: Figure out how many sub-problems ===
    print("=" * 40)
    print("  AI analyzing problem structure...")
    sub_analysis = ai.ask(
        "Read this math modeling problem. How many sub-problems (问题1/2/3/4) are there? "
        "For each: what type (优化/预测/评价/统计/分类)? what data file? what method? "
        "Return as: Q1: type=优化, file=附件1.xlsx, method=TSP. One per line.",
        full_context[:15000], max_tok=2000)
    print(f"  AI: {sub_analysis[:500]}")

    # Parse sub-problem count from AI response
    sub_count = min(max_questions, sum(1 for line in sub_analysis.split('\n') if line.strip().startswith('Q')))
    if sub_count < 1: sub_count = min(max_questions, 2)
    print(f"  Detected {sub_count} sub-problems\n")

    # === AI: Solve each sub-problem ===
    all_results = {}
    for q in range(1, sub_count + 1):
        print("=" * 40)
        print(f"  Q{q}: AI writing solution code (up to 25 rounds)...")

        last_code = ""; last_output = ""
        for r in range(1, 26):  # 25 rounds max
            print(f"  Round {r}/25", end=" ")

            if r == 1:
                prompt = f"""Solve sub-problem {q}. Write a COMPLETE Python script.
The script must:
- Read data from these files in the current directory: {file_list}
- Use ONLY: numpy, scipy, pandas, matplotlib, sklearn (NO networkx/cvxpy/ortools)
- Print all key numerical results clearly
- Save at least 4 figures to {fig_dir}/sub_{q}_fig_{{n}}.pdf
  - Figures: Chinese labels, academic colors, dpi=300, figsize(10,6)
  - Set font: plt.rcParams['font.sans-serif']=['SimHei','Microsoft YaHei','DejaVu Sans']
- Be complete and executable (python script.py should work)

{full_context[:20000]}"""
            else:
                prompt = f"""Previous attempt failed or needs improvement. Output was:
{last_output[:4000]}

Fix ALL issues and write a complete corrected Python script.
Sub-problem {q}. Same requirements as before.
Save figures to {fig_dir}/sub_{q}_fig_{{n}}.pdf
Current directory has these files: {file_list}"""

            code = ai.extract_code(ai.ask(
                "You are a math modeling Python expert. Write complete, working code.",
                prompt, max_tok=8000))
            if len(code) < 200:
                print("(too short)")
                continue

            output = ai.run_code(code, f"q{q}_r{r}", str(Path(__file__).parent))
            last_code = code; last_output = output
            ok = "Traceback" not in output and "ModuleNotFoundError" not in output and "Error" not in output.split('\n')[0]

            print(f"({len(code)} chars, {'OK' if ok else 'ERR'})")

            if ok:
                # AI checks if results are reasonable
                check = ai.ask(
                    "Check these results. Are the numbers reasonable? Reply PASS if acceptable, or explain what's wrong.",
                    f"Sub-problem {q}:\n{output[:3000]}", max_tok=500)
                if "PASS" in check:
                    print(f"  Q{q}: Solution accepted after {r} rounds")
                    break

        all_results[f"sub_{q}"] = {
            "code": last_code, "output": last_output,
            "rounds": r, "summary": last_output[:800]
        }

    # === AI: Write paper ===
    print("\n" + "=" * 40)
    print("  AI writing paper...")

    result_summary = "\n".join(
        f"Q{q}: {all_results.get(f'sub_{q}',{}).get('output','')[:500]}"
        for q in range(1, sub_count + 1))

    ai_content = {}

    # Abstract (3 rounds)
    abs_text = ai.ask("Write a 400-500 word abstract for a CUMCM paper. Chinese. Include problem summary, methods, and key numerical results.",
                      f"Problem:\n{problem_text[:2000]}\nResults:\n{result_summary}", max_tok=4000)
    for _ in range(2):
        abs_text = ai.ask("Review and rewrite this abstract to be better. More precise numbers, clearer logic.",
                          f"Current:\n{abs_text[:3000]}", max_tok=4000)
    ai_content["abstract"] = abs_text; print(f"  Abstract: {len(abs_text)} chars")

    # Each question section (2 rounds each)
    for q in range(1, sub_count + 1):
        r = all_results.get(f"sub_{q}", {})
        sec = ai.ask(
            f"Write the 'Model and Solution for Question {q}' section (500-800 words, Chinese). Include problem description, mathematical model, solution method, and specific numerical results.",
            f"Results:\n{r.get('output','')[:2000]}", max_tok=4000)
        sec = ai.ask("Review and improve this section.", f"Current:\n{sec[:3000]}", max_tok=4000)
        ai_content[f"section_{q}"] = sec
        print(f"  Q{q} section: {len(sec)} chars")

    # Sensitivity + Evaluation + Conclusion
    for key, prompt in [
        ("sensitivity", "Write sensitivity analysis (300-500 words, Chinese)."),
        ("evaluation", "Write model evaluation with advantages and limitations (Chinese)."),
        ("conclusion", "Write conclusion summarizing all findings with key numbers (Chinese)."),
    ]:
        text = ai.ask(prompt, f"Results:\n{result_summary}", max_tok=4000)
        text = ai.ask("Review and improve.", f"Current:\n{text[:3000]}", max_tok=4000)
        ai_content[key] = text
        print(f"  {key}: {len(text)} chars")

    print(f"\n  Total AI calls: {ai.calls}")

    # === Generate Word paper ===
    print("\n" + "=" * 40)
    print("  Generating Word paper...")

    sub_list = [{"id": q, "title": f"Sub-problem {q}", "type": "综合"} for q in range(1, sub_count + 1)]

    try:
        from mathmodel.paper.word_writer import generate_paper
        ts = datetime.datetime.now().strftime("%H%M%S")
        paper_path = generate_paper(
            output_path=str(out_dir / f"论文_{selected.name}_{ts}.docx"),
            problem_text=problem_text,
            analysis={"sub_problems": sub_list},
            recommendations=[{"summary": "AI-Native Solving", "sub_problems": sub_list}],
            results=all_results, figures_dir=str(fig_dir), ai_content=ai_content)
        print(f"  Paper: {paper_path}")
    except Exception as e:
        print(f"  generate_paper failed: {e}")
        from docx import Document
        doc = Document()
        doc.add_heading("AI-Generated Paper", 0)
        for q in range(1, sub_count + 1):
            doc.add_heading(f"Q{q}", 1)
            doc.add_paragraph(all_results.get(f"sub_{q}", {}).get("output", "")[:1000])
        paper_path = out_dir / f"论文_{ts}.docx"; doc.save(str(paper_path))

    # === Save results ===
    json.dump({"sub_problems": sub_list, "results": {k: v.get("output","")[:1000] for k, v in all_results.items()}},
              open(out_dir / "results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2, default=str)

    print(f"\n{'='*60}")
    print(f"  DONE!")
    print(f"  Output: {out_dir}")
    print(f"  Paper:  {paper_path}")
    print(f"  Figures: {fig_dir}")
    print(f"  AI calls: {ai.calls}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
