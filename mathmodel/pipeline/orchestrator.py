"""核心流水线调度器。

负责端到端协调：文档解析 → 题目分析 → 模型推荐 → 模型求解 → 图表生成 → 论文撰写。
每个阶段可独立运行，也可全自动串联执行。
"""

from __future__ import annotations

import json
import shutil
import threading
from pathlib import Path
from typing import Optional

from mathmodel.pipeline.config import PipelineConfig, get_default_config
from mathmodel.pipeline.progress import (
    ProgressTracker,
    StageStatus,
)
from mathmodel.utils.helpers import ensure_dir, get_logger, set_seed, Timer

logger = get_logger("mathmodel.pipeline")

# ---- 阶段定义 ---------------------------------------------------------------

STAGES = [
    ("parse", "文档解析", 0.10),
    ("analyze", "题目分析", 0.10),
    ("recommend", "模型推荐", 0.10),
    ("solve", "模型求解", 0.35),
    ("visualize", "图表生成", 0.15),
    ("paper", "论文撰写", 0.20),
]


class Pipeline:
    """数学建模全自动求解流水线。

    使用方式::

        # 一键运行
        pipe = Pipeline()
        pipe.run(problem="赛题.pdf", data="附件.xlsx")

        # 分步运行
        pipe = Pipeline()
        pipe.parse("赛题.pdf", "附件.xlsx")
        pipe.analyze()
        pipe.recommend()
        pipe.solve()
        pipe.visualize()
        pipe.write_paper()
        pipe.export("./output")

        # 从中间某步恢复
        pipe.resume("./output")

    Attributes:
        config: 流水线配置
        tracker: 进度追踪器
        output_dir: 当前运行的输出目录
        problem_text: 解析后的题目文本
        problem_data: 解析后的数据摘要
        analysis: 题目分析结果
        recommendations: 模型推荐结果
        results: 模型求解结果
        paper_path: 论文输出路径
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Args:
            config: 流水线配置，为 None 时使用全局默认配置
        """
        self.config = config or get_default_config()
        set_seed(self.config.random_seed)

        self.tracker = ProgressTracker(total_stages=len(STAGES))
        self.output_dir: Optional[Path] = None

        # ---- 各阶段产出 -------------------------------------------------
        self.problem_text: str = ""
        self.problem_data: dict = {}
        self.sub_problems: list[dict] = []

        self.analysis: dict = {}
        self.data_profiles: dict = {}

        self.recommendations: list[dict] = []

        self.results: dict = {}

        self.paper_path: Optional[Path] = None

        # ---- 内部状态 ---------------------------------------------------
        self._lock = threading.Lock()
        self._aborted = False

    # =====================================================================
    # 一键运行
    # =====================================================================

    def run(
        self,
        problem: str | Path,
        data: Optional[str | Path | list[str]] = None,
        output_dir: Optional[str | Path] = None,
        *,
        auto_confirm: bool = True,
    ) -> "Pipeline":
        """全自动执行求解流水线。

        Args:
            problem: 题目文件路径（PDF/DOCX）
            data: 数据附件路径（XLSX/CSV 等），可以是单个路径或路径列表
            output_dir: 输出目录（覆盖配置中的设置）
            auto_confirm: 是否自动确认模型推荐方案（False 时会暂停等待用户确认）

        Returns:
            self，支持链式调用
        """
        if output_dir:
            self.config.output_dir = str(output_dir)

        self.output_dir = Path(self.config.output_dir)
        ensure_dir(self.output_dir)

        # 启用 JSON 进度输出
        self.tracker.enable_json(self.output_dir / "progress.json")

        try:
            # ---- Stage 1: 文档解析 ----
            self.parse(problem, data)

            # ---- Stage 2: 题目分析 ----
            self.analyze()

            # ---- Stage 3: 模型推荐 ----
            self.recommend()

            if auto_confirm or self.config.auto_select_model:
                logger.info("自动确认模型推荐方案")
            else:
                self._wait_for_confirmation()

            # ---- Stage 4: 模型求解 ----
            self.solve()

            # ---- Stage 5: 图表生成 ----
            self.visualize()

            # ---- Stage 6: 论文生成 ----
            self.write_paper()

            # ---- 打印摘要 ----
            self._print_summary()

        except Exception as e:
            logger.error(f"流水线执行失败: {e}")
            self.tracker._write_json()
            raise

        return self

    # =====================================================================
    # Stage 1: 文档解析
    # =====================================================================

    def parse(
        self,
        problem: str | Path,
        data: Optional[str | Path | list[str]] = None,
    ) -> dict:
        """解析题目文件和附件数据。

        Args:
            problem: 题目 PDF/DOCX 路径
            data: 数据附件路径（可选）

        Returns:
            dict: 解析结果 {"problem_text": ..., "data_summary": ...}
        """
        stage_id = "parse"
        self.tracker.start_stage(stage_id, "文档解析", weight=0.10)

        try:
            problem_path = Path(problem)
            if not problem_path.exists():
                raise FileNotFoundError(f"题目文件不存在: {problem_path}")

            # 解析题目文本
            self.tracker.start_sub_step(stage_id, "题目文本提取")
            self.problem_text = _parse_problem_file(problem_path)
            self.tracker.complete_sub_step(
                stage_id, "题目文本提取",
                f"提取完成，{len(self.problem_text)} 字符"
            )

            # 加载附件数据
            if data:
                self.tracker.start_sub_step(stage_id, "附件数据加载")
                data_paths = data if isinstance(data, list) else [data]
                self.problem_data = _load_data_files(data_paths)
                self.tracker.complete_sub_step(
                    stage_id, "附件数据加载",
                    f"加载完成，{len(self.problem_data)} 个数据表"
                )
            else:
                self.tracker.add_sub_step(stage_id, "附件数据加载", StageStatus.SKIPPED)

            # 拆分子问题
            self.tracker.start_sub_step(stage_id, "子问题拆分")
            self.sub_problems = _split_problems(self.problem_text)
            self.tracker.complete_sub_step(
                stage_id, "子问题拆分",
                f"识别到 {len(self.sub_problems)} 个子问题"
            )

            self.tracker.complete_stage(stage_id)

        except Exception as e:
            self.tracker.fail_stage(stage_id, str(e))
            raise

        print(self.tracker.render_rich())
        return {"problem_text": self.problem_text, "data_summary": self.problem_data}

    # =====================================================================
    # Stage 2: 题目分析
    # =====================================================================

    def analyze(self) -> dict:
        """分析题目，识别题型和数据特征。

        Returns:
            dict: 分析结果 {"sub_problems": [...], "data_profiles": {...}}
        """
        stage_id = "analyze"
        self.tracker.start_stage(stage_id, "题目分析", weight=0.10)

        try:
            self.tracker.start_sub_step(stage_id, "题型分类")
            self.analysis = _classify_problems(self.sub_problems, self.problem_data)
            self.tracker.complete_sub_step(
                stage_id, "题型分类",
                f"分类完成: {self._format_classification()}"
            )

            self.tracker.start_sub_step(stage_id, "数据画像")
            self.data_profiles = _profile_data(self.problem_data)
            self.tracker.complete_sub_step(
                stage_id, "数据画像",
                f"分析 {len(self.data_profiles)} 个数据表特征"
            )

            self.tracker.complete_stage(stage_id)

        except Exception as e:
            self.tracker.fail_stage(stage_id, str(e))
            raise

        print(self.tracker.render_rich())
        return self.analysis

    def _format_classification(self) -> str:
        """格式化题型分类结果。"""
        if not self.analysis:
            return "无"
        parts = []
        for sp in self.analysis.get("sub_problems", []):
            ptype = sp.get("type", "未知")
            parts.append(f"子问题{sp.get('id','?')}: {ptype}")
        return ", ".join(parts)

    # =====================================================================
    # Stage 3: 模型推荐
    # =====================================================================

    def recommend(self) -> list[dict]:
        """基于分析结果推荐最优模型。

        Returns:
            list[dict]: 推荐方案列表，每个方案包含模型、置信度、理由
        """
        stage_id = "recommend"
        self.tracker.start_stage(stage_id, "模型推荐", weight=0.10)

        try:
            self.tracker.start_sub_step(stage_id, "候选模型检索")
            recs = _recommend_models(
                self.analysis,
                self.data_profiles,
                top_k=self.config.top_k_models,
            )
            self.tracker.complete_sub_step(
                stage_id, "候选模型检索",
                f"检索到 {len(recs)} 个候选方案"
            )

            self.tracker.start_sub_step(stage_id, "方案排序")
            self.recommendations = _rank_recommendations(recs, self.config)
            self.tracker.complete_sub_step(
                stage_id, "方案排序",
                f"最佳方案: {self._format_recommendation()}"
            )

            self.tracker.complete_stage(stage_id)

        except Exception as e:
            self.tracker.fail_stage(stage_id, str(e))
            raise

        # 保存推荐结果
        self._save_intermediate("recommendations.json", self.recommendations)

        print(self.tracker.render_rich())
        return self.recommendations

    def _format_recommendation(self) -> str:
        """格式化推荐方案摘要。"""
        if not self.recommendations:
            return "无"
        top = self.recommendations[0]
        return f"置信度 {top.get('confidence', 0):.1%} — {top.get('summary', '')}"

    # =====================================================================
    # Stage 4: 模型求解
    # =====================================================================

    def solve(self) -> dict:
        """执行模型求解。

        自动为每个子问题编写求解代码、运行、验证。

        Returns:
            dict: 求解结果，按子问题组织
        """
        stage_id = "solve"
        self.tracker.start_stage(stage_id, "模型求解", weight=0.35)

        try:
            self.tracker.start_sub_step(stage_id, "数据预处理")
            preprocessed = _run_preprocessing(
                self.problem_data, self.data_profiles
            )
            self.tracker.complete_sub_step(stage_id, "数据预处理", "完成")

            self.results = {}
            recs = self.recommendations
            if not recs:
                recs = [{}]  # fallback

            # 取第一个方案（最优方案）进行求解
            top_plan = recs[0]
            sub_models = top_plan.get("sub_problems", [])

            for i, sm in enumerate(sub_models):
                sub_id = sm.get("id", i + 1)
                sub_name = f"子问题{sub_id}: {sm.get('model', '未知模型')}"
                self.tracker.start_sub_step(stage_id, sub_name)

                try:
                    result = _solve_sub_problem(
                        sub_id=sub_id,
                        model_info=sm,
                        data=preprocessed,
                        config=self.config,
                        output_dir=self.output_dir,
                    )
                    self.results[f"sub_{sub_id}"] = result
                    self.tracker.complete_sub_step(stage_id, sub_name, result.get("summary", ""))
                except Exception as e:
                    logger.warning(f"子问题 {sub_id} 求解失败: {e}")
                    self.tracker.fail_sub_step(stage_id, sub_name, str(e))
                    self.results[f"sub_{sub_id}"] = {"error": str(e)}

            self.tracker.complete_stage(stage_id)

        except Exception as e:
            self.tracker.fail_stage(stage_id, str(e))
            raise

        self._save_intermediate("results.json", self.results)
        print(self.tracker.render_rich())
        return self.results

    # =====================================================================
    # Stage 5: 图表生成
    # =====================================================================

    def visualize(self) -> dict:
        """生成论文所需的所有图表。

        Returns:
            dict: 图表列表及路径
        """
        stage_id = "visualize"
        self.tracker.start_stage(stage_id, "图表生成", weight=0.15)

        try:
            fig_dir = self.output_dir / self.config.figures_dir
            ensure_dir(fig_dir)

            self.tracker.start_sub_step(stage_id, "数据驱动图表")
            data_figures = _generate_data_figures(
                self.results, self.problem_data, fig_dir, self.config
            )
            self.tracker.complete_sub_step(
                stage_id, "数据驱动图表",
                f"生成 {len(data_figures)} 张图表"
            )

            self.tracker.start_sub_step(stage_id, "流程图/技术路线")
            diagram_figures = _generate_diagrams(
                self.analysis, self.recommendations, fig_dir
            )
            self.tracker.complete_sub_step(
                stage_id, "流程图/技术路线",
                f"生成 {len(diagram_figures)} 张流程图"
            )

            figures = {**data_figures, **diagram_figures}
            self._save_intermediate("figures.json", figures)
            self.tracker.complete_stage(stage_id)

        except Exception as e:
            self.tracker.fail_stage(stage_id, str(e))
            raise

        print(self.tracker.render_rich())
        return figures

    # =====================================================================
    # Stage 6: 论文生成
    # =====================================================================

    def write_paper(self) -> Path:
        """撰写并编译论文。

        Returns:
            Path: 生成的 PDF 路径
        """
        stage_id = "paper"
        self.tracker.start_stage(stage_id, "论文撰写", weight=0.20)

        try:
            self.tracker.start_sub_step(stage_id, "章节撰写")
            tex_content = _compose_paper(
                problem_text=self.problem_text,
                analysis=self.analysis,
                recommendations=self.recommendations,
                results=self.results,
                figures_dir=self.config.figures_dir,
                config=self.config,
            )
            self.tracker.complete_sub_step(stage_id, "章节撰写", f"{len(tex_content)} 字符")

            self.tracker.start_sub_step(stage_id, "LaTeX 编译")
            self.paper_path = _compile_paper(
                tex_content=tex_content,
                output_dir=self.output_dir,
                config=self.config,
            )
            self.tracker.complete_sub_step(
                stage_id, "LaTeX 编译",
                f"编译完成: {self.paper_path}"
            )

            self.tracker.complete_stage(stage_id)

        except Exception as e:
            self.tracker.fail_stage(stage_id, str(e))
            raise

        # 复制一份到输出目录根
        final_path = self.output_dir / "paper.pdf"
        if self.paper_path and self.paper_path != final_path:
            shutil.copy2(self.paper_path, final_path)

        print(self.tracker.render_rich())
        return self.paper_path or final_path

    # =====================================================================
    # 导出 & 恢复
    # =====================================================================

    def export(self, output_dir: Optional[str | Path] = None) -> Path:
        """导出完整成果包（论文 PDF + 代码 + 数据 + 图表）。

        Args:
            output_dir: 导出目录，默认使用配置中的 output_dir

        Returns:
            Path: 导出目录路径
        """
        out = Path(output_dir or self.config.output_dir)
        ensure_dir(out)

        # 导出进度摘要
        with open(out / "summary.json", "w", encoding="utf-8") as f:
            json.dump(self.tracker.to_dict(), f, ensure_ascii=False, indent=2)

        # 导出配置
        self.config.to_file(out / "config.yaml")

        logger.info(f"成果已导出到: {out}")
        return out

    def resume(self, output_dir: str | Path) -> "Pipeline":
        """从已有的输出目录恢复流水线状态。

        可用于中断后继续执行。

        Args:
            output_dir: 已有运行的输出目录

        Returns:
            self
        """
        out = Path(output_dir)
        if not out.exists():
            raise FileNotFoundError(f"输出目录不存在: {out}")

        # 读取已保存的中间结果
        for file_name, attr in [
            ("recommendations.json", "recommendations"),
            ("results.json", "results"),
        ]:
            fpath = out / file_name
            if fpath.exists():
                with open(fpath, "r", encoding="utf-8") as f:
                    setattr(self, attr, json.load(f))

        self.output_dir = out
        logger.info(f"已从 {out} 恢复状态")
        return self

    # =====================================================================
    # 内部辅助
    # =====================================================================

    def _save_intermediate(self, filename: str, data) -> None:
        """保存中间结果到 JSON 文件。"""
        if not self.config.save_intermediate or not self.output_dir:
            return
        fpath = self.output_dir / filename
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def _wait_for_confirmation(self) -> None:
        """等待用户确认模型推荐方案。"""
        print("\n" + "=" * 60)
        print("📋 模型推荐方案，请确认：")
        for i, rec in enumerate(self.recommendations):
            confidence = rec.get("confidence", 0)
            summary = rec.get("summary", "")
            print(f"  [{i+1}] {summary} (置信度: {confidence:.1%})")
        print("  输入方案编号确认，或输入 'q' 退出")
        print("=" * 60)
        # 在非交互模式下自动选择方案 1
        choice = input("> ").strip()
        if choice.lower() == "q":
            self._aborted = True
            raise KeyboardInterrupt("用户取消")
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(self.recommendations):
                self.recommendations = [self.recommendations[idx]]

    def _print_summary(self) -> None:
        """打印最终摘要。"""
        print("\n" + "=" * 60)
        print("🎉 流水线执行完成！")
        print(f"   论文: {self.output_dir / 'paper.pdf'}")
        print(f"   总耗时: {self.tracker.summary()}")
        print("=" * 60)

    def get_paper(self) -> Optional[Path]:
        """获取生成的论文 PDF 路径。"""
        if self.paper_path and Path(self.paper_path).exists():
            return Path(self.paper_path)
        if self.output_dir:
            p = self.output_dir / "paper.pdf"
            if p.exists():
                return p
        return None


