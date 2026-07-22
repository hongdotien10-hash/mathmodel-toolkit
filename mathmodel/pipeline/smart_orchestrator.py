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
