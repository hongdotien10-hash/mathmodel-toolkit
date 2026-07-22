"""
====================================================================
 MathModel Toolkit — 一键启动脚本
====================================================================

使用方法：
  1. 将赛题文件（PDF/DOCX/TXT）和数据文件（XLSX/CSV）放入 problems/ 文件夹
  2. 运行本脚本：python start.py
  3. 论文和图表自动输出到 output/ 文件夹

文件夹结构：
  problems/
    ├── 赛题1/
    │   ├── 题目.pdf          （赛题文件）
    │   ├── 附件1.xlsx         （数据文件）
    │   └── 附件2.xlsx
    └── 赛题2/
        ├── 题目.docx
        └── 数据.csv

  output/
    ├── 赛题1/
    │   ├── 论文.docx          （生成的 Word 论文）
    │   ├── figures/           （生成的图表 PDF）
    │   └── results.json       （数值结果）
    └── 赛题2/
        └── ...
====================================================================
"""

import sys
import json
from pathlib import Path

# 确保能找到 mathmodel 包
sys.path.insert(0, str(Path(__file__).parent))

from mathmodel.utils import set_seed, Timer
from mathmodel.preprocessing import MissingHandler, OutlierDetector
from mathmodel.analyzer import ProblemClassifier, ModelKnowledgeBase
from mathmodel.models import EvaluationSolver, StatsSolver, OptimizationSolver
from mathmodel.sensitivity import SensitivityAnalyzer
from mathmodel.visualization import Plotter, set_style
from mathmodel.paper.word_writer import generate_paper
import pandas as pd
import numpy as np

set_seed(42)

# ================================================================
# 第一步：扫描 problems 文件夹
# ================================================================
PROBLEMS_DIR = Path(__file__).parent / "problems"
OUTPUT_DIR = Path(__file__).parent / "output"

print("╔══════════════════════════════════════════════╗")
print("║     MathModel Toolkit — 一键求解启动         ║")
print("╚══════════════════════════════════════════════╝")
print()

# 列出所有题目
problem_dirs = sorted([
    d for d in PROBLEMS_DIR.iterdir()
    if d.is_dir() and not d.name.startswith('.')
])

if not problem_dirs:
    print("❌ 没有找到题目！")
    print(f"   请将赛题文件放入: {PROBLEMS_DIR}")
    print("   例如: problems/我的赛题/题目.pdf")
    print("              problems/我的赛题/附件1.xlsx")
    sys.exit(1)

print(f"📂 找到 {len(problem_dirs)} 个题目：")
for i, d in enumerate(problem_dirs):
    files = list(d.iterdir())
    print(f"  [{i+1}] {d.name}  ({len(files)} 个文件)")
    for f in files:
        print(f"       └─ {f.name}")

# 如果只有一个题目，直接运行；否则让用户选择
if len(problem_dirs) == 1:
    choice = 1
    print(f"\n🚀 自动选择: {problem_dirs[0].name}")
else:
    print()
    try:
        choice = int(input("请选择题目编号: "))
    except (ValueError, EOFError):
        choice = 1
        print(f"自动选择第 1 个")

selected_dir = problem_dirs[choice - 1]
problem_name = selected_dir.name
output_dir = OUTPUT_DIR / problem_name

print(f"\n{'='*50}")
print(f"  正在求解: {problem_name}")
print(f"{'='*50}\n")

# ================================================================
# 第二步：读取题目和数据
# ================================================================
problem_text = ""
data_files = {}

for f in selected_dir.iterdir():
    suffix = f.suffix.lower()
    if suffix in ('.txt',):
        problem_text = f.read_text(encoding='utf-8')
        print(f"📄 题目: {f.name} ({len(problem_text)} 字符)")
    elif suffix in ('.pdf', '.docx'):
        # PDF/DOCX 直接用文本方式读取标题
        problem_text = f"[题目文件: {f.name}]\n请将题目内容保存为 .txt 格式以获得最佳解析效果"
        print(f"📄 题目: {f.name} (二进制格式)")
    elif suffix in ('.xlsx', '.xls', '.csv'):
        try:
            if suffix == '.csv':
                data_files[f.stem] = pd.read_csv(f)
            else:
                data_files[f.stem] = pd.read_excel(f)
            print(f"📊 数据: {f.name} {data_files[f.stem].shape}")
        except Exception as e:
            print(f"⚠️  跳过 {f.name}: {e}")