# =========================================================================
# 占位实现 — 后续阶段逐步替换为完整实现
# =========================================================================

def _parse_problem_file(path: Path) -> str:
    """解析题目文件（PDF/DOCX）。"""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        try:
            import pdfplumber
            text_parts = []
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text_parts.append(t)
            return "\n\n".join(text_parts)
        except ImportError:
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(path)
                text_parts = [page.get_text() for page in doc]
                doc.close()
                return "\n\n".join(text_parts)
            except ImportError:
                raise ImportError(
                    "需要安装 PDF 解析库: pip install mathmodel-toolkit[pdf]"
                )
    elif suffix == ".docx":
        try:
            from docx import Document
            doc = Document(path)
            return "\n\n".join(p.text for p in doc.paragraphs)
        except ImportError:
            raise ImportError("需要安装 python-docx: pip install python-docx")
    elif suffix == ".txt":
        return path.read_text(encoding="utf-8")
    else:
        raise ValueError(f"不支持的文件格式: {suffix}")


def _load_data_files(paths: list[str | Path]) -> dict:
    """加载数据附件文件。"""
    import pandas as pd

    data = {}
    for p in paths:
        p = Path(p)
        if not p.exists():
            logger.warning(f"数据文件不存在: {p}")
            continue
        suffix = p.suffix.lower()
        key = p.stem
        if suffix in (".xlsx", ".xls"):
            # Excel 可能有多个 sheet
            xl = pd.ExcelFile(p)
            if len(xl.sheet_names) == 1:
                data[key] = pd.read_excel(p)
            else:
                for sheet in xl.sheet_names:
                    data[f"{key}_{sheet}"] = pd.read_excel(p, sheet_name=sheet)
        elif suffix == ".csv":
            data[key] = pd.read_csv(p)
        elif suffix in (".json",):
            import json as _json
            with open(p, "r", encoding="utf-8") as f:
                data[key] = _json.load(f)
        elif suffix == ".txt":
            data[key] = p.read_text(encoding="utf-8")
        elif suffix == ".mat":
            try:
                from scipy.io import loadmat
                data[key] = loadmat(str(p))
            except ImportError:
                logger.warning(f"无法读取 .mat 文件: {p}")
        else:
            logger.warning(f"不支持的数据格式: {suffix}")
    return data


