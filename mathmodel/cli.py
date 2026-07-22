"""命令行入口。

提供 `mathmodel` 命令，支持一键运行和分步操作。

Usage::

    mathmodel run --problem 赛题.pdf --data 附件.xlsx
    mathmodel web
    mathmodel config
"""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        prog="mathmodel",
        description="数学建模竞赛全自动求解器 — 上传题目，一键生成论文",
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # ---- run: 一键运行 ----
    run_parser = subparsers.add_parser("run", help="一键运行完整流水线")
    run_parser.add_argument("--problem", "-p", required=True, help="题目文件路径 (PDF/DOCX)")
    run_parser.add_argument("--data", "-d", nargs="*", help="数据附件路径")
    run_parser.add_argument("--output", "-o", default="./output", help="输出目录")
    run_parser.add_argument("--engine", choices=["latex", "typst"], default="latex", help="论文引擎")
    run_parser.add_argument("--contest", choices=["auto", "cumcm", "mcm"], default="auto", help="比赛类型")
    run_parser.add_argument("--no-auto", action="store_true", help="不自动确认模型推荐")
    run_parser.add_argument("--config", "-c", help="配置文件路径 (YAML/JSON)")
    run_parser.add_argument("--seed", type=int, default=42, help="随机种子")

    # ---- analyze: 仅分析 ----
    analyze_parser = subparsers.add_parser("analyze", help="仅进行题目分析和模型推荐")
    analyze_parser.add_argument("--problem", "-p", required=True, help="题目文件路径")
    analyze_parser.add_argument("--data", "-d", nargs="*", help="数据附件路径")

    # ---- web: 启动 Web 界面 ----
    web_parser = subparsers.add_parser("web", help="启动 Web UI")
    web_parser.add_argument("--port", type=int, default=8501, help="端口号")
    web_parser.add_argument("--host", default="localhost", help="绑定地址")

    # ---- config: 配置管理 ----
    config_parser = subparsers.add_parser("config", help="管理配置")
    config_parser.add_argument("--export", "-e", help="导出默认配置到文件")
    config_parser.add_argument("--show", "-s", action="store_true", help="显示当前配置")

    # ---- version ----
    subparsers.add_parser("version", help="显示版本号")

    args = parser.parse_args()

    if args.command == "run":
        _cmd_run(args)
    elif args.command == "analyze":
        _cmd_analyze(args)
    elif args.command == "web":
        _cmd_web(args)
    elif args.command == "config":
        _cmd_config(args)
    elif args.command == "version":
        print(f"mathmodel-toolkit v0.1.0")
    else:
        parser.print_help()


def _cmd_run(args):
    """执行一键运行命令。"""
    from mathmodel.pipeline import Pipeline, PipelineConfig

    # 加载配置
    if args.config:
        config = PipelineConfig.from_file(args.config)
    else:
        config = PipelineConfig()

    # 覆盖命令行参数
    config.engine = args.engine
    config.contest_type = args.contest
    config.random_seed = args.seed
    if args.output:
        config.output_dir = args.output

    # 运行
    pipe = Pipeline(config=config)
    pipe.run(
        problem=args.problem,
        data=args.data,
        auto_confirm=not args.no_auto,
    )

    # 导出
    pipe.export()

    paper = pipe.get_paper()
    if paper and paper.exists():
        print(f"\n✅ 论文已生成: {paper}")
    else:
        print("\n⚠️  论文未能编译，请检查输出目录中的 .tex 文件")


def _cmd_analyze(args):
    """仅分析和推荐。"""
    from mathmodel.pipeline import Pipeline, PipelineConfig

    config = PipelineConfig()
    pipe = Pipeline(config=config)
    pipe.parse(args.problem, args.data)
    pipe.analyze()
    recommendations = pipe.recommend()

    print("\n" + "=" * 60)
    print("📋 模型推荐结果")
    print("=" * 60)
    for rec in recommendations:
        print(f"\n整体置信度: {rec.get('confidence', 0):.1%}")
        print(f"方案摘要: {rec.get('summary', '')}")
        print("-" * 40)
        for sp in rec.get("sub_problems", []):
            print(f"  子问题 {sp['id']}: {sp['title'][:60]}")
            print(f"    题型: {sp.get('problem_type', '?')}")
            print(f"    推荐: {sp['model']} (分数: {sp['score']:.2f})")
            print(f"    理由: {sp['reason']}")
            if sp.get("alternatives"):
                print(f"    备选: {', '.join(a['model'] for a in sp['alternatives'])}")
    print()


def _cmd_web(args):
    """启动 Web 界面。"""
    try:
        import streamlit as st
    except ImportError:
        print("需要安装 streamlit: pip install mathmodel-toolkit[webui]")
        sys.exit(1)

    import subprocess
    webui_path = Path(__file__).parent.parent / "webui" / "app.py"
    if webui_path.exists():
        subprocess.run([
            "streamlit", "run", str(webui_path),
            "--server.port", str(args.port),
            "--server.address", args.host,
        ])
    else:
        print("Web UI 尚未实现，请等待后续版本")
        sys.exit(1)


def _cmd_config(args):
    """管理配置。"""
    from mathmodel.pipeline.config import PipelineConfig

    if args.export:
        config = PipelineConfig()
        config.to_file(args.export)
        print(f"配置已导出到: {args.export}")
    elif args.show:
        config = PipelineConfig()
        for field in config.__dataclass_fields__:
            print(f"  {field}: {getattr(config, field)}")
    else:
        print("用法: mathmodel config --export config.yaml  或  mathmodel config --show")


if __name__ == "__main__":
    main()
