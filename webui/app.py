"""MathModel Toolkit Web UI.

基于 Streamlit 的交互式 Web 界面，提供：
- 题目文件上传（PDF/DOCX）
- 数据附件上传（XLSX/CSV）
- 实时进度展示
- 论文预览和下载
"""

import sys
import json
import time
from pathlib import Path

import streamlit as st

# 将项目根目录加入路径
sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(
    page_title="MathModel Toolkit",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🚀 MathModel Toolkit")
st.markdown("### 数学建模竞赛全自动求解器 — *上传题目，一键生成论文*")

# ---- Sidebar 配置 ----
with st.sidebar:
    st.header("⚙️ 配置")

    engine = st.selectbox("论文引擎", ["latex", "typst"], index=0)
    contest_type = st.selectbox("比赛类型", ["auto", "cumcm", "mcm"], index=0)
    auto_confirm = st.checkbox("自动确认模型推荐", value=True)
    save_intermediate = st.checkbox("保存中间结果", value=True)

    st.divider()

    if st.button("🚀 开始求解", type="primary", use_container_width=True):
        st.session_state["started"] = True

# ---- 主区域 ----
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📄 题目文件")
    problem_file = st.file_uploader(
        "上传赛题文件（PDF/DOCX/TXT）",
        type=["pdf", "docx", "txt"],
        key="problem",
    )

with col2:
    st.subheader("📊 数据附件")
    data_files = st.file_uploader(
        "上传数据文件（XLSX/CSV）",
        type=["xlsx", "xls", "csv"],
        accept_multiple_files=True,
        key="data",
    )

# ---- 进度区域 ----
if st.session_state.get("started") and problem_file:
    st.divider()
    st.subheader("📈 求解进度")

    progress_bar = st.progress(0, text="准备中…")
    status_area = st.empty()

    try:
        from mathmodel.pipeline import Pipeline, PipelineConfig

        config = PipelineConfig(
            engine=engine,
            contest_type=contest_type,
            auto_select_model=auto_confirm,
            save_intermediate=save_intermediate,
            output_dir="./webui_output",
        )

        # 保存上传的文件
        tmp_dir = Path("./webui_output/uploads")
        tmp_dir.mkdir(parents=True, exist_ok=True)

        problem_path = tmp_dir / problem_file.name
        problem_path.write_bytes(problem_file.getbuffer())

        data_paths = []
        for df in data_files:
            dp = tmp_dir / df.name
            dp.write_bytes(df.getbuffer())
            data_paths.append(str(dp))

        pipe = Pipeline(config=config)

        # 运行并更新进度
        def update_progress():
            while not pipe.tracker.is_complete:
                p = pipe.tracker.overall_progress
                progress_bar.progress(p, text=f"总进度: {p*100:.0f}%")
                # 显示阶段详情
                lines = []
                for stage_id in pipe.tracker._stage_order:
                    stage = pipe.tracker.stages[stage_id]
                    icon = {
                        "pending": "⏳", "running": "🔄",
                        "completed": "✅", "failed": "❌",
                    }.get(stage.status.value, "❓")
                    elapsed = stage.elapsed
                    lines.append(
                        f"{icon} **{stage.name}** "
                        f"[{elapsed:.0f}s] {stage.message}"
                    )
                    for sub in stage.sub_steps:
                        sub_icon = {
                            "pending": "⏳", "running": "🔄",
                            "completed": "✅", "failed": "❌",
                        }.get(sub.status.value, "❓")
                        if sub.status.value == "running":
                            lines.append(f"  {sub_icon} _{sub.name}_ ↻")
                        else:
                            lines.append(f"  {sub_icon} {sub.name}")
                status_area.markdown("\n".join(lines))
                time.sleep(0.5)

        import threading
        thread = threading.Thread(target=update_progress, daemon=True)
        thread.start()

        pipe.run(
            problem=str(problem_path),
            data=data_paths if data_paths else None,
            auto_confirm=auto_confirm,
        )

        progress_bar.progress(1.0, text="✅ 完成！")
        pipe.export()

        # ---- 结果展示 ----
        st.divider()
        st.subheader("📥 生成结果")

        paper_path = pipe.get_paper()
        if paper_path and paper_path.exists() and paper_path.suffix == ".pdf":
            with open(paper_path, "rb") as f:
                st.download_button(
                    "📕 下载论文 PDF",
                    data=f,
                    file_name="paper.pdf",
                    mime="application/pdf",
                )
            st.success(f"论文已生成: {paper_path}")

        # 推荐方案
        if pipe.recommendations:
            st.subheader("🧠 模型推荐方案")
            for rec in pipe.recommendations:
                st.info(
                    f"**方案**: {rec.get('summary', '')}\n\n"
                    f"**置信度**: {rec.get('confidence', 0):.1%}"
                )
                for sp in rec.get("sub_problems", []):
                    st.markdown(
                        f"- 子问题{sp['id']}: **{sp['model']}** "
                        f"(分数: {sp.get('score', 0):.2f}) — {sp.get('reason', '')}"
                    )

    except Exception as e:
        st.error(f"求解失败: {e}")
        import traceback
        st.code(traceback.format_exc())
else:
    st.info("👆 上传题目文件后，点击「开始求解」启动自动建模流水线")