def _split_problems(text: str) -> list[dict]:
    """从题目文本中拆分子问题。

    基于常见的题目标记模式：
    - 「问题一」「问题1」「问题 1」
    - 「Problem 1」「Question 1」
    - 「(1)」「1.」
    """
    import re

    # 匹配子问题标题的模式
    patterns = [
        r"(?:问题|第)\s*([一二三四五六七八九十\d]+)\s*[：:\.\、\）\)]",
        r"(?:问题|第)\s*([一二三四五六七八九十\d]+)\s*(?:部分|题)",
        r"(?:Problem|Question)\s*(\d+)",
        r"\((\d+)\)",
        r"^(\d+)[\.\、]",
    ]

    sub_problems = []
    lines = text.split("\n")

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        for pat in patterns:
            m = re.search(pat, line)
            if m:
                # 收集该子问题下的内容（直到下一个子问题标题）
                sub_problems.append({
                    "id": len(sub_problems) + 1,
                    "title": line[:100],
                    "line_index": i,
                })
                break

    # 如果没找到子问题，整体作为一个问题
    if not sub_problems:
        sub_problems = [{"id": 1, "title": "完整问题", "line_index": 0}]

    return sub_problems


def _classify_problems(sub_problems: list[dict], data: dict) -> dict:
    """题型分类 — 基于关键词和规则。"""
    import re

    # 题型关键词映射
    TYPE_KEYWORDS = {
        "优化": ["优化", "最优", "最大", "最小", "极小", "极大", "目标函数",
                 "约束", "线性规划", "非线性", "整数规划", "调度", "分配"],
        "预测": ["预测", "预报", "趋势", "未来", "走势", "估计", "推测"],
        "评价": ["评价", "评估", "打分", "排名", "优劣", "综合", "指标",
                 "权重", "等级", "绩效"],
        "分类": ["分类", "识别", "判别", "诊断", "聚类"],
        "微分方程": ["微分方程", "动力系统", "变化率", "导数", "传播",
                     "扩散", "传染", "种群"],
        "统计": ["回归", "相关", "检验", "假设", "显著性", "分布",
                 "方差", "均值"],
        "图论": ["路径", "网络", "最短", "连通", "遍历", "流", "节点",
                 "边"],
    }

    classified = []
    for sp in sub_problems:
        title = sp.get("title", "")
        content = sp.get("content", "")
        # 文本中搜索子问题相关内容（标题+正文）
        full_text = title + " " + content
        scores = {}
        for ptype, keywords in TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in full_text)
            if score > 0:
                scores[ptype] = score

        if scores:
            best_type = max(scores, key=scores.get)
        else:
            best_type = "综合"  # 无法明确分类

        classified.append({
            "id": sp["id"],
            "title": sp["title"],
            "content": sp.get("content", ""),
            "type": best_type,
            "type_scores": scores,
        })

    return {
        "sub_problems": classified,
        "data_tables": list(data.keys()),
        "total_sub_problems": len(classified),
    }


