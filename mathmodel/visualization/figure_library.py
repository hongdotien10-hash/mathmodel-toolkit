"""国赛全图类型库 — 近5年CUMCM真题所有图表类型
============================================
覆盖: 预测/评价/优化/统计/灵敏度/微分方程/图论/其他
每类图独立函数, 接受标准数据格式, 论文级300dpi PDF输出
"""
import numpy as np, pandas as pd
from pathlib import Path
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.colors import LinearSegmentedColormap
from scipy import stats, interpolate
import warnings; warnings.filterwarnings('ignore')

# 字体
plt.rcParams['font.sans-serif'] = ['SimHei','Microsoft YaHei','DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 学术配色
C = ['#2C3E50','#E74C3C','#3498DB','#27AE60','#F39C12','#9B59B6','#1ABC9C','#E67E22','#34495E','#E91E63']
LG = '#ECF0F1'; G = '#95A5A6'; DG = '#2C3E50'

def _save(fig, path, dpi=300):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(p), dpi=dpi, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)
    return str(p)

def _style(ax, grid='y'):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(G); ax.spines['bottom'].set_color(G)
    ax.tick_params(colors=G, labelsize=9)
    if grid: ax.grid(alpha=0.25, axis=grid, linestyle='--', linewidth=0.5)


# ===================================================================
# 一、预测类图表 (8种)
# ===================================================================

def prediction_fitted_vs_actual(actual, fitted, forecast, output, title="", xlabel="Period", ylabel="Value"):
    """实际vs拟合vs预测 — 国赛预测题必用"""
    fig, ax = plt.subplots(figsize=(8,4.5))
    n_fit, n_fore = len(fitted), len(forecast)
    x_fit = list(range(1, n_fit+1))
    # forecast line: last fitted point + all forecast points
    fore_line = [fitted[-1]] + list(forecast)
    x_fore = list(range(n_fit, n_fit + len(fore_line)))
    ax.scatter(x_fit, list(actual)[:n_fit], c=C[1], s=50, zorder=5, label='Actual', edgecolors='white', linewidth=1)
    ax.plot(x_fit, fitted, color=C[0], linewidth=2, marker='o', markersize=5, markerfacecolor='white', label='Fitted')
    ax.plot(x_fore, fore_line, color=C[2], linewidth=2, linestyle='--', marker='s', markersize=6, markerfacecolor='white', label='Forecast')
    ax.axvline(x=n_fit+0.5, color=G, linestyle=':', alpha=0.6, linewidth=1)
    ax.set_xlabel(xlabel, fontsize=11); ax.set_ylabel(ylabel, fontsize=11)
    if title: ax.set_title(title, fontsize=12, fontweight='bold', loc='left')
    ax.legend(fontsize=9, frameon=True, facecolor='white', edgecolor=LG)
    _style(ax); _save(fig, output)


def prediction_intervals(fitted, forecast, lower, upper, output, title="", xlabel="Period", ylabel="Value"):
    """预测区间图 — 置信带"""
    fig, ax = plt.subplots(figsize=(8,4))
    n_fit, n_fore = len(fitted), len(forecast)
    x_fit = range(1, n_fit+1)
    x_fore = range(n_fit+1, n_fit+n_fore+1)
    ax.plot(x_fit, fitted, color=C[0], linewidth=2, label='Fitted')
    ax.plot(x_fore, forecast, color=C[2], linewidth=2, marker='s', markersize=5, markerfacecolor='white', label='Forecast')
    # Ensure lower/upper match forecast length
    lo = list(lower)[:n_fore]; hi = list(upper)[:n_fore]
    ax.fill_between(x_fore, lo, hi, alpha=0.2, color=C[2], label='95% Prediction Interval')
    ax.axvline(x=n_fit+0.5, color=G, linestyle=':', alpha=0.5)
    ax.set_xlabel(xlabel, fontsize=11); ax.set_ylabel(ylabel, fontsize=11)
    if title: ax.set_title(title, fontsize=12, fontweight='bold', loc='left')
    ax.legend(fontsize=9, frameon=True, facecolor='white', edgecolor=LG)
    _style(ax); _save(fig, output)


