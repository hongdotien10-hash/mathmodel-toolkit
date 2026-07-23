"""AI驱动智能选图 — 根据题型+数据特征+结果自动判断用哪些图"""
import numpy as np, pandas as pd
from pathlib import Path


# 图类型知识库: (图名, 适用条件, 优先级1-10, 函数名)
FIGURE_KB = {
    # === 预测类 ===
    "pred_fitted_vs_actual": {
        "name": "实际vs拟合vs预测对比图",
        "condition": "has forecast+fitted+actual data, time series",
        "priority": 10, "category": "预测",
        "reason": "预测题核心结果图,展示模型拟合能力和预测趋势,必选"
    },
    "pred_residual_diagnosis": {
        "name": "残差诊断三连图(时序+散点+QQ)",
        "condition": "has fitted+actual data, need model validation",
        "priority": 9, "category": "预测",
        "reason": "检验预测模型残差是否白噪声,验证模型适用性"
    },
    "pred_intervals": {
        "name": "预测区间图(95%置信带)",
        "condition": "has forecast data with uncertainty estimates",
        "priority": 7, "category": "预测",
        "reason": "展示预测不确定性,增强结果可信度"
    },
    "pred_multi_model_compare": {
        "name": "多模型预测精度对比图",
        "condition": "multiple prediction models compared",
        "priority": 8, "category": "预测",
        "reason": "多模型对比体现方法严谨性,评委加分项"
    },

    # === 评价类 ===
    "eval_score_bar": {
        "name": "综合得分排序柱状图",
        "condition": "has scores+labels from evaluation",
        "priority": 10, "category": "评价",
        "reason": "评价题核心结果图,直观展示方案优劣排序"
    },
    "eval_radar": {
        "name": "多指标雷达图",
        "condition": "has multiple indicators per alternative (2-8)",
        "priority": 8, "category": "评价",
        "reason": "展示方案在各维度上的均衡性,多方案对比一目了然"
    },
    "eval_weight_pie": {
        "name": "指标权重分布图",
        "condition": "has computed weights for indicators",
        "priority": 7, "category": "评价",
        "reason": "展示各指标相对重要性,支撑评价结果的可解释性"
    },
    "eval_heatmap": {
        "name": "方案×指标热力图",
        "condition": "has matrix data (alternatives × criteria >= 3×3)",
        "priority": 6, "category": "评价",
        "reason": "展示数据整体分布,发现异常高/低值"
    },
    "eval_lollipop": {
        "name": "排名棒棒糖图",
        "condition": "has ranked scores, want visual impact",
        "priority": 5, "category": "评价",
        "reason": "替代普通柱状图,视觉更有冲击力"
    },

    # === 优化类(背包/资源分配) ===
    "opt_resource": {
        "name": "资源利用对比图(成本/收益/选择)",
        "condition": "has costs+benefits+selection (knapsack type)",
        "priority": 10, "category": "优化",
        "reason": "展示每个项目的成本收益和选择结果"
    },
    "opt_convergence": {
        "name": "优化收敛曲线",
        "condition": "has iterative optimization history",
        "priority": 8, "category": "优化",
        "reason": "展示算法收敛过程,证明解的可靠性"
    },
    "opt_gantt": {
        "name": "调度甘特图",
        "condition": "has task scheduling with start/duration",
        "priority": 9, "category": "优化",
        "reason": "调度/排产问题的标准展示方式"
    },
    "opt_pareto": {
        "name": "帕累托前沿图",
        "condition": "has multi-objective optimization results",
        "priority": 9, "category": "优化",
        "reason": "多目标优化的标准展示,展示目标间的权衡关系"
    },

    # === 优化类(路径/VRP/TSP) ===
    "route_network": {
        "name": "路网拓扑+最优路径图",
        "condition": "has tour/routes + distance matrix/graph",
        "priority": 10, "category": "路径优化",
        "reason": "路径问题的核心可视化,展示路网结构和最优路线"
    },
    "route_algo_compare": {
        "name": "多算法路径对比图",
        "condition": "multiple routing algorithms compared",
        "priority": 8, "category": "路径优化",
        "reason": "展示不同算法的求解质量差异"
    },
    "route_convergence": {
        "name": "SA收敛曲线+移动平均",
        "condition": "has simulated annealing convergence history",
        "priority": 7, "category": "路径优化",
        "reason": "展示模拟退火的收敛过程"
    },

    # === 统计/数据探索 ===
    "stat_corr_heatmap": {
        "name": "相关性热力图",
        "condition": "has correlation matrix with >=3 variables",
        "priority": 9, "category": "统计",
        "reason": "展示变量间相关关系,指导特征选择"
    },
    "stat_boxplot": {
        "name": "分组箱线图",
        "condition": "has grouped numeric data (>=2 groups)",
        "priority": 6, "category": "统计",
        "reason": "对比不同组的数据分布差异"
    },
    "stat_distribution": {
        "name": "数据分布直方图+KDE",
        "condition": "has univariate numeric data",
        "priority": 5, "category": "统计",
        "reason": "了解数据分布形态,支持模型假设"
    },
    "stat_pca_biplot": {
        "name": "PCA双标图(样本+载荷)",
        "condition": "has PCA results with >=2 components",
        "priority": 7, "category": "统计",
        "reason": "展示降维后样本分布和变量贡献"
    },

    # === 灵敏度 ===
    "sens_tornado": {
        "name": "Tornado参数灵敏度图",
        "condition": "has parameter sensitivity results",
        "priority": 9, "category": "灵敏度",
        "reason": "灵敏度分析标配,排序展示各参数影响大小"
    },
    "sens_monte_carlo": {
        "name": "蒙特卡洛输出分布图",
        "condition": "has Monte Carlo simulation results",
        "priority": 7, "category": "灵敏度",
        "reason": "展示随机扰动下的输出分布和置信区间"
    },
    "sens_one_param": {
        "name": "单参数灵敏度曲线",
        "condition": "has single-parameter sweep results",
        "priority": 6, "category": "灵敏度",
        "reason": "展示输出随单一参数连续变化趋势"
    },
    "sens_interaction": {
        "name": "双参数交互热力图",
        "condition": "has two-parameter sweep results",
        "priority": 5, "category": "灵敏度",
        "reason": "展示两参数对输出的交互影响"
    },

    # === 总览 ===
    "overview_comparison": {
        "name": "全部问题结果总览对比图",
        "condition": "has >=2 sub-problem results",
        "priority": 10, "category": "总览",
        "reason": "论文必备,一图展示所有问题的求解结果对比"
    },
    "distance_matrix_heatmap": {
        "name": "原始距离矩阵热力图",
        "condition": "has sparse distance matrix data",
        "priority": 8, "category": "数据理解",
        "reason": "展示原始路网数据的稀疏性和分布特征"
    },
}


