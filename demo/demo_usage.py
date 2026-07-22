"""
MathModel Toolkit 完整使用演示
================================
展示从数据到论文的全流程各模块使用方法
"""

# ================================================================
# 0. 环境准备
# ================================================================
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from mathmodel import Pipeline, PipelineConfig
from mathmodel.analyzer import ModelKnowledgeBase, ProblemClassifier
from mathmodel.preprocessing import MissingHandler, OutlierDetector, Normalizer
from mathmodel.models import EvaluationSolver, StatsSolver, OptimizationSolver
from mathmodel.visualization import Plotter, set_style
from mathmodel.sensitivity import SensitivityAnalyzer
from mathmodel.utils import set_seed, Timer
import pandas as pd
import numpy as np

set_seed(42)

demo_dir = Path(__file__).parent
output_dir = demo_dir / "output_demo"
output_dir.mkdir(exist_ok=True)
fig_dir = output_dir / "figures"
fig_dir.mkdir(exist_ok=True)

print("=" * 60)
print("  MathModel Toolkit 完整演示")
print("=" * 60)

# ================================================================
# 1. 数据预处理
# ================================================================
print("\n" + "─" * 40)
print("  1. 数据预处理")
print("─" * 40)

# 读取数据
df_eval = pd.read_excel(demo_dir / "附件1_评价数据.xlsx")
df_demand = pd.read_excel(demo_dir / "附件2_需求数据.xlsx")

print(f"\n附件1 - 评价数据: {df_eval.shape[0]} 行 x {df_eval.shape[1]} 列")
print(df_eval.to_string(index=False))

print(f"\n附件2 - 需求数据: {df_demand.shape[0]} 行 x {df_demand.shape[1]} 列")
print(df_demand.to_string(index=False))

# 缺失值检查
handler = MissingHandler(strategy="median")
print(f"\n缺失值报告:\n{handler.report(df_eval)}")

# 异常值检测
detector = OutlierDetector(method="iqr")
print(f"\n异常值报告:\n{detector.report(df_eval[['建设成本(万元)', '覆盖人口(万人)']])}")

# 标准化
norm = Normalizer(method="minmax")
df_norm = norm.fit_transform(df_eval[['建设成本(万元)', '覆盖人口(万人)']])
print(f"\n归一化后:\n{df_norm.to_string(index=False)}")

# ================================================================
# 2. 题目分析 & 模型推荐
# ================================================================
print("\n" + "─" * 40)
print("  2. 题目分析 & 智能模型推荐")
print("─" * 40)

# 读取题目
problem_text = (demo_dir / "sample_problem.txt").read_text(encoding="utf-8")

# 题型分类
classifier = ProblemClassifier()
sub_problems = [
    {"id": 1, "title": "问题1：请建立综合评价模型，对5个备选地点进行排序。",
     "full_text": "建立综合评价模型，对5个备选地点排序。建设成本、交通便利度、覆盖人口、环境影响"},
    {"id": 2, "title": "问题2：预测未来3年的物流需求量",
     "full_text": "该城市过去6年物流需求量为12,15,19,24,30,38万吨，请预测未来3年的需求量。时间序列预测"},
    {"id": 3, "title": "问题3：建立优化模型选择配送中心",
     "full_text": "预算不超过100万元，每个配送中心处理能力20万吨。选择配送中心使总覆盖人口最大化。整数规划"},
]

for sp in sub_problems:
    result = classifier.classify(sp["full_text"])
    sp["type"] = result["type"]
    sp["confidence"] = result["confidence"]
    print(f"\n子问题{sp['id']}: {sp['title'][:50]}")
    print(f"  题型: {result['type']} (置信度: {result['confidence']:.1%})")
    print(f"  各类得分: {result['scores']}")

# 模型推荐
kb = ModelKnowledgeBase()
print(f"\n知识库支持的题型: {kb.list_problem_types()}")

for sp in sub_problems:
    candidates = kb.query(problem_type=sp["type"], top_k=3)
    print(f"\n子问题{sp['id']} [{sp['type']}] 推荐模型:")
    for i, c in enumerate(candidates):
        print(f"  [{i+1}] {c['model']} (分数: {c['score']:.2f})")
        print(f"      理由: {c['reason']}")

# ================================================================
# 3. 模型求解 — 使用真实求解器
# ================================================================
print("\n" + "─" * 40)
print("  3. 模型求解")
print("─" * 40)