def _profile_data(data: dict) -> dict:
    """生成数据画像 — 各数据表的基本统计特征。"""
    import pandas as pd

    profiles = {}
    for name, df in data.items():
        if not isinstance(df, pd.DataFrame):
            profiles[name] = {"type": type(df).__name__}
            continue

        profile = {
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": {c: str(t) for c, t in df.dtypes.items()},
            "missing_count": int(df.isnull().sum().sum()),
            "missing_pct": round(float(df.isnull().sum().sum() / df.size * 100), 2),
            "numeric_cols": df.select_dtypes(include="number").columns.tolist(),
            "categorical_cols": df.select_dtypes(include="object").columns.tolist(),
        }

        # 数值列的基础统计
        num_cols = profile["numeric_cols"]
        if num_cols:
            profile["numeric_stats"] = df[num_cols].describe().to_dict()

        profiles[name] = profile

    return profiles


def _recommend_models(analysis: dict, data_profiles: dict, top_k: int = 3) -> list[dict]:
    """模型推荐引擎。

    基于题型分类和数据特征从知识库中检索匹配模型并打分。
    """
    from mathmodel.analyzer.knowledge_base import get_knowledge_base
    kb = get_knowledge_base()

    sub_problems = analysis.get("sub_problems", [])
    plans = []

    for sp in sub_problems:
        ptype = sp.get("type", "综合")
        type_scores = sp.get("type_scores", {})

        # 从知识库匹配
        candidates = kb.query(
            problem_type=ptype,
            data_profiles=data_profiles,
            top_k=top_k,
        )

        # 如果当前类型无结果，尝试其他高分类别
        if not candidates and ptype == "综合" and type_scores:
            for alt_type, alt_score in sorted(type_scores.items(), key=lambda x: -x[1]):
                if alt_type != "综合":
                    candidates = kb.query(
                        problem_type=alt_type,
                        data_profiles=data_profiles,
                        top_k=top_k,
                    )
                    if candidates:
                        ptype = alt_type  # 使用有结果的类型
                        break

        # 最终兜底：尝试所有主要类型
        if not candidates:
            for fallback_type in ["评价", "预测", "优化", "统计", "分类"]:
                candidates = kb.query(
                    problem_type=fallback_type,
                    data_profiles=data_profiles,
                    top_k=top_k,
                )
                if candidates:
                    ptype = fallback_type
                    break

        plans.append({
            "sub_problem_id": sp["id"],
            "title": sp.get("title", ""),
            "problem_type": ptype,
            "candidates": candidates,
            "recommended": candidates[0] if candidates else None,
        })

    # 组装方案
    best_plan = {
        "summary": " → ".join(
            f"{p['recommended']['model']}" if p['recommended']
            else "?"
            for p in plans
        ),
        "confidence": sum(
            p["recommended"]["score"] if p["recommended"] else 0
            for p in plans
        ) / max(len(plans), 1),
        "sub_problems": [
            {
                "id": p["sub_problem_id"],
                "title": p["title"],
                "model": p["recommended"]["model"] if p["recommended"] else "待定",
                "score": p["recommended"]["score"] if p["recommended"] else 0,
                "reason": p["recommended"]["reason"] if p["recommended"] else "",
            }
            for p in plans
        ],
    }

    return [best_plan]


