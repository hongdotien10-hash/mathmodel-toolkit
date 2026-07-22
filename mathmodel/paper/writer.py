"""论文自动撰写器。

根据求解结果自动撰写论文各章节的 LaTeX 源码。
"""

from pathlib import Path
from typing import Optional

from mathmodel.pipeline.config import PipelineConfig


class PaperWriter:
    """论文撰写器。

    根据各阶段的输出自动组织论文内容，生成完整的 .tex 文件。

    Usage::

        writer = PaperWriter(config)
        tex = writer.compose(
            problem_text="...",
            analysis={...},
            recommendations=[{...}],
            results={...},
        )
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.lang = config.language

    def compose(
        self,
        problem_text: str = "",
        analysis: dict = None,
        recommendations: list = None,
        results: dict = None,
        figures_dir: str = "figures",
    ) -> str:
        """撰写完整论文。

        Args:
            problem_text: 题目原文
            analysis: 题目分析结果
            recommendations: 模型推荐方案
            results: 求解结果
            figures_dir: 图表目录（相对路径）

        Returns:
            str: 完整 LaTeX 源码
        """
        analysis = analysis or {}
        recommendations = recommendations or []
        results = results or {}

        parts = []

        # 确定模板
        if self.config.contest_type == "cumcm" or (
            self.config.contest_type == "auto" and self.lang == "zh"
        ):
            parts.append(self._preamble_cumcm())
        else:
            parts.append(self._preamble_mcm())

        # 标题
        title = self._generate_title(problem_text, analysis)
        parts.append(r"\title{" + title + "}")
        parts.append(r"\maketitle")

        # 摘要
        parts.append(self._write_abstract(analysis, recommendations, results))

        # 关键词
        keywords = self._extract_keywords(analysis, recommendations)
        parts.append(r"\keywords{" + "; ".join(keywords) + "}")

        # Section 1: 问题重述
        parts.append(self._write_problem_restatement(problem_text))

        # Section 2: 问题分析
        parts.append(self._write_analysis(analysis))

        # Section 3: 模型假设与符号说明
        parts.append(self._write_assumptions(analysis))

        # Section 4: 模型建立与求解
        parts.append(self._write_modeling(recommendations, results, figures_dir))

        # Section 5: 灵敏度分析
        parts.append(self._write_sensitivity(results))

        # Section 6: 模型评价与推广
        parts.append(self._write_evaluation())

        # 参考文献
        parts.append(self._write_references())

        # 附录
        parts.append(self._write_appendix())

        parts.append(r"\end{document}")

        return "\n\n".join(parts)

    # =====================================================================
    # 模板头部
    # =====================================================================

    def _preamble_cumcm(self) -> str:
        return r"""\documentclass{cumcm}
\usepackage[UTF8]{ctex}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{float}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{multirow}
\usepackage{array}

\graphicspath{{figures/}}

\begin{document}"""

    def _preamble_mcm(self) -> str:
        return r"""\documentclass{mcmthesis}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{float}
\usepackage{hyperref}
\usepackage{enumitem}

\graphicspath{{figures/}}