# ---- 3a. 子问题1: TOPSIS 评价 ----
print("\n>>> 子问题1: TOPSIS 综合评价")
with Timer("TOPSIS"):
    evaluator = EvaluationSolver()

    # 构建决策矩阵: 成本(负向)、交通(正向)、覆盖(正向)、环境(负向)
    matrix = df_eval[['建设成本(万元)', '交通便利度(1-10)', '覆盖人口(万人)', '环境影响(1-10)']].values

    # 熵权法计算权重
    entropy_result = evaluator.entropy_weight(matrix)
    print(f"熵权法权重: 成本={entropy_result['weights'][0]:.3f}, "
          f"交通={entropy_result['weights'][1]:.3f}, "
          f"覆盖={entropy_result['weights'][2]:.3f}, "
          f"环境={entropy_result['weights'][3]:.3f}")

    # TOPSIS 评价
    topsis_result = evaluator.topsis(
        matrix,
        weights=entropy_result['weights'],
        impacts=[-1, 1, 1, -1],  # 成本(-)、交通(+)、覆盖(+)、环境(-)
    )

    # 排名结果
    results_df = df_eval.copy()
    results_df['TOPSIS得分'] = topsis_result['scores'].round(4)
    results_df['排名'] = topsis_result['rank']
    results_df = results_df.sort_values('排名')
    print(f"\n评价结果:")
    print(results_df[['备选地点', 'TOPSIS得分', '排名']].to_string(index=False))
    print(f"\n最优方案: {results_df.iloc[0]['备选地点']} (得分: {results_df.iloc[0]['TOPSIS得分']:.4f})")

# ---- 3b. 子问题2: 灰色预测 GM(1,1) ----
print("\n>>> 子问题2: 灰色预测 GM(1,1)")
with Timer("GM(1,1)"):
    solver = StatsSolver()
    demand_data = df_demand['物流需求量(万吨)'].tolist()

    pred_result = solver.grey_forecast(demand_data, forecast_steps=3)

    print(f"原始数据: {demand_data}")
    print(f"拟合值:   {[round(v, 2) for v in pred_result['fitted']]}")
    print(f"预测值:   {[round(v, 2) for v in pred_result['forecast']]}")
    print(f"发展系数 a = {pred_result['params']['a']:.6f}")
    print(f"灰色作用量 b = {pred_result['params']['b']:.4f}")
    print(f"MAPE = {pred_result['mape']:.2f}%")
    print(f"精度等级: {pred_result['grade']}")

# ---- 3c. 子问题3: 整数规划 ----
print("\n>>> 子问题3: 整数规划 (选择配送中心)")
with Timer("整数规划"):
    opt = OptimizationSolver()

    # 5个备选地点, 变量 xi ∈ {0,1} 表示是否选择
    # 目标: max Σ population_i * xi
    # 约束: Σ cost_i * xi <= 100
    costs = df_eval['建设成本(万元)'].tolist()
    pops = df_eval['覆盖人口(万人)'].tolist()

    # 转为最小化: min Σ -population_i * xi
    c = [-p for p in pops]

    # 约束: Σ cost_i * xi <= 100
    A_ub = [costs]
    b_ub = [100]

    ip_result = opt.integer_program(
        c=c,
        A_ub=A_ub,
        b_ub=b_ub,
        bounds=(0, 1),
        binary=True,
    )

    if ip_result.success:
        selected = [df_eval.iloc[i]['备选地点'] for i, v in enumerate(ip_result.x) if v > 0.5]
        total_cost = sum(costs[i] for i, v in enumerate(ip_result.x) if v > 0.5)
        total_pop = sum(pops[i] for i, v in enumerate(ip_result.x) if v > 0.5)
        print(f"选择方案: {selected}")
        print(f"总成本: {total_cost:.0f} 万元 (预算 100 万)")
        print(f"总覆盖人口: {total_pop:.0f} 万人")
        print(f"解向量: {ip_result.x}")
    else:
        print(f"求解失败: {ip_result.message}")

# ================================================================
# 4. 灵敏度分析
# ================================================================
print("\n" + "─" * 40)
print("  4. 灵敏度分析 (GM(1,1) 鲁棒性)")
print("─" * 40)

sa = SensitivityAnalyzer()

def gm_wrapper(params):
    """包装 GM(1,1) 预测，返回第3年预测值"""
    data = np.array(params[:6])
    result = solver.grey_forecast(data.tolist(), forecast_steps=3)
    return float(result['forecast'][-1]) if result['forecast'] else 0

# 对原始数据加噪声，检验预测稳定性
base_params = demand_data[:6]
oat_result = sa.oat(gm_wrapper, base_params, delta_pct=0.1)
print(f"基准预测(第3年): {oat_result['base_output']:.2f} 万吨")
print(f"最敏感参数: 第{oat_result['most_sensitive']+1}个数据点 "
      f"(灵敏度: {oat_result['sensitivities'][oat_result['most_sensitive']]['sensitivity']:.4f})")

robust = sa.robustness_check(gm_wrapper, base_params, noise_pct=0.05, n_samples=500)
print(f"鲁棒性检验: CV={robust['cv']:.4f}, "
      f"{'稳定' if robust['is_robust'] else '需关注'}")
print(f"95%置信区间: [{robust['ci_95'][0]:.2f}, {robust['ci_95'][1]:.2f}]")