if not problem_text:
    # 找任意文本文件
    for f in selected_dir.iterdir():
        if f.suffix in ('.txt',):
            problem_text = f.read_text(encoding='utf-8')

if not problem_text:
    problem_text = "(未找到题目文本，请在 problems 文件夹中放入 .txt 格式的题目文件)"

print()

# ================================================================
# 第三步：题目分析 & 模型推荐
# ================================================================
print("─" * 40)
print("  📋 题目分析 & 模型推荐")
print("─" * 40)

classifier = ProblemClassifier()
kb = ModelKnowledgeBase()

# 扫描题目中的子问题（取完整行，不截断）
sub_problems_text = []
lines = problem_text.split('\n')
for i, line in enumerate(lines):
    line = line.strip()
    if not line:
        continue
    if '问题' in line and any(c in line for c in '123456789一二三四五六七八九'):
        # 收集上下文：本行+后几行直到下一问题
        context = line
        for j in range(i+1, min(i+4, len(lines))):
            if '问题' in lines[j] and any(c in lines[j] for c in '123456789'):
                break
            context += ' ' + lines[j].strip()
        sub_problems_text.append(context[:300])  # 足够的上下文
        if len(sub_problems_text) >= 5:  # 最多5个子问题
            break

if not sub_problems_text:
    sub_problems_text = [problem_text[:200]]

sub_problems = []
for i, text in enumerate(sub_problems_text):
    result = classifier.classify(text)
    candidates = kb.query(problem_type=result['type'], top_k=3)
    model_name = candidates[0]['model'] if candidates else '待定'
    model_score = candidates[0]['score'] if candidates else 0
    reason = candidates[0]['reason'] if candidates else ''

    sub_problems.append({
        'id': i + 1,
        'title': text,
        'type': result['type'],
        'confidence': result['confidence'],
        'model': model_name,
        'score': model_score,
        'reason': reason,
    })

    print(f"  子问题{i+1}: [{result['type']}] → {model_name} (分数:{model_score:.0%})")
    print(f"           {reason}")

# ================================================================
# 第四步：模型求解
# ================================================================
print()
print("─" * 40)
print("  ⚙️  模型求解")
print("─" * 40)

all_results = {}