def _rank_recommendations(recommendations: list[dict],
                          config: PipelineConfig) -> list[dict]:
    """对推荐方案排序（按置信度降序）。"""
    return sorted(recommendations, key=lambda r: r.get("confidence", 0), reverse=True)


def _run_preprocessing(data: dict, data_profiles: dict) -> dict:
    """执行数据预处理。"""
    import pandas as pd

    processed = {}
    for name, df in data.items():
        if not isinstance(df, pd.DataFrame):
            processed[name] = df
            continue

        df = df.copy()

        # 缺失值处理：数值列用中位数填充，分类列用众数
        profile = data_profiles.get(name, {})
        num_cols = profile.get("numeric_cols", [])
        cat_cols = profile.get("categorical_cols", [])

        for col in num_cols:
            if col in df.columns and df[col].isnull().any():
                df[col] = df[col].fillna(df[col].median())

        for col in cat_cols:
            if col in df.columns and df[col].isnull().any():
                mode = df[col].mode()
                if not mode.empty:
                    df[col] = df[col].fillna(mode[0])

        processed[name] = df

    return processed


def _solve_sub_problem(
    sub_id: int,
    model_info: dict,
    data: dict,
    config: PipelineConfig,
    output_dir: Optional[Path],
) -> dict:
    """求解单个子问题。

    根据模型信息调度对应的求解器。
    """
    model_name = model_info.get("model", "")
    logger.info(f"求解子问题 {sub_id}: {model_name}")

    # TODO: Phase 4 中实现完整的求解调度
    return {
        "sub_problem_id": sub_id,
        "model": model_name,
        "status": "placeholder",
        "summary": f"[{model_name}] 求解占位 — 将在 Phase 4 实现完整求解逻辑",
    }


