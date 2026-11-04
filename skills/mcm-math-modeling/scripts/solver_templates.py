"""
数学建模可复用求解器模板
GA / PSO / SA / 二分法 / 动态规划
每次做题从本文导入，不要从零写网格搜索

用法:
  from solver_templates import GA, PSO, SA, bisection_search
"""
import numpy as np
from scipy.optimize import minimize, differential_evolution

# ============================================================
# 遗传算法 (Genetic Algorithm)
# 适用: 离散/混合变量优化、大规模组合优化(Q5等)
# ============================================================
class GA:
    """实数编码遗传算法，带精英策略和自适应交叉"""
    def __init__(self, fitness_func, bounds, pop_size=100, max_gen=200,
                 cross_prob=0.8, mut_prob=0.1, elite_ratio=0.05):
        self.f = fitness_func        # fitness(x) -> float, 越大越好
        self.bounds = np.array(bounds)  # [[low,high],...]
        self.n_dim = len(bounds)
        self.pop_size = pop_size
        self.max_gen = max_gen
        self.cross_prob = cross_prob
        self.mut_prob = mut_prob
        self.n_elite = max(1, int(pop_size * elite_ratio))
        self.history = []  # (gen, best_fitness)

    def _init_pop(self):
        pop = np.random.rand(self.pop_size, self.n_dim)
        for d in range(self.n_dim):
            lo, hi = self.bounds[d]
            pop[:, d] = lo + pop[:, d] * (hi - lo)
        return pop

    def _tournament(self, fitness, k=3):
        idx = np.random.choice(self.pop_size, k, replace=False)
        return idx[np.argmax(fitness[idx])]

    def _crossover(self, p1, p2):
        if np.random.rand() > self.cross_prob:
            return p1.copy()
        alpha = np.random.rand(self.n_dim)
        return p1 * alpha + p2 * (1 - alpha)

    def _mutate(self, x, gen):
        rate = self.mut_prob * (1 - 0.5 * gen / self.max_gen)  # 递减变异率
        mask = np.random.rand(self.n_dim) < rate
        if not np.any(mask):
            return x
        x_new = x.copy()
        for d in range(self.n_dim):
            if mask[d]:
                delta = (self.bounds[d][1] - self.bounds[d][0]) * 0.1
                x_new[d] += np.random.randn() * delta
        return np.clip(x_new, self.bounds[:, 0], self.bounds[:, 1])

    def optimize(self, seed=42, verbose=True):
        """返回: (最优解, 最优适应度, 收敛历史)"""
        np.random.seed(seed)
        pop = self._init_pop()
        best_x, best_f = None, -np.inf

        for gen in range(self.max_gen):
            fitness = np.array([self.f(x) for x in pop])
            elite_idx = np.argsort(fitness)[-self.n_elite:]
            if fitness[elite_idx[-1]] > best_f:
                best_f = fitness[elite_idx[-1]]
                best_x = pop[elite_idx[-1]].copy()
            self.history.append((gen, best_f))

            new_pop = [pop[i].copy() for i in elite_idx]  # 精英保留
            while len(new_pop) < self.pop_size:
                p1 = pop[self._tournament(fitness)]
                p2 = pop[self._tournament(fitness)]
                child = self._crossover(p1, p2)
                child = self._mutate(child, gen)
                new_pop.append(child)
            pop = np.array(new_pop)

            if verbose and gen % 50 == 0:
                print(f"  GA gen {gen}: best={best_f:.4f}")

        return best_x, best_f, self.history

# ============================================================
# 粒子群优化 (Particle Swarm Optimization)
# 适用: 连续变量优化、单峰/多峰函数(Q2-Q4等)
# ============================================================
class PSO:
    """标准PSO，惯性权重线性递减"""
    def __init__(self, fitness_func, bounds, n_particles=40, max_iter=200,
                 w_start=0.9, w_end=0.4, c1=2.0, c2=2.0):
        self.f = fitness_func
        self.bounds = np.array(bounds)
        self.n_dim = len(bounds)
        self.n_particles = n_particles
        self.max_iter = max_iter
        self.w_start, self.w_end = w_start, w_end
        self.c1, self.c2 = c1, c2
        self.history = []

    def optimize(self, seed=42, verbose=True):
        np.random.seed(seed)
        pos = np.random.rand(self.n_particles, self.n_dim)
        for d in range(self.n_dim):
            pos[:, d] = self.bounds[d, 0] + pos[:, d] * (self.bounds[d, 1] - self.bounds[d, 0])
        vel = np.random.randn(self.n_particles, self.n_dim) * 0.1
        p_best_pos = pos.copy()
        p_best_val = np.array([self.f(x) for x in pos])
        g_best_idx = np.argmax(p_best_val)
        g_best_pos = p_best_pos[g_best_idx].copy()
        g_best_val = p_best_val[g_best_idx]

        for t in range(self.max_iter):
            w = self.w_start - (self.w_start - self.w_end) * t / self.max_iter
            r1, r2 = np.random.rand(2, self.n_particles, self.n_dim)
            vel = w * vel + self.c1 * r1 * (p_best_pos - pos) + self.c2 * r2 * (g_best_pos - pos)
            pos = np.clip(pos + vel, self.bounds[:, 0], self.bounds[:, 1])
            vals = np.array([self.f(x) for x in pos])
            improved = vals > p_best_val
            p_best_pos[improved] = pos[improved].copy()
            p_best_val[improved] = vals[improved]
            new_best = np.argmax(p_best_val)
            if p_best_val[new_best] > g_best_val:
                g_best_val = p_best_val[new_best]
                g_best_pos = p_best_pos[new_best].copy()
            self.history.append((t, g_best_val))
            if verbose and t % 50 == 0:
                print(f"  PSO iter {t}: best={g_best_val:.4f}")

        return g_best_pos, g_best_val, self.history

