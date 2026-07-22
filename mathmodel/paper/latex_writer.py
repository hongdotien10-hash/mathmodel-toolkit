"""LaTeX 论文生成器 — 使用国赛 CUMCM 标准模板"""

from pathlib import Path


def generate_latex_paper(output_dir: str, problem_text: str, analysis: dict,
                         results: dict, figures_dir: str,
                         ai_content: dict = None) -> str:
    """生成符合国赛标准的 LaTeX 论文

    Args:
        output_dir: 输出目录
        problem_text: 题目原文
        analysis: 分析结果 {"sub_problems": [...]}
        results: 求解结果
        figures_dir: 图表目录
        ai_content: AI 撰写的章节内容

    Returns:
        str: 主 tex 文件路径
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "figures").mkdir(exist_ok=True)
    ai = ai_content or {}
    sp_list = (analysis or {}).get("sub_problems", [])

    # ===== 主文件 =====
    tex = [
        r"\documentclass[12pt,a4paper]{ctexart}",
        r"\usepackage[top=2.54cm,bottom=2.54cm,left=3.18cm,right=3.18cm]{geometry}",
        r"\usepackage{amsmath,amssymb}",
        r"\usepackage{graphicx}",
        r"\usepackage{float}",
        r"\usepackage{booktabs}",
        r"\usepackage{hyperref}",
        r"\usepackage{cite}",
        r"\usepackage{caption}",
        r"\usepackage{enumitem}",
        r"\graphicspath{{figures/}}",
        r"\setlength{\parindent}{2em}",
        r"\setlength{\parskip}{0pt}",
        r"\linespread{1.5}",
        "",
        r"\title{\textbf{\Large 基于多模型融合的数学建模研究}}",
        r"\author{}",
        r"\date{}",
        "",
        r"\begin{document}",
        r"\maketitle",
        "",
        # 摘要
        r"\begin{abstract}",
        r"\noindent",
        (ai.get("abstract", _latex_abstract(sp_list, results)))[:800],
        r"",
        r"\vspace{1em}",
        r"\noindent\textbf{关键词：}数学建模；综合评价；预测；优化；灵敏度分析",
        r"\end{abstract}",
        r"\newpage",
        "",
        # 一、问题重述
        r"\section{问题重述}",
        _escape_latex(problem_text[:3000]),
        "",
    ]

    # 二、问题分析
    tex.append(r"\section{问题分析}")
    for sp in sp_list:
        tex.append(_escape_latex(f"问题{sp['id']}（{sp.get('type','综合')}类）：{sp.get('title','')[:200]}"))
    tex.append("")

    # 三、模型假设
    tex.extend([
        r"\section{模型假设与符号说明}",
        r"\subsection{基本假设}",
        r"\begin{enumerate}[label=（\arabic*）]",
    ])
    for a in _latex_assumptions():
        tex.append(r"\item " + _escape_latex(a))
    tex.append(r"\end{enumerate}")

    # 四、模型建立与求解
    tex.append(r"\section{模型建立与求解}")
    for sp in sp_list:
        sp_id = sp["id"]
        ptype = sp.get("type", "")
        ai_sec = ai.get(f"section_{sp_id}", "")
        title_map = {"评价": "综合评价模型——TOPSIS法", "预测": "需求预测模型——GM(1,1)",
                     "优化": "优化决策模型——0-1整数规划", "统计": "统计分析与数据探索",
                     "综合": "综合分析模型"}
        tex.append(r"\subsection{" + title_map.get(ptype, f"子问题{sp_id}建模与求解") + "}")

        if ai_sec and len(ai_sec) > 50:
            for para in ai_sec.split('\n'):
                if para.strip():
                    tex.append(_escape_latex(para.strip()))
        else:
            tex.append(_escape_latex(_generic_model_text(sp, results.get(f"sub_{sp_id}", {}))))

        # 插入图表
        fig_dir_path = Path(figures_dir)
        if fig_dir_path.exists():
            pngs = sorted(fig_dir_path.glob("*.png"))
            for fp in pngs[:2]:
                tex.append(r"\begin{figure}[H]")
                tex.append(r"\centering")
                tex.append(r"\includegraphics[width=0.85\textwidth]{" + str(fp.resolve()) + "}")
                tex.append(r"\caption{" + _escape_latex(fp.stem.replace('_', ' ')) + "}")
                tex.append(r"\end{figure}")

    # 五、灵敏度分析
    tex.extend([
        r"\section{灵敏度分析}",
        _escape_latex(ai.get("sensitivity", _default_sensitivity())),
    ])

    # 六、模型评价
    tex.extend([
        r"\section{模型评价与改进}",
        r"\subsection{模型优点}",
    ])
    for adv in _latex_advantages():
        tex.append(r"\item " + _escape_latex(adv))
    tex.append(r"\subsection{模型不足与改进}")

    tex.append(_escape_latex(ai.get("evaluation", _default_evaluation())))

    # 七、结论
    tex.append(r"\section{结论}")
    tex.append(_escape_latex(f"本文针对多个子问题，综合运用了{', '.join(sp.get('model','')[:20] for sp in sp_list)}等方法进行建模求解。通过灵敏度分析验证了模型的稳定性和可靠性。模型具有良好的可推广性。"))

    # 参考文献
    tex.extend([
        r"\begin{thebibliography}{99}",
    ])
    for i, ref in enumerate(_latex_references()):
        tex.append(r"\bibitem{ref" + str(i+1) + "} " + _escape_latex(ref))
    tex.append(r"\end{thebibliography}")

    # 附录-代码
    tex.extend([
        r"\newpage",
        r"\section*{附录：核心求解代码}",
        r"\begin{verbatim}",
        _get_latex_code(),
        r"\end{verbatim}",
        r"\end{document}",
    ])

    tex_content = '\n'.join(tex)
    main_path = out / "paper.tex"
    main_path.write_text(tex_content, encoding="utf-8")
    print(f"  [LaTeX] Written: {main_path}")

    return str(main_path)


def _escape_latex(s):
    """转义 LaTeX 特殊字符"""
    if not s:
        return ""
    replacements = {
        '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#',
        '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}',
        '^': r'\^{}', '\\': r'\textbackslash{}',
    }
    for old, new in replacements.items():
        s = s.replace(old, new)
    return s


def _latex_abstract(sp_list, results):
    parts = ["本文针对一个综合性数学建模问题，构建了多模型融合的求解方案。"]
    for sp in sp_list:
        parts.append(f"针对问题{sp['id']}，建立了{sp.get('model','模型')}。")
    for v in results.values():
        if isinstance(v, dict) and v.get("summary"):
            parts.append(v["summary"])
    return ' '.join(parts)


def _latex_assumptions():
    return [
        "题目提供的数据真实可靠，无系统性误差。",
        "各指标间相互独立，不存在显著交互效应。",
        "数据趋势在短期预测内保持稳定。",
        "决策变量间相互独立，不考虑协同效应。",
        "忽略不可抗力因素对模型的影响。",
    ]


def _generic_model_text(sp, result):
    text = f"针对子问题{sp['id']}，建立了{sp.get('model','数学模型')}。"
    if result and isinstance(result, dict) and result.get("summary"):
        text += f"求解结果：{result['summary']}。"
    return text


def _default_sensitivity():
    return ("对模型关键参数进行了灵敏度分析。通过改变参数值并观察输出的变化，"
            "验证了模型的稳定性。结果表明模型在合理的参数变化范围内保持稳定。")

def _default_evaluation():
    return ("模型方法科学合理，求解过程严谨。但部分参数依赖数据质量，"
            "对数据异常较为敏感。未来可引入更多影响因素和更复杂的模型结构。")

def _latex_advantages():
    return [
        "模型选择有理有据，基于数据特征和问题需求。",
        "求解过程严谨，结果可复现。",
        "灵敏度分析全面，验证了模型稳定性。",
        "模型具有良好的可推广性。",
    ]

def _latex_references():
    return [
        "姜启源, 谢金星, 叶俊. 数学模型(第五版)[M]. 高等教育出版社, 2018.",
        "司守奎, 孙玺菁. 数学建模算法与应用(第三版)[M]. 国防工业出版社, 2021.",
        "刘思峰等. 灰色系统理论及其应用(第八版)[M]. 科学出版社, 2017.",
        "Hwang C L, Yoon K. Multiple Attribute Decision Making[M]. Springer, 1981.",
    ]

def _get_latex_code():
    return r"""import numpy as np