# ================================================================
# 5. 可视化
# ================================================================
print("\n" + "─" * 40)
print("  5. 生成论文图表")
print("─" * 40)

set_style("zh", "default")
plotter = Plotter(language="zh")

# 图1: TOPSIS得分柱状图
fig1, ax1 = plotter.bar(
    x=results_df['备选地点'].tolist(),
    y=results_df['TOPSIS得分'].tolist(),
    xlabel="备选地点",
    ylabel="TOPSIS得分",
    title="各备选地点 TOPSIS 综合评价得分",
    labels=results_df['备选地點'].tolist() if '备选地點' in results_df.columns else None,
)
plotter.save(fig1, fig_dir / "fig1_topsis_scores.pdf")
print(f"  [1/4] TOPSIS 得分图 -> {fig_dir / 'fig1_topsis_scores.pdf'}")

# 图2: GM(1,1) 预测图
years = list(range(2018, 2024))
forecast_years = list(range(2024, 2027))
fig2, ax2 = plotter.line(
    x=years + forecast_years,
    y=pred_result['fitted'] + pred_result['forecast'],
    xlabel="年份", ylabel="物流需求量 (万吨)",
    title="灰色预测 GM(1,1) 物流需求量预测",
)
# 标注原始数据点
ax2.scatter(years, demand_data, color='red', s=50, zorder=5, label='原始数据')
ax2.scatter(forecast_years, pred_result['forecast'], color='green', s=50, zorder=5, label='预测值')
ax2.axvline(x=2023.5, color='gray', linestyle='--', alpha=0.5, label='预测起点')
ax2.legend()
plotter.save(fig2, fig_dir / "fig2_grey_forecast.pdf")
print(f"  [2/4] 预测图 -> {fig_dir / 'fig2_grey_forecast.pdf'}")

# 图3: 配送中心优化方案
fig3, ax3 = plotter.bar(
    x=df_eval['备选地点'].tolist(),
    y=df_eval['覆盖人口(万人)'].tolist(),
    xlabel="备选地点",
    ylabel="覆盖人口 (万人)",
    title="各备选地点覆盖人口",
    labels=df_eval['备选地点'].tolist(),
)
# 标注是否选中
for i, (xi, pop) in enumerate(zip(ip_result.x, pops)):
    if xi > 0.5:
        ax3.bar(i, pop, color='#2ca02c', alpha=0.7, label='选中' if i == 0 else '')
    else:
        ax3.bar(i, pop, color='#d62728', alpha=0.3, label='未选中' if i == 0 else '')
handles, labels = ax3.get_legend_handles_labels()
ax3.legend(handles[:2], labels[:2])
plotter.save(fig3, fig_dir / "fig3_site_selection.pdf")
print(f"  [3/4] 选址方案图 -> {fig_dir / 'fig3_site_selection.pdf'}")

# 图4: 灵敏度分析
fig4, ax4 = plotter.bar(
    x=[f"第{i+1}点" for i in range(6)],
    y=[s['sensitivity'] for s in oat_result['sensitivities']],
    xlabel="数据点",
    ylabel="相对灵敏度",
    title="GM(1,1) 参数灵敏度分析 (OAT)",
    labels=[f"第{i+1}点" for i in range(6)],
)
plotter.save(fig4, fig_dir / "fig4_sensitivity.pdf")
print(f"  [4/4] 灵敏度图 -> {fig_dir / 'fig4_sensitivity.pdf'}")

plotter.close_all()

# ================================================================
# 6. 汇总报告
# ================================================================
print("\n" + "=" * 60)
print("  求解结果汇总")
print("=" * 60)

summary = f"""
┌──────────────────────────────────────────────────────────────┐
│  数学建模演示 — 完整求解结果                                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  子问题1 (评价): TOPSIS 优劣解距离法                           │
│    最优方案: {results_df.iloc[0]['备选地点']} (得分: {results_df.iloc[0]['TOPSIS得分']:.4f})                │
│    排名: {' > '.join(results_df['备选地点'].tolist())}    │
│                                                              │
│  子问题2 (预测): 灰色预测 GM(1,1)                              │
│    精度: {pred_result['grade']}                                           │
│    未来3年: {', '.join(f'{v:.1f}' for v in pred_result['forecast'])} 万吨                  │
│    MAPE: {pred_result['mape']:.2f}%                                          │
│                                                              │
│  子问题3 (优化): 0-1整数规划                                    │
│    选择: {selected}                                     │
│    成本: {total_cost:.0f} 万 / 覆盖: {total_pop:.0f} 万人                            │
│                                                              │
│  灵敏度分析:                                                  │
│    模型稳定性: {'稳定' if robust['is_robust'] else '需关注'}                                        │
│    CV = {robust['cv']:.4f}                                              │
│                                                              │
│  图表: {fig_dir}                          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
"""

print(summary)
print(f"\n✅ 全部完成! 图表已保存到: {fig_dir}")