"""MathModel Toolkit — 一个prompt出论文"""
import sys, json, subprocess, time, shutil
from pathlib import Path
import urllib.request

API_KEY = ""
try:
    from api.config import APIConfig
    API_KEY = APIConfig().api_key
except: pass
if not API_KEY:
    API_KEY = input("DeepSeek API Key: ").strip()
if not API_KEY:
    print("No API key. 在 .env 里设置 DEEPSEEK_API_KEY=sk-xxx"); sys.exit(1)

PROBLEMS_DIR = Path(__file__).parent / "problems"
OUTPUT_DIR = Path(__file__).parent / "output"

# ============================================================
# Step 1: 收集所有输入
# ============================================================
dirs = sorted([d for d in PROBLEMS_DIR.iterdir() if d.is_dir() and not d.name.startswith('.')])
if not dirs: print("把题目文件夹放到 problems/"); sys.exit(1)
problem_dir = dirs[0]
out = OUTPUT_DIR / problem_dir.name
out.mkdir(parents=True, exist_ok=True)
(out / "figures").mkdir(exist_ok=True)

# Clean output — don't reuse old results
if out.exists():
    import shutil
    for old in out.glob("ai_response.txt"): old.unlink()
    for old in out.glob("prompt.txt"): old.unlink()

print(f"\n  Problem: {problem_dir.name}")
print(f"  Output:  {out}\n")

problem_text = ""; data_text = ""
for f in sorted(problem_dir.iterdir()):
    # Skip old output files — only read problem data
    if f.name in ('ai_response.txt', 'prompt.txt', 'solver_output.txt', 'results.json',
                  'data.csv', 'solve.py') or f.name.startswith('论文_'):
        continue
    if f.suffix in ('.docx', '.doc') and '作业' in f.name:
        continue  # skip unrelated homework files
    s = f.suffix.lower()
    if s == '.txt':
        problem_text = f.read_text(encoding='utf-8')
        print(f"  [doc] {f.name} ({len(problem_text)} chars)")
    elif s == '.pdf':
        try:
            import pdfplumber
            with pdfplumber.open(str(f)) as pdf:
                problem_text = '\n\n'.join(p.extract_text() or "" for p in pdf.pages)
            print(f"  [doc] {f.name} ({len(problem_text)} chars)")
        except: print(f"  [doc] {f.name}: PDF read failed")
    elif s in ('.xlsx', '.xls', '.csv'):
        import pandas as pd
        df = pd.read_excel(f) if s != '.csv' else pd.read_csv(f)
        # Serialize data for prompt
        data_text += f"\n=== {f.name} (shape={df.shape}) ===\n"
        data_text += f"Columns: {list(df.columns)}\n"
        data_text += f"Full data:\n{df.to_string()}\n"
        # Also save clean copy for code to use
        df.to_csv(out / "data.csv", index=False)
        print(f"  [data] {f.name} {df.shape}")

if not problem_text:
    problem_text = "数据分析任务。请基于提供的数据文件进行全面分析。"

# ============================================================
# Step 2: 构建prompt并调用DeepSeek
# ============================================================
PROMPT = f"""你是数学建模竞赛专家。请基于以下题目和数据，完成三个任务。

## 题目
{problem_text[:5000]}

## 数据
{data_text[:15000]}

## 任务一：编写求解代码 (Python)
编写一个完整的Python脚本 solve.py，保存到当前目录。
要求：
- 读取数据文件 data.csv
- 完成所有子问题的求解
- 打印每个子问题的关键数值结果(print)
- 生成论文级图表到 figures/ 目录 (中文标注，dpi=300，学术配色)

## 任务二：生成论文 (LaTeX或Word结构)
用中文写一篇完整的数学建模论文。包含：
1. 标题 (20-35字)
2. 摘要 (400-500字，包含具体数值结果)
3. 关键词
4. 问题重述
5. 模型假设与符号说明
6. 每个子问题的模型建立与求解(含数学公式和结果表格)
7. 灵敏度分析
8. 模型评价与改进
9. 结论
10. 参考文献

## 任务三：解释求解结果
对每个子问题的结果进行深度解读。

---

请完整输出以上三个任务的内容。求解代码放在 ```python 块中。
论文正文直接输出。"""

print("  正在调用 DeepSeek (这可能需要2-5分钟)...")
print(f"  Prompt: {len(PROMPT)} chars\n")

# 保存prompt供手动使用
(out / "prompt.txt").write_text(PROMPT, encoding="utf-8")
print(f"  Prompt已保存到: {out / 'prompt.txt'}")

body = json.dumps({
    "model": "deepseek-chat", "temperature": 0.1, "max_tokens": 8000,
    "messages": [{"role": "system", "content": "你是数学建模竞赛专家。输出完整详细的求解代码和论文。"},
                 {"role": "user", "content": PROMPT}],
}).encode()

# 尝试直连，失败则提示代理
response_text = ""
last_error = ""