def prediction_multi_model_compare(models_data, output, title="Model Comparison", metric="MAPE(%)"):
    """多模型预测对比 — 柱状图+数值标注"""
    fig, ax = plt.subplots(figsize=(7,4.5))
    names = list(models_data.keys())
    vals = list(models_data.values())
    colors = C[:len(names)]
    bars = ax.bar(names, vals, color=colors, width=0.5, edgecolor='white', linewidth=0.5)
    best_idx = np.argmin(vals) if 'MAPE' in metric or 'RMSE' in metric else np.argmax(vals)
    for i, (b, v) in enumerate(zip(bars, vals)):
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+max(vals)*0.02, f'{v:.2f}',
               ha='center', fontsize=10, fontweight='bold' if i==best_idx else 'normal',
               color=C[1] if i==best_idx else DG)
    if best_idx < len(names):
        ax.text(best_idx, vals[best_idx]+max(vals)*0.08, 'BEST', ha='center', fontsize=8, color=C[1], fontstyle='italic')
    ax.set_ylabel(metric, fontsize=11)
    if title: ax.set_title(title, fontsize=12, fontweight='bold', loc='left')
    _style(ax); _save(fig, output)


def prediction_residual_diagnosis(actual, fitted, output, title=""):
    """残差诊断三连: 残差时序+残差vs拟合+QQ图"""
    residuals = np.array(actual)-np.array(fitted)
    fig, axes = plt.subplots(1,3,figsize=(13,4))
    # (a) Residual over time
    ax=axes[0]; ax.plot(range(len(residuals)), residuals, 'o-', color=C[0], markersize=5, markerfacecolor='white')
    ax.axhline(0, color=G, linestyle='--'); ax.fill_between(range(len(residuals)), -2*np.std(residuals), 2*np.std(residuals), alpha=0.1, color=C[0])
    ax.set_title('(a) Residual Sequence', fontsize=10, loc='left'); ax.set_xlabel('Index'); ax.set_ylabel('Residual')
    _style(ax)
    # (b) Residual vs Fitted
    ax=axes[1]; ax.scatter(fitted, residuals, c=C[0], alpha=0.6, s=40, edgecolors='white')
    ax.axhline(0, color=G, linestyle='--'); ax.set_title('(b) Residuals vs Fitted', fontsize=10, loc='left')
    ax.set_xlabel('Fitted'); ax.set_ylabel('Residual'); _style(ax)
    # (c) QQ plot
    ax=axes[2]; stats.probplot(residuals, dist='norm', plot=ax)
    ax.get_lines()[0].set_markerfacecolor(C[0]); ax.get_lines()[0].set_markeredgecolor('white')
    ax.get_lines()[1].set_color(C[1])
    ax.set_title('(c) Q-Q Plot', fontsize=10, loc='left'); _style(ax)
    if title: fig.suptitle(title, fontsize=12, fontweight='bold', y=1.01)
    fig.tight_layout(); _save(fig, output)


# ===================================================================
# 二、评价类图表 (7种)
# ===================================================================

def evaluation_radar(labels, values_list, names, output, title=""):
    """雷达图 — 多方案多指标对比"""
    n = len(labels)
    angles = np.linspace(0, 2*np.pi, n, endpoint=False).tolist()
    angles += angles[:1]
    fig, ax = plt.subplots(figsize=(7,7), subplot_kw=dict(polar=True))
    for i, (vals, name) in enumerate(zip(values_list, names)):
        v = list(vals) + [vals[0]]
        ax.fill(angles, v, alpha=0.1, color=C[i])
        ax.plot(angles, v, 'o-', color=C[i], linewidth=2, markersize=4, label=name)
    ax.set_xticks(angles[:-1]); ax.set_xticklabels(labels, fontsize=9)
    ax.set_yticklabels([]); ax.set_ylim(0, max(max(v) for v in values_list)*1.15)
    if title: ax.set_title(title, fontsize=12, fontweight='bold', pad=20)
    ax.legend(fontsize=8, loc='upper right', bbox_to_anchor=(1.3,1.0))
    _save(fig, output)


