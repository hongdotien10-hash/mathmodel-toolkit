"""专业论文图表 — 真实数据驱动 + 中文字体 + 学术风格"""
import numpy as np, pandas as pd
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.patches import FancyBboxPatch

# 强制中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 学术配色 (Nature/Science 风格)
COLORS = ['#2C3E50', '#E74C3C', '#3498DB', '#27AE60', '#F39C12', '#9B59B6', '#1ABC9C', '#E67E22']
GRAY = '#7F8C8D'
LIGHT_GRAY = '#ECF0F1'


def fig_tsp_network(sparse_matrix, n, tour, total_dist, output_path, title=""):
    """TSP路网图 — 节点位置基于真实距离矩阵MDS投影 + 最优路径高亮"""
    from sklearn.manifold import MDS

    # Floyd complete the graph for MDS
    INF = 1e9
    D = np.full((n, n), INF)
    vals = sparse_matrix[:n, :n]
    for i in range(n):
        for j in range(n):
            v = vals[i,j] if i < vals.shape[0] and j < vals.shape[1] else np.nan
            if not np.isnan(v) and v > 0: D[i,j] = v
            elif i == j: D[i,j] = 0
    for i in range(n):
        for j in range(n):
            if D[i,j] < INF and D[j,i] >= INF: D[j,i] = D[i,j]
    for k in range(n):
        for i in range(n):
            if D[i,k] >= INF: continue
            for j in range(n):
                nd = D[i,k] + D[k,j]
                if nd < D[i,j]: D[i,j] = nd

    # MDS: project distance matrix to 2D coordinates
    mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42, normalized_stress='auto')
    coords = mds.fit_transform(D)

    fig, ax = plt.subplots(figsize=(10, 8))

    # Draw all edges (background road network)
    edge_count = 0
    for i in range(n):
        for j in range(i+1, n):
            v = sparse_matrix[i,j] if i < sparse_matrix.shape[0] and j < sparse_matrix.shape[1] else np.nan
            if not np.isnan(v) and v > 0:
                ax.plot([coords[i,0], coords[j,0]], [coords[i,1], coords[j,1]],
                       color=LIGHT_GRAY, linewidth=0.8, alpha=0.5, zorder=1)
                edge_count += 1

    # Draw TSP optimal path
    for idx in range(len(tour) - 1):
        i, j = tour[idx], tour[idx+1]
        if i < n and j < n:
            ax.plot([coords[i,0], coords[j,0]], [coords[i,1], coords[j,1]],
                   color=COLORS[1], linewidth=2.5, alpha=0.9, zorder=3,
                   marker='o', markersize=0)

    # Draw nodes
    for i in range(n):
        is_start = (i == tour[0])
        ax.scatter(coords[i,0], coords[i,1],
                  s=200 if is_start else 120,
                  c=COLORS[2] if is_start else 'white',
                  edgecolors=COLORS[0], linewidth=2 if is_start else 1.5,
                  zorder=5)
        offset = 3 if i % 2 == 0 else -3
        ax.annotate(str(i+1), (coords[i,0], coords[i,1]),
                   textcoords="offset points", xytext=(offset, offset),
                   fontsize=9, fontweight='bold', ha='center', va='center',
                   color=COLORS[0])

    ax.set_title(f"{title}\n最优配送回路: {total_dist}km, {n}个地点, {edge_count}条道路",
                fontsize=13, fontweight='bold', pad=20)
    ax.set_axis_off()
    ax.set_aspect('equal')

    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0],[0], color=LIGHT_GRAY, linewidth=1, label=f'路网 ({edge_count}条边)'),
        Line2D([0],[0], color=COLORS[1], linewidth=2.5, label=f'最优路径 ({total_dist}km)'),
        Line2D([0],[0], marker='o', color='w', markerfacecolor=COLORS[2],
               markeredgecolor=COLORS[0], markersize=10, label=f'出发点 地点{tour[0]+1}'),
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=9, frameon=True,
             facecolor='white', edgecolor=LIGHT_GRAY)

    fig.tight_layout()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)
    return output_path