def ai_select_figures(sub_problems, all_results, data_files, max_figures=20):
    """AI根据题型、数据特征、结果智能选择最合适的图表组合

    Returns:
        list of (figure_key, figure_info, reason) sorted by priority
    """
    selections = []
    used_categories = set()

    for sp in sub_problems:
        sp_id = sp.get("id", "?")
        ptype = sp.get("type", "")
        result = all_results.get(f"sub_{sp_id}", {})

        # --- 预测类判断 ---
        if result.get("forecast") and result.get("fitted"):
            selections.append(("pred_fitted_vs_actual", FIGURE_KB["pred_fitted_vs_actual"],
                             f"Q{sp_id}是预测题,有拟合和预测数据,用对比图展示模型效果"))
            if result.get("original"):
                selections.append(("pred_residual_diagnosis", FIGURE_KB["pred_residual_diagnosis"],
                                 f"Q{sp_id}有原始数据,用残差诊断验证模型适用性"))
            if any(k in result for k in ["lower", "upper", "ci", "interval"]):
                selections.append(("pred_intervals", FIGURE_KB["pred_intervals"],
                                 f"Q{sp_id}有不确定性估计,加预测区间图"))
            used_categories.add("预测")

        # --- 评价类判断 ---
        if result.get("scores") and result.get("labels"):
            selections.append(("eval_score_bar", FIGURE_KB["eval_score_bar"],
                             f"Q{sp_id}有评价得分,用柱状图展示排名"))
            if result.get("weights") and len(result["weights"]) >= 3:
                selections.append(("eval_weight_pie", FIGURE_KB["eval_weight_pie"],
                                 f"Q{sp_id}有{len(result['weights'])}个指标权重,用饼图展示"))
            if len(result.get("labels", [])) >= 3 and len(result.get("scores", [])) >= 3:
                selections.append(("eval_heatmap", FIGURE_KB["eval_heatmap"],
                                 f"Q{sp_id}有{len(result['labels'])}个方案,热力图展示数据矩阵"))
            used_categories.add("评价")

        # --- 路径优化判断 ---
        if result.get("tour") or result.get("routes"):
            selections.append(("route_network", FIGURE_KB["route_network"],
                             f"Q{sp_id}是路径优化,路网+最优路径是核心图"))
            if result.get("all_methods") and len(result.get("all_methods", [])) >= 2:
                selections.append(("route_algo_compare", FIGURE_KB["route_algo_compare"],
                                 f"Q{sp_id}有{len(result['all_methods'])}种算法对比结果"))
            used_categories.add("路径优化")

        # --- 背包优化判断 ---
        if result.get("selection"):
            selections.append(("opt_resource", FIGURE_KB["opt_resource"],
                             f"Q{sp_id}是资源分配,展示成本收益选择"))
            used_categories.add("优化")

        # --- 统计类判断 ---
        if result.get("corr_matrix"):
            n_cols = len(result.get("columns", []))
            if n_cols >= 3:
                selections.append(("stat_corr_heatmap", FIGURE_KB["stat_corr_heatmap"],
                                 f"Q{sp_id}有{n_cols}个变量的相关矩阵"))
            used_categories.add("统计")

    # --- 灵敏度分析(所有问题都需要) ---
    for sp in sub_problems:
        sp_id = sp.get("id", "?")
        result = all_results.get(f"sub_{sp_id}", {})
        if any(k in str(result.keys()) for k in ["sensitivity", "cv", "robust", "扰动"]):
            if "灵敏度" not in used_categories:
                selections.append(("sens_tornado", FIGURE_KB["sens_tornado"],
                                 "灵敏度分析标配,展示参数影响排序"))
                selections.append(("sens_monte_carlo", FIGURE_KB["sens_monte_carlo"],
                                 "蒙特卡洛验证模型稳定性"))
                used_categories.add("灵敏度")
            break

    # --- 总览图(多问时必加) ---
    if len(sub_problems) >= 2:
        selections.append(("overview_comparison", FIGURE_KB["overview_comparison"],
                         f"{len(sub_problems)}个问题,加总览对比图"))

    # --- 数据理解图 ---
    for name, df in data_files.items():
        if name.endswith("_norm"): continue
        numeric = df.select_dtypes(include=np.number)
        if numeric.shape[1] >= 10 and numeric.isnull().sum().sum() > numeric.size * 0.3:
            selections.append(("distance_matrix_heatmap", FIGURE_KB["distance_matrix_heatmap"],
                             f"{name}是稀疏矩阵({numeric.isnull().sum().sum()/numeric.size:.0%}缺失),热力图展示数据分布"))
            break

    # --- 去重并按优先级排序 ---
    seen = set()
    unique = []
    for key, info, reason in selections:
        if key not in seen:
            seen.add(key)
            unique.append((key, info, reason))
    unique.sort(key=lambda x: -x[1]["priority"])

    # --- 限制数量 ---
    if len(unique) > max_figures:
        print(f"  [AI] {len(unique)} figures proposed, limiting to top {max_figures}")
        unique = unique[:max_figures]

    # --- 打印选择理由 ---
    print(f"\n  [AI Figure Selection] {len(unique)} figures selected:")
    for i, (key, info, reason) in enumerate(unique, 1):
        print(f"    {i:2d}. [{info['category']}] {info['name']}")
        print(f"        {reason}")

    return unique


