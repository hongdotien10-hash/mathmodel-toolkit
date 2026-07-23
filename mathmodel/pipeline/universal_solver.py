"""通用AI求解器 — 不预设任何模型，AI全权决定求解策略
适用于任何国赛题: 优化/预测/评价/统计/分类/微分方程/图论
流程: AI读题→AI分析→AI写代码→执行→AI审查→修正→直到正确"""
import json, urllib.request, time, sys, subprocess, tempfile, os
from pathlib import Path


class UniversalSolver:
    """AI全权驱动 — 不硬编码任何求解逻辑"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.calls = 0

    def _call(self, system: str, user: str, max_tok: int = 8000) -> str:
        body = json.dumps({
            "model": "deepseek-chat", "temperature": 0.1, "max_tokens": max_tok,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
        }).encode()
        req = urllib.request.Request("https://api.deepseek.com/v1/chat/completions",
            data=body, headers={"Content-Type": "application/json",
                               "Authorization": f"Bearer {self.api_key}"}, method="POST")
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=300) as r:
                    self.calls += 1
                    return json.loads(r.read())["choices"][0]["message"]["content"]
            except Exception as e:
                if attempt == 2: return ""
                time.sleep(5)
        return ""

    def _extract_code(self, text: str) -> str:
        if "```python" in text:
            return text.split("```python")[1].split("```")[0].strip()
        elif "```" in text:
            return text.split("```")[1].split("```")[0].strip()
        return text.strip()

    # ================================================================
    # Step 1: AI完整分析题目和数据
    # ================================================================

    def analyze_problem(self, problem_text: str, data_files: dict) -> dict:
        """AI读取完整题目和全部数据，分析所有子问题"""
        # Build comprehensive data description
        data_desc = ""
        for name, df in data_files.items():
            if name.endswith("_norm"): continue
            data_desc += f"\n=== 文件: {name} (.xlsx/.csv) ===\n"
            data_desc += f"Shape: {df.shape}\n"
            data_desc += f"列名: {list(df.columns)}\n"
            data_desc += f"数据类型:\n{df.dtypes.to_string()}\n"
            data_desc += f"前10行:\n{df.head(10).to_string()}\n"
            data_desc += f"统计描述:\n{df.describe().to_string()}\n"
            data_desc += f"缺失值:\n{df.isnull().sum().to_string()}\n\n"

        # Round 1: Initial analysis
        print("  [ANALYZE 1/4] AI reading problem and data...")
        r1 = self._call(
            """你是数学建模竞赛专家。仔细阅读完整题目和全部数据文件。
识别: 1)所有子问题及其类型 2)每个子问题应该用什么模型/算法
3)数据如何对应每个子问题 4)关键约束和参数
返回结构化分析。""",
            f"## 完整题目\n{problem_text}\n\n## 全部数据\n{data_desc[:15000]}",
            max_tok=8000)

        # Round 2: Deeper analysis with self-review
        print("  [ANALYZE 2/4] Deepening analysis...")
        r2 = self._call(
            "基于初步分析，深入思考每个子问题的数学本质。"
            "对于每个子问题: 1)精确的数学描述 2)最合适的算法(具体到算法名) "
            "3)为什么选这个算法 4)有没有更好的替代方案 5)预期结果的范围",
            f"初步分析:\n{r1[:4000]}\n数据:\n{data_desc[:5000]}",
            max_tok=8000)

        # Round 3: Review and refine
        print("  [ANALYZE 3/4] Self-review and refinement...")
        r3 = self._call(
            "严格审查上面的分析。找出: 逻辑漏洞、遗漏的约束条件、不合理的假设、"
            "更好的替代方案。然后给出修正后的最终分析。",
            f"分析:\n{r2[:5000]}\n题目:\n{problem_text[:3000]}",
            max_tok=8000)

        # Round 4: Generate structured plan
        print("  [ANALYZE 4/4] Generating execution plan...")
        r4 = self._call(
            "基于前面的分析，生成具体的执行计划。对每个子问题写出: "
            "1)一句话摘要 2)模型类型 3)推荐算法 4)需要的数据文件 "
            "5)预期输出。用JSON格式。",
            f"最终分析:\n{r3[:5000]}\n数据:\n{data_desc[:3000]}",
            max_tok=8000)

        return {"initial": r1, "deep": r2, "refined": r3, "plan": r4}

    # ================================================================
    # Step 2: AI为每个子问题写代码并循环改进
    # ================================================================

    def solve_sub_problem(self, sp_id: int, sp_desc: str, data_files: dict,
                          fig_dir: str, max_rounds: int = 20) -> dict:
        """AI写代码求解一个子问题，循环改进"""

        # Build data description
        data_desc = ""
        for name, df in data_files.items():
            if name.endswith("_norm"): continue
            data_desc += f"\n文件'{name}' ({df.shape[0]}行×{df.shape[1]}列):\n"
            data_desc += f"列名: {list(df.columns)}\n"
            data_desc += f"前5行:\n{df.head(5).to_string()}\n"

        code = ""; last_output = ""; rounds = []

        for r in range(1, max_rounds + 1):
            print(f"  [SOLVE Q{sp_id} R{r}/{max_rounds}]")

            if r == 1:
                prompt = f"""## 子问题{sp_id}
{sp_desc}

## 可用数据
{data_desc[:10000]}

## 图表保存到
{fig_dir}/sub_{sp_id}_plot_{{n}}.pdf

