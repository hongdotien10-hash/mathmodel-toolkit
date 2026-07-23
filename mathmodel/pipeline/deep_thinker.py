"""深度思考引擎 — 每问30次API + 论文级20次 = 80次/篇 ~¥3"""
import json, urllib.request, time, sys
from pathlib import Path


class DeepThinker:
    """每问30次 + 论文级20次 API调用，深度思考引擎"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.total_calls = 0
        self.total_cost = 0.0

    def _call(self, system: str, user: str, temp: float = 0.3, max_tok: int = 8000) -> str:
        body = json.dumps({
            "model": "deepseek-chat", "temperature": temp, "max_tokens": max_tok,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
        }).encode()
        req = urllib.request.Request("https://api.deepseek.com/v1/chat/completions",
            data=body, headers={"Content-Type": "application/json",
                               "Authorization": f"Bearer {self.api_key}"}, method="POST")
        for attempt in range(2):
            try:
                with urllib.request.urlopen(req, timeout=180) as r:
                    self.total_calls += 1
                    resp = json.loads(r.read())
                    text = resp["choices"][0]["message"]["content"]
                    in_tok = len(system + user) / 3
                    out_tok = len(text) / 3
                    self.total_cost += in_tok/1e6*1.0 + out_tok/1e6*2.0
                    return text
            except Exception as e:
                if attempt == 1: return ""
                time.sleep(3)
        return ""

    def _json(self, system: str, user: str) -> dict:
        text = self._call(system, user, temp=0.2)
        try:
            if "```" in text: text = text.split("```")[1].split("```")[0]
            if text.strip().startswith("json"): text = text[4:]
            s = text.find("{"); e = text.rfind("}") + 1
            return json.loads(text[s:e]) if s >= 0 else {}
        except: return {}

    def _debate(self, topic: str, context: str, rounds: int = 3) -> list:
        """多角色辩论：3个专家角色各自发表意见并互相辩论"""
        roles = [
            ("理论专家", "你是数学/运筹学理论专家，关注模型的数学严谨性和理论最优性。"),
            ("工程专家", "你是工程实践专家，关注算法的可实现性、计算效率和鲁棒性。"),
            ("领域专家", "你是应急物流/配送领域的应用专家，关注方案的实际可行性和业务合理性。"),
        ]
        debate_log = []
        prev_opinions = ""
        for r in range(rounds):
            for role_name, role_sys in roles:
                prompt = (f"辩论主题: {topic}\n背景: {context[:2000]}\n"
                         f"前几轮观点:\n{prev_opinions[-2000:] if prev_opinions else '（首轮）'}\n\n"
                         f"你作为{role_name}，请发表你的观点。如果是第2轮以后，"
                         f"请回应其他专家的观点，指出你同意或不同意的地方。")
                opinion = self._call(role_sys, prompt, temp=0.5)
                debate_log.append({"role": role_name, "round": r+1, "opinion": opinion})
                prev_opinions += f"\n[{role_name} R{r+1}]: {opinion[:500]}"
                time.sleep(0.2)
        return debate_log

    # ================================================================
    # 单问完整流水线: 30次API
    # ================================================================

    def think_one_question(self, sp, problem_text, data_profiles, result, fig_dir):
        """单个子问题30次API深度思考"""
        sp_id = sp.get("id", "?")
        n = result.get("n_locations", "?")
        dist = result.get("total_distance", "?")

        ctx = f"问题{sp_id}: {sp.get('title','')}\n类型: {sp.get('type','')}\n"
        ctx += f"结果: {dist}km, {n}个地点\n"
        ctx += f"数据: {json.dumps({k:str(v.get('shape','?')) for k,v in (data_profiles or {}).items()}, ensure_ascii=False)}"

        print(f"\n  {'='*50}")
        print(f"  Q{sp_id}: 30-API Deep Analysis Pipeline")
        print(f"  {'='*50}")
        out = {}

        # --- 1. 多角色辩论: 问题理解 (3×2=6 calls) ---
        print("  [1/8] Multi-persona problem debate (6 calls)")
        out['problem_debate'] = self._debate(
            f"如何理解和建模这个问题: {sp.get('title','')[:100]}",
            f"{problem_text[:2000]}\n{ctx}", rounds=2)
        time.sleep(0.5)

        # --- 2. 多角色辩论: 建模方案 (3×2=6 calls) ---
        print("  [2/8] Multi-persona modeling debate (6 calls)")
        out['modeling_debate'] = self._debate(
            f"这个{sp.get('type','')}问题应该用什么模型和算法",
            f"问题:\n{ctx}\n\n前一轮辩论:\n{json.dumps([d['opinion'][:300] for d in out['problem_debate'][-3:]], ensure_ascii=False)}",
            rounds=2)
        time.sleep(0.5)

        # --- 3. 求解策略设计 (3 calls) ---
        print("  [3/8] Strategy design + review (3 calls)")
        out['strategy'] = self._call(
            "综合前面的辩论，制定详细的求解方案。包括完整的算法伪代码、"
            "每个参数的物理含义和推荐值、预期的时间复杂度。写到可以直接实现的程度。",
            f"辩论总结:\n{json.dumps([d['opinion'][:400] for d in out['modeling_debate']], ensure_ascii=False)[:3000]}\n"
            f"结果: distance={dist}km\n请写出详细求解方案。")
        time.sleep(0.3)

        out['strategy_review'] = self._call(
            "严格审查上面的求解方案。每个步骤都质疑一遍。参数是否最优？有无遗漏？边界情况？",
            f"方案:\n{out['strategy'][:3000]}\n请逐一审查。")
        time.sleep(0.3)

        out['strategy_final'] = self._call(
            "根据审查意见，写出最终版求解方案。要完整、精确、可直接实现。",
            f"方案:\n{out['strategy'][:1500]}\n审查:\n{out['strategy_review'][:1500]}")
        time.sleep(0.3)

        # --- 4. 结果深度解读 (4 calls) ---
        print("  [4/8] Deep result interpretation (4 calls)")
        out['result_v1'] = self._call(
            "你是一位资深数学建模论文作者。基于求解结果写一份深度的结果分析。"
            "要包含：现象描述→原因分析→数值对比→决策启示。每段都要引用具体数字。"
            "500-800字，中文，学术风格。",
            f"问题:\n{ctx}\n求解方案:\n{out['strategy_final'][:1500]}\n请写结果分析。")
        time.sleep(0.3)

        out['result_critique'] = self._call(
            "你现在是审稿人。严格审阅上面的结果分析。找出：逻辑漏洞、过度解读、"
            "缺失的数据引用、表述不严谨的地方。每条问题都要指出具体位置和改进建议。",
            f"原文:\n{out['result_v1'][:3000]}\n请逐条审阅。")
        time.sleep(0.3)

        out['result_v2'] = self._call(
            "根据审阅意见重写结果分析。要求更高：每个论断都要有数据支撑，"
            "每个数字都要有解释，每个结论都要有依据。写到论文可以直接使用的质量。",
            f"初稿:\n{out['result_v1'][:1500]}\n审阅意见:\n{out['result_critique'][:1500]}\n请重写。")
        time.sleep(0.3)

        out['result_v2_review'] = self._call(
            "再次审阅修改后的分析。给出0-100的写作质量评分和改进到95分以上的具体建议。",
            f"修改稿:\n{out['result_v2'][:3000]}")
        time.sleep(0.3)

        # --- 5. 图表设计与迭代 (3 calls) ---
        print("  [5/8] Figure design + review (3 calls)")
        out['figure_plan'] = self._call(
            "你为Nature期刊设计过数据图表。为这个求解结果设计3张最有说服力的图。"
            "每张图写明：类型、展示内容、论证目的、预期效果、Caption文字。",
            f"结果: distance={dist}km, n={n}\n请设计图表方案。")
        time.sleep(0.3)

        out['figure_review'] = self._call(
            "审查图表方案是否有冗余、是否遗漏关键信息、排列是否合理。"
            "给出优化后的最终方案。",
            f"方案:\n{out['figure_plan'][:2000]}")
        time.sleep(0.3)

        out['figure_final'] = self._call(
            "写出最终3张图的完整Caption（中英文），以及每张图在论文中的位置建议。",
            f"方案:\n{out['figure_plan'][:1000]}\n审查:\n{out['figure_review'][:1000]}")
        time.sleep(0.3)

        # --- 6. 灵敏度分析设计 (2 calls) ---
        print("  [6/8] Sensitivity analysis design (2 calls)")
        out['sensitivity_plan'] = self._call(
            "设计这个问题的灵敏度分析方案。要测试哪些参数？用什么方法？"
            "预期发现什么？结果如何支撑论文结论？",
            f"结果: distance={dist}km\n方案:\n{out['strategy_final'][:1500]}")
        time.sleep(0.3)

        out['sensitivity_detail'] = self._call(
            "基于上面的方案，写出完整的灵敏度分析段落(400-600字)，"
            "包含具体的测试参数、方法和结论。可以直接放进论文。",
            f"方案:\n{out['sensitivity_plan'][:2000]}")
        time.sleep(0.3)

        # --- 7. 模型评价 (2 calls) ---
        print("  [7/8] Model evaluation (2 calls)")
        out['advantages'] = self._call(
            "列出这个模型和求解方法的5-8个具体优点。每个都要有具体依据，不要空泛。",
            f"方案:\n{out['strategy_final'][:1500]}\n结果:\n{out['result_v2'][:1500]}")
        time.sleep(0.3)

        out['limitations'] = self._call(
            "列出这个方法的4-6个具体不足和改进方向。要诚实、具体、有建设性。",
            f"方案:\n{out['strategy_final'][:1500]}\n优点:\n{out['advantages'][:1500]}")
        time.sleep(0.3)

        # --- 8. 最终质量评估 (2 calls) ---
        print("  [8/8] Final quality assessment (2 calls)")
        out['quality'] = self._json(
            f"从模型(0-100)、求解(0-100)、分析(0-100)、图表(0-100)四个维度评分。"
            f"返回JSON: {{'model':0,'solve':0,'analysis':0,'figure':0,'overall':0,"
            f"'top_3_strengths':[],'top_3_improvements':[]}}",
            f"完整产出:\n{json.dumps({k:str(v)[:300] for k,v in out.items()}, ensure_ascii=False)[:4000]}")
        time.sleep(0.3)

        out['final_verdict'] = self._call(
            "给出100字以内的最终评价。总结这个子问题求解的最大亮点和一项可立即改进的建议。",
            f"评分:\n{json.dumps(out.get('quality',{}), ensure_ascii=False)}")
        time.sleep(0.3)

        q = out.get('quality', {})
        overall = q.get('overall', 75) if isinstance(q, dict) else 75
        print(f"  Q{sp_id} done: {self.total_calls} calls, ¥{self.total_cost:.4f}, score={overall}/100")
        return out

    # ================================================================
    # 论文级分析: 20次API
    # ================================================================

    def think_paper_level(self, sub_problems, all_results, problem_text, data_profiles):
        """跨问题综合分析 + 论文整体质量提升 — 20次API"""
        print(f"\n  {'='*50}")
        print(f"  PAPER-LEVEL: 20-API Cross-Question Synthesis")
        print(f"  {'='*50}")
        out = {}

        summary = ""
        for sp in sub_problems:
            sp_id = sp.get("id", "?")
            r = all_results.get(f"sub_{sp_id}", {})
            summary += f"Q{sp_id}: {r.get('total_distance','?')}km, {r.get('n_locations','?')} locations\n"

        # 1. 摘要撰写+迭代 (6 calls)
        print("  [1/4] Abstract writing + 2 critique rounds (6 calls)")
        out['abstract_v1'] = self._call(
            "你是数学建模竞赛论文的摘要撰写专家。基于所有子问题的求解结果，"
            "写一份完整的论文摘要。400-500字，包含：问题概述、每个子问题的方法和结果、最终结论。"
            "中文，学术风格，每个子问题的结果要有具体数字。",
            f"题目:\n{problem_text[:2000]}\n求解结果:\n{summary}\n"
            f"详细结果:\n{json.dumps({k:{kk:str(vv)[:200] for kk,vv in v.items()} for k,v in all_results.items()}, ensure_ascii=False)[:3000]}")
        time.sleep(0.3)

        out['abstract_critique'] = self._call(
            "作为评委审阅这个摘要。是否完整概括了所有问题？数字是否准确？"
            "是否有吸引力？逐条批评并给出改进建议。",
            f"摘要:\n{out['abstract_v1'][:2000]}")
        time.sleep(0.3)

        out['abstract_v2'] = self._call(
            "根据审阅意见重写摘要。精益求精。", f"原稿+意见:\n{out['abstract_critique'][:1500]}")
        time.sleep(0.3)

        out['abstract_critique2'] = self._call(
            "再次审阅修改后的摘要。这次从语言流畅度、信息密度、学术规范三个角度评价。",
            f"摘要v2:\n{out['abstract_v2'][:2000]}")
        time.sleep(0.3)

        out['abstract_final'] = self._call(
            "综合两轮审阅，写出最终版摘要。这是论文的'门面'，要完美。",
            f"v2:\n{out['abstract_v2'][:1500]}\n审阅:\n{out['abstract_critique2'][:1500]}")
        time.sleep(0.3)

        out['keywords'] = self._call(
            "从论文内容中提取6-8个最合适的关键词。要涵盖：问题领域、"
            "核心方法、关键算法。用中文，分号分隔。只返回关键词，不要其他内容。",
            f"摘要:\n{out['abstract_final'][:1500]}\n{summary}")
        time.sleep(0.3)

        # 2. 论文章节规划 (3 calls)
        print("  [2/4] Paper structure planning (3 calls)")
        out['structure'] = self._call(
            "设计论文的完整章节结构。每章写什么内容、占多少篇幅、放哪些图表。"
            "要像真正竞赛论文的结构一样详细。",
            f"题目:\n{problem_text[:2000]}\n结果:\n{summary}")
        time.sleep(0.3)

        out['structure_review'] = self._call(
            "审查论文结构：逻辑流是否清晰？篇幅分配是否合理？有没有重复或缺失的部分？",
            f"结构:\n{out['structure'][:2000]}")
        time.sleep(0.3)

        out['structure_final'] = self._call(
            "根据审查意见优化论文结构。写出最终版本。",
            f"结构:\n{out['structure'][:1000]}\n审查:\n{out['structure_review'][:1000]}")
        time.sleep(0.3)

        # 3. 跨问题对比分析 (5 calls)
        print("  [3/4] Cross-question synthesis (5 calls)")
        out['cross_comparison'] = self._call(
            "对比所有子问题的求解结果。分析：趋势、模式、异常值、"
            "问题之间的关联性。400-600字的综合分析。",
            f"全部结果:\n{summary}\n"
            f"详情:\n{json.dumps({k:{kk:str(vv)[:200] for kk,vv in v.items() if kk!='tour'} for k,v in all_results.items()}, ensure_ascii=False)[:3000]}")
        time.sleep(0.3)

        out['introduction'] = self._call(
            "写一段论文引言(问题背景)。结合题目原文，说明研究意义、"
            "相关工作和本文的贡献。300-400字。",
            f"题目:\n{problem_text[:2500]}\n结果:\n{summary}")
        time.sleep(0.3)

        out['conclusion'] = self._call(
            "写论文结论。总结所有子问题的核心发现，给出综合性的结论和建议。400-500字。",
            f"结果:\n{summary}\n对比:\n{out['cross_comparison'][:1500]}")
        time.sleep(0.3)

        out['conclusion_review'] = self._call(
            "审阅结论部分。是否准确总结了所有发现？建议是否具体可行？",
            f"结论:\n{out['conclusion'][:2000]}")
        time.sleep(0.3)

        out['conclusion_final'] = self._call(
            "根据审阅意见优化结论。这是论文的最后一部分，要给人留下深刻印象。",
            f"结论:\n{out['conclusion'][:1000]}\n意见:\n{out['conclusion_review'][:1000]}")
        time.sleep(0.3)

        # 4. 整体质量终审 (3 calls)
        print("  [4/4] Final quality review (3 calls)")
        out['paper_quality'] = self._json(
            f"从整体质量(0-100)、创新性(0-100)、严谨性(0-100)、可读性(0-100)评分。"
            f"返回JSON: {{'overall':0,'innovation':0,'rigor':0,'readability':0,"
            f"'pass_judge':true/false,'estimated_prize':'省二/省一/国二/国一'}}",
            f"完整论文内容:\n{json.dumps({k:str(v)[:500] for k,v in out.items()}, ensure_ascii=False)[:4000]}")
        time.sleep(0.3)

        out['final_check'] = self._call(
            "做最终检查：有没有数字前后矛盾？有没有图表引用错误？"
            "有没有逻辑断裂？列出所有发现的问题。",
            f"论文:\n{json.dumps({k:str(v)[:300] for k,v in out.items()}, ensure_ascii=False)[:4000]}")
        time.sleep(0.3)

        out['polish_instructions'] = self._call(
            "给出5条最关键的改进建议，每一条都会显著提升论文质量。要具体可操作。",
            f"检查结果:\n{out['final_check'][:2000]}")
        time.sleep(0.3)

        print(f"\n  PAPER-LEVEL done: {self.total_calls} total calls, ¥{self.total_cost:.4f}")
        pq = out.get('paper_quality', {})
        overall = pq.get('overall', 75) if isinstance(pq, dict) else 75
        prize = pq.get('estimated_prize', '?') if isinstance(pq, dict) else '?'
        print(f"  Quality: {overall}/100, Estimated prize: {prize}")
        return out
