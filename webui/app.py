"""
MathModel Toolkit — Web 界面
============================
左侧：上传题目 + API配置
右侧：实时进度 + 结果下载
"""

import sys
import json
import time
import threading
from pathlib import Path
import tempfile
import os

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
import numpy as np

from mathmodel.utils import set_seed
from mathmodel.analyzer import ProblemClassifier, ModelKnowledgeBase
from mathmodel.models import EvaluationSolver, StatsSolver, OptimizationSolver
from mathmodel.sensitivity import SensitivityAnalyzer
from mathmodel.visualization import Plotter, set_style
from mathmodel.paper.word_writer import generate_paper

# ============================================================
# 页面设置
# ============================================================
st.set_page_config(
    page_title="MathModel Toolkit",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 自定义 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .sub-header { color: #888; margin-top: -10px; margin-bottom: 20px; }
    .step-box {
        padding: 12px 16px;
        border-radius: 8px;
        margin: 4px 0;
        font-size: 14px;
    }
    .step-done { background: #e8f5e9; border-left: 4px solid #4caf50; }
    .step-running { background: #fff3e0; border-left: 4px solid #ff9800; }
    .step-pending { background: #f5f5f5; border-left: 4px solid #ccc; }
    .step-error { background: #ffebee; border-left: 4px solid #f44336; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 标题
# ============================================================
st.markdown('<p class="main-header">🚀 MathModel Toolkit</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">上传题目 → 智能分析 → 一键出论文</p>', unsafe_allow_html=True)

# ============================================================
# 左右分栏
# ============================================================
left, right = st.columns([1, 1.2])

# ============================================================
# 左侧：上传 & 配置
# ============================================================
with left:
    st.subheader("📤 上传文件")

    # 题目文件
    problem_file = st.file_uploader(
        "赛题文件（PDF / DOCX / TXT）",
        type=["pdf", "docx", "txt"],
        key="problem",
        help="支持 PDF、Word 和纯文本格式",
    )

    # 数据文件
    data_files = st.file_uploader(
        "数据附件（XLSX / CSV）",
        type=["xlsx", "xls", "csv"],
        accept_multiple_files=True,
        key="data",
        help="可以一次上传多个数据文件",
    )

    st.divider()

    # ========================================================
    # API 配置（用户可选）
    # ========================================================
    st.subheader("🔑 API 配置（可选）")
    st.caption("接入 LLM 获得更智能的题目分析和模型推荐")

    use_api = st.checkbox("启用 AI 智能分析", value=False,
                          help="勾选后使用大语言模型自动分析题目、推荐模型、撰写论文")

    api_provider = st.selectbox(
        "API 提供商",
        ["OpenAI", "Anthropic (Claude)", "DeepSeek", "自定义兼容接口"],
        disabled=not use_api,
    )

    api_key = st.text_input(
        "API Key",
        type="password",
        placeholder="sk-..." if not use_api else "输入你的 API Key",
        disabled=not use_api,
        help="你的 API Key 仅在本机使用，不会上传到任何服务器",
    )

    api_base = st.text_input(
        "API Base URL（可选）",
        placeholder="https://api.openai.com/v1",
        disabled=not use_api,
        help="自定义 API 地址，留空则使用默认地址",
    )

    api_model = st.text_input(
        "模型名称（可选）",
        placeholder="gpt-4o / claude-sonnet-5 / deepseek-chat",
        disabled=not use_api,
        help="留空则自动选择默认模型",
    )

    st.divider()

    # ========================================================
    # 启动按钮
    # ========================================================
    st.subheader("⚡ 开始求解")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        start_btn = st.button(
            "🚀 一键求解",
            type="primary",
            use_container_width=True,
            disabled=not problem_file,
        )
    with col_btn2:
        stop_btn = st.button(
            "⏹ 停止",
            use_container_width=True,
        )

    if not problem_file:
        st.info("👆 请先上传赛题文件")

# ============================================================
# 右侧：进度 & 结果
# ============================================================
with right:
    st.subheader("📊 求解进度")

    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    result_placeholder = st.empty()

    # 初始化 session state
    if "solving" not in st.session_state:
        st.session_state.solving = False
    if "results" not in st.session_state:
        st.session_state.results = None
    if "paper_path" not in st.session_state:
        st.session_state.paper_path = None
    if "progress" not in st.session_state:
        st.session_state.progress = {}
    if "status_text" not in st.session_state:
        st.session_state.status_text = "等待中..."

    # 显示当前状态
    if not st.session_state.solving:
        status_placeholder.info("📌 上传文件后点击「一键求解」开始")
    else:
        # 显示进度
        prog = st.session_state.progress
        with progress_placeholder.container():
            progress_bar = st.progress(prog.get("overall", 0))
            st.caption(f"总进度: {prog.get('overall', 0) * 100:.0f}%")

        # 显示各步骤状态
        steps = prog.get("steps", [
            ("parse", "文档解析", "pending", ""),
        ])
        html_parts = []
        for step_id, step_name, step_status, step_msg in steps:
            if step_status == "done":
                cls = "step-done"
                icon = "✅"
            elif step_status == "running":
                cls = "step-running"
                icon = "🔄"
            elif step_status == "error":
                cls = "step-error"
                icon = "❌"
            else:
                cls = "step-pending"
                icon = "⏳"
            html_parts.append(
                f'<div class="step-box {cls}"><b>{icon} {step_name}</b>'
                f'{" — " + step_msg if step_msg else ""}</div>'
            )
        status_placeholder.markdown("\n".join(html_parts), unsafe_allow_html=True)

    # 显示结果
    if st.session_state.results:
        with result_placeholder.container():
            st.divider()
            st.subheader("📋 求解结果")

            results = st.session_state.results
            for sp in results.get("sub_problems", []):
                with st.expander(f"子问题{sp['id']}: {sp['model']} [{sp['type']}]", expanded=True):
                    st.markdown(f"**推荐理由**: {sp['reason']}")
                    if sp.get('result'):
                        st.json(sp['result'])

            st.divider()
            st.subheader("📥 下载")

            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                if st.session_state.paper_path and Path(st.session_state.paper_path).exists():
                    with open(st.session_state.paper_path, "rb") as f:
                        st.download_button(
                            "📝 下载论文 (Word)",
                            data=f,
                            file_name="论文.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True,
                        )

            with col_dl2:
                # 结果 JSON
                results_json = json.dumps(results, ensure_ascii=False, indent=2, default=str)
                st.download_button(
                    "📊 下载结果 (JSON)",
                    data=results_json,
                    file_name="results.json",
                    mime="application/json",
                    use_container_width=True,
                )

            # 图表下载
            paper_dir = Path(st.session_state.paper_path).parent if st.session_state.paper_path else None
            if paper_dir:
                fig_dir = paper_dir / "figures"
                if fig_dir.exists():
                    st.caption("📈 生成图表：")
                    figs = sorted(fig_dir.glob("*.pdf"))
                    fig_cols = st.columns(min(len(figs), 3))
                    for i, fp in enumerate(figs):
                        with fig_cols[i % 3]:
                            with open(fp, "rb") as f:
                                st.download_button(
                                    f"📎 {fp.name}",
                                    data=f,
                                    file_name=fp.name,
                                    mime="application/pdf",
                                    use_container_width=True,
                                )


# ============================================================
# 求解逻辑
# ============================================================
def update_progress(overall, steps):
    """更新进度"""
    st.session_state.progress = {"overall": overall, "steps": steps}


def run_pipeline(problem_content, data_dfs, api_config):
    """执行求解流水线"""
    set_seed(42)
    tmp_dir = Path(tempfile.mkdtemp(prefix="mathmodel_"))
    output_dir = tmp_dir / "output"
    output_dir.mkdir()

    steps = [
        ("parse", "文档解析", "pending", ""),
        ("analyze", "题目分析", "pending", ""),
        ("recommend", "模型推荐", "pending", ""),
        ("solve", "模型求解", "pending", ""),
        ("sensitivity", "灵敏度分析", "pending", ""),
        ("visualize", "生成图表", "pending", ""),
        ("paper", "生成论文", "pending", ""),
    ]

    def set_step(idx, status, msg=""):
        steps[idx] = (steps[idx][0], steps[idx][1], status, msg)
        update_progress((idx + 1) / len(steps), steps)

    # ---- Step 1: 解析 ----
    set_step(0, "running", "读取文件…")
    time.sleep(0.3)

    problem_text = problem_content
    data_summary = {name: f"{df.shape[0]}行×{df.shape[1]}列" for name, df in data_dfs.items()}

    set_step(0, "done", f"题目 {len(problem_text)} 字符, {len(data_dfs)} 个数据表")

    # ---- Step 2: 分析 ----
    set_step(1, "running", "分类题型…")
    time.sleep(0.3)

    classifier = ProblemClassifier()
    kb = ModelKnowledgeBase()

    # 拆分子问题
    sub_problems = []
    lines = problem_text.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        if '问题' in line and any(c in line for c in '123456789一二三四五六七八九'):
            context = line
            for j in range(i + 1, min(i + 4, len(lines))):
                if '问题' in lines[j] and any(c in lines[j] for c in '123456789'):
                    break
                context += ' ' + lines[j].strip()
            sub_problems.append({"id": len(sub_problems) + 1, "text": context[:400]})
            if len(sub_problems) >= 5:
                break

    if not sub_problems:
        sub_problems = [{"id": 1, "text": problem_text[:400]}]

    set_step(1, "done", f"识别到 {len(sub_problems)} 个子问题")

    # ---- Step 3: 推荐（可选使用 AI） ----
    set_step(2, "running", "检索最佳模型…")
    time.sleep(0.3)

    analyzed = []
    for sp in sub_problems:
        clf = classifier.classify(sp["text"])
        candidates = kb.query(problem_type=clf["type"], top_k=3)

        if api_config.get("enabled") and api_config.get("key"):
            # 用 AI 增强推荐
            try:
                ai_rec = _ai_recommend(sp["text"], clf, candidates, api_config)
                if ai_rec:
                    candidates = ai_rec
            except Exception:
                pass

        analyzed.append({
            "id": sp["id"],
            "title": sp["text"][:100],
            "type": clf["type"],
            "model": candidates[0]["model"] if candidates else "待定",
            "score": candidates[0]["score"] if candidates else 0,
            "reason": candidates[0]["reason"] if candidates else "",
            "solver_path": candidates[0]["solver_path"] if candidates else "",
            "candidates": candidates,
        })

    set_step(2, "done", f"推荐完成: {' → '.join(a['model'] for a in analyzed)}")

    # ---- Step 4: 求解 ----
    set_step(3, "running", "运行求解器…")
    time.sleep(0.3)

    all_results = {}
    for sp in analyzed:
        ptype = sp["type"]

        if ptype == "评价" and data_dfs:
            df = _find_df(data_dfs, min_num_cols=3)
            evaluator = EvaluationSolver()
            numeric = df.select_dtypes(include=np.number)
            matrix = numeric.values
            impacts = []
            for col in numeric.columns:
                if any(kw in str(col) for kw in ["成本", "环境", "影响", "费用"]):
                    impacts.append(-1)
                else:
                    impacts.append(1)
            ew = evaluator.entropy_weight(matrix)
            result = evaluator.topsis(matrix, weights=ew["weights"], impacts=impacts)
            labels = df.iloc[:, 0].tolist()
            all_results[f"sub_{sp['id']}"] = {
                "scores": [round(float(s), 4) for s in result["scores"]],
                "rank": [int(r) for r in result["rank"]],
                "labels": labels,
                "summary": f"最优: {labels[int(np.argmax(result['scores']))]}",
            }
            sp["result"] = {
                "最优方案": labels[int(np.argmax(result["scores"]))],
                "排名": " > ".join(str(labels[i]) for i in np.argsort(result["scores"])[::-1]),
            }

        elif ptype == "预测" and data_dfs:
            df = _find_df(data_dfs, max_num_cols=3, min_rows=4)
            solver = StatsSolver()
            data_col = None
            for col in df.columns:
                if df[col].dtype in ("int64", "float64"):
                    if any(kw in str(col).lower() for kw in ["需求", "量", "值", "demand"]):
                        data_col = col
                        break
            if data_col is None:
                for col in df.columns:
                    if df[col].dtype in ("int64", "float64") and df[col].max() > 10:
                        data_col = col
                        break
            if data_col:
                data = df[data_col].tolist()
                pred = solver.grey_forecast(data, forecast_steps=3)
                all_results[f"sub_{sp['id']}"] = {
                    "forecast": [round(v, 2) for v in pred["forecast"]],
                    "fitted": [round(v, 2) for v in pred["fitted"]],
                    "mape": pred["mape"],
                    "grade": pred["grade"],
                    "summary": f"MAPE={pred['mape']:.2f}% [{pred['grade']}]",
                }
                sp["result"] = {
                    "预测值": [round(v, 1) for v in pred["forecast"]],
                    "MAPE": f"{pred['mape']:.2f}%",
                    "精度": pred["grade"],
                }

        elif ptype == "优化" and data_dfs:
            df = _find_df(data_dfs, min_num_cols=3)
            opt = OptimizationSolver()
            numeric = df.select_dtypes(include=np.number)
            cols = numeric.columns.tolist()
            cost_col = benefit_col = None
            for c in cols:
                if any(kw in str(c) for kw in ["成本", "费用", "cost"]):
                    cost_col = c
                elif any(kw in str(c) for kw in ["覆盖", "人口", "收益", "benefit"]):
                    benefit_col = c
            if cost_col is None:
                cost_col = cols[1] if len(cols) > 1 else cols[0]
            if benefit_col is None:
                benefit_col = cols[2] if len(cols) > 2 else cols[1]

            costs = numeric[cost_col].tolist()
            benefits = numeric[benefit_col].tolist()
            c = [-b for b in benefits]
            A_ub = [costs]
            b_ub = [100]

            try:
                ip_result = opt.integer_program(c=c, A_ub=A_ub, b_ub=b_ub,
                                                 bounds=(0, 1), binary=True)
                if ip_result.success:
                    labels = df.iloc[:, 0].tolist()
                    selected = [labels[i] for i, v in enumerate(ip_result.x) if v > 0.5]
                    total_cost = sum(costs[i] for i, v in enumerate(ip_result.x) if v > 0.5)
                    total_pop = sum(benefits[i] for i, v in enumerate(ip_result.x) if v > 0.5)
                    all_results[f"sub_{sp['id']}"] = {
                        "selection": selected,
                        "total_cost": round(total_cost, 1),
                        "total_population": round(total_pop, 1),
                        "summary": f"选择 {', '.join(selected)}, 成本{total_cost:.0f}, 覆盖{total_pop:.0f}",
                    }
                    sp["result"] = {
                        "选择方案": selected,
                        "总成本": f"{total_cost:.0f}",
                        "覆盖人口": f"{total_pop:.0f}万",
                    }
            except Exception as e:
                sp["result"] = {"error": str(e)}

    set_step(3, "done", f"完成 {sum(1 for v in all_results.values() if isinstance(v, dict))} 个子问题求解")

    # ---- Step 5: 灵敏度 ----
    set_step(4, "running", "检验模型鲁棒性…")
    time.sleep(0.3)

    sa = SensitivityAnalyzer()
    for key, value in all_results.items():
        if "fitted" in value and len(value["fitted"]) >= 4:
            def gm_model(params):
                s = StatsSolver()
                r = s.grey_forecast(params.tolist(), forecast_steps=3)
                return float(r["forecast"][-1]) if r["forecast"] else 0

            robust = sa.robustness_check(gm_model, value["fitted"], noise_pct=0.05, n_samples=300)
            value["sensitivity"] = {"cv": robust["cv"], "is_robust": robust["is_robust"]}

    set_step(4, "done", f"CV={robust.get('cv', 0):.4f}" if robust else "完成")

    # ---- Step 6: 图表 ----
    set_step(5, "running", "绘制图表…")
    time.sleep(0.3)

    fig_dir = output_dir / "figures"
    fig_dir.mkdir(exist_ok=True)
    set_style("zh")
    plotter = Plotter(language="zh")

    for key, value in all_results.items():
        if "scores" in value and "labels" in value:
            fig, ax = plotter.bar(x=value["labels"], y=value["scores"],
                                  xlabel="方案", ylabel="得分",
                                  title="TOPSIS 综合评价得分", labels=value["labels"])
            plotter.save(fig, fig_dir / "topsis_scores.pdf")
        if "forecast" in value and "fitted" in value:
            n = len(value["fitted"])
            all_y = value["fitted"] + value["forecast"]
            x = list(range(len(all_y)))
            fig, ax = plotter.line(x=x, y=all_y, xlabel="时间", ylabel="值",
                                   title="灰色预测结果", markers=True)
            plotter.save(fig, fig_dir / "forecast.pdf")

    plotter.close_all()
    set_step(5, "done", f"生成 {len(list(fig_dir.glob('*.pdf')))} 张图表")

    # ---- Step 7: 论文 ----
    set_step(6, "running", "撰写 Word 论文…")
    time.sleep(0.3)

    paper_path = generate_paper(
        output_path=str(output_dir / "论文.docx"),
        problem_text=problem_text,
        analysis={"sub_problems": analyzed},
        recommendations=[{
            "summary": " → ".join(a["model"] for a in analyzed),
            "confidence": sum(a["score"] for a in analyzed) / max(len(analyzed), 1),
            "sub_problems": analyzed,
        }],
        results=all_results,
        figures_dir=str(fig_dir),
    )

    set_step(6, "done", "论文生成完成")

    update_progress(1.0, steps)

    return {
        "sub_problems": analyzed,
        "results": all_results,
        "paper_path": str(paper_path),
    }


def _find_df(data_dfs, min_num_cols=2, max_num_cols=99, min_rows=2):
    """智能选择数据表"""
    for name, df in data_dfs.items():
        num_cols = df.select_dtypes(include=np.number).shape[1]
        if min_num_cols <= num_cols <= max_num_cols and df.shape[0] >= min_rows:
            return df
    return list(data_dfs.values())[0] if data_dfs else pd.DataFrame()


def _ai_recommend(text, classification, candidates, api_config):
    """调用 AI API 增强模型推荐"""
    import urllib.request
    import urllib.error

    provider = api_config.get("provider", "OpenAI")
    key = api_config.get("key", "")
    base = api_config.get("base", "")
    model = api_config.get("model", "")

    # 设置默认值
    if not model:
        if provider == "Anthropic (Claude)":
            model = "claude-sonnet-5"
        elif provider == "DeepSeek":
            model = "deepseek-chat"
        else:
            model = "gpt-4o"

    if not base:
        if provider == "Anthropic (Claude)":
            base = "https://api.anthropic.com/v1"
        elif provider == "DeepSeek":
            base = "https://api.deepseek.com/v1"
        else:
            base = "https://api.openai.com/v1"

    prompt = f"""你是一个数学建模竞赛专家。分析以下子问题并推荐最佳模型。

子问题: {text[:300]}
已分类题型: {classification['type']} (置信度: {classification['confidence']:.1%})
知识库候选模型: {json.dumps(candidates, ensure_ascii=False)}

请以 JSON 格式返回推荐结果:
{{"recommended_model": "模型名", "reason": "推荐理由"}}"""

    # OpenAI 兼容格式
    messages = [{"role": "user", "content": prompt}]
    url = f"{base.rstrip('/')}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }
    body = json.dumps({"model": model, "messages": messages, "temperature": 0.3}).encode()

    try:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            content = data["choices"][0]["message"]["content"]
            # 尝试解析 JSON
            ai_result = json.loads(content)
            # 与知识库候选合并
            return [{
                "model": ai_result.get("recommended_model", candidates[0]["model"]),
                "score": 0.98,
                "reason": ai_result.get("reason", ""),
                "solver_path": candidates[0].get("solver_path", ""),
            }] + candidates[1:]
    except Exception:
        return None


# ============================================================
# 按钮回调
# ============================================================
if start_btn:
    if not problem_file:
        st.error("请上传赛题文件")
    else:
        st.session_state.solving = True
        st.session_state.results = None
        st.session_state.paper_path = None

        # 读取文件
        problem_content = ""
        try:
            if problem_file.name.endswith(".txt"):
                problem_content = problem_file.read().decode("utf-8")
            elif problem_file.name.endswith(".pdf"):
                try:
                    import pdfplumber
                    with pdfplumber.open(problem_file) as pdf:
                        problem_content = "\n\n".join(
                            p.extract_text() or "" for p in pdf.pages
                        )
                except ImportError:
                    problem_content = f"[PDF: {problem_file.name}]\n需要安装 pdfplumber 解析。\n请上传 TXT 格式的题目文件。"
            elif problem_file.name.endswith(".docx"):
                try:
                    from docx import Document
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
                    tmp.write(problem_file.read())
                    tmp.close()
                    doc = Document(tmp.name)
                    problem_content = "\n\n".join(p.text for p in doc.paragraphs)
                    os.unlink(tmp.name)
                except ImportError:
                    problem_content = f"[DOCX: {problem_file.name}]\n需要安装 python-docx 解析。"
        except Exception as e:
            problem_content = f"读取文件出错: {e}"

        # 读取数据
        data_dfs = {}
        for df_file in data_files or []:
            try:
                if df_file.name.endswith(".csv"):
                    data_dfs[df_file.name] = pd.read_csv(df_file)
                else:
                    data_dfs[df_file.name] = pd.read_excel(df_file)
            except Exception as e:
                st.warning(f"读取 {df_file.name} 失败: {e}")

        # API 配置
        api_config = {
            "enabled": use_api and bool(api_key),
            "provider": api_provider,
            "key": api_key,
            "base": api_base,
            "model": api_model,
        }

        # 运行
        try:
            results = run_pipeline(problem_content, data_dfs, api_config)
            st.session_state.results = results
            st.session_state.paper_path = results["paper_path"]
            st.session_state.solving = False
            st.rerun()
        except Exception as e:
            st.session_state.solving = False
            import traceback
            st.error(f"求解出错: {e}\n\n```\n{traceback.format_exc()}\n```")

if stop_btn:
    st.session_state.solving = False
