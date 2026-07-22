"""
MathModel Toolkit — 一键启动（支持大规模数据）
==============================================
自动识别题目 → 分析数据结构 → 聚合+采样 → 建模求解 → 生成论文
"""

import sys, json, time, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')

sys.path.insert(0, str(Path(__file__).parent))

from mathmodel.utils import set_seed, Timer
from mathmodel.utils.helpers import safe_call, PhaseGuard
from mathmodel.analyzer import ProblemClassifier, ModelKnowledgeBase
from mathmodel.models import EvaluationSolver, StatsSolver, OptimizationSolver, MLSolver
from mathmodel.sensitivity import SensitivityAnalyzer
from mathmodel.visualization import Plotter, set_style, get_colors
from mathmodel.paper.word_writer import generate_paper
from mathmodel.paper.latex_writer import generate_latex_paper
from mathmodel.preprocessing import MissingHandler, OutlierDetector, Normalizer
from mathmodel.pipeline.rich_progress import PhaseTracker, print_header, print_section, print_result_summary

set_seed(42)

PROBLEMS_DIR = Path(__file__).parent / "problems"
OUTPUT_DIR = Path(__file__).parent / "output"


def main():
    # ================================================================
    # Step 1: Scan & Load
    # ================================================================
    problem_dirs = sorted([d for d in PROBLEMS_DIR.iterdir()
                           if d.is_dir() and not d.name.startswith('.')])
    if not problem_dirs:
        print("ERROR: No problems found in problems/")
        sys.exit(1)

    selected = problem_dirs[0]
    if len(problem_dirs) > 1:
        print(f"Found {len(problem_dirs)} problems:")
        for i, d in enumerate(problem_dirs):
            print(f"  [{i+1}] {d.name}")
        try:
            selected = problem_dirs[int(input("Select: ") or "1") - 1]
        except (ValueError, EOFError):
            pass

    out_dir = OUTPUT_DIR / selected.name
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # ---- Rich progress tracker ----
    tracker = PhaseTracker(title=f"MathModel Toolkit — {selected.name}")

    print_header(f"MathModel Toolkit — {selected.name}")

    # ---- Read problem text ----
    problem_text = ""
    for f in sorted(selected.iterdir()):
        if f.suffix == '.txt':
            problem_text = f.read_text(encoding='utf-8')
            print(f"[doc] {f.name} ({len(problem_text)} chars)")
        elif f.suffix == '.pdf':
            try:
                import pdfplumber
                with pdfplumber.open(str(f)) as pdf:
                    parts = [p.extract_text() or "" for p in pdf.pages]
                problem_text = '\n\n'.join(parts)
                print(f"[doc] {f.name} ({len(problem_text)} chars, {len(pdf.pages)}p)")
            except Exception as e:
                print(f"[doc] {f.name} — PDF failed: {e}")

    # ---- Smart data loading: small files full, large files sampled ----
    data_files = {}
    data_profiles = {}

    for f in sorted(selected.iterdir()):
        suffix = f.suffix.lower()
        if suffix in ('.xlsx', '.xls', '.csv'):
            try:
                # Always read sample first (fast)
                if suffix == '.csv':
                    df_sample = pd.read_csv(f, nrows=500)
                else:
                    df_sample = pd.read_excel(f, nrows=500)

                # Estimate size
                est_rows = int(f.stat().st_size / 200)  # ~200 bytes per row average
                profile = {
                    'path': str(f),
                    'name': f.stem,
                    'shape': (est_rows, len(df_sample.columns)),
                    'columns': list(df_sample.columns),
                    'dtypes': {c: str(t) for c, t in df_sample.dtypes.items()},
                    'size_category': 'large' if est_rows > 50000 else
                                     'medium' if est_rows > 1000 else 'small',
                    'sample': df_sample,
                }

                if profile['size_category'] == 'large':
                    # Don't load full data — keep sample + metadata for lazy loading
                    print(f"[data] {f.name} ~{est_rows} rows (LARGE — lazy load)")
                    # Store sample as the working data, solvers can request full load
                    data_files[f.stem] = df_sample
                elif profile['size_category'] == 'medium':
                    print(f"[data] {f.name} ~{est_rows} rows (medium)")
                    data_files[f.stem] = pd.read_excel(f) if suffix != '.csv' else pd.read_csv(f)
                else:
                    print(f"[data] {f.name} ~{est_rows} rows (small)")
                    data_files[f.stem] = pd.read_excel(f) if suffix != '.csv' else pd.read_csv(f)

                data_profiles[f.stem] = profile

            except Exception as e:
                print(f"[data] {f.name} — FAILED: {e}")

    if not problem_text:
        print("\nERROR: No problem text found. Add a .txt or .pdf file.")
        sys.exit(1)

    global _data_profiles_global
    _data_profiles_global = data_profiles

    print()

    # ================================================================
    # Step 2: Analyze & Classify
    # ================================================================
    print_section("Phase 1: Problem Analysis")

    # Split sub-problems
    lines = problem_text.split('\n')
    sub_raw = []
    for i, line in enumerate(lines):
        line = line.strip()
        if not line: continue
        if '问题' in line and any(c in line for c in '123456789一二三四五六七八九'):
            ctx = line
            for j in range(i+1, min(i+8, len(lines))):
                if '问题' in lines[j] and any(c in lines[j] for c in '123456789'):
                    break
                ctx += ' ' + lines[j].strip()
            sub_raw.append({"id": len(sub_raw)+1, "text": ctx[:500]})
            if len(sub_raw) >= 6: break

    if not sub_raw:
        sub_raw = [{"id": 1, "text": problem_text[:500]}]

    # Try API first, fall back to rule-based
    sub_problems = _analyze_with_api_or_rules(sub_raw, data_profiles, problem_text)

    for sp in sub_problems:
        print(f"  Q{sp['id']}: [{sp['type']}] → {sp['model']} ({sp['score']:.0%}) [{sp.get('source','rule')}]")

    print()

    # ================================================================
    # Step 2: AI Data Cleaning
    # ================================================================
    print_section("Phase 1.5: AI Data Cleaning")

    try:
        from api.config import APIConfig
        cfg_c = APIConfig()
        if cfg_c.is_configured:
            from mathmodel.pipeline.smart_orchestrator import AIDrivenPipeline
            ai_clean = AIDrivenPipeline(api_key=cfg_c.api_key, model=cfg_c.model)
            clean_plan = ai_clean.clean_data_with_ai(problem_text, data_profiles)

            # Execute cleaning on actual data (with fuzzy file matching)
            import re
            cleaned_count = 0
            for issue in clean_plan.get("issues_found", []):
                if issue.get("severity") in ("critical", "high"):
                    fname = issue.get("file", "")
                    col = issue.get("column", "")
                    action = issue.get("fix_action", "")
                    params = issue.get("fix_params", {})

                    # Fuzzy match file name
                    fn_num = re.search(r'(\d+)', fname)
                    fn_num = fn_num.group(1) if fn_num else ''
                    matched_key = fname if fname in data_files else None
                    if not matched_key:
                        for k in data_files:
                            k_num = re.search(r'(\d+)', k)
                            if fn_num and k_num and fn_num == k_num.group(1):
                                matched_key = k
                                break

                    if matched_key:
                        df = data_files[matched_key]
                        try:
                            if action == "convert_type" and col in df.columns:
                                df[col] = pd.to_numeric(df[col], errors='coerce')
                                cleaned_count += 1
                                print(f"  [Clean] {fname}/{col}: converted to numeric")
                            elif action == "fill_value" and col in df.columns:
                                method = params.get("method", "median")
                                if method == "median" and df[col].dtype in ('int64', 'float64'):
                                    df[col] = df[col].fillna(df[col].median())
                                elif method == "mode":
                                    m = df[col].mode()
                                    if not m.empty: df[col] = df[col].fillna(m[0])
                                cleaned_count += 1
                                print(f"  [Clean] {fname}/{col}: filled missing ({method})")
                            elif action == "remove_outliers" and col in df.columns:
                                threshold = params.get("threshold", 3)
                                if df[col].dtype in ('int64', 'float64'):
                                    z = np.abs((df[col] - df[col].mean()) / df[col].std())
                                    n_before = len(df)
                                    df = df[z < threshold]
                                    data_files[fname] = df
                                    cleaned_count += 1
                                    print(f"  [Clean] {fname}/{col}: removed {n_before - len(df)} outliers ({len(df)} kept)")
                            elif action == "drop_rows" and col in df.columns:
                                n_before = len(df)
                                df = df[df[col].notna()]
                                data_files[fname] = df
                                cleaned_count += 1
                                print(f"  [Clean] {fname}/{col}: dropped {n_before - len(df)} rows with null")
                        except Exception as e:
                            print(f"  [Clean] {fname}/{col}: FAILED - {e}")

            print(f"  [AI-Clean] Completed: {cleaned_count} fixes applied")
    except Exception as e:
        print(f"  [AI-Clean] Skipped: {e}")

    # ================================================================
    # Step 2.6: 数据预处理（缺失值→异常值→标准化）
    # ================================================================
    print_section("Phase 1.6: Data Preprocessing")

    preprocess_report = {}
    new_dfs = {}  # 收集新 DataFrame，避免迭代时修改 dict
    for name, df in list(data_files.items()):
        try:
            n_before = len(df)
            # 1. Handle missing values
            mh = MissingHandler(strategy="median")
            df_clean = mh.fit_transform(df)
            missing_count = df.isnull().sum().sum()

            # 2. Detect and remove outliers (only on numeric columns)
            od = OutlierDetector(method="iqr", threshold=1.5)
            df_clean = od.remove(df_clean)
            n_removed = n_before - len(df_clean)

            # 3. Normalize (Z-score) — store normalized in separate key for ML models
            norm = Normalizer(method="zscore")
            df_norm = norm.fit_transform(df_clean)

            new_dfs[name] = df_clean
            new_dfs[f"{name}_norm"] = df_norm  # for ML/classification models

            preprocess_report[name] = {
                "missing_filled": int(missing_count),
                "outliers_removed": n_removed,
                "final_rows": len(df_clean),
                "normalized_cols": len(df_norm.select_dtypes(include=np.number).columns),
            }
            print(f"  [{name}] missing={missing_count} outliers={n_removed} -> {len(df_clean)} rows")
        except Exception as e:
            print(f"  [{name}] preprocessing skipped: {e}")
            new_dfs[name] = df  # keep original
    data_files.update(new_dfs)

    # ================================================================
    # Step 2.5: AI 指导数据加载
    # ================================================================
    data_guide = {}
    try:
        from api.config import APIConfig
        cfg = APIConfig()
        if cfg.is_configured:
            from mathmodel.pipeline.smart_orchestrator import AIDrivenPipeline
            ai0 = AIDrivenPipeline(api_key=cfg.api_key, model=cfg.model)
            data_guide = ai0.guide_data_loading(problem_text, data_profiles)
    except Exception as e:
        print(f"  [AI-Data] Skipped: {e}")

    # ================================================================
    # Step 3: AI-guided Solve → Validate → Fix loop
    # ================================================================
    print_section("Phase 2-3: AI-Guided Solving & Validation")

    all_results = {}
    max_solve_rounds = 3

    for solve_round in range(1, max_solve_rounds + 1):
        print(f"\n  === Solve Round {solve_round}/{max_solve_rounds} ===")

        # ---- Solve all sub-problems ----
        for sp in sub_problems:
            ptype = sp["type"]
            sp_id = sp["id"]
            if f"sub_{sp_id}" in all_results:
                continue

            # Build AI hints from data_guide
            dg_hints = {}
            for pp in data_guide.get("per_problem", []):
                if pp.get("sub_problem_id") == sp_id:
                    dg_hints = pp
                    break

            print(f"\n  >> Q{sp_id}: {sp['model']}")

            # ---- TRY AI EXECUTOR FIRST when data guide says needs multi-file ----
            ai_executed = False
            if dg_hints and len(dg_hints.get("files", [])) >= 2:
                try:
                    from api.config import APIConfig
                    cfg_ex = APIConfig()
                    if cfg_ex.is_configured:
                        from mathmodel.pipeline.smart_orchestrator import AIDrivenPipeline
                        ai_ex = AIDrivenPipeline(api_key=cfg_ex.api_key, model=cfg_ex.model)
                        # Convert data_guide hints to fix format
                        fix_plan = {
                            "fixes": [{
                                "sub_problem_id": sp_id,
                                "solver_type": ptype,
                                "files": dg_hints.get("files", []),
                                "columns_for_solver": {
                                    "cost_col": dg_hints.get("feature_columns", [None])[0] if dg_hints.get("feature_columns") else None,
                                    "benefit_col": dg_hints.get("target_columns", [None])[0] if dg_hints.get("target_columns") else None,
                                    "id_columns": dg_hints.get("id_columns", []),
                                },
                                "data_processing": dg_hints.get("aggregation", ""),
                                "join_keys": dg_hints.get("join_instructions", ""),
                                "solver_params": {"id_columns": dg_hints.get("id_columns", [])},
                            }]
                        }
                        fixed = ai_ex.execute_fix(fix_plan, data_files, data_profiles,
                                                   load_full_fn=_get_full_data)
                        if fixed.get(f"sub_{sp_id}"):
                            all_results.update(fixed)
                            ai_executed = True
                            print(f"     [AI-Exec] Direct solve, multi-file merge")
                            continue
                except Exception as e:
                    print(f"     [AI-Exec] Failed: {e}")

            # ---- Fallback: local solvers with AI hints ----
            if not ai_executed:
                with Timer() as t:
                    def solve_one():
                        if ptype == "评价" and data_files:
                            _solve_evaluation(sp, data_files, fig_dir, all_results, dg_hints)
                        elif ptype == "预测" and data_files:
                            _solve_prediction(sp, data_files, fig_dir, all_results, dg_hints)
                        elif ptype == "优化" and data_files:
                            _solve_optimization(sp, data_files, fig_dir, all_results, dg_hints)
                        elif ptype in ("分类", "聚类") and data_files:
                            _solve_classification(sp, data_files, fig_dir, all_results, dg_hints)
                        elif ptype == "统计" and data_files:
                            _solve_statistics(sp, data_files, fig_dir, all_results, dg_hints)
                        elif ptype == "综合" and data_files:
                            _solve_statistics(sp, data_files, fig_dir, all_results, dg_hints)
                            if f"sub_{sp_id}" not in all_results:
                                _solve_optimization(sp, data_files, fig_dir, all_results, dg_hints)
                    safe_call(solve_one, desc=f"Q{sp_id} {ptype} solver", timeout=120)
                print(f"     Time: {t.duration}")

        # ---- AI validate results (with timeout guard) ----
        def validate_and_fix():
            from api.config import APIConfig
            cfg2 = APIConfig()
            if not cfg2.is_configured:
                return "no_api"
            from mathmodel.pipeline.smart_orchestrator import AIDrivenPipeline
            aiv = AIDrivenPipeline(api_key=cfg2.api_key, model=cfg2.model)
            validation = aiv.validate_results(problem_text, sub_problems, all_results, data_guide)

            all_valid = all(c.get("valid", False) for c in validation.get("checks", []))
            if all_valid:
                print(f"\n  [AI-Validate] ALL RESULTS VALID!")
                return "all_valid"

            n_invalid = sum(1 for c in validation.get("checks", []) if not c.get("valid"))
            print(f"\n  [AI-Validate] {n_invalid} invalid. AI fix + execute...")
            ai_fix_plan = aiv.fix_solving_issues(problem_text, validation, data_guide)
            fixed_results = aiv.execute_fix(ai_fix_plan, data_files, data_profiles,
                                             load_full_fn=_get_full_data)
            n_fixed = len(fixed_results)
            if n_fixed == 0:
                print(f"       No fixes could be applied — accepting results with warnings")
                return "no_fix"
            for c in validation.get("checks", []):
                if not c.get("valid"):
                    key = f"sub_{c.get('sub_problem_id', '?')}"
                    if key in all_results: del all_results[key]
            all_results.update(fixed_results)
            print(f"       Applied {n_fixed} fixes")
            return "fixed"

        vresult = safe_call(validate_and_fix, desc="AI validate+fix loop", timeout=300)
        if vresult in ("all_valid", "no_fix", "no_api", None):
            break

    # ================================================================
    # Step 4: Sensitivity
    # ================================================================
    print_section("Phase 3: Sensitivity Analysis")

    sa = SensitivityAnalyzer()

    for key, value in all_results.items():
        if "forecast" in value and len(value.get("fitted", [])) >= 4:

            def gm_model(params):
                s = StatsSolver()
                r = s.grey_forecast(params.tolist(), forecast_steps=3)
                return float(r["forecast"][-1])

            data_arr = np.array(value["fitted"])
            try:
                robust = sa.robustness_check(gm_model, data_arr, noise_pct=0.05, n_samples=300)
                value["sensitivity"] = {
                    "cv": round(robust["cv"], 4),
                    "is_robust": robust["is_robust"],
                }
                print(f"  GM(1,1): CV={robust['cv']:.4f} "
                      f"({'STABLE' if robust['is_robust'] else 'UNSTABLE'})")
            except Exception as e:
                print(f"  Sensitivity failed: {e}")

    # ================================================================
    # Step 5: Figures
    # ================================================================
    print_section("Phase 4: Figures")

    set_style("zh", "default")
    plotter = Plotter(language="zh")
    fig_count = 0

    for key, value in all_results.items():
        # 评价得分柱状图
        if "scores" in value and "labels" in value:
            labels = value["labels"]
            scores = [float(s) for s in value["scores"]]
            fig, ax = plotter.bar(x=labels, y=scores, xlabel="方案", ylabel="综合得分", labels=labels)
            plotter.save(fig, fig_dir / "evaluation_scores.pdf")
            plotter.save(fig, fig_dir / "evaluation_scores.png")
            fig_count += 1
            print(f"  [{fig_count}] 评价得分图")

        # 预测对比图 (国赛标准: 实际+拟合+预测)
        if "forecast" in value and "fitted" in value:
            fitted = value["fitted"]
            forecast = value["forecast"]
            # Use forecast_plot for CUMCM standard
            if "original" in value:
                actual = value["original"]
                fig, ax = plotter.forecast_plot(actual, fitted, forecast,
                                                xlabel="时间序号", ylabel="数值")
            else:
                # Fallback to line chart with markers
                all_y = fitted + forecast
                n = len(fitted)
                fig, ax = plotter.line(x=list(range(len(all_y))), y=all_y, xlabel="时间序号", ylabel="数值")
                ax.scatter(range(n), fitted, color=get_colors(2)[0], s=40, zorder=5, label="拟合值")
                ax.scatter(range(n, len(all_y)), forecast, color=get_colors(2)[1], s=40, zorder=5, label="预测值")
                ax.axvline(x=n-0.5, color="gray", linestyle=":", alpha=0.5)
                ax.legend(fontsize=9, frameon=False)
            plotter.save(fig, fig_dir / "forecast.pdf")
            plotter.save(fig, fig_dir / "forecast.png")
            fig_count += 1
            print(f"  [{fig_count}] 预测趋势图")

        # 相关性热力图
        if "corr_matrix" in value and len(value.get("corr_matrix", [])) > 0:
            corr = np.array(value["corr_matrix"])
            cols = value.get("columns", [f"V{i}" for i in range(len(corr))])
            if len(cols) <= 12:
                fig, ax = plotter.heatmap(corr, cols)
            else:
                # Too many columns, take top 10
                fig, ax = plotter.heatmap(corr[:10, :10], cols[:10])
            plotter.save(fig, fig_dir / "correlation_heatmap.pdf")
            plotter.save(fig, fig_dir / "correlation_heatmap.png")
            fig_count += 1
            print(f"  [{fig_count}] 相关热力图")

        # 优化方案图
        if "selection" in value:
            labels = value.get("labels_all", value.get("selection", []))
            costs = value.get("costs", [])
            benefits = value.get("benefits", [])
            solution = value.get("solution", [])
            if costs and benefits and len(costs) == len(benefits):
                panels = [
                    {"type": "bar", "x": labels, "y": costs, "label": "(a) 成本对比", "xlabel": "", "ylabel": "成本"},
                    {"type": "bar", "x": labels, "y": benefits, "label": "(b) 收益对比", "xlabel": "", "ylabel": "收益"},
                ]
                fig, axes = plotter.multi_panel(panels, 1, 2, figsize=(10, 4))
                # Highlight selected items
                if solution:
                    colors_bar = get_colors(len(labels))
                    for i, (ax, vals) in enumerate(zip(np.atleast_1d(axes).flat, [costs, benefits])):
                        for j, (bar, selected) in enumerate(zip(ax.patches, solution)):
                            if not selected:
                                bar.set_alpha(0.25)
                plotter.save(fig, fig_dir / "optimization.pdf")
                plotter.save(fig, fig_dir / "optimization.png")
                fig_count += 1
                print(f"  [{fig_count}] 优化方案对比图")

        # 聚类/分类可视化 (PCA散点+聚类标签)
        if "pca_transformed" in value and "labels" in value:
            pca_xy = np.array(value["pca_transformed"])
            labels = value["labels"]
            n_clusters = value.get("n_clusters", 3)
            fig, ax = plt.subplots(figsize=(6, 5))
            colors = get_colors(n_clusters)
            for c in range(n_clusters):
                mask = np.array(labels) == c
                ax.scatter(pca_xy[mask, 0], pca_xy[mask, 1],
                          c=[colors[c]], s=30, alpha=0.7, edgecolors="white",
                          label=f"Cluster {c+1}")
            ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
            ax.legend(fontsize=8, frameon=False, title="Clusters")
            despine_fn = getattr(plotter, 'despine', None)
            if despine_fn is None:
                from mathmodel.visualization.styles import despine
                despine_fn = despine
            despine_fn(ax)
            ax.grid(alpha=0.2, linestyle=":")
            fig.tight_layout()
            plotter.save(fig, fig_dir / "clustering_pca.pdf")
            plotter.save(fig, fig_dir / "clustering_pca.png")
            fig_count += 1
            print(f"  [{fig_count}] 聚类PCA可视化 (轮廓系数={value.get('silhouette_score',0):.3f})")

    plotter.close_all()
    print(f"  Generated {fig_count} figures")

    # ================================================================
    # Step 6: Paper
    # ================================================================
    print_section("Phase 5: AI-Enhanced Paper")

    # ---- AI-enhanced writing (with per-step timeout protection) ----
    ai_content = {}
    try:
        from api.config import APIConfig
        cfg = APIConfig()
        if cfg.is_configured:
            from mathmodel.pipeline.smart_orchestrator import AIDrivenPipeline
            ai = AIDrivenPipeline(api_key=cfg.api_key, model=cfg.model)
            dsum = "\n".join(f"{n}: {p['shape'][0]}r x {p['shape'][1]}c" for n, p in data_profiles.items())

            # Phase 1+: AI 最优模型选择
            print("  [Phase 1+] AI Model Selection...")
            model_selection = ai.select_best_models(problem_text, dsum, sub_problems)

            # Phase 2: AI 制定计划
            plan = ai.analyze_and_plan(problem_text, dsum)
            analyses = ai.interpret_results(plan, all_results)

            # Phase 3: AI 写论文
            ai_content["abstract"] = ai.write_abstract(problem_text, plan, all_results, analyses)
            for sp in sub_problems:
                r = all_results.get(f"sub_{sp['id']}", {})
                a = {}
                for aa in analyses.get("analyses", []):
                    if aa.get("sub_problem_id") == sp["id"]: a = aa; break
                ai_content[f"section_{sp['id']}"] = ai.write_section(f"Q{sp['id']}", sp, r, a)
            ai_content["sensitivity"] = ai.write_sensitivity_section(all_results)
            ai_content["evaluation"] = ai.write_evaluation_section(sub_problems, all_results)

            # Phase 6: 复盘论证 → 审查 → 质疑 → 优化 → 重写
            print(f"\n  [Phase 6] AI Review & Refine...")
            refined = ai.review_and_refine(
                problem_text, sub_problems, all_results, ai_content, max_rounds=3
            )
            ai_content = refined.get("final_sections", ai_content)
            final_score = refined.get("final_score", 0)
            print(f"  [Phase 6] Final quality score: {final_score}/100")

            print(f"\n  [AI] Abstract: {len(ai_content.get('abstract',''))} chars")
            print(f"  [AI] Sections: {sum(1 for k in ai_content if k.startswith('section_'))}")
    except Exception as e:
        import traceback
        print(f"  [AI] Failed: {e}\n{traceback.format_exc()[:200]}")

    import datetime
    ts = datetime.datetime.now().strftime("%H%M%S")
    paper_path = generate_paper(
        output_path=str(out_dir / f"论文_{selected.name}_{ts}.docx"),
        problem_text=problem_text,
        analysis={"sub_problems": sub_problems},
        recommendations=[{
            "summary": " → ".join(sp["model"] for sp in sub_problems),
            "confidence": sum(sp["score"] for sp in sub_problems) / max(len(sub_problems), 1),
            "sub_problems": sub_problems,
        }],
        results=all_results,
        figures_dir=str(fig_dir),
        ai_content=ai_content,
    )
    print(f"  Word: {paper_path}")

    # ---- Also generate LaTeX paper ----
    try:
        tex_path = generate_latex_paper(
            str(out_dir / "latex"), problem_text,
            {"sub_problems": sub_problems}, all_results,
            str(fig_dir), ai_content
        )
        print(f"  LaTeX: {tex_path}")
    except Exception as e:
        print(f"  LaTeX: skipped ({e})")

    # Save results
    with open(out_dir / "results.json", "w", encoding="utf-8") as f:
        json.dump({"problem": selected.name, "sub_problems": sub_problems,
                    "results": _serializable(all_results)}, f, ensure_ascii=False, indent=2, default=str)

    # Done
    print()
    tracker.finish()
    print_result_summary(sub_problems, all_results)
    print_header(f"DONE! Paper → {paper_path}")
    print(f"  Figures: output/{selected.name}/figures/")
    print(f"  Results: output/{selected.name}/results.json")