# ============================================================
# 模拟退火 (Simulated Annealing)
# 适用: 复杂非凸函数、需要逃离局部最优的场景
# ============================================================
class SA:
    """快速模拟退火，指数降温"""
    def __init__(self, fitness_func, bounds, T_start=1000, T_end=0.01,
                 cooling_rate=0.95, steps_per_T=50):
        self.f = fitness_func
        self.bounds = np.array(bounds)
        self.n_dim = len(bounds)
        self.T_start = T_start
        self.T_end = T_end
        self.cooling_rate = cooling_rate
        self.steps_per_T = steps_per_T
        self.history = []

    def optimize(self, seed=42, verbose=True):
        np.random.seed(seed)
        x = np.random.rand(self.n_dim)
        for d in range(self.n_dim):
            x[d] = self.bounds[d, 0] + x[d] * (self.bounds[d, 1] - self.bounds[d, 0])
        best_x, best_f = x.copy(), self.f(x)
        T = self.T_start

        while T > self.T_end:
            for _ in range(self.steps_per_T):
                x_new = x + np.random.randn(self.n_dim) * T * 0.01
                x_new = np.clip(x_new, self.bounds[:, 0], self.bounds[:, 1])
                f_new = self.f(x_new)
                delta = f_new - self.f(x)
                if delta > 0 or np.random.rand() < np.exp(delta / (T + 1e-10)):
                    x = x_new
                    if f_new > best_f:
                        best_f = f_new
                        best_x = x_new.copy()
            self.history.append((T, best_f))
            if verbose and T > 10:
                print(f"  SA T={T:.1f}: best={best_f:.4f}")
            T *= self.cooling_rate

        return best_x, best_f, self.history

# ============================================================
# 二分法搜索 (Bisection)
# 适用: 单调函数的零点/阈值搜索(碰撞时刻、最小螺距等)
# ============================================================
def bisection_search(f, lo, hi, target=0, tol=1e-8, max_iter=100):
    """
    f(x)单调, 求 f(x)=target 的x值
    f(lo)和f(hi)必须在target两侧
    """
    flo, fhi = f(lo) - target, f(hi) - target
    if flo * fhi > 0:
        raise ValueError(f"f({lo})={flo+target} and f({hi})={fhi+target} on same side of {target}")
    for i in range(max_iter):
        mid = (lo + hi) / 2
        fmid = f(mid) - target
        if abs(fmid) < tol or (hi - lo) < tol:
            return mid
        if flo * fmid < 0:
            hi, fhi = mid, fmid
        else:
            lo, flo = mid, fmid
    return (lo + hi) / 2

# ============================================================
# 自适应网格搜索 (Adaptive Grid)
# 适用: 低维(≤3D)参数的粗定位→精搜索
# ============================================================
def adaptive_grid_search(f, bounds, n_coarse=20, n_fine=50, refine_ratio=0.2):
    """
    二阶段网格搜索: 粗网格定位→在最优附近细网格精搜
    bounds: [[lo,hi],...]
    返回: (最优解, 最优值)
    """
    n_dim = len(bounds)
    # Coarse grid
    coarse_axes = [np.linspace(b[0], b[1], n_coarse) for b in bounds]
    coarse_grid = np.stack(np.meshgrid(*coarse_axes, indexing='ij'), -1).reshape(-1, n_dim)
    coarse_vals = np.array([f(x) for x in coarse_grid])
    best_idx = np.argmax(coarse_vals)
    best_x = coarse_grid[best_idx].copy()
    # Fine grid around best
    fine_bounds = []
    for d in range(n_dim):
        span = bounds[d][1] - bounds[d][0]
        center = best_x[d]
        half = span * refine_ratio / 2
        fine_bounds.append([max(bounds[d][0], center-half), min(bounds[d][1], center+half)])
    fine_axes = [np.linspace(b[0], b[1], n_fine) for b in fine_bounds]
    fine_grid = np.stack(np.meshgrid(*fine_axes, indexing='ij'), -1).reshape(-1, n_dim)
    fine_vals = np.array([f(x) for x in fine_grid])
    best_fine_idx = np.argmax(fine_vals)
    return fine_grid[best_fine_idx], fine_vals[best_fine_idx]
