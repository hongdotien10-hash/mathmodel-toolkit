"""交互式终端菜单 — 选比赛类型+题数"""

def show_menu():
    """显示交互菜单，返回 (contest_type, max_questions)"""
    print()
    print("=" * 55)
    print("    MathModel Toolkit — 数学建模竞赛求解器")
    print("=" * 55)
    print()
    print("  [1] 国赛 CUMCM   (车速50km/h, 中文, 25页)")
    print("  [2] 电工杯        (车速50km/h, 中文, 25页)")
    print("  [3] 美赛 MCM/ICM  (车速31mph, 英文, 25页)")
    print("  [4] 华为杯         (车速50km/h, 中文, 25页)")
    print("  [5] 其他/自动检测")
    print()

    contest_map = {"1": "cumcm", "2": "diangong", "3": "mcm", "4": "huawei", "5": "auto",
                   "": "auto"}

    choice = input("  选择比赛类型 [1-5, 默认1]: ").strip() or "1"
    contest = contest_map.get(choice, "auto")

    print()
    choice2 = input("  做几问? [1-9, 默认全部]: ").strip()
    n_questions = int(choice2) if choice2.isdigit() else 99

    contest_names = {"cumcm": "国赛 CUMCM", "diangong": "电工杯", "mcm": "美赛 MCM/ICM",
                     "huawei": "华为杯", "auto": "自动检测"}
    print()
    print(f"  >> {contest_names.get(contest, contest)} | {'全部' if n_questions >= 99 else f'前{n_questions}问'}")
    print("=" * 55)
    print()

    return contest, n_questions
