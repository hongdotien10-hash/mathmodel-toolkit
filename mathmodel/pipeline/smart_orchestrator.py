"""
AI 驱动智能流水线

LLM 读取题目+数据 → 制定求解计划 → 调度求解器 → 解释结果 → 撰写论文
每一步都由 AI 根据 skills 工作流上下文做智能决策，而不是无脑走模板。
"""

import json
import urllib.request
from pathlib import Path
from typing import Optional

SOLVER_CATALOG = """
Available solvers:

1. EvaluationSolver: TOPSIS, AHP, Entropy Weight, Fuzzy Comprehensive, Grey Relational, CRITIC
   - Input: decision matrix (m alternatives × n criteria)
   - Output: scores, ranks, weights

2. StatsSolver: Grey Forecast GM(1,1), ARIMA, Correlation Analysis, t-test, ANOVA
   - Input: time series data or sample groups
   - Output: forecasts, correlation matrix, p-values

3. OptimizationSolver: Linear Programming, Integer Programming, Nonlinear Programming
   - Input: cost/benefit vectors, constraint matrices
   - Output: optimal solution vector, objective value

4. SensitivityAnalyzer: OAT, Morris, Sobol, Monte Carlo robustness checks
   - Input: model function, parameter ranges
   - Output: sensitivity indices, confidence intervals

Figure types: bar chart, line chart, scatter plot, correlation heatmap, box plot
"""