# ================================================================
# Intelligent Solvers
# ================================================================

def _solve_evaluation(sp, data_files, fig_dir, results, ai_hints=None):
    """评价类：TOPSIS综合评价"""
    # Find mid-sized structured data (not huge transaction tables)
    best_name, best_df = None, None
    for name, df in data_files.items():
        if name.endswith("_norm"): continue
        num_cols = df.select_dtypes(include=np.number).shape[1]
        if 3 <= num_cols <= 20 and df.shape[0] < 1000:
            best_name, best_df = name, df
            break
    if best_df is None:
        for name, df in data_files.items():
            if name.endswith("_norm"): continue
            if df.select_dtypes(include=np.number).shape[1] >= 3:
                best_name, best_df = name, df
                break
    if best_df is None:
        print("     No suitable data for evaluation")
        return

    df = best_df
    numeric = df.select_dtypes(include=np.number)
    if numeric.shape[1] < 2:
        print("     Not enough numeric columns")
        return

    matrix = numeric.values.astype(float)

    # Determine impacts: columns with cost/loss-like names are negative
    impacts = []
    for col in numeric.columns:
        if any(kw in str(col) for kw in ['成本', '费用', '损失', '损耗', '率', 'cost', 'loss']):
            impacts.append(-1)
        else:
            impacts.append(1)

    evaluator = EvaluationSolver()
    ew = evaluator.entropy_weight(matrix)
    res = evaluator.topsis(matrix, weights=ew["weights"], impacts=impacts)

    labels = df.iloc[:, 0].tolist() if not df.iloc[:, 0].dtype == np.number else \
             [f"方案{i+1}" for i in range(len(df))]
    best_idx = int(np.argmax(res["scores"]))

    results[f"sub_{sp['id']}"] = {
        "labels": labels,
        "scores": [round(float(s), 4) for s in res["scores"]],
        "rank": [int(r) for r in res["rank"]],
        "weights": {str(c): round(float(w), 4) for c, w in zip(numeric.columns, ew["weights"])},
        "summary": f"最优: {labels[best_idx]} (得分: {max(res['scores']):.4f})",
    }
    print(f"     Best: {labels[best_idx]} ({max(res['scores']):.4f})")