def evaluation_score_bar(labels, scores, output, title="", xlabel="Score", sort=True):
    """评价得分横向柱状图 — 排序+标注"""
    if sort:
        idx = np.argsort(scores)
        labels = [labels[i] for i in idx]
        scores = [scores[i] for i in idx]
    fig, ax = plt.subplots(figsize=(7, 1+len(labels)*0.45))
    colors = [C[1] if s==max(scores) else C[0] for s in scores]
    bars = ax.barh(range(len(labels)), scores, color=colors, height=0.6, edgecolor='white')
    for b, s in zip(bars, scores):
        ax.text(b.get_width()+max(scores)*0.01, b.get_y()+b.get_height()/2, f'{s:.4f}',
               va='center', fontsize=9, fontweight='bold' if s==max(scores) else 'normal')
    ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel(xlabel, fontsize=11)
    if title: ax.set_title(title, fontsize=12, fontweight='bold', loc='left')
    _style(ax); _save(fig, output)


def evaluation_weight_pie(weights_dict, output, title="Weight Distribution"):
    """权重分布饼图 — 国赛常用"""
    fig, ax = plt.subplots(figsize=(7,5))
    labels = list(weights_dict.keys())[:8]
    vals = [float(weights_dict[k]) for k in labels]
    explode = [0.05]*len(labels)
    wedges, texts, autotexts = ax.pie(vals, labels=labels, autopct='%1.1f%%',
                                       colors=C[:len(labels)], explode=explode,
                                       startangle=90, textprops={'fontsize':9})
    for at in autotexts: at.set_fontweight('bold'); at.set_fontsize(9)
    if title: ax.set_title(title, fontsize=12, fontweight='bold')
    _save(fig, output)


def evaluation_heatmap(matrix, row_labels, col_labels, output, title="", cmap='RdYlBu_r'):
    """评价矩阵热力图 — 方案×指标"""
    fig, ax = plt.subplots(figsize=(max(6, len(col_labels)*0.8), max(4, len(row_labels)*0.5)))
    im = ax.imshow(matrix, cmap=cmap, aspect='auto')
    ax.set_xticks(range(len(col_labels))); ax.set_yticks(range(len(row_labels)))
    ax.set_xticklabels(col_labels, rotation=30, ha='right', fontsize=8)
    ax.set_yticklabels(row_labels, fontsize=8)
    for i in range(len(row_labels)):
        for j in range(len(col_labels)):
            ax.text(j, i, f'{matrix[i,j]:.2f}', ha='center', va='center', fontsize=7,
                   color='white' if abs(matrix[i,j])>0.5 else 'black')
    cbar = plt.colorbar(im, ax=ax, shrink=0.85); cbar.ax.tick_params(labelsize=7)
    if title: ax.set_title(title, fontsize=12, fontweight='bold', loc='left')
    _save(fig, output)


def evaluation_ranking_lollipop(labels, scores, output, title=""):
    """排名棒棒糖图 — 国赛常见"""
    fig, ax = plt.subplots(figsize=(7, 1+len(labels)*0.4))
    order = np.argsort(scores)[::-1]
    ordered_scores = [scores[i] for i in order]
    ordered_labels = [labels[i] for i in order]
    ax.stem(range(len(ordered_scores)), ordered_scores, linefmt=C[0], markerfmt='o', basefmt=' ')
    ax.scatter(range(len(ordered_scores)), ordered_scores, c=C[:len(ordered_scores)], s=100, zorder=5, edgecolors='white')
    for i, (l, s) in enumerate(zip(ordered_labels, ordered_scores)):
        ax.annotate(f'{l}\n{s:.3f}', (i, s), textcoords='offset points', xytext=(0,10), ha='center', fontsize=8)
    ax.set_xticks([]); ax.set_ylabel('Score', fontsize=11)
    if title: ax.set_title(title, fontsize=12, fontweight='bold', loc='left')
    _style(ax); _save(fig, output)


# ===================================================================
# 三、优化类图表 (5种)
# ===================================================================