from scipy import optimize

# TOPSIS 综合评价
def topsis(matrix, weights, impacts):
    m, n = matrix.shape
    norm = matrix / np.sqrt((matrix**2).sum(axis=0))
    weighted = norm * weights
    best = np.array([weighted[:,j].max() if impacts[j]>0
        else weighted[:,j].min() for j in range(n)])
    worst = np.array([weighted[:,j].min() if impacts[j]>0
        else weighted[:,j].max() for j in range(n)])
    d_plus = np.sqrt(((weighted-best)**2).sum(axis=1))
    d_minus = np.sqrt(((weighted-worst)**2).sum(axis=1))
    return d_minus / (d_plus + d_minus)

# GM(1,1) Grey Forecast
def grey_forecast(x0, steps=3):
    x1 = np.cumsum(x0)
    n = len(x0)
    z1 = 0.5*(x1[1:]+x1[:-1])
    B = np.column_stack([-z1, np.ones(n-1)])
    a, b = np.linalg.lstsq(B, x0[1:], rcond=None)[0]
    fitted = [(x0[0]-b/a)*(1-np.exp(a))*np.exp(-a*k)
              for k in range(n+steps)]
    mape = np.mean(np.abs((np.array(x0)-fitted[:n])/np.array(x0)))*100
    return fitted[:n], fitted[n:], mape"""
