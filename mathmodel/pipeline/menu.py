"""交互菜单 — 比赛类型/页数/图数/自定义需求"""
import sys


def show_menu():
    """显示完整交互菜单，返回 (contest_type, max_questions, max_pages, max_figures, user_notes)"""
    print()
    print("=" * 60)
    print("    MathModel Toolkit — 数学建模竞赛求解器")
    print("=" * 60)
    print()

    # ---- Step 1: 比赛类型 ----
    contests = [
        ("1", "cumcm",   "国赛 CUMCM",     "中文, LaTeX, 20-25页, 省一标准"),
        ("2", "diangong", "电工杯",         "中文, LaTeX, 15-20页, 企业赛标准"),
        ("3", "mcm",     "美赛 MCM/ICM",   "英文, LaTeX, 20-25页, M奖标准"),
        ("4", "huawei",  "华为杯",          "中文, LaTeX, 20-25页"),
        ("5", "auto",    "其他/自动检测",    "根据题目自动适配"),
    ]
    for num, key, name, desc in contests:
        print(f"  [{num}] {name:<16} {desc}")
    print()
    choice = input("  选择比赛类型 [1-5, 默认1]: ").strip() or "1"
    contest_map = {c[0]: c[1] for c in contests}
    contest_names = {c[1]: c[0] for c in contests}
    contest = contest_map.get(choice, "cumcm")
    contest_name = [c[2] for c in contests if c[1] == contest][0]

    # ---- Step 2: 做几问 ----
    print()
    choice = input("  做几问? [1-9, 默认全部]: ").strip()
    n_questions = int(choice) if choice.isdigit() else 99

    # ---- Step 3: 推荐页数和图表数 ----
    print()
    print("  " + "-" * 50)

    # 页数推荐
    page_recs = {
        1: "12-15页 (1问: 摘要+重述+模型+求解+结论)",
        2: "15-18页 (2问: 含对比分析)",
        3: "18-22页 (3问: 含灵敏度+模型评价)",
        4: "20-25页 (4问: 完整论文结构)",
        99: "22-25页 (全问: 完整竞赛论文)",
    }
    rec_key = n_questions if n_questions in page_recs else 99
    page_rec = page_recs[rec_key]
    print(f"  推荐页数: {page_rec}")

    # 图表数推荐
    fig_recs = {
        1: "4-6张 (问题图×1-2 + 灵敏度图×1-2 + 流程图×1 + 对比图×1)",
        2: "6-10张 (每问2-3张 + 灵敏度×2 + 对比×1 + 流程图×1)",
        3: "10-15张 (每问2-4张 + 灵敏度×2-3 + 对比×2 + 流程图×1-2)",
        4: "15-20张 (每问3-4张 + 灵敏度×3 + 对比×2 + 流程图×2)",
        99: "15-22张 (全结构图表)",
    }
    fig_rec = fig_recs[rec_key]
    print(f"  推荐图表数: {fig_rec}")

    print("  " + "-" * 50)

    # ---- Step 4: 页数 ----
    print()
    rec_pages = {1: 15, 2: 18, 3: 22, 4: 25, 99: 25}
    default_pages = rec_pages.get(rec_key, 25)
    choice = input(f"  论文最多几页? [默认{default_pages}]: ").strip()
    max_pages = int(choice) if choice.isdigit() else default_pages

    # ---- Step 5: 图表最大数量 ----
    rec_figs = {1: 6, 2: 10, 3: 15, 4: 20, 99: 22}
    default_figs = rec_figs.get(rec_key, 20)
    choice = input(f"  图表最多几张? [默认{default_figs}]: ").strip()
    max_figures = int(choice) if choice.isdigit() else default_figs

    # ---- Step 6: 用户自定义要求 ----
    print()
    print("  " + "=" * 50)
    print("  自定义要求 (可选)")
    print("  可以写: 解题思路/侧重点/特殊要求/模型偏好/任何想法")
    print("  直接回车跳过")
    print("  " + "=" * 50)
    user_notes = input("  > ").strip()

    # ---- Summary ----
    print()
    print("=" * 60)
    print(f"  比赛类型: {contest_name}")
    print(f"  做几问:   {'全部' if n_questions >= 99 else f'前{n_questions}问'}")
    print(f"  最多页数: {max_pages}页")
    print(f"  最多图表: {max_figures}张")
    if user_notes:
        print(f"  自定义要求: {user_notes[:80]}{'...' if len(user_notes)>80 else ''}")
    print("=" * 60)
    print()

    return contest, n_questions, max_pages, max_figures, user_notes
