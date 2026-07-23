"""电工杯B题 共享工具：数据加载、Floyd-Warshall、TSP求解器"""
import numpy as np, pandas as pd
from pathlib import Path

PROBLEM_DIR = Path(__file__).parent.parent / "problems" / "sample"
FIG_DIR = Path(__file__).parent.parent / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# 题面参数
VEHICLE_SPEED = 50  # km/h
DRONE_SPEED = 75    # km/h
DRONE_MAX_FLIGHT_MIN = 70  # min
DRONE_CAPACITY = 50  # kg
START_NODE = 8  # 地点9 (0-indexed)


def load_distance_matrix(filename, n_locations=None):
    """加载稀疏距离矩阵，返回 n×n numpy array"""
    df = pd.read_excel(PROBLEM_DIR / filename, header=None)
    vals = df.iloc[1:, 1:].values.astype(float)
    n = vals.shape[0] if n_locations is None else min(n_locations, vals.shape[0])
    vals = vals[:n, :n]
    return vals, n


def floyd_warshall(sparse_matrix, n):
    """Floyd-Warshall: 稀疏距离矩阵 -> 全对最短路径"""
    INF = 1e9
    D = np.full((n, n), INF)
    for i in range(n):
        for j in range(n):
            v = sparse_matrix[i, j] if i < sparse_matrix.shape[0] and j < sparse_matrix.shape[1] else np.nan
            if not np.isnan(v) and v > 0:
                D[i, j] = v
            elif i == j:
                D[i, j] = 0

    # 对称化
    for i in range(n):
        for j in range(n):
            if D[i, j] < INF and D[j, i] >= INF:
                D[j, i] = D[i, j]

    for k in range(n):
        for i in range(n):
            if D[i, k] >= INF: continue
            for j in range(n):
                nd = D[i, k] + D[k, j]
                if nd < D[i, j]:
                    D[i, j] = nd
    return D


def tsp_nearest_neighbor(D, n, start=0):
    """最近邻 TSP"""
    unvisited = set(range(n))
    tour = [start]; unvisited.remove(start)
    curr = start
    while unvisited:
        nxt = min(unvisited, key=lambda v: D[curr, v])
        tour.append(nxt); unvisited.remove(nxt); curr = nxt
    tour.append(start)
    dist = sum(D[tour[i]][tour[i+1]] for i in range(n))
    return tour, dist


def tsp_two_opt(tour, D, n):
    """2-opt 局部搜索"""
    best = sum(D[tour[i]][tour[i+1]] for i in range(n))
    improved = True
    iters = 0
    while improved and iters < 200:
        improved = False; iters += 1
        for i in range(1, n - 1):
            for j in range(i + 2, n + 1):
                old = D[tour[i-1]][tour[i]] + D[tour[j-1]][tour[j]]
                new = D[tour[i-1]][tour[j-1]] + D[tour[i]][tour[j]]
                if new < old - 1e-10:
                    tour[i:j] = reversed(tour[i:j])
                    best = best - old + new
                    improved = True
    return tour, best


def tsp_simulated_annealing(D, n, iterations=5000):
    """模拟退火 TSP"""
    import random
    tour = list(range(n)); random.shuffle(tour); tour.append(tour[0])
    curr = sum(D[tour[i]][tour[i+1]] for i in range(n))
    best_tour, best_dist = tour[:], curr
    T = 1000.0
    for _ in range(iterations):
        i, j = sorted(random.sample(range(1, n), 2))
        if j - i < 2: continue
        new_tour = tour[:i] + tour[i:j+1][::-1] + tour[j+1:]
        new_dist = sum(D[new_tour[k]][new_tour[k+1]] for k in range(n))
        if new_dist < curr or random.random() < np.exp((curr - new_dist) / max(T, 1e-10)):
            tour, curr = new_tour, new_dist
            if curr < best_dist:
                best_tour, best_dist = tour[:], curr
        T *= 0.995
    return best_tour, best_dist


def solve_tsp(D, n, n_starts=15):
    """TSP 三阶段求解: NN多起点 + 2-opt + SA 选最优"""
    best_tour, best_dist = None, float('inf')
    for start in range(min(n, n_starts)):
        tour, dist = tsp_nearest_neighbor(D, n, start)
        tour, dist = tsp_two_opt(tour, D, n)
        if dist < best_dist:
            best_tour, best_dist = tour, dist

    if n >= 10:
        sa_tour, sa_dist = tsp_simulated_annealing(D, n, 3000)
        if sa_dist < best_dist:
            best_tour, best_dist = sa_tour, sa_dist
            print(f"  SA improved: {sa_dist:.1f}")

    return best_tour, round(best_dist, 1)


def tour_to_labels(tour):
    """0-indexed tour -> 1-indexed labels"""
    return [t + 1 for t in tour]
