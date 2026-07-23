"""AI逐段写论文 — 每段3轮打磨 + AI审图 + 写到满意为止
每段: 初稿→自审→修改→编辑审→定稿 = 5次API
整篇论文: ~15段 × 5次 = 75次API + 图表审查 = ~100次"""
import json, urllib.request, time


class AIPaperWriter:
    """AI驱动论文写作 — 逐段生成，每段多轮打磨"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.calls = 0
        self.cost = 0.0
        self.sections = {}

    def _call(self, system: str, user: str, temp: float = 0.3, max_tok: int = 8000) -> str:
        body = json.dumps({
            "model": "deepseek-chat", "temperature": temp, "max_tokens": max_tok,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
        }).encode()
        req = urllib.request.Request("https://api.deepseek.com/v1/chat/completions",
            data=body, headers={"Content-Type": "application/json",
                               "Authorization": f"Bearer {self.api_key}"}, method="POST")
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=180) as r:
                    self.calls += 1
                    resp = json.loads(r.read())
                    text = resp["choices"][0]["message"]["content"]
                    self.cost += (len(system+user)/3)/1e6*1.0 + (len(text)/3)/1e6*2.0
                    return text
            except Exception as e:
                if attempt == 2: return f"[API错误: {e}]"
                time.sleep(5)
        return ""

    def _reason(self, system: str, user: str) -> str:
        """用reasoner模型进行深度推理"""
        body = json.dumps({
            "model": "deepseek-reasoner", "temperature": 0.2, "max_tokens": 8000,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
        }).encode()
        req = urllib.request.Request("https://api.deepseek.com/v1/chat/completions",
            data=body, headers={"Content-Type": "application/json",
                               "Authorization": f"Bearer {self.api_key}"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                self.calls += 1
                resp = json.loads(r.read())
                text = resp["choices"][0]["message"]["content"]
                self.cost += (len(system+user)/3)/1e6*1.0 + (len(text)/3)/1e6*2.0
                return text
        except Exception as e:
            return self._call(system, user)  # fallback to chat

    # ================================================================
    # 逐段写作流水线: 每段5次API (初稿→自审→修改→编辑审→定稿)
    # ================================================================

    def write_section(self, section_name: str, context: str, requirements: str,
                      prev_sections: str = "") -> str:
        """写一个章节，5轮打磨"""
        print(f"  [WRITE] {section_name} (5-round polishing)")

        # Round 1: 初稿 (reasoner深度思考)
        draft = self._reason(
            f"你是数学建模竞赛论文的{section_name}撰写专家。请根据提供的信息撰写这一节。"
            f"要求：{requirements}。学术风格，中文，引用具体数字，逻辑严密。",
            f"论文上下文:\n{context[:3000]}\n前面已写章节:\n{prev_sections[:2000]}\n请撰写{section_name}。")
        time.sleep(0.3)

        # Round 2: 自我审查
        critique = self._call(
            "你是一位严格的审稿人。逐段审查你刚才写的内容。从5个维度评分(1-10)："
            "逻辑严密性、数据引用准确性、语言流畅度、学术规范性、信息密度。"
            "每个扣分点都要指出具体位置。",
            f"章节: {section_name}\n内容:\n{draft[:4000]}\n请严格审查。")
        time.sleep(0.3)

        # Round 3: 修改
        revised = self._call(
            "根据审稿意见认真修改。每个批评都要回应。目标是将每个维度的评分提升到8分以上。"
            "修改后的版本应该明显优于原稿。",
            f"原稿:\n{draft[:2000]}\n审稿意见:\n{critique[:2000]}\n请修改。")
        time.sleep(0.3)

        # Round 4: 编辑审
        editor_review = self._call(
            "作为资深学术编辑，审阅修改稿。重点关注：1)有没有数字前后矛盾 2)术语是否统一 "
            "3)句式是否流畅 4)有没有冗余内容。给0-10分并说明理由。",
            f"章节: {section_name}\n修改稿:\n{revised[:4000]}\n请审阅。")
        time.sleep(0.3)

        # Round 5: 定稿
        final = self._call(
            "根据编辑的意见做最后润色。这是最终稿，将直接放进论文。必须完美。"
            "特别注意：数字必须准确、逻辑必须通顺、表达必须学术化但不枯燥。",
            f"修改稿:\n{revised[:2000]}\n编辑意见:\n{editor_review[:2000]}\n请写出最终稿。")

        self.sections[section_name] = {"draft": draft, "critique": critique,
                                        "revised": revised, "editor_review": editor_review,
                                        "final": final}
        print(f"  [WRITE] {section_name} done: {self.calls} calls")
        return final

    # ================================================================
    # 图表审查
    # ================================================================

    def review_figures(self, figure_descriptions: list, results: dict) -> list:
        """审查所有图表"""
        print(f"  [FIG-REVIEW] Reviewing {len(figure_descriptions)} figures")
        reviews = []
        for i, fig in enumerate(figure_descriptions):
            r = self._call(
                "你是Nature期刊的图表审稿人。评价这张图的科学性和视觉质量。"
                "1)是否能独立理解(不看正文) 2)标注是否完整 3)是否有误导 "
                "4)视觉设计如何改进。给出1-10评分。",
                f"图{i+1}: {json.dumps(fig, ensure_ascii=False)}\n"
                f"相关数据: {json.dumps({k:str(v)[:200] for k,v in results.items()}, ensure_ascii=False)}")
            reviews.append({"index": i+1, "review": r})
            time.sleep(0.2)
        return reviews


def write_full_paper(api_key, sub_problems, all_results, problem_text, data_profiles, fig_dir):
    """AI写完整论文 — 每段打磨，总100+次API"""
    writer = AIPaperWriter(api_key)
    ctx = json.dumps({
        "title": problem_text[:200] if problem_text else "",
        "questions": [{"id": sp.get("id"), "type": sp.get("type"),
                       "title": sp.get("title","")} for sp in sub_problems],
        "results": {k: {kk: str(vv)[:300] for kk, vv in v.items()
                    if kk not in ('tour',)} for k, v in all_results.items()},
    }, ensure_ascii=False)

    prev = ""
    sections = {}

    # 1. 标题
    sections['title'] = writer._call(
        "根据论文内容生成一个精准的学术标题。20-35字，突出方法和核心发现。只返回标题。",
        f"论文内容:\n{ctx[:3000]}")
    time.sleep(0.2)

    # 2. 摘要 (最重要，用reasoner)
    sections['abstract'] = writer.write_section(
        "摘要", ctx,
        "400-500字。必须包含: 1)问题概述 2)每个子问题的方法+具体结果数字 "
        "3)核心结论。这是论文最重要的部分，评委第一眼就看这里。")
    prev += f"\n摘要: {sections['abstract'][:300]}"

    # 3. 问题重述
    sections['problem_restatement'] = writer.write_section(
        "问题重述", ctx,
        "包含: 1.1问题背景(基于题目原文) 1.2问题重述(每个子问题一句话)"
        "1.3问题分析(每个子问题一段，分析数学本质和难点)", prev)
    prev += f"\n问题重述: {sections['problem_restatement'][:300]}"

    # 4. 模型假设与符号
    sections['assumptions'] = writer.write_section(
        "模型假设与符号说明", ctx,
        "2.1基本假设(5-8条,基于实际模型,不是泛泛而谈) 2.2符号说明表格", prev)
    prev += f"\n假设: {sections['assumptions'][:200]}"

    # 5. 每个子问题
    for sp in sub_problems:
        sp_id = sp.get("id", "?")
        r = all_results.get(f"sub_{sp_id}", {})
        sp_ctx = json.dumps({
            "sub_problem": sp, "result": {k: str(v)[:300] for k, v in r.items()},
        }, ensure_ascii=False)
        sec_name = f"问题{sp_id}的模型建立与求解"
        sections[f'model_q{sp_id}'] = writer.write_section(
            sec_name, sp_ctx,
            "包含: 问题描述与建模(数学公式) 求解方法(算法步骤,为什么选这个算法) "
            "求解结果(具体数字,表格,分析)。500-800字。", prev)
        prev += f"\nQ{sp_id}: {sections[f'model_q{sp_id}'][:200]}"

    # 6. 灵敏度分析
    sections['sensitivity'] = writer.write_section(
        "灵敏度分析", ctx,
        "分析模型对关键参数的敏感程度。包含具体的测试参数、方法和结论。300-500字。", prev)
    prev += f"\n灵敏度: {sections['sensitivity'][:200]}"

    # 7. 模型评价
    sections['evaluation'] = writer.write_section(
        "模型评价与改进", ctx,
        "5.1模型优点(5-8条,具体) 5.2模型不足与改进(4-6条,诚实且有建设性)。300-400字。", prev)
    prev += f"\n评价: {sections['evaluation'][:200]}"

    # 8. 结论
    sections['conclusion'] = writer.write_section(
        "结论", ctx,
        "总结所有子问题的核心发现。每条结论引用具体数字。给出综合建议。300-400字。", prev)

    # 9. 图表审查
    fig_reviews = writer.review_figures(
        [{"purpose": f"问题{sp.get('id','?')}的路线图"} for sp in sub_problems],
        all_results)

    print(f"\n  PAPER COMPLETE: {writer.calls} API calls, ¥{writer.cost:.4f}")
    return sections, fig_reviews, writer.cost