def _generate_data_figures(
    results: dict,
    data: dict,
    fig_dir: Path,
    config: PipelineConfig,
) -> dict:
    """生成数据驱动图表。"""
    # TODO: Phase 6 中实现完整的图表生成
    return {}


def _generate_diagrams(
    analysis: dict,
    recommendations: list[dict],
    fig_dir: Path,
) -> dict:
    """生成流程图和技术路线图。"""
    # TODO: Phase 6 中实现
    return {}


def _compose_paper(
    problem_text: str,
    analysis: dict,
    recommendations: list[dict],
    results: dict,
    figures_dir: str,
    config: PipelineConfig,
) -> str:
    """撰写论文 LaTeX 源文件。"""
    # TODO: Phase 5 中实现完整的论文撰写
    lines = [
        r"\documentclass{cumcm}",
        r"\begin{document}",
        r"\title{数学建模竞赛论文}",
        r"\maketitle",
        r"\begin{abstract}",
        r"本文基于……",
        r"\end{abstract}",
        r"\section{问题重述}",
        problem_text[:2000] if problem_text else "（待填充）",
        r"\section{模型建立与求解}",
        r"（待填充）",
        r"\section{模型评价}",
        r"（待填充）",
        r"\end{document}",
    ]
    return "\n\n".join(lines)


