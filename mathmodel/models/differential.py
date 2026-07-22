"""微分方程求解器。

提供 ODE 数值求解、SIR 传染病模型、Logistic 模型等。
"""

import numpy as np
from typing import Callable, Optional


class DiffEqSolver:
    """微分方程求解器。

    Usage::

        des = DiffEqSolver()

        # ODE 求解
        def dydt(t, y): return -0.5 * y
        t, y = des.solve_ode(dydt, y0=[10], t_span=[0, 10])

        # SIR 模型
        result = des.sir_model(population=10000, beta=0.3, gamma=0.1)
    """

    def solve_ode(
        self,
        f: Callable,
        y0: list[float],
        t_span: list[float],
        t_eval: Optional[np.ndarray] = None,
        method: str = "RK45",
        **kwargs,
    ) -> dict:
        """求解常微分方程初值问题。

        dy/dt = f(t, y), y(t0) = y0

        Args:
            f: 微分方程函数 f(t, y) -> dy/dt
            y0: 初始条件
            t_span: [t0, t_end]
            t_eval: 输出时间点，None 时自动生成等间距点
            method: RK45 / LSODA / DOP853
            **kwargs: 传递给 solve_ivp 的参数

        Returns:
            dict: {"t": 时间点, "y": 解矩阵 (len(t) × len(y0)), "success": bool, "message": str}
        """
        from scipy.integrate import solve_ivp

        if t_eval is None:
            t_eval = np.linspace(t_span[0], t_span[1], 100)

        sol = solve_ivp(f, t_span, y0, method=method, t_eval=t_eval, **kwargs)

        return {
            "t": sol.t,
            "y": sol.y.T,
            "success": sol.success,
            "message": sol.message,
            "nfev": sol.nfev,
        }

    def sir_model(
        self,
        population: float = 10000,
        beta: float = 0.3,
        gamma: float = 0.1,
        initial_infected: float = 1,
        initial_recovered: float = 0,
        days: int = 100,
    ) -> dict:
        """SIR 传染病模型。

        dS/dt = -beta * S * I / N
        dI/dt =  beta * S * I / N - gamma * I
        dR/dt =  gamma * I

        Args:
            population: 总人口 N
            beta: 传染率
            gamma: 恢复率 (1/平均病程)
            initial_infected: 初始感染者
            initial_recovered: 初始恢复者
            days: 模拟天数

        Returns:
            dict: {"t": 时间, "S": 易感者, "I": 感染者, "R": 恢复者, "R0": 基本再生数}
        """
        N = population
        S0 = N - initial_infected - initial_recovered
        I0 = initial_infected
        R0_init = initial_recovered

        def sir(t, y):
            S, I, R = y
            dS = -beta * S * I / N
            dI = beta * S * I / N - gamma * I
            dR = gamma * I
            return [dS, dI, dR]

        sol = self.solve_ode(sir, [S0, I0, R0_init], [0, days])

        y = sol["y"]
        return {
            "t": sol["t"].tolist(),
            "S": y[:, 0].tolist(),
            "I": y[:, 1].tolist(),
            "R": y[:, 2].tolist(),
            "R0": round(beta / gamma, 4),
            "peak_infected": round(float(y[:, 1].max()), 1),
            "peak_day": int(sol["t"][np.argmax(y[:, 1])]),
        }

    def logistic_model(
        self,
        t_data: list[float],
        y_data: list[float],
        forecast_steps: int = 5,
    ) -> dict:
        """Logistic 种群增长模型拟合。

        y = K / (1 + (K/y0 - 1) * exp(-r * t))

        Args:
            t_data: 时间点
            y_data: 观测值
            forecast_steps: 预测步数

        Returns:
            dict: {"K": 承载力, "r": 增长率, "y0": 初始值, "fitted": 拟合值, "forecast": 预测值}
        """
        from scipy.optimize import curve_fit

        def logistic(t, K, r, y0):
            return K / (1 + (K / y0 - 1) * np.exp(-r * t))

        t_arr = np.array(t_data, dtype=float)
        y_arr = np.array(y_data, dtype=float)

        # 参数初始猜测
        p0 = [y_arr.max() * 1.5, 0.5, y_arr[0]]

        try:
            popt, _ = curve_fit(logistic, t_arr, y_arr, p0=p0, maxfev=5000)
            K, r, y0 = popt
        except Exception:
            K, r, y0 = y_arr.max() * 1.2, 0.3, y_arr[0]

        fitted = logistic(t_arr, K, r, y0)
        t_forecast = np.arange(len(t_arr), len(t_arr) + forecast_steps)
        forecast = logistic(t_forecast, K, r, y0)

        return {
            "K": float(K),
            "r": float(r),
            "y0": float(y0),
            "fitted": fitted.tolist(),
            "forecast": forecast.tolist(),
            "t_forecast": t_forecast.tolist(),
        }
