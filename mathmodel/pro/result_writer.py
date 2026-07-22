"""Pro: 结果驱动写作 — AI拿到真实数值写分析"""

import json
import urllib.request
import numpy as np


class ResultNarrator:
    """基于实际结果的AI叙事写作"""

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.api_key = api_key
        self.model = model

    def _call_ai(self, system: str, user: str) -> str:
        body = json.dumps({
            "model": self.model, "temperature": 0.4, "max_tokens": 4096,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
        }).encode()
        req = urllib.request.Request(
            "https://api.deepseek.com/v1/chat/completions", data=body,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self.api_key}"}, method="POST")
        for _ in range(3):
            try:
                with urllib.request.urlopen(req, timeout=90) as r:
                    return json.loads(r.read())["choices"][0]["message"]["content"]
            except Exception:
                import time; time.sleep(2)
        return ""

    def narrate_result(self, sub_problem: dict, result: dict, contest_result: dict = None) -> str:
        """根据实际结果写深度分析

        Args:
            sub_problem: {"id":1, "type":"评价", "title":"...", "model":"TOPSIS"}
            result: solver output dict (scores, labels, forecast, selection, etc.)
            contest_result: optional multi-model comparison result

        Returns:
            str: 3-5段深度分析（现象描述 + 原因解读 + 业务建议）
        """
        ptype = sub_problem.get("type", "")
        sp_id = sub_problem.get("id", "")

        # Build context with ALL available data
        context = {
            "problem": sub_problem.get("title", "")[:300],
            "problem_type": ptype,
            "model_used": sub_problem.get("model", ""),
            "results": {k: v for k, v in (result or {}).items() if k != "summary" and not isinstance(v, list) or (isinstance(v, list) and len(str(v)) < 200)},
        }

        # Add contest info if available
        if contest_result:
            context["model_contest"] = {
                "winner": contest_result.get("winner", ""),
                "all_models": [c["model"] for c in contest_result.get("candidates", [])],
                "ai_reason": contest_result.get("ai_reason", "")[:300],
            }

        system = """你是一位数学建模竞赛论文的资深写作者。你的任务是：基于提供的真实求解结果，
对每个子问题写出深度的、有洞察力的分析段落。你必须做到：
1. 描述现象——具体数值说明了什么
2. 分析原因——为什么是这个结果，数值差异源于何处
3. 给出建议——基于分析结论的实际建议
4. 语言学术化但不枯燥，可以适当使用"显著优于""表现出色"等表述
5. 每个子问题3-5段，每段150-300字
写中文。"""

        user = f"""以下是一个数学建模子问题的求解结果，请写出深度分析：

子问题: {json.dumps(context['problem'], ensure_ascii=False)}
题型: {context['problem_type']}
模型: {context['model_used']}

真实求解结果:
{json.dumps(context['results'], ensure_ascii=False, default=str)[:3000]}

{f"模型竞赛结果: {json.dumps(context.get('model_contest', {}), ensure_ascii=False)[:1000]}" if contest_result else ""}

请写出3-5段深度分析。每段都要包含：
- 具体数字
- 数字说明什么
- 为什么
- 意味着什么"""

        text = self._call_ai(system, user)
        return text or self._fallback_narrative(sub_problem, result)

    def narrate_comparison(self, contest_result: dict, ptype: str) -> str:
        """写模型对比分析"""
        if not contest_result:
            return ""

        system = "你是数学建模竞赛评委。写一段模型对比分析，说明为何选这个模型而不是其他。"
        candidates_text = "\n".join(
            f"- {c['model']}: {c['result'].get('metric_name','?')}={c['result'].get('metric_value','?')}"
            for c in contest_result.get("candidates", [])
        )
        user = f"""以下是子问题的模型对比结果：
{candidates_text}

最终选择: {contest_result.get('winner', '')}
AI理由: {contest_result.get('ai_reason', '')}

请用一段话(150-250字)说明为何选择这个模型，其他模型为何被淘汰。使用具体数字。"""

        return self._call_ai(system, user) or (
            f"综合考虑各模型表现，选择{contest_result.get('winner', '')}。"
            f"理由：{contest_result.get('ai_reason', '表现最优')}。")

    def narrate_sensitivity(self, deep_sens_results: dict) -> str:
        """基于深度灵敏度结果写分析段落"""
        system = "写灵敏度分析的学术段落。200-400字，中文。"
        user = f"""灵敏度分析结果:
{json.dumps(deep_sens_results, ensure_ascii=False, default=str)[:2000]}

请写出：最敏感参数是什么，其含义是什么，对决策有何启示。"""

        return self._call_ai(system, user) or "灵敏度分析验证了模型的稳定性。"

    def _fallback_narrative(self, sp, result):
        """API失败时的回退叙事"""
        ptype = sp.get("type", "")
        parts = [f"针对子问题{sp['id']}，建立了{sp.get('model','模型')}进行求解。"]
        if result and isinstance(result, dict):
            if "scores" in result and "labels" in result:
                labels = result.get("labels", [])
                scores = [float(s) for s in result.get("scores", [])]
                if labels and scores:
                    best = labels[int(np.argmax(scores))]
                    parts.append(f"评价结果显示{best}方案得分最高（{max(scores):.4f}），为最优选择。")
            if "forecast" in result:
                f_val = result["forecast"]
                parts.append(f"预测未来数值为{'、'.join(f'{v:.1f}' for v in f_val)}。")
            if "selection" in result:
                parts.append(f"优化得到最优方案：选择{', '.join(str(s) for s in result['selection'])}，"
                             f"总成本{result.get('total_cost',0):.1f}。")
        return "\n\n".join(parts)