for attempt in range(5):
    try:
        req = urllib.request.Request("https://api.deepseek.com/v1/chat/completions",
            data=body, headers={"Content-Type": "application/json",
                               "Authorization": f"Bearer {API_KEY}"}, method="POST")
        with urllib.request.urlopen(req, timeout=120) as r:
            response_text = json.loads(r.read())["choices"][0]["message"]["content"]
        break
    except Exception as e:
        last_error = str(e)
        print(f"  API attempt {attempt+1}/5: {e}")
        if attempt == 0 and "10061" in str(e) or "refused" in str(e).lower():
            print("\n  ⚠ 无法连接DeepSeek API（可能被墙）")
            print("  方案1: 开全局代理后重试")
            print("  方案2: 手动复制 prompt.txt 到 DeepSeek 网页对话")
            print("  https://chat.deepseek.com\n")
        time.sleep(5)

if not response_text:
    print(f"\n  API全部失败: {last_error}")
    print(f"\n  手动方案: 打开 {out / 'prompt.txt'}")
    print(f"  复制全部内容到 https://chat.deepseek.com")
    print(f"  将回复保存为 {out / 'ai_response.txt'}")
    print(f"  然后运行: python start.py --from-file {out / 'ai_response.txt'}")
    sys.exit(1)

print(f"  Response: {len(response_text)} chars\n")

# ============================================================
# 支持从文件读AI回复 (手动模式)
# ============================================================
FROM_FILE = None
for i, a in enumerate(sys.argv):
    if a == "--from-file" and i + 1 < len(sys.argv):
        FROM_FILE = Path(sys.argv[i + 1])

if FROM_FILE and FROM_FILE.exists():
    print(f"  从文件读取AI回复: {FROM_FILE}")
    response_text = FROM_FILE.read_text(encoding="utf-8")

# ============================================================
# Step 3: 提取代码并执行
# ============================================================
code = ""
if "```python" in response_text:
    code = response_text.split("```python")[1].split("```")[0].strip()
elif "```" in response_text:
    for part in response_text.split("```")[1::2]:
        if len(part) > 200 and ("import" in part or "def " in part or "print" in part):
            code = part.strip(); break

if code:
    print(f"  Executing solver ({len(code)} chars)...")
    code_path = out / "solve.py"
    code_path.write_text(code, encoding="utf-8")
    try:
        r = subprocess.run([sys.executable, str(code_path)],
            capture_output=True, text=True, timeout=300,
            cwd=str(out), encoding='utf-8', errors='replace')
        solver_output = r.stdout + "\n" + r.stderr
        print(f"  Solver output: {solver_output[:500]}...")
    except Exception as e:
        solver_output = f"Execution error: {e}"
        print(f"  Solver: {e}")
else:
    solver_output = "(No executable code found in response)"
    print("  No code found in response")

# ============================================================
# Step 4: 保存论文
# ============================================================
paper_part = response_text
for marker in ["```python", "```"]:
    if marker in paper_part:
        parts = paper_part.split(marker)
        paper_part = parts[0] + "\n".join(p.split("```")[1] if "```" in p else p for p in parts[1:])

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()
section = doc.sections[0]
section.page_width = Cm(21); section.page_height = Cm(29.7)
section.top_margin = Cm(2.54); section.bottom_margin = Cm(2.54)
section.left_margin = Cm(3.18); section.right_margin = Cm(3.18)

# Title
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = title.add_run(problem_dir.name)
r.bold = True; r.font.size = Pt(18)

# Parse paper sections from response
lines = paper_part.split('\n')
current_section = []
in_code_block = False
for line in lines:
    if line.strip().startswith('```'): in_code_block = not in_code_block; continue
    if in_code_block: continue
    if line.strip().startswith('#') and len(line.strip()) > 2:
        if current_section:
            p = doc.add_paragraph(); p.add_run('\n'.join(current_section))
            current_section = []
        h = doc.add_paragraph(); r = h.add_run(line.strip('# ').strip())
        r.bold = True; r.font.size = Pt(14)
    else:
        if line.strip():
            current_section.append(line)

if current_section:
    doc.add_paragraph('\n'.join(current_section))

# Add solver output as appendix
doc.add_paragraph()
h = doc.add_paragraph(); r = h.add_run("附录：求解输出"); r.bold = True; r.font.size = Pt(14)
p = doc.add_paragraph(); p.add_run(solver_output[:5000]).font.size = Pt(9)

# Embed figures
fig_dir = out / "figures"
figs = sorted(list(fig_dir.glob("*.pdf")) + list(fig_dir.glob("*.png")))
if figs:
    doc.add_paragraph()
    h = doc.add_paragraph(); r = h.add_run("附录：图表"); r.bold = True; r.font.size = Pt(14)
    for i, f in enumerate(figs, 1):
        try:
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run(f"图{i}: {f.stem}").font.size = Pt(10)
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture(str(f), width=Cm(14))
        except: pass

import datetime
ts = datetime.datetime.now().strftime("%H%M%S")
paper_path = out / f"论文_{ts}.docx"
doc.save(str(paper_path))

# Save full response
(out / "ai_response.txt").write_text(response_text, encoding="utf-8")
(out / "solver_output.txt").write_text(solver_output, encoding="utf-8")

print(f"\n{'='*60}")
print(f"  DONE!")
print(f"  Paper: {paper_path}")
print(f"  Code:  {out / 'solve.py'}")
print(f"  Figures: {fig_dir}")
print(f"  Response: {out / 'ai_response.txt'} ({len(response_text)} chars)")
print(f"  Solver: {out / 'solver_output.txt'}")
print(f"{'='*60}")
