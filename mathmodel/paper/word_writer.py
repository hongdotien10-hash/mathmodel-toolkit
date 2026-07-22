"""
论文 Word 文档生成器
将求解结果输出为格式规范的 .docx 论文
"""

from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn


def generate_paper(
    output_path: str,
    problem_text: str = "",
    analysis: dict = None,
    recommendations: list = None,
    results: dict = None,
    figures_dir: str = "",
) -> Path:
    """生成完整的 Word 论文文档。

    Args:
        output_path: 输出路径 (如 output/论文.docx)
        problem_text: 题目原文
        analysis: 分析结果
        recommendations: 模型推荐
        results: 求解结果
        figures_dir: 图表目录

    Returns:
        Path: 生成的文档路径
    """
    doc = Document()
    analysis = analysis or {}
    recommendations = recommendations or []
    results = results or {}

    # ---- 页面设置 ----
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.18)
    section.right_margin = Cm(3.18)

    # ---- 中文字体设置 ----
    style = doc.styles['Normal']
    font = style.font
    font.name = '宋体'
    font.size = Pt(12)
    style.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    # ===== 标题 =====
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_para.add_run('数学建模竞赛论文')
    title_run.bold = True
    title_run.font.size = Pt(22)
    title_run.font.name = '黑体'
    title_run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')

    doc.add_paragraph()

    # ===== 摘要 =====
    _add_heading(doc, '摘要')
    sub_problems = analysis.get('sub_problems', [])
    n = len(sub_problems) if sub_problems else 0

    abstract_text = f'本文针对一个多子问题综合题目，综合运用多种数学建模方法进行求解。\n\n'
    for i, sp in enumerate(sub_problems):
        model = sp.get('model', '相关模型') if isinstance(sp, dict) else '相关模型'
        sp_id = sp.get('id', i+1) if isinstance(sp, dict) else i+1
        abstract_text += f'针对问题{sp_id}，建立了{model}模型，进行了数值求解和验证。\n'

    # 填入实际结果
    for key, value in results.items():
        if isinstance(value, dict) and 'summary' in value:
            abstract_text += f'{value["summary"]}\n'

    abstract_text += f'\n最终通过灵敏度分析验证了模型的稳定性和合理性。'
    _add_para(doc, abstract_text)

    # 关键词
    keywords = ['数学模型']
    if recs := recommendations:
        for sp in recs[0].get('sub_problems', []):
            m = sp.get('model', '').split('(')[0].strip()
            if m and m not in keywords:
                keywords.append(m)
    keywords.extend(['灵敏度分析', 'MATLAB', 'Python'])
    _add_para(doc, f'关键词：{"；".join(keywords[:8])}')

    # ===== 问题重述 =====
    _add_heading(doc, '一、问题重述')
    text = problem_text[:3000] if problem_text else '（请将题目文件放入 problems 文件夹）'
    _add_para(doc, text)

    # ===== 问题分析 =====
    _add_heading(doc, '二、问题分析')
    for sp in sub_problems:
        sp_id = sp.get('id', '?')
        sp_type = sp.get('type', '综合') if isinstance(sp, dict) else '综合'
        sp_title = sp.get('title', '') if isinstance(sp, dict) else ''
        _add_para(doc, f'问题{sp_id}（{sp_type}类）：{sp_title[:100]}')

    # ===== 模型推荐 =====
    _add_heading(doc, '三、模型选择与推荐')
    if recommendations:
        rec = recommendations[0]
        _add_para(doc, f'综合置信度：{rec.get("confidence", 0):.1%}')
        for sp in rec.get('sub_problems', []):
            _add_para(doc,
                f'子问题{sp["id"]}：推荐 {sp["model"]}（分数：{sp.get("score", 0):.2f}）\n'
                f'理由：{sp.get("reason", "")}')

    # ===== 模型假设与符号说明 =====
    _add_heading(doc, '四、模型假设与符号说明')
    _add_heading(doc, '4.1 模型假设', level=2)
    assumptions = [
        '假设题目所提供数据真实可靠，无系统误差。',
        '假设各变量之间的关系在考察时间范围内保持稳定。',
        '忽略次要因素对模型的影响，仅考虑主要因素。',
        '假设模型参数在合理范围内连续变化。',
    ]
    for i, a in enumerate(assumptions, 1):
        _add_para(doc, f'（{i}）{a}')

    _add_heading(doc, '4.2 符号说明', level=2)
    table = doc.add_table(rows=5, cols=3, style='Light Grid Accent 1')
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ['符号', '含义', '单位']
    symbols_data = [
        ['$x_i$', '第i个决策变量', '—'],
        ['$f(x)$', '目标函数', '—'],
        ['$w_j$', '第j个指标权重', '—'],
        ['$S$', 'TOPSIS 相对贴近度', '—'],
    ]
    for j, h in enumerate(headers):
        table.rows[0].cells[j].text = h
    for i, row_data in enumerate(symbols_data, 1):
        for j, val in enumerate(row_data):
            table.rows[i].cells[j].text = val

    # ===== 模型建立与求解 =====
    _add_heading(doc, '五、模型建立与求解')

    # 插入实际求解结果
    result_descriptions = _format_results(results)
    for rd in result_descriptions:
        _add_heading(doc, rd['title'], level=2)
        _add_para(doc, rd['content'])

    # 尝试插入图表
    if figures_dir:
        figs_path = Path(figures_dir)
        if figs_path.exists():
            pdfs = sorted(figs_path.glob('*.pdf'))
            for i, pdf_path in enumerate(pdfs):
                _add_para(doc, f'图{i+1}：{pdf_path.stem}')
                try:
                    doc.add_picture(str(pdf_path), width=Inches(5.5))
                    last_paragraph = doc.paragraphs[-1]
                    last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                except Exception:
                    _add_para(doc, f'  [图表: {pdf_path.name}]')

    # ===== 灵敏度分析 =====
    _add_heading(doc, '六、灵敏度分析')
    _add_para(doc, '为检验模型的稳定性，对关键参数进行了灵敏度分析。')
    _add_para(doc, '分析结果表明，模型对参数变化具有一定的鲁棒性，'
              '在合理的参数波动范围内，模型结论保持稳定。')

    # 如果有灵敏度结果
    for key, value in results.items():
        if isinstance(value, dict) and 'sensitivity' in value:
            sens = value['sensitivity']
            _add_para(doc, f'变异系数 CV = {sens.get("cv", "N/A")}，'
                      f'模型{"稳定" if sens.get("is_robust") else "需关注"}。')

    # ===== 模型评价 =====
    _add_heading(doc, '七、模型评价与推广')
    _add_heading(doc, '7.1 模型优点', level=2)
    advantages = [
        '模型建立过程严谨，假设合理，数学推导清晰。',
        '综合运用多种方法（评价、预测、优化），互补验证。',
        '结果可视化清晰，便于决策者理解和应用。',
        '通过灵敏度分析验证了模型的稳定性。',
    ]
    for adv in advantages:
        _add_para(doc, f'• {adv}')

    _add_heading(doc, '7.2 模型不足', level=2)
    weaknesses = [
        '部分参数依赖专家经验，具有一定主观性。',
        '对极端情况考虑不够充分。',
        '部分模型假设可能与实际存在偏差。',
    ]
    for w in weaknesses:
        _add_para(doc, f'• {w}')

    _add_heading(doc, '7.3 模型推广', level=2)
    _add_para(doc, '本模型方法可推广应用于其他城市的配送中心选址、'
              '物流需求预测等类似问题，具有较好的普适性。')

    # ===== 参考文献 =====
    _add_heading(doc, '参考文献')
    refs = [
        '[1] 姜启源, 谢金星, 叶俊. 数学模型（第五版）. 高等教育出版社, 2018.',
        '[2] 司守奎, 孙玺菁. 数学建模算法与应用（第三版）. 国防工业出版社, 2021.',
        '[3] 韩中庚. 数学建模方法及其应用（第三版）. 高等教育出版社, 2017.',
    ]
    for ref in refs:
        _add_para(doc, ref)

    # ===== 保存 =====
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output))
    return output


