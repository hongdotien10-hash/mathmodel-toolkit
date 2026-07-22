"""图论与网络模型求解器。

提供最短路径、最大流、最小生成树、TSP 等算法。
"""

import numpy as np
from typing import Optional


class GraphSolver:
    """图论求解器。

    Usage::

        gs = GraphSolver()

        # 最短路径
        dist, path = gs.dijkstra(adj_matrix, source=0, target=5)

        # 最大流
        max_flow = gs.max_flow(capacity_matrix, source=0, sink=5)
    """

    def dijkstra(
        self,
        adj_matrix: np.ndarray | list[list[float]],
        source: int = 0,
        target: Optional[int] = None,
    ) -> dict:
        """Dijkstra 最短路径算法。

        Args:
            adj_matrix: 邻接矩阵 (n×n)，inf 表示无边
            source: 起点
            target: 终点，None 时返回所有点的最短距离

        Returns:
            dict: {"distances", "paths", "source"}
        """
        n = len(adj_matrix)
        A = np.array(adj_matrix, dtype=float)
        A[A == 0] = np.inf  # 0 也视为无边
        np.fill_diagonal(A, 0)

        dist = np.full(n, np.inf)
        dist[source] = 0
        visited = np.zeros(n, dtype=bool)
        prev = np.full(n, -1, dtype=int)

        for _ in range(n):
            # 找最近的未访问节点
            u = np.argmin(np.where(visited, np.inf, dist))
            if dist[u] == np.inf:
                break
            visited[u] = True

            for v in range(n):
                if not visited[v] and A[u, v] < np.inf:
                    new_dist = dist[u] + A[u, v]
                    if new_dist < dist[v]:
                        dist[v] = new_dist
                        prev[v] = u

        # 回溯路径
        def reconstruct_path(t: int) -> list[int]:
            path = []
            current = t
            while current != -1:
                path.append(current)
                current = prev[current]
            path.reverse()
            return path if path[0] == source else []

        result = {
            "distances": dist.tolist(),
            "source": source,
        }

        if target is not None:
            result["distance_to_target"] = float(dist[target])
            result["path_to_target"] = reconstruct_path(target)
        else:
            result["paths"] = {i: reconstruct_path(i) for i in range(n) if i != source}

        return result

    def floyd(self, adj_matrix: np.ndarray | list[list[float]]) -> dict:
        """Floyd-Warshall 全源最短路径。"""
        n = len(adj_matrix)
        A = np.array(adj_matrix, dtype=float)
        A[A == 0] = np.inf
        np.fill_diagonal(A, 0)

        dist = A.copy()
        nxt = np.full((n, n), -1, dtype=int)

        for i in range(n):
            for j in range(n):
                if i != j and dist[i, j] < np.inf:
                    nxt[i, j] = j

        for k in range(n):
            for i in range(n):
                for j in range(n):
                    if dist[i, k] + dist[k, j] < dist[i, j]:
                        dist[i, j] = dist[i, k] + dist[k, j]
                        nxt[i, j] = nxt[i, k]

        return {
            "distance_matrix": dist.tolist(),
            "has_negative_cycle": bool(np.any(np.diag(dist) < 0)),
        }

    def min_spanning_tree(
        self,
        adj_matrix: np.ndarray | list[list[float]],
        method: str = "kruskal",
    ) -> dict:
        """最小生成树。

        Returns:
            dict: {"edges": [(u, v, weight), ...], "total_weight"}
        """
        n = len(adj_matrix)
        A = np.array(adj_matrix, dtype=float)

        # 提取边列表
        edges = []
        for i in range(n):
            for j in range(i + 1, n):
                w = A[i, j]
                if w > 0 and w < np.inf:
                    edges.append((w, i, j))

        edges.sort()

        # Kruskal
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[py] = px
                return True
            return False

        mst_edges = []
        total_weight = 0
        for w, u, v in edges:
            if union(u, v):
                mst_edges.append((int(u), int(v), float(w)))
                total_weight += w
                if len(mst_edges) == n - 1:
                    break

        return {
            "edges": mst_edges,
            "total_weight": round(float(total_weight), 4),
            "n_edges": len(mst_edges),
        }

    def max_flow(
        self,
        capacity: np.ndarray | list[list[float]],
        source: int,
        sink: int,
    ) -> dict:
        """最大流 (Edmonds-Karp 算法)。

        Returns:
            dict: {"max_flow", "flow_matrix"}
        """
        n = len(capacity)
        C = np.array(capacity, dtype=float)
        F = np.zeros((n, n))
        total_flow = 0

        while True:
            # BFS 找增广路
            parent = np.full(n, -1, dtype=int)
            parent[source] = source
            q = [source]
            found = False

            for u in q:
                if u == sink:
                    found = True
                    break
                for v in range(n):
                    if parent[v] == -1 and C[u, v] - F[u, v] > 0:
                        parent[v] = u
                        q.append(v)

            if not found:
                break

            # 找瓶颈容量
            bottleneck = float("inf")
            v = sink
            while v != source:
                u = parent[v]
                bottleneck = min(bottleneck, C[u, v] - F[u, v])
                v = u

            # 更新流量
            v = sink
            while v != source:
                u = parent[v]
                F[u, v] += bottleneck
                F[v, u] -= bottleneck
                v = u

            total_flow += bottleneck

        return {
            "max_flow": round(float(total_flow), 4),
            "flow_matrix": F.tolist(),
        }

    def tsp_nearest_neighbor(
        self,
        distance_matrix: np.ndarray | list[list[float]],
        start: int = 0,
    ) -> dict:
        """TSP 最近邻启发式算法。

        Returns:
            dict: {"tour", "total_distance"}
        """
        D = np.array(distance_matrix, dtype=float)
        n = len(D)

        unvisited = set(range(n))
        tour = [start]
        unvisited.remove(start)
        total_dist = 0

        current = start
        while unvisited:
            nxt = min(unvisited, key=lambda v: D[current, v])
            total_dist += D[current, nxt]
            tour.append(nxt)
            unvisited.remove(nxt)
            current = nxt

        total_dist += D[current, start]  # 回到起点
        tour.append(start)

        return {
            "tour": tour,
            "total_distance": round(float(total_dist), 4),
            "n_nodes": n,
        }
