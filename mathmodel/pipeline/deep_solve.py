"""深度求解引擎 — 每问10分钟+多算法全量对比"""
import numpy as np, pandas as pd, time, json
from pathlib import Path
from mathmodel.models.graph import GraphSolver


def deep_solve_tsp(sparse_matrix, n, fig_dir, question_id, time_budget=600):
    """TSP深度求解: NN(50起点) + 2-opt(完全收敛) + SA(5轮×10000次) + 收敛曲线

    Args:
        time_budget: 时间预算(秒), 默认600=10分钟
    """
    gs = GraphSolver()
    start_time = time.time()
    results = {"methods": {}, "convergence": {}, "best": None}

    # --- Floyd-Warshall ---
    INF = 1e9
    D = np.full((n, n), INF)
    vals = sparse_matrix[:n, :n]
    for i in range(n):
        for j in range(n):
            v = vals[i,j] if i < vals.shape[0] and j < vals.shape[1] else np.nan
            if not np.isnan(v) and v > 0:
                D[i,j] = v
            elif i == j: D[i,j] = 0
    for i in range(n):
        for j in range(n):
            if D[i,j] < INF and D[j,i] >= INF:
                D[j,i] = D[i,j]
    for k in range(n):
        for i in range(n):
            if D[i,k] >= INF: continue
            for j in range(n):
                if D[i,k] + D[k,j] < D[i,j]:
                    D[i,j] = D[i,k] + D[k,j]
    print(f"  [DeepTSP] Floyd completed: {int(np.sum((D>0)&(D<INF)))} paths")

    # --- Method 1: NN + 2-opt (50 starts) ---
    best_nn, best_tour = float('inf'), None
    nn_times = []
    for start in range(min(n, 50)):
        if time.time() - start_time > time_budget * 0.3: break
        t0 = time.time()
        tour, dist = _nn_tour(D, n, start)
        tour, dist = _two_opt_full(tour, D, n, dist)
        nn_times.append(time.time() - t0)
        if dist < best_nn:
            best_nn, best_tour = dist, tour[:]
    results["methods"]["NN+2-opt(50starts)"] = {"dist": round(best_nn,1), "tour": best_tour}
    results["convergence"]["nn_starts"] = len(nn_times)
    print(f"  [DeepTSP] NN+2-opt: {best_nn:.1f} ({len(nn_times)} starts, {sum(nn_times):.1f}s)")

    # --- Method 2: Simulated Annealing × 5 runs ---
    best_sa, best_sa_tour = float('inf'), None
    sa_history = []
    for run_id in range(5):
        if time.time() - start_time > time_budget * 0.8: break
        t0 = time.time()
        tour, dist, history = _sa_tsp(D, n, iterations=10000, temp_start=2000, cooling=0.998)
        sa_history.append({"run": run_id, "dist": round(dist,1), "time": round(time.time()-t0,1),
                          "convergence": history[-10:]})
        if dist < best_sa:
            best_sa, best_sa_tour = dist, tour[:]
        print(f"  [DeepTSP] SA run {run_id+1}: {dist:.1f} ({time.time()-t0:.1f}s)")
    results["methods"]["SA(5runs)"] = {"dist": round(best_sa,1), "tour": best_sa_tour,
                                        "all_runs": [h["dist"] for h in sa_history]}
    results["convergence"]["sa_runs"] = len(sa_history)

    # --- Method 3: Greedy insertion ---
    tour_gi, dist_gi = _greedy_insertion(D, n)
    tour_gi, dist_gi = _two_opt_full(tour_gi, D, n, dist_gi)
    results["methods"]["GreedyInsert+2opt"] = {"dist": round(dist_gi,1), "tour": tour_gi}
    print(f"  [DeepTSP] GreedyInsert+2opt: {dist_gi:.1f}")

    # --- Pick best ---
    all_methods = [(v["dist"], k, v["tour"]) for k, v in results["methods"].items()]
    all_methods.sort()
    best_dist, best_method, best_tour = all_methods[0]
    results["best"] = {"method": best_method, "distance": best_dist, "tour": best_tour}
    results["all_ranked"] = [(d, m) for d, m, _ in all_methods]
    results["total_time"] = round(time.time() - start_time, 1)

    elapsed = time.time() - start_time
    print(f"  [DeepTSP] BEST: {best_method} -> {best_dist} (took {elapsed:.1f}s)")

    # --- Generate professional figures ---
    try:
        from mathmodel.pipeline.professional_figures import (
            fig_tsp_network, fig_algorithm_comparison, fig_convergence_curve,
            fig_distance_matrix_heatmap
        )
        # TSP network with real layout
        fig_tsp_network(sparse_matrix, n, best_tour, best_dist,
                       str(Path(fig_dir) / f"sub_{question_id}_network.pdf"),
                       title=f"Question {question_id}: TSP Optimal Route")

        # Algorithm comparison
        methods_dict = {m[:25]: d for d, m in results.get("all_ranked", [])}
        if methods_dict:
            fig_algorithm_comparison(methods_dict,
                                    str(Path(fig_dir) / f"sub_{question_id}_algo_compare.pdf"),
                                    title=f"Q{question_id}: Algorithm Comparison")

        # Convergence curves
        if sa_history:
            fig_convergence_curve(sa_history,
                                 str(Path(fig_dir) / f"sub_{question_id}_convergence.pdf"),
                                 title=f"Q{question_id}: Simulated Annealing Convergence")
    except Exception as e:
        print(f"  Professional figures failed: {e}, falling back to basic")
        _plot_tsp_convergence(results, sa_history, fig_dir, question_id)

    return results