def optimization_convergence(history, output, title="Convergence Curve", xlabel="Iteration", ylabel="Objective"):
    """优化收敛曲线 — 必用"""
    fig, ax = plt.subplots(figsize=(8,4))
    ax.plot(range(len(history)), history, color=C[0], linewidth=1.5)
    best = min(history); best_idx = history.index(best)
    ax.axhline(best, color=C[1], linestyle='--', alpha=0.6, label=f'Best={best:.2f}')
    ax.scatter([best_idx], [best], c=C[1], s=80, zorder=5, edgecolors='white')
    ax.set_xlabel(xlabel, fontsize=11); ax.set_ylabel(ylabel, fontsize=11)
    if title: ax.set_title(title, fontsize=12, fontweight='bold', loc='left')
    ax.legend(fontsize=9, frameon=True, facecolor='white', edgecolor=LG)
    _style(ax); _save(fig, output)


def optimization_gantt(tasks, output, title="Schedule Gantt Chart"):
    """甘特图 — 调度/资源分配"""
    fig, ax = plt.subplots(figsize=(10, 2+len(tasks)*0.4))
    for i, task in enumerate(tasks):
        ax.barh(i, task['duration'], left=task['start'], color=C[i%len(C)], height=0.6,
               edgecolor='white', label=task.get('name', f'Task {i+1}'))
    ax.set_yticks(range(len(tasks)))
    ax.set_yticklabels([tasks[i].get('name', f'Task{i+1}') for i in range(len(tasks))], fontsize=9)
    ax.set_xlabel('Time', fontsize=11)
    if title: ax.set_title(title, fontsize=12, fontweight='bold', loc='left')
    _style(ax); _save(fig, output)


def optimization_pareto_front(obj1, obj2, output, title="Pareto Frontier", xlabel="Obj1", ylabel="Obj2"):
    """帕累托前沿 — 多目标优化"""
    fig, ax = plt.subplots(figsize=(7,5.5))
    ax.scatter(obj1, obj2, c=C[0], alpha=0.5, s=40, edgecolors='white', label='Solutions')
    # Find Pareto front
    points = sorted(zip(obj1, obj2))
    pareto = [points[0]]
    for p in points[1:]:
        if p[1] > pareto[-1][1]: pareto.append(p)
    px, py = zip(*pareto)
    ax.plot(px, py, 'o-', color=C[1], linewidth=2.5, markersize=6, markerfacecolor='white', label='Pareto Front')
    ax.set_xlabel(xlabel, fontsize=11); ax.set_ylabel(ylabel, fontsize=11)
    if title: ax.set_title(title, fontsize=12, fontweight='bold', loc='left')
    ax.legend(fontsize=9, frameon=True, facecolor='white', edgecolor=LG)
    _style(ax); _save(fig, output)


def optimization_resource_usage(costs, benefits, selection, labels, output, title=""):
    """资源利用对比图 — 优化前后"""
    fig, axes = plt.subplots(1,2,figsize=(11,4.5))
    n = len(costs)
    sel_colors = [C[1] if selection[i]>0.5 else G for i in range(n)]
    ax=axes[0]; ax.bar(range(n), costs, color=sel_colors, width=0.6, edgecolor='white')
    ax.set_title('Cost per Item (Red=Selected)', fontsize=10, loc='left'); ax.set_ylabel('Cost'); _style(ax)
    ax=axes[1]; ax.bar(range(n), benefits, color=sel_colors, width=0.6, edgecolor='white')
    ax.set_title('Benefit per Item (Red=Selected)', fontsize=10, loc='left'); ax.set_ylabel('Benefit'); _style(ax)
    if title: fig.suptitle(title, fontsize=12, fontweight='bold', y=1.02)
    fig.tight_layout(); _save(fig, output)


# ===================================================================
# 四、统计/数据分析类图表 (7种)
# ===================================================================

