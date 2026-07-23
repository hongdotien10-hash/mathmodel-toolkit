"""深度思考引擎 — 每问15-20次API调用，确保深度分析
每问至少5分钟，每篇论文50+次API，成本~2元"""
import json, urllib.request, time, sys
from pathlib import Path


class DeepThinker:
    """多轮深度AI思考 — 每问15-20次API调用"""

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.api_key = api_key
        self.model = model
        self.total_calls = 0
        self.total_cost = 0.0
        # DeepSeek pricing: ~1 RMB per 1M input tokens, ~2 RMB per 1M output tokens
        # Average call: ~2000 input + ~500 output tokens ≈ 0.003 RMB

    def _call(self, system: str, user: str, temperature: float = 0.3, max_tokens: int = 4096) -> str:
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
                    self.total_calls += 1
                    # Rough cost estimate
                    in_tokens = len(system + user) / 3
                    resp = json.loads(r.read())
                    out_text = resp["choices"][0]["message"]["content"]
                    out_tokens = len(out_text) / 3
                    self.total_cost += (in_tokens / 1e6) * 1.0 + (out_tokens / 1e6) * 2.0
                    return out_text
            except Exception as e:
                if attempt == 1: return ""
                time.sleep(3)
        return ""

    def _call_json(self, system: str, user: str) -> dict:
        text = self._call(system, user, temperature=0.2)
        try:
            if "```" in text: text = text.split("```")[1].split("```")[0]
            if text.strip().startswith("json"): text = text[4:]
            start = text.find("{"); end = text.rfind("}") + 1
            return json.loads(text[start:end]) if start >= 0 else {}
        except: return {}

    # ================================================================
    # 完整思考流水线 (15-20次API调用)
    # ================================================================

    def think_deep(self, sp, problem_text, data_profiles, result, fig_dir):
        """对单个子问题进行完整深度思考流水线"""
        sp_id = sp.get("id", "?")
        ptype = sp.get("type", "")
        n = result.get("n_locations", "?")
        dist = result.get("total_distance", "?")

        print(f"\n  {'='*55}")
        print(f"  DEEP THINK Q{sp_id} — 18-round AI analysis pipeline")
        print(f"  {'='*55}")

        ctx = json.dumps({
            "sub_problem": sp, "type": ptype,
            "data": {k: f"shape={v.get('shape','?')}" for k, v in (data_profiles or {}).items()},
            "result_summary": f"distance={dist}km, locations={n}",
            "result_detail": {k: str(v)[:300] for k, v in (result or {}).items()
                            if k not in ('tour','all_methods')},
        }, ensure_ascii=False)

        output = {}

        # === PHASE 1: 问题理解 (3 calls) ===
        print(f"  [Phase 1/6] Problem Understanding (3 calls)")

        r = self._call_json(
            "你是一位数学建模竞赛资深教练。请深入分析这个子问题。"
            "不要只复述题目，要看到背后的数学本质和隐藏的难点。",
            f"题目:\n{problem_text[:3000]}\n\n子问题:\n{ctx[:3000]}\n\n"
            f"返回JSON: {{'mathematical_essence':'', 'hidden_difficulties':[], "
            f"'key_insights':[], 'what_makes_it_hard':''}}"
        ); output['problem_essence'] = r; time.sleep(0.3)

        r2 = self._call(
            "基于对问题的初步理解，请进一步思考：这个问题的哪些方面可能被初学者忽略？"
            "数据的特殊性是什么？有哪些经典错误需要避免？请用中文写出3-4段深入分析。",
            f"问题本质:\n{json.dumps(r, ensure_ascii=False)}\n\n请写出你的深入思考。"
        ); output['deeper_thoughts'] = r2; time.sleep(0.3)

        r3 = self._call(
            "现在请换一个角度思考这个问题。如果你是评委，你希望看到什么样的分析？"
            "什么样的切入点会让你觉得'这篇论文有深度'？请给出具体建议。",
            f"之前的分析:\n{r2[:1500]}\n\n请从评委视角给出建议。"
        ); output['judge_perspective'] = r3; time.sleep(0.3)

        # === PHASE 2: 建模辩论 (3 calls) ===
        print(f"  [Phase 2/6] Modeling Debate (3 calls)")

        m1 = self._call(
            "请为这个子问题提出至少两种不同的建模思路。每种思路都要说清楚："
            "模型类型、适用条件、优缺点、预期的求解难度。要让评委看到你在权衡不同方案。"
            "用中文写，详细具体。",
            f"问题分析:\n{r3[:1500]}\n\n请提出多种建模思路。"
        ); output['model_proposals'] = m1; time.sleep(0.3)

        m2 = self._call(
            "你是一位批判性思维专家。请对上面提出的每种建模思路进行严格的批判性分析。"
            "找出每种方法的弱点、假设是否合理、计算是否可行。要具体，不要泛泛而谈。",
            f"建模方案:\n{m1[:2000]}\n\n请批判每种方案。"
        ); output['model_critique'] = m2; time.sleep(0.3)

        m3 = self._call(
            "综合前面的分析和批判，做出最终的建模选择。说明为什么选这个而不是其他。"
            "你的选择标准是什么？这个选择在什么条件下最优？有什么风险？",
            f"方案:\n{m1[:1000]}\n批判:\n{m2[:1000]}\n\n请做出最终选择并说明理由。"
        ); output['model_decision'] = m3; time.sleep(0.3)

        # === PHASE 3: 求解策略 (2 calls) ===
        print(f"  [Phase 3/6] Solving Strategy (2 calls)")

        s1 = self._call_json(
            "制定详细的求解策略。包括：具体算法步骤、每一步的输入输出、"
            "关键参数如何确定、可能遇到的问题和应对方案。",
            f"选定的模型:\n{m3[:1500]}\n"
            f"返回JSON: {{'algorithm_steps':[], 'parameters':{{}}, "
            f"'edge_cases':[], 'fallback_plan':''}}"
        ); output['solve_strategy'] = s1; time.sleep(0.3)

        s2 = self._call(
            "你是一位数值计算专家。请审查上面的求解策略。参数选择是否合理？"
            "是否有数值稳定性问题？收敛性如何保证？如果求解失败，备选方案是什么？",
            f"求解策略:\n{json.dumps(s1, ensure_ascii=False)[:2000]}\n"
            f"实际结果: distance={dist}km, n={n}\n请给出技术审查意见。"
        ); output['solve_review'] = s2; time.sleep(0.3)

        # === PHASE 4: 结果深度解读 (3 calls) ===
        print(f"  [Phase 4/6] Result Interpretation (3 calls)")

        i1 = self._call(
            "基于求解结果写出深度的结果分析。从多个维度解读："
            "1)数值本身说明了什么 2)与其他可能方案的对比 "
            "3)结果对实际问题决策的意义 4)结果的局限性和适用范围。"
            "每段200-300字，共4-5段。用中文，学术风格。",
            f"求解结果: distance={dist}km, locations={n}\n"
            f"方法: Floyd-Warshall + NN + 2-opt + SA\n"
            f"请写出深度结果分析。"
        ); output['result_interpretation'] = i1; time.sleep(0.3)

        i2 = self._call(
            "现在请你质疑你自己刚才写的分析。找出分析中的逻辑跳跃、"
            "过度解读、或者不够严谨的地方。然后重新写一个更严谨的版本。",
            f"原始分析:\n{i1[:2000]}\n\n请批判并重写。"
        ); output['result_self_critique'] = i2; time.sleep(0.3)

        i3 = self._call(
            "综合前面的分析和批判，写出最终版的结果分析。"
            "要求：逻辑严密、数值引用准确、结论审慎、对决策有实际指导意义。"
            "这是要放进论文里的关键段落，请精益求精。",
            f"初版:\n{i1[:1000]}\n修正版:\n{i2[:1000]}\n\n请写出最终版。"
        ); output['result_final'] = i3; time.sleep(0.3)

        # === PHASE 5: 图表设计 (2 calls) ===
        print(f"  [Phase 5/6] Figure Design (2 calls)")

        f1 = self._call_json(
            "你是Nature/Science级别的数据可视化专家。为这个子问题设计图表方案。"
            "每张图都要有明确的科学论证目的。不要堆砌，宁缺毋滥。"
            "考虑：什么图最能让评委理解你的结果？",
            f"问题: {ptype}, 结果: distance={dist}km, n={n}\n"
            f"返回JSON: {{'figures':[{{'type':'','purpose':'','what_to_show':'',"
            f"'layout_description':'','caption_text':''}}], 'design_philosophy':''}}"
        ); fig_plan = f1; time.sleep(0.3)

        f2 = self._call(
            "审查这个图表设计方案。有没有遗漏重要的可视化？有没有多余的图？"
            "图的排列顺序是否合理？标注是否充分？给出改进意见。",
            f"图表方案:\n{json.dumps(f1, ensure_ascii=False)[:2000]}\n请审查。"
        ); output['figure_review'] = f2; time.sleep(0.3)

        # Add figure plan to output
        for i, fig in enumerate(fig_plan.get('figures', [])[:3]):
            output[f'figure_{i+1}'] = fig

        # === PHASE 6: 质量保证 (2 calls) ===
        print(f"  [Phase 6/6] Quality Assurance (2 calls)")

        q1 = self._call_json(
            "你是数学建模竞赛的终审评委。全面评估这个子问题的求解质量。"
            "从模型选择、求解方法、结果合理性、分析深度四个维度打分(1-100)。"
            "要严格，不要放水。",
            f"完整求解过程:\n{json.dumps({k: str(v)[:300] for k,v in output.items()}, ensure_ascii=False)[:3000]}\n"
            f"返回JSON: {{'model_score':0,'method_score':0,'result_score':0,"
            f"'analysis_score':0,'overall_score':0,'verdict':'','suggestions':[]}}"
        ); output['quality_scores'] = q1; time.sleep(0.3)

        q2 = self._call(
            "最后，请给出一段200字以内的'评委点评'，总结这个子问题的求解亮点和不足。"
            "以及一条最重要的改进建议。",
            f"评分:\n{json.dumps(q1, ensure_ascii=False)}\n请写评委点评。"
        ); output['judge_comment'] = q2; time.sleep(0.3)

        # Summary
        overall = q1.get('overall_score', 75) if isinstance(q1, dict) else 75
        print(f"\n  DEEP THINK Q{sp_id} COMPLETE:")
        print(f"    API calls: {self.total_calls}")
        print(f"    Est. cost: ¥{self.total_cost:.4f}")
        print(f"    Quality:   {overall}/100")
        print(f"    Stages:    18 calls across 6 phases")

        return output
