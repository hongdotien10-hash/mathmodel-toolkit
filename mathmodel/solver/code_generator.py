"""求解代码生成器。

根据模型推荐结果，自动生成可执行的求解代码。
"""

from pathlib import Path
from typing import Optional


# ---- 代码模板 ---------------------------------------------------------------

_TEMPLATES = {
    "optimization.linear_programming": '''"""
子问题 {sub_id}: {model_name}
线性规划求解
"""
import numpy as np
from scipy.optimize import linprog

# 目标函数系数
c = {c!r}

# 不等式约束
A_ub = {A_ub!r}
b_ub = {b_ub!r}

# 边界
bounds = {bounds!r}

# 求解
result = linprog(c=c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")

print("Status:", result.message)
print("Optimal solution:", result.x)
print("Optimal value:", result.fun)
''',

    "statistics.grey_forecast": '''"""
子问题 {sub_id}: {model_name}
灰色预测 GM(1,1)
"""
import numpy as np

data = np.array({data!r}, dtype=float)

# GM(1,1) 模型
x1 = np.cumsum(data)
z = (x1[:-1] + x1[1:]) / 2.0
B = np.column_stack([-z, np.ones(len(data) - 1)])
Y = data[1:]
params = np.linalg.inv(B.T @ B) @ B.T @ Y
a, b = params[0], params[1]

def predict(k):
    return (data[0] - b/a) * np.exp(-a * k) + b/a

# 预测未来 N 步
N = {forecast_steps}
forecast_ago = [predict(k) for k in range(len(data) + N)]
fitted = np.diff(forecast_ago, prepend=0)
fitted[0] = data[0]
forecast = fitted[-N:]

print("发展系数 a:", a)
print("灰色作用量 b:", b)
print("拟合值:", fitted[:len(data)])
print("预测值:", forecast)
''',

    "evaluation.topsis": '''"""
子问题 {sub_id}: {model_name}
TOPSIS 综合评价
"""
import numpy as np

# 决策矩阵 (m 方案 × n 指标)
matrix = np.array({matrix!r}, dtype=float)
weights = np.array({weights!r}, dtype=float)
impacts = {impacts!r}  # 1=正向, -1=负向

# 归一化
norm = np.sqrt((matrix ** 2).sum(axis=0))
normalized = matrix / norm

# 加权
weighted = normalized * weights

# 正负理想解
ideal_best = np.array([weighted[:, j].max() if impacts[j] > 0 else weighted[:, j].min()
                       for j in range(len(impacts))])
ideal_worst = np.array([weighted[:, j].min() if impacts[j] > 0 else weighted[:, j].max()
                        for j in range(len(impacts))])

# 距离
d_plus = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
d_minus = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

# 相对贴近度
scores = d_minus / (d_plus + d_minus)
rank = scores.argsort()[::-1].argsort() + 1

print("TOPSIS 得分:", scores)
print("排名:", rank)
''',
}


class CodeGenerator:
    """求解代码自动生成器。

    根据模型推荐方案，生成可独立运行的 Python 求解脚本。

    Usage::

        cg = CodeGenerator()
        script = cg.generate(
            solver_path="statistics.grey_forecast",
            sub_id=1,
            model_name="灰色预测 GM(1,1)",
            params={"data": [10, 15, 20, 30], "forecast_steps": 3},
        )
        cg.save(script, "./output/problem1_solve.py")
    """

    def __init__(self):
        self._templates = dict(_TEMPLATES)

    def register_template(self, solver_path: str, template: str) -> None:
        """注册自定义代码模板。

        Args:
            solver_path: 求解器路径（如 "optimization.linear_programming"）
            template: Python 代码模板（使用 {key} 作为占位符）
        """
        self._templates[solver_path] = template

    def generate(
        self,
        solver_path: str,
        sub_id: int,
        model_name: str,
        params: Optional[dict] = None,
    ) -> str:
        """生成求解代码。

        Args:
            solver_path: 求解器路径
            sub_id: 子问题编号
            model_name: 模型名称
            params: 模板参数

        Returns:
            str: Python 源代码
        """
        params = params or {}
        template_params = {
            "sub_id": sub_id,
            "model_name": model_name,
            "forecast_steps": params.get("forecast_steps", 5),
            "data": params.get("data", [1, 2, 3, 4, 5]),
            "c": params.get("c", [1, 1]),
            "A_ub": params.get("A_ub", [[1, 1]]),
            "b_ub": params.get("b_ub", [10]),
            "bounds": params.get("bounds", [(0, None)] * 2),
            "matrix": params.get("matrix", [[1, 2], [3, 4]]),
            "weights": params.get("weights", [0.5, 0.5]),
            "impacts": params.get("impacts", [1, 1]),
            **params,
        }

        template = self._templates.get(solver_path)
        if template:
            return template.format(**template_params)

        # 通用模板
        return f'''"""
子问题 {sub_id}: {model_name}
自动求解脚本

求解器: {solver_path}
"""
import numpy as np
import json

# TODO: 实现 {model_name} 的求解逻辑
# 参数: {params}

print("求解完成 (占位)")
result = {{"status": "placeholder", "model": "{model_name}"}}
with open("sub{sub_id}_result.json", "w") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
'''

    def generate_all(
        self,
        recommendations: list[dict],
    ) -> dict[int, str]:
        """为所有子问题批量生成代码。

        Args:
            recommendations: 推荐方案列表

        Returns:
            dict: {sub_id: source_code}
        """
        codes = {}
        for plan in recommendations:
            for sp in plan.get("sub_problems", []):
                sid = sp["id"]
                codes[sid] = self.generate(
                    solver_path=sp.get("solver_path", ""),
                    sub_id=sid,
                    model_name=sp.get("model", "未指定"),
                    params=sp.get("solve_params"),
                )
        return codes

    def save(self, code: str, path: str | Path) -> None:
        """保存代码到文件。"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(code, encoding="utf-8")
