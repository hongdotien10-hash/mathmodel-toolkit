#!/usr/bin/env python3
"""
强制验证脚本 — 每个checkpoint必须运行，输出PASS/FAIL
不可跳过，不可手动标记 [OK] 代替
用法: python verify_checkpoint.py cp1|cp2|cp3 <项目目录>
"""
import sys, os, re, json, ast

def fail(msg):
    print(f"[FAIL] {msg}")
    return False

def ok(msg):
    print(f"[OK] {msg}")
    return True

def verify_cp1(proj_dir):
    """CP1: 建模分析验证"""
    print("="*50)
    print("CP1 强制验证")
    print("="*50)
    all_ok = True

    # 1. 检查 ANALYSIS_MODELING_REPORT.md 存在
    report = os.path.join(proj_dir, 'reports', 'ANALYSIS_MODELING_REPORT.md')
    if not os.path.exists(report):
        return fail(f"缺少 {report}")

    with open(report, 'r', encoding='utf-8') as f:
        content = f.read()

    # 2. 子问题数量声明
    sub_match = re.findall(r'本赛题共\s*(\d+)\s*个子问题', content)
    if not sub_match:
        all_ok &= fail("未找到「本赛题共X个子问题」声明")
    else:
        all_ok &= ok(f"子问题声明: {sub_match[0]}个")

    # 3. 约束追溯矩阵存在
    if '约束追溯矩阵' not in content:
        all_ok &= fail("缺少「约束追溯矩阵」")
    else:
        # 统计未解决标记：既支持 [FAIL] 字面量，也支持 SKILL.md 模板用的 ❌ emoji
        fail_count = content.count('[FAIL]') + content.count('❌')
        if fail_count > 0:
            all_ok &= fail(f"约束追溯矩阵中有 {fail_count} 个未解决约束（❌）")
        else:
            all_ok &= ok("约束追溯矩阵: 全部 [OK]")

    # 4. 题面完整性校验
    if '题面完整性校验' not in content and '题面完整性' not in content:
        all_ok &= fail("缺少「题面完整性校验」（Step 0）")
    else:
        all_ok &= ok("题面完整性校验: 存在")

    # 5. G类给定方法约束
    if '给定方法' in content or 'G类' in content:
        all_ok &= ok("G类给定方法约束: 已列出")
    else:
        print("[WARN] No G-type constraints found (OK if problem doesn't specify methods)")

    # 6. 子问题都有建模方案
    # 兼容两种写法："## 4. 问题一模型"（章节标题）和 "问题一：xxx"（行内声明）
    prob_sections = set(re.findall(r'问题[一二三四五六七八九十\d]+(?=[：:\s*]|模型)', content))
    declared = int(sub_match[0]) if sub_match else 0
    if len(prob_sections) < declared:
        all_ok &= fail(f"子问题建模: 声明{declared}个, 实际建模{len(prob_sections)}个")
    else:
        all_ok &= ok(f"子问题建模: {len(prob_sections)}个")

    # 7. 参数来源检查（防拍脑袋+防漏优化变量）——B题+A题教训
    # 7a: 附件参数逐项对照
    # 兼容 "附件1" / "附件 1" / "附件一" 等写法；单位组须含 km（否则 "3.5 km" 匹配不上）
    attachment_params = re.findall(
        r'附件\s*[三四\d一二三四五六七八九十]+\s*[^。\n|]{0,60}?(\d+(?:\.\d+)?)\s*(?:kg|km|m|N|s|rad|W|元|吨|米|小时|分钟)',
        content)
    if len(attachment_params) < 3:
        all_ok &= fail("参数来源不足——A题教训：必须逐项引用附件数据。I_add=7001.9未被引用导致c_rot错了48倍")
    else:
        all_ok &= ok(f"附件参数引用: {len(attachment_params)}处")

    # 7b: 优化变量清单
    # 兼容表格写法（| V1 | ... | [0, 1] |）和行内写法（α∈[0,1]）
    opt_table_rows = re.findall(r'^\s*\|\s*V\d+\s*\|', content, re.MULTILINE)
    opt_inline = re.findall(r'优化变量|决策变量|∈\s*\[', content)
    if '优化' in content and len(opt_table_rows) + len(opt_inline) < 2:
        all_ok &= fail("缺少优化变量清单——A题教训：Q2(2)幂指数α∈[0,1]是决策变量但未列出，导致固定为0.5、Pmax虚高10倍")
    else:
        all_ok &= ok(f"优化变量清单: 存在（表格{len(opt_table_rows)}行）")

    # 8. Skill调用记录检查（强制执行——防闲置skill）
    decisions_path = os.path.join(proj_dir, 'reports', 'DECISIONS.md')
    if os.path.exists(decisions_path):
        with open(decisions_path, 'r', encoding='utf-8') as f:
            dec = f.read()
        if 'brainstorming' not in dec.lower():
            all_ok &= fail("DECISIONS.md 中未记录 brainstorming skill 调用——深度审题前必须先调用brainstorming")
        else:
            all_ok &= ok("brainstorming: 已调用记录")
    else:
        all_ok &= fail("缺少 DECISIONS.md")

    # 文献循证
    lit_path = os.path.join(proj_dir, 'reports', 'LITERATURE_EVIDENCE.md')
    if os.path.exists(lit_path):
        all_ok &= ok("lit-evidence: 已产出文献循证报告")
    else:
        all_ok &= fail("缺少 LITERATURE_EVIDENCE.md——建模后必须调用lit-evidence skill")

    if all_ok:
        print("\n*** CP1: ALL PASS ***")
    else:
        print("\n*** CP1: FAIL - fix issues before entering decision gate 1 ***")
    return all_ok