def fig_algorithm_comparison(methods_dict, output_path, title="Algorithm Comparison"):
    """多算法对比柱状图 — 论文级品质"""
    names = list(methods_dict.keys())
    values = list(methods_dict.values())

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.barh(range(len(names)), values, height=0.55, color=COLORS[:len(names)],
                   edgecolor='white', linewidth=0.5)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=10)
    ax.set_xlabel('Total Distance (km)', fontsize=11)
    ax.invert_yaxis()

    # Value labels
    best_val = min(values)
    for i, (bar, val) in enumerate(zip(bars, values)):
        color = COLORS[1] if val == best_val else GRAY
        weight = 'bold' if val == best_val else 'normal'
        ax.text(val + max(values)*0.01, bar.get_y() + bar.get_height()/2,
               f'{val:.1f}', va='center', fontsize=10, color=color, fontweight=weight)
        if val == best_val:
            ax.text(val + max(values)*0.12, bar.get_y() + bar.get_height()/2,
                   '← BEST', va='center', fontsize=8, color=COLORS[1], fontstyle='italic')

    ax.set_title(title, fontsize=12, fontweight='bold', loc='left')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(LIGHT_GRAY)
    ax.spines['bottom'].set_color(LIGHT_GRAY)
    ax.tick_params(colors=GRAY, labelsize=9)
    ax.grid(alpha=0.3, axis='x', linestyle='--', linewidth=0.5)

    fig.tight_layout()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)
    return output_path


def fig_convergence_curve(sa_history, output_path, title="SA Convergence"):
    """SA收敛曲线 — 多轮叠加 + 移动平均"""
    fig, ax = plt.subplots(figsize=(8, 4))

    for ri, h in enumerate(sa_history):
        conv = h.get("convergence", [])
        if len(conv) > 1:
            its = [c[0] for c in conv]
            dists = [c[2] for c in conv]
            color = COLORS[ri % len(COLORS)]
            ax.plot(its, dists, color=color, linewidth=1.2, alpha=0.7,
                   label=f"Run {h['run']+1} (final: {h['dist']})")

            # Moving average for last run
            if ri == len(sa_history) - 1 and len(dists) > 20:
                window = max(1, len(dists)//20)
                ma = np.convolve(dists, np.ones(window)/window, mode='valid')
                ax.plot(its[window-1:], ma, color=color, linewidth=2.5, linestyle='--',
                       alpha=0.9, label=f'Moving Avg (w={window})')

    ax.set_xlabel('Iteration', fontsize=11)
    ax.set_ylabel('Best Distance (km)', fontsize=11)
    ax.set_title(title, fontsize=12, fontweight='bold', loc='left')
    ax.legend(fontsize=8, frameon=True, facecolor='white', edgecolor=LIGHT_GRAY,
             loc='upper right')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(LIGHT_GRAY)
    ax.spines['bottom'].set_color(LIGHT_GRAY)
    ax.tick_params(colors=GRAY, labelsize=9)
    ax.grid(alpha=0.3, linestyle='--', linewidth=0.5)
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f'))

    fig.tight_layout()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)
    return output_path


def fig_distance_matrix_heatmap(sparse_matrix, n, output_path, title="Distance Matrix"):
    """距离矩阵热力图 — 展示路网稀疏性"""
    vals = np.zeros((n, n))
    for i in range(min(n, sparse_matrix.shape[0])):
        for j in range(min(n, sparse_matrix.shape[1])):
            v = sparse_matrix[i, j]
            vals[i, j] = v if not np.isnan(v) and v > 0 else 0

    mask = (vals == 0)

    fig, ax = plt.subplots(figsize=(7, 6))
    cmap = plt.cm.YlOrRd
    cmap.set_bad('white')
    im = ax.imshow(np.ma.masked_where(mask, vals) if mask.any() else vals,
                   cmap=cmap, aspect='auto', vmin=0)

    # Annotate with values
    for i in range(n):
        for j in range(n):
            if vals[i, j] > 0:
                ax.text(j, i, f'{vals[i,j]:.0f}', ha='center', va='center',
                       fontsize=6, color='white' if vals[i,j] > 30 else 'black')

    ax.set_xticks(range(n)); ax.set_yticks(range(n))
    ax.set_xticklabels([str(i+1) for i in range(n)], fontsize=7)
    ax.set_yticklabels([str(i+1) for i in range(n)], fontsize=7)
    ax.set_xlabel('To Location', fontsize=10)
    ax.set_ylabel('From Location', fontsize=10)

    n_edges = int(np.sum(vals > 0))
    ax.set_title(f'{title}\n{n} locations, {n_edges} edges ({n_edges/(n*n)*100:.1f}% density)',
                fontsize=11, fontweight='bold', loc='left')

    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Distance (km)', fontsize=9)

    fig.tight_layout()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)
    return output_path