def _nn_tour(D, n, start):
    unvisited = set(range(n)); tour = [start]; unvisited.remove(start)
    curr = start
    while unvisited:
        nxt = min(unvisited, key=lambda v: D[curr, v])
        tour.append(nxt); unvisited.remove(nxt); curr = nxt
    tour.append(start)
    return tour, sum(D[tour[i]][tour[i+1]] for i in range(n))


def _two_opt_full(tour, D, n, current_dist=None):
    if current_dist is None:
        current_dist = sum(D[tour[i]][tour[i+1]] for i in range(n))
    improved = True
    while improved:
        improved = False
        for i in range(1, n - 1):
            for j in range(i + 2, n + 1):
                old = D[tour[i-1]][tour[i]] + D[tour[j-1]][tour[j]]
                new = D[tour[i-1]][tour[j-1]] + D[tour[i]][tour[j]]
                if new < old - 1e-10:
                    tour[i:j] = reversed(tour[i:j])
                    current_dist = current_dist - old + new
                    improved = True
    return tour, current_dist


def _sa_tsp(D, n, iterations=10000, temp_start=2000, cooling=0.998):
    import random
    tour = list(range(n)); random.shuffle(tour); tour.append(tour[0])
    curr = sum(D[tour[i]][tour[i+1]] for i in range(n))
    best_tour, best_dist = tour[:], curr
    T = temp_start
    history = []
    record_every = max(1, iterations // 50)
    for it in range(iterations):
        i, j = sorted(random.sample(range(1, n), 2))
        if j - i < 2: continue
        new_tour = tour[:i] + tour[i:j+1][::-1] + tour[j+1:]
        new_dist = sum(D[new_tour[k]][new_tour[k+1]] for k in range(n))
        if new_dist < curr or random.random() < np.exp((curr - new_dist) / max(T, 1e-10)):
            tour, curr = new_tour, new_dist
            if curr < best_dist:
                best_tour, best_dist = tour[:], curr
        T *= cooling
        if it % record_every == 0:
            history.append((it, round(curr, 1), round(best_dist, 1)))
    return best_tour, round(best_dist, 1), history


def _greedy_insertion(D, n):
    """贪心插入法构建TSP"""
    import random
    unvisited = set(range(n))
    start = random.randint(0, n-1)
    tour = [start, start]; unvisited.remove(start)
    while unvisited:
        best_node, best_pos, best_inc = None, -1, float('inf')
        for node in unvisited:
            for pos in range(len(tour) - 1):
                inc = D[tour[pos]][node] + D[node][tour[pos+1]] - D[tour[pos]][tour[pos+1]]
                if inc < best_inc:
                    best_inc, best_node, best_pos = inc, node, pos
        tour.insert(best_pos + 1, best_node)
        unvisited.remove(best_node)
    dist = sum(D[tour[i]][tour[i+1]] for i in range(len(tour)-1))
    return tour, dist


def _plot_tsp_convergence(results, sa_history, fig_dir, question_id):
    """画TSP收敛曲线和多算法对比"""
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mathmodel.visualization.styles import despine, get_colors

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    colors = get_colors(max(len(sa_history), 3))

    # Left: SA convergence
    for ri, h in enumerate(sa_history):
        if h.get("convergence"):
            its = [c[0] for c in h["convergence"]]
            dists = [c[2] for c in h["convergence"]]
            ax1.plot(its, dists, color=colors[ri % len(colors)], linewidth=1.5,
                    alpha=0.7, label=f"SA Run {h['run']+1} ({h['dist']})")
    ax1.set_xlabel("Iteration"); ax1.set_ylabel("Best Distance")
    ax1.set_title("SA Convergence", fontsize=11, loc='left')
    ax1.legend(fontsize=7, frameon=False)
    despine(ax1); ax1.grid(alpha=0.2, linestyle=":")

    # Right: Method comparison
    methods = results.get("all_ranked", [])
    names = [m[:20] for _, m in methods]
    dists = [d for d, _ in methods]
    ax2.barh(range(len(names)), dists, color=colors[:len(names)], height=0.5)
    ax2.set_yticks(range(len(names))); ax2.set_yticklabels(names, fontsize=8)
    for i, d in enumerate(dists):
        ax2.text(d + max(dists)*0.01, i, str(d), va='center', fontsize=8)
    ax2.set_xlabel("Distance"); ax2.set_title("Algorithm Comparison", fontsize=11, loc='left')
    despine(ax2); ax2.grid(alpha=0.2, axis='x', linestyle=":")

    fig.tight_layout()
    out = Path(fig_dir) / f"sub_{question_id}_deep_tsp.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(out), dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  [DeepTSP] Figure: {out.name}")