def verify_cp2(proj_dir):
    """CP2: verify solution quality"""
    print("="*50)
    print("CP2 MANDATORY VERIFICATION")
    print("="*50)
    all_ok = True

    code_dir = os.path.join(proj_dir, 'code')
    fig_dir = os.path.join(proj_dir, 'figures')
    results_dir = os.path.join(proj_dir, 'results')

    # 1. 代码文件存在
    py_files = [f for f in os.listdir(code_dir) if f.endswith('.py')] if os.path.exists(code_dir) else []
    if len(py_files) == 0:
        return fail("code/ 目录无 .py 文件")
    all_ok &= ok(f"{len(py_files)} 个Python文件")

    # 2. 求解器/数值方法调用检查
    solver_keywords = [
        'solve(', '.solve(', 'optimize(', 'minimize(', 'bisect', 'newton',
        'fsolve', 'root(', 'curve_fit', 'odeint', 'solve_ivp',
        'golden(', 'brent(', 'fmin(', 'differential_evolution',
        '.fit(', 'LinearRegression', 'LSTM', 'RandomForest',
        'np.linalg.solve', 'spsolve',
        # 统计/仿真方法 — B题教训：MC仿真和统计检验也是合法求解
        'np.random', 'random.', 'stats.', 'sprt_', 'monte_carlo', 'mc_',
        'bootstrap', 'permutation', 'resample',
        'enumerate(', 'product(', 'combinations(',  # 穷举搜索
    ]
    greedy_patterns = [
        r'sorted\(.*key.*reverse=True\)',  # 贪心排序
    ]

    has_solver = False
    has_greedy = False
    for pf in py_files:
        with open(os.path.join(code_dir, pf), 'r', encoding='utf-8') as f:
            code = f.read()
        for kw in solver_keywords:
            if kw in code:
                has_solver = True
                break
        for gp in greedy_patterns:
            if re.search(gp, code):
                has_greedy = True
                print(f"[WARN] {pf} suspected greedy pattern: {gp[:30]}...")

    if has_solver:
        all_ok &= ok("求解器/数值方法调用: 已检测到")
    else:
        all_ok &= fail("未检测到任何求解器或数值方法调用！")

    if has_greedy:
        print("[WARN]️ WARN: 检测到贪心分配模式。如果贪心是唯一方法 → CP2 FAIL")
        # Check if solver also exists
        if not has_solver:
            all_ok &= fail("仅使用贪心分配，未调用求解器 → FAIL")

    # 3. 图表数据规划表检查（防填充图）——B题教训：9张图内容相同
    rr_path = os.path.join(proj_dir, 'reports', 'RESULTS_REPORT.md')
    has_figure_plan = False
    if os.path.exists(rr_path):
        with open(rr_path, 'r', encoding='utf-8') as f:
            rr_content = f.read()
        if '图表规划' in rr_content or '图表数据规划' in rr_content:
            has_figure_plan = True
            # 检查规划表中是否有「合成数据」标记
            synthetic_count = rr_content.count('合成数据') + rr_content.count('示意图') + rr_content.count('占位')
            if synthetic_count > 2:
                all_ok &= fail(f"图表规划中 {synthetic_count} 处标记为合成数据/示意图——真实数据不足")
            else:
                all_ok &= ok(f"图表规划: 存在 ({synthetic_count}处合成标记)")
    if not has_figure_plan:
        all_ok &= fail("缺少图表数据规划表——每张图必须标注数据来源(solver输出/参数扫描/题面数据)。B题教训：无规划→填充图")

    # 4. 图表数量检查
    fig_files = [f for f in os.listdir(fig_dir) if f.endswith('.pdf')] if os.path.exists(fig_dir) else []
    n_figs = len(fig_files)
    if n_figs < 12:
        all_ok &= fail(f"图表数量: {n_figs}张 (最低要求12张)")
    else:
        all_ok &= ok(f"图表数量: {n_figs}张")

    # 4. 结果文件检查
    xlsx_files = [f for f in os.listdir(results_dir) if f.endswith('.xlsx')] if os.path.exists(results_dir) else []
    if len(xlsx_files) == 0:
        all_ok &= fail("results/ 目录无 .xlsx 结果文件")
    else:
        all_ok &= ok(f"结果文件: {len(xlsx_files)}个")

    # 5. RESULTS_REPORT 存在
    rr = os.path.join(proj_dir, 'reports', 'RESULTS_REPORT.md')
    if not os.path.exists(rr):
        all_ok &= fail("缺少 RESULTS_REPORT.md")
    else:
        all_ok &= ok("RESULTS_REPORT.md: 存在")

    # 6. 检查是否有「参数乘系数」冒充蒙特卡洛
    for pf in py_files:
        with open(os.path.join(code_dir, pf), 'r', encoding='utf-8') as f:
            code = f.read()
        # 危险信号: for循环里只是乘系数然后求和
        if 'scenario' in pf.lower() or 'monte' in pf.lower() or 'simulation' in pf.lower():
            if 'for' in code and 'np.random' not in code and 'random.' not in code:
                print(f"[WARN]️ WARN: {pf} 文件名含scenario/simulation但未使用随机数生成")

    # 7. Skill调用记录检查（强制执行——防闲置skill）
    rr_path2 = os.path.join(proj_dir, 'reports', 'RESULTS_REPORT.md')
    if os.path.exists(rr_path2):
        with open(rr_path2, 'r', encoding='utf-8') as f:
            rr2 = f.read()
        if 'scipilot' not in rr2.lower() and 'nature-figure' not in rr2.lower():
            all_ok &= fail("RESULTS_REPORT.md 中未记录 scipilot-figure/nature-figure skill 调用——生成图表前必须调用绘图skill")
        else:
            all_ok &= ok("绘图skill: 已调用记录")
    else:
        all_ok &= fail("缺少 RESULTS_REPORT.md")

    # solver_templates
    for pf in py_files:
        with open(os.path.join(code_dir, pf), 'r', encoding='utf-8') as f:
            code = f.read()
        if 'GA' in code and 'PSO' in code:
            all_ok &= ok("solver_templates: 检测到GA/PSO导入")
            break
        if 'solver_templates' in code:
            all_ok &= ok("solver_templates: 检测到导入")
            break
    else:
        # 只有在需要优化的题目才检查——简化处理：有网格搜索就提醒
        has_search = any('for' in open(os.path.join(code_dir, pf),'r',encoding='utf-8').read() and 'np.linspace' in open(os.path.join(code_dir, pf),'r',encoding='utf-8').read() for pf in py_files)
        if has_search:
            all_ok &= fail("检测到手动网格搜索——必须用 solver_templates.py 的 adaptive_grid_search 代替")

    if all_ok:
        print("\n CP2: ALL PASS")
    else:
        print("\n CP2: FAIL — 修复以上问题后才能进入决策门2")
    return all_ok

