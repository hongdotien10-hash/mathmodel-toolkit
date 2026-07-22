"""数学模型知识库。

维护题型与推荐模型的映射关系，作为模型推荐的「大脑」。
知识库可扩展：用户可以通过 add_rule() 注册自定义规则。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelEntry:
    """知识库中的单个模型条目。

    Attributes:
        model: 模型名称（如 "灰色预测 GM(1,1)"）
        problem_type: 匹配的题型（如 "预测"）
        score: 基础推荐分数 (0~1)
        reason: 推荐理由描述
        data_requirements: 数据要求，如 {"min_samples": 4, "numeric": True}
        tags: 标签，如 ["时序", "小样本", "单变量"]
        solver_path: 对应的求解器路径，如 "statistics.grey_forecast"
    """
    model: str
    problem_type: str
    score: float = 0.5
    reason: str = ""
    data_requirements: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    solver_path: str = ""


# =========================================================================
# 内置知识库
# =========================================================================

def _build_builtin_kb() -> list[ModelEntry]:
    """构建内置的题型↔模型映射知识库。"""
    entries = []

    # ---- 优化类 ----
    opt = "优化"
    entries.extend([
        ModelEntry("线性规划 (scipy.optimize.linprog)", opt,
                   score=0.9,
                   reason="变量连续、约束和目标均为线性时的标准方法",
                   data_requirements={"numeric": True},
                   tags=["连续", "线性", "单目标"],
                   solver_path="optimization.linear_programming"),
        ModelEntry("整数规划 (PuLP)", opt,
                   score=0.85,
                   reason="变量为整数（如人员分配、选址）时的精确求解",
                   data_requirements={"numeric": True},
                   tags=["离散", "整数", "组合"],
                   solver_path="optimization.integer_programming"),
        ModelEntry("非线性规划 (scipy.optimize.minimize)", opt,
                   score=0.8,
                   reason="目标或约束包含非线性项",
                   data_requirements={"numeric": True},
                   tags=["连续", "非线性"],
                   solver_path="optimization.nonlinear_programming"),
        ModelEntry("多目标优化 (NSGA-II / 加权法)", opt,
                   score=0.75,
                   reason="多个相互冲突的优化目标",
                   data_requirements={"numeric": True},
                   tags=["多目标", "Pareto"],
                   solver_path="optimization.multi_objective"),
        ModelEntry("动态规划", opt,
                   score=0.7,
                   reason="具有最优子结构的多阶段决策问题",
                   data_requirements={},
                   tags=["多阶段", "递推"],
                   solver_path="optimization.dynamic_programming"),
    ])

    # ---- 预测类 ----
    pred = "预测"
    entries.extend([
        ModelEntry("灰色预测 GM(1,1)", pred,
                   score=0.95,
                   reason="小样本（4-10个数据点）单变量时序预测的首选",
                   data_requirements={"min_samples": 4, "max_samples": 30},
                   tags=["小样本", "指数趋势", "单变量"],
                   solver_path="statistics.grey_forecast"),
        ModelEntry("ARIMA 时间序列", pred,
                   score=0.9,
                   reason="中长时序的平稳/可差分平稳序列预测",
                   data_requirements={"min_samples": 30, "numeric": True},
                   tags=["时序", "大样本", "平稳"],
                   solver_path="statistics.arima"),
        ModelEntry("多元线性回归", pred,
                   score=0.85,
                   reason="因变量与多个自变量呈线性关系时的预测",
                   data_requirements={"min_samples": 20, "numeric": True},
                   tags=["多变量", "线性", "可解释"],
                   solver_path="statistics.linear_regression"),
        ModelEntry("多项式回归", pred,
                   score=0.7,
                   reason="非线性趋势但可用多项式近似的预测",
                   data_requirements={"min_samples": 10, "numeric": True},
                   tags=["非线性", "趋势"],
                   solver_path="statistics.polynomial_regression"),
        ModelEntry("随机森林回归", pred,
                   score=0.8,
                   reason="高维非线性关系、交互效应复杂时的预测",
                   data_requirements={"min_samples": 50, "numeric": True},
                   tags=["非线性", "高维", "集成"],
                   solver_path="ml.random_forest"),
        ModelEntry("三次指数平滑 (Holt-Winters)", pred,
                   score=0.75,
                   reason="具有趋势和季节性的时序预测",
                   data_requirements={"min_samples": 12, "numeric": True},
                   tags=["时序", "季节性", "趋势"],
                   solver_path="statistics.holt_winters"),
        ModelEntry("XGBoost 回归", pred,
                   score=0.82,
                   reason="结构化数据的强基线模型，自动处理复杂关系",
                   data_requirements={"min_samples": 50, "numeric": True},
                   tags=["非线性", "高维", "集成", "竞赛"],
                   solver_path="ml.xgboost"),
    ])

    # ---- 评价类 ----
    eva = "评价"
    entries.extend([
        ModelEntry("TOPSIS 优劣解距离法", eva,
                   score=0.95,
                   reason="多方案多指标综合评价的通用方法，结果直观",
                   data_requirements={"min_samples": 2, "numeric": True},
                   tags=["多方案", "客观", "距离"],
                   solver_path="evaluation.topsis"),
        ModelEntry("层次分析法 AHP", eva,
                   score=0.9,
                   reason="含主观判断的多层次指标体系评价",
                   data_requirements={},
                   tags=["主观权重", "层次", "一致性"],
                   solver_path="evaluation.ahp"),
        ModelEntry("熵权法", eva,
                   score=0.88,
                   reason="完全基于数据离散度的客观赋权评价",
                   data_requirements={"min_samples": 3, "numeric": True},
                   tags=["客观权重", "信息熵"],
                   solver_path="evaluation.entropy_weight"),
        ModelEntry("模糊综合评价", eva,
                   score=0.85,
                   reason="评价标准模糊、边界不清晰的综合评价",
                   data_requirements={},
                   tags=["模糊数学", "隶属度"],
                   solver_path="evaluation.fuzzy_comprehensive"),
        ModelEntry("灰色关联分析", eva,
                   score=0.8,
                   reason="小样本、信息不完整情况下的多因素关联度分析",
                   data_requirements={"min_samples": 3, "numeric": True},
                   tags=["小样本", "关联度", "灰色理论"],
                   solver_path="evaluation.grey_relational"),
        ModelEntry("CRITIC 权重法", eva,
                   score=0.78,
                   reason="考虑指标对比强度和冲突性的客观赋权",
                   data_requirements={"min_samples": 3, "numeric": True},
                   tags=["客观权重", "相关性"],
                   solver_path="evaluation.critic"),
        ModelEntry("VIKOR 折中排序法", eva,
                   score=0.75,
                   reason="群效用最大化和个体遗憾最小化的折中评价",
                   data_requirements={"min_samples": 2, "numeric": True},
                   tags=["折中", "群效用"],
                   solver_path="evaluation.vikor"),
    ])

    # ---- 分类/识别类 ----
    cls = "分类"
    entries.extend([
        ModelEntry("K-means 聚类", cls,
                   score=0.9,
                   reason="无标签数据的探索性聚类分析",
                   data_requirements={"min_samples": 10, "numeric": True},
                   tags=["无监督", "球形簇"],
                   solver_path="ml.kmeans"),
        ModelEntry("DBSCAN 密度聚类", cls,
                   score=0.82,
                   reason="任意形状簇且能识别噪声的聚类",
                   data_requirements={"min_samples": 10, "numeric": True},
                   tags=["无监督", "任意形状", "噪声"],
                   solver_path="ml.dbscan"),
        ModelEntry("层次聚类", cls,
                   score=0.8,
                   reason="需要看到聚类层次结构的分析",
                   data_requirements={"min_samples": 10, "numeric": True},
                   tags=["无监督", "层次", "树状图"],
                   solver_path="ml.hierarchical"),
        ModelEntry("SVM 支持向量机", cls,
                   score=0.88,
                   reason="高维小样本的有监督分类",
                   data_requirements={"min_samples": 20, "labeled": True},
                   tags=["有监督", "高维", "核方法"],
                   solver_path="ml.svm"),
        ModelEntry("随机森林分类", cls,
                   score=0.85,
                   reason="通用分类器，自动特征选择，抗过拟合",
                   data_requirements={"min_samples": 30, "labeled": True},
                   tags=["有监督", "集成", "特征重要度"],
                   solver_path="ml.random_forest_classifier"),
        ModelEntry("PCA 主成分分析", cls,
                   score=0.88,
                   reason="高维数据降维可视化，提取主成分",
                   data_requirements={"min_samples": 10, "numeric": True},
                   tags=["降维", "可视化", "特征提取"],
                   solver_path="ml.pca"),
    ])

    # ---- 微分方程类 ----
    de = "微分方程"
    entries.extend([
        ModelEntry("ODE 常微分方程 (scipy.integrate.odeint)", de,
                   score=0.9,
                   reason="描述随时间/空间连续变化的动力学系统",
                   data_requirements={"numeric": True},
                   tags=["连续", "动力系统"],
                   solver_path="differential.ode_solver"),
        ModelEntry("SIR 传染病模型", de,
                   score=0.85,
                   reason="经典流行病传播动力学模型",
                   data_requirements={},
                   tags=["传染病", "仓室模型"],
                   solver_path="differential.sir_model"),
        ModelEntry("Logistic 种群增长模型", de,
                   score=0.8,
                   reason="资源受限的种群增长规律",
                   data_requirements={"min_samples": 5},
                   tags=["种群", "增长", "阻滞"],
                   solver_path="differential.logistic"),
        ModelEntry("PDE 偏微分方程", de,
                   score=0.7,
                   reason="多维空间扩散/传播问题（有限差分/有限元）",
                   data_requirements={"numeric": True},
                   tags=["多维", "扩散", "数值解"],
                   solver_path="differential.pde_solver"),
    ])

    # ---- 图论/网络类 ----
    graph = "图论"
    entries.extend([
        ModelEntry("Dijkstra 最短路径", graph,
                   score=0.95,
                   reason="非负权图的单源最短路径问题",
                   data_requirements={"graph": True},
                   tags=["最短路径", "非负权"],
                   solver_path="graph.dijkstra"),
        ModelEntry("Floyd-Warshall 全源最短路", graph,
                   score=0.85,
                   reason="任意两点间最短路径（密集图）",
                   data_requirements={"graph": True},
                   tags=["全源最短路径"],
                   solver_path="graph.floyd"),
        ModelEntry("最大流 (Dinic / Edmonds-Karp)", graph,
                   score=0.88,
                   reason="网络流瓶颈分析、分配问题",
                   data_requirements={"graph": True},
                   tags=["最大流", "网络流"],
                   solver_path="graph.max_flow"),
        ModelEntry("最小生成树 (Kruskal / Prim)", graph,
                   score=0.82,
                   reason="最小成本连通所有节点的网络设计",
                   data_requirements={"graph": True},
                   tags=["生成树", "连通"],
                   solver_path="graph.min_spanning_tree"),
        ModelEntry("TSP/VRP 路径规划", graph,
                   score=0.78,
                   reason="旅行商/车辆路径的组合优化问题",
                   data_requirements={"locations": True},
                   tags=["组合优化", "路径", "NP-hard"],
                   solver_path="graph.tsp"),
        ModelEntry("A* 启发式搜索", graph,
                   score=0.8,
                   reason="有启发信息的最短路径搜索（如栅格地图）",
                   data_requirements={"graph": True, "heuristic": True},
                   tags=["启发式", "地图", "路径"],
                   solver_path="graph.astar"),
    ])

    # ---- 统计类 ----
    stat = "统计"
    entries.extend([
        ModelEntry("t 检验", stat,
                   score=0.9,
                   reason="两组均值差异的显著性检验",
                   data_requirements={"min_samples": 6, "numeric": True},
                   tags=["假设检验", "均值比较"],
                   solver_path="statistics.ttest"),
        ModelEntry("卡方检验", stat,
                   score=0.88,
                   reason="分类变量独立性/拟合优度检验",
                   data_requirements={"categorical": True},
                   tags=["假设检验", "独立性"],
                   solver_path="statistics.chi2_test"),
        ModelEntry("方差分析 ANOVA", stat,
                   score=0.85,
                   reason="多组均值差异显著性检验",
                   data_requirements={"min_samples": 10, "numeric": True},
                   tags=["假设检验", "多组比较"],
                   solver_path="statistics.anova"),
        ModelEntry("K-S 分布检验", stat,
                   score=0.75,
                   reason="检验数据是否服从特定分布",
                   data_requirements={"min_samples": 30, "numeric": True},
                   tags=["分布检验", "非参数"],
                   solver_path="statistics.ks_test"),
        ModelEntry("Pearson/Spearman 相关分析", stat,
                   score=0.92,
                   reason="变量间线性/单调相关关系的量化",
                   data_requirements={"min_samples": 10, "numeric": True},
                   tags=["相关性", "双变量"],
                   solver_path="statistics.correlation"),
    ])

    return entries


# =========================================================================
# 知识库查询引擎
# =========================================================================

class ModelKnowledgeBase:
    """数学模型知识库。

    管理题型与推荐模型之间的映射，支持内置基础和用户自定义扩展。

    Usage::

        kb = ModelKnowledgeBase()
        matches = kb.query(problem_type="预测", data_profiles={...})
        for m in matches:
            print(f"{m['model']}: {m['score']:.2f} — {m['reason']}")
    """

    def __init__(self):
        self._entries: list[ModelEntry] = _build_builtin_kb()
        self._custom_entries: list[ModelEntry] = []

    # ---- 查询 ---------------------------------------------------------------

    def query(
        self,
        problem_type: str,
        data_profiles: Optional[dict] = None,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> list[dict]:
        """根据题型和数据特征查询推荐模型。

        Args:
            problem_type: 题型（如 "预测", "优化"）
            data_profiles: 数据画像（用于调整分数）
            top_k: 返回前 K 个推荐
            min_score: 最低分数阈值

        Returns:
            list[dict]: 推荐模型列表，每项含 model / score / reason / tags / solver_path
        """
        all_entries = self._entries + self._custom_entries
        candidates = []

        for entry in all_entries:
            if entry.problem_type != problem_type:
                continue

            score = entry.score

            # 根据数据画像调整分数
            if data_profiles:
                score = self._adjust_score(entry, data_profiles)

            if score >= min_score:
                candidates.append({
                    "model": entry.model,
                    "score": round(score, 4),
                    "reason": entry.reason,
                    "tags": entry.tags,
                    "solver_path": entry.solver_path,
                    "data_requirements": entry.data_requirements,
                })

        # 按分数降序排列
        candidates.sort(key=lambda c: c["score"], reverse=True)
        return candidates[:top_k]

    def _adjust_score(self, entry: ModelEntry, data_profiles: dict) -> float:
        """根据实际数据特征调整模型推荐分数。"""
        score = entry.score
        req = entry.data_requirements

        if not req:
            return score

        # 取第一个数据表的画像做参考
        # （实际使用中应对每个表做匹配）
        ref_profile = next(iter(data_profiles.values()), {}) if data_profiles else {}

        # 样本量调整
        if "min_samples" in req:
            min_s = req["min_samples"]
            shape = ref_profile.get("shape", (0, 0))
            n_samples = shape[0] if isinstance(shape, tuple) else 0
            if n_samples < min_s:
                score -= 0.2  # 惩罚样本不足
            elif n_samples >= min_s * 3:
                score += 0.05  # 奖励充足样本

        if "max_samples" in req:
            max_s = req["max_samples"]
            shape = ref_profile.get("shape", (0, 0))
            n_samples = shape[0] if isinstance(shape, tuple) else 0
            if n_samples > max_s:
                score -= 0.3

        # 数值列检查
        if req.get("numeric"):
            num_cols = ref_profile.get("numeric_cols", [])
            if not num_cols:
                score -= 0.3  # 没有数值列，不适合

        # 标签检查
        if req.get("labeled"):
            # 假设：如果有 "label" 或 "target" 列则认为有标签
            cols = [c.lower() for c in ref_profile.get("columns", [])]
            if not any(lbl in cols for lbl in ("label", "target", "class", "y", "result")):
                score -= 0.2

        return max(0.1, min(1.0, score))

    # ---- 知识库管理 ---------------------------------------------------------

    def add_rule(
        self,
        model: str,
        problem_type: str,
        score: float = 0.7,
        reason: str = "",
        data_requirements: Optional[dict] = None,
        tags: Optional[list[str]] = None,
        solver_path: str = "",
    ) -> None:
        """添加用户自定义模型规则。

        Args:
            model: 模型名称
            problem_type: 匹配的题型
            score: 基础推荐分数
            reason: 推荐理由
            data_requirements: 数据要求
            tags: 标签列表
            solver_path: 求解器路径
        """
        entry = ModelEntry(
            model=model,
            problem_type=problem_type,
            score=score,
            reason=reason,
            data_requirements=data_requirements or {},
            tags=tags or [],
            solver_path=solver_path,
        )
        self._custom_entries.append(entry)

    def remove_rule(self, model: str, problem_type: str) -> bool:
        """移除用户自定义规则。"""
        for i, e in enumerate(self._custom_entries):
            if e.model == model and e.problem_type == problem_type:
                self._custom_entries.pop(i)
                return True
        return False

    def list_problem_types(self) -> list[str]:
        """列出所有支持的题型。"""
        types = set()
        for e in self._entries + self._custom_entries:
            types.add(e.problem_type)
        return sorted(types)

    def export_rules(self) -> list[dict]:
        """导出所有规则（含内置和自定义）。"""
        rules = []
        for e in self._entries + self._custom_entries:
            rules.append({
                "model": e.model,
                "problem_type": e.problem_type,
                "score": e.score,
                "reason": e.reason,
                "data_requirements": e.data_requirements,
                "tags": e.tags,
                "solver_path": e.solver_path,
            })
        return rules

    def reset(self) -> None:
        """重置为仅内置规则。"""
        self._custom_entries.clear()


# ---- 单例 ----

_global_kb: Optional[ModelKnowledgeBase] = None


def get_knowledge_base() -> ModelKnowledgeBase:
    """获取全局知识库单例。"""
    global _global_kb
    if _global_kb is None:
        _global_kb = ModelKnowledgeBase()
    return _global_kb