for sp in sub_problems:
    ptype = sp['type']
    print(f"\n  >>> 子问题{sp['id']}: {sp['model']}")

    # ---- 评价类：TOPSIS ----
    if ptype == '评价' and data_files:
        with Timer():
            evaluator = EvaluationSolver()
            # 找评价型数据（含多个评分指标列的表）
            best_name, best_df = None, None
            for name, df in data_files.items():
                num_cols = df.select_dtypes(include=np.number).shape[1]
                if num_cols >= 3:
                    best_name, best_df = name, df
                    break
            if best_df is None:
                best_name, best_df = next(iter(data_files.items()))
            name, df = best_name, best_df
            numeric_df = df.select_dtypes(include=np.number)
            if numeric_df.shape[1] >= 3:
                matrix = numeric_df.values
                # 自动计算权重
                ew = evaluator.entropy_weight(matrix)
                # TOPSIS（第1、3列正向，第2、4列负向）简单启发
                n_cols = matrix.shape[1]
                impacts = [1] * n_cols
                # 含"成本""环境"关键词的列设为负向
                for j, col in enumerate(numeric_df.columns):
                    if any(kw in str(col) for kw in ['成本', '环境', '影响', '费用']):
                        impacts[j] = -1
                result = evaluator.topsis(matrix, weights=ew['weights'], impacts=impacts)
                # 取地点列名
                label_col = df.columns[0] if len(df.columns) > 0 else '方案'
                labels = df.iloc[:, 0].tolist()
                all_results[f'sub_{sp["id"]}'] = {
                    'scores': [round(s, 4) for s in result['scores'].tolist()],
                    'rank': [int(r) for r in result['rank'].tolist()],
                    'labels': labels,
                    'summary': f'TOPSIS 评价完成，最优: {labels[int(np.argmax(result["scores"]))]}',
                }
                print(f"    最优方案: {labels[int(np.argmax(result['scores']))]} "
                      f"(得分: {max(result['scores']):.4f})")
                print(f"    排名: {' > '.join(str(labels[i]) for i in np.argsort(result['scores'])[::-1])}")

    # ---- 预测类：灰色预测 ----
    elif ptype == '预测' and data_files:
        with Timer():
            solver = StatsSolver()
            # 找时序型数据（较少列、数值型、有增长趋势的表）
            best_name, best_df = None, None
            for name, df in data_files.items():
                num_cols = df.select_dtypes(include=np.number).shape[1]
                if num_cols <= 3 and df.shape[0] >= 4:
                    best_name, best_df = name, df
                    break
            if best_df is None:
                best_name, best_df = next(iter(data_files.items()))
            name, df = best_name, best_df
            # 找数值列
            # 找非年份/非序号的真正数值列（数值范围大的优先）
            data_col = None
            for col in df.columns:
                if df[col].dtype in ('int64', 'float64'):
                    if any(kw in str(col).lower() for kw in ['需求', '量', '值', 'demand', 'value', '产量']):
                        data_col = col
                        break
            if data_col is None:
                for col in df.columns:
                    if df[col].dtype in ('int64', 'float64') and df[col].max() > 10:
                        data_col = col
                        break
            if data_col:
                data = df[data_col].tolist()
                pred = solver.grey_forecast(data, forecast_steps=3)
                all_results[f'sub_{sp["id"]}'] = {
                    'forecast': [round(v, 2) for v in pred['forecast']],
                    'fitted': [round(v, 2) for v in pred['fitted']],
                    'mape': pred['mape'],
                    'grade': pred['grade'],
                    'params': pred['params'],
                    'summary': f'灰色预测完成，MAPE={pred["mape"]:.2f}%，未来3年: {[round(v,1) for v in pred["forecast"]]}',
                }
                print(f"    MAPE: {pred['mape']:.2f}%  [{pred['grade']}]")
                print(f"    预测: {[round(v, 1) for v in pred['forecast']]}")

    # ---- 优化类：整数规划 ----
    elif ptype == '优化' and data_files:
        with Timer():
            opt = OptimizationSolver()
            # 找结构化决策数据（多列数值、含成本和收益的表）
            best_name, best_df = None, None
            for name, df in data_files.items():
                num_cols = df.select_dtypes(include=np.number).shape[1]
                if num_cols >= 3:
                    best_name, best_df = name, df
                    break
            if best_df is None:
                best_name, best_df = next(iter(data_files.items()))
            name, df = best_name, best_df
            numeric = df.select_dtypes(include=np.number)
            if numeric.shape[1] >= 2:
                # 找成本列和收益列
                cols = numeric.columns.tolist()
                cost_col, benefit_col = None, None
                for c in cols:
                    if any(kw in str(c) for kw in ['成本', '费用', 'cost', '预算']):
                        cost_col = c
                    elif any(kw in str(c) for kw in ['覆盖', '人口', '收益', '效益', 'benefit', 'pop']):
                        benefit_col = c
                if cost_col is None:
                    cost_col = cols[1] if len(cols) > 1 else cols[0]
                if benefit_col is None:
                    benefit_col = cols[2] if len(cols) > 2 else cols[1]
                costs = numeric[cost_col].tolist()
                benefits = numeric[benefit_col].tolist()

                # 预算约束（默认 100）
                budget = 100.0
                c = [-b for b in benefits]
                A_ub = [costs]
                b_ub = [budget]

                try:
                    result = opt.integer_program(c=c, A_ub=A_ub, b_ub=b_ub,
                                                  bounds=(0, 1), binary=True)
                    if result.success:
                        labels = df.iloc[:, 0].tolist()
                        selected = [labels[i] for i, v in enumerate(result.x) if v > 0.5]
                        total_cost = sum(costs[i] for i, v in enumerate(result.x) if v > 0.5)
                        total_benefit = sum(benefits[i] for i, v in enumerate(result.x) if v > 0.5)
                        all_results[f'sub_{sp["id"]}'] = {
                            'selection': selected,
                            'total_cost': round(total_cost, 1),
                            'total_population': round(total_benefit, 1),
                            'solution': [int(v) for v in result.x],
                            'summary': f'优化完成，选择 {selected}，成本 {total_cost:.0f}，覆盖 {total_benefit:.0f}',
                        }
                        print(f"    选择: {selected}")
                        print(f"    成本: {total_cost:.0f} / 预算: {budget:.0f}")
                        print(f"    覆盖: {total_benefit:.0f}")
                except Exception as e:
                    print(f"    ⚠️ 优化求解失败: {e}")

