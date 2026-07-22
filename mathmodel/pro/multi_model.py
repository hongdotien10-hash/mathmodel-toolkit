"""Pro: 多模型对比选优
每子问题跑2-3种方法，AI综合比较选最优
"""

import json
import urllib.request
import numpy as np
import pandas as pd
from typing import Optional


class ModelContest:
    """多模型竞赛 — 跑候选方法，AI对比选最优"""

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.api_key = api_key
        self.model = model

    def _call_ai(self, system: str, user: str) -> str:
        body = json.dumps({
            "model": self.model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "temperature": 0.3, "max_tokens": 4096,
        }).encode()
        req = urllib.request.Request(
            "https://api.deepseek.com/v1/chat/completions", data=body,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self.api_key}"}, method="POST")
        for _ in range(3):
            try:
                with urllib.request.urlopen(req, timeout=90) as r:
                    return json.loads(r.read())["choices"][0]["message"]["content"]
            except Exception:
                import time; time.sleep(2)
        return "{}"

    # ================================================================
    # 主入口：对一个子问题跑多模型对比
    # ================================================================

    def contest(self, sub_problem: dict, data_files: dict) -> dict:
        """对子问题跑模型竞赛

        Args:
            sub_problem: {"id":1, "type":"预测", "title":"..."}
            data_files: {"附件1": DataFrame, ...}

        Returns:
            {"winner": "best model", "all_results": [...], "comparison": {...}, "ai_analysis": "..."}
        """
        ptype = sub_problem.get("type", "综合")
        candidates = self._get_candidates(ptype)
        results = []

        for c in candidates:
            try:
                r = self._run_candidate(c, sub_problem, data_files)
                results.append({"model": c["name"], "result": r, "source": c["source"]})
                print(f"     [Contest] {c['name']}: {r.get('metric_name','?')}={r.get('metric_value','?')}")
            except Exception as e:
                print(f"     [Contest] {c['name']}: FAILED ({e})")
                results.append({"model": c["name"], "result": {"error": str(e)}, "source": c["source"]})

        # AI 选最优
        comparison = self._ai_compare(ptype, sub_problem.get("title", ""), results)
        winner = comparison.get("winner", candidates[0]["name"])

        return {
            "winner": winner,
            "candidates": results,
            "comparison": comparison,
            "ai_reason": comparison.get("reason", ""),
        }

    # ================================================================
    # 候选模型池
    # ================================================================

    def _get_candidates(self, ptype: str) -> list[dict]:
        """返回该题型的候选模型列表"""
        pool = {
            "评价": [
                {"name": "熵权-TOPSIS", "source": "local",
                 "metric": "top2_gap", "desc": "TOP2得分差距,越大区分度越好"},
                {"name": "AHP层次分析", "source": "local",
                 "metric": "consistency", "desc": "CR一致性比率,<0.1为通过"},
                {"name": "灰色关联分析", "source": "local",
                 "metric": "resolution", "desc": "关联度极差,越大区分度越好"},
            ],
            "预测": [
                {"name": "GM(1,1)灰色预测", "source": "local",
                 "metric": "mape", "desc": "MAPE,越小越好"},
                {"name": "三次指数平滑", "source": "statsmodels",
                 "metric": "mape", "desc": "MAPE,越小越好"},
                {"name": "线性回归", "source": "local",
                 "metric": "r_squared", "desc": "R²,越大拟合越好"},
            ],
            "优化": [
                {"name": "0-1整数规划", "source": "PuLP",
                 "metric": "optimality_gap", "desc": "对偶间隙,0=最优"},
                {"name": "贪心算法", "source": "local",
                 "metric": "ratio", "desc": "目标值/预算利用率的综合"},
                {"name": "线性松弛+修复", "source": "local",
                 "metric": "gap", "desc": "松弛解与整数解差距"},
            ],
            "统计": [
                {"name": "Pearson相关", "source": "local",
                 "metric": "max_corr", "desc": "最强相关系数"},
                {"name": "Spearman秩相关", "source": "local",
                 "metric": "max_corr", "desc": "最强秩相关系数"},
                {"name": "PCA主成分", "source": "sklearn",
                 "metric": "explained_var", "desc": "前2主成分累积方差"},
            ],
        }
        return pool.get(ptype, pool["统计"])

    # ================================================================
    # 运行候选模型
    # ================================================================

    def _run_candidate(self, candidate: dict, sp: dict, data_files: dict) -> dict:
        name = candidate["name"]
        ptype = sp.get("type", "")

        # Find data
        df = self._get_df(data_files, ptype)
        if df is None:
            return {"error": "no suitable data"}

        numeric = df.select_dtypes(include=np.number)

        if "TOPSIS" in name and ptype == "评价":
            return self._run_topsis(numeric, df)
        elif "AHP" in name and ptype == "评价":
            return self._run_ahp(numeric)
        elif "灰色关联" in name and ptype == "评价":
            return self._run_grey_relational(numeric, df)

        elif "GM(1,1)" in name and ptype == "预测":
            return self._run_gm11(numeric, df)
        elif "指数平滑" in name and ptype == "预测":
            return self._run_hw(numeric, df)
        elif "线性回归" in name and ptype == "预测":
            return self._run_lr(numeric, df)

        elif "整数规划" in name and ptype == "优化":
            return self._run_ip(numeric, df)
        elif "贪心" in name and ptype == "优化":
            return self._run_greedy(numeric, df)
        elif "松弛" in name and ptype == "优化":
            return self._run_relaxed(numeric, df)

        elif "Pearson" in name and ptype == "统计":
            return self._run_pearson(numeric)
        elif "Spearman" in name and ptype == "统计":
            return self._run_spearman(numeric)
        elif "PCA" in name and ptype == "统计":
            return self._run_pca(numeric)

        return {"error": f"unknown candidate: {name}"}

    def _get_df(self, data_files, ptype):
        for k, v in data_files.items():
            if v.select_dtypes(include=np.number).shape[1] >= 2:
                return v
        return list(data_files.values())[0] if data_files else None

    # ---- Evaluation methods ----
    def _run_topsis(self, numeric, df):
        from mathmodel.models.evaluation import EvaluationSolver
        ev = EvaluationSolver()
        matrix = numeric.values.astype(float)
        ew = ev.entropy_weight(matrix)
        res = ev.topsis(matrix, weights=ew["weights"], impacts=[1]*matrix.shape[1])
        scores = res["scores"]
        sorted_s = sorted(scores, reverse=True)
        top2_gap = (sorted_s[0] - sorted_s[1]) if len(sorted_s) > 1 else 0
        labels = df.iloc[:, 0].tolist() if not pd.api.types.is_numeric_dtype(df.iloc[:,0]) else [f"方案{i+1}" for i in range(len(df))]
        return {"metric_name": "Top2区分度", "metric_value": round(top2_gap, 4),
                "scores": [round(float(s),4) for s in scores],
                "best": labels[int(np.argmax(scores))], "ranking": " > ".join(
                    str(labels[i]) for i in np.argsort([-s for s in scores]))}

    def _run_ahp(self, numeric):
        from mathmodel.models.evaluation import EvaluationSolver
        ev = EvaluationSolver()
        n = min(numeric.shape[1], 5)
        mat = np.ones((n, n))
        for i in range(n):
            for j in range(i+1, n):
                ratio = numeric.iloc[:, i].mean() / max(numeric.iloc[:, j].mean(), 1e-10)
                mat[i][j] = min(max(ratio, 0.1), 10)
                mat[j][i] = 1/mat[i][j]
        res = ev.ahp(mat)
        return {"metric_name": "CR一致性", "metric_value": round(res["cr"], 4),
                "weights": [round(float(w),4) for w in res["weights"]],
                "consistent": res["cr"] < 0.1}

    def _run_grey_relational(self, numeric, df):
        from mathmodel.models.evaluation import EvaluationSolver
        ev = EvaluationSolver()
        res = ev.grey_relational(numeric.values.astype(float))
        degrees = res["degrees"]
        resolution = max(degrees) - min(degrees) if len(degrees) > 1 else 0
        labels = df.iloc[:,0].tolist() if not pd.api.types.is_numeric_dtype(df.iloc[:,0]) else [f"G{i+1}" for i in range(len(df))]
        return {"metric_name": "分辨率", "metric_value": round(float(resolution), 4),
                "degrees": [round(float(d),4) for d in degrees], "best": labels[int(np.argmax(degrees))]}

    # ---- Prediction methods ----
    def _run_gm11(self, numeric, df):
        from mathmodel.models.statistics import StatsSolver
        ss = StatsSolver()
        data = numeric.iloc[:,0].dropna().tolist()
        if len(data) < 4: return {"error": "need 4+ points"}
        pred = ss.grey_forecast(data, forecast_steps=3)
        return {"metric_name": "MAPE(%)", "metric_value": round(pred["mape"], 2),
                "forecast": [round(v,2) for v in pred["forecast"]],
                "fitted": [round(v,2) for v in pred["fitted"]],
                "grade": pred["grade"]}

    def _run_hw(self, numeric, df):
        data = numeric.iloc[:,0].dropna().tolist()
        if len(data) < 8: return {"error": "need 8+ points for HW"}
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            model = ExponentialSmoothing(data, trend="add", seasonal=None)
            fitted = model.fit()
            forecast = fitted.forecast(3)
            pred_vals = fitted.fittedvalues.tolist()
            mape = np.mean(np.abs((np.array(data) - np.array(pred_vals))/np.array(data)))*100
            return {"metric_name": "MAPE(%)", "metric_value": round(mape, 2),
                    "forecast": [round(float(v),2) for v in forecast]}
        except Exception as e:
            return {"error": str(e)}

    def _run_lr(self, numeric, df):
        nc = numeric.shape[1]
        if nc < 2:
            x = np.arange(len(numeric)).reshape(-1,1)
            y = numeric.iloc[:,0].values
        else:
            x = numeric.iloc[:,1:].values
            y = numeric.iloc[:,0].values
        from numpy.linalg import lstsq
        X = np.column_stack([np.ones(len(x)), x])
        beta, residuals, rank, sv = lstsq(X, y, rcond=None)
        y_pred = X @ beta
        ss_res = np.sum((y - y_pred)**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0
        return {"metric_name": "R²", "metric_value": round(float(r2), 4),
                "coefficients": [round(float(b),4) for b in beta]}

    # ---- Optimization methods ----
    def _run_ip(self, numeric, df):
        from mathmodel.models.optimization import OptimizationSolver
        costs = numeric.iloc[:,1].values.astype(float).tolist() if numeric.shape[1] > 1 else numeric.iloc[:,0].tolist()
        benefits = numeric.iloc[:,2].values.astype(float).tolist() if numeric.shape[1] > 2 else numeric.iloc[:,0].tolist()
        budget = sum(costs) * 0.6
        opt = OptimizationSolver()
        c = [-b for b in benefits]
        try:
            r = opt.integer_program(c=c, A_ub=[costs], b_ub=[budget], bounds=(0,1), binary=True)
            if r.success:
                sel = [int(v > 0.5) for v in r.x]
                total_c = sum(costs[i] for i, v in enumerate(sel) if v)
                total_b = sum(benefits[i] for i, v in enumerate(sel) if v)
                return {"metric_name": "目标值", "metric_value": round(total_b, 1),
                        "selection": [int(v) for v in sel], "cost": round(total_c, 1),
                        "benefit": round(total_b, 1)}
        except Exception:
            pass
        return {"error": "IP solver failed"}

    def _run_greedy(self, numeric, df):
        costs = numeric.iloc[:,1].values.astype(float).tolist() if numeric.shape[1] > 1 else [1]*len(numeric)
        benefits = numeric.iloc[:,2].values.astype(float).tolist() if numeric.shape[1] > 2 else numeric.iloc[:,0].tolist()
        budget = sum(costs) * 0.6
        ratios = [(benefits[i]/costs[i] if costs[i] > 0 else 0, i) for i in range(len(costs))]
        ratios.sort(key=lambda x: -x[0])
        selected = []; remaining = budget
        for _, idx in ratios:
            if costs[idx] <= remaining:
                selected.append(idx); remaining -= costs[idx]
        total_b = sum(benefits[i] for i in selected)
        total_c = sum(costs[i] for i in selected)
        return {"metric_name": "目标值", "metric_value": round(total_b, 1),
                "selection": selected, "cost": round(total_c, 1), "benefit": round(total_b, 1)}

    def _run_relaxed(self, numeric, df):
        costs = numeric.iloc[:,1].values.astype(float).tolist() if numeric.shape[1] > 1 else [1]*len(numeric)
        benefits = numeric.iloc[:,2].values.astype(float).tolist() if numeric.shape[1] > 2 else numeric.iloc[:,0].tolist()
        budget = sum(costs) * 0.6
        ratios = sorted([(benefits[i]/(costs[i] or 1), i) for i in range(len(costs))], key=lambda x: -x[0])
        selected = []; remaining = budget; used = [0.0]*len(costs)
        for r, idx in ratios:
            if costs[idx] <= remaining:
                selected.append(idx); remaining -= costs[idx]; used[idx] = 1.0
            elif remaining > 0:
                frac = remaining / costs[idx]
                selected.append(idx); used[idx] = frac; remaining = 0; break
        total_b = sum(benefits[i]*used[i] for i in range(len(costs)))
        return {"metric_name": "松驰目标值", "metric_value": round(total_b, 1),
                "solution": [round(u,3) for u in used], "integer_gap": round(total_b - sum(benefits[i] for i in selected), 2)}

    # ---- Statistics methods ----
    def _run_pearson(self, numeric):
        corr = numeric.corr()
        vals = []
        cols = numeric.columns.tolist()
        for i in range(len(cols)):
            for j in range(i+1, len(cols)):
                vals.append(abs(corr.iloc[i, j]))
        max_corr = max(vals) if vals else 0
        return {"metric_name": "最强|r|", "metric_value": round(float(max_corr), 4),
                "pairs": [{"pair":(cols[i],cols[j]), "r":round(float(corr.iloc[i,j]),4)}
                          for i in range(len(cols)) for j in range(i+1,len(cols))
                          if abs(corr.iloc[i,j]) > 0.3][:5]}

    def _run_spearman(self, numeric):
        from scipy import stats as sp_stats
        corr, _ = sp_stats.spearmanr(numeric)
        corr = pd.DataFrame(corr, index=numeric.columns, columns=numeric.columns)
        vals = []
        for i in range(len(numeric.columns)):
            for j in range(i+1, len(numeric.columns)):
                vals.append(abs(corr.iloc[i, j]))
        max_corr = max(vals) if vals else 0
        return {"metric_name": "最强|ρ|", "metric_value": round(float(max_corr), 4)}

    def _run_pca(self, numeric):
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import StandardScaler
        if numeric.shape[1] < 2:
            return {"error": "need 2+ columns for PCA"}
        X = StandardScaler().fit_transform(numeric.fillna(0))
        pca = PCA(n_components=min(5, numeric.shape[1]))
        pca.fit(X)
        explained = float(np.cumsum(pca.explained_variance_ratio_)[:2][-1])
        return {"metric_name": "累积方差(前2)", "metric_value": round(explained, 4)}

    # ================================================================
    # AI 对比选优
    # ================================================================

    def _ai_compare(self, ptype: str, problem: str, results: list[dict]) -> dict:
        system = "你是数学建模竞赛评委。对比多个模型的结果，选出最优并说明理由。返回严格JSON。"
        summary = [{"model": r["model"], "metric_name": r["result"].get("metric_name",""),
                    "metric_value": r["result"].get("metric_value",""),
                    "other": {k:v for k,v in r["result"].items()
                              if k not in ("metric_name","metric_value") and isinstance(v,(int,float,str))}}
                   for r in results]
        user = f"题型: {ptype}\n问题: {problem[:300]}\n候选结果:\n{json.dumps(summary, ensure_ascii=False)[:3000]}\n\n返回JSON:{{\"winner\":\"模型名\",\"reason\":\"为什么选它\",\"ranking\":[\"按优劣排序\"],\"analysis\":\"对比总结\"}}"

        try:
            text = self._call_ai(system, user)
            text = text.strip()
            if "```" in text: text = text.split("```")[1].split("```")[0]
            start = text.find("{"); end = text.rfind("}")+1
            return json.loads(text[start:end]) if start >= 0 else {"winner": results[0]["model"]}
        except Exception:
            return {"winner": results[0]["model"] if results else "N/A", "reason": "auto selected"}
