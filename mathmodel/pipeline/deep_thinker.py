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
        return self._call_model("deepseek-chat", system, user, temp, max_tok)

    def _reason(self, system: str, user: str) -> str:
        """用reasoner模型进行更深度的推理"""
        return self._call_model("deepseek-reasoner", system, user, 0.2, 8000)

    def _call_model(self, model: str, system: str, user: str, temp: float = 0.3, max_tok: int = 8000) -> str:
        body = json.dumps({
            "model": model, "temperature": temp, "max_tokens": max_tok,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
        }).encode()
        req = urllib.request.Request("https://api.deepseek.com/v1/chat/completions",
            data=body, headers={"Content-Type": "application/json",
                               "Authorization": f"Bearer {self.api_key}"}, method="POST")
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=300) as r:
                    self.total_calls += 1
                    resp = json.loads(r.read())
                    text = resp["choices"][0]["message"]["content"]
                    in_tok = len(system + user) / 3
                    out_tok = len(text) / 3
                    self.total_cost += in_tok/1e6*1.0 + out_tok/1e6*2.0
                    return text
            except Exception as e:
                if attempt == 2: return ""
                time.sleep(5)
        return ""

    def _json(self, system: str, user: str) -> dict:
        text = self._call(system, user, temp=0.2)
        try:
            if "```" in text: text = text.split("```")[1].split("```")[0]
            if text.strip().startswith("json"): text = text[4:]
            s = text.find("{"); e = text.rfind("}") + 1
            return json.loads(text[s:e]) if s >= 0 else {}
        except: return {}

    def _debate(self, topic: str, context: str, rounds: int = 4) -> list:
        """多角色辩论：3专家×4轮=12次API，reasoner模型深度推理"""
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
                opinion = self._reason(role_sys, prompt)  # reasoner for deeper thinking
                debate_log.append({"role": role_name, "round": r+1, "opinion": opinion})
                prev_opinions += f"\n[{role_name} R{r+1}]: {opinion[:500]}"
                time.sleep(0.3)
        return debate_log

    # ================================================================
    # 单问完整流水线: 30次API
    # ================================================================

    def think_one_question(self, sp, problem_text, data_profiles, result, fig_dir):
        """单个子问题 100+次API 极限深度思考"""
        sp_id = sp.get("id", "?")
        n = result.get("n_locations", "?")
        dist = result.get("total_distance", "?")

        ctx = f"问题{sp_id}: {sp.get('title','')}\n类型: {sp.get('type','')}\n"
        ctx += f"结果: {dist}km, {n}个地点\n"

        print(f"\n  {'='*55}")
        print(f"  Q{sp_id}: 100+ API Deep Analysis Pipeline")
        print(f"  {'='*55}")
        out = {}

        # === 1. 多角色辩论: 问题理解 (3×4=12 calls, reasoner) ===
        print("  [1/10] Problem debate (12 reasoner calls)")
        out['problem_debate'] = self._debate(
            f"如何理解和建模这个问题: {sp.get('title','')[:100]}",
            f"{problem_text[:2000]}\n{ctx}", rounds=4)

        # === 2. 多角色辩论: 建模方案 (3×4=12 calls, reasoner) ===
        print("  [2/10] Modeling debate (12 reasoner calls)")
        out['modeling_debate'] = self._debate(
            f"这个{sp.get('type','')}问题应该用什么模型和算法",
            f"问题:\n{ctx}\n\n前一轮辩论:\n{json.dumps([d['opinion'][:300] for d in out['problem_debate'][-3:]], ensure_ascii=False)}",
            rounds=4)

        # === 3. 求解策略 (5 calls, reasoner+chat) ===
        print("  [3/10] Strategy design (5 calls)")
        out['strategy_v1'] = self._reason("制定初步求解方案。", f"辩论:\n{json.dumps([d['opinion'][:300] for d in out['modeling_debate']], ensure_ascii=False)[:3000]}")
        out['strategy_critique'] = self._call("严格审查。每个步骤质疑一遍。", f"方案:\n{out['strategy_v1'][:3000]}")
        out['strategy_v2'] = self._call("根据审查重写。", f"v1:\n{out['strategy_v1'][:1500]}\n审查:\n{out['strategy_critique'][:1500]}")
        out['strategy_critique2'] = self._call("再审。必须满分才通过。", f"v2:\n{out['strategy_v2'][:3000]}")
        out['strategy_final'] = self._call("最终版。完整精确可直接实现。", f"v2:\n{out['strategy_v2'][:1500]}\n审查:\n{out['strategy_critique2'][:1500]}")

        # === 4. 结果解读 (8 calls, reasoner+反复打磨) ===
        print("  [4/10] Result interpretation (8 calls)")
        out['result_v1'] = self._reason(f"深度分析求解结果。{dist}km意味着什么？", f"问题:\n{ctx}\n方案:\n{out['strategy_final'][:1500]}")
        out['result_v1_critique'] = self._call("审稿人严格审阅。找出所有问题。", f"分析:\n{out['result_v1'][:3000]}")
        out['result_v2'] = self._call("根据审阅修改。每个批评都要回应。", f"v1:\n{out['result_v1'][:1500]}\n审阅:\n{out['result_v1_critique'][:1500]}")
        out['result_v2_critique'] = self._call("再审。要求95分以上。", f"v2:\n{out['result_v2'][:3000]}")
        out['result_v3'] = self._call("再次修改。精益求精。", f"v2:\n{out['result_v2'][:1500]}\n审阅:\n{out['result_v2_critique'][:1500]}")
        out['result_v3_score'] = self._call("给v3打分(0-100), 如果不到95分, 说明具体差距。", f"v3:\n{out['result_v3'][:3000]}")
        out['result_v4'] = self._call("根据评分意见做最后修改。必须是论文可直接用的最终版。", f"v3:\n{out['result_v3'][:1500]}\n评分:\n{out['result_v3_score'][:1500]}")
        out['result_final_v4_score'] = self._call("最终评分。这个版本能打多少分？", f"v4:\n{out['result_v4'][:3000]}")

        # === 5. 图表设计 (6 calls) ===
        print("  [5/10] Figure design (6 calls)")
        out['fig_v1'] = self._reason(f"设计3张最有说服力的图来展示{dist}km的结果。", f"结果:\n{ctx}\n分析:\n{out['result_v4'][:2000]}")
        out['fig_review'] = self._call("审查图表方案。是否有冗余/遗漏/不合理。", f"方案:\n{out['fig_v1'][:2000]}")
        out['fig_v2'] = self._call("优化方案。", f"v1:\n{out['fig_v1'][:1000]}\n审查:\n{out['fig_review'][:1000]}")
        out['fig_captions'] = self._call("写每张图的完整Caption。", f"方案:\n{out['fig_v2'][:2000]}")
        out['fig_caption_review'] = self._call("审查Caption是否准确完整。", f"Caption:\n{out['fig_captions'][:2000]}")
        out['fig_final'] = self._call("最终Caption定稿。", f"Caption:\n{out['fig_captions'][:1000]}\n审查:\n{out['fig_caption_review'][:1000]}")

        # === 6. 灵敏度设计 (4 calls) ===
        print("  [6/10] Sensitivity design (4 calls)")
        out['sens_v1'] = self._reason("设计完整的灵敏度分析方案。", f"结果: {dist}km\n方案:\n{out['strategy_final'][:1500]}")
        out['sens_review'] = self._call("审查灵敏度方案。", f"方案:\n{out['sens_v1'][:2000]}")
        out['sens_v2'] = self._call("优化方案并写出可直接放入论文的段落。", f"v1:\n{out['sens_v1'][:1000]}\n审查:\n{out['sens_review'][:1000]}")
        out['sens_final'] = self._call("最终版灵敏度分析段落。", f"v2+意见:\n{out['sens_v2'][:2000]}")

        # === 7. 模型评价 (4 calls) ===
        print("  [7/10] Model evaluation (4 calls)")
        out['pros'] = self._call("列出8-10个具体优点，每个要有依据。", f"方案:\n{out['strategy_final'][:1500]}\n结果:\n{out['result_v4'][:1500]}")
        out['cons'] = self._call("列出6-8个具体不足和改进方向。诚实且有建设性。", f"方案:\n{out['strategy_final'][:1500]}")
        out['eval_review'] = self._call("审查优缺点是否客观全面。", f"优点:\n{out['pros'][:1500]}\n不足:\n{out['cons'][:1500]}")
        out['eval_final'] = self._call("根据审查写出最终版模型评价。", f"优缺点:\n{out['pros'][:1000]}\n{out['cons'][:1000]}\n审查:\n{out['eval_review'][:1500]}")

        # === 8. 写作素材整理 (4 calls) ===
        print("  [8/10] Writing material preparation (4 calls)")
        out['abstract_para'] = self._call("为摘要写一段关于这个子问题的描述(100-150字,含具体数字)。", f"结果:\n{ctx}\n分析:\n{out['result_v4'][:1500]}")
        out['background_para'] = self._call("写一段问题背景(150-200字)。", f"问题:\n{ctx}\n题目:\n{problem_text[:1500]}")
        out['method_para'] = self._call("写一段方法说明(200-300字)。", f"方案:\n{out['strategy_final'][:1500]}")
        out['conclusion_para'] = self._call("写一段结论(100-150字,含数字)。", f"结果:\n{ctx}\n分析:\n{out['result_v4'][:1500]}")

        # === 9. 自我一致性检查 (3 calls) ===
        print("  [9/10] Self-consistency check (3 calls)")
        out['consistency_v1'] = self._call("检查所有分析中引用的数字是否一致。列出所有不一致的地方。",
            json.dumps({k: str(v)[:500] for k, v in out.items()}, ensure_ascii=False)[:4000])
        out['consistency_fixes'] = self._call("修正所有不一致。", f"问题:\n{out['consistency_v1'][:2000]}")
        out['consistency_final'] = self._call("最终一致性确认。", f"修正:\n{out['consistency_fixes'][:2000]}")

        # === 10. 最终评审 (3 calls, reasoner) ===
        print("  [10/10] Final review (3 reasoner calls)")
        out['final_score'] = self._json(
            f"四维评分(model/solve/analysis/figure各0-100)。返回JSON。",
            json.dumps({k: str(v)[:400] for k, v in out.items()}, ensure_ascii=False)[:4000])
        out['final_verdict'] = self._reason("给出200字最终评价: 最大亮点+最重要改进建议+预期获奖等级。",
            json.dumps(out.get('final_score', {}), ensure_ascii=False))

        q = out.get('final_score', {})
        overall = q.get('overall', 75) if isinstance(q, dict) else 75
        print(f"\n  Q{sp_id} COMPLETE: {self.total_calls} calls, ¥{self.total_cost:.4f}, score={overall}/100")
        return out

    # ================================================================
    # 论文级分析: 20次API
    # ================================================================

    def think_paper_level(self, sub_problems, all_results, problem_text, data_profiles):
        """论文级综合分析 — 40+次API, reasoner深度推理"""
        print(f"\n  {'='*50}")
        print(f"  PAPER-LEVEL: 40+ API Cross-Question Synthesis")
        print(f"  {'='*50}")
        out = {}

        summary = ""
        for sp in sub_problems:
            sp_id = sp.get("id", "?")
            r = all_results.get(f"sub_{sp_id}", {})
            summary += f"Q{sp_id}: {r.get('total_distance','?')}km, {r.get('n_locations','?')} locations\n"

        # 1. 摘要 (8 calls, reasoner+反复打磨)
        print("  [1/4] Abstract (8 calls)")
        out['abstract_v1'] = self._reason("撰写完整的论文摘要。400-500字。", f"题目:\n{problem_text[:2000]}\n结果:\n{summary}")
        out['abs_c1'] = self._call("评委审阅。逐条批评。", f"摘要:\n{out['abstract_v1'][:2000]}")
        out['abstract_v2'] = self._call("根据审阅重写。", f"v1:\n{out['abstract_v1'][:1000]}\n审阅:\n{out['abs_c1'][:1000]}")
        out['abs_c2'] = self._call("再审: 流畅度/信息密度/学术规范。", f"v2:\n{out['abstract_v2'][:2000]}")
        out['abstract_v3'] = self._call("二次修改。", f"v2:\n{out['abstract_v2'][:1000]}\n审阅:\n{out['abs_c2'][:1000]}")
        out['abs_c3'] = self._call("三审: 是否完美? 哪里还能提升?", f"v3:\n{out['abstract_v3'][:2000]}")
        out['abstract_final'] = self._call("最终版。论文门面，必须完美。", f"v3:\n{out['abstract_v3'][:1000]}\n审阅:\n{out['abs_c3'][:1000]}")
        out['keywords'] = self._call("提取6-8个关键词，分号分隔。只返回关键词。", f"摘要:\n{out['abstract_final'][:1500]}")

        # 2. 结构规划 (4 calls)
        print("  [2/4] Structure (4 calls)")
        out['structure'] = self._reason("设计完整论文结构。每章内容/篇幅/图表位置。", f"题目:\n{problem_text[:2000]}\n结果:\n{summary}")
        out['structure_review'] = self._call("审查结构。", f"结构:\n{out['structure'][:2000]}")
        out['structure_final'] = self._call("优化结构。", f"结构:\n{out['structure'][:1000]}\n审查:\n{out['structure_review'][:1000]}")

        # 3. 跨问题分析 (8 calls)
        print("  [3/4] Cross-question (8 calls)")
        out['cross_v1'] = self._reason("对比所有子问题结果。趋势/模式/关联。", f"结果:\n{summary}")
        out['cross_c1'] = self._call("审阅对比分析。", f"分析:\n{out['cross_v1'][:2000]}")
        out['cross_final'] = self._call("最终版对比分析。", f"v1:\n{out['cross_v1'][:1000]}\n审阅:\n{out['cross_c1'][:1000]}")
        out['intro_v1'] = self._reason("写引言(300-400字)。", f"题目:\n{problem_text[:2500]}\n结果:\n{summary}")
        out['intro_final'] = self._call("最终版引言。", f"v1:\n{out['intro_v1'][:2000]}")
        out['concl_v1'] = self._reason("写结论(400-500字)。", f"结果:\n{summary}\n对比:\n{out['cross_final'][:1500]}")
        out['concl_review'] = self._call("审阅结论。", f"结论:\n{out['concl_v1'][:2000]}")
        out['concl_final'] = self._call("最终版结论。", f"v1:\n{out['concl_v1'][:1000]}\n审阅:\n{out['concl_review'][:1000]}")

        # 4. 终审 (5 calls)
        print("  [4/4] Final review (5 calls)")
        out['quality'] = self._json(
            "评分: overall/innovation/rigor/readability 0-100。返回JSON。",
            json.dumps({k: str(v)[:500] for k, v in out.items()}, ensure_ascii=False)[:4000])
        out['final_check'] = self._reason("终极检查: 数字矛盾/图引用错误/逻辑断裂?", json.dumps({k: str(v)[:300] for k, v in out.items()}, ensure_ascii=False)[:4000])
        out['polish'] = self._call("5条最关键改进建议。", f"检查:\n{out['final_check'][:2000]}")
        out['prize_estimate'] = self._call("预估获奖等级和概率。", f"全部:\n{json.dumps(out.get('quality',{}), ensure_ascii=False)}")
        out['final_verdict'] = self._reason("200字最终评审意见。", json.dumps({k: str(v)[:300] for k, v in out.items()}, ensure_ascii=False)[:3000])

        pq = out.get('quality', {})
        overall = pq.get('overall', 75) if isinstance(pq, dict) else 75
        prize = pq.get('estimated_prize', '?') if isinstance(pq, dict) else '?'
        print(f"\n  PAPER DONE: {self.total_calls} calls, ¥{self.total_cost:.4f}, {overall}/100, est.{prize}")
        return out