def _solve_prediction(sp, data_files, fig_dir, results, ai_hints=None):
    """预测类：聚合时序数据后用GM(1,1)预测"""
    # Find time-series-like data: fewer columns, time-like index, NOT huge
    best_name, best_df = None, None
    for name, df in data_files.items():
        if name.endswith("_norm"): continue
        n_num = df.select_dtypes(include=np.number).shape[1]
        n_rows = df.shape[0]
        # Prediction needs small, time-series data (skip transaction tables)
        if n_num <= 3 and 4 <= n_rows <= 5000:
            # Check if there's a column that looks like dates
            for col in df.columns:
                if '日期' in str(col) or '时间' in str(col) or 'date' in str(col).lower() or '年份' in str(col):
                    best_name, best_df = name, df
                    break
            if best_df is not None:
                break

    # Fallback: any small table (max 500 rows)
    if best_df is None:
        for name, df in data_files.items():
            if name.endswith("_norm"): continue
            if df.shape[0] <= 500 and df.select_dtypes(include=np.number).shape[1] >= 1:
                best_name, best_df = name, df
                break

    if best_df is None:
        print("     No suitable data for prediction (need small time-series, <=5000 rows)")
        return

    df = best_df
    n_rows = df.shape[0]
    print(f"     Using: {best_name} ({n_rows} rows)")

    # If there's a date column, aggregate by it
    date_col = None
    for col in df.columns:
        if '日期' in str(col) or 'date' in str(col).lower():
            date_col = col
            break

    if date_col and n_rows > 50:
        # Aggregate by date (limit rows for safety)
        if n_rows > 5000:
            df = df.head(5000)  # safety trim
            print(f"     Trimmed to 5000 rows for date parsing")
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])  # remove rows where date parsing failed
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        if len(numeric_cols) >= 1:
            value_col = numeric_cols[0]
            for c in numeric_cols:
                if any(kw in str(c) for kw in ['销量', '销售', '数量', '金额', 'price', 'qty', 'amount']):
                    value_col = c
                    break
            if df.shape[0] > 0:
                daily = df.groupby(date_col)[value_col].sum().sort_index()
                data = daily.tolist()
            else:
                data = []
        else:
            data = df.select_dtypes(include=np.number).iloc[:, 0].tolist()
    else:
        # Find numeric value column
        data_col = None
        for col in df.columns:
            if df[col].dtype in ('int64', 'float64'):
                if any(kw in str(col) for kw in ['销量', '销售', '需求', '量', '金额', '值']):
                    data_col = col
                    break
        if data_col is None:
            numeric_cols = df.select_dtypes(include=np.number).columns
            data_col = numeric_cols[0] if len(numeric_cols) > 0 else None

        if data_col is None:
            print("     No numeric column found")
            return

        data = df[data_col].dropna().tolist()

    # Final safety: ensure data is reasonable
    if len(data) < 4:
        print(f"     Not enough data points ({len(data)})")
        return
    if len(data) > 200:
        data = data[-50:]  # take last 50 for trend
        print(f"     Trimmed to last 50 points")

    print(f"     Series: {len(data)} data points, range [{min(data):.1f}, {max(data):.1f}]")

    solver = StatsSolver()
    pred = solver.grey_forecast(data, forecast_steps=3)

    results[f"sub_{sp['id']}"] = {
        "original": data,
        "fitted": [round(v, 4) for v in pred["fitted"]],
        "forecast": [round(v, 4) for v in pred["forecast"]],
        "mape": round(pred["mape"], 2),
        "grade": pred["grade"],
        "params": pred["params"],
        "summary": f"MAPE={pred['mape']:.2f}% [{pred['grade']}], "
                   f"预测: {[round(v,1) for v in pred['forecast']]}",
    }
    print(f"     MAPE: {pred['mape']:.2f}% [{pred['grade']}]")
    print(f"     Forecast: {[round(v, 1) for v in pred['forecast']]}")


