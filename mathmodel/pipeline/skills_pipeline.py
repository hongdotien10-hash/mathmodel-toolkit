"""Skills六阶段管线 — 5M token预算, 每问10分钟
Stage 1: 分析(50 calls) → Stage 2: 建模(20) → Stage 3: 编码(15)
→ Stage 4: 图表(20) → Stage 5: 写作(60) → Stage 6: 验证(30)"""
import json, urllib.request, time, sys, subprocess, tempfile
from pathlib import Path
import numpy as np


class SkillsPipeline:
    """6阶段管线，目标5M token/篇，每问10分钟"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.calls = 0
        self.total_in = 0
        self.total_out = 0
        self.ctx = ""  # global context built up over stages

    def _call(self, system: str, user: str, max_tok: int = 8000) -> str:
        body = json.dumps({
            "model": "deepseek-chat", "temperature": 0.1, "max_tokens": max_tok,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": self.ctx + "\n\n" + user}],
        }).encode()
        req = urllib.request.Request("https://api.deepseek.com/v1/chat/completions",
            data=body, headers={"Content-Type": "application/json",
                               "Authorization": f"Bearer {self.api_key}"}, method="POST")
        for _ in range(3):
            try:
                with urllib.request.urlopen(req, timeout=300) as r:
                    self.calls += 1
                    text = json.loads(r.read())["choices"][0]["message"]["content"]
                    self.total_in += len(system + self.ctx + user) // 3
                    self.total_out += len(text) // 3
                    return text
            except: time.sleep(5)
        return ""

    def _n(self, msg=""):
        """打印阶段统计"""
        total = (self.total_in + self.total_out) // 1000
        print(f"  [{msg}] {self.calls} calls, {total}K tokens ({self.total_in//1000}K in + {self.total_out//1000}K out)")

    # ================================================================
    # Stage 1: 深度分析 (50 calls)
    # ================================================================

    def stage1_analyze(self, problem_text: str, data_files: dict) -> dict:
        """50次API调用深度分析题目和数据"""

        # Build data context
        data_str = ""
        for name, df in data_files.items():
            if name.endswith("_norm"): continue
            data_str += f"\n{'='*40}\n文件: {name} ({df.shape[0]}x{df.shape[1]})\n"
            data_str += f"列: {list(df.columns)}\n类型:\n{df.dtypes.to_string()}\n"
            data_str += f"前15行:\n{df.head(15).to_string()}\n"
            data_str += f"统计:\n{df.describe().to_string()}\n"
            data_str += f"缺失: {df.isnull().sum().sum()}个\n"

        self.ctx = f"## 完整题目\n{problem_text}\n\n## 全部数据\n{data_str}"
        out = {}

        print("  [Stage 1/6] Deep Analysis (50 calls)")

        # 1.1 Multi-perspective reading (15 calls)
        for i in range(5):
            out[f'perspective_{i}'] = self._call(
                f"你是数学建模专家视角{i+1}。仔细阅读题目和数据，从不同角度分析。",
                f"这是第{i+1}轮分析，请从前几轮中获取灵感但提出新的见解。", max_tok=8000)
        self._n("1.1 perspectives")

        # 1.2 Cross-review perspectives (15 calls)
        for i in range(5):
            prev = "\n".join(str(out.get(f'perspective_{j}', ''))[:500] for j in range(5) if j != i)
            out[f'review_{i}'] = self._call(
                "审阅其他视角的分析。指出遗漏、错误、更好的方法。批判性思维。",
                f"其他视角:\n{prev}\n你的视角:\n{out.get(f'perspective_{i}','')[:2000]}", max_tok=8000)
        self._n("1.2 cross-review")

        # 1.3 Problem decomposition (10 calls)
        for i in range(5):
            out[f'decomp_{i}'] = self._call(
                "将题目拆解为子问题。识别每个子问题的类型、数据需求、推荐模型。",
                f"分析:\n{json.dumps({k: str(v)[:500] for k,v in out.items()}, ensure_ascii=False)[:4000]}", max_tok=8000)
        self._n("1.3 decomposition")

        # 1.4 Synthesis (10 calls)
        for i in range(5):
            out[f'synthesis_{i}'] = self._call(
                "综合所有分析，给出最终的题目理解和求解策略。",
                f"所有分析:\n{json.dumps({k: str(v)[:300] for k,v in out.items()}, ensure_ascii=False)[:5000]}", max_tok=8000)
        for i in range(5):
            out[f'synth_review_{i}'] = self._call(
                "审阅综合结果。找出矛盾、遗漏、改进空间。",
                f"综合:\n{out.get(f'synthesis_{i}','')[:3000]}", max_tok=8000)
        self._n("1.4 synthesis")

        # Store key findings
        self.ctx += f"\n\n## Stage 1 Analysis Results\n{json.dumps({k: str(v)[:500] for k,v in out.items()}, ensure_ascii=False)[:5000]}"
        return out

    # ================================================================
    # Stage 2: 建模设计 (20 calls)
    # ================================================================

    def stage2_model(self, sub_count: int) -> dict:
        """20 calls — 为每个子问题设计数学模型"""
        print("  [Stage 2/6] Model Design (20 calls)")
        out = {}

        for q in range(1, sub_count + 1):
            for i in range(10):
                out[f'q{q}_model_{i}'] = self._call(
                    f"为子问题{q}设计数学模型。包括: 变量定义、目标函数、约束条件、"
                    f"推荐算法、预期输出。每次尝试不同的建模角度。",
                    f"这是第{i+1}次尝试。前几次:\n"
                    f"{json.dumps({k: str(v)[:300] for k,v in out.items() if f'q{q}' in k}, ensure_ascii=False)[:3000]}",
                    max_tok=8000)
        self._n("2. modeling")
        self.ctx += f"\n\n## Models\n{json.dumps({k: str(v)[:300] for k,v in out.items()}, ensure_ascii=False)[:3000]}"
        return out

    # ================================================================
    # Stage 3: 编程验证 (15 calls)
    # ================================================================

    def stage3_code(self, sub_count: int, fig_dir: str) -> dict:
        """15 calls — AI写验证代码确认求解器结果"""
        print("  [Stage 3/6] Code Verification (15 calls)")
        out = {}

        for q in range(1, sub_count + 1):
            for i in range(8):  # 8 attempts
                code = self._call(
                    "写Python代码验证子问题的求解结果。读数据→计算→验证数值→生成对比图。"
                    "用numpy/scipy/pandas/matplotlib/sklearn,不要用networkx。",
                    f"子问题{q}。图表保存到 {fig_dir}/sub_{q}_verify_{i}.pdf", max_tok=8000)
                if "```python" in code:
                    code = code.split("```python")[1].split("```")[0].strip()
                # Execute
                cp = Path(tempfile.gettempdir()) / f"stage3_q{q}_{i}.py"
                cp.write_text(code, encoding="utf-8")
                try:
                    r = subprocess.run([sys.executable, str(cp)],
                        capture_output=True, text=True, timeout=120,
                        cwd=str(Path(__file__).parent.parent.parent),
                        encoding='utf-8', errors='replace')
                    out[f'q{q}_run_{i}'] = r.stdout[-2000:] + "\n" + r.stderr[-1000:]
                except: out[f'q{q}_run_{i}'] = "TIMEOUT/ERROR"
        self._n("3. coding")
        return out

    # ================================================================
    # Stage 4: 图表生成 (20 calls)
    # ================================================================

    def stage4_figures(self, sub_count: int, fig_dir: str) -> dict:
        """20 calls — AI生成专业图表"""
        print("  [Stage 4/6] Figure Generation (20 calls)")
        out = {}

        for q in range(1, sub_count + 1):
            for i in range(10):  # 10 figures per question
                code = self._call(
                    "生成一张论文级matplotlib图表。要求: figsize(10,6), dpi=300, "
                    "中文标注, 学术配色, 去除顶部右边框。保存为PDF。",
                    f"子问题{q}。保存到 {fig_dir}/sub_{q}_fig_{i}.pdf", max_tok=8000)
                if "```python" in code:
                    code = code.split("```python")[1].split("```")[0].strip()
                cp = Path(tempfile.gettempdir()) / f"stage4_q{q}_{i}.py"
                cp.write_text(code, encoding="utf-8")
                try:
                    subprocess.run([sys.executable, str(cp)],
                        capture_output=True, text=True, timeout=60,
                        cwd=str(Path(__file__).parent.parent.parent),
                        encoding='utf-8', errors='replace')
                    fp = Path(fig_dir) / f"sub_{q}_fig_{i}.pdf"
                    if fp.exists():
                        out[f'q{q}_fig_{i}'] = f"OK {fp.stat().st_size} bytes"
                    else: out[f'q{q}_fig_{i}'] = "NOT FOUND"
                except: out[f'q{q}_fig_{i}'] = "ERROR"
        self._n("4. figures")
        return out

    # ================================================================
    # Stage 5: 论文写作 (60 calls)
    # ================================================================

    def stage5_write(self, problem_text: str, sub_count: int, results: dict) -> dict:
        """60 calls — 逐段写论文+多轮打磨"""
        print("  [Stage 5/6] Paper Writing (60 calls)")

        result_str = "\n".join(f"Q{q}: {results.get(f'sub_{q}',{}).get('summary','')[:300]}"
                               for q in range(1, sub_count + 1))
        out = {}

        # Title (3 calls)
        out['title'] = self._call("生成论文标题(20-35字,中文)。", f"结果:\n{result_str}", max_tok=200)
        for _ in range(2):
            out['title'] = self._call("改进标题。更精准更有力。", f"原标题:\n{out['title']}", max_tok=200)

        # Abstract (8 calls: 4 drafts + 4 reviews)
        for i in range(4):
            out[f'abstract_v{i}'] = self._call("写400-500字摘要。", f"结果:\n{result_str}", max_tok=4000)
            out[f'abstract_r{i}'] = self._call("审阅摘要。指出问题。",
                f"摘要:\n{out[f'abstract_v{i}'][:3000]}", max_tok=1000)
        out['abstract'] = out.get('abstract_v3', out.get('abstract_v0', ''))

        # Each question section (8 calls × 2Q = 16)
        for q in range(1, sub_count + 1):
            r = results.get(f'sub_{q}', {})
            for i in range(4):
                out[f'q{q}_v{i}'] = self._call(
                    f"写问题{q}的模型建立与求解(500-800字)。",
                    f"结果: {str(r)[:2000]}", max_tok=4000)
                out[f'q{q}_r{i}'] = self._call("审阅并指出改进点。",
                    f"章节:\n{out[f'q{q}_v{i}'][:3000]}", max_tok=1000)
            out[f'section_{q}'] = out.get(f'q{q}_v3', out.get(f'q{q}_v0', ''))

        # Sensitivity (6 calls)
        for i in range(3):
            out[f'sens_v{i}'] = self._call("写灵敏度分析(300-500字)。", f"结果:\n{result_str}", max_tok=4000)
            out[f'sens_r{i}'] = self._call("审阅灵敏度分析。", f"分析:\n{out[f'sens_v{i}'][:3000]}", max_tok=1000)
        out['sensitivity'] = out.get('sens_v2', '')

        # Evaluation (6 calls)
        for i in range(3):
            out[f'eval_v{i}'] = self._call("写模型评价(优点+不足)。", f"结果:\n{result_str}", max_tok=4000)
            out[f'eval_r{i}'] = self._call("审阅评价。", f"评价:\n{out[f'eval_v{i}'][:3000]}", max_tok=1000)
        out['evaluation'] = out.get('eval_v2', '')

        # Conclusion (6 calls)
        for i in range(3):
            out[f'concl_v{i}'] = self._call("写结论(300-400字)。", f"结果:\n{result_str}", max_tok=4000)
            out[f'concl_r{i}'] = self._call("审阅结论。", f"结论:\n{out[f'concl_v{i}'][:3000]}", max_tok=1000)
        out['conclusion'] = out.get('concl_v2', '')

        # Full review and polish (5 calls)
        all_text = "\n\n".join(f"{k}: {str(v)[:500]}" for k, v in out.items() if 'v' in k[-3:])
        for i in range(5):
            out[f'polish_{i}'] = self._call("审阅全文。找矛盾、冗余、缺失。修改建议。",
                f"全文:\n{all_text[:8000]}", max_tok=4000)

        self._n("5. writing")
        return out

    # ================================================================
    # Stage 6: 验证 (30 calls)
    # ================================================================

    def stage6_verify(self, sub_count: int, results: dict, paper: dict) -> dict:
        """30 calls — 全面验证论文质量"""
        print("  [Stage 6/6] Verification (30 calls)")
        out = {}
        result_str = "\n".join(f"Q{q}: {results.get(f'sub_{q}',{}).get('summary','')[:300]}"
                               for q in range(1, sub_count + 1))

        # Numerical consistency (10 calls)
        for i in range(10):
            out[f'num_{i}'] = self._call(
                "检查论文中所有数值是否前后一致。摘要/每问/结论中的数字是否有矛盾。",
                f"论文:\n{json.dumps({k: str(v)[:500] for k,v in paper.items()}, ensure_ascii=False)[:6000]}\n"
                f"原始结果:\n{result_str}", max_tok=4000)

        # Quality scoring (10 calls)
        for i in range(10):
            out[f'score_{i}'] = self._call(
                f"从维度{i%5+1}/5给论文打分(0-100): "
                f"{['模型正确性','求解深度','图表质量','写作水平','整体结构'][i%5]}。",
                f"论文:\n{json.dumps({k: str(v)[:300] for k,v in paper.items()}, ensure_ascii=False)[:4000]}",
                max_tok=2000)

        # Final check (10 calls)
        for i in range(10):
            out[f'final_{i}'] = self._call(
                "最终检查: 图表引用是否正确? 公式编号是否连续? 参考文献是否齐全? 语言是否流畅?",
                f"论文:\n{json.dumps({k: str(v)[:300] for k,v in paper.items()}, ensure_ascii=False)[:4000]}",
                max_tok=4000)

        self._n("6. verify")
        return out

    # ================================================================
    # Run full pipeline
    # ================================================================

    def run(self, problem_text: str, data_files: dict, fig_dir: str, results: dict,
            sub_count: int = 2) -> dict:
        """运行完整6阶段管线"""
        print(f"\n{'='*60}")
        print(f"  Skills Pipeline — 6 Stages, ~5M tokens target")
        print(f"{'='*60}")

        s1 = self.stage1_analyze(problem_text, data_files)
        s2 = self.stage2_model(sub_count)
        s3 = self.stage3_code(sub_count, fig_dir)
        s4 = self.stage4_figures(sub_count, fig_dir)
        s5 = self.stage5_write(problem_text, sub_count, results)
        s6 = self.stage6_verify(sub_count, results, s5)

        total = (self.total_in + self.total_out) // 1000
        print(f"\n  PIPELINE DONE: {self.calls} calls, {total}K tokens")
        return {"analysis": s1, "model": s2, "code": s3, "figures": s4,
                "paper": s5, "verify": s6}