def verify_cp3(proj_dir):
    """CP3: 论文就绪验证（精简5项——防翻车，不防出彩）"""
    print("="*50)
    print("CP3 强制验证（5项核心检查）")
    print("="*50)
    all_ok = True

    paper_dir = os.path.join(proj_dir, 'paper')
    output_paper_dir = os.path.join(proj_dir, 'output', 'paper')
    for d in [paper_dir, output_paper_dir]:
        if os.path.exists(os.path.join(d, 'main.tex')):
            paper_dir = d
            break

    pdf = os.path.join(paper_dir, 'main.pdf')
    tex = os.path.join(paper_dir, 'main.tex')

    # === 1. PDF存在且编译通过 ===
    if not os.path.exists(pdf):
        return fail(f"论文PDF不存在: {pdf}")
    all_ok &= ok(f"PDF存在: {os.path.getsize(pdf)/1024:.0f}KB")

    log = os.path.join(paper_dir, 'main.log')
    if os.path.exists(log):
        with open(log, 'r', encoding='utf-8', errors='ignore') as f:
            log_text = f.read()
        errors = log_text.count('! ')
        if '! Emergency stop' in log_text or errors > 3:
            all_ok &= fail(f"编译错误: {errors}处")
        else:
            all_ok &= ok(f"编译通过: {errors}个非致命问题")

    # === 2. 页数≥10（基本门槛） ===
    if os.path.exists(log):
        m = re.search(r'Output written on.*\((\d+) pages', log_text)
        pages = int(m.group(1)) if m else 5
    else:
        pages = 5
    if pages < 10:
        all_ok &= fail(f"页数: {pages}页 (基本门槛10页)")
    else:
        all_ok &= ok(f"页数: {pages}页")

    # === 3. 泄漏检查（内部文件名/占位符/填充图） ===
    if os.path.exists(tex):
        with open(tex, 'r', encoding='utf-8') as f:
            tex_text = f.read()
        leaks = ['ANALYSIS_MODELING_REPORT', 'RESULTS_REPORT', 'TBD', 'TODO', 'placeholder']
        found = [lk for lk in leaks if lk.lower() in tex_text.lower()]
        if found:
            all_ok &= fail(f"检测到泄漏/占位符: {found}")
        else:
            all_ok &= ok("无泄漏/占位符")

    # === 4. 图片内容去重（防填充图） ===
    import hashlib
    fig_dirs = []
    for d in [os.path.join(proj_dir, 'figures'), os.path.join(proj_dir, 'output', 'figures')]:
        if os.path.exists(d):
            fig_dirs.append(d)
    fig_hashes = {}; dup_count = 0
    for fig_dir in fig_dirs:
        for f in sorted(os.listdir(fig_dir)):
            if f.endswith('.pdf'):
                fpath = os.path.join(fig_dir, f)
                with open(fpath, 'rb') as fh:
                    h = hashlib.md5(fh.read()).hexdigest()
                if h in fig_hashes:
                    dup_count += 1
                    print(f"  [FAIL] 重复图片: {f} = {fig_hashes[h]} (MD5={h[:8]})")
                else:
                    fig_hashes[h] = f
    if dup_count > 0:
        all_ok &= fail(f"检测到 {dup_count} 张重复图片——填充图=学术造假")
    elif len(fig_hashes) >= 2:
        all_ok &= ok(f"图片去重: {len(fig_hashes)}张, 0重复")

    # === 5. 章节结构完整（缺节→FAIL） ===
    if os.path.exists(tex):
        required_sections = ['问题重述', '模型假设', '符号说明', '模型评价', '参考文献']
        missing = [s for s in required_sections if s not in tex_text]
        if missing:
            all_ok &= fail(f"缺少必需章节: {missing}")
        else:
            all_ok &= ok(f"章节结构: 5项必需章节齐全")

    if all_ok:
        print("\n*** CP3: ALL PASS ***")
    else:
        print("\n*** CP3: FAIL ***")
    return all_ok

if __name__ == '__main__':
    if len(sys.argv) >= 2 and sys.argv[1] in ('-h', '--help', 'help'):
        print("用法: python verify_checkpoint.py cp1|cp2|cp3 <项目目录>")
        print("示例: python verify_checkpoint.py cp1 ./CUMCM2024_A_solution")
        print("退出码: 0=通过, 1=未通过（门禁阻断）")
        sys.exit(0)

    if len(sys.argv) < 3:
        print("用法: python verify_checkpoint.py cp1|cp2|cp3 <项目目录>")
        print("示例: python verify_checkpoint.py cp1 ./CUMCM2024_A_solution")
        sys.exit(1)

    checkpoint = sys.argv[1]
    proj_dir = sys.argv[2]

    if checkpoint == 'cp1':
        ok_result = verify_cp1(proj_dir)
    elif checkpoint == 'cp2':
        ok_result = verify_cp2(proj_dir)
    elif checkpoint == 'cp3':
        ok_result = verify_cp3(proj_dir)
    else:
        print(f"未知checkpoint: {checkpoint}")
        sys.exit(1)

    sys.exit(0 if ok_result else 1)