def fig_question_comparison(all_results, output_path):
    """四问总览对比图"""
    fig, axes = plt.subplots(1, 4, figsize=(16, 4.5))

    q_data = []
    for key in sorted(all_results.keys()):
        val = all_results[key]
        q_id = key.replace('sub_', '')
        dist = val.get('total_distance', 0)
        n_veh = val.get('n_vehicles', 1)
        method = val.get('method', '?')[:30]
        q_data.append((q_id, dist, n_veh, method))

    # Bar comparison
    ids = [f'Q{d[0]}' for d in q_data]
    dists = [d[1] for d in q_data]

    bars = axes[0].bar(ids, dists, color=COLORS[:len(ids)], width=0.5, edgecolor='white')
    for bar, d in zip(bars, dists):
        axes[0].text(bar.get_x()+bar.get_width()/2, bar.get_height()+max(dists)*0.02,
                    f'{d:.0f}', ha='center', fontsize=10, fontweight='bold')
    axes[0].set_ylabel('Distance (km)', fontsize=9)
    axes[0].set_title('Distance Comparison', fontsize=10, fontweight='bold', loc='left')

    # Method labels
    axes[1].axis('off')
    text = 'Methods Used:\n\n' + '\n\n'.join(f'Q{d[0]}: {d[3]}' for d in q_data)
    axes[1].text(0.1, 0.5, text, fontsize=8, va='center', transform=axes[1].transAxes,
                fontfamily='monospace')

    # Time comparison (estimated)
    speeds = {'Q1': 50, 'Q2': 50, 'Q3': 50, 'Q4': 50}
    times = [dists[i] / speeds.get(ids[i], 50) for i in range(len(dists))]
    bars2 = axes[2].bar(ids, times, color=COLORS[2:2+len(ids)], width=0.5, edgecolor='white')
    for bar, t in zip(bars2, times):
        axes[2].text(bar.get_x()+bar.get_width()/2, bar.get_height()+max(times)*0.02,
                    f'{t:.1f}h', ha='center', fontsize=9, fontweight='bold')
    axes[2].set_ylabel('Time (h)', fontsize=9)
    axes[2].set_title('Delivery Time @50km/h', fontsize=10, fontweight='bold', loc='left')

    # Summary table
    axes[3].axis('off')
    rows = [['Q#', '距离(km)', '时间(h)', '车辆数']]
    for d in q_data:
        rows.append([f'Q{d[0]}', f'{d[1]:.0f}', f'{d[1]/50:.1f}', str(d[2])])

    table = axes[3].table(cellText=rows, cellLoc='center', loc='center',
                          colWidths=[0.15, 0.25, 0.25, 0.2])
    table.auto_set_font_size(False); table.set_fontsize(9)
    for i in range(len(rows)):
        for j in range(4):
            cell = table[i, j]
            cell.set_edgecolor(LIGHT_GRAY)
            if i == 0:
                cell.set_facecolor(COLORS[0])
                cell.get_text().set_color('white')

    for ax in axes:
        if ax.patches:
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color(LIGHT_GRAY)
            ax.spines['bottom'].set_color(LIGHT_GRAY)
            ax.tick_params(colors=GRAY, labelsize=8)
            ax.grid(alpha=0.3, axis='y', linestyle='--', linewidth=0.5)

    fig.suptitle('2022电工杯B题 应急物资配送 — 各问题求解结果对比', fontsize=14,
                fontweight='bold', y=1.02)
    fig.tight_layout()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)
    return output_path