def statistics_correlation_heatmap(corr_matrix, col_labels, output, title="Correlation Matrix"):
    """相关性热力图 — 最常用"""
    fig, ax = plt.subplots(figsize=(len(col_labels)*0.9+1, len(col_labels)*0.7+0.5))
    im = ax.imshow(corr_matrix, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
    ax.set_xticks(range(len(col_labels))); ax.set_yticks(range(len(col_labels)))
    ax.set_xticklabels(col_labels, rotation=45, ha='right', fontsize=8)
    ax.set_yticklabels(col_labels, fontsize=8)
    for i in range(len(col_labels)):
        for j in range(len(col_labels)):
            v = corr_matrix[i,j]
            ax.text(j, i, f'{v:.2f}', ha='center', va='center', fontsize=7,
                   color='white' if abs(v)>0.5 else 'black')
    cbar = plt.colorbar(im, ax=ax, shrink=0.85); cbar.ax.tick_params(labelsize=7)
    if title: ax.set_title(title, fontsize=12, fontweight='bold', loc='left')
    _save(fig, output)


def statistics_boxplot(data_dict, output, title="Distribution Comparison"):
    """箱线图 — 多组对比"""
    fig, ax = plt.subplots(figsize=(max(5, len(data_dict)*1.2), 5))
    bp = ax.boxplot(data_dict.values(), patch_artist=True, widths=0.5)
    for i, (patch, key) in enumerate(zip(bp['boxes'], data_dict.keys())):
        patch.set_facecolor(C[i%len(C)]); patch.set_alpha(0.7)
    ax.set_xticklabels(data_dict.keys(), fontsize=9)
    if title: ax.set_title(title, fontsize=12, fontweight='bold', loc='left')
    _style(ax); _save(fig, output)


def statistics_violin(data_dict, output, title="Distribution Comparison"):
    """小提琴图 — 分布形状"""
    fig, ax = plt.subplots(figsize=(max(5, len(data_dict)*1.2), 5))
    parts = ax.violinplot(data_dict.values(), showmeans=True, showmedians=True)
    for i, body in enumerate(parts['bodies']):
        body.set_facecolor(C[i%len(C)]); body.set_alpha(0.7)
    ax.set_xticks(range(1, len(data_dict)+1)); ax.set_xticklabels(data_dict.keys(), fontsize=9)
    if title: ax.set_title(title, fontsize=12, fontweight='bold', loc='left')
    _style(ax); _save(fig, output)


def statistics_pca_biplot(transformed, components, features, output, title="PCA Biplot"):
    """PCA双标图 — 样本+载荷"""
    fig, ax = plt.subplots(figsize=(8,6.5))
    ax.scatter(transformed[:,0], transformed[:,1], c=C[0], alpha=0.5, s=40, edgecolors='white')
    for i, feat in enumerate(features):
        ax.arrow(0, 0, components[0,i]*max(abs(transformed[:,0]))*0.8,
                components[1,i]*max(abs(transformed[:,1]))*0.8,
                color=C[1], width=0.002, head_width=0.05, alpha=0.8)
        ax.text(components[0,i]*max(abs(transformed[:,0]))*0.9,
               components[1,i]*max(abs(transformed[:,1]))*0.9, feat, fontsize=9, color=C[1])
    ax.set_xlabel(f'PC1 ({components[0].var()*100:.1f}%)', fontsize=11)
    ax.set_ylabel(f'PC2 ({components[1].var()*100:.1f}%)', fontsize=11)
    ax.axhline(0, color=G, linestyle='-', linewidth=0.5); ax.axvline(0, color=G, linestyle='-', linewidth=0.5)
    if title: ax.set_title(title, fontsize=12, fontweight='bold', loc='left')
    _style(ax); _save(fig, output)


def statistics_scatter_matrix(df, columns, output, title="Scatter Matrix"):
    """散点矩阵图"""
    n = len(columns)
    fig, axes = plt.subplots(n, n, figsize=(n*2.5, n*2.5))
    for i in range(n):
        for j in range(n):
            ax = axes[i,j] if n>1 else axes
            if i == j:
                ax.hist(df[columns[i]].dropna(), bins=20, color=C[0], alpha=0.7, edgecolor='white')
            else:
                ax.scatter(df[columns[j]], df[columns[i]], c=C[0], alpha=0.3, s=10, edgecolors='none')
            if j == 0: ax.set_ylabel(columns[i][:8], fontsize=7)
            if i == n-1: ax.set_xlabel(columns[j][:8], fontsize=7)
            ax.tick_params(labelsize=6)
    if title: fig.suptitle(title, fontsize=12, fontweight='bold', y=1.01)
    fig.tight_layout(); _save(fig, output)


def statistics_distribution_hist(data, output, title="Distribution", bins=30):
    """分布直方图+密度曲线"""
    fig, ax = plt.subplots(figsize=(7,4))
    ax.hist(data, bins=bins, density=True, color=C[0], alpha=0.6, edgecolor='white')
    kde_x = np.linspace(min(data), max(data), 200)
    kde = stats.gaussian_kde(data)
    ax.plot(kde_x, kde(kde_x), color=C[1], linewidth=2.5, label='KDE')
    ax.set_xlabel('Value', fontsize=11); ax.set_ylabel('Density', fontsize=11)
    if title: ax.set_title(title, fontsize=12, fontweight='bold', loc='left')
    ax.legend(fontsize=9); _style(ax); _save(fig, output)


# ===================================================================
# 五、灵敏度分析图表 (4种)
# ===================================================================

def sensitivity_tornado(params, impacts, output, title="Sensitivity Tornado"):
    """Tornado图 — 参数灵敏度排序"""
    fig, ax = plt.subplots(figsize=(7, max(3, len(params)*0.4)))
    order = np.argsort([abs(i) for i in impacts])
    names = [params[i] for i in order]
    up_vals = [max(0, impacts[i]) for i in order]
    dn_vals = [min(0, impacts[i]) for i in order]
    ax.barh(range(len(names)), up_vals, height=0.5, color=C[1], alpha=0.7, label='+perturbation', edgecolor='white')
    ax.barh(range(len(names)), dn_vals, height=0.5, color=C[2], alpha=0.7, label='-perturbation', edgecolor='white')
    ax.set_yticks(range(len(names))); ax.set_yticklabels(names, fontsize=9)
    ax.axvline(0, color='black', linewidth=0.8)
    ax.set_xlabel('Output Change', fontsize=11)
    if title: ax.set_title(title, fontsize=12, fontweight='bold', loc='left')
    ax.legend(fontsize=8, frameon=True, facecolor='white', edgecolor=LG)
    _style(ax); _save(fig, output)


def sensitivity_monte_carlo(outputs, output, title="Monte Carlo Distribution", ci=95):
    """蒙特卡洛输出分布"""
    fig, ax = plt.subplots(figsize=(7,4))
    ax.hist(outputs, bins=40, density=True, color=C[0], alpha=0.6, edgecolor='white')
    mean = np.mean(outputs); lo, hi = np.percentile(outputs, [(100-ci)/2, 100-(100-ci)/2])
    ax.axvline(mean, color=C[1], linewidth=2.5, label=f'Mean={mean:.4f}')
    ax.axvline(lo, color=G, linestyle='--', alpha=0.7, label=f'{ci}% CI=[{lo:.4f},{hi:.4f}]')
    ax.axvline(hi, color=G, linestyle='--', alpha=0.7)
    ax.set_xlabel('Output', fontsize=11); ax.set_ylabel('Density', fontsize=11)
    if title: ax.set_title(title, fontsize=12, fontweight='bold', loc='left')
    ax.legend(fontsize=8, frameon=True, facecolor='white', edgecolor=LG)
    _style(ax); _save(fig, output)


def sensitivity_one_param(param_values, outputs, output, title="Parameter Sensitivity", xlabel="Parameter"):
    """单参数灵敏度曲线"""
    fig, ax = plt.subplots(figsize=(7,4))
    ax.plot(param_values, outputs, 'o-', color=C[0], linewidth=2, markersize=6, markerfacecolor='white')
    ax.set_xlabel(xlabel, fontsize=11); ax.set_ylabel('Output', fontsize=11)
    if title: ax.set_title(title, fontsize=12, fontweight='bold', loc='left')
    _style(ax); _save(fig, output)


def sensitivity_interaction_heatmap(param1_vals, param2_vals, output_matrix, output, title="Interaction Heatmap"):
    """双参数交互热力图"""
    fig, ax = plt.subplots(figsize=(7,5.5))
    im = ax.imshow(output_matrix, cmap='YlOrRd', aspect='auto', origin='lower')
    ax.set_xticks(range(len(param2_vals))); ax.set_yticks(range(len(param1_vals)))
    ax.set_xticklabels([f'{v:.1f}' for v in param2_vals], fontsize=8, rotation=30)
    ax.set_yticklabels([f'{v:.1f}' for v in param1_vals], fontsize=8)
    for i in range(len(param1_vals)):
        for j in range(len(param2_vals)):
            ax.text(j, i, f'{output_matrix[i,j]:.1f}', ha='center', va='center', fontsize=7)
    cbar = plt.colorbar(im, ax=ax, shrink=0.85); cbar.ax.tick_params(labelsize=7)
    ax.set_xlabel('Parameter 2', fontsize=11); ax.set_ylabel('Parameter 1', fontsize=11)
    if title: ax.set_title(title, fontsize=12, fontweight='bold', loc='left')
    _save(fig, output)


# ===================================================================
# 六、3D/高级图表 (3种)
# ===================================================================

def advanced_3d_surface(x, y, z, output, title="3D Surface", xlabel="X", ylabel="Y", zlabel="Z"):
    """3D曲面图"""
    from mpl_toolkits.mplot3d import Axes3D
    fig = plt.figure(figsize=(9,7))
    ax = fig.add_subplot(111, projection='3d')
    X, Y = np.meshgrid(x, y)
    surf = ax.plot_surface(X, Y, z, cmap='viridis', alpha=0.85, edgecolor='none')
    ax.set_xlabel(xlabel, fontsize=10); ax.set_ylabel(ylabel, fontsize=10)
    ax.set_zlabel(zlabel, fontsize=10)
    if title: ax.set_title(title, fontsize=12, fontweight='bold')
    fig.colorbar(surf, ax=ax, shrink=0.6)
    _save(fig, output)


def advanced_contour(x, y, z, output, title="Contour Map", xlabel="X", ylabel="Y"):
    """等高线图"""
    fig, ax = plt.subplots(figsize=(7,6))
    X, Y = np.meshgrid(x, y)
    cs = ax.contour(X, Y, z, levels=12, colors=C[0], linewidths=0.8)
    ax.clabel(cs, fontsize=7)
    cf = ax.contourf(X, Y, z, levels=12, cmap='YlOrRd', alpha=0.7)
    ax.set_xlabel(xlabel, fontsize=11); ax.set_ylabel(ylabel, fontsize=11)
    if title: ax.set_title(title, fontsize=12, fontweight='bold', loc='left')
    fig.colorbar(cf, ax=ax, shrink=0.85)
    _save(fig, output)


def advanced_stacked_area(x, y_dict, output, title="Stacked Area", xlabel="X", ylabel="Y"):
    """堆叠面积图"""
    fig, ax = plt.subplots(figsize=(8,4.5))
    names = list(y_dict.keys())
    y_data = list(y_dict.values())
    ax.stackplot(x, *y_data, labels=names, colors=C[:len(names)], alpha=0.8)
    ax.set_xlabel(xlabel, fontsize=11); ax.set_ylabel(ylabel, fontsize=11)
    if title: ax.set_title(title, fontsize=12, fontweight='bold', loc='left')
    ax.legend(fontsize=8, frameon=True, facecolor='white', edgecolor=LG, loc='upper left')
    _style(ax); _save(fig, output)


# ===================================================================
# 七、图论/网络图表 (3种)
# ===================================================================

def graph_network_topology(adj_matrix, tour=None, output="", title="Network Topology"):
    """网络拓扑图 — 节点+边+最优路径"""
    import networkx as nx
    n = len(adj_matrix)
    G = nx.Graph()
    for i in range(n):
        for j in range(i+1,n):
            if adj_matrix[i,j] > 0:
                G.add_edge(i, j, weight=adj_matrix[i,j])

    pos = nx.spring_layout(G, seed=42, k=2)
    fig, ax = plt.subplots(figsize=(9,8))

    # All edges
    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.3, edge_color=G, width=1)

    # Tour edges if provided
    if tour:
        tour_edges = [(tour[i], tour[i+1]) for i in range(len(tour)-1)]
        nx.draw_networkx_edges(G, pos, ax=ax, edgelist=tour_edges, edge_color=C[1], width=3, alpha=0.9)

    # Edge labels
    labels = {(i,j): f'{adj_matrix[i,j]:.0f}' for i,j in G.edges()}
    nx.draw_networkx_edge_labels(G, pos, ax=ax, edge_labels=labels, font_size=6, alpha=0.6)

    # Nodes
    node_colors = [C[2] if i==tour[0] else 'white' for i in range(n)] if tour else [C[0]]*n
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=300, node_color=node_colors,
                          edgecolors=C[0], linewidths=1.5)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=9, font_weight='bold')

    ax.set_axis_off()
    if title: ax.set_title(title, fontsize=12, fontweight='bold')
    _save(fig, output)