def _compile_paper(
    tex_content: str,
    output_dir: Path,
    config: PipelineConfig,
) -> Path:
    """编译论文为 PDF。"""
    tex_dir = output_dir / "paper_src"
    ensure_dir(tex_dir)

    tex_path = tex_dir / "paper.tex"
    tex_path.write_text(tex_content, encoding="utf-8")

    pdf_path = tex_dir / "paper.pdf"

    # 尝试 xelatex 编译
    import subprocess
    import shutil

    for compiler in ["xelatex", "pdflatex"]:
        exe = shutil.which(compiler)
        if exe:
            try:
                subprocess.run(
                    [exe, "-interaction=nonstopmode", "-output-directory",
                     str(tex_dir), str(tex_path)],
                    check=True, capture_output=True, timeout=120,
                    cwd=str(tex_dir),
                )
                # 再跑一次解决交叉引用
                subprocess.run(
                    [exe, "-interaction=nonstopmode", "-output-directory",
                     str(tex_dir), str(tex_path)],
                    check=True, capture_output=True, timeout=120,
                    cwd=str(tex_dir),
                )
                logger.info(f"论文编译成功 [{compiler}]: {pdf_path}")
                return pdf_path
            except Exception:
                continue

    logger.warning("未找到 LaTeX 编译器，论文源文件已保存，请手动编译")
    return tex_path  # 编译失败时返回 .tex 文件