def _solve_optimization(sp, data_files, fig_dir, results, ai_hints=None):
    """优化类：自动聚合大数据后再做优化"""
    # Try to aggregate large transaction data into optimization-ready form
    # Look for sales data (large) + price/cost data
    large_dfs = {k: v for k, v in data_files.items() if v.shape[0] > 1000 and not k.endswith("_norm")}
    small_dfs = {k: v for k, v in data_files.items() if v.shape[0] <= 1000 and not k.endswith("_norm")}

    best_name, best_df = None, None

    # Strategy 1: Aggregate large sales data by category
    if large_dfs:
        for name, df in large_dfs.items():
            num_cols = df.select_dtypes(include=np.number).columns.tolist()
            cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

            if '销量' in ' '.join(df.columns) or '销售' in ' '.join(df.columns):
                # Find category column and aggregate
                group_col = None
                for c in cat_cols:
                    if any(kw in str(c) for kw in ['品类', '分类', '类别', 'category', '单品']):
                        group_col = c
                        break
                if group_col is None and cat_cols:
                    group_col = cat_cols[0]

                value_col = None
                for c in num_cols:
                    if any(kw in str(c) for kw in ['销量', '销售', '数量', '金额', 'qty', 'amount', 'sales']):
                        value_col = c
                        break
                if value_col is None and num_cols:
                    value_col = num_cols[-1]

                if group_col and value_col:
                    agg = df.groupby(group_col)[value_col].sum().reset_index()
                    agg.columns = ['项目', '总销量']
                    agg = agg.sort_values('总销量', ascending=False).head(30)
                    print(f"     Aggregated {name}: {df.shape[0]} → {agg.shape[0]} groups")
                    best_df = agg
                    best_name = name
                    break

    # Strategy 2: Use small structured data (original behavior)
    if best_df is None and small_dfs:
        for name, df in small_dfs.items():
            num = df.select_dtypes(include=np.number)
            if num.shape[1] >= 2:
                best_name, best_df = name, df
                break

    if best_df is None:
        print("     No suitable data for optimization")
        return

    df = best_df
    numeric = df.select_dtypes(include=np.number)
    cols = numeric.columns.tolist()

    # AI hints take priority for column selection
    cost_col, benefit_col = None, None
    if ai_hints:
        ai_cols = ai_hints.get("columns_for_solver", {})
        if ai_cols.get("cost_col") in cols:
            cost_col = ai_cols["cost_col"]
            print(f"     [AI hint] cost_col = {cost_col}")
        if ai_cols.get("benefit_col") in cols:
            benefit_col = ai_cols["benefit_col"]
            print(f"     [AI hint] benefit_col = {benefit_col}")

    # Auto-detect only if AI didn't specify
    if cost_col is None:
        for c in cols:
            if any(kw in str(c) for kw in ['成本', '费用', '价格', '批发价', 'cost', 'price', '单价']):
                cost_col = c; break
    if benefit_col is None:
        for c in cols:
            if any(kw in str(c) for kw in ['收益', '利润', '销量', '覆盖', '人口', 'benefit', 'sales', '销售']):
                benefit_col = c; break

    if cost_col is None:
        cost_col = cols[1] if len(cols) > 1 else cols[0]
    if benefit_col is None:
        benefit_col = cols[2] if len(cols) > 2 else cols[1]

    # Exclude ID columns from being chosen as cost/benefit
    exclude = set(ai_hints.get("id_columns", []) if ai_hints else [])
    if cost_col in exclude and len(cols) > len(exclude):
        for c in cols:
            if c not in exclude: cost_col = c; break
    if benefit_col in exclude and len(cols) > len(exclude):
        for c in cols:
            if c not in exclude and c != cost_col: benefit_col = c; break

    costs = numeric[cost_col].values.astype(float).tolist()
    benefits = numeric[benefit_col].values.astype(float).tolist()
    labels = df.iloc[:, 0].tolist() if not df.iloc[:, 0].dtype == np.number else \
             [f"项目{i+1}" for i in range(len(df))]

    print(f"     Cost col: {cost_col}, Benefit col: {benefit_col}")
    print(f"     Items: {len(labels)}, Budget: auto")

    # Auto budget: 60% of total cost
    total_cost = sum(costs)
    budget = total_cost * 0.6

    # Reduce to top 15 items by ratio for efficiency
    if len(labels) > 15:
        ratios = [b / c if c > 0 else 0 for b, c in zip(benefits, costs)]
        idx_sorted = np.argsort(ratios)[::-1][:15]
        labels = [labels[i] for i in idx_sorted]
        costs = [costs[i] for i in idx_sorted]
        benefits = [benefits[i] for i in idx_sorted]
        budget = sum(costs) * 0.5
        print(f"     Reduced to top 15 items, budget={budget:.1f}")

    # Use greedy approach (fast & reliable for knapsack)
    ratios = [(benefits[i] / costs[i] if costs[i] > 0 else 0, i)
              for i in range(len(labels))]
    ratios.sort(key=lambda x: -x[0])

    selected = []
    remaining = budget
    sel_cost = 0
    sel_benefit = 0
    solution = [0] * len(labels)

    for ratio, idx in ratios:
        if costs[idx] <= remaining:
            solution[idx] = 1
            selected.append(labels[idx])
            remaining -= costs[idx]
            sel_cost += costs[idx]
            sel_benefit += benefits[idx]

    # Try swapping last selected with next best for better fit
    print(f"     Greedy: {len(selected)} items, cost={sel_cost:.1f}, benefit={sel_benefit:.1f}")

    # Also try IP for comparison if small enough
    if len(labels) <= 12:
        try:
            opt = OptimizationSolver()
            c_obj = [-float(b) for b in benefits]
            A_ub = [[float(x) for x in costs]]
            b_ub = [float(budget)]
            ip_result = opt.integer_program(
                c=c_obj, A_ub=A_ub, b_ub=b_ub, bounds=(0, 1), binary=True,
            )
            if ip_result.success:
                ip_solution = [int(v > 0.5) for v in ip_result.x]
                ip_selected = [labels[i] for i, v in enumerate(ip_solution) if v]
                ip_cost = sum(costs[i] for i, v in enumerate(ip_solution) if v)
                ip_benefit = sum(benefits[i] for i, v in enumerate(ip_solution) if v)
                if ip_benefit > sel_benefit:
                    selected, sel_cost, sel_benefit, solution = (
                        ip_selected, ip_cost, ip_benefit, ip_solution)
                    print(f"     IP improved: benefit {ip_benefit:.1f}")
        except Exception:
            pass

    results[f"sub_{sp['id']}"] = {
        "selection": [str(s) for s in selected],
        "total_cost": round(float(sel_cost), 1),
        "total_population": round(float(sel_benefit), 1),
        "solution": solution,
        "costs": costs,
        "benefits": benefits,
        "budget": round(float(budget), 1),
        "summary": f"选择 {len(selected)} 个, 成本 {sel_cost:.1f}, 收益 {sel_benefit:.1f}",
    }
    print(f"     Final: {len(selected)} items, cost={sel_cost:.1f}/{budget:.1f}, benefit={sel_benefit:.1f}")