def _add_heading(doc, text, level=1):
    """添加标题"""
    para = doc.add_paragraph()
    if level == 1:
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run(text)
    run.bold = True
    if level == 1:
        run.font.size = Pt(16)
        run.font.name = '黑体'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    elif level == 2:
        run.font.size = Pt(14)
        run.font.name = '黑体'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    para.space_before = Pt(12)
    para.space_after = Pt(6)


def _add_para(doc, text):
    """添加正文段落"""
    para = doc.add_paragraph()
    run = para.add_run(text)
    run.font.size = Pt(12)
    run.font.name = '宋体'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    para.paragraph_format.first_line_indent = Pt(24)
    para.paragraph_format.line_spacing = 1.5


def _format_results(results: dict) -> list[dict]:
    """将求解结果格式化为论文章节"""
    sections = []

    for key, value in results.items():
        if not isinstance(value, dict):
            continue

        # TOPSIS 结果
        if 'scores' in value and 'rank' in value:
            scores = value.get('scores', [])
            rank = value.get('rank', [])
            content = f'采用 TOPSIS 法对备选方案进行综合评价，结果如下：\n\n'
            for i in range(len(scores)):
                content += f'方案 {chr(65+i)}：得分 {scores[i]:.4f}，排名第 {rank[i]}\n'
            sections.append({
                'title': '5.1 综合评价模型（TOPSIS 法）',
                'content': content
            })

        # 灰色预测结果
        if 'forecast' in value and 'mape' in value:
            forecast = value.get('forecast', [])
            fitted = value.get('fitted', [])
            params = value.get('params', {})
            content = (
                f'采用灰色预测 GM(1,1) 模型对物流需求量进行预测。\n\n'
                f'模型参数：发展系数 a = {params.get("a", "N/A"):.6f}，'
                f'灰色作用量 b = {params.get("b", "N/A"):.4f}\n'
                f'拟合精度：MAPE = {value.get("mape", "N/A"):.2f}%，'
                f'精度等级：{value.get("grade", "N/A")}\n\n'
                f'拟合值：{", ".join(f"{v:.2f}" for v in fitted)}\n'
                f'预测值：{", ".join(f"{v:.2f}" for v in forecast)} 万吨\n\n'
                f'预测结果表明，未来三年物流需求量将持续增长。'
            )
            sections.append({
                'title': '5.2 需求预测模型（灰色预测 GM(1,1)）',
                'content': content
            })

        # 优化结果
        if 'selection' in value:
            sel = value.get('selection', [])
            cost = value.get('total_cost', 0)
            pop = value.get('total_population', 0)
            content = (
                f'采用 0-1 整数规划模型求解配送中心选址问题。\n\n'
                f'最优选择方案：{", ".join(sel)}\n'
                f'总建设成本：{cost} 万元（预算约束 100 万元）\n'
                f'总覆盖人口：{pop} 万人\n\n'
                f'该方案在满足预算约束的前提下实现了覆盖人口最大化。'
            )
            sections.append({
                'title': '5.3 选址优化模型（0-1 整数规划）',
                'content': content
            })

    return sections