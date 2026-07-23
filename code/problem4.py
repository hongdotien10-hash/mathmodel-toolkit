"""Q4: 选址+路径联合优化 — 30地点 500kg 选2个集散点"""
import sys; sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from utils import *
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mathmodel.visualization.styles import despine, get_colors
from itertools import combinations

def main():
    print("=" * 50)
    print("  Q4: Location-Routing (30 locations, 500kg, 2 depots)")
    print("=" * 50)

    # Load 30-location data from attachment 2
    sparse, n_full = load_distance_matrix("附件2.xlsx")
    n = min(n_full, 30)
    sparse = sparse[:n, :n] if sparse.shape[0] >= n else sparse
    # If data only has 14 locations, pad with Floyd completion
    if sparse.shape[0] < 30:
        print(f"  Warning: Only {sparse.shape[0]} locations in data (need 30)")
        print(f"  Using available {sparse.shape[0]} locations for demonstration")
        n = sparse.shape[0]

    print(f"  Data: {n} locations, {(~np.isnan(sparse)).sum()} edges")

    # Floyd-Warshall
    D = floyd_warshall(sparse, n)
    print(f"  Floyd completed")

    # Enumerate 2-depot combinations
    locations = list(range(n))

    # Limit to top candidates for speed
    if n > 15:
        # Use centrality heuristic: pick nodes with smallest max distance to others
        centrality = [(np.max(D[i]), i) for i in range(n)]
        centrality.sort()
        candidates = [i for _, i in centrality[:15]]
        print(f"  Reduced to {len(candidates)} depot candidates by centrality")
    else:
        candidates = locations

    best_total_time = float('inf')
    best_solution = None

    n_combos = len(list(combinations(candidates, 2)))
    print(f"  Evaluating {n_combos} depot combinations...")

    for d1, d2 in combinations(candidates, 2):
        # Assign each location to nearest depot
        assigned = {d1: [d1], d2: [d2]}
        for loc in locations:
            if loc in (d1, d2): continue
            if D[loc][d1] <= D[loc][d2]:
                assigned[d1].append(loc)
            else:
                assigned[d2].append(loc)

        # Solve TSP for each depot's region
        total_time = 0
        region_info = {}
        for depot in [d1, d2]:
            region = assigned[depot]
            if len(region) <= 1:
                region_info[depot] = {"dist": 0, "time": 0}
                continue
            # Build sub-distance matrix for this region
            idx_map = {old: new for new, old in enumerate(region)}
            m = len(region)
            sub_D = np.zeros((m, m))
            for i_old, i_new in idx_map.items():
                for j_old, j_new in idx_map.items():
                    sub_D[i_new, j_new] = D[i_old, j_old]
            # Find start index (depot position in region)
            start = idx_map[depot]
            tour, dist = solve_tsp(sub_D, m, n_starts=min(m, 10))
            time_h = dist / VEHICLE_SPEED
            region_info[depot] = {"dist": dist, "time": time_h,
                                   "n_locations": m, "tour": [region[t] + 1 for t in tour]}
            total_time = max(total_time, time_h)

        if total_time < best_total_time:
            best_total_time = total_time
            best_solution = {
                "depots": (d1 + 1, d2 + 1),
                "total_time": round(total_time, 2),
                "regions": region_info
            }

    print(f"\n  === RESULTS ===")
    print(f"  Best depots: Location {best_solution['depots'][0]} & {best_solution['depots'][1]}")
    print(f"  Total time: {best_solution['total_time']:.2f} h (max of two regions)")
    for d, info in best_solution['regions'].items():
        print(f"  Depot {d+1}: {info['n_locations']} locations, {info['dist']}km, {info['time']:.2f}h")

    # Figure: depot selection map
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = get_colors(3)
    d1, d2 = best_solution['depots'][0] - 1, best_solution['depots'][1] - 1
    for loc in locations:
        dist_to_d1 = D[loc][d1]
        dist_to_d2 = D[loc][d2]
        if dist_to_d1 <= dist_to_d2:
            ax.scatter(loc, 0, c=colors[0], s=100, zorder=5, edgecolors='white')
        else:
            ax.scatter(loc, 0, c=colors[1], s=100, zorder=5, edgecolors='white')
        ax.annotate(str(loc+1), (loc, 0.15), fontsize=7, ha='center')
    ax.scatter([d1, d2], [0, 0], c='red', s=200, marker='*', zorder=10, edgecolors='white',
               label=f"Depots ({d1+1}, {d2+1})")
    ax.set_title(f"Q4 Depot Selection: {best_solution['depots']}, Total Time={best_solution['total_time']}h",
                 fontsize=11, loc='left')
    ax.set_yticks([]); ax.set_xlabel("Location ID")
    ax.legend(fontsize=8); despine(ax); ax.grid(alpha=0.2, axis='x', linestyle=":")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "q4_depot_selection.pdf", dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print("  Figure saved: q4_depot_selection.pdf")

    return best_solution

if __name__ == "__main__":
    main()