def _solve_statistics(sp, data_files, fig_dir, results, ai_hints=None):
    """统计类：相关性分析、分布统计。支持AI指定列名。"""
    # AI hints: use specified columns instead of auto-detection
    exclude_cols = []
    if ai_hints:
        exclude_cols = ai_hints.get("id_columns", [])
        print(f"     [AI hint] Excluding ID cols: {exclude_cols[:5]}")

    # Try to load full data for large transaction files
    best_name, best_df = None, None
    for name, df in data_files.items():
        if name.endswith("_norm"): continue
        num = df.select_dtypes(include=np.number).shape[1]
        if num >= 2 and df.shape[0] > 100:
            # If large file, try to load full data for better analysis
            if df.shape[0] < 1000 or (name in _full_data_cache):
                pass  # use as-is
            elif _data_profiles_global.get(name, {}).get('size_category') == 'large' and df.shape[0] <= 500:
                # This is a sample — try loading full
                full_df = _get_full_data(name)
                if full_df is not None and full_df.shape[0] > df.shape[0]:
                    df = full_df
                    data_files[name] = df  # cache
            best_name, best_df = name, df
            break

    if best_df is None:
        print("     No suitable data for statistics")
        return

    df = best_df
    print(f"     Using: {best_name} ({df.shape[0]} rows)")

    # Exclude ID columns
    numeric = df.select_dtypes(include=np.number)
    cols_to_use = [c for c in numeric.columns if c not in exclude_cols]
    if len(cols_to_use) < 2:
        cols_to_use = numeric.columns.tolist()
    numeric = numeric[cols_to_use]

    # If large, sample for correlation
    if df.shape[0] > 10000:
        df_sample = df.sample(10000, random_state=42)
        numeric = df_sample[numeric.columns].select_dtypes(include=np.number)
        print(f"     Sampled to 10000 rows for correlation")

    # Limit columns for correlation (wide tables are slow)
    n_cols = numeric.shape[1]
    if n_cols > 30:
        # Keep top 30 columns by variance
        variances = numeric.var().sort_values(ascending=False)
        top_cols = variances.head(30).index.tolist()
        numeric = numeric[top_cols]
        print(f"     Limited to top 30 columns by variance (from {n_cols})")

    # Correlation matrix
    corr_matrix = numeric.corr().values
    columns = numeric.columns.tolist()

    # Also compute basic stats
    top_corrs = []
    for i in range(len(columns)):
        for j in range(i + 1, len(columns)):
            top_corrs.append({
                "pair": (columns[i], columns[j]),
                "correlation": round(float(corr_matrix[i][j]), 4),
            })
    top_corrs.sort(key=lambda x: abs(x["correlation"]), reverse=True)

    results[f"sub_{sp['id']}"] = {
        "columns": columns,
        "corr_matrix": [[round(float(v), 4) for v in row] for row in corr_matrix],
        "top_correlations": top_corrs[:15],
        "data_shape": (df.shape[0], len(columns)),
        "summary": (f"相关性分析: {df.shape[0]}行×{len(columns)}列, "
                   f"最强相关: {top_corrs[0]['pair'][0]}-{top_corrs[0]['pair'][1]} "
                   f"(r={top_corrs[0]['correlation']:.3f})" if top_corrs else ""),
    }

    print(f"     Analyzed {len(columns)} columns, {df.shape[0]} rows")
    for tc in top_corrs[:5]:
        print(f"       {tc['pair'][0]} vs {tc['pair'][1]}: r={tc['correlation']:.3f}")


