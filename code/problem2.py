"""Q2+Q3: 车辆+无人机协同配送"""
import sys; sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from utils import *
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mathmodel.visualization.styles import despine, get_colors

def solve_vehicle_drone(D_vehicle, D_drone, n, capacity_kg, demands=None):
    """
    车辆+无人机协同求解：
    1. TSP 确定车辆主线
    2. 扫描每个地点，判断无人机能否从车辆位置起飞完成配送并在70min内返回
    """
    if demands is None:
        demands = [0] * n
        demands[START_NODE] = 0

    # Phase 1: Vehicle TSP route
    tour, total_dist = solve_tsp(D_vehicle, n, n_starts=min(n, 14))

    # Phase 2: Assign drone tasks
    drone_tasks = []
    served_by_drone = set()

    for idx in range(len(tour) - 1):
        curr_node = tour[idx]
        # Check nearby nodes reachable by drone from current vehicle position
        for target in range(n):
            if target == curr_node or target == START_NODE:
                continue
            if target in served_by_drone:
                continue
            # Check if drone can: curr -> target -> next_vehicle_pos within 70 min
            next_vehicle_pos = tour[min(idx + 2, len(tour) - 1)]
            flight_dist = D_drone[curr_node][target] + D_drone[target][next_vehicle_pos]
            flight_time_min = (flight_dist / DRONE_SPEED) * 60
            if flight_time_min <= DRONE_MAX_FLIGHT_MIN and demands[target] <= DRONE_CAPACITY:
                drone_tasks.append({
                    "from_vehicle": curr_node + 1,
                    "target": target + 1,
                    "return_to": next_vehicle_pos + 1,
                    "flight_dist": round(flight_dist, 1),
                    "flight_time_min": round(flight_time_min, 1)
                })
                served_by_drone.add(target)

    # Calculate total time: vehicle time dominates
    vehicle_time = total_dist / VEHICLE_SPEED
    # Drone time is bounded by vehicle route + individual flights
    drone_total_flights = sum(t["flight_dist"] for t in drone_tasks)
    drone_total_time = drone_total_flights / DRONE_SPEED

    return {
        "tour": tour, "tour_labels": tour_to_labels(tour),
        "total_dist": total_dist, "vehicle_time": round(vehicle_time, 2),
        "drone_tasks": drone_tasks, "n_drone_tasks": len(drone_tasks),
        "drone_total_dist": round(drone_total_flights, 1),
        "drone_total_time": round(drone_total_time, 2),
        "n_served_by_drone": len(served_by_drone),
        "capacity": capacity_kg
    }


def main():
    for q_id, cap, fname in [("Q2", 1000, "附件2.xlsx"), ("Q3", 500, "附件2.xlsx")]:
        print(f"\n{'='*50}")
        print(f"  {q_id}: Vehicle + Drone (14 loc, {cap}kg)")
        print(f"{'='*50}")

        sparse, n = load_distance_matrix(fname, 14)
        D_vehicle = floyd_warshall(sparse, n)
        # For drone: same network but includes drone-only edges (虚线)
        # 简化：用同一个路网，无人机可飞直线所以用欧氏距离近似
        # 实际应区分实线(车辆+无人机)和虚线(仅无人机)
        D_drone = D_vehicle.copy()  # 简化假设：无人机路网=车辆路网

        result = solve_vehicle_drone(D_vehicle, D_drone, n, cap)
        print(f"  Vehicle route: {' -> '.join(str(l) for l in result['tour_labels'][:8])}...")
        print(f"  Total distance: {result['total_dist']} km")
        print(f"  Vehicle time: {result['vehicle_time']:.2f} h")
        print(f"  Drone tasks: {result['n_drone_tasks']}")
        for t in result['drone_tasks'][:5]:
            print(f"    Drone: vehicle@{t['from_vehicle']} -> loc{t['target']} -> return@{t['return_to']} ({t['flight_time_min']}min)")

        # Figure
        fig, ax = plt.subplots(figsize=(10, 3.5))
        colors = get_colors(3)
        tour = result['tour']
        n_pts = len(tour)
        ax.plot(range(n_pts), [0]*n_pts, 'o-', color=colors[0], markersize=8,
                linewidth=2, markerfacecolor='white', label='Vehicle Route')
        # Mark drone targets
        drone_targets = [t['target'] - 1 for t in result['drone_tasks']]
        for i, node in enumerate(tour):
            if node in drone_targets:
                ax.annotate(f'{node+1}✈', (i, 0.2), fontsize=8, ha='center', color=colors[1], fontweight='bold')
            else:
                ax.annotate(str(node+1), (i, 0.1), fontsize=8, ha='center')
        ax.set_title(f"{q_id} Vehicle+Drone Route ({result['total_dist']}km, {result['n_drone_tasks']} drone tasks)", fontsize=11, loc='left')
        ax.set_xlabel("Sequence"); ax.set_yticks([])
        ax.legend(fontsize=8, frameon=False)
        despine(ax); ax.grid(alpha=0.2, axis='x', linestyle=":")
        fig.tight_layout()
        fpath = FIG_DIR / f"{q_id.lower()}_drone_route.pdf"
        fig.savefig(fpath, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        print(f"  Figure saved: {fpath.name}")

if __name__ == "__main__":
    main()
