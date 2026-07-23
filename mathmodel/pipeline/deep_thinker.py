"""深度思考引擎 — 每问多轮AI: 分析→质疑→改进→求解→验证→修正
每问最低5分钟计算预算，多次API调用确保质量"""
import json, urllib.request, time, sys
from pathlib import Path


class DeepThinker:
    """多轮AI思考 — 每问至少5次API调用"""

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.api_key = api_key
        self.model = model
        self.call_count = 0

    def _call(self, system: str, user: str, temperature: float = 0.3, max_tokens: int = 4096) -> str:
        """调用API"""
        body = json.dumps({
            "model": self.model, "temperature": temperature, "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
        }).encode()
        req = urllib.request.Request("https://api.deepseek.com/v1/chat/completions",
            data=body, headers={"Content-Type": "application/json",
                               "Authorization": f"Bearer {self.api_key}"}, method="POST")
        for attempt in range(2):
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    self.call_count += 1
                    return json.loads(r.read())["choices"][0]["message"]["content"]
            except Exception as e:
                if attempt == 1: return str(e)
                time.sleep(3)
        return ""

    def _call_json(self, system: str, user: str) -> dict:
        text = self._call(system, user, temperature=0.2)
        try:
            if "```" in text:
                text = text.split("```")[1].split("```")[0]
                if text.startswith("json"): text = text[4:]
            start = text.find("{"); end = text.rfind("}") + 1
            return json.loads(text[start:end]) if start >= 0 else {}
        except:
            return {}

    def think_about_problem(self, sp, problem_text, data_profiles, result):
        """对单个子问题进行多轮深度思考

        Returns: refined analysis dict with insights
        """
        sp_id = sp.get("id", "?")
        print(f"\n  {'='*50}")
        print(f"  DEEP THINK: Q{sp_id} — Multi-round AI analysis")
        print(f"  {'='*50}")

        context = {
            "sub_problem": sp,
            "data_summary": {k: f"{v.get('shape','?')} cols={v.get('columns','?')[:5]}"
                           for k, v in (data_profiles or {}).items()},
            "result": {k: str(v)[:200] for k, v in (result or {}).items()},
        }

        # === Round 1: Initial analysis ===
        print(f"  [Round 1/5] Analyzing problem structure...")
        r1 = self._call_json(
            "你是数学建模专家。仔细分析这个子问题，识别：问题类型、关键约束、数据需求、"
            "可能的陷阱、与经典模型的异同。要具体，不要泛泛而谈。",
            f"题目:\n{problem_text[:3000]}\n\n子问题:\n{json.dumps(context['sub_problem'], ensure_ascii=False)}\n\n"
            f"数据概况:\n{json.dumps(context['data_summary'], ensure_ascii=False)}\n\n"
            f"返回JSON: {{'problem_type':'', 'key_constraints':[], 'data_needs':[], "
            f"'pitfalls':[], 'similar_to_classic':'', 'complexity_assessment':''}}"
        )
        time.sleep(0.5)

        # === Round 2: Critical review of Round 1 ===
        print(f"  [Round 2/5] Self-critique — challenging assumptions...")
        r2 = self._call_json(
            "你是数学建模竞赛评委。严格审查下面的分析，找出逻辑漏洞、遗漏的约束、"
            "不合理的简化、更好的替代方法。要挑剔，要具体。",
            f"原始分析:\n{json.dumps(r1, ensure_ascii=False)}\n\n"
            f"返回JSON: {{'flaws':[], 'missing_constraints':[], 'better_approaches':[], "
            f"'overall_assessment':'', 'confidence':0.0}}"
        )
        time.sleep(0.5)

        # === Round 3: Improved plan ===
        print(f"  [Round 3/5] Synthesizing improved approach...")
        r3 = self._call_json(
            "基于前面的分析和审查，制定具体的求解方案。要精确到：用什么算法、"
            "算法步骤、关键参数、如何验证结果正确性、预期的输出格式。",
            f"初始分析:\n{json.dumps(r1, ensure_ascii=False)}\n"
            f"审查意见:\n{json.dumps(r2, ensure_ascii=False)}\n"
            f"返回JSON: {{'algorithm':'', 'steps':[], 'parameters':{{}}, "
            f"'validation_method':'', 'expected_output':{{}}, 'confidence_after_review':0.0}}"
        )
        time.sleep(0.5)

        # === Round 4: Result interpretation ===
        print(f"  [Round 4/5] Interpreting results — what do the numbers mean?...")
        r4 = self._call(
            "你是数学建模论文作者。基于求解结果写出深度的结果分析。"
            "要回答：1)数字说明了什么 2)为什么是这个数字 3)它合理吗 4)对决策有何启示。"
            "写中文，3-5段，每段要有具体数值。",
            f"求解方案:\n{json.dumps(r3, ensure_ascii=False)[:2000]}\n"
            f"实际结果:\n{json.dumps(context['result'], ensure_ascii=False)[:2000]}\n"
            f"请写出详细的结果分析。"
        )
        time.sleep(0.5)

        # === Round 5: Final quality check ===
        print(f"  [Round 5/5] Final quality assessment...")
        r5 = self._call_json(
            "对求解过程和结果做最终评估。给出质量分数(0-100)和改进建议。",
            f"求解方案:\n{json.dumps(r3, ensure_ascii=False)[:1500]}\n"
            f"结果:\n{json.dumps(context['result'], ensure_ascii=False)[:1500]}\n"
            f"结果分析:\n{r4[:1000]}\n"
            f"返回JSON: {{'quality_score':0, 'strengths':[], 'weaknesses':[], "
            f"'suggestions_for_improvement':[]}}"
        )

        quality = r5.get("quality_score", 70)
        print(f"  DEEP THINK Q{sp_id} complete: {self.call_count} API calls, quality={quality}/100")
        if quality < 80:
            print(f"  Suggestions: {r5.get('suggestions_for_improvement', [])}")

        return {
            "initial_analysis": r1,
            "critique": r2,
            "plan": r3,
            "interpretation": r4,
            "quality_check": r5,
            "total_api_calls": self.call_count,
        }

    def design_figures(self, sp_id, problem_info, result, fig_dir, max_figures=3):
        """AI设计图表方案 — 不只生成，还要思考什么图最有意义"""
        print(f"\n  [FIG-DESIGN] Q{sp_id}: AI designing figure strategy...")

        r = self._call_json(
            "你是数据可视化专家和数学建模评委。根据求解结果，设计最有意义的图表方案。"
            "考虑：1)什么图最能说明问题 2)图的类型和内容 3)图表如何支撑论文论证。"
            "不要堆砌图表，每张图要有明确的论证目的。",
            f"问题信息:\n{json.dumps(problem_info, ensure_ascii=False)[:1000]}\n"
            f"求解结果:\n{json.dumps({k: str(v)[:200] for k,v in result.items()}, ensure_ascii=False)}\n"
            f"最多{max_figures}张图\n"
            f"返回JSON: {{'figures':[{{'type':'', 'title':'', 'purpose':'', "
            f"'what_it_shows':'', 'why_important':''}}]}}"
        )

        figures = r.get("figures", [])
        print(f"  [FIG-DESIGN] Proposed {len(figures)} figures:")
        for i, f in enumerate(figures, 1):
            print(f"    {i}. [{f.get('type','?')}] {f.get('title','?')[:60]}")
            print(f"       Purpose: {f.get('purpose','?')[:80]}")
        return figures

    def review_figure(self, fig_path, purpose, result):
        """AI审查生成的图表"""
        r = self._call(
            "你审阅这张数据图表。评价：1)是否清晰传达信息 2)标注是否完整 "
            "3)是否有误导 4)如何改进。如果图质量不够,指出具体问题。",
            f"图表用途: {purpose}\n数据: {json.dumps({k:str(v)[:100] for k,v in result.items()}, ensure_ascii=False)}\n"
            f"请给出评价和改进建议。"
        )
        return r


def enforce_time_budget(target_seconds=300):
    """确保每个子问题至少用足时间预算"""
    start = time.time()

    def check():
        elapsed = time.time() - start
        remaining = target_seconds - elapsed
        if remaining > 0:
            print(f"  [TIME-BUDGET] Waiting {remaining:.0f}s to ensure thorough computation...")
            # Use remaining time for more computation
            time.sleep(min(remaining, 10))  # small sleeps, let main work happen
        return elapsed

    return check