请写完整的Python代码求解这个问题。要求:
- 完整可执行(能直接python运行)
- 打印所有关键数值结果
- 生成至少2张专业图表(matplotlib,中文标注,学术配色,dpi=300)
- 代码长度不限,写清楚每步的注释
- 不依赖networkx/cvxpy/ortools等未安装库

只返回Python代码在```python```块中。"""
            else:
                prompt = f"""上一轮代码执行结果有问题或需要改进:

{last_output[:3000]}

请修正代码。注意:
- 如果报错,修复bug
- 如果数值不合理(负数/零/超大),修正算法
- 如果图表不好看,改进matplotlib代码
- 确保所有约束条件都被满足

只返回完整的修正后Python代码在```python```块中。"""

            response = self._call(
                "你是数学建模Python求解专家。写高质量、完整可执行的代码。",
                prompt, max_tok=8000)
            code = self._extract_code(response)
            if len(code) < 100:
                print(f"  [WARN] Code too short ({len(code)} chars), retrying")
                continue

            # Execute
            code_path = Path(tempfile.gettempdir()) / f"universal_q{sp_id}_r{r}.py"
            code_path.write_text(code, encoding="utf-8")
            try:
                result = subprocess.run(
                    [sys.executable, str(code_path)],
                    capture_output=True, text=True, timeout=180,
                    cwd=str(Path(__file__).parent.parent.parent),
                    encoding='utf-8', errors='replace')
                last_output = (result.stdout[-5000:] or "") + "\n" + (result.stderr[-3000:] or "")
                rounds.append({"round": r, "code_len": len(code),
                              "returncode": result.returncode, "output": last_output[:2000]})
                print(f"  [EXEC] Return {result.returncode}, output {len(last_output)} chars")

                if result.returncode == 0 and "ModuleNotFoundError" not in last_output:
                    # Check if results look reasonable
                    check = self._call(
                        "检查这个执行结果。数值是否合理?图表是否生成?如果一切正常回复'PASS',否则说明问题。",
                        f"输出:\n{last_output[:3000]}", max_tok=500)
                    if "PASS" in check:
                        print(f"  [PASS] Solution accepted after {r} rounds")
                        break
            except subprocess.TimeoutExpired:
                last_output = "TIMEOUT: >180s"
            except Exception as e:
                last_output = f"ERROR: {e}"

        return {"rounds": rounds, "final_code": code, "final_output": last_output}

    # ================================================================
    # Step 3: AI写完整论文
    # ================================================================

    def write_paper(self, problem_text: str, sub_problems: list, all_results: dict,
                    fig_dir: str, contest_type: str = "cumcm") -> dict:
        """AI写完整论文(摘要→每节→灵敏度→评价→结论)"""

        result_summary = ""
        for sp in sub_problems:
            sp_id = sp.get("id", "?")
            r = all_results.get(f"sub_{sp_id}", {})
            result_summary += f"Q{sp_id}: {str(r.get('summary', r))[:300]}\n"

        sections = {}

        # 标题
        print("  [PAPER] Title + Abstract")
        sections['title'] = self._call(
            "根据论文内容生成学术标题(20-35字,中文)。只返回标题。",
            f"题目:\n{problem_text[:2000]}\n结果:\n{result_summary}", max_tok=200)

        # 摘要 (3轮打磨)
        abstract = self._call(
            "写400-500字摘要。包含问题概述、每问方法+结果数字、结论。中文学术风格。",
            f"题目:\n{problem_text[:2000]}\n结果:\n{result_summary}", max_tok=4000)
        for _ in range(2):
            abstract = self._call(
                "审阅并重写此摘要使其更出色。数字要准确、逻辑要清晰、语言要流畅。",
                f"原摘要:\n{abstract[:3000]}", max_tok=4000)
        sections['abstract'] = abstract

        # 每问章节 (3轮)
        for sp in sub_problems:
            sp_id = sp.get("id", "?")
            r = all_results.get(f"sub_{sp_id}", {})
            sec = self._call(
                f"写问题{sp_id}的模型建立与求解章节(500-800字)。"
                f"包含: 问题分析、数学模型、求解方法、具体结果数字。",
                f"题目: {sp.get('title','')}\n结果: {str(r)[:2000]}", max_tok=4000)
            for _ in range(2):
                sec = self._call("审阅并重写使其更专业深入。", f"原稿:\n{sec[:3000]}", max_tok=4000)
            sections[f'model_{sp_id}'] = sec

        # 灵敏度 (2轮)
        sens = self._call(
            "写300-500字灵敏度分析。测试哪些参数、什么方法、什么结论。中文。",
            f"结果:\n{result_summary}", max_tok=4000)
        sens = self._call("审阅并重写灵敏度分析。", f"原稿:\n{sens[:3000]}", max_tok=4000)
        sections['sensitivity'] = sens

        # 评价 (2轮)
        ev = self._call("写模型评价(优点+不足+改进)。中文。", f"结果:\n{result_summary}", max_tok=4000)
        ev = self._call("审阅并重写模型评价。", f"原稿:\n{ev[:3000]}", max_tok=4000)
        sections['evaluation'] = ev

        # 结论 (2轮)
        concl = self._call(
            "写300-400字结论。逐问列出核心发现和数字。中文。",
            f"结果:\n{result_summary}", max_tok=4000)
        concl = self._call("审阅并重写结论。", f"原稿:\n{concl[:3000]}", max_tok=4000)
        sections['conclusion'] = concl

        print(f"  Paper done: {self.calls} total calls")
        return sections