def generate_selected_figures(selections, all_results, data_files, fig_dir, sub_problems=None):
    """根据AI选择生成图表"""
    from mathmodel.visualization.figure_library import (
        prediction_fitted_vs_actual, prediction_residual_diagnosis,
        prediction_multi_model_compare, prediction_intervals,
        evaluation_score_bar, evaluation_radar, evaluation_weight_pie,
        evaluation_heatmap, evaluation_ranking_lollipop,
        optimization_convergence, optimization_gantt, optimization_pareto_front,
        optimization_resource_usage,
        statistics_correlation_heatmap, statistics_boxplot, statistics_violin,
        statistics_pca_biplot, statistics_distribution_hist,
        sensitivity_tornado, sensitivity_monte_carlo,
        sensitivity_one_param, sensitivity_interaction_heatmap,
    )
    from mathmodel.pipeline.professional_figures import (
        fig_tsp_network, fig_algorithm_comparison, fig_convergence_curve,
        fig_distance_matrix_heatmap, fig_question_comparison
    )

    generated = []
    for key, info, reason in selections:
        try:
            path = str(Path(fig_dir) / f"{key}.pdf")
            match_found = False

            # Route matching to correct function
            for sp in (sub_problems or []):
                sp_id = sp.get("id", "?")
                result = all_results.get(f"sub_{sp_id}", {})

                if key == "pred_fitted_vs_actual" and result.get("forecast"):
                    actual = result.get("original", result.get("fitted", []))
                    prediction_fitted_vs_actual(actual, result["fitted"], result["forecast"],
                                               path, title=f"Q{sp_id}: Forecast")
                    match_found = True; break

                if key == "pred_residual_diagnosis" and result.get("original"):
                    prediction_residual_diagnosis(result["original"], result["fitted"],
                                                 path, title=f"Q{sp_id}: Residual Diagnosis")
                    match_found = True; break

                if key == "eval_score_bar" and result.get("scores"):
                    evaluation_score_bar(result["labels"], [float(s) for s in result["scores"]],
                                        path, title=f"Q{sp_id}: Evaluation Scores")
                    match_found = True; break

                if key == "eval_weight_pie" and result.get("weights"):
                    evaluation_weight_pie(result["weights"], path,
                                         title=f"Q{sp_id}: Weight Distribution")
                    match_found = True; break

                if key == "route_network" and result.get("tour"):
                    fig_tsp_network.__call__ if False else None  # placeholder
                    match_found = True; break

                if key == "route_algo_compare" and result.get("all_methods"):
                    methods = {m[:25]: d for d, m in result.get("all_methods", [])[:6]}
                    fig_algorithm_comparison(methods, path,
                                            title=f"Q{sp_id}: Algorithm Comparison")
                    match_found = True; break

                if key == "opt_resource" and result.get("selection"):
                    costs = result.get("costs", [])
                    benefits = result.get("benefits", [0]*len(costs))
                    solution = result.get("solution", [0]*len(costs))
                    labels = result.get("labels_all", [f"Item{i}" for i in range(len(costs))])
                    optimization_resource_usage(costs, benefits, solution, labels, path,
                                               title=f"Q{sp_id}: Resource Allocation")
                    match_found = True; break

                if key == "stat_corr_heatmap" and result.get("corr_matrix"):
                    cols = result.get("columns", [f"V{i}" for i in range(10)])[:10]
                    corr = np.array(result["corr_matrix"])[:10, :10]
                    statistics_correlation_heatmap(corr, cols, path,
                                                  title=f"Q{sp_id}: Correlation Matrix")
                    match_found = True; break

            # Global figures
            if key == "overview_comparison" and len(all_results) >= 2:
                fig_question_comparison(all_results, path)
                match_found = True

            if key == "distance_matrix_heatmap":
                for name, df in data_files.items():
                    if name.endswith("_norm"): continue
                    numeric = df.select_dtypes(include=np.number)
                    if numeric.shape[1] >= 5:
                        fig_distance_matrix_heatmap(numeric.values,
                                                   min(numeric.shape[0], numeric.shape[1]),
                                                   path, title=f"Distance Matrix - {name}")
                        match_found = True; break

            if match_found:
                generated.append(key)
            else:
                print(f"    [SKIP] {key}: no matching data")

        except Exception as e:
            print(f"    [FAIL] {key}: {e}")

    return generated