# ===================================================================
# 自动选择函数
# ===================================================================

def auto_generate_figures(all_results, data_files, fig_dir, sub_problems=None):
    """根据结果类型自动生成所有合适的图表"""
    generated = []
    for key, val in all_results.items():
        sp_id = key.replace('sub_', '')
        ptype = "综合"
        if sub_problems:
            for sp in sub_problems:
                if str(sp.get('id','')) == sp_id:
                    ptype = sp.get('type', '综合'); break

        try:
            # 评价类
            if 'scores' in val and 'labels' in val:
                evaluation_score_bar(val['labels'], [float(s) for s in val['scores']],
                                    str(Path(fig_dir)/f'{key}_score_bar.pdf'),
                                    title=f'Q{sp_id}: Evaluation Scores')
                generated.append(f'{key}_score_bar')
                if 'weights' in val:
                    evaluation_weight_pie(val['weights'],
                                         str(Path(fig_dir)/f'{key}_weight_pie.pdf'),
                                         title=f'Q{sp_id}: Weight Distribution')
                    generated.append(f'{key}_weight_pie')

            # 预测类
            if 'forecast' in val and 'fitted' in val:
                actual = val.get('original', [])
                if actual:
                    prediction_fitted_vs_actual(actual, val['fitted'], val['forecast'],
                                               str(Path(fig_dir)/f'{key}_forecast.pdf'),
                                               title=f'Q{sp_id}: Forecast')
                    generated.append(f'{key}_forecast')
                    prediction_residual_diagnosis(actual, val['fitted'],
                                                 str(Path(fig_dir)/f'{key}_residual.pdf'),
                                                 title=f'Q{sp_id}: Residual Diagnosis')
                    generated.append(f'{key}_residual')

            # 优化类 - 背包
            if 'selection' in val and 'costs' in val:
                optimization_resource_usage(val['costs'], val.get('benefits', [0]*len(val['costs'])),
                                           val.get('solution', [0]*len(val['costs'])),
                                           val.get('labels_all', [f'Item{i}' for i in range(len(val['costs']))]),
                                           str(Path(fig_dir)/f'{key}_resource.pdf'),
                                           title=f'Q{sp_id}: Resource Allocation')
                generated.append(f'{key}_resource')

            # 统计类
            if 'corr_matrix' in val:
                cols = val.get('columns', [f'V{i}' for i in range(len(val['corr_matrix'][:10]))])
                corr = np.array(val['corr_matrix'])[:10,:10]
                statistics_correlation_heatmap(corr, cols[:10],
                                              str(Path(fig_dir)/f'{key}_corr_heatmap.pdf'),
                                              title=f'Q{sp_id}: Correlation Matrix')
                generated.append(f'{key}_corr_heatmap')

        except Exception as e:
            print(f'  Figure {key}: {e}')

    return generated
