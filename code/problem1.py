"""Q1: 纯车辆配送 TSP — 14地点 1000kg"""
import sys; sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from utils import *
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mathmodel.visualization.styles import despine, get_colors

def main():
    print("=" * 50)
    print("  Q1: Pure Vehicle TSP (14 locations, 1000kg)")
    print("=" * 50)

    # Load data
    sparse, n = load_distance_matrix("附件1.xlsx")
    print(f"  Data: {n} locations, {(~np.isnan(sparse)).sum()} edges")

    # Floyd-Warshall
    D = floyd_warshall(sparse, n)
    n_edges = int(np.sum((D > 0) & (D < 1e8)))
    print(f"  Floyd completed: {n_edges} paths")

    # Solve TSP
    tour, dist = solve_tsp(D, n, n_starts=14)
    time_h = dist / VEHICLE_SPEED
    labels = tour_to_labels(tour)

    print(f"\n  === RESULTS ===")
    print(f"  Optimal route: {' -> '.join(str(l) for l in labels)}")
    print(f"  Total distance: {dist} km")
    print(f"  Delivery time: {time_h:.2f} h")
    print(f"  Expected: ~582 km, ~6.32 h")
    print(f"  Error: {abs(dist-582):.1f} km ({abs(dist-582)/582*100:.1f}%)")

    # Figure: TSP route diagram
    fig, ax = plt.subplots(figsize=(10, 3))
    colors = get_colors(2)
    xs = list(range(len(tour)))
    ax.plot(xs, [0]*len(tour), 'o-', color=colors[0], markersize=8,
            linewidth=2, markerfacecolor='white', markeredgewidth=2)
    for i, node in enumerate(tour):
        ax.annotate(str(node+1), (i, 0.15), fontsize=9, ha='center', fontweight='bold')
    ax.set_title(f"Q1 Optimal Vehicle Route: {dist}km, {time_h:.2f}h", fontsize=11, loc='left')
    ax.set_xlabel("Visit Order"); ax.set_yticks([])
    despine(ax); ax.grid(alpha=0.2, axis='x', linestyle=":")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "q1_tsp_route.pdf", dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print("  Figure saved: q1_tsp_route.pdf")

    return tour, dist, time_h

if __name__ == "__main__":
    main()