def _solve_classification(sp, data_files, fig_dir, results, ai_hints=None):
    """分类/聚类类：K-means聚类+PCA降维可视化"""
    mls = MLSolver()

    # Find suitable data — prefer normalized version if available
    best_name, best_df = None, None
    for name, df in data_files.items():
        if name.endswith("_norm"):
            continue  # skip normalized variants for selection, use originals
        num = df.select_dtypes(include=np.number).shape[1]
        if num >= 2:
            best_name, best_df = name, df
            break
    if best_df is None:
        for name, df in data_files.items():
            if name.endswith("_norm"):
                best_name, best_df = name, df
                break
    if best_df is None:
        print("     No suitable data for classification")
        return

    df = best_df
    numeric = df.select_dtypes(include=np.number)
    print(f"     Using: {best_name} ({numeric.shape[0]} rows, {numeric.shape[1]} features)")

    # Use normalized data if available
    df_norm = data_files.get(f"{best_name}_norm", df)
    numeric_norm = df_norm.select_dtypes(include=np.number)

    n_samples = numeric.shape[0]
    n_features = numeric.shape[1]

    # Determine number of clusters
    if n_samples <= 50:
        n_clusters = min(5, n_samples - 1)
    elif n_samples <= 200:
        n_clusters = min(5, max(2, n_samples // 20))
    else:
        n_clusters = min(8, max(3, n_samples // 50))
    n_clusters = max(2, n_clusters)

    # --- K-means clustering ---
    kmeans_result = mls.kmeans(numeric_norm.values, n_clusters=n_clusters)

    # --- PCA for visualization ---
    pca_result = mls.pca(numeric_norm.values, n_components=2)

    # --- Hierarchical clustering for comparison ---
    try:
        hier_result = mls.hierarchical(numeric_norm.values, n_clusters=n_clusters)
    except Exception:
        hier_result = None

    # --- Build cluster profiles (mean of each feature per cluster) ---
    labels_arr = np.array(kmeans_result["labels"])
    cluster_profiles = {}
    for c in range(n_clusters):
        mask = labels_arr == c
        if mask.sum() > 0:
            cluster_profiles[f"Cluster {c+1}"] = {
                "size": int(mask.sum()),
                "pct": round(float(mask.sum() / n_samples * 100), 1),
                "feature_means": {str(col): round(float(numeric.iloc[:, i][mask].mean()), 3)
                                  for i, col in enumerate(numeric.columns[:8])},
            }

    # --- Determine dominant cluster ---
    sizes = [(c, p["size"]) for c, p in cluster_profiles.items()]
    sizes.sort(key=lambda x: -x[1])
    dominant = sizes[0][0] if sizes else "Cluster 1"

    results[f"sub_{sp['id']}"] = {
        "method": "K-means + PCA",
        "n_clusters": n_clusters,
        "n_samples": n_samples,
        "n_features": n_features,
        "labels": kmeans_result["labels"],
        "silhouette_score": kmeans_result["silhouette_score"],
        "pca_transformed": pca_result["transformed"],
        "pca_variance": pca_result["explained_variance_ratio"],
        "cumulative_variance": pca_result["cumulative_variance"],
        "cluster_profiles": cluster_profiles,
        "hierarchical_labels": hier_result["labels"] if hier_result else [],
        "dominant_cluster": dominant,
        "summary": (f"K-means聚类: {n_samples}样本→{n_clusters}类, "
                   f"轮廓系数={kmeans_result['silhouette_score']:.4f}, "
                   f"最大类={dominant}({cluster_profiles.get(dominant, {}).get('pct', '?')}%), "
                   f"PCA前2维累积方差={pca_result['cumulative_variance']:.2%}"),
    }

    print(f"     K-means: {n_clusters} clusters, silhouette={kmeans_result['silhouette_score']:.4f}")
    print(f"     PCA: {pca_result['cumulative_variance']:.2%} variance retained")
    for c, p in cluster_profiles.items():
        print(f"       {c}: {p['size']} samples ({p['pct']}%)")


# ================================================================
# Data Helpers
# ================================================================

# Cache for full data loaded on demand
_full_data_cache = {}
_data_profiles_global = {}

def _analyze_with_api_or_rules(sub_raw, data_profiles, problem_text):
    """AI分析回退规则引擎：API可用时用AI，否则用本地规则"""
    # Summarize data for API
    data_summary_lines = []
    for name, profile in data_profiles.items():
        data_summary_lines.append(
            f"{name}: {profile['shape'][0]}行×{profile['shape'][1]}列, "
            f"列名: {', '.join(str(c) for c in profile['columns'][:10])}"
        )
    data_summary = '\n'.join(data_summary_lines)

    # Try API
    try:
        from api.config import APIConfig
        from api.analyzer import AIAnalyzer

        config = APIConfig()  # auto-loads from .env
        if config.is_configured:
            print("  [Using AI analysis (DeepSeek)...]")
            analyzer = AIAnalyzer(config)

            # Build full problem context
            full_context = problem_text
            for sp in sub_raw:
                full_context += '\n' + sp['text']

            analysis = analyzer.full_analysis(full_context, data_summary)

            if analysis.get("source") == "ai":
                sub_problems = []
                recs = analysis.get("model_recommendations", [])
                for sp in analysis.get("problem_analysis", {}).get("sub_problems", []):
                    sp_id = sp.get("id", len(sub_problems) + 1)
                    # Get AI recommendation for this sub-problem
                    ai_model = ""
                    ai_score = 0.0
                    ai_reason = ""
                    for r in recs:
                        if r.get("sub_problem_id") == sp_id:
                            best = r.get("best_choice", "")
                            rec_list = r.get("recommendations", [])
                            if rec_list:
                                ai_model = rec_list[0].get("model", best)
                                ai_score = rec_list[0].get("score", 0.9)
                                ai_reason = rec_list[0].get("reason", "")
                            break

                    sub_problems.append({
                        "id": sp_id,
                        "title": sp.get("title", "")[:150],
                        "full_text": sp.get("title", ""),
                        "type": sp.get("type", "综合"),
                        "model": ai_model or f"{sp.get('type','')}相关模型",
                        "score": ai_score or 0.85,
                        "reason": ai_reason or f"AI分析推荐: {sp.get('type','')}类问题",
                        "source": "ai",
                    })
                if sub_problems:
                    return sub_problems
    except Exception as e:
        print(f"  [AI unavailable: {e}, using rule-based]")

    # Rule-based fallback
    classifier = ProblemClassifier()
    kb = ModelKnowledgeBase()
    sub_problems = []
    for sp in sub_raw:
        clf = classifier.classify(sp["text"])
        cand = kb.query(problem_type=clf["type"], top_k=3)
        m = cand[0] if cand else {"model": "待定", "score": 0, "reason": ""}
        sub_problems.append({
            "id": sp["id"], "title": sp["text"][:150], "full_text": sp["text"],
            "type": clf["type"], "type_scores": clf.get("scores", {}),
            "model": m.get("model", ""), "score": m.get("score", 0),
            "reason": m.get("reason", ""), "source": "rule",
        })
    return sub_problems


def _get_full_data(name: str) -> pd.DataFrame | None:
    """Load full data on demand with caching"""
    if name in _full_data_cache:
        return _full_data_cache[name]

    profile = _data_profiles_global.get(name)
    if not profile:
        return None

    path = Path(profile['path'])
    print(f"     [Loading full data: {path.name}...]")
    if path.suffix == '.csv':
        df = pd.read_csv(path, low_memory=True)
    else:
        df = pd.read_excel(path)

    _full_data_cache[name] = df
    return df

def _count_rows(path: Path) -> int:
    """Quick row count estimate"""
    try:
        # For .xlsx, just load header + first data row to estimate
        df = pd.read_excel(path, nrows=5)
        # Use file size to estimate
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > 10:
            return int(size_mb * 50000)  # rough estimate for large files
        return pd.read_excel(path).shape[0]
    except Exception:
        return 50000  # fallback estimate


def _count_csv_rows(path: Path) -> int:
    """Quick row count for CSV"""
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > 50:
        return int(size_mb * 60000)  # estimate
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return sum(1 for _ in f) - 1


def _load_optimized(path: Path) -> pd.DataFrame:
    """Load Excel with optimized dtypes for large files"""
    df = pd.read_excel(path)
    for col in df.columns:
        if df[col].dtype == 'float64':
            df[col] = pd.to_numeric(df[col], downcast='float')
        elif df[col].dtype == 'int64':
            df[col] = pd.to_numeric(df[col], downcast='integer')
        elif df[col].dtype == 'object':
            # If column has few unique values, use category
            if df[col].nunique() / len(df) < 0.5:
                df[col] = df[col].astype('category')
    return df


def _load_csv_optimized(path: Path) -> pd.DataFrame:
    """Load CSV with optimized dtypes"""
    # Read with low_memory and dtype optimization
    df = pd.read_csv(path, low_memory=True)
    for col in df.select_dtypes(include=['float64']).columns:
        df[col] = pd.to_numeric(df[col], downcast='float')
    return df


def _serializable(obj):
    """Convert numpy types to native Python for JSON"""
    if isinstance(obj, dict):
        return {str(k): _serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serializable(v) for v in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


if __name__ == "__main__":
    main()