# ================================================================
# 第五步：灵敏度分析
# ================================================================
print()
print("─" * 40)
print("  📊 灵敏度分析")
print("─" * 40)

sa = SensitivityAnalyzer()
for key, value in all_results.items():
    if 'forecast' in value:
        data = value.get('fitted', [])
        if len(data) >= 4:

            def gm_model(params):
                s = StatsSolver()
                r = s.grey_forecast(params.tolist(), forecast_steps=3)
                return float(r['forecast'][-1]) if r['forecast'] else 0

            robust = sa.robustness_check(gm_model, data, noise_pct=0.05, n_samples=300)
            value['sensitivity'] = {
                'cv': robust['cv'],
                'is_robust': robust['is_robust'],
            }
            print(f"  预测模型鲁棒性: CV={robust['cv']:.4f}, "
                  f"{'稳定' if robust['is_robust'] else '需关注'}")

# ================================================================
# 第六步：生成图表
# ================================================================
print()
print("─" * 40)
print("  🎨 生成图表")
print("─" * 40)

fig_dir = output_dir / "figures"
fig_dir.mkdir(parents=True, exist_ok=True)

set_style("zh")
plotter = Plotter(language="zh")

for key, value in all_results.items():
    # TOPSIS 得分图
    if 'scores' in value and 'labels' in value:
        fig, ax = plotter.bar(
            x=value['labels'], y=value['scores'],
            xlabel="方案", ylabel="得分",
            title="TOPSIS 综合评价得分",
            labels=value['labels'],
        )
        plotter.save(fig, fig_dir / "topsis_scores.pdf")
        print(f"  ✅ TOPSIS 得分图")

    # 预测图
    if 'forecast' in value and 'fitted' in value:
        n = len(value['fitted'])
        all_y = value['fitted'] + value['forecast']
        x = list(range(len(all_y)))
        fig, ax = plotter.line(x=x, y=all_y, xlabel="时间", ylabel="值",
                               title="灰色预测结果", markers=True)
        ax.scatter(x[:n], value['fitted'], color='red', s=50, zorder=5, label='拟合')
        ax.scatter(x[n:], value['forecast'], color='green', s=50, zorder=5, label='预测')
        ax.legend()
        plotter.save(fig, fig_dir / "forecast.pdf")
        print(f"  ✅ 预测趋势图")

plotter.close_all()

# ================================================================
# 第七步：生成 Word 论文
# ================================================================
print()
print("─" * 40)
print("  📝 生成 Word 论文")
print("─" * 40)

paper_path = generate_paper(
    output_path=str(output_dir / "论文.docx"),
    problem_text=problem_text,
    analysis={'sub_problems': sub_problems},
    recommendations=[{
        'summary': ' → '.join(sp['model'] for sp in sub_problems),
        'confidence': sum(sp['score'] for sp in sub_problems) / max(len(sub_problems), 1),
        'sub_problems': sub_problems,
    }],
    results=all_results,
    figures_dir=str(fig_dir),
)

print(f"  ✅ 论文已生成: {paper_path}")

# ================================================================
# 保存结果
# ================================================================
results_json = {
    'problem': problem_name,
    'sub_problems': sub_problems,
    'results': {
        k: {sk: sv for sk, sv in v.items() if sk != 'summary'}
        for k, v in all_results.items()
    },
}
with open(output_dir / 'results.json', 'w', encoding='utf-8') as f:
    json.dump(results_json, f, ensure_ascii=False, indent=2, default=str)

# ================================================================
# 完成
# ================================================================
print()
print("╔══════════════════════════════════════════════╗")
print("║          ✅ 求解完成！                        ║")
print("╠══════════════════════════════════════════════╣")
print(f"║  论文: output/{problem_name}/论文.docx")
print(f"║  图表: output/{problem_name}/figures/")
print(f"║  数据: output/{problem_name}/results.json")
print("╚══════════════════════════════════════════════╝")
print()
print("💡 下次使用：把新赛题放入 problems/ 文件夹，运行 python start.py 即可")