class AIDrivenPipeline:
    """AI 驱动的智能求解流水线"""

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.deepseek.com/v1"
        self.conversation = []  # 保持对话上下文

    # ================================================================
    # LLM 调用
    # ================================================================

    def _call_llm(self, system: str, user: str, temperature: float = 0.3) -> str:
        """调用 DeepSeek"""
        body = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": 4096,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    result = json.loads(resp.read())
                    return result["choices"][0]["message"]["content"]
            except Exception as e:
                if attempt == 2:
                    raise
                import time
                time.sleep(2)

    def _call_llm_json(self, system: str, user: str) -> dict:
        """调用 LLM 并解析 JSON"""
        text = self._call_llm(system, user, temperature=0.2)

        # Try multiple strategies to extract JSON
        import re

        # Strategy 1: ```json code block
        m = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if m:
            try: return json.loads(m.group(1).strip())
            except: pass

        # Strategy 2: Find outermost { }
        depth = 0; start = -1
        for i, c in enumerate(text):
            if c == '{':
                if depth == 0: start = i
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0 and start >= 0:
                    try: return json.loads(text[start:i+1])
                    except: pass
                    start = -1

        # Strategy 3: Try raw text
        text = text.strip()
        if text.startswith('{'):
            try: return json.loads(text)
            except: pass

        # Fallback: wrap in dict
        return {"raw_response": text, "parse_error": True}

    # ================================================================
    # Phase 1: 理解题目 + 制定计划
    # ================================================================

    def analyze_and_plan(self, problem_text: str, data_summary: str) -> dict:
        """AI 分析题目并制定详细求解计划"""
        print("  [AI] Analyzing problem and creating plan...")

        system = """You are a mathematical modeling competition expert. Your task is to analyze the problem
and create a detailed, executable solving plan. You have access to these solvers:

""" + SOLVER_CATALOG + """

For each sub-problem, you must specify:
- Which data file(s) to use
- Which solver to apply
- How to preprocess the data (aggregation, filtering, joining)
- What parameters to use
- What output to expect
- How to interpret the results

Be specific and precise. Don't give generic advice — give exact instructions that can be followed programmatically.
"""

        user = f"""Problem text:
{problem_text[:4000]}

Data files available:
{data_summary}

Please create a solving plan in JSON format:

{{
    "overall_theme": "brief description",
    "sub_problems": [
        {{
            "id": 1,
            "type": "evaluation/prediction/optimization/statistics",
            "description": "what this sub-problem asks",
            "data_file": "which data file to use",
            "data_processing": "exactly how to process the data (aggregate by X, filter Y, join with Z)",
            "solver": "which solver to use",
            "solver_params": {{"key": "value"}},
            "expected_output": "what the result should look like",
            "figure_types": ["bar", "line"]
        }}
    ],
    "cross_table_joins": ["if tables need to be joined, explain how"]
}}"""

        plan = self._call_llm_json(system, user)
        print(f"  [AI] Plan: {plan.get('overall_theme', 'N/A')[:80]}")
        for sp in plan.get("sub_problems", []):
            print(f"       Q{sp['id']}: {sp.get('type','?')} — {sp.get('solver','?')} "
                  f"[data: {sp.get('data_file','?')}]")
        return plan

    # ================================================================
    # Phase 2: 解释结果
    # ================================================================

    def interpret_results(self, plan: dict, results: dict) -> dict:
        """AI 解释求解结果并生成论文内容"""
        print("  [AI] Interpreting results and writing analysis...")

        system = """You are a mathematical modeling expert writing a competition paper.
Given the solving plan and numerical results, write insightful analysis for each sub-problem.
Your analysis should:
1. Explain what the numbers mean in context
2. Highlight key findings
3. Compare alternatives if applicable
4. Discuss limitations and implications
Write in academic Chinese suitable for a competition paper."""

        user = f"""Solving plan: {json.dumps(plan, ensure_ascii=False)[:2000]}

Numerical results: {json.dumps(results, ensure_ascii=False, default=str)[:3000]}

For each sub-problem, write:
1. A one-paragraph analysis of the results
2. Key numerical findings
3. Practical interpretation

Return JSON:
{{
    "analyses": [
        {{
            "sub_problem_id": 1,
            "analysis": "paragraph of analysis...",
            "key_finding": "most important finding",
            "numerical_highlight": "key number"
        }}
    ]
}}"""

        return self._call_llm_json(system, user)

    # ================================================================
    # Phase 3: 写论文摘要
    # ================================================================

    def write_abstract(self, problem_text: str, plan: dict, results: dict, analyses: dict) -> str:
        """AI 撰写高质量论文摘要"""
        print("  [AI] Writing abstract...")

        system = """You are writing the abstract for a Chinese mathematical modeling competition paper (CUMCM).
The abstract is the most important part — it must be:
- 200-400 Chinese characters
- Cover ALL sub-problems with methods AND numerical results
- Professional academic tone
- No markdown, no bullet points"""

        user = f"""Problem: {problem_text[:1000]}
Methods used: {json.dumps(plan.get('sub_problems', []), ensure_ascii=False)[:1000]}
Key results: {json.dumps(results, ensure_ascii=False, default=str)[:1500]}

Write the abstract in Chinese. Include specific numbers."""

        return self._call_llm(system, user, temperature=0.3)

    # ================================================================
    # Phase 4: 写论文章节
    # ================================================================

    def write_section(self, section_name: str, sub_problem: dict,
                      result: dict, analysis: dict) -> str:
        """AI 撰写论文章节"""
        system = f"""You are writing the '{section_name}' section of a CUMCM paper.
Write in academic Chinese. Include mathematical reasoning, not just results.
This section covers sub-problem {sub_problem.get('id','?')}."""

        user = f"""Problem: {json.dumps(sub_problem, ensure_ascii=False)[:1000]}
Results: {json.dumps(result, ensure_ascii=False, default=str)[:1000]}
Analysis: {json.dumps(analysis, ensure_ascii=False)[:500]}

Write a complete section with:
1. Modeling approach and rationale
2. Mathematical formulation (if applicable)
3. Results presentation
4. Discussion and interpretation

Write 3-5 paragraphs in Chinese academic style."""

        return self._call_llm(system, user, temperature=0.4)

    def write_sensitivity_section(self, results: dict) -> str:
        """AI 撰写灵敏度分析章节"""
        system = "Write a sensitivity analysis section for a CUMCM paper in Chinese academic style."

        user = f"""Results: {json.dumps(results, ensure_ascii=False, default=str)[:2000]}

Write about:
1. Which parameters were tested and why
2. How results changed under perturbation
3. What this means for model reliability
4. Recommendations based on sensitivity findings

Write 3-5 paragraphs."""

        return self._call_llm(system, user, temperature=0.4)

    # ================================================================
    # Phase 1+: 最优模型选择（多候选评估+自动选优）
    # ================================================================

    def select_best_models(self, problem_text: str, data_summary: str,
                           sub_problems: list) -> dict:
        """为每个子问题评估多个候选模型，选出最优方案"""
        print("  [AI-Select] Evaluating multiple candidate models per sub-problem...")

        sp_text = "\n".join(
            f"Q{sp['id']}: {sp.get('title','')[:200]}" for sp in sub_problems
        )

        system = """You are a mathematical modeling competition judge.
For each sub-problem, you must:
1. Propose 3-5 candidate model approaches
2. Score each on: theoretical fit (0-10), data compatibility (0-10),
   interpretability for competition paper (0-10), computational feasibility (0-10)
3. Select the best model with detailed justification
4. Note why the alternatives are rejected
Be rigorous and specific — this determines the entire paper quality."""

        user = f"""Problem:
{problem_text[:3000]}

Sub-problems:
{sp_text}

Data summary:
{data_summary}

For each sub-problem, evaluate candidates and select the best. Return JSON:
{{
    "selections": [
        {{
            "sub_problem_id": 1,
            "candidates": [
                {{"model": "model name", "fit": 9, "data": 8, "interpretability": 9, "feasibility": 8,
                  "pros": "why good", "cons": "limitations"}}
            ],
            "winner": "best model name",
            "winner_total_score": 34,
            "justification": "detailed reasoning why this model is best for this specific problem",
            "rejected_reasons": "why alternatives were not chosen"
        }}
    ],
    "overall_strategy": "how these models complement each other"
}}"""

        result = self._call_llm_json(system, user)
        selections = result.get("selections", [])
        for sel in selections:
            print(f"  [AI-Select] Q{sel.get('sub_problem_id','?')}: "
                  f"{sel.get('winner','?')} (score: {sel.get('winner_total_score','?')})")
        return result

    # ================================================================
    # Phase 6: 复盘论证机制（审查→质疑→优化→重写）
    # ================================================================

    def review_and_refine(self, problem_text: str, sub_problems: list,
                          results: dict, paper_sections: dict,
                          max_rounds: int = 3) -> dict:
        """多轮复盘：AI审查论文 → 发现漏洞 → 优化 → 重写，直到满意"""
        print(f"  [AI-Review] Starting review loop (max {max_rounds} rounds)...")

        improved = dict(paper_sections)  # start with current
        review_history = []

        for round_num in range(1, max_rounds + 1):
            print(f"\n  [AI-Review] ==== Round {round_num}/{max_rounds} ====")

            # Step 1: 审查当前论文
            review = self._review_paper(problem_text, sub_problems, results, improved)
            issues = review.get("issues", [])
            score = review.get("quality_score", 0)

            print(f"  [AI-Review] Quality score: {score}/100, Issues found: {len(issues)}")

            for iss in issues[:5]:
                print(f"       [{iss.get('severity','?')}] {iss.get('finding','')[:80]}")

            review_history.append({
                "round": round_num,
                "score": score,
                "issues_count": len(issues),
                "top_issues": issues[:3],
            })

            # Step 2: 如果问题少且分数高，提前结束
            if score >= 85 and len(issues) <= 2:
                print(f"  [AI-Review] Quality sufficient ({score}/100). Stopping review.")
                break

            # Step 3: 针对问题优化
            if issues:
                fixes = self._generate_fixes(problem_text, sub_problems, results, improved, issues)
                improved = dict(fixes)  # update with fixes

        return {
            "final_sections": improved,
            "review_history": review_history,
            "final_score": review_history[-1]["score"] if review_history else 0,
        }

    def _review_paper(self, problem_text: str, sub_problems: list,
                      results: dict, paper_sections: dict) -> dict:
        """AI 作为审稿人审查论文"""
        system = """You are a rigorous CUMCM paper reviewer. Your job is to find flaws,
gaps, and inconsistencies. Be harsh but fair. Check:
1. Are all claims backed by data?
2. Are model assumptions justified?
3. Is the methodology sound?
4. Are numerical results internally consistent?
5. Is the sensitivity analysis thorough enough?
6. Are there alternative interpretations not considered?
7. Is anything overstated or understated?
8. Are there missing sections or analysis types?
Return specific, actionable findings."""

        sections_text = "\n\n".join(
            f"=== {k} ===\n{v[:1000]}" for k, v in list(paper_sections.items())[:8]
        )

        user = f"""Problem context: {problem_text[:1000]}
Models used: {json.dumps([{'id': sp['id'], 'type': sp.get('type',''), 'model': sp.get('model','')} for sp in sub_problems], ensure_ascii=False)}
Results: {json.dumps(results, ensure_ascii=False, default=str)[:2000]}
Paper sections: {sections_text[:5000]}

Review the paper. Return JSON:
{{
    "quality_score": 75,
    "issues": [
        {{
            "severity": "critical/high/medium/low",
            "finding": "specific issue found",
            "impact": "how this affects paper quality",
            "fix_suggestion": "concrete suggestion to fix"
        }}
    ],
    "strengths": ["what's done well"],
    "overall_assessment": "summary paragraph"
}}"""

        return self._call_llm_json(system, user)

    def _generate_fixes(self, problem_text: str, sub_problems: list,
                        results: dict, current_sections: dict,
                        issues: list) -> dict:
        """根据审查意见重新生成论文章节"""
        system = """You are fixing a CUMCM paper based on reviewer feedback.
Rewrite the affected sections to address ALL issues. Be thorough.
If an issue says 'missing sensitivity analysis', add a complete one.
If an issue says 'assumptions not justified', add detailed justification.
If an issue says 'results inconsistent', reconcile them properly."""

        issues_text = "\n".join(
            f"[{i.get('severity','?')}] {i.get('finding','')} → {i.get('fix_suggestion','')}"
            for i in issues[:8]
        )

        user = f"""Problem: {problem_text[:1000]}
Sub-problems: {json.dumps([{'id':sp['id'],'type':sp.get('type',''),'model':sp.get('model','')} for sp in sub_problems], ensure_ascii=False)}
Results: {json.dumps(results, ensure_ascii=False, default=str)[:1500]}
Reviewer issues to fix:
{issues_text}

For each issue, provide the corrected/improved text for the affected section(s).
Return JSON: {{"improvements": {{"section_name": "improved text...", ...}}}}

IMPORTANT: Write in Chinese academic style. Each improved section should be complete and self-contained."""

        result = self._call_llm_json(system, user)
        improvements = result.get("improvements", {})

        # Merge improvements into current sections
        fixed = dict(current_sections)
        for section_name, improved_text in improvements.items():
            if improved_text and len(improved_text) > 50:
                fixed[section_name] = improved_text
                print(f"  [AI-Fix] Updated: {section_name} ({len(improved_text)} chars)")

        return fixed

    # ================================================================
    # AI 指导数据加载（Phase 0）
    # ================================================================

    def clean_data_with_ai(self, problem_text: str, data_profiles: dict) -> dict:
        """AI 结合实际场景检测并清洗数据"""
        print("  [AI-Clean] Inspecting data for real-world anomalies...")

        profiles_text = ""
        for name, p in data_profiles.items():
            sample = p.get('sample', '')
            profiles_text += f"\n=== {name} ===\n"
            profiles_text += f"Shape: {p['shape']}\nColumns: {p['columns']}\n"
            profiles_text += f"Sample:\n{sample}\n"

        system = """You are a data quality engineer for real-world retail/supply chain data.
Inspect the data for issues that would affect mathematical modeling:
1. Impossible values (negative prices, zero quantities where there should be sales)
2. Outliers that are clearly data entry errors (not real extreme values)
3. Date issues (future dates, duplicate dates, gaps)
4. Missing values that need imputation
5. Encoding issues (columns stored as text that should be numeric)
6. Business-logic violations (e.g. selling price < cost price)
7. Redundant columns (all same value, all null)

IMPORTANT: Distinguish between real outliers (extreme but valid) and data errors.
For each issue, specify the exact fix in executable pandas code."""

        user = f"""Problem context: {problem_text[:1500]}
{profiles_text[:5000]}

Return JSON with cleaning plan:
{{
    "issues_found": [
        {{
            "file": "filename",
            "column": "specific column",
            "issue": "description of the problem",
            "real_world_impact": "how this affects modeling in real business context",
            "severity": "critical/high/medium/low",
            "fix_action": "drop_rows/fill_value/convert_type/remove_outliers/flag_only",
            "fix_params": {{"method": "median", "threshold": 3.0}}
        }}
    ],
    "cleaning_summary": "overall data quality assessment"
}}"""

        result = self._call_llm_json(system, user)
        issues = result.get("issues_found", [])
        for iss in issues:
            print(f"  [AI-Clean] [{iss.get('severity','?')}] {iss.get('file','?')}/{iss.get('column','?')}: {iss.get('issue','')[:80]}")
        print(f"  [AI-Clean] Found {len(issues)} issues, summary: {result.get('cleaning_summary','')[:100]}")
        return result

    def guide_data_loading(self, problem_text: str, data_profiles: dict) -> dict:
        """AI 检查数据文件，指出每道题该用哪些列、如何关联、如何聚合"""
        print("  [AI-Data] Analyzing data requirements for each sub-problem...")

        profiles_text = ""
        for name, profile in data_profiles.items():
            profiles_text += f"\n文件: {name}\n"
            profiles_text += f"  行列: {profile['shape'][0]} x {profile['shape'][1]}\n"
            profiles_text += f"  列名: {profile['columns']}\n"
            profiles_text += f"  样本数据(前5行):\n{profile.get('sample', 'N/A')}\n"

        system = """You are a data engineer for a CUMCM paper.
For each sub-problem, specify EXACTLY:
1. Which data file(s) to use
2. Which columns are inputs (features, costs, quantities)
3. Which columns are outputs (targets, benefits, labels)
4. How to join tables (which key columns)
5. How to aggregate (group by, sum/average, filter date range)
6. Which columns are ID/encoding (do NOT use these for calculations!)
7. Any data cleaning needed (missing values, outliers, type conversion)

Be PRECISE — these instructions will be executed programmatically."""

        user = f"""Problem:
{problem_text[:3000]}

Data profiles:{profiles_text[:5000]}

Return JSON:
{{
    "per_problem": [
        {{
            "sub_problem_id": 1,
            "files": ["附件1(1)"],
            "key_columns": ["column names for joining"],
            "feature_columns": ["columns to use as model inputs"],
            "target_columns": ["columns to predict/optimize"],
            "id_columns": ["columns that are IDs — do NOT use for math"],
            "aggregation": "how to aggregate (e.g. group by 单品编码, sum 销量)",
            "join_instructions": "how to join tables",
            "date_filter": "date range filter if applicable",
            "notes": "any data quality issues to handle"
        }}
    ],
    "cross_table_joins": ["global join instructions"],
    "data_quality_issues": ["issues found and how to fix"]
}}"""

        result = self._call_llm_json(system, user)
        for pp in result.get("per_problem", []):
            print(f"  [AI-Data] Q{pp.get('sub_problem_id','?')}: "
                  f"files={pp.get('files','?')}, "
                  f"features={pp.get('feature_columns','?')[:3]}...")
        return result

    # ================================================================
    # AI 验证结果（Phase 3+）
    # ================================================================

    def validate_results(self, problem_text: str, sub_problems: list,
                         results: dict, data_guide: dict) -> dict:
        """AI 验证求解结果是否合理——数量级、一致性、物理意义"""
        print("  [AI-Validate] Checking result correctness...")

        sp_summary = []
        for sp in sub_problems:
            sp_id = sp["id"]
            r = results.get(f"sub_{sp_id}", {})
            sp_summary.append({
                "id": sp_id, "type": sp.get("type", ""), "model": sp.get("model", ""),
                "result_keys": list(r.keys()),
                "result_values": {k: str(v)[:100] for k, v in r.items() if k != "summary"},
                "summary": r.get("summary", ""),
            })

        system = """You are a CUMCM result validator. Check each sub-problem's output:
1. Are the numeric magnitudes physically reasonable? (e.g. vegetable sales should be kg, not millions of yuan)
2. Are constraints satisfied? (budget, quantity limits, display minimums)
3. Are results internally consistent? (costs + profits should make sense)
4. Do results match the problem requirements? (right number of items, right time range)
5. Are any results using ID codes as numeric values? (严重错误!)
Flag EVERY issue. Be harsh."""

        user = f"""Problem: {problem_text[:2000]}
Sub-problems: {json.dumps(sp_summary, ensure_ascii=False)[:3000]}
Data guide: {json.dumps(data_guide, ensure_ascii=False)[:1000]}

Return JSON:
{{
    "overall_valid": true/false,
    "checks": [
        {{
            "sub_problem_id": 1,
            "valid": true/false,
            "issues": ["specific issue 1", "issue 2"],
            "severity": "critical/warning/ok",
            "fix_needed": "exactly what needs to change"
        }}
    ]
}}"""

        result = self._call_llm_json(system, user)
        valid_count = sum(1 for c in result.get("checks", []) if c.get("valid"))
        total = len(result.get("checks", []))
        print(f"  [AI-Validate] {valid_count}/{total} sub-problems valid")
        for c in result.get("checks", []):
            if not c.get("valid"):
                print(f"       Q{c.get('sub_problem_id','?')}: {c.get('severity','?')} — {c.get('fix_needed','')[:100]}")
        return result

    # ================================================================
    # AI 修正求解（Phase 3++）
    # ================================================================

    def fix_solving_issues(self, problem_text: str, validation: dict,
                           data_guide: dict) -> dict:
        """AI 给出具体修正指令——哪些列、什么参数、如何重新求解"""
        print("  [AI-Fix] Generating fixing instructions...")

        issues = [c for c in validation.get("checks", []) if not c.get("valid")]

        system = """You are fixing CUMCM solver issues. For each problem, specify:
1. Which solver to use
2. Exact column names for costs, benefits, features, targets
3. How to preprocess the data (aggregation, filtering, joining)
4. Solver parameters (constraints, bounds, objective direction)
5. Expected output format
Be extremely specific — these instructions must be executable by Python code."""

        user = f"""Problem: {problem_text[:2000]}
Issues found: {json.dumps(issues, ensure_ascii=False)}
Data guide: {json.dumps(data_guide, ensure_ascii=False)[:1500]}

Return JSON:
{{
    "fixes": [
        {{
            "sub_problem_id": 1,
            "solver_type": "evaluation/prediction/optimization/statistics",
            "data_file": "which file",
            "data_processing": "exact pandas operations (groupby, merge, filter)",
            "columns_for_solver": {{"cost_col": "exact_name", "benefit_col": "exact_name"}},
            "solver_params": {{"key": "value"}},
            "expected_output": "what the correct output should look like"
        }}
    ],
    "re_run_order": [1, 2, 3, 4]
}}"""

        return self._call_llm_json(system, user)

    # ================================================================
    # AI 指令执行器 — 真正操作数据
    # ================================================================

    def execute_fix(self, fix_plan: dict, data_files: dict, data_profiles: dict,
                    load_full_fn) -> dict:
        """执行 AI 修正指令 — 加载数据、关联表、聚合、求解"""
        import pandas as pd
        import numpy as np
        from mathmodel.models import EvaluationSolver, StatsSolver, OptimizationSolver

        results = {}
        evaluator = EvaluationSolver()
        stats_solver = StatsSolver()
        opt = OptimizationSolver()

        for fix in fix_plan.get("fixes", []):
            sp_id = fix.get("sub_problem_id", 0)
            solver_type = fix.get("solver_type", "")
            files_needed = fix.get("files", fix.get("data_file", []))
            if isinstance(files_needed, str):
                files_needed = [files_needed]
            processing = fix.get("data_processing", "")
            col_info = fix.get("columns_for_solver", {})
            params = fix.get("solver_params", {})

            print(f"  [AI-Exec] Q{sp_id}: loading {files_needed}...")

            # Step 1: Load all needed data files (fuzzy match + full load)
            dfs = {}
            for fname in files_needed:
                fname = str(fname).strip()
                # Fuzzy match: extract key words (附件1, 附件2, etc)
                import re
                fn_key = re.sub(r'[（(]\d+[）)]', '', fname).replace('.xlsx','').replace('.csv','').strip()
                fn_num = re.search(r'(\d+)', fname)
                fn_num = fn_num.group(1) if fn_num else ''

                matched = None
                # Try exact match
                if fname in data_files:
                    matched = fname
                else:
                    # Try matching by number (附件1, 附件2...)
                    for k in data_files:
                        k_num = re.search(r'(\d+)', k)
                        k_num = k_num.group(1) if k_num else ''
                        if fn_num and fn_num == k_num:
                            matched = k
                            break
                        # Try keyword overlap
                        if any(w in k for w in fn_key.split() if len(w) > 1):
                            matched = k
                            break

                if matched:
                    df = data_files[matched]
                    profile = data_profiles.get(matched, {})
                    # Always try full load for medium+ files
                    if profile.get('size_category', 'small') != 'small' and df.shape[0] <= 500:
                        try:
                            full = load_full_fn(matched)
                            if full is not None and full.shape[0] > df.shape[0]:
                                df = full
                                data_files[matched] = full  # cache the full data
                                print(f"  [AI-Exec]     Full load: {matched} -> {df.shape[0]} rows")
                        except Exception as e:
                            print(f"  [AI-Exec]     Full load failed for {matched}: {e}")
                    dfs[matched] = df
                    print(f"  [AI-Exec]     {fname} -> {matched} ({df.shape[0]} rows)")
                else:
                    print(f"  [AI-Exec]     NOT FOUND: {fname} (available: {list(data_files.keys())[:5]})")

            if not dfs:
                print(f"  [AI-Exec] Q{sp_id}: files not found: {files_needed}")
                continue

            # Step 2: Execute data processing instructions from AI
            result_df = None

            # Check if AI specified a merge
            join_keys = fix.get("join_keys", fix.get("join_instructions", ""))
            if len(dfs) >= 2:
                # AI specified how to join
                df_list = list(dfs.values())
                result_df = df_list[0]

                for i, df2 in enumerate(df_list[1:], 1):
                    # Find common columns for merging
                    common = [c for c in result_df.columns if c in df2.columns
                              and c not in ['Unnamed: 0', 'index']]
                    if common:
                        try:
                            result_df = result_df.merge(df2, on=common[0], how='left',
                                                        suffixes=('', f'_dup{i}'))
                            # Drop duplicate columns
                            dup_cols = [c for c in result_df.columns if '_dup' in str(c)]
                            result_df = result_df.drop(columns=dup_cols)
                            print(f"  [AI-Exec]     Merged on '{common[0]}': {result_df.shape}")
                        except Exception as e:
                            print(f"  [AI-Exec]     Merge failed: {e}")

            if result_df is None:
                result_df = list(dfs.values())[0]

            # Step 3: Aggregate if AI specified
            if processing and 'group' in processing.lower():
                group_col = col_info.get("group_col")
                agg_col = col_info.get("value_col")
                if group_col and agg_col and group_col in result_df.columns:
                    result_df = result_df.groupby(group_col)[agg_col].sum().reset_index()
                    result_df.columns = ['项目', '数值']
                    print(f"  [AI-Exec]     Aggregated: {result_df.shape[0]} groups")

            # Also try date aggregation if date column exists
            date_cols = [c for c in result_df.columns if '日期' in str(c) or 'date' in str(c).lower()]
            if date_cols and processing and 'aggregate' in processing.lower():
                try:
                    result_df[date_cols[0]] = pd.to_datetime(result_df[date_cols[0]], errors='coerce')
                    num_cols = result_df.select_dtypes(include=np.number).columns.tolist()
                    if num_cols:
                        result_df = result_df.groupby(date_cols[0])[num_cols].sum()
                        print(f"  [AI-Exec]     Date aggregated: {result_df.shape}")
                except Exception:
                    pass

            if result_df is None or result_df.empty:
                print(f"  [AI-Exec] Q{sp_id}: no data after processing")
                continue

            # Step 4: Detect columns with AI help
            numeric = result_df.select_dtypes(include=np.number)
            if numeric.empty:
                print(f"  [AI-Exec] Q{sp_id}: no numeric columns")
                continue

            cols = numeric.columns.tolist()
            ai_cost = col_info.get("cost_col", "")
            ai_benefit = col_info.get("benefit_col", "")

            # Exclude ID columns
            id_cols = set(params.get("id_columns", col_info.get("id_columns", [])))
            valid_cols = [c for c in cols if c not in id_cols]

            if ai_cost and ai_cost in cols:
                cost_col = ai_cost
            else:
                cost_col = next((c for c in valid_cols if '成本' in str(c) or '价格' in str(c) or '批发' in str(c)), valid_cols[0] if valid_cols else cols[0])

            if ai_benefit and ai_benefit in cols:
                benefit_col = ai_benefit
            else:
                benefit_col = next((c for c in valid_cols if '销量' in str(c) or '收益' in str(c) or '销售' in str(c) or '利润' in str(c)), valid_cols[-1] if len(valid_cols) > 1 else cols[-1])

            print(f"  [AI-Exec]     cost={cost_col}, benefit={benefit_col}")

            # Step 5: Run solver
            if solver_type in ("evaluation", "评价"):
                matrix = numeric[valid_cols].values.astype(float) if valid_cols else numeric.values.astype(float)
                if matrix.shape[1] < 2:
                    continue
                impacts = [1] * matrix.shape[1]
                for j, c in enumerate(numeric.columns):
                    if any(kw in str(c) for kw in ['成本', '费用', '损耗', '率', '环境']):
                        impacts[j] = -1
                ew = evaluator.entropy_weight(matrix)
                res = evaluator.topsis(matrix, weights=ew["weights"], impacts=impacts)
                labels = result_df.iloc[:, 0].tolist() if not pd.api.types.is_numeric_dtype(result_df.iloc[:, 0]) else [f"方案{i+1}" for i in range(len(result_df))]
                best_idx = int(np.argmax(res["scores"]))
                results[f"sub_{sp_id}"] = {
                    "labels": labels,
                    "scores": [round(float(s), 4) for s in res["scores"]],
                    "rank": [int(r) for r in res["rank"]],
                    "weights": {str(c): round(float(w), 4) for c, w in zip(numeric.columns, ew["weights"])},
                    "summary": f"最优: {labels[best_idx]} (得分: {max(res['scores']):.4f})",
                }
                print(f"  [AI-Exec]     TOPSIS done: best={labels[best_idx]}")

            elif solver_type in ("prediction", "预测"):
                data_series = numeric[benefit_col].dropna().tolist()
                if len(data_series) < 4:
                    data_series = numeric.iloc[:, 0].dropna().tolist()
                if len(data_series) >= 4:
                    pred = stats_solver.grey_forecast(data_series, forecast_steps=3)
                    results[f"sub_{sp_id}"] = {
                        "original": data_series,
                        "fitted": [round(v, 4) for v in pred["fitted"]],
                        "forecast": [round(v, 4) for v in pred["forecast"]],
                        "mape": round(pred["mape"], 2),
                        "grade": pred["grade"],
                        "params": pred["params"],
                        "summary": f"MAPE={pred['mape']:.2f}% [{pred['grade']}], 预测: {[round(v,1) for v in pred['forecast']]}",
                    }
                    print(f"  [AI-Exec]     GM(1,1): MAPE={pred['mape']:.2f}%")

            elif solver_type in ("optimization", "优化"):
                costs = numeric[cost_col].values.astype(float).tolist()
                benefits = numeric[benefit_col].values.astype(float).tolist()
                budget_val = params.get("budget", sum(costs) * 0.6)

                # 0-1 knapsack greedy
                ratios = [(benefits[i] / costs[i] if costs[i] > 0 else 0, i) for i in range(min(len(costs), 30))]
                ratios.sort(key=lambda x: -x[0])
                selected_idx = []; remaining = budget_val; total_cost = 0; total_benefit = 0
                for ratio, idx in ratios:
                    if costs[idx] <= remaining:
                        selected_idx.append(idx)
                        remaining -= costs[idx]
                        total_cost += costs[idx]
                        total_benefit += benefits[idx]

                labels = result_df.iloc[:, 0].tolist() if not pd.api.types.is_numeric_dtype(result_df.iloc[:, 0]) else [f"项目{i+1}" for i in range(len(result_df))]
                selected_labels = [labels[i] for i in selected_idx]
                results[f"sub_{sp_id}"] = {
                    "selection": [str(l) for l in selected_labels],
                    "total_cost": round(total_cost, 1),
                    "total_population": round(total_benefit, 1),
                    "budget": round(budget_val, 1),
                    "solution": [1 if i in selected_idx else 0 for i in range(len(costs))],
                    "costs": costs, "benefits": benefits,
                    "labels_all": labels,
                    "summary": f"选择 {len(selected_labels)} 项, 成本 {total_cost:.1f}/{budget_val:.1f}",
                }
                print(f"  [AI-Exec]     Optimization: {len(selected_idx)} selected, cost={total_cost:.1f}")

            elif solver_type in ("statistics", "统计"):
                numeric = result_df.select_dtypes(include=np.number)
                if numeric.shape[1] >= 2:
                    corr = numeric.corr()
                    corr_matrix = corr.values
                    cols_list = numeric.columns.tolist()
                    top = []
                    for i in range(len(cols_list)):
                        for j in range(i+1, len(cols_list)):
                            top.append({"pair": (cols_list[i], cols_list[j]), "correlation": round(float(corr_matrix[i][j]), 4)})
                    top.sort(key=lambda x: -abs(x["correlation"]))
                    results[f"sub_{sp_id}"] = {
                        "columns": cols_list,
                        "corr_matrix": [[round(float(v), 4) for v in row] for row in corr_matrix],
                        "top_correlations": top[:15],
                        "data_shape": result_df.shape,
                        "summary": f"相关分析: {result_df.shape[0]}行×{len(cols_list)}列" + (f", 最强: {top[0]['pair'][0]}-{top[0]['pair'][1]} r={top[0]['correlation']:.3f}" if top else ""),
                    }
                    print(f"  [AI-Exec]     Statistics: {len(top)} correlations computed")
                    for t in top[:3]:
                        print(f"       {t['pair'][0]} vs {t['pair'][1]}: r={t['correlation']:.3f}")

        return results

    def write_evaluation_section(self, sub_problems: list, results: dict) -> str:
        """AI 撰写模型评价章节"""
        system = "Write a model evaluation section for a CUMCM paper in Chinese academic style."

        user = f"""Models used: {json.dumps(sub_problems, ensure_ascii=False)[:1000]}
Results summary: {json.dumps(results, ensure_ascii=False, default=str)[:1000]}

Write about:
1. Model strengths (3-5 points)
2. Model limitations (3-5 points)
3. Improvement directions
4. Generalization potential

Write 4-6 paragraphs."""

        return self._call_llm(system, user, temperature=0.4)