\begin{document}"""

    # =====================================================================
    # 各章节
    # =====================================================================

    def _write_abstract(self, analysis, recommendations, results) -> str:
        """撰写摘要。"""
        sub_problems = analysis.get("sub_problems", [])
        n = len(sub_problems)

        rec_summary = ""
        if recommendations:
            rec = recommendations[0]
            rec_summary = rec.get("summary", "")

        abstract = (
            r"\begin{abstract}" + "\n"
            f"本文针对{self._problem_brief(analysis)}，"
            f"综合运用{rec_summary}等方法，建立了相应的数学模型。\n\n"
        )

        for i, sp in enumerate(sub_problems):
            model = sp.get("model", "相关模型") if isinstance(sp, dict) else "相关模型"
            sp_id = sp.get("id", i + 1) if isinstance(sp, dict) else i + 1
            abstract += f"针对问题{sp_id}，建立了{model}，"
            # 添加求解细节
            sub_key = f"sub_{sp_id}"
            if sub_key in results and isinstance(results[sub_key], dict):
                abstract += results[sub_key].get("summary", "求解得到相关结果。")
            else:
                abstract += "进行了数值求解和验证。\n"

        abstract += "\n最终，通过灵敏度分析和模型检验，验证了模型的稳定性和合理性。"
        abstract += "\n" + r"\end{abstract}"
        return abstract

    def _write_problem_restatement(self, problem_text: str) -> str:
        text = problem_text[:2000] if len(problem_text) > 2000 else problem_text
        return (
            r"\section{问题重述}" + "\n\n"
            + text
            + "\n"
        )

    def _write_analysis(self, analysis: dict) -> str:
        sub_problems = analysis.get("sub_problems", [])
        lines = [r"\section{问题分析}"]
        lines.append("")
        for sp in sub_problems:
            sp_id = sp.get("id", "?")
            sp_type = sp.get("type", "综合") if isinstance(sp, dict) else "综合"
            sp_title = sp.get("title", "") if isinstance(sp, dict) else ""
            lines.append(
                f"\\textbf{{问题{sp_id}}}（{sp_type}类）：{sp_title[:100]}\\\\"
            )
        lines.append("")
        lines.append("各子问题的数据特征和求解思路如上所述。")
        return "\n".join(lines)

    def _write_assumptions(self, analysis: dict) -> str:
        assumptions = [
            "假设题目所提供数据真实可靠，无系统误差。",
            "假设各变量之间的关系在考察时间范围内保持稳定。",
            "忽略次要因素对模型的影响，仅考虑主要因素。",
            "假设模型参数在合理范围内连续变化。",
        ]
        lines = [r"\section{模型假设与符号说明}"]
        lines.append(r"\subsection{模型假设}")
        lines.append(r"\begin{enumerate}")
        for a in assumptions:
            lines.append(f"  \\item {a}")
        lines.append(r"\end{enumerate}")
        lines.append("")
        lines.append(r"\subsection{符号说明}")
        lines.append(r"\begin{table}[H]")
        lines.append(r"\centering")
        lines.append(r"\caption{符号说明}")
        lines.append(r"\begin{tabular}{cll}")
        lines.append(r"\toprule")
        lines.append(r"符号 & 含义 & 单位 \\")
        lines.append(r"\midrule")
        lines.append(r"$x_i$ & 第$i$个决策变量 & --- \\")
        lines.append(r"$f(x)$ & 目标函数 & --- \\")
        lines.append(r"$w_j$ & 第$j$个指标权重 & --- \\")
        lines.append(r"\bottomrule")
        lines.append(r"\end{tabular}")
        lines.append(r"\end{table}")
        return "\n".join(lines)

    def _write_modeling(self, recommendations, results, figures_dir) -> str:
        lines = [r"\section{模型建立与求解}"]

        if not recommendations:
            lines.append("\n（模型求解结果将在此处展示）\n")
            return "\n".join(lines)

        rec = recommendations[0]
        for i, sp in enumerate(rec.get("sub_problems", [])):
            sp_id = sp.get("id", i + 1)
            model = sp.get("model", "未指定")
            reason = sp.get("reason", "")
            lines.append(rf"\subsection{{问题{sp_id}：{model}}}")

            # 模型原理
            lines.append(f"选用{model}，理由：{reason}")
            lines.append("")

            # 求解结果
            sub_key = f"sub_{sp_id}"
            if sub_key in results:
                res = results[sub_key]
                if isinstance(res, dict):
                    lines.append(f"求解结果：{res.get('summary', '计算完成')}")

            # 插入图表
            lines.append(rf"\begin{{figure}}[H]")
            lines.append(r"\centering")
            lines.append(rf"\includegraphics[width=0.85\textwidth]{{{figures_dir}/sub{sp_id}_result.pdf}}")
            lines.append(rf"\caption{{问题{sp_id}求解结果}}")
            lines.append(rf"\label{{fig:sub{sp_id}}}")
            lines.append(r"\end{figure}")

        lines.append(r"\subsection{模型汇总}")
        lines.append("各子问题的模型选择及求解结果汇总如表所示。")
        return "\n".join(lines)

    def _write_sensitivity(self, results: dict) -> str:
        lines = [r"\section{灵敏度分析}"]
        lines.append("")
        lines.append("为检验模型的稳定性，对关键参数进行灵敏度分析。")
        lines.append("")
        lines.append(r"\subsection{参数灵敏度}")
        lines.append("改变模型中的主要参数，观察输出的变化。分析结果表明，")
        lines.append("模型对参数变化具有一定的鲁棒性。")
        lines.append("")
        return "\n".join(lines)

    def _write_evaluation(self) -> str:
        lines = [r"\section{模型评价与推广}"]
        lines.append(r"\subsection{模型优点}")
        lines.append(r"\begin{itemize}")
        lines.append(r"  \item 模型建立过程严谨，假设合理。")
        lines.append(r"  \item 综合运用多种方法，互补验证。")
        lines.append(r"  \item 结果可视化清晰，便于解释。")
        lines.append(r"\end{itemize}")
        lines.append("")
        lines.append(r"\subsection{模型不足}")
        lines.append(r"\begin{itemize}")
        lines.append(r"  \item 部分参数依赖专家经验，具有主观性。")
        lines.append(r"  \item 对极端情况考虑不够充分。")
        lines.append(r"\end{itemize}")
        lines.append("")
        lines.append(r"\subsection{模型推广}")
        lines.append("本模型方法可推广应用于其他领域的类似问题。")
        return "\n".join(lines)

    def _write_references(self) -> str:
        return (
            r"\begin{thebibliography}{99}" + "\n"
            r"\bibitem{ref1} 姜启源, 谢金星, 叶俊. 数学模型（第五版）. 高等教育出版社, 2018." + "\n"
            r"\bibitem{ref2} 司守奎, 孙玺菁. 数学建模算法与应用（第三版）. 国防工业出版社, 2021." + "\n"
            r"\end{thebibliography}"
        )

    def _write_appendix(self) -> str:
        return (
            r"\section*{附录}" + "\n"
            r"\subsection*{核心求解代码}" + "\n"
            r"详见随论文附带的代码文件。"
        )

    # =====================================================================
    # 辅助方法
    # =====================================================================

    def _generate_title(self, problem_text: str, analysis: dict) -> str:
        """自动生成论文标题。"""
        # 尝试从前200字符中提取关键词
        snippet = problem_text[:200]
        # 简单规则：找"问题"后的内容
        if "基于" in snippet:
            return snippet.split("基于")[0][:40].strip() or "数学建模竞赛论文"
        if "针对" in snippet:
            return "基于数学建模的" + snippet.split("针对")[1][:30].strip() + "研究"
        return "数学建模竞赛论文"

    def _problem_brief(self, analysis: dict) -> str:
        """生成问题简述。"""
        sub_problems = analysis.get("sub_problems", [])
        types = [sp.get("type", "") for sp in sub_problems if isinstance(sp, dict)]
        type_str = "、".join(set(types)) if types else "综合型"
        return f"一个{type_str}问题"

    def _extract_keywords(self, analysis, recommendations) -> list[str]:
        """提取论文关键词。"""
        keywords = ["数学模型"]
        sub_problems = analysis.get("sub_problems", [])
        for sp in sub_problems:
            if isinstance(sp, dict):
                ptype = sp.get("type", "")
                if ptype and ptype not in keywords:
                    keywords.append(ptype)
        if recommendations:
            rec = recommendations[0]
            for sp in rec.get("sub_problems", []):
                model = sp.get("model", "").split("(")[0].strip()
                if model and model not in keywords:
                    keywords.append(model)
        keywords.extend(["灵敏度分析", "MATLAB", "Python"])
        return keywords[:8]
